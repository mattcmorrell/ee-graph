# Employee Graph Prototype — Build Intent

## Goal
Build a prototype so compelling the CEO/board green-lights a massive rearchitecture to make the Employee Graph real. Target audience: leadership who needs to *feel* why a graph data model changes everything.

## What We're Building

### Cascade Explorer (primary demo)
Pick an event (resignation, relocation, promotion, new hire) and watch the ripple propagate through the employee graph. AI walks outward from the changed node, discovers consequences at each hop, surfaces actions. Each hop is something a traditional HRIS misses.

Example scenarios:
- **Raj Patel resigns**: broken mentoring edges → single-threaded projects → flight risk for collaborators → skill gaps → recruiting pipeline check → manager briefing
- **Employee relocates**: jurisdiction change → tax withholding → benefits plan check → compliance filings → office implications
- **Promotion**: comp band validation → skill coverage changes → gap in old role → backfill candidates → equity check

### Reorg Simulator (secondary demo)
Drag someone to a new team, watch the blast radius: broken edges, compliance implications, skill gaps, collaboration disruption.

### Onboarding as Graph Construction (tertiary demo)
Watch a new hire's subgraph build from 0% to 100%. Edges light up as created.

## Key Decisions
- **Graph as infrastructure, not feature** — users see workflows and insights, not nodes and edges
- **AI traversal for prototype** — LLM reasons about graph consequences, no pre-programmed rules. Production would be hybrid.
- **JSON data layer** — nodes.json + edges.json, schema designed to map to Neo4j later
- **Cascade/workflow demos over analytics** — "impossible without the graph" beats "slightly better with the graph"

See `product-decisions.json` for full decision journal with reasoning.

## Reference Docs
- `KNOWLEDGE.md` — Full product vision, walkthrough details, 9 feature specs, personas, competitive positioning
- `data/` — Graph data: 252 nodes, 311 edges, 18 node types, 25+ edge types
- `product-decisions.json` — Decision journal with all brainstorm output, parked ideas, rejected approaches

## What's Done
- Explored full product walkthrough (9 sections)
- Captured comprehensive knowledge base (KNOWLEDGE.md)
- Built graph data layer (data/)
- Brainstormed and narrowed demo direction
- Set up decision journal

## What's Next
- Pick tech stack
- Design cascade explorer UI
- Build it
