#!/usr/bin/env python3
"""
Temporal Data Backfill for Employee Graph

Adds 18 months of historical depth:
- 8 terminated employees with full edge sets
- 4 historical survey rounds (Q2'24 through Q1'25)
- Dec 2024 annual review cycle
- Promotions, transfers, manager changes
- in_department metadata backfill

Run: python3 data/backfill-temporal.py
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
comp_nodes = {n["id"]: n for n in nodes if n["type"] == "comp"}
position_nodes = {n["id"]: n for n in nodes if n["type"] == "position"}

# Department mapping
person_to_dept = {}
person_to_div = {}
for e in edges:
    if e["type"] == "in_department":
        person_to_dept[e["source"]] = e["target"]
    elif e["type"] == "in_division":
        person_to_div[e["source"]] = e["target"]

dept_names = {}
for n in nodes:
    if n["type"] == "department":
        dept_names[n["id"]] = n["properties"]["name"]

# Department -> Division mapping
DEPT_DIV = {
    "department-001": "division-001",  # Engineering
    "department-002": "division-002",  # Customer Support
    "department-003": "division-002",  # Sales
    "department-004": "division-001",  # Design
    "department-005": "division-003",  # Operations
    "department-006": "division-004",  # Executive
}

# People by department
dept_people = defaultdict(list)
for n in person_nodes:
    pid = n["id"]
    dept = person_to_dept.get(pid)
    if dept:
        dept_people[dept].append(n)

# Comp by person
person_comp = {}
for e in edges:
    if e["type"] == "has_comp":
        person_comp[e["source"]] = e["target"]

# ─── ID Generators ────────────────────────────────────────────────────────────

_counters = {
    "person": 149,
    "comp": 159,
    "survey": 21,
    "review": 7,
    "cobra": 3,
    "position": 50,
}


def next_id(prefix):
    n = _counters[prefix]
    _counters[prefix] = n + 1
    return f"{prefix}-{n:03d}"


def make_edge(source, target, etype, metadata):
    """Create edge dict matching the bulk-add pattern (no id, no timestamp)."""
    return {"source": source, "target": target, "type": etype, "metadata": metadata}


# Collectors for new data
new_nodes = []
new_edges = []
stats = defaultdict(int)

# ─── Step 0: Schema Updates ──────────────────────────────────────────────────

schema["nodeTypes"]["person"]["properties"]["terminationReason"] = {
    "type": "string",
    "enum": ["voluntary", "involuntary"],
    "required": False,
    "description": "Reason for termination",
}
schema["nodeTypes"]["person"]["properties"]["terminationDetail"] = {
    "type": "string",
    "required": False,
    "description": "Specific termination details: joined competitor, burnout, etc.",
}
schema["nodeTypes"]["person"]["properties"]["regrettable"] = {
    "type": "boolean",
    "required": False,
    "description": "Whether the departure was regrettable — knowledge or relationship loss",
}
print("Schema: added terminationReason, terminationDetail, regrettable to person")

# ─── Step 1: Terminated Employees ────────────────────────────────────────────

TERMINATED = [
    {
        "id": "person-149",
        "name": "Marcus Cole",
        "email": "marcus.cole@acmeco.com",
        "role": "Senior Engineer",
        "level": "IC-4",
        "startDate": "2022-06-15",
        "endDate": "2024-08-30",
        "terminationReason": "voluntary",
        "terminationDetail": "Joined competitor",
        "regrettable": True,
        "department": "department-001",
        "team": "team-002",
        "manager": "person-004",
        "location": "location-001",
        "salary": 162000,
        "gender": "male",
        "race": "white",
        "eeoCategory": "professionals",
        "bio": "Top performer. Deep platform knowledge. Left for competitor offer. Departure triggered workload crisis in Product Engineering.",
    },
    {
        "id": "person-150",
        "name": "Priya Desai",
        "email": "priya.desai@acmeco.com",
        "role": "Engineer",
        "level": "IC-2",
        "startDate": "2023-01-10",
        "endDate": "2024-10-15",
        "terminationReason": "voluntary",
        "terminationDetail": "Burnout",
        "regrettable": True,
        "department": "department-001",
        "team": "team-002",
        "manager": "person-019",
        "location": "location-001",
        "salary": 98000,
        "gender": "female",
        "race": "asian",
        "eeoCategory": "professionals",
        "bio": "Strong contributor. Departure was preventable with workload management. Second Engineering loss in 2 months.",
    },
    {
        "id": "person-151",
        "name": "Tyler Morrison",
        "email": "tyler.morrison@acmeco.com",
        "role": "Tech Lead",
        "level": "M-1",
        "startDate": "2021-03-20",
        "endDate": "2024-11-22",
        "terminationReason": "voluntary",
        "terminationDetail": "Startup opportunity",
        "regrettable": True,
        "department": "department-001",
        "team": "team-015",
        "manager": "person-002",
        "location": "location-001",
        "salary": 178000,
        "gender": "male",
        "race": "white",
        "eeoCategory": "first_mid_officials",
        "bio": "Led Horizon scrum team. 3.5 years institutional knowledge walked out the door. Third Engineering loss in Q3-Q4 2024.",
    },
    {
        "id": "person-152",
        "name": "Kenji Watanabe",
        "email": "kenji.watanabe@acmeco.com",
        "role": "Support Specialist",
        "level": "IC-2",
        "startDate": "2022-09-01",
        "endDate": "2024-06-15",
        "terminationReason": "voluntary",
        "terminationDetail": "Career change to teaching",
        "regrettable": False,
        "department": "department-002",
        "team": "team-004",
        "manager": "person-042",
        "location": "location-001",
        "salary": 52000,
        "gender": "male",
        "race": "asian",
        "eeoCategory": "admin_support",
        "bio": "Average performer. Natural career transition to education. Departure was expected.",
    },
    {
        "id": "person-153",
        "name": "Brianna Foster",
        "email": "brianna.foster@acmeco.com",
        "role": "Support Team Lead",
        "level": "IC-3",
        "startDate": "2021-11-15",
        "endDate": "2024-04-30",
        "terminationReason": "involuntary",
        "terminationDetail": "Performance — consistent underperformance, multiple coaching attempts",
        "regrettable": False,
        "department": "department-002",
        "team": "team-004",
        "manager": "person-005",
        "location": "location-001",
        "salary": 65000,
        "gender": "female",
        "race": "black",
        "eeoCategory": "admin_support",
        "bio": "Consistent underperformance despite multiple coaching attempts. Involuntary separation.",
    },
    {
        "id": "person-154",
        "name": "Derek Novak",
        "email": "derek.novak@acmeco.com",
        "role": "Account Executive",
        "level": "IC-3",
        "startDate": "2023-03-01",
        "endDate": "2025-07-18",
        "terminationReason": "voluntary",
        "terminationDetail": "Relocated out of state",
        "regrettable": True,
        "department": "department-003",
        "team": "team-005",
        "manager": "person-021",
        "location": "location-001",
        "salary": 115000,
        "gender": "male",
        "race": "white",
        "eeoCategory": "sales_workers",
        "bio": "Strong pipeline. Client relationships walked out the door. Relocated to Portland.",
    },
    {
        "id": "person-155",
        "name": "Megan Hartley",
        "email": "megan.hartley@acmeco.com",
        "role": "HR Coordinator",
        "level": "IC-2",
        "startDate": "2023-06-01",
        "endDate": "2025-02-28",
        "terminationReason": "involuntary",
        "terminationDetail": "Role eliminated in restructuring",
        "regrettable": False,
        "department": "department-005",
        "team": "team-007",
        "manager": "person-022",
        "location": "location-001",
        "salary": 55000,
        "gender": "female",
        "race": "white",
        "eeoCategory": "admin_support",
        "bio": "Role eliminated during ops restructuring. Not performance-related. Good terms.",
    },
    {
        "id": "person-156",
        "name": "Alex Romero",
        "email": "alex.romero@acmeco.com",
        "role": "QA Engineer",
        "level": "IC-3",
        "startDate": "2022-08-15",
        "endDate": "2025-01-10",
        "terminationReason": "voluntary",
        "terminationDetail": "Left for graduate school",
        "regrettable": False,
        "department": "department-001",
        "team": "team-003",
        "manager": "person-023",
        "location": "location-003",
        "salary": 88000,
        "gender": "male",
        "race": "hispanic",
        "eeoCategory": "professionals",
        "bio": "Planned departure for grad school. Good terms, may return. Solid QA contributor.",
    },
]

# Find or create position for a terminated person
def find_position(title, level, dept_name):
    """Find existing position matching title+level, or create one."""
    for pid, p in position_nodes.items():
        props = p["properties"]
        if props.get("title") == title and props.get("level") == level:
            return pid
    # Create new position
    pos_id = next_id("position")
    pos_node = {
        "id": pos_id,
        "type": "position",
        "properties": {
            "title": title,
            "level": level,
            "department": dept_name,
            "jobFamily": dept_name,
            "isOpen": False,
        },
    }
    new_nodes.append(pos_node)
    position_nodes[pos_id] = pos_node
    return pos_id


for tp in TERMINATED:
    dept_name = dept_names[tp["department"]]
    div_id = DEPT_DIV[tp["department"]]

    # Person node
    person_node = {
        "id": tp["id"],
        "type": "person",
        "properties": {
            "name": tp["name"],
            "email": tp["email"],
            "role": tp["role"],
            "level": tp["level"],
            "startDate": tp["startDate"],
            "endDate": tp["endDate"],
            "status": "terminated",
            "location": "Austin, TX" if tp["location"] == "location-001" else "Denver, CO",
            "flsaClassification": "exempt",
            "eeoCategory": tp["eeoCategory"],
            "gender": tp["gender"],
            "race": tp["race"],
            "veteranStatus": "not_veteran",
            "employmentType": "full_time",
            "payType": "salary",
            "payPeriod": "semimonthly",
            "terminationReason": tp["terminationReason"],
            "terminationDetail": tp["terminationDetail"],
            "regrettable": tp["regrettable"],
            "bio": tp["bio"],
        },
    }
    new_nodes.append(person_node)
    stats["terminated_people"] += 1

    # Comp node
    comp_id = next_id("comp")
    new_nodes.append(
        {
            "id": comp_id,
            "type": "comp",
            "properties": {
                "type": "salary",
                "amount": tp["salary"],
                "currency": "USD",
                "effectiveDate": tp["startDate"],
                "endDate": tp["endDate"],
            },
        }
    )
    stats["comp_nodes"] += 1

    # Position
    pos_id = find_position(tp["role"], tp["level"], dept_name)

    # COBRA event
    cobra_id = next_id("cobra")
    evt_dt = datetime.strptime(tp["endDate"], "%Y-%m-%d")
    notice_dl = (evt_dt + timedelta(days=14)).strftime("%Y-%m-%d")
    election_dl = (evt_dt + timedelta(days=74)).strftime("%Y-%m-%d")
    # Old terminations: lapsed. Recent ones: waived or elected.
    if evt_dt < datetime(2025, 1, 1):
        cobra_status = "lapsed"
    elif evt_dt < datetime(2025, 6, 1):
        cobra_status = "waived"
    else:
        cobra_status = "waived"

    new_nodes.append(
        {
            "id": cobra_id,
            "type": "cobra_event",
            "properties": {
                "qualifyingEvent": "termination",
                "eventDate": tp["endDate"],
                "noticeDeadline": notice_dl,
                "electionDeadline": election_dl,
                "status": cobra_status,
                "monthlyPremium": 918,
            },
        }
    )
    stats["cobra_events"] += 1

    # Edges for this terminated person
    end = tp["endDate"]
    start = tp["startDate"]

    new_edges.extend(
        [
            make_edge(
                tp["id"],
                tp["manager"],
                "reports_to",
                {"startDate": start, "endDate": end, "isPrimary": True},
            ),
            make_edge(
                tp["id"],
                tp["team"],
                "member_of",
                {
                    "role": "lead" if tp["level"] == "M-1" else "individual_contributor",
                    "startDate": start,
                    "endDate": end,
                },
            ),
            make_edge(
                tp["id"],
                tp["department"],
                "in_department",
                {"startDate": start, "endDate": end},
            ),
            make_edge(
                tp["id"],
                div_id,
                "in_division",
                {"startDate": start, "endDate": end},
            ),
            make_edge(
                tp["id"],
                pos_id,
                "holds_position",
                {"startDate": start, "endDate": end, "status": "previous"},
            ),
            make_edge(
                tp["id"],
                tp["location"],
                "located_at",
                {"type": "primary", "startDate": start},
            ),
            make_edge(
                tp["id"],
                comp_id,
                "has_comp",
                {"effectiveDate": start},
            ),
            make_edge(tp["id"], cobra_id, "has_cobra_event", {}),
        ]
    )
    stats["terminated_edges"] += 8

    # Add to lookup so surveys/reviews can find them
    node_by_id[tp["id"]] = person_node
    person_to_dept[tp["id"]] = tp["department"]
    person_to_div[tp["id"]] = div_id

print(f"Step 1: Added {stats['terminated_people']} terminated people, {stats['comp_nodes']} comp, {stats['cobra_events']} COBRA events")

# ─── Step 2: Historical Survey Rounds ────────────────────────────────────────

SURVEY_ROUNDS = [
    {"date": "2024-04-20", "label": "Q2 2024"},
    {"date": "2024-07-20", "label": "Q3 2024"},
    {"date": "2024-10-20", "label": "Q4 2024"},
    {"date": "2025-04-20", "label": "Q1 2025"},
]

# eNPS score ranges by department per round
# Format: (min, max) for random.randint
ENPS_RANGES = {
    "department-001": [  # Engineering: 40→10→35
        (7, 9),   # Q2'24 — healthy
        (5, 7),   # Q3'24 — dipping
        (3, 6),   # Q4'24 — bottom
        (6, 8),   # Q1'25 — recovering
    ],
    "department-002": [  # Customer Support: 15→30
        (5, 7),   # Q2'24 — mediocre
        (5, 7),   # Q3'24 — still low
        (6, 7),   # Q4'24 — improving
        (7, 8),   # Q1'25 — getting better
    ],
    "department-003": [  # Sales: flat ~20
        (6, 7),
        (6, 7),
        (6, 7),
        (6, 7),
    ],
    "department-004": [  # Design: consistently happy ~50+
        (8, 10),
        (8, 10),
        (8, 10),
        (8, 10),
    ],
    "department-005": [  # Operations: flat ~25
        (6, 8),
        (6, 8),
        (6, 8),
        (6, 8),
    ],
}

# Comment templates by department and sentiment
ENPS_COMMENTS = {
    "department-001": {
        "promoter": [
            "Love the engineering culture. Great autonomy and interesting problems.",
            "Team is strong. We're shipping fast and the tech stack is solid.",
            "Best engineering org I've worked in. Smart people, good leadership.",
            "Really enjoy the technical challenges here. Feels like we're building something that matters.",
            "Great team dynamics. Collaboration is strong across squads.",
        ],
        "neutral": [
            "Engineering is decent but workload is creeping up since departures.",
            "Things are OK. Missing some key people. New hires are ramping but slowly.",
            "Cautiously optimistic. Recovery is real but we're not back to where we were.",
            "Team is rebuilding. Not bad, not great. Need more senior hires.",
            "Mixed feelings. The work is good but we're spread thin.",
        ],
        "detractor": [
            "We lost three key people in 4 months and haven't backfilled. I'm doing the work of two.",
            "Morale is tanking. Workload is unsustainable since Marcus and Priya left.",
            "No career growth path. Same level for 18 months, no conversation about what's next.",
            "Burned out. On-call rotation is brutal with the team this small.",
            "Starting to look elsewhere. The workload crisis isn't being addressed.",
        ],
    },
    "department-002": {
        "promoter": [
            "New processes are working. Team feels more organized and supported.",
            "Rachel's leadership changes are making a real difference.",
            "Support team is improving. Better tooling, better processes.",
            "Feeling more valued. Leadership is actually listening now.",
        ],
        "neutral": [
            "Support is OK. Some improvements but still understaffed.",
            "Things are getting better slowly. Workload still heavy.",
            "Decent place. Could use better tooling — too much manual work.",
            "Company is fine. More transparency from leadership would help.",
        ],
        "detractor": [
            "Support is understaffed and underappreciated. Engineering gets all the recognition.",
            "Queue times are terrible. Customers are frustrated and so are we.",
            "Feeling burned out. Haven't taken a real vacation in months.",
            "Workload is unsustainable. We lost two people and haven't backfilled.",
        ],
    },
    "department-003": {
        "promoter": [
            "Sales team is great. Clear targets and good leadership.",
            "Rachel is a strong leader. We know what's expected.",
        ],
        "neutral": [
            "Sales is fine. Targets are reasonable. Nothing exciting.",
            "Decent team. Wish we had better tooling for prospecting.",
            "Could use more product marketing support but overall OK.",
        ],
        "detractor": [
            "Pipeline feels stagnant. Need better inbound leads.",
            "Compensation model needs work. Commission structure isn't competitive.",
        ],
    },
    "department-004": {
        "promoter": [
            "Love the creative environment. Kevin gives us real ownership.",
            "Best design team I've been on. Collaborative and empowering.",
            "Design team is collaborative and creative. Great autonomy.",
            "Incredible team. We ship beautiful work and leadership trusts us.",
        ],
        "neutral": [
            "Design is good. Small team means lots of context switching though.",
        ],
        "detractor": [],  # Design rarely has detractors
    },
    "department-005": {
        "promoter": [
            "Ops is stable and well-run. Good work-life balance.",
            "Diane runs a tight ship. I always know what's expected.",
        ],
        "neutral": [
            "Operations is steady. Nothing exciting or terrible.",
            "Good stability. Wish there was more room for growth.",
            "Fine place to work. Processes are solid.",
        ],
        "detractor": [
            "Feeling like operations is an afterthought. Engineering gets all the budget.",
        ],
    },
}

WELLBEING_COMMENTS = {
    "good": [
        "Work-life balance is solid. Feeling good about things.",
        "Managing well. Team is supportive and workload is reasonable.",
        "Feeling energized by the work. Good balance overall.",
    ],
    "ok": [
        "Getting by. Some weeks are heavier than others.",
        "Work-life balance could be better but it's manageable.",
        "Neutral. Not burning out but not thriving either.",
    ],
    "bad": [
        "Feeling stretched thin across too many projects. Not sustainable.",
        "Stress level is high. Working late most nights.",
        "Struggling with work-life balance. On-call rotation is brutal.",
        "Burning out. Haven't taken real time off in months.",
        "Feeling isolated. Working solo with little mentorship.",
    ],
}


def get_sentiment(score):
    if score >= 9:
        return "promoter"
    elif score >= 7:
        return "neutral"
    else:
        return "detractor"


def was_employed(person_node, date_str):
    """Check if person was employed on a given date."""
    props = person_node["properties"]
    start = props.get("startDate", "2099-01-01")
    end = props.get("endDate")
    if start > date_str:
        return False
    if end and end < date_str:
        return False
    return True


def has_enough_tenure(person_node, date_str, min_days=90):
    """Check if person had at least min_days tenure by date."""
    start = datetime.strptime(person_node["properties"]["startDate"], "%Y-%m-%d")
    dt = datetime.strptime(date_str, "%Y-%m-%d")
    return (dt - start).days >= min_days


# Build pool of all people (including newly added terminated ones)
all_people = list(person_nodes)  # existing
for n in new_nodes:
    if n["type"] == "person":
        all_people.append(n)


for round_idx, round_info in enumerate(SURVEY_ROUNDS):
    survey_date = round_info["date"]
    round_label = round_info["label"]

    # Get eligible people per department
    eligible_by_dept = defaultdict(list)
    for p in all_people:
        if p["properties"].get("status") in ("active", "terminated"):
            if was_employed(p, survey_date) and has_enough_tenure(p, survey_date, 60):
                dept = person_to_dept.get(p["id"])
                if dept and dept != "department-006":  # Skip executive
                    eligible_by_dept[dept].append(p)

    # Select respondents: proportional to dept size, ~14 eNPS + 5 wellbeing
    enps_target = {
        "department-001": 6,  # Eng
        "department-002": 3,  # CS
        "department-003": 2,  # Sales
        "department-004": 1,  # Design
        "department-005": 1,  # Ops
    }
    wellbeing_target = {
        "department-001": 2,
        "department-002": 1,
        "department-003": 1,
        "department-004": 0,
        "department-005": 1,
    }

    round_respondents = set()

    for dept_id in sorted(eligible_by_dept.keys()):
        eligible = eligible_by_dept[dept_id]
        random.shuffle(eligible)

        # eNPS responses
        n_enps = min(enps_target.get(dept_id, 1), len(eligible))
        score_range = ENPS_RANGES[dept_id][round_idx]

        for i in range(n_enps):
            person = eligible[i]
            score = random.randint(score_range[0], score_range[1])
            sentiment = get_sentiment(score)

            # Pick appropriate comment
            dept_comments = ENPS_COMMENTS.get(dept_id, {})
            comment_pool = dept_comments.get(sentiment, [])
            if not comment_pool:
                # Fall back to neutral
                comment_pool = dept_comments.get("neutral", ["No comment."])
            comment = random.choice(comment_pool)

            survey_id = next_id("survey")
            new_nodes.append(
                {
                    "id": survey_id,
                    "type": "survey_response",
                    "properties": {
                        "surveyType": "enps",
                        "date": survey_date,
                        "score": score,
                        "sentiment": sentiment,
                        "comment": comment,
                    },
                }
            )
            new_edges.append(
                make_edge(person["id"], survey_id, "responded_to", {})
            )
            round_respondents.add(person["id"])
            stats["enps_surveys"] += 1

        # Wellbeing responses (from different people than eNPS if possible)
        n_well = wellbeing_target.get(dept_id, 0)
        remaining = [p for p in eligible if p["id"] not in round_respondents]
        if len(remaining) < n_well:
            remaining = eligible[n_enps:]  # Use overlap if necessary
        random.shuffle(remaining)

        for i in range(min(n_well, len(remaining))):
            person = remaining[i]

            # Wellbeing score correlates with department morale
            enps_range = ENPS_RANGES[dept_id][round_idx]
            avg_enps = (enps_range[0] + enps_range[1]) / 2
            if avg_enps >= 7:
                wb_score = random.choice([3, 4, 4])
                comment = random.choice(WELLBEING_COMMENTS["good"])
            elif avg_enps >= 5:
                wb_score = random.choice([2, 3, 3])
                comment = random.choice(WELLBEING_COMMENTS["ok"])
            else:
                wb_score = random.choice([1, 2, 2])
                comment = random.choice(WELLBEING_COMMENTS["bad"])

            survey_id = next_id("survey")
            new_nodes.append(
                {
                    "id": survey_id,
                    "type": "survey_response",
                    "properties": {
                        "surveyType": "wellbeing",
                        "date": survey_date,
                        "score": wb_score,
                        "comment": comment,
                    },
                }
            )
            new_edges.append(
                make_edge(person["id"], survey_id, "responded_to", {})
            )
            round_respondents.add(person["id"])
            stats["wellbeing_surveys"] += 1

    print(f"Step 2: {round_label} — {len(round_respondents)} survey responses")

print(f"Step 2 total: {stats['enps_surveys']} eNPS + {stats['wellbeing_surveys']} wellbeing = {stats['enps_surveys'] + stats['wellbeing_surveys']} surveys")

# ─── Step 3: Dec 2024 Review Cycle ───────────────────────────────────────────

REVIEW_DATE = "2024-12-15"
REVIEW_PERIOD = "2024_annual"

# Get people eligible for Dec 2024 annual review:
# - Employed on Dec 15, 2024
# - At least 6 months tenure (startDate <= 2024-06-15)
# - Not executive level
review_eligible = []
for p in all_people:
    props = p["properties"]
    if not was_employed(p, REVIEW_DATE):
        continue
    if not has_enough_tenure(p, REVIEW_DATE, 180):
        continue
    if props.get("level") in ("C-1", "VP"):
        continue
    dept = person_to_dept.get(p["id"])
    if dept == "department-006":
        continue
    review_eligible.append(p)

random.shuffle(review_eligible)

# Select ~30 people across departments
review_targets_per_dept = {
    "department-001": 15,
    "department-002": 7,
    "department-003": 4,
    "department-004": 2,
    "department-005": 2,
}

# Narrative-critical review assignments
# People who go from "meets" → "exceeds" in Dec 2025 (growth story)
NARRATIVE_REVIEWS = {
    "person-006": "meets",      # Mike Torres: meets→exceeds (Dec 2025)
    "person-008": "meets",      # Raj Patel: meets→exceeds (Dec 2025)
    "person-007": "meets",      # Ana Kim: meets→meets (stable)
    "person-149": "meets",      # Marcus Cole: meets before departure (declining)
    "person-151": "developing", # Tyler Morrison: mid-year review showing decline
}

# Rating distribution for remaining: exceeds 20%, meets 60%, developing 15%, below 5%
RATING_WEIGHTS = ["exceeds"] * 20 + ["meets"] * 60 + ["developing"] * 15 + ["below"] * 5

review_count = 0
reviewed_people = set()

# First, handle narrative-critical reviews
for pid, rating in NARRATIVE_REVIEWS.items():
    person = node_by_id.get(pid)
    if not person:
        # Check new nodes
        for n in new_nodes:
            if n["id"] == pid:
                person = n
                break
    if not person:
        continue
    if not was_employed(person, REVIEW_DATE):
        continue

    review_id = next_id("review")
    review_type = "annual"
    completed_date = REVIEW_DATE

    # Tyler Morrison gets a mid-year review instead
    if pid == "person-151":
        review_type = "semi_annual"
        completed_date = "2024-07-15"

    # Marcus Cole gets his review before departure
    if pid == "person-149":
        completed_date = "2024-08-01"

    summary_map = {
        "person-006": "Mike Torres annual review. Solid contributor, reliable delivery. Workload increasing due to team departures.",
        "person-008": "Raj Patel annual review. Strong technical depth across multiple projects. Carrying heavy load.",
        "person-007": "Ana Kim annual review. Consistent design system contributions. Growing cross-team influence.",
        "person-149": "Marcus Cole annual review. Meeting expectations but engagement declining. Flight risk signals present.",
        "person-151": "Tyler Morrison mid-year check-in. Quality of work declining. Disengagement visible. Multiple missed deadlines in Q2.",
    }

    # Determine reviewer
    reviewer_map = {
        "person-006": "person-003",  # Lisa Huang
        "person-008": "person-003",  # Lisa Huang
        "person-007": "person-020",  # Kevin Tran (Design VP, but Ana is Eng... let's use person-003)
    }
    # Ana Kim is Frontend Engineer in Engineering, reports to... let me use her dept lead
    reviewer_map["person-007"] = "person-008"  # Raj Patel (her lead)
    reviewer_map["person-149"] = "person-004"  # David Park
    reviewer_map["person-151"] = "person-002"  # James Wright

    new_nodes.append(
        {
            "id": review_id,
            "type": "review",
            "properties": {
                "type": review_type,
                "status": "completed",
                "completedDate": completed_date,
                "rating": rating,
                "summary": summary_map.get(pid, f"{person['properties']['name']} {review_type} review."),
            },
        }
    )
    new_edges.append(
        make_edge(
            pid,
            review_id,
            "has_review",
            {"reviewerId": reviewer_map.get(pid, "person-002"), "period": REVIEW_PERIOD},
        )
    )
    reviewed_people.add(pid)
    review_count += 1

# Now fill in remaining reviews by department
eligible_by_dept = defaultdict(list)
for p in review_eligible:
    if p["id"] not in reviewed_people:
        dept = person_to_dept.get(p["id"])
        if dept:
            eligible_by_dept[dept].append(p)

# Manager/reviewer lookup
person_manager = {}
for e in edges:
    if e["type"] == "reports_to" and e["metadata"].get("isPrimary"):
        person_manager[e["source"]] = e["target"]
# Also add terminated people's managers
for tp in TERMINATED:
    person_manager[tp["id"]] = tp["manager"]

for dept_id in sorted(review_targets_per_dept.keys()):
    target = review_targets_per_dept[dept_id]
    already = len([p for p in reviewed_people if person_to_dept.get(p) == dept_id])
    needed = max(0, target - already)

    eligible = eligible_by_dept.get(dept_id, [])
    random.shuffle(eligible)

    for i in range(min(needed, len(eligible))):
        person = eligible[i]
        pid = person["id"]
        rating = random.choice(RATING_WEIGHTS)

        review_id = next_id("review")
        reviewer = person_manager.get(pid, "person-002")

        summary_templates = {
            "exceeds": f"{person['properties']['name']} annual review. Exceeded expectations. Strong contributions across multiple areas.",
            "meets": f"{person['properties']['name']} annual review. Meeting expectations. Consistent, reliable delivery.",
            "developing": f"{person['properties']['name']} annual review. Developing in role. Areas for improvement identified.",
            "below": f"{person['properties']['name']} annual review. Below expectations. Performance improvement plan recommended.",
        }

        new_nodes.append(
            {
                "id": review_id,
                "type": "review",
                "properties": {
                    "type": "annual",
                    "status": "completed",
                    "completedDate": REVIEW_DATE,
                    "rating": rating,
                    "summary": summary_templates[rating],
                },
            }
        )
        new_edges.append(
            make_edge(
                pid,
                review_id,
                "has_review",
                {"reviewerId": reviewer, "period": REVIEW_PERIOD},
            )
        )
        reviewed_people.add(pid)
        review_count += 1

print(f"Step 3: Added {review_count} Dec 2024 reviews")
stats["reviews"] = review_count

# ─── Step 4: Promotions, Transfers, Manager Changes ──────────────────────────

# Track edges that need modification
edges_to_modify = []  # list of (edge_index, modifications_dict)

PROMOTIONS = [
    {
        "person_id": "person-006",
        "date": "2025-03-01",
        "old_role": "Platform Engineer",
        "new_role": "Senior Platform Engineer",
        "old_level": "IC-3",
        "new_level": "IC-4",
        "old_salary": 165000,
        "new_salary": 185000,
        "reviewer": "person-003",
    },
    {
        "person_id": "person-011",
        "date": "2025-06-01",
        "old_role": "Engineer",
        "new_role": "Senior Engineer",
        "old_level": "IC-2",
        "new_level": "IC-3",
        "old_salary": 109000,
        "new_salary": 130000,
        "reviewer": "person-004",
    },
    {
        "person_id": "person-025",
        "date": "2025-09-01",
        "old_role": "Engineer",
        "new_role": "Senior Engineer",
        "old_level": "IC-2",
        "new_level": "IC-3",
        "old_salary": 112000,
        "new_salary": 132000,
        "reviewer": "person-019",
    },
    {
        "person_id": "person-068",
        "date": "2025-04-15",
        "old_role": "Platform Engineer",
        "new_role": "Senior Platform Engineer",
        "old_level": "IC-3",
        "new_level": "IC-4",
        "old_salary": 124000,
        "new_salary": 152000,
        "reviewer": "person-003",
    },
]

for promo in PROMOTIONS:
    pid = promo["person_id"]
    person = node_by_id[pid]

    # Update person node properties
    person["properties"]["role"] = promo["new_role"]
    person["properties"]["level"] = promo["new_level"]

    # Find and endDate old holds_position edge
    for idx, e in enumerate(edges):
        if (
            e["type"] == "holds_position"
            and e["source"] == pid
            and e["metadata"].get("status") == "current"
        ):
            edges_to_modify.append(
                (idx, {"endDate": promo["date"], "status": "previous"})
            )
            break

    # Create new holds_position edge
    new_pos_id = find_position(promo["new_role"], promo["new_level"], "Engineering")
    new_edges.append(
        make_edge(
            pid,
            new_pos_id,
            "holds_position",
            {"startDate": promo["date"], "status": "current"},
        )
    )

    # EndDate old comp, create new comp
    old_comp_id = person_comp.get(pid)
    if old_comp_id and old_comp_id in comp_nodes:
        comp_node = comp_nodes[old_comp_id]
        # Find and update the comp node
        for n in nodes:
            if n["id"] == old_comp_id:
                n["properties"]["endDate"] = promo["date"]
                break

    new_comp_id = next_id("comp")
    new_nodes.append(
        {
            "id": new_comp_id,
            "type": "comp",
            "properties": {
                "type": "salary",
                "amount": promo["new_salary"],
                "currency": "USD",
                "effectiveDate": promo["date"],
            },
        }
    )
    new_edges.append(
        make_edge(
            pid,
            new_comp_id,
            "has_comp",
            {"effectiveDate": promo["date"], "approvedBy": promo["reviewer"]},
        )
    )

    stats["promotions"] += 1

print(f"Step 4a: {stats['promotions']} promotions applied")

# Sofia Reyes (person-044): position change Tier 1 → Tier 2 (2025-01-15)
# She's currently Support Specialist IC-2 in team-004
# Change to Tier 2 Specialist IC-3
sofia_id = "person-044"
sofia = node_by_id[sofia_id]
sofia["properties"]["role"] = "Tier 2 Specialist"
sofia["properties"]["level"] = "IC-3"

# EndDate old holds_position
for idx, e in enumerate(edges):
    if (
        e["type"] == "holds_position"
        and e["source"] == sofia_id
        and e["metadata"].get("status") == "current"
    ):
        edges_to_modify.append((idx, {"endDate": "2025-01-15", "status": "previous"}))
        break

# New position
tier2_pos = find_position("Tier 2 Specialist", "IC-3", "Customer Support")
new_edges.append(
    make_edge(
        sofia_id,
        tier2_pos,
        "holds_position",
        {"startDate": "2025-01-15", "status": "current"},
    )
)

# Comp bump for Sofia
old_sofia_comp = person_comp.get(sofia_id)
if old_sofia_comp:
    for n in nodes:
        if n["id"] == old_sofia_comp:
            n["properties"]["endDate"] = "2025-01-15"
            break

new_sofia_comp = next_id("comp")
new_nodes.append(
    {
        "id": new_sofia_comp,
        "type": "comp",
        "properties": {
            "type": "salary",
            "amount": 68000,
            "currency": "USD",
            "effectiveDate": "2025-01-15",
        },
    }
)
new_edges.append(
    make_edge(
        sofia_id,
        new_sofia_comp,
        "has_comp",
        {"effectiveDate": "2025-01-15", "approvedBy": "person-005"},
    )
)

print("Step 4b: Sofia Reyes — Support Specialist → Tier 2 Specialist")
stats["transfers"] += 1

# Karen Washington (person-037): manager change from person-079 → person-042 (2025-02-01)
karen_id = "person-037"
for idx, e in enumerate(edges):
    if (
        e["type"] == "reports_to"
        and e["source"] == karen_id
        and e["metadata"].get("isPrimary") is True
    ):
        edges_to_modify.append((idx, {"endDate": "2025-02-01"}))
        break

new_edges.append(
    make_edge(
        karen_id,
        "person-042",
        "reports_to",
        {"startDate": "2025-02-01", "isPrimary": True},
    )
)

print("Step 4c: Karen Washington — manager change (Ava Thompson → Rachel Kim)")
stats["manager_changes"] += 1

# Apply all edge modifications
for idx, mods in edges_to_modify:
    edges[idx]["metadata"].update(mods)

print(f"Step 4: {len(edges_to_modify)} existing edges modified")

# ─── Step 5: in_department Metadata Backfill ──────────────────────────────────

fixed_count = 0
for e in edges:
    if e["type"] == "in_department" and e["metadata"] == {}:
        person = node_by_id.get(e["source"])
        if person:
            start_date = person["properties"].get("startDate")
            if start_date:
                e["metadata"]["startDate"] = start_date
            # For terminated people, add endDate
            if person["properties"].get("status") == "terminated":
                end_date = person["properties"].get("endDate")
                if end_date:
                    e["metadata"]["endDate"] = end_date
            fixed_count += 1

print(f"Step 5: Backfilled startDate on {fixed_count} in_department edges")
stats["in_dept_fixed"] = fixed_count

# ─── Merge & Write ────────────────────────────────────────────────────────────

# Add new nodes to existing
nodes.extend(new_nodes)
edges.extend(new_edges)

# Write schema
with open("data/schema.json", "w") as f:
    json.dump(schema, f, indent=2)
    f.write("\n")

# Write nodes
with open("data/nodes.json", "w") as f:
    json.dump({"nodes": nodes}, f, indent=2)
    f.write("\n")

# Write edges
with open("data/edges.json", "w") as f:
    json.dump({"edges": edges}, f, indent=2)
    f.write("\n")

# ─── Summary ──────────────────────────────────────────────────────────────────

print("\n" + "=" * 60)
print("BACKFILL COMPLETE")
print("=" * 60)
print(f"New nodes:  {len(new_nodes)}")
print(f"New edges:  {len(new_edges)}")
print(f"Modified:   {len(edges_to_modify)} existing edges")
print(f"Total nodes: {len(nodes)}")
print(f"Total edges: {len(edges)}")
print()
print("Breakdown:")
print(f"  Terminated people:  {stats['terminated_people']}")
print(f"  Comp records:       {stats['comp_nodes'] + stats['promotions'] + stats['transfers']}")
print(f"  COBRA events:       {stats['cobra_events']}")
print(f"  eNPS surveys:       {stats['enps_surveys']}")
print(f"  Wellbeing surveys:  {stats['wellbeing_surveys']}")
print(f"  Dec 2024 reviews:   {stats['reviews']}")
print(f"  Promotions:         {stats['promotions']}")
print(f"  Transfers:          {stats['transfers']}")
print(f"  Manager changes:    {stats['manager_changes']}")
print(f"  in_department fixed: {stats['in_dept_fixed']}")


# Script runs at top level — no main() wrapper needed
