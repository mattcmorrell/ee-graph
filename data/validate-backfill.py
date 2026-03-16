#!/usr/bin/env python3
"""
Validation script for temporal data backfill.
Checks data integrity, narrative consistency, and schema compliance.
"""

import json
from collections import defaultdict, Counter

with open("data/nodes.json") as f:
    nodes = json.load(f)["nodes"]
with open("data/edges.json") as f:
    edges = json.load(f)["edges"]

node_by_id = {n["id"]: n for n in nodes}
node_ids = set(node_by_id.keys())

errors = []
warnings = []

def err(msg):
    errors.append(msg)
    print(f"  FAIL: {msg}")

def warn(msg):
    warnings.append(msg)
    print(f"  WARN: {msg}")

def ok(msg):
    print(f"  OK: {msg}")

# ─── 1. Terminated People ────────────────────────────────────────────────────

print("\n1. TERMINATED PEOPLE")
terminated = [n for n in nodes if n["type"] == "person" and n["properties"].get("status") == "terminated"]

if len(terminated) >= 10:
    ok(f"{len(terminated)} terminated people found")
else:
    err(f"Expected >= 10 terminated, got {len(terminated)}")

for t in terminated:
    pid = t["id"]
    props = t["properties"]
    if not props.get("endDate"):
        err(f"{pid} ({props['name']}) missing endDate")
    if not props.get("terminationReason"):
        err(f"{pid} ({props['name']}) missing terminationReason")
    if "regrettable" not in props:
        err(f"{pid} ({props['name']}) missing regrettable")

regrettable = [t for t in terminated if t["properties"].get("regrettable") is True]
non_regrettable = [t for t in terminated if t["properties"].get("regrettable") is False]
ok(f"Regrettable: {len(regrettable)}, Non-regrettable: {len(non_regrettable)}")

# Check edges for new terminated people (person-149 through person-156)
new_term_ids = [f"person-{i}" for i in range(149, 157)]
for pid in new_term_ids:
    if pid not in node_ids:
        err(f"{pid} not found in nodes")
        continue
    person = node_by_id[pid]
    end_date = person["properties"].get("endDate")
    person_edges = [e for e in edges if e["source"] == pid or e["target"] == pid]

    # Check required edge types exist
    edge_types = set(e["type"] for e in person_edges if e["source"] == pid)
    required = {"reports_to", "member_of", "in_department", "in_division", "holds_position", "located_at", "has_comp", "has_cobra_event"}
    missing = required - edge_types
    if missing:
        err(f"{pid}: missing edge types: {missing}")
    else:
        ok(f"{pid} ({person['properties']['name']}): all required edges present")

    # Check endDates on temporal edges
    temporal_types = {"reports_to", "member_of", "in_department", "in_division", "holds_position"}
    for e in person_edges:
        if e["source"] == pid and e["type"] in temporal_types:
            edge_end = e["metadata"].get("endDate")
            if not edge_end:
                warn(f"{pid} edge {e['type']}->{e['target']} missing endDate")
            elif end_date and edge_end > end_date:
                err(f"{pid} edge endDate {edge_end} > person endDate {end_date}")

# ─── 2. Survey Responses ─────────────────────────────────────────────────────

print("\n2. SURVEY RESPONSES")
surveys = [n for n in nodes if n["type"] == "survey_response"]
by_date = defaultdict(list)
for s in surveys:
    by_date[s["properties"]["date"]].append(s)

dates = sorted(by_date.keys())
expected_dates = {"2024-04-20", "2024-07-20", "2024-10-20", "2025-04-20", "2026-01-20"}
actual_dates = set(dates)

if expected_dates == actual_dates:
    ok(f"5 survey dates found: {dates}")
elif expected_dates.issubset(actual_dates):
    ok(f"All 5 expected dates present (plus extras: {actual_dates - expected_dates})")
else:
    err(f"Missing survey dates: {expected_dates - actual_dates}")

for date in dates:
    svs = by_date[date]
    enps = [s for s in svs if s["properties"]["surveyType"] == "enps"]
    well = [s for s in svs if s["properties"]["surveyType"] == "wellbeing"]
    ok(f"{date}: {len(enps)} eNPS + {len(well)} wellbeing = {len(svs)} total")

# Check respondents were employed at survey date
survey_person = {}
for e in edges:
    if e["type"] == "responded_to":
        survey_person[e["target"]] = e["source"]

for s in surveys:
    sid = s["id"]
    pid = survey_person.get(sid)
    if not pid:
        err(f"Survey {sid} has no responded_to edge")
        continue
    person = node_by_id.get(pid)
    if not person:
        err(f"Survey {sid} respondent {pid} not found")
        continue
    survey_date = s["properties"]["date"]
    start = person["properties"].get("startDate", "2099-01-01")
    end = person["properties"].get("endDate")
    if start > survey_date:
        err(f"Survey {sid}: {pid} started {start} but survey on {survey_date}")
    if end and end < survey_date:
        err(f"Survey {sid}: {pid} ended {end} but survey on {survey_date}")

# ─── 3. Review Cycles ────────────────────────────────────────────────────────

print("\n3. REVIEW CYCLES")
reviews = [n for n in nodes if n["type"] == "review"]
review_dates = set()
for r in reviews:
    cd = r["properties"].get("completedDate")
    if cd:
        review_dates.add(cd[:7])  # YYYY-MM

if "2024-12" in review_dates and "2025-12" in review_dates:
    ok("Both Dec 2024 and Dec 2025 review cycles present")
else:
    warn(f"Review months found: {sorted(review_dates)}")

# Count Dec 2024 reviews
dec24 = [r for r in reviews if r["properties"].get("completedDate", "").startswith("2024")]
ok(f"Dec 2024 cycle: {len(dec24)} reviews")

# Rating distribution for Dec 2024
dec24_ratings = Counter(r["properties"].get("rating") for r in dec24)
ok(f"Dec 2024 ratings: {dict(dec24_ratings)}")

# ─── 4. Edge Integrity ───────────────────────────────────────────────────────

print("\n4. EDGE INTEGRITY")

orphan_source = 0
orphan_target = 0
for e in edges:
    if e["source"] not in node_ids:
        orphan_source += 1
    if e["target"] not in node_ids:
        orphan_target += 1

if orphan_source == 0 and orphan_target == 0:
    ok("No orphaned edges")
else:
    err(f"Orphaned edges: {orphan_source} sources, {orphan_target} targets")

# ─── 5. in_department Metadata ────────────────────────────────────────────────

print("\n5. IN_DEPARTMENT METADATA")
id_edges = [e for e in edges if e["type"] == "in_department"]
empty = [e for e in id_edges if not e["metadata"].get("startDate")]
if empty:
    err(f"{len(empty)} in_department edges still missing startDate")
else:
    ok(f"All {len(id_edges)} in_department edges have startDate")

# ─── 6. eNPS Narrative Trajectory ─────────────────────────────────────────────

print("\n6. eNPS NARRATIVE CHECK")

# Build dept mapping
dept_names_map = {}
for n in nodes:
    if n["type"] == "department":
        dept_names_map[n["id"]] = n["properties"]["name"]

person_dept_name = {}
for e in edges:
    if e["type"] == "in_department":
        person_dept_name[e["source"]] = dept_names_map.get(e["target"], "?")

dept_date_scores = defaultdict(lambda: defaultdict(list))
for s in surveys:
    if s["properties"]["surveyType"] != "enps":
        continue
    pid = survey_person.get(s["id"])
    if not pid:
        continue
    dept = person_dept_name.get(pid, "?")
    date = s["properties"]["date"]
    score = s["properties"]["score"]
    dept_date_scores[dept][date].append(score)

def calc_enps(scores):
    if not scores:
        return None
    n = len(scores)
    promoters = sum(1 for s in scores if s >= 9)
    detractors = sum(1 for s in scores if s <= 6)
    return round(((promoters - detractors) / n) * 100)

for dept in ["Engineering", "Customer Support", "Sales", "Design"]:
    scores_by_date = dept_date_scores.get(dept, {})
    trajectory = []
    for date in sorted(scores_by_date.keys()):
        enps = calc_enps(scores_by_date[date])
        avg = sum(scores_by_date[date]) / len(scores_by_date[date])
        trajectory.append(f"{date[:7]}:{enps:+d}(avg {avg:.1f})")
    ok(f"{dept}: {' → '.join(trajectory)}")

# ─── 7. Promotions Verified ──────────────────────────────────────────────────

print("\n7. PROMOTIONS & TRANSFERS")
promo_checks = {
    "person-006": ("Senior Platform Engineer", "IC-4"),
    "person-011": ("Senior Engineer", "IC-3"),
    "person-025": ("Senior Engineer", "IC-3"),
    "person-068": ("Senior Platform Engineer", "IC-4"),
    "person-044": ("Tier 2 Specialist", "IC-3"),
}

for pid, (exp_role, exp_level) in promo_checks.items():
    person = node_by_id.get(pid)
    if not person:
        err(f"{pid} not found")
        continue
    role = person["properties"]["role"]
    level = person["properties"]["level"]
    if role == exp_role and level == exp_level:
        ok(f"{pid} ({person['properties']['name']}): {role} {level}")
    else:
        err(f"{pid}: expected {exp_role} {exp_level}, got {role} {level}")

# Check holds_position edges have previous + current
for pid in promo_checks:
    hp_edges = [e for e in edges if e["source"] == pid and e["type"] == "holds_position"]
    statuses = [e["metadata"].get("status") for e in hp_edges]
    if "previous" in statuses and "current" in statuses:
        ok(f"{pid}: has both previous and current holds_position")
    else:
        warn(f"{pid}: holds_position statuses = {statuses}")

# ─── Summary ──────────────────────────────────────────────────────────────────

print("\n" + "=" * 60)
print(f"VALIDATION: {len(errors)} errors, {len(warnings)} warnings")
if errors:
    print("\nERRORS:")
    for e in errors:
        print(f"  - {e}")
if warnings:
    print("\nWARNINGS:")
    for w in warnings:
        print(f"  - {w}")
if not errors:
    print("\nAll checks passed!")
print("=" * 60)
