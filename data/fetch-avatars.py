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

# ─── Fetch one avatar per person with unique seed ────────────────────────────

people = [n for n in data["nodes"] if n["type"] == "person"]
people.sort(key=lambda p: p["id"])

print(f"People to process: {len(people)}")

total_fetched = 0
errors = 0

for person in people:
    props = person["properties"]
    person_id = person["id"]
    name = props["name"]
    gender = props.get("gender", "male")
    race = props.get("race", "white")
    api_gender = GENDER_MAP.get(gender, "male")
    nat = RACE_TO_NAT.get(race, "US")
    local_path = f"data/avatars/{person_id}.jpg"

    # Unique seed per person ensures different photo each time
    seed = f"acme-{person_id}"
    api_url = (
        f"https://randomuser.me/api/"
        f"?results=1&gender={api_gender}&nat={nat}&seed={seed}"
    )

    # Skip if avatar already exists and looks valid (>1KB)
    if os.path.exists(local_path) and os.path.getsize(local_path) > 1024:
        person["properties"]["avatarUrl"] = local_path
        total_fetched += 1
        continue

    fetched = False
    for attempt in range(3):
        try:
            req = urllib.request.Request(api_url, headers={"User-Agent": "AcmeCo-HRIS-Demo/1.0"})
            with urllib.request.urlopen(req, timeout=15) as resp:
                api_data = json.loads(resp.read())
                results = api_data.get("results", [])
                if not results:
                    time.sleep(1 + attempt)
                    continue
                result = results[0]
                photo_url = result["picture"]["large"]

            urllib.request.urlretrieve(photo_url, local_path)
            person["properties"]["avatarUrl"] = local_path
            total_fetched += 1
            if total_fetched % 20 == 0 or total_fetched <= 5:
                print(f"  {person_id}: {name} ({api_gender}/{race}) -> {local_path}")
            fetched = True
            break
        except Exception as e:
            if attempt == 2:
                print(f"  ERROR {person_id} ({name}): {e}")
                errors += 1
            else:
                time.sleep(1 + attempt)

    # Be nice to the API
    time.sleep(0.25)

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
