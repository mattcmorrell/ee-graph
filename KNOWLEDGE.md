# Employee Graph — Complete Knowledge Base

> Source: Product walkthrough at plans-ashen.vercel.app/demo.html (password: graphwalks)
> Captured: March 3, 2026

---

## Table of Contents
1. [The Big Idea](#the-big-idea)
2. [Architecture Deep Dive](#architecture-deep-dive)
3. [The Employee Graph (Data Layer)](#the-employee-graph-data-layer)
4. [Intelligence Layer](#intelligence-layer)
5. [Decision Layer](#decision-layer)
6. [Interface Layer](#interface-layer)
7. [Feature: Daily Briefing (HR Pro)](#feature-daily-briefing-hr-pro)
8. [Feature: Dynamic Dashboards (HR Pro)](#feature-dynamic-dashboards-hr-pro)
9. [Feature: Onboarding (HR Pro)](#feature-onboarding-hr-pro)
10. [Feature: Manager Briefing](#feature-manager-briefing)
11. [Feature: Recognition](#feature-recognition)
12. [Feature: Life Event Concierge (Employee)](#feature-life-event-concierge-employee)
13. [Feature: Org Explorer (Employee)](#feature-org-explorer-employee)
14. [Feature: ATS Experience (Recruiting)](#feature-ats-experience-recruiting)
15. [Flywheels and Moat](#flywheels-and-moat)
16. [Design Principles and Patterns](#design-principles-and-patterns)
17. [Sample Data / Personas](#sample-data--personas)
18. [Competitive Positioning](#competitive-positioning)
19. [BHR Parity Analysis](#bhr-parity-analysis)

---

## The Big Idea

Today's HRIS is a database you operate through forms. An AI-native HRIS is a system that **operates itself** and comes to you when it needs human judgment.

The core insight: every traditional HR module — payroll, performance, comp, benefits, onboarding, compliance, recognition, recruiting — is not a separate application. They are all **different traversals of the same underlying graph**. The Employee Graph is the single data primitive. "Modules" are just views.

This is targeted at **SMB Core HR** — small-to-medium businesses that don't have dedicated HR ops teams and can't afford the complexity of enterprise HRIS platforms.

---

## Architecture Deep Dive

Four layers, bottom to top:

```
┌─────────────────────────────────────────┐
│         INTERFACE LAYER                 │
│   HR Pro views  │  Employee views       │
├─────────────────────────────────────────┤
│         DECISION LAYER                  │
│   Autonomous │ Nudge │ Surface          │
├─────────────────────────────────────────┤
│         INTELLIGENCE LAYER              │
│   Pattern │ Impact │ Proactive │ Org    │
├─────────────────────────────────────────┤
│         THE EMPLOYEE GRAPH              │
│   Nodes, edges, timestamps, context     │
└─────────────────────────────────────────┘
```

The arrows between layers:
- Graph → Intelligence: "traversal + events"
- Intelligence → Decision: "events + graph context"
- Decision → Interface: "surfaces insights & actions"
- Interface → Graph: "every interaction enriches the graph"

This circular flow is the flywheel — usage makes it smarter.

---

## The Employee Graph (Data Layer)

### Node Types (18 confirmed)
| Node | Description |
|------|-------------|
| **Person** | Core employee node |
| **Candidate** | Pre-hire, persists through conversion |
| **Interview** | Interview events and feedback |
| **Position** | Role definitions (e.g., Support Lead, IC-4) |
| **Team** | Organizational units |
| **Location** | Physical offices and jurisdictions |
| **Document** | Offer letters, I-9s, W-4s, handbooks, etc. |
| **Benefits** | Health plans, 401k, dental, HSA |
| **Comp** | Salary, bands, adjustments |
| **Policy** | Company policies, handbook sections |
| **Equipment** | Laptops, badges, corporate cards |
| **Life Event** | Baby, marriage, relocation, leave |
| **Review** | Performance reviews, 90-day reviews |
| **Certification** | Go certification, K8s cert, compliance training |
| **Project** | Active work assignments |
| **Skill** | Technical and professional skills |
| **Recognition** | Recognition events (peer and manager) |
| **Jurisdiction** | State/federal tax and compliance jurisdictions |

### Edge Properties
Every edge has:
- **Type** (reports_to, collaborates_with, mentored_by, approves_for, recognized, etc.)
- **Timestamp** (when created/modified)
- **Context** (additional metadata)
- Nothing is ever deleted — only **superseded** (temporal graph)

### Modules as Graph Traversals
This is the key conceptual mapping — each "module" is just a path through the graph:

| Traditional Module | Graph Traversal |
|---|---|
| Performance Management | Person → Review → Skill → Project → Team |
| Compensation Management | Person → Position → Comp → Team → Location |
| Payroll | Person → Comp → Jurisdiction → Policy → Document |
| Benefits Administration | Person → Benefits → Policy → Jurisdiction → Life Event |
| Onboarding | Person → Position → Team → Equipment → Document |
| Learning & Development | Person → Skill → Certification → Project → Review |
| Org Planning | Team → Position → Person → Skill → Location |
| Compliance | Jurisdiction → Policy → Person → Document → Life Event |
| Rewards & Recognition | Person → Recognition → Project → Team → Skill |
| Applicant Tracking | Candidate → Skill → Position → Interview → Team → Document |

---

## Intelligence Layer

Five capabilities a traditional HRIS can't match:

### 1. Pattern Detection
Surfaces correlations across people, time, and events that no one would think to query. Examples from the walkthrough:
- Support turnover is 4.5x department average, correlated with workload
- Recognition clustering: same 3 people recognized every month, 3 others invisible
- Raj's collaboration pattern shifted from deep (2 people, daily) to wide (7 people, sporadic) — context-switching risk

### 2. Impact Analysis
Walks the graph outward from any node to show blast radius of changes. Example: employee relocates → traverses to jurisdiction → tax withholding → payroll → compliance filing requirements.

### 3. Proactive Intelligence
Contextual nudges, not dumb reminders. Considers the full situation, not just a deadline. Examples:
- "Alex Rivera hasn't started benefits enrollment (day 11)" — not just "enrollment deadline approaching"
- "David Park hasn't scheduled Jamie Chen's first 1:1 and they're in week 2" — knows the relationship, the timing, the context

### 4. Graph Construction
Onboarding as building a subgraph. The AI knows which edges are missing and fills them. A new hire goes from 0% to 100% graph completeness as edges are created: position, team, manager, equipment, benefits, documents, training, buddy, software access, compliance jurisdictions.

### 5. Org Intelligence
Complex org queries are graph traversals in milliseconds. "Who knows Kubernetes?" becomes a traversal through Skill nodes, weighted by Certification edges, Project edges, and mentoring edges. No report builder needed.

### Event Stream
Every graph change is an event. Four event types observed:
- `new_edge` — new relationship created
- `attr_change` — attribute modified on node/edge
- `threshold` — a metric crossed a boundary
- `edge_removed` — relationship ended/superseded

AI watches the event stream continuously and triggers the Decision Layer.

---

## Decision Layer

The AI interprets events in context of the full graph and decides the appropriate response level. **Not rigid if/then rules — contextual judgment.**

### Three Response Levels

**Autonomous ("Do It")**
Agent acts, HR pro sees a summary. Routine, low-risk, reversible actions.
> "New hire starts Monday. Equipment requested, benefits email sent, manager notified, Slack invite triggered."

Examples from walkthrough:
- Provisioning software access (Zendesk, Slack, Jira)
- Sending benefits enrollment reminders
- Scheduling phone screens for candidates
- Sending personalized rejection emails
- Processing dependent enrollment
- Submitting payroll adjustments
- Auto-boosting low-volume job postings

**Nudge ("Prompt the Right Person")**
Contextual, timely prompt to a manager or employee. The AI knows who should act and when.
> "Hey Sarah, your new team member Jamie hasn't had a 1:1 yet and they're in week 2. Want me to find a time?"

Examples:
- Manager hasn't submitted interview feedback (36 hours)
- Employee hasn't started benefits enrollment (day 11)
- IT hasn't confirmed laptop request (day 3)
- Hiring manager hasn't reviewed screened candidates (5 days)

**Surface ("Bring to HR")**
Requires human judgment. Full context, options, and the AI's recommendation presented together.
> "Two employees moved to the same new state. This may trigger new withholding requirements. Here's what needs to happen."

Examples:
- Buddy assignment for new hire (with AI recommendation + reasoning)
- Parental leave extension request (with policy citation)
- Candidate with employment gap (with referrer context)
- Salary exception above band (with market data + pipeline urgency)
- Conflicting interviewer feedback (with calibration context)

### Trust Profile
The autonomy boundary **moves outward over time** per customer, per action type. **Learned, not configured.**

Four factors determine the boundary:
1. **Risk tier** — how consequential is this action?
2. **Policy** — what does company policy say?
3. **Context** — what does the graph tell us about this specific situation?
4. **Confidence** — how sure is the system about its judgment?

Month 1: flag everything. Month 12: auto-file in 15 states, surface only edge cases.

---

## Interface Layer

### What the HR Pro Sees
The HR professional's job changes from "enter data, pull reports, check compliance" to **"set policy, make judgment calls, build culture."**

| Surface | Replaces |
|---------|----------|
| **Daily Briefing** | Dashboard of widgets |
| **Conversational UI** | Report builder + SQL |
| **Dynamic Dashboards** | Configured dashboards |
| **AI-Filled Forms** | Manual data entry |

### What Employees See
Employees rarely visit "the HRIS." The system reaches them where they work.

| Surface | Replaces |
|---------|----------|
| **Ambient Nudges** | Emailing HR "when does X happen?" |
| **Org Explorer** | Static org chart + "ask around" |
| **Life Event Concierge** | Benefits portal + HR knowledge base |
| **My Timeline** | "Check your personnel file with HR" |

---

## Feature: Daily Briefing (HR Pro)

The HR pro's morning starts here. **Two items need attention, eight actions taken overnight.** No dashboard of widgets — a structured scan that takes 10 minutes, not 45.

### Structure
Three sections, each with a count badge:

**1. Needs Your Attention (decisions)**
Each item shows:
- Person avatar + name
- Badge: "Decision"
- Natural language explanation of the situation
- Context/recommendation with source (e.g., "Policy: Extension allowed per handbook §4.3")
- Action buttons (2-3 options)

Example items:
- Jamie Chen needs a buddy assigned. Rec: Sam Kim (14 mo tenure, previous buddy scored 9/10 NPS). Actions: [Assign Sam] [See other options]
- Sarah Chen asked about extending parental leave. Policy allows up to 16 weeks unpaid. Actions: [Approve 16 weeks] [Discuss with Sarah]

**2. Overnight Activity (autonomous actions taken)**
Each item shows:
- Icon indicating type (◎ onboarding, ✓ documents, → nudge, ◈ compliance, ↩ follow-up, ▪ payroll)
- Category label
- Natural language summary

Example items:
- ◎ Onboarding: Sam Okafor — Zendesk and Jira access provisioned. 4 of 5 tools done.
- ✓ Documents: Nina Kowalski signed performance review acknowledgment. All docs complete.
- → Nudge: Alex Rivera hasn't started benefits enrollment (day 11). Sent reminder.
- → Nudge: David Park hasn't scheduled Jamie Chen's first 1:1. Reminded with suggested time.
- ◈ Compliance: Q1 harassment prevention training: 142/148 complete. 6 outstanding, reminders sent.
- ✓ Benefits: Sarah Chen — dependent enrollment processed. Emma added to PPO.
- ↩ Follow-up: Jamie Chen — IT still hasn't confirmed laptop request (day 3). Sent second follow-up.
- ▪ Payroll: February adjustments submitted. 3 changes listed.

**3. Coming Up (forward-looking)**
Grouped by date, each item shows:
- What's happening
- System's autonomy level for that item (e.g., "I'll handle this — no action needed" / "Autonomous — all provisioning complete" / link to "Review draft")

Example items:
- Tomorrow: Sam Okafor Day 2, I-9 verification due
- Monday: Alex Rivera starts, fully prepared, autonomous
- Thursday: Nina Kowalski 90-day review, draft ready from accumulated signals
- Friday: Jamie Chen laptop escalation deadline, auto-escalate if unresolved

---

## Feature: Dynamic Dashboards (HR Pro)

When the briefing flags something (e.g., "turnover in Support trending up"), clicking **"Show me more"** generates a dashboard assembled on the fly.

### How It Works
1. Shows the **graph traversal** being performed: `Employee → Team(Support) → Termination → Survey → Workload`
2. "Assembled just now" indicator — not a pre-configured dashboard
3. AI **auto-selects** the right chart types for the question

### Dashboard Components (turnover example)
- **Breadcrumb trail**: Customer Support → 28 employees → 3 terminations → exit surveys → workload signals
- **KPI cards**: Annualized Turnover (38%, ↑ from 18%), Exits (3, 2 top performers), Avg Tenure at Exit (14mo, down from 22mo), Team Size (28, was 31)
- **12-Month Turnover Trend** chart: Support vs Company avg (auto-selected)
- **Exit Reasons** horizontal bar chart: Workload (3), Career Growth (2), Compensation (1), Relocation (1), Manager (0)
- **Tenure at Exit** donut chart: <12mo (43%), 12-24mo (43%), >24mo (14%)
- **Exits by Role**: Tier 1 Agent (4), Tier 2 Specialist (2), Team Lead (1)
- **Elevated Risk Signals** (graph-detected):
  - Karen Washington: Workload spike + No recognition 84 days, 18mo tenure
  - Derek Martinez: PTO pattern change + Close to exit tenure, 11mo
  - Amy Lin: Workload above avg, 8mo

### Follow-up Reshaping
Text input: "Ask a question to reshape this dashboard..."
Suggested follow-ups: "How does this compare across all of Engineering?" / "What would backfilling cost?" / "Show workload distribution"

When asked about Engineering-wide:
- New traversal: `Department(Engineering) → Team(*) → Termination → Tenure → Survey`
- Comparison across 6 teams, 142 employees
- Heat map: Turnover by Team × Quarter
- **Pattern Detected**: "Support is an outlier. Other 5 teams combined: 3.5%. Support accounts for 58% of all Engineering exits. Common thread: workload (4 of 7 exits) and lack of career progression (3). Ticket volume per agent +23% since Q2 while headcount dropped from 31 to 28."

---

## Feature: Onboarding (HR Pro)

**Onboarding is graph construction.** The system detects a new hire from the ATS and autonomously builds their subgraph.

### Onboarding List View
Table: Name, Role, Start Date, Status (Preparing/Day 1/First 30/First 90), Attention items
- 4 active, 2 completed this quarter in the demo

### Individual Onboarding View (Jamie Chen example)

**Timeline phases**: Preparing (Feb 6 → Mar 2) → Day 1 (Mar 3) → First 30 (Mar 3 → Apr 2) → First 90 (Apr 2 → Jun 1)

**Header**: Name, role, department, office, start date, manager, source (Greenhouse), recruiter, office

**Graph Completeness**: 62% (visual progress indicator)

**Employee Subgraph** — expandable sections:

| Section | Status | Details |
|---------|--------|---------|
| **Employment** | Complete | Position: Support Lead ✓, Level: IC-4, Dept: Customer Support ✓, Reports to: Maria Santos ✓, Comp: $95,000/yr ✓ |
| **Location & Compliance** | Complete | Office: Austin TX ✓, State jurisdiction: Texas ✓, Federal: Applied ✓, Tax: No state income tax ✓ |
| **Benefits** | Enrollment opens day 1 | Eligibility: Immediate ✓, Medical: PPO/HDHP w/ HSA (day 1), Dental: PPO Plus (day 1), 401k: Fidelity 4% match (day 1) |
| **Documents** | 1 of 4 signed | Offer letter: Signed Feb 5 ✓, I-9: queued for day 1, W-4: queued for day 1, Handbook: queued for day 1 |
| **Equipment** | In progress | Laptop: MacBook Pro M3 14" (requested), Badge: Austin Standard (requested). **Alert**: IT hasn't confirmed laptop — request submitted Feb 4, follow-up sent Feb 5, will escalate if unconfirmed by Feb 14 |
| **Software & Access** | 3 of 5 provisioned | Zendesk Admin ✓, Slack (#support, #support-leads, #austin) ✓, Jira (Support project) ✓, Notion: pending IT, Salesforce: pending IT |
| **Financial** | In progress | Corporate card: Brex $2,500/mo (requested), Expense policy: IC-4 Standard ✓ |
| **People** | Needs attention | Manager: Maria Santos (notified ✓), 1:1: will schedule after buddy assigned, **Buddy: needs decision** — AI recommends Sam Kim (14mo tenure, previous buddy 9/10 NPS). Also considered: Taylor Brooks. Actions: [Assign Sam Kim] [Choose Taylor instead] |
| **Training** | Path assigned | Onboarding path: Support Lead track ✓, Compliance: Harassment prevention + data security (day 1), Tool training: Zendesk Admin certification (week 1) |

**Graph View**: Visual representation of Jamie's subgraph showing all connected nodes.

---

## Feature: Manager Briefing

Manager opens every morning, knows where team stands in **5 minutes**. Collaboration signals from the graph, 1:1 prep assembled automatically.

### Greeting
"Good morning, Lisa." + date + summary: "Everyone is in a good place. 1 thing to keep an eye on. You have 1:1s with Mike and Ana today."

### Team Pulse (6 reports)
Each person shows:
- Avatar, name, role, tenure
- Current projects
- Status signal with context:
  - **steady** — "Collaboration stable, mentoring Derek this week" + "1:1 today 2pm"
  - **high** — "Cross-team with Design this week — 3 shared sessions" + "1:1 today 4pm"
  - **spreading thin** — "3 new project edges in 2 weeks, context-switching risk" + ⚠ "Worth a check-in"
  - **growing** — "Paired with Mike on 2 tasks, first solo PR submitted"
  - **building** — "4 team edges, 1 cross-team — heads-down on solo project"
  - **pto** — "On PTO through Monday, returns Feb 10. No action needed."

### 1:1 Prep (auto-assembled)
For each upcoming 1:1:
- Person + time + days since last 1:1
- **Since last time**: Bullet list of concrete accomplishments/changes (from graph events)
- **Worth discussing**: AI-generated talking points based on graph signals:
  - "K8s consolidation is a big win. Has Mike gotten visible recognition?"
  - "Mike has mentored 3 people in 6 months. Could signal readiness for senior/lead conversation."
  - "Payment migration enters the hard phase. Check if he needs additional support."
  - "Ana's PRs have been waiting 3 days. Reviewer bottleneck?"
  - "Design system rewrite on track for March. Good time to discuss what comes after."
- **Open items from last 1:1**: Tracked automatically with "open" status
  - "Mike asked about conference budget for KubeCon. You said you'd check."
  - "Discussed timeline for senior engineer leveling. No action yet."

### Signals (graph-detected patterns)
Each signal has: person, label, narrative explanation, and a **sparkline visualization**.

1. **Raj Patel — workload shift**: 4 active project edges up from 2. Collaboration went from deep (2 people, daily) to wide (7 people, sporadic). Context-switching risk. Sparkline: project edges over 5 months.

2. **Derek Lin — accelerating**: Go certification completed, paired with Mike twice, first solo PR. Graph density doubled since month 3. Ramping faster than typical. Sparkline: graph density over 11 months.

3. **Sarah Okafor — watch the edges**: 4 months in, 4 team edges + 1 cross-team. Typical at 4 months: 6-8 team + 2-3 cross-team. May be heads-down. Not a problem yet — if pattern holds through month 6, she might be isolated. Sparkline: edges vs typical at 4 months.

4. **Ana Kim — emerging bridge**: 3 new cross-team edges with Design in 2 weeks. Becoming informal bridge between engineering and design. Valuable connector role, often goes unrecognized. Sparkline: cross-team edges over 5 months.

---

## Feature: Recognition

**Recognition isn't a module — it's invisible infrastructure.** No feed, no badges, no leaderboard. Just genuine human recognition, made effortless.

### Manager Experience
Recognition signals weave into the daily briefing the manager already reads. Team pulse shows last-recognized timestamps:
- "recognized 2 days ago"
- "peer shoutout this week"
- "last recognized: 67 days" (⚠)

**Signals detect gaps**:
- "Raj hasn't been recognized in 67 days. During that time: 2 additional projects, collaboration graph widened significantly. High output, zero acknowledgment."
- "3 of 6 team members received recognition this month. The same 3 were recognized last month." (clustering detection)

**Recognition Prompt** (appears in briefing):
- Shows person, role, tenure, days since last recognition
- Natural language explanation of what they did (from graph)
- **AI-drafted message** in the manager's voice: "Raj, I want to call out something I should have said sooner — you've been holding the line on the API refactor while picking up the observability dashboard and CI/CD work without missing a beat. That kind of reliability is what keeps this team moving. Thank you."
- Actions: [Send as-is] [Edit first] [Skip]

**1:1 Talking Point** (also in briefing):
- "Derek has paired with 3 junior engineers in the last month. This mentoring pattern is consistent and growing. Has he gotten feedback on how valuable this is?"

### How Recognition Lands
The employee **never sees system chrome** — just a genuine message from a human.
- **Manager recognition**: Arrives as a direct message (DM). Looks like a personal message from the manager.
- **Peer recognition**: Appears in the team Slack channel as a normal message with emoji reactions.
- **Frontline**: SMS. "Maria, you handled the Saturday rush with a short crew and still hit every prep target. The weekend team runs because of you. Thank you. — Carlos." No app. No login. No behavior change.

### Peer-to-Peer Recognition
Two paths feeding the same graph edge:

**1. Graph-Prompted Nudge**:
> "Hey Ana — you and Derek paired on the deployment tooling twice this week while Mike was heads-down on the migration. Want to give him a shoutout?"
> [Sure, draft something] [I'll handle it] [Not now]

**2. Organic / Frictionless Input**:
> `/recognize @derek Saved me two hours on the deployment pipeline issue. Knew exactly where to look.`
No forms. No categories. No points to pick. One line of text and a name.

### Recognition in the Graph
Every recognition event creates a **first-class edge**:
```
[Ana Kim] —recognized→ [Derek Lin]
  type: peer
  trigger: collaboration
  message: "Saved me two hours..."
  signal_source: organic
  points: 10

[Lisa Chen] —recognized→ [Raj Patel]
  type: manager
  trigger: workload_absorption
  message: "Holding the line..."
  signal_source: graph_prompted
  points: 50
```

Points accrue silently for future rewards. Edges are queryable:
- "Who on my team hasn't been recognized in 60 days?"
- "Which employees get recognized by peers but never by their manager?" (blind spot detection)
- "Who recognizes others most often?" (culture carriers)

### Moat
Standalone R&R tools (Bonusly, Awardco, Achievers) bolt onto the side of an HRIS and have to **guess** what's worth recognizing. This system **knows** — because it owns the Employee Graph. It sees collaboration patterns, milestone completions, workload shifts, tenure clocks. Competitors would need to build the entire graph to replicate this.

---

## Feature: Life Event Concierge (Employee)

Employee says **"I'm having a baby"** in Slack → system instantly traverses the graph. 10 minutes replaces 6 hours of anxiety.

### Channel
Lives in Slack as an "HR Team" app. Sidebar shows: Channels, Apps (HR Team), Direct Messages. The employee messages the HR Team bot directly.

### Conversation Flow

**Trigger**: "Hey, I'm expecting a baby. Due date is around August 15th."

**Instant graph traversal** produces:
- FMLA eligibility (2.5 years tenure, well over 12-month minimum → qualifies for 12 weeks)
- Short-term disability through current Aetna plan
- Benefits changes — adding dependent to PPO
- Manager notification timing
- Leave planning with team

**System asks for 3 decisions**:
1. Preferred leave start date
2. Whether to notify manager (David) now or later
3. Benefits timing decisions

**Leave planning conversation**:
- Eligibility breakdown: FMLA (12 weeks job-protected), STD (6-8 weeks at 60%), Company parental (4 weeks full pay, concurrent with FMLA)
- Common pattern explained: "4 weeks company leave at full pay, then STD for remaining weeks"
- Return date calculated: ~November 7th
- PTO top-up option: "You have 14 days available"

**Extension question handled**:
- Company policy allows up to 16 weeks unpaid (handbook §4.3)
- Extended return date calculated: December 5th

**Final plan confirmed**:
```
Aug 15 – Sep 12: Company parental leave, full pay
Sep 12 – Nov 7:  Short-term disability + PTO top-up, full pay
Nov 7:           Planned return date
```
- 10 of 14 PTO days reserved for top-up, 4 remaining

**Automatic cascading actions**:
- Calendar blocks starting Aug 15
- Payroll notified of leave schedule
- Benefits continue uninterrupted during FMLA
- Dependent enrollment reminder closer to birth
- Manager notification: "I won't notify anyone until you say so" — employee controls timing

### Key Design Decisions
- Slack-native (no separate portal)
- Conversational, not form-based
- System shows its work (eligibility reasoning, policy citations)
- Employee controls disclosure timing
- One trigger cascades through the entire graph

---

## Feature: Org Explorer (Employee)

Not a static org chart — a **searchable, explorable network**.

### Two Modes

**Search Mode**:
- Text input: "Ask a question..."
- Suggested queries: "Who knows Kubernetes?" / "Show me the Platform team" / "Who works on payments?" / "Who just joined?" / "Austin office"
- Results ranked by **graph density**, not just title:
  - Mike Torres: cert (K8s certification 2025), runs 3 production clusters, mentored 2 engineers
  - Lisa Huang: 6 projects using K8s in last year, wrote internal migration guide
  - Raj Patel: contributed to K8s deployment tooling, collaborates frequently with Platform
- "Need help with something specific? I can introduce you to Mike."

**Structure Mode**:
- Traditional org tree, expandable
- 148 people, 6 departments
- CEO (Elena Voss) → VPs → Leads → Individual contributors
- Departments: Engineering (28), Customer Support (14), Sales (10), Design (6), Operations (4), + others

### Organization Structure (from walkthrough)
```
Elena Voss (CEO)
├── James Wright (VP Engineering) — 28 people
│   ├── Platform — Lisa Huang (Infrastructure Lead) — 8 people
│   │   ├── Mike Torres (Platform Engineer)
│   │   ├── Raj Patel (Senior Engineer)
│   │   ├── Ana Kim (Engineer)
│   │   ├── Chris Lee (Engineer)
│   │   └── Priya Sharma (Engineer)
│   ├── Product Engineering — David Park (Eng Manager) — 12 people
│   │   ├── Sam Okafor (Engineer)
│   │   ├── Nina Kowalski (Engineer)
│   │   ├── Tom Walsh (Senior Engineer)
│   │   ├── Maya Singh (Engineer)
│   │   ├── Alex Kim (Engineer)
│   │   └── Jordan Liu (Senior Engineer)
│   └── Quality — Karen Cho (QA Lead) — 8 people
│       ├── Ben Alvarez (QA Engineer)
│       └── Lin Zhang (QA Engineer)
├── Maria Santos (VP Customer Support) — 14 people
│   ├── Jamie Chen (Support Lead, starting Mar 3) — 6 people
│   ├── Sam Kim (Support Specialist)
│   ├── Taylor Brooks (Support Specialist)
│   └── Alex Rivera (Support Specialist, starting Feb 10)
├── Rachel Foster (VP Sales) — 10 people
│   ├── Lisa Park (Account Executive)
│   ├── Mark Johnson (Account Executive)
│   └── Sarah Wells (SDR Lead) — 4 people
├── Kevin Tran (VP Design) — 6 people
│   ├── Emma Davies (Senior Designer)
│   ├── Yuki Tanaka (Product Designer)
│   └── Omar Hassan (UX Researcher)
└── Diane Crawford (VP Operations) — 4 people
    ├── Priya Sharma (HR Manager)
    └── Tom Nguyen (Office Manager)
```

---

## Feature: ATS Experience (Recruiting)

No Kanban board. The system screens, schedules, follows up, and advances candidates **autonomously**. The recruiter makes **3-5 judgment calls per day**.

### Recruiting Briefing
Same pattern as HR/Manager briefing: greeting, date, summary counts.
> "3 decisions need your judgment. 14 actions taken overnight. Pipeline: 47 active candidates across 6 open roles."

### Judgment Calls (3 examples)

**1. Ambiguous Candidate — Aisha Obi (Senior Engineer)**
- Tag: "Maybe"
- Strong systems design (9/10), solid references. 2-year employment gap (2022-2024), "personal sabbatical."
- **Graph context**: Referrer Mike Torres vouches — they worked together at Stripe.
- Actions: [Advance to onsite] [Request more context] [Pass]

**2. Conflicting Feedback — Chris Wong (Product Designer)**
- Tag: "Conflicting Feedback"
- Portfolio review: Ana Kim rated "strong hire." Design exercise: James Liu rated "no hire" — weak interaction design.
- **Calibration context**: "James Liu rates 40% harder than average on design exercises. His last 5 'no hire' ratings — 3 were overturned and hired successfully."
- Actions: [Schedule debrief] [See full feedback] [Pass]

**3. Salary Exception — Maya Patel (Senior Engineer)**
- Tag: "Salary"
- Expected comp: $185k. Role band: $150-175k. 3 interviewers rated "strong hire." Market data supports $180k.
- **Pipeline context**: "Searching for 6 weeks. Maya is the first candidate all interviewers agree on. Next strongest candidate is 2 stages behind."
- Actions: [Approve $185k] [Counter at $175k] [Discuss with HM]

### Overnight Activity (14 actions)
| Icon | Action |
|------|--------|
| ◎ | Screened 12 new apps for Senior Engineer. 4 advanced, 6 rejected, 2 need review. |
| ▪ | Scheduled phone screens for Maya Patel (tomorrow 2pm) and Chris Wong (Friday 10am). Both confirmed. |
| → | Nudge: David Park hasn't submitted interview feedback for Aisha Obi (36 hours). Reminded with one-click form. |
| ✕ | Rejected 6 candidates for Product Designer. Personalized emails sent, timed for morning. |
| ↻ | Rescheduled James Liu's onsite (Thu → Mon). Interviewer PTO conflict. All notified. |
| ▲ | Advanced Sarah Kim — passed technical screen (4/4 positive). Onsite panel scheduled Tuesday. |
| ★ | Marcus Johnson accepted Account Executive offer. Start Feb 24. **Onboarding activated — 11 edges carried forward.** |
| → | Nudge: Hiring manager for Solutions Architect hasn't reviewed 2 candidates (5 days). Second reminder with urgency context. |
| ◎ | Screened 8 apps for Account Executive. 3 advanced, 4 rejected, 1 needs review. |
| ◈ | Reference check for Sarah Kim complete. 2/2 responded, both strong. |
| ↩ | Candidate Tanya Brooks (Customer Success) hasn't responded (48 hours). Reminder sent. |
| ◎ | Screened 5 apps for Customer Success. 2 advanced, 3 rejected. |
| ▪ | Scheduled final round for Emily Tran (Engineering Manager) — panel with VP Eng + two leads, Monday 1pm. |
| ◇ | Solutions Architect posting auto-boosted on LinkedIn — low volume triggered automatic promotion. |

### Pipeline Health (6 roles)
Each role shows: funnel (applied → screening → interviewing → offer), velocity metric, and contextual notes.

| Role | Funnel | Velocity | Notes |
|------|--------|----------|-------|
| Senior Engineer (2) | 47→8→3→1 | 12 days avg (healthy) | Sarah Kim ready for offer |
| Product Designer (1) | 31→4→2→0 | 18 days avg ⚠ slowing | Bottleneck: design exercise stage, avg 6 days waiting for feedback |
| Solutions Architect (1) | 9→2→0→0 | too early | ⚠ Low volume. Auto-boosted. Consider expanding sourcing. |
| Account Executive (2) | 52→6→4→1 | 9 days avg (fast) | Marcus Johnson accepted. 1 of 2 filled. |
| Engineering Manager (1) | 14→3→1→0 | 15 days avg (normal) | — |
| Customer Success (1) | 28→5→2→0 | 11 days avg (healthy) | — |

### Key Insight: ATS → Onboarding Continuity
When a candidate accepts, the node **persists**. "Marcus Johnson accepted. Onboarding activated — 11 edges carried forward." The candidate node becomes a person node. Interview feedback, skills assessed, references, recruiter relationship — all preserved. Onboarding starts from a rich subgraph, not a blank record.

---

## Flywheels and Moat

### Graph Flywheel — Organizational Knowledge
```
1. Interaction → Employee updates address, manager approves PTO, document uploaded, Slack shows collaboration
2. Graph Enrichment → AI creates edges, flags implications, links to policies. Data no one explicitly entered.
3. Better Intelligence → Richer graph means better patterns, more accurate nudges, smarter recommendations.
4. More Trust → Better outcomes build trust. Autonomy boundary expands. More actions, more interactions, more data.
→ (loops back to 1)
```

### Compliance Flywheel — Regulatory Confidence
```
1. Compliance Event → New hire in new state, relocation, benefits window, policy change, audit request
2. Precedent Creation → Records not just what happened but HOW it was resolved — jurisdiction, rule, human judgment, outcome
3. Pattern Recognition → "This looks like the CA meal-break issue from March, but in Oregon." Novel events shrink.
4. Earned Automation → Matched patterns with successful outcomes unlock autonomous handling.
→ (loops back to 1)
```

### Interlocking
Both flywheels share one substrate (the graph), compounding different things simultaneously. Every compliance event enriches the graph. Every graph traversal improves compliance context.

### Defensibility Statement
> "A competitor can copy the UI and the AI prompts. They can't copy two things simultaneously: the organizational knowledge encoded in graph relationships, and the compliance precedent history that justifies autonomous filing. Without the precedents, they can't prove the automation is safe. Without the trust, precedents don't translate into autonomy. Switching resets both to zero — and that feels like a downgrade."

---

## Design Principles and Patterns

### UX Patterns Observed Across All Sections

1. **Briefing-first architecture**: Every persona (HR pro, manager, recruiter) starts with a morning briefing. The system comes to you, not the other way around.

2. **Three-tier action model**: Every surface uses Autonomous / Nudge / Surface. The user only sees what needs their judgment.

3. **Show the graph traversal**: When presenting insights, the system shows its path through the data (e.g., "Employee → Team(Support) → Termination → Survey → Workload"). Transparency builds trust.

4. **AI recommends, human decides**: For every decision surfaced, the system provides context, options, and a recommendation — but the human always has the final say.

5. **Contextual, not configured**: Dashboards assembled on the fly, not pre-configured. 1:1 prep generated from graph events, not manual notes. Recognition prompts from detected patterns, not scheduled reminders.

6. **Meet people where they are**: HR pro in the product. Manager in the product. Employee in Slack. Frontline worker via SMS. No new apps to install.

7. **No empty states**: The graph means everything is connected. A new hire doesn't start with a blank profile — they inherit context from the ATS, the position, the team, the location.

8. **Temporal awareness**: Everything is timestamped. "67 days since last recognition." "36 hours since feedback request." "Day 11 of benefits enrollment window." The system tracks time as a first-class dimension.

9. **Invisible infrastructure**: The best features (recognition, nudges, compliance) are invisible to the end user. They experience human interactions, not software features.

10. **Progressive autonomy**: The system starts cautious and earns trust. Month 1: flag everything. Month 12: handle 80% autonomously.

### Anti-patterns Explicitly Rejected
- Dashboard of widgets → replaced by briefings
- Report builder + SQL → replaced by conversational UI
- Configured dashboards → replaced by dynamic, on-the-fly assembly
- Manual data entry → replaced by AI-filled forms with human verification
- Static org chart → replaced by graph-powered search
- Benefits portal + HR knowledge base → replaced by conversational concierge
- Kanban boards for recruiting → replaced by autonomous pipeline management
- Standalone R&R tools with badges/leaderboards → replaced by invisible recognition infrastructure
- Forms and categories for recognition → replaced by one-line text + name

---

## Sample Data / Personas

The walkthrough uses a fictional company **"Acme Co"** with consistent characters throughout:

### Company
- 148 employees
- 6 departments
- Offices in Austin, TX (at minimum)
- Current date in walkthrough: February 6, 2026 (briefings) / June 2, 2026 (life event)

### Key People Referenced

| Person | Role | Dept | Notable |
|--------|------|------|---------|
| Elena Voss | CEO | — | Top of org chart |
| James Wright | VP Engineering | Engineering | 28 reports (indirect) |
| Lisa Huang | Infrastructure Lead | Platform | Mike's manager in manager briefing. K8s expert. |
| David Park | Engineering Manager | Product Eng | 12 reports. Referenced in nudges (hasn't scheduled 1:1, slow on feedback) |
| Maria Santos | VP Customer Support | Support | Jamie Chen's manager |
| Mike Torres | Platform Engineer | Platform | 2.4 yrs. K8s consolidation shipped. Mentoring Derek. Payment migration. |
| Ana Kim | Frontend Engineer | Platform | 1.8 yrs. Design system rewrite. Emerging bridge to Design team. |
| Raj Patel | Senior Engineer | Platform | 3.1 yrs. Spreading thin (4 projects). 67 days without recognition. |
| Derek Lin | Engineer | Platform | 11 mo. Accelerating. Go cert. First solo PR. |
| Sarah Okafor | Engineer | Product Eng | 4 mo. Solo project (search service). Fewer edges than typical. |
| Priya Sharma | Engineer / HR Manager | Platform/Ops | On PTO. Also listed as HR Manager under Ops. Recruiter for Jamie Chen. |
| Jamie Chen | Support Lead (new) | Support | Starting Mar 3. Onboarding 62% complete. Needs buddy. |
| Alex Rivera | Support Specialist (new) | Support | Starting Feb 10 (later: Mar 10). Benefits enrollment lagging. |
| Sam Okafor | Engineer (new) | Engineering | Starting Feb 24 (Day 1). I-9 due. |
| Nina Kowalski | Engineer | Engineering | Started Jan 6. First 90 days. 90-day review upcoming. |
| Sam Kim | Support Specialist | Support | 14 mo tenure. Recommended as buddy for Jamie. |
| Sarah Chen | Employee | — | Life event: expecting a baby. Due Aug 15. 2.5 yrs tenure. Manager: David. PPO plan with Aetna. |
| Kevin Tran | VP Design | Design | 6 people |
| Rachel Foster | VP Sales | Sales | 10 people |
| Diane Crawford | VP Operations | Ops | 4 people |

### ATS Candidates
| Candidate | Role | Status |
|-----------|------|--------|
| Aisha Obi | Senior Engineer | Maybe — employment gap, strong technical, internal referral from Mike |
| Chris Wong | Product Designer | Conflicting feedback — split between reviewers |
| Maya Patel | Senior Engineer | Salary exception — $185k vs $150-175k band |
| Sarah Kim | Senior Engineer | Ready for offer — 4/4 interviewers positive |
| Marcus Johnson | Account Executive | Accepted offer, start Feb 24 |
| Emily Tran | Engineering Manager | Final round Monday |
| Tanya Brooks | Customer Success | Unresponsive (48 hours) |
| James Liu | — | Onsite rescheduled (interviewer, not candidate — rates 40% harder than average) |

---

## Competitive Positioning

### What This Replaces
Traditional HRIS platforms (BambooHR, Gusto, Rippling, etc.) that are:
- Database-driven, form-operated
- Module-based (separate products bolted together)
- Reactive (you go to the system, not the other way around)
- Report-configured (build reports manually)
- Compliance as checklist (not learned automation)

### Why Graph > Database
- A database stores records. A graph stores **relationships**.
- Queries become traversals (natural language, not SQL)
- Context is inherent (every node knows its neighbors)
- Temporal dimension built in (nothing deleted, only superseded)
- AI operates naturally on graphs (pattern detection, impact analysis)

### Why Incumbents Can't Replicate
1. The graph is the data model — retrofitting a relational HRIS into a graph is an architectural rewrite
2. The flywheels compound over time — a competitor starting today is months/years behind any established customer
3. Switching costs are genuine — not lock-in through friction, but through accumulated organizational intelligence that would reset to zero
4. Recognition/intelligence features are **downstream effects** of owning the data layer — bolted-on tools can't match them

### Standalone Tool Displacement
- **R&R tools** (Bonusly, Awardco, Achievers): Can't see collaboration patterns, milestone completions, workload shifts
- **ATS tools** (Greenhouse, Lever): Candidate data dies at the ATS boundary; here it flows into the employee graph
- **Performance tools**: Can't see the full context of someone's work, collaboration, skills growth
- **Benefits portals**: Require employees to navigate complex systems; here one sentence triggers a full cascade

---

## BHR Parity Analysis

Mapped all 35 BHR chatbot tools (from `AI-AGENT-INTENT.md` on `ee-backfill-demo` branch) against our graph data. **Parity achieved** — graph covers everything BHR offers plus graph-native advantages.

### BHR Tool Coverage

| Category | BHR Tool | Graph Coverage | Notes |
|----------|----------|---------------|-------|
| **Employee Data** | get_employee_info | person nodes | All fields mapped |
| | get_employee_directory | person + team + reports_to | Graph traversal gives richer results |
| | get_org_chart | reports_to + member_of + team_parent | Native graph operation |
| | search_employees | All node/edge types | Graph enables multi-hop search |
| **Time & Attendance** | get_time_off_balances | time_off + entitled_to | Balances + accrual policies |
| | request_time_off | request + requested_by + approves | Full approval chain as edges |
| | get_time_off_requests | request nodes | With status tracking |
| | get_whos_out | time_off + has_time_off | **Graph advantage**: cross-reference with project coverage |
| **Benefits & Comp** | get_benefits_info | benefits + has_benefits | |
| | get_compensation_info | comp + has_comp | |
| | get_payroll_summary | payroll_run + included_in | Run-level aggregation |
| **Hiring** | get_job_openings | position nodes (status=open) | |
| | get_candidates | candidate + candidate_for | With stageHistory enrichment |
| | get_interview_schedule | interview + has_interview + interviewed_by | |
| | get_hiring_pipeline | candidate + position + interview | **Graph advantage**: referral chains, interviewer load |
| **Performance** | get_performance_reviews | review + has_review | |
| | get_goals | person properties | |
| | get_training_status | certification + has_certification | **Graph advantage**: skill gap analysis via traversal |
| **Surveys** | get_survey_results | survey_response + responded_to | eNPS, satisfaction, wellbeing |
| **Expenses** | get_expense_reports | expense + submitted_expense | |
| **Contractors** | get_contractor_info | contractor + contracts_for + manages_contractor | |

### Intentional Exclusions (BHR features NOT in graph)

| BHR Feature | Why Excluded |
|-------------|-------------|
| Notifications/alerts | Delivery infrastructure, not data. Graph *triggers* notifications via cascade discovery. |
| Admin configuration | System settings (permissions, field config). Not employee data. |
| Document templates | Application assets, not graph nodes. Signed documents ARE in the graph. |
| Employee Community | Social feature (posts/comments). Could add later but low graph-advantage. |

### Graph-Native Advantages (things BHR can't do)

These capabilities are impossible or impractical in traditional HRIS:
1. **Cascade discovery** — One event (resignation, relocation) ripples across the entire graph
2. **Org impact analysis** — "Who's affected if Raj leaves?" requires multi-hop traversal
3. **Flight risk detection** — Collaboration + mentoring + recognition edges reveal isolation
4. **Compliance cascades** — Jurisdiction → policy traversal automates state-specific rules
5. **Skill gap analysis** — Team → member → has_skill traversal finds coverage holes
6. **Onboarding as graph construction** — Progress = edge count, visible and measurable
7. **Cross-domain correlation** — Time-off patterns + survey scores + review ratings in one model
8. **Required certifications per job** — BHR tracks training *completion* but NOT which certifications a job *requires*. The graph links `position.requiredCertifications` → certification nodes, enabling automatic gap detection on backfill ("Raj left — who else has CKA + AWS certs?")
9. **Backfill skill matching** — `position.requiredSkills` → skill nodes enables "find internal candidates who already have 3/4 required skills" — impossible in BHR

### BHR Custom Fields & Tables

BHR allows customers to add custom fields and custom tables to employee records (e.g., t-shirt size, union status, dietary restrictions, parking spot, emergency contact details). These are freeform and vary by customer. The graph handles this differently: rather than generic custom fields, graph-relevant data becomes **first-class nodes and edges** (dependents, garnishments, leave designations), while truly arbitrary data (t-shirt size) stays as properties. The graph's advantage is that structured nodes participate in traversal and cascade discovery — a custom text field in BHR cannot.

### Future BHR Features — Evaluation

| Feature | In Graph? | Justification |
|---------|-----------|---------------|
| **Expense Management** | **Yes** — added | `expense` nodes + `submitted_expense` edges. Graph advantage: correlate expenses with projects, team budgets, travel patterns. |
| **Contractor of Record** | **Yes** — added | `contractor` nodes + `contracts_for` + `manages_contractor` edges. Graph advantage: contractor ↔ project ↔ team traversal, compliance cascades for contractor jurisdictions. |
| **IT Device Management** | **Yes** — already covered | `equipment` nodes + `assigned_equipment` edges already in schema. Covers laptops, monitors, peripherals. Graph advantage: offboarding cascades (return equipment), cost tracking per person/team. |
| **Employer of Record (EOR)** | **No** — exclude | EOR is a *service relationship* with a third-party provider (like Remote), not employee data. The graph already handles what EOR affects: jurisdiction, compliance, contractor management. Adding EOR would model the vendor relationship, not the employee graph. |
| **Background Checks** | **Yes** — added | `background_check` nodes + `has_background_check` edges. BHR adding this soon. Graph advantage: link check results to candidate pipeline, flag adverse actions in hiring cascade. |

### Compliance Layer (added after HRIS market / JTBD / HR services analysis)

Evaluated graph against HRIS market (9 platforms), HR admin jobs-to-be-done, and HR services companies (PEOs, EORs, payroll bureaus, benefits TPAs, background check providers, workers comp, compliance services). Added:

| Addition | Type | Why |
|----------|------|-----|
| **Dependents** | 27 nodes, `has_dependent` + `dependent_covered_by` edges | Drive benefits eligibility, QLE cascades, age-out compliance. Were hidden as string arrays — now first-class. |
| **FLSA classification** | Property on all 144 person nodes | #1 SMB litigation risk. Exempt vs nonexempt drives overtime, meal breaks. |
| **EEO demographics** | Properties on all 144 person nodes (gender, race, eeoCategory, veteranStatus) | Required for EEO-1 filing at 50+ employees. Enables pay equity analysis. |
| **Garnishments** | 3 nodes, `has_garnishment` edges | Court-ordered, hard deadlines, priority rules. High compliance risk. |
| **COBRA events** | 2 nodes, `has_cobra_event` edges | Federally mandated 14-day notice on every termination. |
| **Leave designations** | 4 nodes, `has_leave_designation` edges | FMLA, state leave, concurrent tracking. 5-day designation deadline. |
| **Background checks** | 8 nodes, `has_background_check` edges | BHR adding this. Criminal, employment verification, adverse action tracking. |
| **HR investigations** | 2 nodes, `investigation_subject` edges | BHR has only free-text Notes. Graph formalizes complainant/subject/status/outcome. |
| **Equity grants** | 10 comp nodes with vesting properties | BHR tracks in total comp. Graph adds vesting schedule, cliff dates, vested shares. |
| **I-9 auth expiry** | Properties on document nodes | Civil/criminal fines if re-verification missed. 2 employees expiring within 90 days. |
| **Tax document types** | Expanded document type enum | W-2, 1099-NEC, 1094-C, 1095-C hosting (BHR does this via payroll). |

### BHR Partnership: VirgilHR (Compliance Intelligence)

BHR bundles VirgilHR for compliance guidance. VirgilHR is a *knowledge/guidance* tool (chatbot, handbook builder, multistate law comparison, legal alerts, resource library), not a data system. No employee data flows between BHR and VirgilHR — it's SSO-only.

**Graph-relevant insight**: What VirgilHR does manually (look up state-specific rules, compare jurisdictions), the graph does structurally via `jurisdiction → policy` traversal. The graph's compliance cascade capability is the automated version of what VirgilHR helps HR admins do by hand.
