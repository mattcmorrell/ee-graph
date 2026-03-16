#!/usr/bin/env python3
"""
Combined backfill: change nodes, richer reviews, terminated people, career ladder.

Adds:
- Career ladder (level nodes with comp bands, title templates)
- 8 new terminated employees (10 total) with full metadata
- Fix 2 existing terminated employees (add termination fields)
- Annual reviews for ~80% of org across 2 cycles (Dec 2024 + Dec 2025)
- Self-assessment + manager-assessment text on all reviews
- Change nodes: comp history, level changes, role changes
- has_change edges connecting people to their changes

Tiers:
  Stars (~10%): 8-15% annual bumps, level changes, off-cycle adjustments
  Strong (~25%): 5-8% annual bumps, occasional level change
  Solid (~45%): 3-5% annual bumps, steady
  Stagnant (~15%): 1-3% or flat, same role 2+ years
  Declining (~5%): flat, PIP or concerns

Run: python3 data/backfill-changes.py
"""

import json
import random
from datetime import datetime, timedelta
from collections import defaultdict
from copy import deepcopy

random.seed(42)

# ─── Load Data ────────────────────────────────────────────────────────────────

with open("data/nodes.json") as f:
    nodes_data = json.load(f)
with open("data/edges.json") as f:
    edges_data = json.load(f)
with open("data/schema.json") as f:
    schema = json.load(f)

nodes = nodes_data["nodes"]
edges = edges_data["edges"]

# ─── Build Lookups ────────────────────────────────────────────────────────────

node_by_id = {n["id"]: n for n in nodes}
person_nodes = [n for n in nodes if n["type"] == "person"]
active_people = [n for n in person_nodes if n["properties"].get("status") == "active"]

# Department mapping
person_to_dept = {}
person_to_team = {}
person_to_manager = {}
person_to_comp = {}

for e in edges:
    if e["type"] == "in_department":
        person_to_dept[e["source"]] = e["target"]
    elif e["type"] == "member_of":
        if e["source"] not in person_to_team:
            person_to_team[e["source"]] = e["target"]
    elif e["type"] == "reports_to":
        person_to_manager[e["source"]] = e["target"]
    elif e["type"] == "has_comp":
        src = e["source"]
        tgt_node = node_by_id.get(e["target"])
        if tgt_node and tgt_node["properties"].get("type") == "salary":
            person_to_comp[src] = tgt_node

dept_names = {}
for n in nodes:
    if n["type"] == "department":
        dept_names[n["id"]] = n["properties"]["name"]

# ─── ID Generators ────────────────────────────────────────────────────────────

_counters = {
    "person": 149,
    "comp": 159,
    "review": 7,
    "change": 1,
    "level": 1,
    "cobra": 3,
}


def next_id(prefix):
    n = _counters[prefix]
    _counters[prefix] = n + 1
    return f"{prefix}-{n:03d}"


def make_edge(source, target, etype, metadata, timestamp=None):
    e = {"source": source, "target": target, "type": etype, "metadata": metadata}
    if timestamp:
        e["timestamp"] = timestamp
    return e


def date_str(d):
    if isinstance(d, str):
        return d
    return d.strftime("%Y-%m-%d")


def ts(d):
    if isinstance(d, str):
        return d + "T00:00:00Z"
    return d.strftime("%Y-%m-%dT00:00:00Z")


new_nodes = []
new_edges = []
stats = defaultdict(int)

# ─── Step 0: Schema Updates ──────────────────────────────────────────────────

# Add change node type
schema["nodeTypes"]["change"] = {
    "description": "A discrete change to an employee record field",
    "properties": {
        "field": {
            "type": "string",
            "enum": ["level", "role", "salary", "salary_band", "manager", "team", "department"],
            "required": True,
            "description": "Which field changed",
        },
        "from": {"type": "string", "required": True, "description": "Previous value"},
        "to": {"type": "string", "required": True, "description": "New value"},
        "effectiveDate": {"type": "string", "format": "date", "required": True},
        "reason": {
            "type": "string",
            "enum": ["promotion", "lateral_move", "reorg", "market_adjustment", "annual_review", "merit", "correction", "new_hire"],
            "required": False,
            "description": "Optional reason for the change",
        },
    },
}

# Add level node type (career ladder)
schema["nodeTypes"]["level"] = {
    "description": "A career level in the organization's leveling framework",
    "properties": {
        "code": {"type": "string", "required": True, "description": "Level code e.g. IC-1, M-2"},
        "track": {
            "type": "string",
            "enum": ["individual_contributor", "management"],
            "required": True,
        },
        "title_template": {"type": "string", "required": False, "description": "Typical title at this level"},
        "salary_band_min": {"type": "number", "required": True},
        "salary_band_max": {"type": "number", "required": True},
        "salary_band_mid": {"type": "number", "required": True},
        "description": {"type": "string", "required": False},
    },
}

# Add has_change edge type
schema["edgeTypes"]["has_change"] = {
    "source": "person",
    "target": "change",
    "description": "Links a person to a change in their employment record",
}

# Add next_level edge type
schema["edgeTypes"]["next_level"] = {
    "source": "level",
    "target": "level",
    "description": "Career progression path between levels",
}

# Add selfAssessment and managerAssessment to review properties
schema["nodeTypes"]["review"]["properties"]["selfAssessment"] = {
    "type": "string",
    "required": False,
    "description": "Employee's self-assessment text",
}
schema["nodeTypes"]["review"]["properties"]["managerAssessment"] = {
    "type": "string",
    "required": False,
    "description": "Manager's assessment text",
}

# Add terminationReason, terminationDetail, regrettable to person
if "terminationReason" not in schema["nodeTypes"]["person"]["properties"]:
    schema["nodeTypes"]["person"]["properties"]["terminationReason"] = {
        "type": "string",
        "enum": ["voluntary", "involuntary"],
        "required": False,
    }
    schema["nodeTypes"]["person"]["properties"]["terminationDetail"] = {
        "type": "string",
        "required": False,
    }
    schema["nodeTypes"]["person"]["properties"]["regrettable"] = {
        "type": "boolean",
        "required": False,
    }

print("Schema updated: change, level node types; has_change, next_level edge types; review+person fields")

# ─── Step 1: Career Ladder ───────────────────────────────────────────────────

LEVELS = [
    {"code": "IC-1", "track": "individual_contributor", "title_template": "Associate / Junior",
     "salary_band_min": 55000, "salary_band_max": 80000, "salary_band_mid": 67500,
     "description": "Entry level. Learning the role, needs guidance on most tasks."},
    {"code": "IC-2", "track": "individual_contributor", "title_template": "Engineer / Specialist",
     "salary_band_min": 75000, "salary_band_max": 115000, "salary_band_mid": 95000,
     "description": "Independently productive. Owns features or workstreams end to end."},
    {"code": "IC-3", "track": "individual_contributor", "title_template": "Senior",
     "salary_band_min": 105000, "salary_band_max": 155000, "salary_band_mid": 130000,
     "description": "Experienced. Mentors others, drives technical decisions, handles ambiguity."},
    {"code": "IC-4", "track": "individual_contributor", "title_template": "Staff / Lead",
     "salary_band_min": 140000, "salary_band_max": 195000, "salary_band_mid": 167500,
     "description": "Deep expertise. Sets direction for projects or domains. Cross-team influence."},
    {"code": "IC-5", "track": "individual_contributor", "title_template": "Principal / Distinguished",
     "salary_band_min": 180000, "salary_band_max": 260000, "salary_band_mid": 220000,
     "description": "Org-wide impact. Defines strategy and technical vision."},
    {"code": "M-1", "track": "management", "title_template": "Manager / Lead",
     "salary_band_min": 120000, "salary_band_max": 170000, "salary_band_mid": 145000,
     "description": "Manages a team. Responsible for people development and team delivery."},
    {"code": "M-2", "track": "management", "title_template": "Senior Manager / Director",
     "salary_band_min": 155000, "salary_band_max": 220000, "salary_band_mid": 187500,
     "description": "Manages managers or large teams. Owns department-level outcomes."},
    {"code": "M-3", "track": "management", "title_template": "VP",
     "salary_band_min": 190000, "salary_band_max": 280000, "salary_band_mid": 235000,
     "description": "Division leader. Sets strategy, manages multiple teams/functions."},
    {"code": "C-1", "track": "management", "title_template": "C-Suite",
     "salary_band_min": 250000, "salary_band_max": 400000, "salary_band_mid": 325000,
     "description": "Executive leadership. Company-wide strategy and accountability."},
]

level_nodes = {}
level_progression = {
    "IC-1": "IC-2", "IC-2": "IC-3", "IC-3": "IC-4", "IC-4": "IC-5",
    "M-1": "M-2", "M-2": "M-3", "M-3": "C-1",
}
# Cross-track: IC-3/IC-4 can move to M-1
cross_track = {"IC-3": "M-1", "IC-4": "M-1"}

for lv in LEVELS:
    lid = f"level-{lv['code'].lower().replace('-', '')}"
    node = {
        "id": lid,
        "type": "level",
        "properties": {
            "code": lv["code"],
            "track": lv["track"],
            "title_template": lv["title_template"],
            "salary_band_min": lv["salary_band_min"],
            "salary_band_max": lv["salary_band_max"],
            "salary_band_mid": lv["salary_band_mid"],
            "description": lv["description"],
        },
    }
    new_nodes.append(node)
    level_nodes[lv["code"]] = node
    stats["level_nodes"] += 1

# next_level edges
for from_code, to_code in level_progression.items():
    from_id = f"level-{from_code.lower().replace('-', '')}"
    to_id = f"level-{to_code.lower().replace('-', '')}"
    new_edges.append(make_edge(from_id, to_id, "next_level", {"track": "same"}))
    stats["next_level_edges"] += 1

for from_code, to_code in cross_track.items():
    from_id = f"level-{from_code.lower().replace('-', '')}"
    to_id = f"level-{to_code.lower().replace('-', '')}"
    new_edges.append(make_edge(from_id, to_id, "next_level", {"track": "cross_track", "note": "IC to management transition"}))
    stats["next_level_edges"] += 1

print(f"Career ladder: {stats['level_nodes']} levels, {stats['next_level_edges']} progression edges")

# ─── Step 2: Fix Existing Terminated People ──────────────────────────────────

for n in nodes:
    if n["id"] == "person-070":  # Jason Cooper
        n["properties"]["terminationReason"] = "voluntary"
        n["properties"]["terminationDetail"] = "Accepted offer at larger company. Cited lack of growth opportunities."
        n["properties"]["regrettable"] = True
        n["properties"]["bio"] = "Reliable Platform engineer. Deep knowledge of deployment pipeline. Left after 11 months — felt stuck at IC-2 with no promotion path discussed. Departure exposed single-point-of-failure in CI/CD ownership."
        stats["terminated_fixed"] += 1
    elif n["id"] == "person-112":  # Patrick O'Malley
        n["properties"]["terminationReason"] = "voluntary"
        n["properties"]["terminationDetail"] = "Relocated out of state for family reasons."
        n["properties"]["regrettable"] = False
        n["properties"]["bio"] = "Solid Product Engineering contributor. Departure was personal, not performance-related. Team absorbed workload but velocity dropped 20% for two sprints."
        stats["terminated_fixed"] += 1

print(f"Fixed {stats['terminated_fixed']} existing terminated employees")

# ─── Step 3: Add New Terminated Employees ────────────────────────────────────

TERMINATED = [
    {
        "name": "Marcus Cole",
        "email": "marcus.cole@acmeco.com",
        "role": "Senior Engineer",
        "level": "IC-4",
        "startDate": "2022-06-15",
        "endDate": "2024-08-30",
        "terminationReason": "voluntary",
        "terminationDetail": "Joined competitor for 40% raise. Had been flagged for promotion but it stalled in approvals for 6 months.",
        "regrettable": True,
        "department": "department-001",
        "team": "team-001",
        "manager": "person-008",  # Raj
        "location": "location-001",
        "salary": 162000,
        "gender": "male",
        "race": "white",
        "eeoCategory": "professionals",
        "bio": "Top performer on Platform team. Deep infrastructure knowledge — was the only person who understood the legacy auth system. Departure triggered 3-month scramble to document and redistribute his work. The promotion delay was the tipping point.",
    },
    {
        "name": "Priya Desai",
        "email": "priya.desai@acmeco.com",
        "role": "Engineer",
        "level": "IC-2",
        "startDate": "2023-01-10",
        "endDate": "2024-10-15",
        "terminationReason": "voluntary",
        "terminationDetail": "Burnout. Cited unsustainable workload after Marcus Cole's departure. No backfill for 4 months.",
        "regrettable": True,
        "department": "department-001",
        "team": "team-001",
        "manager": "person-008",  # Raj
        "location": "location-002",
        "salary": 98000,
        "gender": "female",
        "race": "asian",
        "eeoCategory": "professionals",
        "bio": "Strong IC-2 who absorbed too much after Marcus left. Workload went from 2 projects to 4 overnight. Manager (Raj) flagged it but headcount wasn't approved for months. Classic preventable loss.",
    },
    {
        "name": "Tom Fischer",
        "email": "tom.fischer@acmeco.com",
        "role": "Support Specialist",
        "level": "IC-1",
        "startDate": "2024-02-05",
        "endDate": "2025-01-20",
        "terminationReason": "involuntary",
        "terminationDetail": "Performance. Missed SLA targets consistently after ramp period.",
        "regrettable": False,
        "department": "department-002",
        "team": "team-004",
        "manager": "person-079",
        "location": "location-003",
        "salary": 48000,
        "gender": "male",
        "race": "white",
        "eeoCategory": "office_clerical",
        "bio": "Struggled with ticket complexity after onboarding. PIP initiated but metrics didn't improve. Clean separation.",
    },
    {
        "name": "Lisa Park",
        "email": "lisa.park@acmeco.com",
        "role": "Account Executive",
        "level": "IC-3",
        "startDate": "2023-03-20",
        "endDate": "2025-06-15",
        "terminationReason": "voluntary",
        "terminationDetail": "Better comp package at a competitor. Was mid-band, requested market adjustment that was denied.",
        "regrettable": False,
        "department": "department-003",
        "team": "team-005",
        "manager": "person-026",
        "location": "location-001",
        "salary": 92000,
        "gender": "female",
        "race": "asian",
        "eeoCategory": "professionals",
        "bio": "Solid performer, not a standout. The denied market adjustment stung but her pipeline numbers were middle of pack. Replacement hired within 6 weeks.",
    },
    {
        "name": "Rachel Kim",
        "email": "rachel.kim@acmeco.com",
        "role": "Designer",
        "level": "IC-3",
        "startDate": "2022-09-12",
        "endDate": "2025-03-01",
        "terminationReason": "voluntary",
        "terminationDetail": "Career change — left to start a freelance practice. Not driven by dissatisfaction.",
        "regrettable": False,
        "department": "department-004",
        "team": "team-006",
        "manager": "person-029",
        "location": "location-002",
        "salary": 125000,
        "gender": "female",
        "race": "asian",
        "eeoCategory": "professionals",
        "bio": "Talented designer who wanted to go independent. Left on great terms. Still does occasional contract work.",
    },
    {
        "name": "James Wilson",
        "email": "james.wilson@acmeco.com",
        "role": "Operations Analyst",
        "level": "IC-2",
        "startDate": "2023-08-01",
        "endDate": "2025-05-30",
        "terminationReason": "voluntary",
        "terminationDetail": "Spouse relocated for work. Would have stayed otherwise.",
        "regrettable": False,
        "department": "department-005",
        "team": "team-007",
        "manager": "person-035",
        "location": "location-003",
        "salary": 78000,
        "gender": "male",
        "race": "white",
        "eeoCategory": "professionals",
        "bio": "Reliable ops contributor. Departure was purely personal. Offered remote arrangement but role required on-site compliance work.",
    },
    {
        "name": "Maya Johnson",
        "email": "maya.johnson@acmeco.com",
        "role": "Engineer",
        "level": "IC-3",
        "startDate": "2022-03-01",
        "endDate": "2024-11-15",
        "terminationReason": "voluntary",
        "terminationDetail": "Burnout and frustration. Felt passed over for promotion twice. Joined a startup.",
        "regrettable": True,
        "department": "department-001",
        "team": "team-002",
        "manager": "person-019",  # Sarah Chen
        "location": "location-001",
        "salary": 142000,
        "gender": "female",
        "race": "black",
        "eeoCategory": "professionals",
        "bio": "Strong IC-3 who wanted IC-4 but was told to 'wait for the next cycle' twice. Her departure was the third regrettable loss from Engineering in 2024 — the pattern should have been caught earlier. Now at a Series B startup as a founding engineer.",
    },
    {
        "name": "Carlos Rodriguez",
        "email": "carlos.rodriguez@acmeco.com",
        "role": "Support Lead",
        "level": "M-1",
        "startDate": "2023-05-15",
        "endDate": "2025-09-01",
        "terminationReason": "voluntary",
        "terminationDetail": "Poached by enterprise SaaS company. Offered director-level role we couldn't match.",
        "regrettable": False,
        "department": "department-002",
        "team": "team-004",
        "manager": "person-023",
        "location": "location-001",
        "salary": 105000,
        "gender": "male",
        "race": "hispanic",
        "eeoCategory": "professionals",
        "bio": "Good support leader but not exceptional. The enterprise offer was a level jump we couldn't match and probably shouldn't have. His team transitioned smoothly under Ava Thompson.",
    },
]

for t in TERMINATED:
    pid = next_id("person")
    comp_id = next_id("comp")

    person_node = {
        "id": pid,
        "type": "person",
        "properties": {
            "name": t["name"],
            "email": t["email"],
            "role": t["role"],
            "level": t["level"],
            "startDate": t["startDate"],
            "endDate": t["endDate"],
            "status": "terminated",
            "terminationReason": t["terminationReason"],
            "terminationDetail": t["terminationDetail"],
            "regrettable": t["regrettable"],
            "bio": t["bio"],
            "location": t["location"],
            "gender": t["gender"],
            "race": t["race"],
            "eeoCategory": t["eeoCategory"],
            "employmentType": "full_time",
            "payType": "salary",
            "payPeriod": "biweekly",
            "flsaClassification": "exempt",
        },
    }
    new_nodes.append(person_node)

    comp_node = {
        "id": comp_id,
        "type": "comp",
        "properties": {
            "type": "salary",
            "amount": t["salary"],
            "currency": "USD",
            "effectiveDate": t["startDate"],
            "endDate": t["endDate"],
            "payPeriod": "biweekly",
        },
    }
    new_nodes.append(comp_node)

    # Standard edges
    new_edges.append(make_edge(pid, t["department"], "in_department", {}))
    dept = t["department"]
    div_map = {"department-001": "division-001", "department-002": "division-002",
               "department-003": "division-002", "department-004": "division-001",
               "department-005": "division-003", "department-006": "division-004"}
    new_edges.append(make_edge(pid, div_map.get(dept, "division-003"), "in_division", {}))
    new_edges.append(make_edge(pid, t["team"], "member_of", {"role": "individual_contributor", "startDate": t["startDate"]}))
    new_edges.append(make_edge(pid, t["manager"], "reports_to", {"startDate": t["startDate"], "isPrimary": True}))
    new_edges.append(make_edge(pid, t["location"], "located_at", {}))
    new_edges.append(make_edge(pid, comp_id, "has_comp", {"effectiveDate": t["startDate"]}))

    stats["terminated_added"] += 1

print(f"Added {stats['terminated_added']} new terminated employees")

# ─── Step 4: Assign Tiers ────────────────────────────────────────────────────

# Explicit star assignments (people we want specific narratives for)
STAR_IDS = {
    "person-008",  # Raj Patel — neglected star
    "person-007",  # Ana Kim — hidden star
    "person-006",  # Mike Torres — strong performer
    "person-009",  # Derek Lin — well-managed star (junior)
    "person-003",  # Lisa Huang — VP Eng
    "person-004",  # David Park — Eng Manager
    "person-019",  # Sarah Chen — Eng Lead
    "person-030",  # Emma Davies — Senior Designer
    "person-029",  # Kevin Tran — VP Design
    "person-001",  # Elena Voss — CEO
    "person-002",  # James Wright — COO
    "person-026",  # Rachel Foster — VP Sales
    "person-023",  # Maria Santos — VP CS
    "person-005",  # Diane Crawford — VP People
}

STAGNANT_IDS = {
    "person-037",  # Karen Washington — quiet decline
    "person-038",  # Derek Martinez — detractor
    "person-011",  # Chris Lee — invisible despite tenure
}

DECLINING_IDS = {
    "person-010",  # Sarah Okafor — isolated new hire
}

# Build tier map for all active people
tier_map = {}
non_assigned = []

for p in active_people:
    pid = p["id"]
    if pid in STAR_IDS:
        tier_map[pid] = "star"
    elif pid in STAGNANT_IDS:
        tier_map[pid] = "stagnant"
    elif pid in DECLINING_IDS:
        tier_map[pid] = "declining"
    else:
        non_assigned.append(pid)

# Distribute remaining people
random.shuffle(non_assigned)
total_remaining = len(non_assigned)
n_strong = int(total_remaining * 0.28)
n_solid = int(total_remaining * 0.50)
n_stagnant = int(total_remaining * 0.15)
n_declining = total_remaining - n_strong - n_solid - n_stagnant

for i, pid in enumerate(non_assigned):
    if i < n_strong:
        tier_map[pid] = "strong"
    elif i < n_strong + n_solid:
        tier_map[pid] = "solid"
    elif i < n_strong + n_solid + n_stagnant:
        tier_map[pid] = "stagnant"
    else:
        tier_map[pid] = "declining"

tier_counts = defaultdict(int)
for t in tier_map.values():
    tier_counts[t] += 1
print(f"Tier distribution: {dict(tier_counts)}")

# ─── Step 5: Generate Change Nodes (Comp History) ────────────────────────────

# Annual review cycles happen in December, comp changes effective January
REVIEW_CYCLES = [
    datetime(2024, 12, 15),
    datetime(2025, 12, 15),
]
COMP_EFFECTIVE_DATES = [
    datetime(2025, 1, 1),
    datetime(2026, 1, 1),
]

TIER_RAISE_RANGES = {
    "star": (0.08, 0.15),
    "strong": (0.05, 0.08),
    "solid": (0.03, 0.05),
    "stagnant": (0.01, 0.02),
    "declining": (0.00, 0.01),
}

# Level progression probabilities per cycle
TIER_PROMO_CHANCE = {
    "star": 0.40,
    "strong": 0.15,
    "solid": 0.05,
    "stagnant": 0.00,
    "declining": 0.00,
}

# Off-cycle adjustment chance (market adj, correction, etc.)
TIER_OFFCYCLE_CHANCE = {
    "star": 0.30,
    "strong": 0.10,
    "solid": 0.02,
    "stagnant": 0.00,
    "declining": 0.00,
}

LEVEL_ORDER = ["IC-1", "IC-2", "IC-3", "IC-4", "IC-5", "M-1", "M-2", "M-3", "C-1"]

# Level band lookup
LEVEL_BANDS = {}
for lv in LEVELS:
    LEVEL_BANDS[lv["code"]] = (lv["salary_band_min"], lv["salary_band_max"], lv["salary_band_mid"])


def next_level_for(current_level):
    """Get the next level up, handling IC->M crossover at IC-3/IC-4."""
    if current_level in level_progression:
        return level_progression[current_level]
    return None


# Special handling for specific narrative people
FORCE_PROMO = {
    # (person_id, cycle_index): (from_level, to_level)
    ("person-008", 0): ("M-1", "M-1"),  # Raj — no promo despite deserving one (narrative: neglected)
    ("person-007", 1): None,  # Ana — promotion pending but not yet happened
}

FORCE_NO_RAISE = {
    "person-008",  # Raj — comp frozen (core narrative)
}


for p in active_people:
    pid = p["id"]
    tier = tier_map.get(pid, "solid")
    current_level = p["properties"].get("level", "IC-2")
    start_date = datetime.strptime(p["properties"]["startDate"], "%Y-%m-%d")
    comp_node = person_to_comp.get(pid)

    if not comp_node:
        continue

    current_salary = comp_node["properties"].get("amount", 80000)
    original_salary = current_salary

    for cycle_idx, (review_date, comp_date) in enumerate(zip(REVIEW_CYCLES, COMP_EFFECTIVE_DATES)):
        # Skip if person wasn't employed yet
        if start_date > review_date - timedelta(days=90):
            continue

        # Skip Raj's raises (narrative: frozen comp)
        if pid in FORCE_NO_RAISE:
            continue

        # --- Comp change ---
        low, high = TIER_RAISE_RANGES[tier]
        raise_pct = random.uniform(low, high)
        new_salary = round(current_salary * (1 + raise_pct), -2)  # Round to nearest 100

        if new_salary != current_salary:
            change_id = next_id("change")
            reason = "annual_review"
            if raise_pct >= 0.10:
                reason = "merit"

            new_nodes.append({
                "id": change_id,
                "type": "change",
                "properties": {
                    "field": "salary",
                    "from": str(int(current_salary)),
                    "to": str(int(new_salary)),
                    "effectiveDate": date_str(comp_date),
                    "reason": reason,
                },
            })
            new_edges.append(make_edge(pid, change_id, "has_change", {}, ts(comp_date)))
            stats["comp_changes"] += 1
            current_salary = new_salary

        # --- Level change (promotion) ---
        promo_chance = TIER_PROMO_CHANCE[tier]

        # Don't promote C-suite or IC-5
        if current_level in ("C-1", "IC-5"):
            promo_chance = 0

        # Don't promote people with < 1 year tenure at current level
        if start_date > review_date - timedelta(days=365) and cycle_idx == 0:
            promo_chance *= 0.3

        if random.random() < promo_chance:
            new_level = next_level_for(current_level)
            if new_level:
                change_id = next_id("change")
                new_nodes.append({
                    "id": change_id,
                    "type": "change",
                    "properties": {
                        "field": "level",
                        "from": current_level,
                        "to": new_level,
                        "effectiveDate": date_str(comp_date),
                        "reason": "promotion",
                    },
                })
                new_edges.append(make_edge(pid, change_id, "has_change", {}, ts(comp_date)))
                stats["level_changes"] += 1

                # Also bump comp to at least new band minimum
                band_min, band_max, band_mid = LEVEL_BANDS.get(new_level, (current_salary, current_salary * 1.3, current_salary * 1.15))
                if current_salary < band_min:
                    promo_salary = round(random.uniform(band_min, band_mid), -2)
                    change_id = next_id("change")
                    new_nodes.append({
                        "id": change_id,
                        "type": "change",
                        "properties": {
                            "field": "salary",
                            "from": str(int(current_salary)),
                            "to": str(int(promo_salary)),
                            "effectiveDate": date_str(comp_date),
                            "reason": "promotion",
                        },
                    })
                    new_edges.append(make_edge(pid, change_id, "has_change", {}, ts(comp_date)))
                    stats["comp_changes"] += 1
                    current_salary = promo_salary

                current_level = new_level

    # --- Off-cycle adjustments (mid-year, market, etc.) ---
    offcycle_chance = TIER_OFFCYCLE_CHANCE[tier]
    if pid not in FORCE_NO_RAISE and random.random() < offcycle_chance:
        # Random date in the middle of the year
        offcycle_date = datetime(2025, random.randint(4, 9), random.randint(1, 28))
        if start_date < offcycle_date:
            adj_pct = random.uniform(0.03, 0.08)
            adj_salary = round(current_salary * (1 + adj_pct), -2)
            reasons = ["market_adjustment", "merit", "correction"]
            change_id = next_id("change")
            new_nodes.append({
                "id": change_id,
                "type": "change",
                "properties": {
                    "field": "salary",
                    "from": str(int(current_salary)),
                    "to": str(int(adj_salary)),
                    "effectiveDate": date_str(offcycle_date),
                    "reason": random.choice(reasons),
                },
            })
            new_edges.append(make_edge(pid, change_id, "has_change", {}, ts(offcycle_date)))
            stats["offcycle_changes"] += 1

# Also add change history for terminated people who had tenure
for t in TERMINATED:
    pid = f"person-{_counters['person'] - len(TERMINATED) + TERMINATED.index(t)}"
    # Find the actual ID we assigned
    for nn in new_nodes:
        if nn["type"] == "person" and nn["properties"]["name"] == t["name"]:
            pid = nn["id"]
            break

    start = datetime.strptime(t["startDate"], "%Y-%m-%d")
    end = datetime.strptime(t["endDate"], "%Y-%m-%d")
    tenure_years = (end - start).days / 365.25

    if tenure_years >= 1.0:
        # At least one annual cycle
        for comp_date in COMP_EFFECTIVE_DATES:
            if start < comp_date - timedelta(days=90) and end > comp_date:
                # Was employed during this cycle
                raise_pct = random.uniform(0.03, 0.08)
                old_sal = t["salary"]
                new_sal = round(old_sal * (1 + raise_pct), -2)
                change_id = next_id("change")
                new_nodes.append({
                    "id": change_id,
                    "type": "change",
                    "properties": {
                        "field": "salary",
                        "from": str(int(old_sal)),
                        "to": str(int(new_sal)),
                        "effectiveDate": date_str(comp_date),
                        "reason": "annual_review",
                    },
                })
                new_edges.append(make_edge(pid, change_id, "has_change", {}, ts(comp_date)))
                stats["terminated_comp_changes"] += 1

print(f"Change nodes: {stats['comp_changes']} comp, {stats['level_changes']} level, {stats['offcycle_changes']} off-cycle, {stats['terminated_comp_changes']} terminated")

# ─── Step 6: Generate Reviews ────────────────────────────────────────────────

# Self-assessment and manager-assessment templates by tier
SELF_ASSESSMENTS = {
    "star": [
        "I've taken on significantly more scope this year. Leading {project} while mentoring two junior engineers has been rewarding but I'm starting to feel the edges of what I can sustain. I'd like to talk about what's next for me here.",
        "This has been my strongest year. I shipped {project} ahead of schedule and the cross-team work has been energizing. I'm ready for more responsibility and think I've demonstrated the impact to back that up.",
        "I'm proud of what I've delivered but I'm being honest — the workload isn't sustainable long-term. I need either more support or a clearer path to the next level so I can focus.",
        "I feel like I'm operating above my level. The work I'm doing on {project} has org-wide impact and I'd like my title and comp to reflect that.",
    ],
    "strong": [
        "Good year overall. I've grown a lot technically and I'm starting to take on more ownership. I'd like to work toward a senior role in the next year.",
        "I feel confident in my core work and I've started contributing beyond my immediate team. The {project} collaboration was a highlight.",
        "I've hit my goals and I'm looking for the next challenge. I'm interested in taking on a mentoring role or leading a workstream.",
    ],
    "solid": [
        "I feel settled in my role and I'm delivering consistently. No major concerns — I'd like to keep building depth in my current area.",
        "This year was steady. I met my commitments and I'm comfortable with the pace. I'd appreciate more feedback on where I can improve.",
        "I'm doing good work and I feel supported by my team. I'm not looking for a change right now, just want to keep executing well.",
    ],
    "stagnant": [
        "I'm not sure where I stand. I've been doing the same work for a while and I haven't had a conversation about growth in over a year. I'd like some clarity.",
        "Honestly, I feel stuck. The work is fine but there's no path forward that I can see. I'd like to talk about what options exist.",
        "I'm getting the job done but I'm not growing. I need more challenge or a change of some kind.",
    ],
    "declining": [
        "This has been a tough stretch. I'm struggling with the workload and I don't feel like I have the support I need. I want to do better but I need help.",
        "I know my performance hasn't been where it needs to be. I'm dealing with some personal stuff and I'm trying to get back on track.",
    ],
}

MANAGER_ASSESSMENTS = {
    "star": [
        "{name} continues to be one of our highest-impact contributors. Their work on {project} demonstrates IC-4+ level thinking. I'm concerned about burnout — they're carrying too much. We need to promote and retain.",
        "{name} is operating above level. Cross-team influence, mentoring, and technical leadership are all strong. The gap between their impact and their title/comp is my biggest concern.",
        "{name} delivered exceptional results this cycle. They're the kind of person other teams request by name. We risk losing them if we don't act on the promotion case.",
        "{name} is indispensable to the team's success. They've absorbed extra work without complaint but I can see the strain. Promotion and comp adjustment are overdue.",
    ],
    "strong": [
        "{name} had a strong year. Consistently reliable, growing in scope, and starting to influence beyond their immediate work. On track for next-level in 12-18 months.",
        "{name} is developing well. They've taken on more ownership and their technical judgment is improving. I'd like to give them a stretch project next quarter.",
        "{name} meets expectations and then some. Not quite ready for promotion but clearly trending up. Comp should reflect their trajectory.",
    ],
    "solid": [
        "{name} is a reliable contributor. Meets expectations consistently. No concerns, no urgent development needs. Good team player.",
        "{name} delivers solid work. I'd like to see more initiative on cross-team problems but their core execution is dependable.",
        "{name} is steady and trustworthy. They do what's asked, do it well, and don't create drama. Not every performer needs to be a star.",
    ],
    "stagnant": [
        "{name} is meeting minimum expectations but hasn't grown in the past year. I haven't invested enough 1:1 time here — that's on me. We need a development plan.",
        "{name} is capable of more than they're showing. I think the role has become routine for them. Need to discuss either a lateral move or new challenges.",
        "{name}'s work is acceptable but flat. Same output, same scope, no evolution. I need to have a candid conversation about expectations.",
    ],
    "declining": [
        "{name} has struggled this cycle. Output has dropped and there are quality concerns. I've started weekly check-ins. If we don't see improvement in 60 days, we'll need to discuss a PIP.",
        "{name} is underperforming relative to their level. I believe some of this is situational but we need a clear turnaround plan. I want to support them but I also need accountability.",
    ],
}

RATING_BY_TIER = {
    "star": ["exceeds", "exceeds", "exceeds", "meets"],  # Mostly exceeds, occasional meets
    "strong": ["exceeds", "meets", "meets", "meets"],
    "solid": ["meets", "meets", "meets"],
    "stagnant": ["meets", "meets", "needs_improvement"],
    "declining": ["needs_improvement", "needs_improvement", "meets"],
}

# Existing reviews (don't duplicate)
existing_review_people = set()
for e in edges:
    if e["type"] == "has_review":
        existing_review_people.add(e["source"])

# Get project names for templates
project_names = {}
for n in nodes:
    if n["type"] == "project":
        project_names[n["id"]] = n["properties"].get("name", "the project")

# Person to project mapping
person_projects = defaultdict(list)
for e in edges:
    if e["type"] == "works_on":
        pname = project_names.get(e["target"], "cross-team initiatives")
        person_projects[e["source"]].append(pname)

for p in active_people:
    pid = p["id"]
    tier = tier_map.get(pid, "solid")
    name = p["properties"]["name"].split()[0]  # First name
    full_name = p["properties"]["name"]
    start_date = datetime.strptime(p["properties"]["startDate"], "%Y-%m-%d")
    manager_id = person_to_manager.get(pid)

    # Get a project name for templates
    projects = person_projects.get(pid, ["their core work"])
    project = projects[0] if projects else "their core work"

    for cycle_idx, review_date in enumerate(REVIEW_CYCLES):
        # Skip if not employed 90+ days before review
        if start_date > review_date - timedelta(days=90):
            continue

        # Skip if already has a review near this date
        if pid in existing_review_people and cycle_idx == 1:
            continue

        review_id = next_id("review")
        rating = random.choice(RATING_BY_TIER.get(tier, ["meets"]))

        self_templates = SELF_ASSESSMENTS.get(tier, SELF_ASSESSMENTS["solid"])
        mgr_templates = MANAGER_ASSESSMENTS.get(tier, MANAGER_ASSESSMENTS["solid"])

        self_text = random.choice(self_templates).format(project=project, name=full_name)
        mgr_text = random.choice(mgr_templates).format(project=project, name=full_name)

        review_node = {
            "id": review_id,
            "type": "review",
            "properties": {
                "type": "annual",
                "status": "completed",
                "scheduledDate": date_str(review_date),
                "completedDate": date_str(review_date + timedelta(days=random.randint(1, 14))),
                "rating": rating,
                "selfAssessment": self_text,
                "managerAssessment": mgr_text,
            },
        }
        new_nodes.append(review_node)

        metadata = {"period": f"annual_{review_date.year}"}
        if manager_id:
            metadata["reviewerId"] = manager_id
        new_edges.append(make_edge(pid, review_id, "has_review", metadata, ts(review_date)))
        stats["reviews_added"] += 1

# Also enrich existing review nodes with self/manager assessments
for n in nodes:
    if n["type"] == "review" and "selfAssessment" not in n["properties"]:
        # Find who this review is for
        review_person = None
        for e in edges:
            if e["type"] == "has_review" and e["target"] == n["id"]:
                review_person = e["source"]
                break
        if review_person:
            tier = tier_map.get(review_person, "solid")
            person_name = node_by_id.get(review_person, {}).get("properties", {}).get("name", "This person")
            first_name = person_name.split()[0]
            projects = person_projects.get(review_person, ["their core work"])
            project = projects[0]

            self_text = random.choice(SELF_ASSESSMENTS.get(tier, SELF_ASSESSMENTS["solid"])).format(
                project=project, name=person_name
            )
            mgr_text = random.choice(MANAGER_ASSESSMENTS.get(tier, MANAGER_ASSESSMENTS["solid"])).format(
                project=project, name=person_name
            )
            n["properties"]["selfAssessment"] = self_text
            n["properties"]["managerAssessment"] = mgr_text
            stats["reviews_enriched"] += 1

print(f"Reviews: {stats['reviews_added']} new, {stats['reviews_enriched']} enriched with self/manager assessments")

# ─── Step 7: Add More Survey Rounds ──────────────────────────────────────────

# Add 4 historical survey rounds: Q2'24, Q3'24, Q4'24, Q2'25
# Each round has ~30-40% response rate (realistic)
SURVEY_ROUNDS = [
    {"date": "2024-06-15", "label": "Q2 2024"},
    {"date": "2024-09-15", "label": "Q3 2024"},
    {"date": "2024-12-15", "label": "Q4 2024"},
    {"date": "2025-06-15", "label": "Q2 2025"},
]

# Department eNPS trends (to make aggregate patterns visible)
# Engineering: crisis Q3-Q4'24 (lost 3 people), recovering
# CS: steady improvement
# Sales: flat
# Design: happy
DEPT_ENPS_TREND = {
    "department-001": [7.5, 5.0, 4.5, 6.5],  # Eng: good, crash, bottom, recovering
    "department-002": [5.5, 6.0, 6.5, 7.0],  # CS: steady climb
    "department-003": [6.0, 6.0, 5.5, 6.0],  # Sales: flat
    "department-004": [8.0, 8.0, 7.5, 8.5],  # Design: happy
    "department-005": [6.5, 6.5, 6.0, 6.5],  # Ops: steady
    "department-006": [7.0, 7.0, 7.0, 7.0],  # Exec: stable
}

for round_idx, survey_round in enumerate(SURVEY_ROUNDS):
    round_date = survey_round["date"]

    # Select ~35% of active people who were employed at that time
    eligible = [p for p in active_people
                if datetime.strptime(p["properties"]["startDate"], "%Y-%m-%d") < datetime.strptime(round_date, "%Y-%m-%d") - timedelta(days=30)]

    respondents = random.sample(eligible, min(len(eligible), int(len(eligible) * random.uniform(0.30, 0.40))))

    for p in respondents:
        pid = p["id"]
        dept = person_to_dept.get(pid, "department-001")
        dept_avg = DEPT_ENPS_TREND.get(dept, [6.0, 6.0, 6.0, 6.0])[round_idx]

        # Individual score varies around department average
        tier = tier_map.get(pid, "solid")
        tier_offset = {"star": 1.5, "strong": 0.5, "solid": 0, "stagnant": -1.5, "declining": -2.5}
        base_score = dept_avg + tier_offset.get(tier, 0) + random.uniform(-1.5, 1.5)
        enps_score = max(0, min(10, round(base_score)))

        survey_id = next_id("review")  # reusing counter, but different type
        survey_id = f"survey-{_counters['review']:03d}"
        _counters["review"] += 1

        # eNPS response
        survey_node = {
            "id": survey_id,
            "type": "survey_response",
            "properties": {
                "surveyType": "eNPS",
                "question": "How likely are you to recommend working here to a friend?",
                "score": enps_score,
                "date": round_date,
                "period": survey_round["label"],
                "sentiment": "promoter" if enps_score >= 9 else "passive" if enps_score >= 7 else "detractor",
            },
        }
        new_nodes.append(survey_node)
        new_edges.append(make_edge(pid, survey_id, "responded_to", {}, ts(datetime.strptime(round_date, "%Y-%m-%d"))))
        stats["surveys_added"] += 1

print(f"Surveys: {stats['surveys_added']} new responses across {len(SURVEY_ROUNDS)} rounds")

# ─── Save ────────────────────────────────────────────────────────────────────

nodes.extend(new_nodes)
edges.extend(new_edges)

with open("data/nodes.json", "w") as f:
    json.dump({"nodes": nodes}, f, indent=2)
with open("data/edges.json", "w") as f:
    json.dump({"edges": edges}, f, indent=2)
with open("data/schema.json", "w") as f:
    json.dump(schema, f, indent=2)

print(f"\n── Summary ──")
print(f"Total nodes: {len(nodes)}")
print(f"Total edges: {len(edges)}")
print(f"New nodes: {len(new_nodes)}")
print(f"New edges: {len(new_edges)}")
