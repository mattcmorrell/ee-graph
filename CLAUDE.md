## Project Ground Rules

These are non-negotiable principles. Push back if work violates them.

1. **Don't recreate Brian's website.** If something we're building is too similar to the BambooHR site in KNOWLEDGE.md, flag it. We must push boundaries, not rebuild existing work.
2. **Traditional HRIS is the enemy.** If an approach would work fine with flat tables and standard queries, push back. Every feature must demonstrate what the employee graph makes possible that traditional systems can't do.
3. **Graph traversal is the proof.** Every feature should require walking edges to work. If it could be built with a single database query, it's not proving the graph's value.
4. **One event, many consequences.** Favor scenarios that cascade across multiple node types. Single-hop lookups (person → team) aren't impressive. Multi-hop discovery (person resigns → team coverage → project risk → hiring pipeline) is.
5. **AI reasons, graph discovers.** Don't hardcode business logic for what matters in a cascade. The graph surfaces connections, the LLM judges significance. If we're writing if/else rules for specific node types, we're building traditional HRIS with extra steps.
6. **Keep it tangible.** Use real names and real org dynamics from the data, not abstract descriptions. "Raj Patel resigns and here's what breaks" convinces a CEO. "The system identifies downstream impacts of attrition events" does not.

Gentle pushback is fine on infrastructure work — sometimes you need it to get the demo healthy — but always ask whether it's serving the demo or just feeling productive.

## Decision Journal (Auto-Start & Auto-Update)

When `product-decisions.json` exists in the project root:

**Auto-start server:** At the beginning of a session, check if port 3334 is in use (`lsof -ti:3334`). If not, start the journal server in the background: `node decision-journal-server.js &`. Don't mention this to the user unless it fails.

**Auto-update journal:** As you work, maintain `product-decisions.json`:
- When a significant decision is made → add a `decisions` entry with reasoning
- When a new solution or approach is explored → add a `solutions` entry
- When an experiment is run → add an `experiments` entry
- When an approach is rejected, deferred, or chosen → update the entry's `status`
- Always capture `reasoning` — the WHY, not just the what
- Never delete entries — change `status` instead
- Update `lastUpdated` when making changes
