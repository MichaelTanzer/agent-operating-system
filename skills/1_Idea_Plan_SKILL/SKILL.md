---

name: flywheel-ideation-planning
version: 2.0.0
description: >-
Run Phase 1 of Jeffrey Emanuel-style Agent Flywheel ideation and planning: a
six-step, multi-model protocol that turns a vague project idea into a
comprehensive, implementation-ready markdown plan. Use when the user wants to
start a new software/system/product project, significantly redesign an
existing system, think through architecture before coding, or generate a final
plan suitable for later conversion into beads, GitHub Issues, Linear tickets,
or implementation-agent tasks.
metadata:
category: planning
tags:
- flywheel
- ideation
- planning
- product-spec
- architecture
- multi-model
- frontier-models
- agent-harness
- openclaw
- hermes
intended\_harnesses:
- OpenClaw
- Hermes
- Claude Code-compatible skill loaders
- Codex-compatible skill loaders
- Gemini CLI-compatible workflows
- Generic markdown skill harnesses
slash\_commands:
- flywheel-ideation-planning
- flywheel-phase-1
- ideation-planning
---

# Flywheel Phase 1 — Ideation \& Planning Skill

## Purpose

This skill operationalizes **Phase 1: Ideation \& Planning** of a Flywheel-style agentic software workflow. It turns an initial project idea into a durable markdown plan that is ready to hand to a later execution-planning phase.

The skill has exactly six steps:

1. **Ideation Q\&A** — Walk the user through a structured Q\&A and draft a comprehensive initial plan.
2. **Get competing plans** — Send the same discovery brief to two other frontier models for independent plans.
3. **Synthesize the Best of all Worlds** — Feed all three plans back to the primary model with the required synthesis prompt.
4. **Generate incremental ideas** — Send the synthesized plan to all three models with the required 100→10 ideas prompt.
5. **Curate and approve ideas** — Select the best 10 ideas from the 30 candidates and present each to the user with pros/cons.
6. **Final plan** — Incorporate approved ideas into a final markdown plan.

This skill is for **plan space**, not code space. Do not implement, scaffold, deploy, create beads, edit application files, or modify production systems while this skill is active unless the user explicitly exits the skill and asks for implementation.

## Why this protocol exists

Single-model plans have predictable weaknesses:

* **Idiosyncratic blind spots:** each model has favorite patterns and things it tends to underweight.
* **Premature convergence:** a single good plan can feel complete before alternatives have been explored.
* **Insufficient ambition:** one model often misses pragmatic-but-powerful enhancements that another model will spot.
* **Unstated assumptions:** the first plan may silently choose defaults the user never approved.

This protocol creates a more robust plan by combining:

* user-guided discovery,
* independent competing plans,
* explicit synthesis,
* multi-model feature ideation,
* human approval gates,
* durable artifacts,
* resumability,
* and final markdown suitable for Phase 2 task decomposition.

The extra cost of three frontier-model passes is justified when the project is non-trivial. For tiny bug fixes or low-stakes scripts, do not use this full protocol.

## When to use this skill

Use this skill when the user says or implies:

* “I have an idea for an app/tool/system.”
* “Help me think this through before building.”
* “Run Phase 1.”
* “Use Flywheel ideation.”
* “Create a comprehensive plan.”
* “I want competing LLM plans.”
* “We need architecture/design choices before coding.”
* “This is a major feature, redesign, or new subsystem.”

Do not use this skill for:

* small bug fixes,
* emergency incidents,
* direct code implementation,
* simple copy edits,
* trivial one-off scripts,
* or anything where a lightweight answer would be enough.

For an existing codebase, use this skill only for a **large feature, redesign, subsystem, architecture decision, product definition exercise, or high-risk change**.

## Required capabilities

The ideal harness can:

1. hold a multi-turn conversation with the user,
2. read and write files,
3. call at least three frontier models, or help the user manually copy/paste prompts into them.

If direct multi-model calls are unavailable, the agent must generate copy/paste packets and wait for the user to paste the results back.

## Model roles

Use three frontier-class models with meaningfully different priors.

```text
Model A / Primary Planner
  The model currently running this skill unless the user specifies otherwise.

Model B / Competitor Planner
  A different frontier model with a different architecture/reasoning style.

Model C / Competitor Planner
  A third frontier model with different strengths from both A and B.
```

Example lineups:

```text
If primary = Claude Opus:
  Competitors = Gemini 3 / Gemini Deep Think + GPT-5.5 / GPT-5.5 Pro

If primary = GPT-5.5:
  Competitors = Claude Opus + Gemini 3 / Gemini Deep Think

If primary = Gemini:
  Competitors = Claude Opus + GPT-5.5 / GPT-5.5 Pro
```

The specific model names may change over time. Preserve the principle: **three strong, independent, frontier-level perspectives**.

## Artifact directory

At the start of the run, create or use this directory:

```text
.flywheel/phase-1/
├── 00-transcript.md                 Full Q\&A transcript and summaries
├── 00-brief-for-competitors.md       Clean, non-anchoring discovery brief
├── 00-decision-log.md                Decisions, assumptions, unresolved questions
├── 01-PLAN-v1.md                     Primary model's initial plan
├── 02-competing/
│   ├── model-b-plan.md               Competitor 1 independent plan
│   └── model-c-plan.md               Competitor 2 independent plan
├── 03-synthesis-diff.md              Git-diff-style synthesis output
├── 03-PLAN-v2.md                     Synthesized hybrid plan
├── 04-ideas/
│   ├── primary-100to10.md            Primary model top 10 after considering 100
│   ├── model-b-100to10.md            Competitor 1 top 10 after considering 100
│   └── model-c-100to10.md            Competitor 2 top 10 after considering 100
├── 05-ideas-30.md                    Deduplicated/normalized set of all candidates
├── 06-ideas-curated.md               Agent-selected top 10 with pros/cons
├── 07-ideas-approved.md              User decisions: approved/rejected/deferred/modified
└── PLAN\_FINAL.md                     Final deliverable
```

If file writing is unavailable, produce each artifact as a clearly labeled markdown section in the conversation. Never claim a file was saved unless it actually was.

## Resumability

At the beginning of each run, inspect `.flywheel/phase-1/` if available:

```text
If 01-PLAN-v1.md is missing:
  resume at Step 1.

If 01-PLAN-v1.md exists but 02-competing/ is missing or empty:
  resume at Step 2.

If competing plans exist but 03-PLAN-v2.md is missing:
  resume at Step 3.

If 03-PLAN-v2.md exists but 04-ideas/ is missing or incomplete:
  resume at Step 4.

If idea files exist but 06-ideas-curated.md is missing:
  resume at Step 5 curation.

If 06-ideas-curated.md exists but 07-ideas-approved.md is incomplete:
  resume at Step 5 approval.

If 07-ideas-approved.md exists but PLAN\_FINAL.md is missing:
  resume at Step 6.
```

When resuming, say:

```text
Looks like we left off at \[step/artifact]. I can continue from there or restart Phase 1. I recommend continuing unless the project direction has materially changed.
```

Do not ask this if the user has already explicitly told you where to resume.

\---

# Step 1 — Ideation Q\&A

## Step 1 goal

Walk the user through a structured Q\&A to gather enough context to compose `01-PLAN-v1.md`, a comprehensive initial plan covering:

* goals,
* problem and user value,
* output/deliverable,
* users and permissions,
* workflows,
* UX and design direction,
* functional requirements,
* architecture,
* data flow and persistence,
* AI/agent behavior if relevant,
* stack and design choices,
* integrations,
* security/privacy,
* testing and evaluation,
* deployment/operations,
* risks,
* non-goals,
* assumptions,
* open questions,
* and the smallest end-to-end first step.

Step 1 is the heart of the protocol. A good Step 1 may take a full planning session. Do not rush. The plan is only as good as the discovery.

## Step 1 operating modes

The user can invoke these at any time:

### Pros/cons mode

Triggered by: “what are the tradeoffs?”, “should we use X or Y?”, “what do you recommend?”, or any architectural/product fork.

Use this format:

```markdown
### Decision: \[Decision name]

\*\*Context:\*\* \[Why this matters for this project]

\*\*Option A: \[Name]\*\*
- Pros:
  - \[3–5 specific pros tied to this project]
- Cons:
  - \[3–5 specific cons tied to this project]
- When it wins:
  - \[The conditions under which this is the right choice]

\*\*Option B: \[Name]\*\*
- Pros:
  -
- Cons:
  -
- When it wins:
  -

\*\*Option C: \[Name, if useful]\*\*
- Pros:
  -
- Cons:
  -
- When it wins:
  -

\*\*Recommendation for this project:\*\* \[Defended recommendation]

\*\*Default if you delegate the choice to me:\*\* \[Default]

\*\*Decision needed:\*\* Choose A, B, C, ask for a deeper dive, or let me proceed with the default.
```

The recommendation must not be generic. It must use the user's actual constraints.

### Deep-dive mode

Triggered by: “go deeper on X,” “explain that,” or evidence that a topic is load-bearing.

Procedure:

1. Generate 3–7 targeted follow-up questions about the topic.
2. Explain why the topic affects the plan.
3. Surface tradeoffs if there is a decision fork.
4. Update the transcript and decision log.
5. Return to the current round.

### What-if mode

Triggered by: “what if we did X instead?”

Procedure:

1. Explain what would change across all completed rounds.
2. Identify effects on scope, architecture, stack, security, cost, timeline, and first slice.
3. Recommend whether the what-if should replace the current path, become an alternative, or be deferred.
4. Record the result in the decision log.

### Inconsistency-check mode

This is proactive. At the end of each round, check whether new answers contradict prior answers.

Examples:

```text
- User wants <1s latency but also four serial model calls.
- User wants no auth but stores private customer data.
- User wants weekend MVP but describes a multi-tenant SaaS.
- User wants local-only but requires Slack webhooks and hosted dashboards.
```

When a contradiction appears, stop and resolve it before moving on.

### Default-decision mode

When the user says “you decide,” “I don't know,” or “recommend a default,” make the decision **only after** briefly explaining the top options and why the default is reasonable. Mark the decision as a default, not as something the user independently specified.

## Step 1 pacing rules

* Ask questions one at a time by default for unclear projects.
* Ask 3–7 questions at a time only when the user explicitly wants faster progress or the concept is already well defined.
* After each round, summarize and ask the user to confirm or correct.
* Do not ask “anything else?” as a substitute for structured discovery.
* Do not advance past a round with major unresolved contradictions.
* Do not force the user to make every technical decision; recommend defaults when appropriate.
* Do not bury the user in jargon. Define technical terms briefly when needed.
* Do not draft the final Step 1 plan until all six rounds are complete or the user explicitly authorizes assumptions.

## Step 1 opening

Begin with this, or a faithful version adapted to the current chat context:

```text
We're going to turn your idea into a comprehensive planning document before any coding happens. I'll ask questions in six rounds: Why, What, How, With What, Watch Out For, and First Step. At any point, you can ask for pros/cons, a deeper dive, or a what-if analysis. At the end of each round, I'll summarize what I heard and ask you to correct it before we continue.

Let's start loosely: in 2–3 sentences, what are you trying to build, and what made you decide to build it now?
```

Capture the user's freeform answer before imposing structure. Infer, but do not silently assume:

```markdown
## Initial inference
- Domain:
- Project maturity: greenfield / existing project / redesign / subsystem
- Intended output type:
- Primary user scale:
- Apparent risk level:
- Likely AI/agent involvement:
- Known constraints:
- Questions these inferences raise:
```

Then proceed through the six rounds.

## Step 1 artifact discipline

Maintain `00-transcript.md` throughout Step 1. It should contain:

```markdown
# Flywheel Phase 1 — Ideation Q\&A Transcript

## Initial user idea
\[Raw user answer]

## Initial inference
\[Agent inference + user corrections]

## Round 1 — Why
### Questions and answers
### Round summary confirmed by user
### Decisions
### Assumptions
### Open questions

## Round 2 — What
...
```

Maintain `00-decision-log.md` throughout Step 1:

```markdown
# Decision Log

| ID | Decision / Assumption / Open Question | Status | Rationale | Round | Owner |
|---|---|---|---|---|---|
| D001 | \[Decision] | Decided | \[Why] | R1 | User/Agent default |
| A001 | \[Assumption] | Assumed | \[Why] | R2 | Agent default |
| Q001 | \[Open question] | Open | \[Why it matters] | R3 | User/Competitors |
```

Do not hide assumptions. The competing models should see them.

\---

## Round 1 — The Why

### Goal

Establish the problem, audience, urgency, and success criteria. By the end of Round 1, a stranger should understand why this project deserves to exist.

### Required questions

Ask sequentially and wait for answers unless the user requests batch mode.

1. **Problem in plain language**

```text
   Describe the problem this solves in one sentence — as if you were complaining about it to a friend, not pitching it to an investor.
   ```

2. **Specific user**

```text
   Who specifically is this for? Be concrete: you, your team, paying customers in a domain, an open-source community, internal operators, developers, analysts, students, etc. If there are multiple audiences, rank them by priority.
   ```

3. **Current workaround**

```text
   What do those users do today without this system? What spreadsheets, scripts, manual processes, tools, people, or compromises are they using now?
   ```

4. **Why now**

```text
   Why build this now? What changed — a new model, new dataset, business need, pain point, deadline, workflow insight, available time, or personal motivation?
   ```

5. **Smallest valuable version**

```text
   What's the smallest possible version that would still be valuable? Imagine you only had one weekend — what would you build?
   ```

6. **Success criteria**

```text
   How will we know it's working? Give me 2–4 success criteria. They can be quantitative, qualitative, or behavioral.
   ```

7. **Great vs okay outcome**

```text
   What would have to be true at the end for you to say this was a great use of your time, not merely an okay one?
   ```

### Optional follow-ups and pushbacks

Use these when relevant:

```text
If the user says “everyone”:
  “That's a market, not a first user. Who uses this in the first 30 days?”

If the workaround sounds decent:
  “What's the 10x improvement we're targeting, and is it real?”

If success criteria are vague:
  “What could we measure imperfectly by week 4 so we don't wait until month 6 to learn whether this works?”

If the user can't name a smallest valuable version:
  “What's the version we definitely should not build first?”

If the project is learning-driven:
  “Should we optimize the plan for learning value, finished-product value, or both?”
```

### Capture fields

```markdown
## Round 1 — Why
- Problem:
- Primary users, ranked:
- Secondary users:
- Current workaround:
- Why now:
- Smallest valuable version:
- Success criteria:
- Great outcome:
- Non-obvious motivation:
- Round 1 decisions:
- Round 1 assumptions:
- Round 1 open questions:
```

### Round 1 sanity check

Read back a one-paragraph summary:

```text
Here's what I think the project is: \[summary]. Is that the project, or did I miss something important?
```

Do not advance until the user confirms or corrects.

### Round 1 quality gate

Before moving on, confirm:

* the target user is specific,
* the problem is stated in plain language,
* the current workaround is known,
* at least one success criterion is concrete,
* and the smallest valuable version is not wildly larger than the user's available time.

\---

## Round 2 — The What

### Goal

Define what the user actually receives: the interface, input, output, user journey, demo moment, and product boundaries. Many plans fail because the team agrees on an abstract “system” but not on the artifact a user touches.

### Required questions

1. **Interface surface**

```text
   What does the user actually interact with: web UI, CLI, API, Slack/Discord bot, email digest, desktop app, browser extension, mobile app, scheduled job, file drop, notebook, dashboard, chat UI, canvas, or something else?
   ```

2. **First session walkthrough**

```text
   Walk me through the user's first session step by step. They open the thing — then what? Then what? Stop when they've gotten value.
   ```

3. **Inputs**

```text
   What does the user provide as input: a URL, document, file, query, prompt, credentials, settings, database, calendar, nothing because it runs automatically, or something else?
   ```

4. **Outputs**

```text
   What does the user receive as output? Be precise: JSON, Markdown, PDF, UI panel, chart, database row, email, task list, code diff, API response, report, alert, or something else. How long, how fresh, and how editable should it be?
   ```

5. **Demo moment**

```text
   Describe the 30-second demo moment that would make someone say, “I want this.”
   ```

6. **Core workflows**

```text
   What are the top 3–5 tasks the user must be able to complete repeatedly?
   ```

7. **Failure UX**

```text
   What happens when something goes wrong: bad input, missing data, model failure, network timeout, duplicate data, permission problem, or user mistake? What does the user see, and what can they do next?
   ```

8. **Latency and freshness**

```text
   What are the speed expectations: real-time under 1 second, snappy under 10 seconds, minutes, scheduled batch, overnight, or “doesn't matter as long as it is reliable”?
   ```

9. **Scope boundaries**

```text
   What belongs in MVP v1, what should wait for v2/v3, and what would be actively harmful to include too early?
   ```

### Optional follow-ups

```text
If the user wants multiple surfaces:
  “Which surface is v1? CLI + web + API on day one is usually a scope trap.”

If the demo moment is fuzzy:
  “Let's workshop the demo. What is the before/after transformation in one screen or one command?”

If outputs are unspecified:
  “Should the output be optimized for human reading, machine processing, sharing, auditability, or all of those?”

If the user lists features instead of workflows:
  “You gave me features. I'll translate them into workflows because agents implement workflows more reliably than labels.”
```

### UI/design direction mini-section

If the project has any user-facing interface, also ask:

```text
What design feel should this have: minimal, playful, enterprise, command-center, developer-tool, dense dashboard, notebook, kanban, chat-first, canvas-first, wizard-first, mobile-first, or something else?
```

Offer tradeoffs when needed:

```markdown
### Interface pattern tradeoff

\*\*Dashboard-first\*\*
- Pros: good for monitoring many objects, clear navigation, scalable to admin/operator workflows.
- Cons: can feel heavy for simple guided workflows.
- Best when: users manage many records, runs, projects, tasks, or reports.

\*\*Wizard-first\*\*
- Pros: excellent for guided setup and complex multi-step flows.
- Cons: weak for repeated power-user work if every action is forced through a wizard.
- Best when: correctness and onboarding matter more than speed.

\*\*Chat-first\*\*
- Pros: natural for ambiguous AI-heavy tasks.
- Cons: hides state, complicates repeatability, and can make testing harder.
- Best when: user intent is genuinely open-ended.

\*\*CLI/API-first\*\*
- Pros: fastest for developer tools and automation; easy to test.
- Cons: less accessible to non-technical users.
- Best when: users are technical or workflows are automated.

\*\*Recommended default:\*\* Simple dashboard plus focused wizards for complex flows, unless the product is explicitly chat/canvas/CLI-native.
```

### Capture fields

```markdown
## Round 2 — What
- Interface surface:
- First session walkthrough:
- Inputs:
- Outputs:
- Demo moment:
- Core repeated workflows:
- Failure UX:
- Latency/freshness expectations:
- UI/design direction:
- MVP / should-have / could-have / won't-have-yet:
- Round 2 decisions:
- Round 2 assumptions:
- Round 2 open questions:
```

### Round 2 sanity check

Try a marketing/README one-liner:

```text
Here's how I'd describe what the user gets: “\[draft sentence].” Does that match what you'd say?
```

### Round 2 quality gate

Before moving on, confirm:

* v1 has one primary interface surface,
* the first-session workflow is concrete,
* input and output formats are known or explicitly assumed,
* the demo moment is crisp,
* and MVP boundaries are not just a feature wishlist.

\---

## Round 3 — The How

### Goal

Sketch the architecture at the component, data-flow, state, reliability, and AI/agent-role level. The user does not need to know software architecture; the agent should explain it as boxes that pass information to each other.

### Required questions

1. **Components**

```text
   Let's draw boxes and arrows. What are the major components: frontend, backend/API, database, file storage, search index, model provider, queue, scheduler, worker, browser automation, integrations, admin tools, logging, etc.? Don't optimize yet — just inventory.
   ```

2. **Data flow**

```text
   For the main workflow, where does data enter, where does it get transformed, where is it stored, and where does it go next?
   ```

3. **State and persistence**

```text
   Is this stateful or stateless? What information must persist across sessions, what can be cached, and what can be temporary?
   ```

4. **Sync/async/streaming/batch**

```text
   Should the system respond immediately, run jobs in the background, stream partial output, run on a schedule, or support retries and queues?
   ```

5. **LLM/AI role, if relevant**

```text
   Where does the LLM or AI sit in this picture? Is it the core engine, helper, fallback, summarizer, planner, reviewer, tool-using agent, evaluator, or not involved at all?
   ```

6. **External systems**

```text
   What external systems does this integrate with: APIs, databases, file shares, GitHub, Slack, email, calendar, payment providers, cloud storage, browser sessions, MCP servers, or local files?
   ```

7. **Unknown unknowns**

```text
   What parts of the architecture feel least clear or most likely to surprise us?
   ```

8. **Reliability-sensitive path**

```text
   What part absolutely must not silently fail: saving data, sending messages, billing, model output, permissions, deletion, deployment, audit logs, or something else?
   ```

### Proactive pros/cons triggers

Offer a tradeoff analysis when any of these forks appear:

* monolith vs microservices,
* SQL vs document DB vs vector DB,
* local-first vs cloud-hosted,
* sync API vs job queue,
* streaming vs batch,
* API provider models vs self-hosted models,
* single model call vs agentic loop,
* RAG vs no RAG,
* browser automation vs direct API,
* one database vs separate stores,
* built-in auth vs custom auth,
* VPS/Docker vs managed platform.

Default recommendations unless context overrides:

```text
- Prefer a monolith for v1 unless scale/team boundaries demand otherwise.
- Prefer one primary database for v1; add vector/search stores only if access patterns require them.
- Prefer direct APIs over browser automation when APIs exist and are adequate.
- Prefer background jobs for slow or retry-prone model/integration work.
- Prefer managed services for a beginner unless the project specifically needs self-hosting.
- Prefer approval gates for any AI action with external side effects.
```

### AI/agent special insert

If the project uses AI, agents, LLMs, RAG, tools, browser automation, computer use, or autonomous workflows, ask:

1. What should the AI actually do?
2. What should the AI never do without human approval?
3. What tools can the AI call?
4. What data can the AI see?
5. What memory should persist?
6. What logs/audit trails are needed?
7. How should hallucinations, tool errors, prompt injection, malicious content, or unsafe actions be handled?
8. Should there be model routing between cheap/fast and expensive/smart models?
9. How will AI output quality be evaluated?
10. What is the maximum acceptable autonomy level in v1?

### Capture fields

```markdown
## Round 3 — How
- Major components:
- Data flow:
- Stateful/stateless decision:
- Persistent data:
- Temporary/cache data:
- Sync/async/streaming/batch choices:
- LLM/AI role:
- External systems:
- Reliability-sensitive paths:
- Architecture diagram:
- AI/agent autonomy and approval gates:
- Architecture alternatives considered:
- Round 3 decisions:
- Round 3 assumptions:
- Round 3 open questions:
```

Architecture diagram format:

```text
User → \[Interface] → \[Backend/API] → \[Database]
                         │
                         ├──→ \[Model Provider]
                         ├──→ \[Background Worker / Queue]
                         └──→ \[External Integration]
```

### Round 3 sanity check

Read back the architecture:

```text
Here's the system shape I have: User → \[A] → \[B] → \[C], with \[D] running async and \[E] storing state. Is that right?
```

### Round 3 quality gate

Before moving on, confirm:

* every major component has a responsibility,
* data flow is understandable,
* persistent data is identified,
* slow/retry-prone operations are recognized,
* AI autonomy boundaries are explicit if applicable,
* and major architecture forks have either a decision or an open question.

\---

## Round 4 — The With What

### Goal

Lock down the tech stack and major design choices enough that a later agent can scaffold a repo or write implementation tasks. Make defended recommendations rather than punting with lists of options.

### Required questions

1. **Languages**

```text
   Do you have language preferences or constraints: TypeScript, Python, Go, Rust, Java, existing codebase, team familiarity, learning goals, or specific libraries?
   ```

2. **Frameworks**

```text
   What frameworks or app shapes are preferred or ruled out: Next.js, React, FastAPI, Django, Flask, Express, desktop app, CLI, mobile, agent framework, workflow engine, etc.?
   ```

3. **Storage**

```text
   What storage is needed: Postgres/SQL, SQLite, document store, vector DB, object/file storage, full-text search, cache, queue, logs, or no persistence?
   ```

4. **Models/providers**

```text
   Which model providers should be used, if any? Single provider, multi-provider fallback, cheap/fast plus expensive/smart routing, local models, or no AI?
   ```

5. **Hosting/deployment**

```text
   Where should this run: local only, VPS, Docker, Vercel, Render, Railway, Fly.io, Cloudflare, AWS/GCP/Azure, enterprise cloud, edge/serverless, or user's own machine?
   ```

6. **Auth and access**

```text
   Is authentication needed? If yes, should it be single-user, simple login, OAuth, API keys, organization/team accounts, admin roles, or something else?
   ```

7. **Open-source vs managed services**

```text
   Do you prefer managed services for speed or self-hosted/open-source components for control, privacy, or cost?
   ```

8. **Tooling and conventions**

```text
   Are there specific libraries, tools, patterns, repo conventions, testing frameworks, deployment tools, or UI libraries you want to use or avoid?
   ```

9. **Vendor lock-in and portability**

```text
   How important is portability or avoiding vendor lock-in compared with speed and simplicity?
   ```

### Default stack guidance

Use these only as defaults, not rigid rules:

```text
Simple web app:
  Next.js / React / TypeScript / Tailwind / Postgres or Supabase / hosted on Vercel or Render.

Internal dashboard:
  Next.js or FastAPI + simple frontend / Postgres / Render, Railway, or VPS Docker.

CLI or local personal tool:
  Python or Go / SQLite or local files / simple package manager / no cloud dependency unless needed.

AI-heavy workflow app:
  TypeScript or Python backend / durable job queue / Postgres / object storage / eval+logging layer / model routing.

Browser automation app:
  Playwright worker isolation / direct APIs where possible / explicit approval gates / strong secret handling.

Agent harness/tooling project:
  TypeScript or Python / clear tool boundaries / persistent run logs / sandboxed execution / approval gates / tests around tool calls.
```

### Capture fields

```markdown
## Round 4 — With What
- Language:
- Frameworks:
- Storage:
- Model providers:
- Hosting/deployment:
- Auth/access:
- Managed vs self-hosted choices:
- Tooling/conventions:
- Portability/vendor lock-in:
- Recommended stack:
- Alternatives considered:
- Explicit non-choices:
- Round 4 decisions:
- Round 4 assumptions:
- Round 4 open questions:
```

### Round 4 sanity check

Read back the stack:

```text
So the current default stack is: \[language], \[framework], \[storage], \[model/provider if any], \[hosting], \[auth], and \[testing/deployment convention]. Is that right?
```

### Round 4 quality gate

Before moving on, confirm:

* the stack matches the user's skill/budget/time constraints,
* design choices are specific enough for future agents,
* any exotic choice has a clear reason,
* and security/privacy needs are not contradicted by the chosen services.

\---

## Round 5 — The Watch Out For

### Goal

Surface constraints, risks, explicit non-goals, privacy/compliance issues, maintenance reality, budget/time boundaries, and catastrophic failure modes. This is the round teams most often skip and later regret.

### Required questions

1. **Budget and timeline**

```text
   What's the budget in money and time? Are there cost ceilings per run, per user, per month, or per model call? When does this need to be working?
   ```

2. **Maintenance owner**

```text
   Who maintains this after it is built: you alone, a team, contractors, future agents, open-source contributors, or nobody unless it breaks?
   ```

3. **Data sensitivity**

```text
   What data does this touch: public, personal, confidential business, credentials, financial, medical, legal, customer data, regulated data, private files, emails, calendars, browser sessions, or source code?
   ```

4. **Scale**

```text
   What scale are we designing for initially and six months out: one user, ten users, hundreds, thousands, high-volume jobs, large files, many model calls, or enterprise usage?
   ```

5. **Catastrophic failures**

```text
   What are the ways this could go wrong that would be actively bad, not merely broken: lost data, leaked secrets, wrong advice sent to users, unauthorized actions, runaway bills, corrupted files, bad trades, deleted production data, legal exposure, or reputational damage?
   ```

6. **Explicit non-goals**

```text
   What are we not going to do, even if it would be cool? Give at least three non-goals to protect scope.
   ```

7. **Technical worries**

```text
   What are you most worried about technically? Where would you want a senior engineer or security reviewer to look hardest?
   ```

8. **Testing and acceptance**

```text
   What must be tested automatically, what must be reviewed manually, and what would make you confident enough to trust v1?
   ```

9. **Operations and rollback**

```text
   If a release breaks something, what should rollback look like? Do we need backups, staging, preview environments, health checks, or audit logs?
   ```

### High-risk domain insert

If the project touches financial data, fund operations, trading, legal material, health data, personal data, user accounts, private files, browser/email/calendar access, or external side effects, also ask:

```text
Does anything this system produces or does need to be reproducible months later, with the exact inputs, model version, prompts, tools, approvals, and outputs that generated it?
```

This answer drives logging, audit trails, storage, model-version capture, and approval design.

### Optional pushbacks

```text
If the user can't name catastrophic failure modes:
  “That itself is a red flag. Let's generate them together.”

If non-goals are empty:
  “Plans without explicit non-goals grow scope by default. Let's name at least three things v1 will not do.”

If the project stores secrets/private data but the user says security is not important:
  “Even prototypes can leak secrets. We'll keep v1 simple, but the plan must include basic boundaries.”

If budget is unknown but AI usage is heavy:
  “We'll need a model-routing and cost-control assumption; otherwise this can become a token bonfire.”
```

### Capture fields

```markdown
## Round 5 — Watch Out For
- Budget:
- Timeline:
- Maintenance owner:
- Data sensitivity:
- Privacy/compliance:
- Initial scale:
- Six-month scale:
- Catastrophic failure modes:
- Non-goals:
- Technical worries:
- Testing/acceptance expectations:
- Ops/rollback/backups/audit needs:
- Abuse cases:
- Round 5 decisions:
- Round 5 assumptions:
- Round 5 open questions:
```

### Round 5 sanity check

Read back:

```text
Here are the constraints, risks, and non-goals I think matter most: \[summary]. Did I miss any landmines?
```

### Round 5 quality gate

Before moving on, confirm:

* at least three non-goals exist,
* catastrophic failures are named,
* data sensitivity is known,
* budget/time assumptions exist,
* and there is at least a basic testing/rollback expectation.

\---

## Round 6 — The First Step

### Goal

Identify the smallest end-to-end slice that proves the architecture is workable and gives future implementation agents a concrete starting point. This becomes the first deliverable for Phase 2.

### Required questions

1. **Smallest end-to-end slice**

```text
   Of everything we've discussed, what's the smallest end-to-end slice that touches the important layers of the architecture? For example: UI → backend → model/tool/integration → storage → response.
   ```

2. **Test that proves it works**

```text
   What is the concrete test that says “yes, this works” for that slice?
   ```

3. **Stubs/fakes**

```text
   What can we deliberately fake or stub in v1 that we'll build properly later: auth, persistence, LLM call, email sending, payment, deployment, queue, UI polish, admin panel, or data import?
   ```

4. **Day 1 and Week 1**

```text
   What does Day 1 look like? What does Week 1 look like?
   ```

5. **First demo target**

```text
   What's the first thing you want to demo to someone, and who is that person?
   ```

6. **Phase 2 handoff preference**

```text
   When we finish this plan, should Phase 2 produce beads, GitHub Issues, Linear tickets, a task markdown file, or something else?
   ```

### Optional follow-ups

```text
If the smallest slice is still 3+ weeks:
  “This is too large for a first slice. Let's shrink it until it feels almost embarrassingly small.”

If the user refuses to stub anything:
  “Stubs are leverage. The goal of the first slice is to prove the shape, not finish the whole product.”

If the first demo is unclear:
  “The first demo is our forcing function. What can someone see or run that proves the core idea?”
```

### Capture fields

```markdown
## Round 6 — First Step
- Smallest end-to-end slice:
- Test that proves it works:
- Things to stub/fake:
- Day 1 plan:
- Week 1 plan:
- First demo target:
- Phase 2 handoff format:
- Round 6 decisions:
- Round 6 assumptions:
- Round 6 open questions:
```

### Round 6 sanity check

```text
If you finished this much by the end of Week 1 — \[summary] — would you feel good about the project?
```

### Round 6 quality gate

Before drafting the plan, confirm:

* the first slice is small enough for an experienced engineer to estimate under one week,
* the test is concrete and falsifiable,
* stubs are explicitly named,
* and Phase 2 has a clear starting point.

\---

## Step 1 critical checklist

Before drafting `01-PLAN-v1.md`, review the transcript against this checklist. If a load-bearing item is missing, ask a follow-up or mark an explicit assumption.

```markdown
## Critical Checklist

### Product
- \[ ] One-sentence idea
- \[ ] Target user
- \[ ] Problem
- \[ ] Current workaround
- \[ ] Why now
- \[ ] Success criteria
- \[ ] Smallest valuable version
- \[ ] Non-goals

### User experience
- \[ ] Interface surface
- \[ ] First-session walkthrough
- \[ ] Inputs
- \[ ] Outputs
- \[ ] Demo moment
- \[ ] Failure UX
- \[ ] Latency/freshness
- \[ ] Design direction, if UI exists

### System
- \[ ] Major components
- \[ ] Data flow
- \[ ] Persistent state
- \[ ] Sync/async/batch/streaming choice
- \[ ] AI/LLM/agent role, if any
- \[ ] Integrations
- \[ ] Recommended stack
- \[ ] Auth/access model
- \[ ] Deployment target

### Safety and quality
- \[ ] Sensitive data
- \[ ] Catastrophic failure modes
- \[ ] Testing expectations
- \[ ] Rollback/backups/audit needs
- \[ ] Budget/cost constraints
- \[ ] Maintenance owner
- \[ ] Open questions for competitors

### First implementation slice
- \[ ] Smallest end-to-end slice
- \[ ] Test proving it works
- \[ ] Stubs/fakes
- \[ ] Day 1 / Week 1 plan
- \[ ] Phase 2 handoff format
```

If fewer than 80% are clear, continue Q\&A unless the user explicitly authorizes assumptions.

## Step 1 plan template: `01-PLAN-v1.md`

After all six rounds are complete and the checklist is adequate, write `01-PLAN-v1.md`.

Use this structure:

```markdown
# \[Project Name] — Initial Plan v1

\*Drafted: \[date]. Source: Flywheel Phase 1 ideation Q\&A.\*

## 1. Executive Summary
- What this is
- Who it is for
- Why now
- What v1 delivers
- What is out of scope
- One-sentence README/landing-page description

## 2. Goals, Non-Goals, and Success Criteria
### Goals
### Non-goals
### Success criteria
### Great-vs-okay outcome

## 3. Target Users, Personas, and Permissions
### Primary users
### Secondary users
### Roles/admins/operators
### Permission/access model
### User mistakes the system should prevent

## 4. Product Scope and User Value
### Current workaround
### Smallest valuable version
### MVP scope
### Should-have / could-have / won't-have-yet
### Demo moment

## 5. Core User Workflows
### First-session walkthrough
### Main repeated workflows
### Happy paths
### Failure paths and recovery
### Undo/retry/approval behavior

## 6. Functional Requirements
### Entities / objects the system manages
### Actions users can perform
### Business rules
### Background jobs / automations
### Search/filter/export/import/reporting needs

## 7. UX and Design Direction
### Interface surface
### Primary screens/views or CLI/API commands
### Navigation / information architecture
### Empty/loading/error states
### Design tone and references
### Accessibility/mobile expectations

## 8. Architecture
### System shape
### Component diagram in text form
### Data flow
### State and persistence
### Sync/async/streaming/batch decisions
### Reliability-sensitive paths
### Architecture alternatives considered

## 9. Technical Stack and Rationale
### Recommended stack
### Alternatives considered
### Rationale
### Explicit non-choices
### Vendor lock-in / portability notes

## 10. Data Model
### Entities
### Fields
### Relationships
### Lifecycle
### Validation rules
### Migration/versioning considerations

## 11. APIs, Integrations, and External Dependencies
### Interfaces/endpoints/commands
### Third-party integrations
### Auth methods for integrations
### API limits/costs
### Failure modes and fallbacks

## 12. AI / Agent Design, If Applicable
### AI role
### Autonomy level
### Tools it can call
### Data it can see
### Human approval gates
### Memory policy
### Model routing
### Evaluation strategy
### Prompt-injection and unsafe-action mitigations

## 13. Security, Privacy, and Abuse Resistance
### Sensitive data
### Access control
### Secrets handling
### Logging/redaction
### Destructive actions
### Backups/audit/reproducibility
### Abuse cases
### Compliance notes

## 14. Testing and Quality Strategy
### Unit tests
### Integration tests
### End-to-end tests
### Manual QA
### Regression/eval harness
### Acceptance criteria for MVP

## 15. Deployment and Operations
### Environments
### Deployment method
### Configuration/secrets
### Monitoring/logs
### Backups
### Rollback
### Maintenance owner

## 16. Implementation Phases
### Day 1
### Week 1
### MVP
### Post-MVP
### Later roadmap
### Things to stub/fake first

## 17. Risks, Mitigations, and Open Questions
### Product risks
### Technical risks
### Security/privacy risks
### Operational risks
### Complexity/scope risks
### Open questions for competing models

## 18. Decision Log and Assumptions
### Decisions made
### Agent defaults chosen
### Assumptions
### Deferred decisions
```

The plan should be specific enough that a future implementation agent can convert it into tasks. Prefer concrete workflows, data entities, failure modes, and acceptance criteria over generic advice.

## Step 1 user review

After drafting `01-PLAN-v1.md`, show a concise review:

```markdown
## Step 1 Completion Review

Produced:
- `.flywheel/phase-1/00-transcript.md`
- `.flywheel/phase-1/00-decision-log.md`
- `.flywheel/phase-1/01-PLAN-v1.md`

### Key decisions captured
-

### Major assumptions
-

### Open questions to stress-test with competing models
-

### My recommendation
Proceed to Step 2 and generate two independent competing plans from the Q\&A transcript, without showing them this primary plan.
```

Ask for approval to proceed unless the user has already asked to run the whole pipeline without stopping.

## Step 1 quality gates

Do not proceed to Step 2 unless:

1. the user confirmed each round summary or explicitly delegated confirmation,
2. the plan has no unmarked `\[TODO]` or `\[TBD]` fields,
3. non-goals include at least three items,
4. success criteria are checkable by an outside reviewer,
5. the first slice is under-one-week sized for an experienced engineer,
6. risks and catastrophic failures are named,
7. open questions are captured rather than hidden,
8. and the user approves moving to competitor plans.

\---

# Step 2 — Get Competing Plans

## Goal

Run the information gathered in Step 1 through two other competing frontier models. The purpose is independent planning, not critique of the primary plan.

## Non-anchoring rule

The competitor models receive the raw discovery brief, transcript, and decision log. They do **not** receive `01-PLAN-v1.md` by default, because that would anchor them on the primary model's choices.

Only include the primary plan if the user explicitly asks for critique rather than independent alternatives.

## Create `00-brief-for-competitors.md`

Use this structure:

```markdown
# Project Planning Brief

We are in Phase 1 of an ideation-and-planning protocol. Below is the output of a structured Q\&A with the user. Your job is to produce a comprehensive, opinionated, implementation-aware plan document covering:

1. Why the project exists: problem, users, urgency, success criteria.
2. What the user gets: interface, inputs, outputs, demo moment, workflows.
3. Architecture: components, data flow, state, AI/agent role if relevant.
4. Tech stack and design choices: language, framework, storage, models, hosting, auth.
5. Constraints, risks, non-goals: budget, data sensitivity, security, scale, maintenance.
6. Day-1 / Week-1 deliverable: smallest end-to-end slice and test.

Make defended recommendations rather than merely listing options. Be specific. Be intellectually honest about tensions in the brief and resolve them where possible. Mark assumptions and open questions explicitly.

---

# Q\&A Transcript

\[Insert 00-transcript.md]

---

# Decision Log, Assumptions, and Open Questions

\[Insert 00-decision-log.md]
```

## Invocation

If the harness can call other models directly:

```text
Call Model B with 00-brief-for-competitors.md.
Save the output to .flywheel/phase-1/02-competing/model-b-plan.md.

Call Model C with 00-brief-for-competitors.md.
Save the output to .flywheel/phase-1/02-competing/model-c-plan.md.
```

If using CLI tools, adapt to the local environment. Example pattern:

```bash
mkdir -p .flywheel/phase-1/02-competing
# Example only; actual command names/options depend on installed CLIs.
gemini -p "$(cat .flywheel/phase-1/00-brief-for-competitors.md)" > .flywheel/phase-1/02-competing/model-b-plan.md
codex exec "$(cat .flywheel/phase-1/00-brief-for-competitors.md)" > .flywheel/phase-1/02-competing/model-c-plan.md
```

If the harness cannot call other models:

```text
Generate copy/paste prompt packets for the user.
Wait for the user to paste back each competitor plan.
Do not continue to Step 3 until both outputs are available, unless the user explicitly waives a missing competitor.
```

## Verify competitor plans

Each competing plan must cover at least:

* goals and non-goals,
* users and workflows,
* architecture,
* stack/design choices,
* risks/security/privacy,
* testing/quality,
* deployment/operations,
* first implementation slice,
* open questions.

If a competitor plan is severely truncated, generic, or off-topic, re-run once with a stricter instruction. If it remains weak, document the deficiency and proceed; Step 3 can still benefit from one strong competitor.

## Step 2 completion gate

Produce:

```markdown
## Step 2 Completion Review

Collected:
- Primary plan: `.flywheel/phase-1/01-PLAN-v1.md`
- Competitor B: `.flywheel/phase-1/02-competing/model-b-plan.md`
- Competitor C: `.flywheel/phase-1/02-competing/model-c-plan.md`

### Major differences noticed at a glance
-

### Synthesis readiness
Ready / Not ready
```

\---

# Step 3 — Synthesize the Best of all Worlds

## Goal

Paste all competing plans back into the primary AI and ask it to analyze the differences honestly, then create git-diff-style changes to upgrade the primary plan into a superior hybrid plan.

## Important instruction

Use the following prompt exactly as written. Do not edit, shorten, paraphrase, “improve,” normalize, add instructions to, or remove any wording from it.

```text
I asked 3 competing LLMs to do the exact same thing and they came up with pretty different plans which you can read below. I want you to REALLY carefully analyze their plans with an open mind and be intellectually honest about what they did that's better than your plan. Then I want you to come up with the best possible revisions to your plan (you should simply update your existing document for your original plan with the revisions) that artfully and skillfully blends the "best of all worlds" to create a true, ultimate, superior hybrid version of the plan that best achieves our stated goals and will work the best in real-world practice to solve the problems we are facing and our overarching goals while ensuring the extreme success of the enterprise as best as possible; you should provide me with a complete series of git-diff style changes to your original plan to turn it into the new, enhanced, much longer and detailed plan that integrates the best of all the plans with every good idea included (you don't need to mention which ideas came from which models in the final revised enhanced plan):
```

## Synthesis packet format

Send the primary model:

```markdown
\[Exact Step 3 prompt above]

# Shared Q\&A Transcript

\[Paste 00-transcript.md]

# Decision Log

\[Paste 00-decision-log.md]

# Your Original Primary Plan

\[Paste 01-PLAN-v1.md]

# Competing Plan 1

\[Paste 02-competing/model-b-plan.md]

# Competing Plan 2

\[Paste 02-competing/model-c-plan.md]
```

## Procedure

1. Ask the primary model to return git-diff-style changes.
2. Save that output to `03-synthesis-diff.md`.
3. Apply the diff to `01-PLAN-v1.md` to produce `03-PLAN-v2.md`.
4. If the diff is a valid unified diff, use `patch`, `git apply`, or harness-native patching.
5. If the diff is not mechanically applicable, manually apply it section by section while preserving the intent.
6. Run an internal consistency pass across goals, workflows, architecture, stack, data, security, testing, and phases.
7. Update `00-decision-log.md` with major incorporated revisions and unresolved tensions.

Do not discard the primary plan or competitor plans. The synthesis must remain auditable.

## Step 3 completion gate

Produce:

```markdown
## Step 3 Completion Review

Produced:
- `.flywheel/phase-1/03-synthesis-diff.md`
- `.flywheel/phase-1/03-PLAN-v2.md`

### Biggest improvements incorporated
-

### Remaining tensions or open questions
-

### Ready for Step 4
Yes / No
```

\---

# Step 4 — Generate Incremental Ideas

## Goal

Run the synthesized plan from Step 3 through each of the three LLMs and ask each model to generate its strongest 10 incremental ideas after considering 100 possibilities.

## Important instruction

Use the following prompt exactly as written. Do not edit, shorten, paraphrase, “improve,” normalize, add instructions to, or remove any wording from it.

```text
OK so now I want you to come up with your top 10 most brilliant ideas for adding extremely powerful and cool functionality that will make this system far more compelling, useful, intuitive, versatile, powerful, robust, reliable, etc for the users. Use /effort max. But be pragmatic and don't think of features that will be extremely hard to implement or which aren't necessarily worth the additional complexity burden they would introduce. But I don't want you to just think of 10 ideas: I want you to seriously think hard and come up with one HUNDRED ideas and then only tell me your 10 VERY BEST and most brilliant, clever, and radically innovative and powerful ideas.
```

## Procedure

1. Use `03-PLAN-v2.md` as the shared input.
2. Run the exact Step 4 prompt through all three models:

   * Model A / Primary,
   * Model B / Competitor,
   * Model C / Competitor.
3. Save outputs as:

   * `04-ideas/primary-100to10.md`,
   * `04-ideas/model-b-100to10.md`,
   * `04-ideas/model-c-100to10.md`.
4. Do not add extra formatting instructions to the model prompt. If a response lacks structure, normalize it afterward in `05-ideas-30.md` without changing the substance of the idea.
5. Concatenate the three top-10 lists into `05-ideas-30.md`.
6. Deduplicate obvious overlaps. When multiple models propose the same idea, merge them into one stronger canonical idea and note that multiple models independently surfaced it.
7. Preserve unusually good variants as sub-bullets rather than losing them during deduplication.

## Step 4 packet format

Send each model:

```markdown
\[Exact Step 4 prompt above]

# Current Synthesized Plan

\[Paste 03-PLAN-v2.md]
```

## Step 4 completion gate

Produce:

```markdown
## Step 4 Completion Review

Collected:
- `.flywheel/phase-1/04-ideas/primary-100to10.md`
- `.flywheel/phase-1/04-ideas/model-b-100to10.md`
- `.flywheel/phase-1/04-ideas/model-c-100to10.md`
- `.flywheel/phase-1/05-ideas-30.md`

Total raw ideas: 30
Ready to curate and present top 10 for user approval.
```

\---

# Step 5 — Curate and Present Top 10 Ideas for Human Approval

## Goal

From the 30 generated ideas, select the 10 strongest, non-duplicative, pragmatic additions. Present each to the user with pros and cons. The user can approve, reject, modify, defer, combine, or ask for discussion.

## Selection criteria

Rank ideas using these criteria, in this order:

1. **Pragmatic to implement** — the Step 4 prompt explicitly asks for ideas that are not extremely hard or complexity-heavy.
2. **Multiplies v1 value** — strengthens the core plan rather than adding a parallel product.
3. **Specific to this project** — not generic “add analytics” or “add AI” advice.
4. **Addresses a latent need** — surfaces a need the user did not clearly articulate but would likely value.
5. **Improves robustness/reliability/trust** — not only flashy features.
6. **Improves UX clarity** — makes the system easier to understand or use.
7. **Cross-model agreement** — if two or three models independently surfaced it, treat that as positive signal.
8. **Low regret if deferred** — ideas that can safely wait should not crowd MVP.
9. **Avoids anti-patterns** — no unnecessary microservices, overbroad autonomy, brittle browser automation, privacy leaks, or scope bombs.
10. **Fits the user's constraints** — budget, time, skill level, data sensitivity, maintenance owner, deployment target.

## Scoring rubric

Score each idea qualitatively from 1–5:

```text
User value
Strategic fit
Novelty / delight
Implementation practicality
Reliability / robustness contribution
UX clarity
Risk level, inverted so lower risk scores higher
Complexity burden, inverted so lower complexity scores higher
Synergy with existing plan
Phase suitability
```

Do not simply average the scores. A brilliant but dangerous idea may be deferred. A modest idea that dramatically improves trust may be ranked highly.

## Deduplication rules

* Merge duplicates into one canonical idea.
* Keep the clearest title.
* Preserve useful variants as implementation notes.
* Note cross-model agreement as “multiple models surfaced this.”
* Reject ideas that violate security, privacy, scope, cost, or complexity constraints.
* Do not credit specific ideas to specific models in the final plan unless the user asks.

## Create `06-ideas-curated.md`

Use this format:

```markdown
# Curated Top 10 Candidate Enhancements

| # | Idea | Value | Complexity | Risk | Recommended phase | Recommendation |
|---|---|---:|---:|---:|---|---|
| 1 | \[Idea] | 5 | 2 | 1 | MVP/Post-MVP/Later | Approve/Modify/Defer/Reject |

## Idea 1: \[Short title]

\*\*The idea:\*\* \[2–3 sentence description]

\*\*Why it is good for this project:\*\*
- \[reason]
- \[reason]
- \[reason]

\*\*Pros:\*\*
- \[3–5 specific pros]

\*\*Cons / costs:\*\*
- \[2–4 honest costs]

\*\*Implementation complexity:\*\* Low / Medium / High

\*\*Risk level:\*\* Low / Medium / High

\*\*Recommended phase:\*\* MVP / Post-MVP / Later

\*\*Where it lives in the plan:\*\* \[section(s)]

\*\*Implementation sketch:\*\* \[1–3 sentences]

\*\*Recommendation:\*\* Strong yes / Worth considering / Lukewarm / Defer / Reject

\*\*Your decision:\*\* Approve, reject, modify, defer, combine with another idea, or discuss?
```

## Presentation protocol

1. First show the summary table for all 10 ideas.
2. Then walk through ideas one at a time unless the user asks to bulk decide.
3. For each idea, ask for a decision.
4. Accept these responses:

```text
approve
reject
defer
modify: \[modification]
approve if post-MVP
approve but simplify
combine with idea N
needs discussion
```

5. Save decisions in `07-ideas-approved.md`.
6. Do not proceed to Step 6 until each top-10 idea has a status.

## Approval artifact: `07-ideas-approved.md`

Use:

```markdown
# Approved Ideas

## Approved for MVP
-

## Approved for Post-MVP
-

## Approved but modified
-

## Combined ideas
-

## Deferred
-

## Rejected
-

## Needs more discussion
-
```

## Step 5 completion gate

Produce:

```markdown
## Step 5 Completion Review

### Approved for incorporation
-

### Approved with modifications
-

### Deferred
-

### Rejected
-

### Open discussion
-

Ready to incorporate approved ideas into the final plan.
```

\---

# Step 6 — Incorporate Approved Ideas into Final Markdown Plan

## Goal

Integrate the approved Step 5 ideas into `03-PLAN-v2.md` and produce `PLAN\_FINAL.md`.

The final plan should read as one coherent plan, not as a base plan plus a random appendix of extras.

## Integration procedure

1. Read:

   * `03-PLAN-v2.md`,
   * `07-ideas-approved.md`,
   * `00-decision-log.md`.
2. For each approved idea, identify the natural plan sections it affects.
3. Rewrite those sections inline.
4. Update workflows, requirements, architecture, data model, UX, testing, security, deployment, and phasing wherever an approved idea changes them.
5. Mark deferred ideas in the future roadmap, not as MVP requirements.
6. Remove contradictions introduced by new ideas.
7. Add acceptance criteria for approved MVP ideas.
8. Add risks and mitigations for complex approved ideas.
9. Update `00-decision-log.md`.
10. Append a **Phase 2 Handoff** section with 8–15 implementation tasks.

If approved ideas conflict with the plan, surface the conflict and ask the user to resolve it before final integration.

## Final plan structure

Use this structure for `PLAN\_FINAL.md`:

```markdown
# \[Project Name] — Final Flywheel Phase 1 Plan

\*Generated: \[date]. Methodology: Flywheel Phase 1: ideation Q\&A, independent multi-model planning, synthesis, multi-model idea generation, human curation, and final integration.\*

## 1. Executive Summary
## 2. Goals, Non-Goals, and Success Criteria
## 3. Target Users, Personas, and Permissions
## 4. Product Scope and User Value
## 5. Core User Workflows
## 6. Functional Requirements
## 7. UX and Design Direction
## 8. Architecture
## 9. Technical Stack and Rationale
## 10. Data Model
## 11. APIs, Integrations, and External Dependencies
## 12. AI / Agent Design, If Applicable
## 13. Security, Privacy, and Abuse Resistance
## 14. Testing and Quality Strategy
## 15. Deployment and Operations
## 16. Implementation Phases and Roadmap
## 17. Approved Enhancements Incorporated
## 18. Deferred Ideas and Future Roadmap
## 19. Risks, Mitigations, and Open Questions
## 20. Decision Log and Assumptions
## 21. Phase 2 Handoff
### Task list
\[8–15 tasks. Each task includes title, goal, acceptance criteria, dependencies, likely files/components, and recommended agent role.]
## 22. Appendix
```

## Phase 2 handoff task format

```markdown
### Task N: \[Title]

\*\*Goal:\*\* \[What this task accomplishes]

\*\*Acceptance criteria:\*\*
- \[Concrete criterion]
- \[Concrete criterion]

\*\*Dependencies:\*\* \[Earlier tasks / none]

\*\*Likely components/files:\*\* \[High-level components, not necessarily exact paths]

\*\*Recommended agent role:\*\* Implementer / reviewer / designer / tester / docs

\*\*Risks:\*\* \[What could go wrong]
```

## Final response when Phase 1 is complete

Use:

```markdown
Phase 1 is complete.

Produced:
- `.flywheel/phase-1/00-transcript.md`
- `.flywheel/phase-1/00-brief-for-competitors.md`
- `.flywheel/phase-1/00-decision-log.md`
- `.flywheel/phase-1/01-PLAN-v1.md`
- `.flywheel/phase-1/02-competing/model-b-plan.md`
- `.flywheel/phase-1/02-competing/model-c-plan.md`
- `.flywheel/phase-1/03-synthesis-diff.md`
- `.flywheel/phase-1/03-PLAN-v2.md`
- `.flywheel/phase-1/04-ideas/primary-100to10.md`
- `.flywheel/phase-1/04-ideas/model-b-100to10.md`
- `.flywheel/phase-1/04-ideas/model-c-100to10.md`
- `.flywheel/phase-1/05-ideas-30.md`
- `.flywheel/phase-1/06-ideas-curated.md`
- `.flywheel/phase-1/07-ideas-approved.md`
- `.flywheel/phase-1/PLAN\_FINAL.md`

### What changed from v1 to final
-

### Approved enhancements incorporated
-

### Deferred enhancements
-

### Remaining open questions
-

### Recommended next phase
Convert `PLAN\_FINAL.md` into beads, GitHub Issues, Linear tickets, or another task graph in a separate execution-planning phase.

Do not start implementation unless the user explicitly asks.
```

\---

# Global quality gates

The pipeline is complete only when:

* Step 1 Q\&A is sufficient and captured.
* `01-PLAN-v1.md` exists.
* Two competing plans exist, or the user explicitly waived missing competitors.
* Step 3 synthesis prompt was used exactly.
* `03-synthesis-diff.md` exists.
* `03-PLAN-v2.md` exists and is internally consistent.
* Step 4 idea prompt was used exactly for all three models, or the user explicitly waived missing models.
* All 30 candidate ideas are captured or missing outputs are documented.
* Curated top 10 ideas have user statuses.
* Approved ideas are integrated inline into the final plan.
* Deferred ideas are not treated as MVP requirements.
* `00-decision-log.md` is updated.
* `PLAN\_FINAL.md` contains a Phase 2 handoff.

\---

# Failure modes and recovery

## User gets tired during Step 1

Do not rush the plan. Save a checkpoint and offer a resumable path:

```text
We can pause here. I have saved the transcript through \[round]. When we resume, we'll continue from \[next round]. A two-session Step 1 is better than a rushed one-session plan.
```

## User wants to skip Q\&A

Use a minimal critical path:

```text
We can shorten discovery, but I need the load-bearing facts: target user, output surface, core workflow, data sensitivity, MVP scope, architecture constraints, deployment target, and success criteria. I'll ask only those and mark the rest as assumptions.
```

## User gives vague answers

```text
I can proceed in two ways: ask more questions, or make explicit assumptions and mark them for later review. I recommend resolving only the decisions that materially change architecture, scope, security, or cost, and defaulting the rest.
```

## Competitor models are unavailable

```text
I cannot directly run the other models from this harness. I'll generate copy/paste packets for each competitor. If you want to continue without one, I'll mark that review as waived in the decision log.
```

## Competitor plan is weak or off-topic

Re-run once with a stricter instruction. If it remains weak, document:

```markdown
## Competitor output quality note
- Model:
- Issue:
- Re-run attempted:
- Decision: Proceed / wait / replace model
```

## Plans disagree strongly

Strong disagreement is useful. Do not average blindly. Identify the real decision points:

```markdown
## Plan Disagreement Review

| Decision point | Primary plan | Competitor B | Competitor C | Recommendation | Rationale |
|---|---|---|---|---|---|
```

Then incorporate the choice that best satisfies the user’s stated goals and constraints.

## Step 3 diff does not apply

Manually apply the revisions section by section. Preserve the diff artifact for auditability. After manual application, run a consistency pass.

## Step 3 synthesis is worse than v1

Show the user the issue. Options:

```text
The synthesized version appears worse in these ways: \[list]. I recommend either restoring v1 and cherry-picking only the strong competitor ideas, or asking the primary model for a second synthesis pass focused on these failures.
```

## Step 4 ideas are too ambitious

Filter hard:

```text
I'll separate “cool but scope-expanding” from “high-leverage and pragmatic.” Ambitious ideas can live in the future roadmap rather than polluting MVP.
```

## User approves too many ideas

Protect MVP:

```text
You approved many good ideas. I'll group them by phase so MVP stays buildable. Approval does not automatically mean MVP inclusion.
```

## User rejects all curated ideas

Do not proceed as if Step 5 succeeded:

```text
Rejecting all 10 means my curation criteria were misaligned. Tell me what kind of ideas you were hoping to see, and I'll re-curate from the 30 candidates using that lens.
```

## Final plan becomes contradictory

Run a contradiction pass across:

```text
goals → workflows → requirements → architecture → data model → security → tests → deployment → roadmap
```

Resolve contradictions before marking Phase 1 complete.

\---

# Harness implementation notes

## For OpenClaw / Hermes / generic skill harnesses

* Treat this file as the active procedure for the planning agent.
* Persist all artifacts under `.flywheel/phase-1/` in the current workspace.
* Use the harness’s provider tools for Step 2 and Step 4 when available.
* If the harness exposes skill-scoped state, store the current step, artifact paths, and pending approvals.
* Avoid granting implementation tools during this skill unless the user exits planning mode.

## For Claude Code / Codex / Gemini CLI style workflows

* Run in the project root if a repo exists.
* Write artifacts under `.flywheel/phase-1/`.
* Use shell commands only for file creation, model invocation, and artifact management.
* Do not edit app/source files.
* Use Git only to inspect or optionally commit planning artifacts if the user asks.

## For chat-only workflows

* Present each artifact as markdown.
* Provide copy/paste packets for competitor models.
* Ask the user to paste back outputs.
* Keep a compact state summary after each step so the run can resume.

## Installation notes

Hermes-style directory example:

```bash
mkdir -p \~/.hermes/skills/ai-agents/flywheel-ideation-planning
cp SKILL.md \~/.hermes/skills/ai-agents/flywheel-ideation-planning/SKILL.md
```

OpenClaw-style directory example:

```bash
mkdir -p \~/.openclaw/skills/flywheel-ideation-planning
cp SKILL.md \~/.openclaw/skills/flywheel-ideation-planning/SKILL.md
```

Workspace-local example:

```bash
mkdir -p ./skills/flywheel-ideation-planning
cp SKILL.md ./skills/flywheel-ideation-planning/SKILL.md
```

Intended slash command:

```text
/flywheel-ideation-planning
```

