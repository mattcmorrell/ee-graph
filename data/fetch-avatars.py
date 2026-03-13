#!/usr/bin/env python3
"""
Fetch gender + ethnicity-appropriate photographic avatars for all people.
Downloads from randomuser.me API, saves locally to data/avatars/.
Sets avatarUrl on each person node.

Run: python3 data/fetch-avatars.py
"""

import json
import os
import time
import urllib.request
from collections import defaultdict

with open("data/nodes.json") as f:
    data = json.load(f)

os.makedirs("data/avatars", exist_ok=True)

# ─── Configuration ────────────────────────────────────────────────────────────

# randomuser.me nationality params that produce ethnicity-appropriate photos
# API supports: AU,BR,CA,CH,DE,DK,ES,FI,FR,GB,IE,IN,IR,MX,NL,NO,NZ,RS,TR,UA,US
RACE_TO_NAT = {
    "white": "US,GB,DE,FR,AU,CA,DK,NL,NO,FI",
    "black": "US,BR",
    "hispanic": "ES,MX,BR",
    "asian": "IN,IR,TR",       # South/West Asian — imperfect for East Asian
    "native_american": "US",
    "pacific_islander": "NZ,AU",
    "two_or_more": "US,BR",
    "prefer_not_to_say": "US",
}

# Map our gender field to randomuser.me's binary gender param
GENDER_MAP = {
    "male": "male",
    "female": "female",
    "nonbinary": "female",         # default for nonbinary
    "prefer_not_to_say": "male",   # default for undisclosed
}

# ─── Group people by (api_gender, race) ───────────────────────────────────────

groups = defaultdict(list)
for node in data["nodes"]:
    if node["type"] != "person":
        continue
    props = node["properties"]
    gender = props.get("gender", "male")
    race = props.get("race", "white")
    api_gender = GENDER_MAP.get(gender, "male")
    groups[(api_gender, race)].append(node)

print(f"People to process: {sum(len(v) for v in groups.values())}")
print(f"Groups: {len(groups)}")
for (g, r), people in sorted(groups.items()):
    print(f"  {g}/{r}: {len(people)}")

# ─── Fetch photos per group via batch API ─────────────────────────────────────

total_fetched = 0
errors = 0

for (api_gender, race), people in sorted(groups.items()):
    nat = RACE_TO_NAT.get(race, "US")
    n = len(people)
    seed = f"acme-{api_gender}-{race}"

    # Batch request — one call per group
    api_url = (
        f"https://randomuser.me/api/"
        f"?results={n}&gender={api_gender}&nat={nat}&seed={seed}"
    )

    print(f"\nFetching {n} photos for {api_gender}/{race} (nat={nat})...")

    try:
        req = urllib.request.Request(api_url, headers={"User-Agent": "AcmeCo-HRIS-Demo/1.0"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            api_data = json.loads(resp.read())
            results = api_data["results"]
    except Exception as e:
        print(f"  ERROR fetching batch: {e}")
        errors += n
        continue

    if len(results) < n:
        print(f"  WARNING: got {len(results)} results, needed {n}")

    # Sort people deterministically for consistent assignment
    people_sorted = sorted(people, key=lambda p: p["id"])

    for i, person in enumerate(people_sorted):
        if i >= len(results):
            print(f"  SKIP {person['id']}: no more results")
            errors += 1
            continue

        result = results[i]
        photo_url = result["picture"]["large"]  # 128x128 JPG on randomuser.me CDN
        person_id = person["id"]
        local_path = f"data/avatars/{person_id}.jpg"

        # Download the photo
        try:
            urllib.request.urlretrieve(photo_url, local_path)
            person["properties"]["avatarUrl"] = local_path
            name = person["properties"]["name"]
            total_fetched += 1
            if total_fetched % 20 == 0 or total_fetched <= 5:
                print(f"  {person_id}: {name} -> {local_path}")
        except Exception as e:
            print(f"  ERROR downloading {person_id}: {e}")
            # Fall back to CDN URL
            person["properties"]["avatarUrl"] = photo_url
            errors += 1

    # Be nice to the API between groups
    time.sleep(0.5)

# ─── Save ─────────────────────────────────────────────────────────────────────

with open("data/nodes.json", "w") as f:
    json.dump(data, f, indent=2)
    f.write("\n")

# ─── Summary ──────────────────────────────────────────────────────────────────

avatar_count = sum(
    1
    for n in data["nodes"]
    if n["type"] == "person" and n["properties"].get("avatarUrl")
)

print(f"\n{'=' * 50}")
print(f"DONE: {total_fetched} photos downloaded, {errors} errors")
print(f"People with avatarUrl: {avatar_count}")
print(f"Photos saved to: data/avatars/")
print(f"{'=' * 50}")
