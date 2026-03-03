# Employee Graph — Data Layer

Graph dataset for the AI-native HRIS prototype "Employee Graph." This data powers interactive demos showing how every traditional HR module is a different traversal of the same underlying graph.

## Company: Acme Co
- **148 employees** across 6 departments
- **Primary office:** Austin, TX
- **Current date:** February 6, 2026

## File Structure

### `schema.json`
Defines all 18 node types and 25+ edge types with their properties. Every edge has: `id`, `source`, `target`, `type`, `timestamp`, and `metadata`.

### `nodes.json`
All nodes in the graph. ~252 nodes across 18 types:
- **Person** (144): All named characters from the walkthrough plus generated employees
- **Candidate** (8): ATS pipeline candidates (Aisha Obi, Chris Wong, Maya Patel, etc.)
- **Interview** (16): Interview events with scores and feedback
- **Position** (43): Every role/level combination with salary bands
- **Team** (13): Org units including sub-teams
- **Skill** (40): Technical and professional skills
- **Certification** (10): Professional certs and compliance training
- **Project** (14): Active initiatives (payment migration, K8s consolidation, etc.)
- **Equipment** (8): Laptops, badges, corporate cards for onboarding
- **Document** (14): Offer letters, I-9s, W-4s, handbook acknowledgments
- **Benefits** (8): PPO, HDHP/HSA, dental, 401k, vision, life, disability
- **Comp** (23): Salary records with realistic Austin TX tech bands
- **Location** (2): Austin HQ and remote
- **Jurisdiction** (2): Texas (no state income tax) and Federal
- **Policy** (11): FMLA, parental leave, PTO, harassment prevention, etc.
- **Life Event** (1): Sarah Chen's pregnancy
- **Review** (6): Performance and milestone reviews
- **Recognition** (8): Peer and manager recognition events

### `edges.json`
All edges in the graph. ~311 edges across 25+ types:
- **reports_to** (94): Full org chart from CEO down
- **member_of** (46): Person-to-team assignments
- **has_skill** (30): Skills with proficiency levels
- **works_on** (23): Project assignments with roles and allocation %
- **has_comp** (17): Compensation records
- **collaborates_with** (17): Collaboration patterns with frequency and strength
- **has_interview** (16): Candidate interview linkages
- **signed** (14): Document signatures
- **interviewed_by** (12): Interview feedback from specific people
- **holds_position** (10): Position assignments
- **has_benefits** (9): Benefits enrollment
- **recognized** (8): Recognition events with messages and points
- **candidate_for** (8): ATS applications
- **assigned_equipment** (8): Equipment assignments
- **has_certification** (7): Professional and compliance certs
- **has_review** (6): Performance reviews
- **mentors** (5): Active mentoring relationships
- Plus: `located_at`, `subject_to`, `governed_by`, `team_parent`, `buddy_of`, `converted_from`, `referred_by`, `life_event`, `onboarding_step`

### `graph-stats.json`
Summary counts by node type and edge type.

## Key Named Characters

| Person | Role | Notable |
|--------|------|---------|
| Elena Voss | CEO | Top of org |
| James Wright | VP Engineering | 28 indirect reports |
| Lisa Huang | Infrastructure Lead | Platform team, K8s expert |
| David Park | Engineering Manager | Product Engineering, 12 reports |
| Maria Santos | VP Customer Support | Jamie Chen's manager |
| Mike Torres | Platform Engineer | K8s consolidation, mentoring 3 people |
| Ana Kim | Frontend Engineer | Design system rewrite, bridge to Design |
| Raj Patel | Senior Engineer | 4 projects, 67 days without recognition |
| Derek Lin | Engineer | Accelerating: Go cert, first solo PR |
| Sarah Okafor | Engineer | 4 months, solo on search service |
| Jamie Chen | Support Lead (new) | Starting Mar 3, 62% onboarding complete |
| Sarah Chen | Senior Engineer | Expecting baby Aug 15, FMLA eligible |

## Temporal Richness

- Collaboration edges span months with frequency shifts (Raj: deep to wide)
- Recognition gaps are realistic (Raj: 67 days, Karen Washington: 84 days)
- Project edges show start/end dates and allocation percentages
- Historical/superseded edges marked with `_historical` flag
- Onboarding timelines track day-by-day progress
- Skill acquisition dates are after employee start dates

## How to Use

### Load the full graph
```javascript
const nodes = require('./nodes.json').nodes;
const edges = require('./edges.json').edges;
```

### Build an adjacency list
```javascript
const graph = {};
nodes.forEach(n => graph[n.id] = { ...n, edges: [] });
edges.forEach(e => {
  if (graph[e.source]) graph[e.source].edges.push(e);
  if (graph[e.target]) graph[e.target].edges.push({ ...e, _reverse: true });
});
```

### Example traversals
```javascript
// Org chart: who reports to Lisa Huang?
edges.filter(e => e.type === 'reports_to' && e.target === 'person-003');

// Who knows Kubernetes?
edges.filter(e => e.type === 'has_skill' && e.target === 'skill-001');

// Jamie Chen's onboarding subgraph
edges.filter(e => e.source === 'person-013' || e.target === 'person-013');
```
