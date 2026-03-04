# Employee Graph Prototype — Build Intent

## Goal
Build a prototype so compelling the CEO/board green-lights a massive rearchitecture to make the Employee Graph real. Target audience: leadership who needs to *feel* why a graph data model changes everything.

## What We're Building

### Cascade Explorer (primary demo)
Pick an event (resignation, relocation, promotion, new hire) and watch the ripple propagate through the employee graph. AI walks outward from the changed node, discovers consequences at each hop, surfaces actions. Each hop is something a traditional HRIS misses.

Example scenarios:
- **Raj Patel resigns**: broken mentoring edges (Derek Lin loses only mentor) → single-threaded projects (API refactor, observability dashboard, CI/CD all lose him — he's the only contributor on 3 of 4) → flight risk for close collaborators → team loses Go/K8s/CI-CD expertise → recruiting pipeline check → manager (Lisa Huang) briefing with full context
- **Employee relocates**: jurisdiction change → tax withholding → benefits plan check (state-specific) → compliance filings → office implications → buddy/mentor proximity edges
- **Promotion**: comp band validation → skill coverage changes → gap in old role → backfill candidates (skill traversal) → peer equity check → recognition prompt

### Reorg Simulator (secondary demo)
Drag someone to a new team, watch the blast radius: broken edges, compliance implications, skill gaps, collaboration disruption.

### Onboarding as Graph Construction (tertiary demo)
Watch a new hire's subgraph build from 0% to 100%. Edges light up as created.

## Key Decisions
- **Graph as infrastructure, not feature** — users see workflows and insights, not nodes and edges
- **AI traversal for prototype** — LLM reasons about graph consequences, no pre-programmed rules. Production would be hybrid (rules for common patterns, AI for novel situations).
- **JSON data layer** — nodes.json + edges.json, schema designed to map to Neo4j later
- **Cascade/workflow demos over analytics** — "impossible without the graph" beats "slightly better with the graph"
- Flight Risk Radar and Comp Equity Explorer were **rejected** as primary demos — doable in traditional HRIS, not differentiated enough
- "Ask the Graph" natural language query is **parked** — graph-as-feature vs infrastructure debate unresolved

See `product-decisions.json` for full decision journal with reasoning.

## Architecture Insight
Traditional HRIS workflows are **linear and siloed** (one module, one checklist). Graph workflows are **cascading and cross-cutting** — one event ripples across the entire graph, discovering consequences nobody pre-programmed. The graph makes discovery automatic (walk outward, find connections), but something still needs to judge what's meaningful at each hop. For the prototype, an LLM does this reasoning. For production, you'd codify common patterns into rules and use AI for edge cases.

## Reference Docs
- `KNOWLEDGE.md` — Full product vision, walkthrough details, all 9 feature specs from the original walkthrough, sample personas, competitive positioning, design principles. **This is the bible.** Read it first when resuming.
- `data/` — Graph data layer:
  - `schema.json` — 30 node types, 43 edge types with full property definitions
  - `nodes.json` — 507 nodes (144 people with FLSA/EEO demographics, 27 dependents, 33 comp records incl 10 equity grants, 8 background checks, 4 leave designations, 3 garnishments, 2 COBRA events, 2 investigations, plus all prior types)
  - `edges.json` — 596 edges (54 dependent_covered_by, 27 has_dependent, plus all prior edge types)
  - `graph-stats.json` — Summary counts
  - `README.md` — Schema docs
  - All 41 named characters match walkthrough exactly. Dates internally consistent. Salary bands realistic for Austin TX SMB. Temporal richness built in.
- `product-decisions.json` — Decision journal (view at http://localhost:3334). Contains all brainstorm output, parked ideas, rejected approaches with reasoning.
- `viewer.html` — Interactive D3 force-directed graph viewer. **Serve via local HTTP** (`python3 -m http.server 8765`), then open http://localhost:8765/viewer.html. Features: search, filter by node/edge type, click to highlight connections + detail panel, zoom/pan, drag nodes. Dark theme, exec-ready polish.

## Source Material
- Product walkthrough: https://plans-ashen.vercel.app/demo.html (password: graphwalks)
- 9 sections: Architecture, Daily Briefing, Dynamic Dashboards, Onboarding, Manager Briefing, Recognition, Life Event Concierge, Org Explorer, ATS Experience
- Company in walkthrough: "Acme Co", 148 employees, Austin TX, current date Feb 6 2026

## What's Done
- Explored full product walkthrough (all 9 sections, every detail captured)
- Captured comprehensive knowledge base (KNOWLEDGE.md — ~800 lines)
- Built graph data layer (data/ — 507 nodes, 596 edges, 30 node types, 43 edge types)
- Built interactive graph viewer (viewer.html — D3 force-directed, search, filters, detail panel, clickable properties, selection history with back button)
- Brainstormed demo ideas, narrowed to cascade/workflow direction
- Set up decision journal with 5 decisions, 8 solutions explored, 4 open questions
- Achieved BHR parity — graph covers all BHR chatbot capabilities (see below)
- GitHub repo: https://github.com/mattcmorrell/ee-graph (public)

## Graph Functions (31 total)

All operations that create/maintain the graph. Each is "create node + create edge."

| # | Function | BambooHR Today | Notes |
|---|----------|---------------|-------|
| 1 | Hire employee | Yes | |
| 2 | Set reporting relationship | Yes | |
| 3 | Assign to team | Yes | |
| 4 | Create team | Yes | |
| 5 | Nest teams | Yes | |
| 6 | Assign position | Yes | |
| 7 | Create position | Yes | |
| 8 | Set work location | Yes | |
| 9 | Terminate employee | Yes | |
| 10 | Record skill | Yes | |
| 11 | Earn certification | Yes | |
| 12 | Assign to project | **No** | |
| 13 | Complete performance review | Yes | |
| 14 | Set compensation | Yes | |
| 15 | Enroll in benefits | Yes | |
| 16 | Assign jurisdiction | Yes | Person → jurisdiction based on work location. Enables tax/compliance cascades |
| 17 | Link jurisdiction to policy | **No** | Jurisdiction → policy. The other half of compliance cascades |
| 18 | Sign document | Yes | |
| 19 | Record collaboration | **No** | Hard to do — requires passive signal collection (Slack, calendar, PRs). Only graph-native function |
| 20 | Assign mentor | **No** | |
| 21 | Recognize someone | Yes | |
| 22 | Assign buddy | **No** | |
| 23 | Create candidate | Yes | |
| 24 | Apply for position | Yes | |
| 25 | Schedule interview | Yes | |
| 26 | Record interview feedback | Yes | |
| 27 | Record referral | Yes | |
| 28 | Convert candidate to employee | Yes | |
| 29 | Assign equipment | **No** | |
| 30 | Track onboarding step | Yes | |
| 31 | Report life event | **No** | |

**7 gaps** — functions the graph needs that Bamboo doesn't do today (#12, 17, 19, 20, 22, 29, 31).
**#19 (collaboration)** is the only one that's hard — requires passive signal ingestion, not just a form. The other 6 are straightforward CRUD that Bamboo just hasn't built yet.

## Graph / BHR Parity

**Parity achieved.** Full analysis in `KNOWLEDGE.md` § BHR Parity Analysis. Graph covers all 35 BHR chatbot tools, excludes 4 non-graph features (notifications, admin config, doc templates, community), and adds 7 graph-native advantages BHR can't replicate. Future BHR features (expense, contractor, IT devices) covered; EOR excluded (vendor relationship, not employee data).

## Open Questions
- **Tech stack for cascade explorer**: could extend viewer.html with cascade animation, or build a separate app (React/Next.js). Viewer is already working well as single-file HTML+D3.
- **Interactivity level**: Preset scenarios (pick from menu) vs freeform (type any event). Preset is safer for demo, freeform is more impressive.
- **Real LLM vs simulated**: Real LLM calls for AI traversal are more flexible but add latency/cost. Could do hybrid — real LLM with pre-computed fallbacks for demo scenarios.
- **Graph-as-feature vs infrastructure line**: Some demos (reorg simulator) benefit from showing graph visually. Is there a middle ground where graph visualization IS the workflow UI?

## Next Steps
1. Design the cascade explorer — what does the UI look like? How does the AI traversal work mechanically?
2. Pick whether to extend viewer.html or build separate
3. Build cascade explorer prototype
4. Test with Raj Patel resignation scenario
5. Add reorg simulator and onboarding construction demos

## Local Dev Setup
```bash
# Start graph viewer
python3 -m http.server 8765 &
open http://localhost:8765/viewer.html

# Start decision journal
node decision-journal-server.js &
open http://localhost:3334
```
