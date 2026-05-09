---
name: flywheel-swarm-implementation-and-polish
version: 1.0.0
description: >-
  Run Phases 3 and 4 of Jeffrey Emanuel-style Agent Flywheel workflow:
  spawn a parallel agent swarm against the bead graph produced in Phase
  2, operate the swarm via NTM and Agent Mail on a steady cadence, and
  cycle review-test-polish prompts until the codebase reaches a clean
  steady state. Use after the user has a polished bead graph in the
  Beads database, AGENTS.md configured, and the Agent Mail server
  running. Designed for the Hermes harness running against a
  VPS-hosted multi-agent environment.
metadata:
  category: implementation
  tags:
    - flywheel
    - agent-swarm
    - parallel-implementation
    - review
    - testing
    - polish
    - ntm
    - agent-mail
    - beads
    - bv
    - agent-harness
    - hermes
    - vps
    - tmux
    - ultrathink
    - frontier-models
  intended_harnesses:
    - Hermes
    - OpenClaw
    - Claude Code-compatible skill loaders
    - Generic markdown skill harnesses
  slash_commands:
    - flywheel-swarm-implementation-and-polish
    - flywheel-phase-3-4
    - swarm-implement-and-polish
    - launch-swarm
---

# Flywheel Phases 3 & 4 — Swarm Implementation, Review, Testing & Polish Skill

## Purpose

This skill operationalizes **Phase 3: Agent Swarm Implementation** and **Phase 4: Review, Testing & Polish** of a Flywheel-style agentic software workflow. It spawns a parallel swarm of generalist agents against the bead graph produced in Phase 2, operates the swarm on a steady cadence, and cycles review-test-polish prompts until the codebase reaches a clean steady state.

The skill is structured as one continuous loop, not a sequence of discrete steps, because implementation and review are not sequential in this workflow — they are interleaved, with review prompts triggered repeatedly throughout execution and run until the codebase settles.

The skill organizes the work into six segments:

1. **Pre-flight** — Verify prerequisites, confirm AGENTS.md is current, confirm Agent Mail and NTM are healthy, and prepare the initial marching orders prompt.
2. **Spawn** — Launch the agent swarm with NTM and broadcast the exact initial prompt to all agents.
3. **Operate** — Run the operator cadence: check `bv` triage, glance at Agent Mail, watch for stuck beads, nudge agents post-compaction, and trigger the next-bead prompt as needed.
4. **Review and polish loop** — Trigger self-review, cross-review, random-exploration, test-coverage, and UI/UX prompts on rotation until the loop reaches steady state (reviews come back clean).
5. **Commit and ship** — Have agents commit logically grouped changes with detailed messages and push.
6. **Report** — Generate a single human-readable markdown report summarizing what the swarm built, what changed during review, the steady-state evidence, and recommendations for Phase 5 (deploy and maintenance).

This skill is for **execution space**. Unlike Phases 1 and 2, the agent running this skill is *orchestrating* — it does not write production code itself. The swarm writes the code; this skill keeps the swarm healthy and pointed at the right work.

## Why this protocol exists

Single-agent implementation has predictable failure modes that compound at scale:

* **Serial bottlenecking.** One agent can only do one thing at a time. A 50-bead project with parallelizable work runs in ~1/N the wall-clock time when the swarm coordinates correctly.
* **Tunnel vision.** A single agent that wrote a piece of code is the worst auditor of that code. Cross-agent review surfaces issues the original author cannot see.
* **Compaction amnesia.** Long Claude Code sessions hit context compaction. Without an explicit re-grounding prompt, agents forget AGENTS.md tool conventions and quietly degrade.
* **Communication purgatory.** Without an explicit warning in the prompt, agents will spend hours waiting on each other instead of working in parallel and announcing progress.

The protocol is calibrated to address each of these:

* NTM spawns a heterogeneous swarm (Claude Code + Codex + Gemini) so different priors are looking at the same code.
* Agent Mail provides file reservations and structured messaging so agents don't clobber each other.
* Beads + `bv` give the swarm a shared, prioritized work queue; any agent can pick up any bead.
* The exact prompts include "ultrathink," explicit anti-purgatory instructions, and forced re-reads of AGENTS.md after compaction.
* Review cycles run until they come back clean — the *steady-state signal* — rather than for a fixed number of passes.

The leverage in this phase is not in the prompts being clever. It is in (a) running the *exact* canonical prompts, (b) running review cycles to convergence rather than a fixed budget, and (c) keeping the operator cadence boring and consistent so the swarm self-heals.

## When to use this skill

Use this skill when:

* The Beads database has a polished, reviewed bead graph (Phase 2 complete).
* `AGENTS.md` exists in the project root and references the relevant tool blurbs (Beads/`br`, BV, Agent Mail, NTM, CASS/CM/UBS/DCG/SLB if installed).
* The Agent Mail server is reachable.
* The user wants to start parallel implementation, or wants to resume a swarm session that was paused.
* The user says: "launch the swarm," "run Phase 3," "run Phase 3 and 4," "start implementation," "polish the codebase," or any equivalent.

Do not use this skill for:

* Projects without a bead graph. Run `flywheel-decompose-into-beads` first.
* Projects without `AGENTS.md`. Stop and ask the user to author it (or to confirm an existing one is current).
* Single-bead bug fixes. A swarm is overkill; one Claude Code session is faster.
* Projects already in deploy/maintenance mode. That is Phase 5; use a different skill.
* Direct human implementation. The whole point of this skill is to drive the swarm; if the user wants to write code themselves, they don't need this skill running.

## Prerequisites

Before launching the swarm, verify:

1. **Beads graph is healthy.** `br list --all` returns a non-trivial graph; `bv --robot-triage` returns a coherent recommendation; `bv --robot-insights | jq '.Cycles'` returns no cycles.
2. **AGENTS.md exists and is current.** Verify it references: `br` (Beads), `bv` with the robot flags, Agent Mail registration, file reservation patterns, and any other tools the swarm will use (CASS, CM, UBS, DCG, SLB, CAAM, RU as applicable).
3. **Agent Mail server is running.** Either via `am` or `~/projects/mcp_agent_mail/scripts/run_server_with_token.sh`. The server must be reachable from inside the agent tmux sessions.
4. **NTM is installed and working.** `ntm --help` returns; `ntm list` returns the current session set.
5. **BV is installed.** `bv --robot-triage --help` returns. Bare `bv` is interactive and will block sessions — never invoke it bare.
6. **CLI auth is fresh.** Each model that will be in the swarm (Claude Code, Codex, Gemini) is authenticated. If CAAM is in use, the relevant profiles are loaded.
7. **Repo is in a clean state.** Uncommitted changes should be committed or stashed before the swarm starts touching files. The pre-commit guard depends on file reservations from Agent Mail; conflicting local changes will surface as confusing failures.
8. **The user has approved the swarm size and model mix.** This is a real budget decision — every agent burns tokens.

If any prerequisite is missing, stop and surface it. Do not "best-effort" launch a swarm against a broken environment — partial swarms produce inconsistent code that's harder to debug than no code at all.

## Required capabilities

The Hermes harness running this skill must be able to:

1. SSH or otherwise connect to the VPS hosting the swarm.
2. Run `ntm spawn` and `ntm send` from outside the agent tmux sessions.
3. Read `bv --robot-*` output and parse JSON.
4. Read Agent Mail thread state (via the `am` CLI or HTTP API).
5. Read and write files in the project workspace.
6. Send long-form prompt content to agents via `ntm send` without truncation, smart-quote substitution, or shell-escape mangling. The exact prompts contain quotes, em-dashes, and "AGENTS dot md" verbatim — preserve them.
7. Detach from the swarm and reattach later without killing it.

If any capability is unavailable, surface the limitation instead of silently degrading.

## Model mix and swarm sizing

Recommended starting mix:

```text
Default swarm (medium project):
  3 Claude Code agents (Opus 4.7 or latest frontier Anthropic model)
  2 Codex agents (latest frontier OpenAI model)
  1 Gemini agent (latest frontier Google model)

Smaller swarm (learning, small scope):
  1 Claude Code + 1 Codex
  Or: 2 Claude Code

Larger swarm (mature project, deep work):
  Up to 5 of each, scaled to the user's budget.
```

Rationale:

* Every agent is fungible; specialization doesn't come from the prompt, it comes from AGENTS.md plus the bead the agent picks up. Don't try to assign "frontend agent" or "backend agent" roles via the launch prompt.
* Mixing model families is genuinely useful: different priors catch different bugs in cross-review.
* **Stagger agent starts by at least 30 seconds** to avoid the thundering-herd problem where every agent grabs the same top bead.
* Start smaller than ego suggests. 1 agent to learn, 2 to feel coordination, 4 for real swarm behavior. Add agents incrementally if the bead graph supports more parallelism.

Do not silently substitute smaller models. The implementation and review prompts assume frontier-level reasoning and "Use ultrathink" — a smaller model will produce code the swarm then has to throw away.

## Artifact directory

At the start of the run, create or reuse this directory in the project root:

```text
.flywheel/phase-3-4/
├── 00-session-info.md            Swarm metadata: agents, models, ntm names, started-at
├── 01-launch-prompt.txt          Exact text sent to agents at launch (the marching orders)
├── 02-prompt-library/            Copies of the exact prompts (one file per prompt) for replay
├── 03-operator-log.md            Append-only log of every operator action and timestamp
├── 04-review-cycles/             One folder per review pass, with the prompt sent and the result
│   ├── cycle-01-self-review/
│   ├── cycle-02-cross-review/
│   ├── cycle-03-random-exploration/
│   ├── cycle-04-test-coverage/
│   ├── cycle-05-ui-ux-scrutiny/
│   └── cycle-N-...
├── 05-bead-progression.md        Snapshot of bead state at key checkpoints
├── 06-steady-state-evidence.md   The clean-review evidence that ended the loop
├── 07-commit-log.md              Final commit groupings and messages
└── REPORT_FINAL.md               Final human-readable report (last segment deliverable)
```

The codebase itself is the primary artifact, not a markdown file. The artifacts above are the audit trail and the human-facing summary. Never claim a file was saved unless it actually was.

## Resumability

At the start of each run, inspect `.flywheel/phase-3-4/` and the NTM session set:

```text
If no NTM session for this project exists and 00-session-info.md is missing:
  resume at Pre-flight (segment 1).

If NTM sessions exist but 01-launch-prompt.txt is missing:
  the swarm exists but was not launched via this skill — surface to the user
  and ask whether to take ownership or start fresh.

If NTM sessions exist and 01-launch-prompt.txt exists but 03-operator-log.md
shows no recent activity (>30 minutes):
  resume at Operate (segment 3) by checking swarm health first.

If 04-review-cycles/ shows partial cycles and 06-steady-state-evidence.md is missing:
  resume at Review and polish loop (segment 4) from the next cycle.

If 06-steady-state-evidence.md exists but 07-commit-log.md is missing:
  resume at Commit and ship (segment 5).

If 07-commit-log.md exists but REPORT_FINAL.md is missing:
  resume at Report (segment 6).
```

When resuming, say:

```text
Looks like we left off at [segment]. The swarm [is/is not] currently alive on the VPS. I can resume from there or restart Phases 3-4. I recommend continuing unless the bead graph or AGENTS.md has materially changed since the last run.
```

Do not ask this if the user has already explicitly told you where to resume.

---

# Segment 1 — Pre-flight

## Pre-flight goal

Verify every prerequisite before any token is spent on the swarm. Pre-flight failures are cheap; mid-swarm failures are expensive.

## Procedure

1. SSH to the VPS as the project user and `cd` to the project root.
2. Run the prerequisite checks in this order, capturing each result:

   ```bash
   # Beads health
   br list --all | head -50
   bv --robot-triage
   bv --robot-insights | jq '.Cycles'
   bv --robot-insights | jq '.bottlenecks'

   # AGENTS.md
   test -f AGENTS.md && wc -l AGENTS.md && grep -c "br\|bv\|Agent Mail" AGENTS.md

   # Agent Mail
   am --health   # or curl the health endpoint, depending on installation

   # NTM
   ntm --version
   ntm list

   # CLIs
   claude --version
   codex --version 2>/dev/null || echo "codex not installed"
   gemini --version 2>/dev/null || echo "gemini not installed"

   # Repo state
   git status --porcelain
   git rev-parse HEAD
   ```

3. If any check fails, stop and surface to the user. Do not "best-effort" past missing prerequisites.

4. If `bv --robot-insights` reports cycles in the bead graph, **STOP**. Cycles will deadlock the swarm. Send the user back to Phase 2 to fix the graph.

5. If AGENTS.md is older than the bead graph or older than the most recent change to project tooling, ask the user whether to refresh it before launch. Stale AGENTS.md is a leading cause of agent confusion.

6. Decide swarm composition with the user:

   ```markdown
   ## Proposed swarm composition

   - 3 Claude Code agents (Opus 4.7)
   - 2 Codex agents
   - 1 Gemini agent
   - Total: 6 agents

   Stagger: 30 seconds between starts.
   Initial bead capacity: <bv estimate of parallelizable beads>.

   Approve, modify, or specify a different mix?
   ```

7. Capture session metadata to `00-session-info.md`:

   ```markdown
   # Phase 3-4 Session Info

   - Project name: <name>
   - Project root: <absolute path>
   - VPS host: <host>
   - Started at (UTC): <timestamp>
   - Beads database: <path>
   - Beads at start: <count>
   - Open beads at start: <count>
   - In-progress beads at start: <count>
   - Closed beads at start: <count>
   - AGENTS.md SHA-256: <hash>
   - Initial git HEAD: <commit hash>
   - Swarm composition:
     - <agent name>: <model> (NTM session: <name>)
     - <agent name>: <model> (NTM session: <name>)
     - ...
   - Agent Mail server: <url or path>
   ```

8. Write the launch prompt to `01-launch-prompt.txt` (verbatim — see Segment 2).

9. Copy each canonical prompt to `02-prompt-library/` as a separate file so replays are byte-identical:

   ```text
   02-prompt-library/
     01-initial-marching-orders.txt
     02-move-to-next-bead.txt
     03-self-review.txt
     04-post-compaction.txt
     05-cross-agent-review.txt
     06-random-exploration.txt
     07-commit-changes.txt
     08-test-coverage.txt
     09-ui-ux-scrutiny.txt
     10-deep-ui-ux-enhancement.txt
   ```

   The exact text of each is in the relevant segment below.

## Pre-flight quality gates

Do not proceed to Spawn unless:

1. `br list` returns a non-trivial graph.
2. `bv --robot-triage` returns a coherent recommendation.
3. `bv --robot-insights | jq '.Cycles'` returns no cycles.
4. `AGENTS.md` exists and references the relevant tools.
5. Agent Mail server responds healthy.
6. `ntm` and at least one CLI (`claude`, `codex`, `gemini`) are installed and authenticated.
7. The repo is in a clean state.
8. The user has approved the swarm composition.

---

# Segment 2 — Spawn the Swarm

## Spawn goal

Launch the swarm with NTM and broadcast the exact initial marching orders to every agent. From this moment forward, the swarm is alive on the VPS and consuming tokens.

## Procedure

1. From outside the agent sessions (i.e., from your Hermes-driven shell), spawn the swarm with NTM. Use a project-scoped NTM name:

   ```bash
   ntm spawn <project-name> --cc=3 --cod=2 --gmi=1
   ```

   Adjust the flags to match the swarm composition approved in Pre-flight. NTM creates one tmux session/pane per agent in the project folder.

2. Stagger the agent launches by at least 30 seconds. If `ntm spawn` does not stagger automatically, send the launch prompt to one agent at a time with sleep between sends.

3. Confirm each agent is alive:

   ```bash
   ntm list
   ntm status <project-name>
   ```

   You should see one entry per agent, all idle and waiting for the first prompt.

4. Send the **exact initial marching orders** to all agents:

   ```bash
   ntm send <project-name> --all "$(cat .flywheel/phase-3-4/01-launch-prompt.txt)"
   ```

   You can also broadcast per model class if you want to vary which agents get the prompt first:

   ```bash
   ntm send <project-name> --cc "$(cat ...)"
   sleep 30
   ntm send <project-name> --cod "$(cat ...)"
   sleep 30
   ntm send <project-name> --gmi "$(cat ...)"
   ```

5. Append a launch entry to `03-operator-log.md`:

   ```markdown
   ## <UTC timestamp> — Swarm launched
   - NTM project: <name>
   - Agents launched: <count>
   - Prompt: 01-initial-marching-orders.txt
   - Initial bead capacity per `bv --robot-plan`: <count parallel tracks>
   ```

## The exact prompt — Initial Marching Orders

Use this prompt **exactly as written**. Do not edit, shorten, paraphrase, "improve," normalize, change "AGENTS dot md" to "AGENTS.md," or remove any wording. The "Use ultrathink" suffix is part of the prompt.

```text
First read ALL of the AGENTS dot md file and README dot md file super carefully and understand ALL of both! Then use your code investigation agent mode to fully understand the code, and technical architecture and purpose of the project. Then register with MCP Agent Mail and introduce yourself to the other agents.

Be sure to check your agent mail and to promptly respond if needed to any messages; then proceed meticulously with your next assigned beads, working on the tasks systematically and meticulously and tracking your progress via beads and agent mail messages.

Don't get stuck in "communication purgatory" where nothing is getting done; be proactive about starting tasks that need to be done, but inform your fellow agents via messages when you do so and mark beads appropriately.

When you're not sure what to do next, use the bv tool mentioned in AGENTS dot md to prioritize the best beads to work on next; pick the next one that you can usefully work on and get started. Make sure to acknowledge all communication requests from other agents and that you are aware of all active agents and their names. Use ultrathink.
```

## Spawn quality gates

Do not proceed to Operate unless:

1. `ntm list` shows every expected agent alive.
2. The launch prompt was sent to every agent.
3. Within 5 minutes, the operator log shows agents have registered with Agent Mail (visible in `am` thread state) — this confirms the prompt actually landed and agents are following it.
4. No agent has crashed or returned an immediate error.

If an agent failed to register with Agent Mail within 5 minutes, the prompt may not have landed cleanly. Re-send to that specific agent.

---

# Segment 3 — Operate the Swarm

## Operate goal

Keep the swarm healthy and pointed at the right work. The operator role is *boring on purpose*: a steady ~10-15 minute cadence of small checks. The single biggest mistake is over-managing — every nudge is an interruption that costs context.

## The operator cadence

Every 10-15 minutes (longer for large/stable swarms; shorter when something feels off), do this:

1. **Check `bv --robot-triage`.** Does the top recommendation still make sense given recent commits and bead state? If yes, do nothing. If no, ask why — the graph may have drifted.

2. **Glance at Agent Mail threads.** Are agents making progress, or is someone stuck waiting on someone else? Look for threads with no activity in the last 15-20 minutes that are still marked open.

3. **Look for stuck beads.** `br list --status=in_progress` and check timestamps. Beads stuck `in_progress` with no recent agent activity are a flag. They might mean an agent crashed mid-bead, or hit context compaction without recovering, or got into a confused state.

4. **Check for compaction signals.** If an agent has gone quiet or its responses suddenly look generic, it may have just compacted. The fix is the post-compaction prompt (see below).

5. **Check for "communication purgatory."** If two or more agents are sending messages back and forth without anyone *actually doing work*, intervene with a "move to next bead" prompt. The launch prompt warns against this, but it still happens.

6. **Confirm no agent is destructively wrong.** A glance at recent commits or recent `br` activity is usually enough. SLB and DCG should catch the worst, but don't fully trust them.

7. **Append an entry to `03-operator-log.md`** for every action taken:

   ```markdown
   ## <UTC timestamp> — Cadence check
   - bv top recommendation: <bead id, makes sense / doesn't make sense>
   - Agent Mail health: <ok / N stuck threads>
   - Stuck beads: <list or none>
   - Actions taken: <none / nudged agent X with prompt Y>
   ```

The cadence is *the work* during this segment. The temptation to keep typing prompts at the swarm is itself a failure mode — let the agents work.

## The exact prompt — Move to Next Bead

When an agent finishes a bead and goes idle, or when an agent is stalled on a bead it shouldn't keep working on, send this **exactly**:

```text
Reread AGENTS dot md so it's still fresh in your mind. Use ultrathink. Use bv with the robot flags (see AGENTS dot md for info on this) to find the most impactful bead(s) to work on next and then start on it. Remember to mark the beads appropriately and communicate with your fellow agents. Pick the next bead you can actually do usefully now and start coding on it immediately; communicate what you're working on to your fellow agents and mark beads appropriately as you work. And respond to any agent mail messages you've received.
```

Send to a single agent with `ntm send <project-name> --to=<agent-name> "$(cat ...)"` or to a class with `--cc`/`--cod`/`--gmi`. Avoid `--all` for this prompt — broadcasting it triggers thundering-herd on the next bead.

## The exact prompt — Post-Compaction

When an agent compacts its context (Claude Code shows a compaction event; or you notice a sudden quality drop / forgotten tool conventions), send this **immediately and exactly**:

```text
Reread AGENTS dot md so it's still fresh in your mind. Use ultrathink.
```

Short, on purpose. The point is to re-establish AGENTS.md context without flooding the freshly-compacted window with new instructions.

## When to escalate to "kill and respawn"

If an agent is degraded — repeating mistakes, ignoring the bead system, refusing to communicate via Agent Mail, or producing low-quality code despite re-grounding — kill it and start a fresh one:

```bash
ntm kill <project-name> --agent=<agent-name>
ntm spawn <project-name> --cc=1   # or --cod=1, --gmi=1 to match
ntm send <project-name> --to=<new-agent-name> "$(cat .flywheel/phase-3-4/01-launch-prompt.txt)"
```

Agents are fungible. The bead remains marked `in_progress`; any other agent (including the new one) can resume it. Failure recovery is supposed to be cheap — use it.

## Operate quality gates

Do not proceed to Review and polish loop until:

1. The bead graph has materially advanced (a meaningful percentage of beads have moved from open → in_progress → closed). The exact threshold is project-specific; the user decides.
2. There is at least one batch of completed work to review.
3. The operator log shows steady cadence checks were happening — not a long silent stretch.

It is fine for Operate and Review and polish loop to interleave repeatedly. Implementation is rarely "done" and *then* reviewed — review prompts run throughout. The segment boundary here is mostly conceptual.

---

# Segment 4 — Review and Polish Loop

## Loop goal

Cycle through the canonical review/test/polish prompts until the swarm consistently returns clean — no bugs found, no changes made, no further improvements proposed. This is the **steady-state signal**, and it is the actual exit condition for Phases 3-4. Do not exit on a fixed cycle count.

## The cycle order

Run prompts in this rotation. Each cycle = one prompt sent to a relevant subset of agents. After each cycle, capture the result.

```text
1. Self-Review            — agents review their own recent work
2. Cross-Agent Review     — agents review each other's work
3. Random Exploration     — agents pick code at random and audit it
4. Test Coverage          — check test coverage and create beads if gaps exist
5. UI/UX Scrutiny         — first pass at UI/UX issues (only if project has UI)
6. Deep UI/UX Enhancement — second deep pass on UI/UX (only if project has UI)
7. Repeat from 1.
```

For projects without a UI, skip cycles 5-6 and rotate through 1-4.

For projects without tests, cycle 4 will surface a need to create test beads — feed those beads back through the swarm via Operate, then resume the loop.

## Capturing each cycle

For each cycle, create a folder under `04-review-cycles/`:

```text
cycle-<NN>-<cycle-name>/
├── prompt-sent.txt         The exact prompt text broadcast (byte-identical to library)
├── target-agents.txt       Which agents received it
├── timestamp.txt           When it was sent
├── ntm-output.log          Captured agent responses
└── outcome.md              What changed: bugs found, fixes applied, beads created, or "clean"
```

`outcome.md` is the load-bearing artifact. Without a clear outcome statement, you cannot tell whether the loop has reached steady state.

## The exact prompt — Self-Review (after bead completion)

Use **exactly**:

```text
Great, now I want you to carefully read over all of the new code you just wrote and other existing code you just modified with "fresh eyes" looking super carefully for any obvious bugs, errors, problems, issues, confusion, etc. Carefully fix anything you uncover. Use ultrathink.
```

Send to whichever agent(s) recently completed beads. Send right after a bead is marked closed; the model's working memory of the change is freshest then.

**Run this in repeated rounds until they stop finding bugs.**

## The exact prompt — Cross-Agent Review

Use **exactly**:

```text
Ok can you now turn your attention to reviewing the code written by your fellow agents and checking for any issues, bugs, errors, problems, inefficiencies, security problems, reliability issues, etc. and carefully diagnose their underlying root causes using first-principle analysis and then fix or revise them if necessary? Don't restrict yourself to the latest commits, cast a wider net and go super deep! Use ultrathink.
```

Broadcast to the swarm (or rotate which agent reviews which other agent's work). Cross-review is where the heterogeneous model mix earns its cost — different priors catch different bugs.

## The exact prompt — Random Exploration

Use **exactly**:

```text
I want you to sort of randomly explore the code files in this project, choosing code files to deeply investigate and understand and trace their functionality and execution flows through the related code files which they import or which they are imported by.

Once you understand the purpose of the code in the larger context of the workflows, I want you to do a super careful, methodical, and critical check with "fresh eyes" to find any obvious bugs, problems, errors, issues, silly mistakes, etc. and then systematically and meticulously and intelligently correct them.

Be sure to comply with ALL rules in AGENTS dot md and ensure that any code you write or revises conforms to the best practice guides referenced in the AGENTS dot md file. Use ultrathink.
```

Especially valuable late in the loop, when the obvious bugs have been caught and only deep cross-file issues remain.

## The exact prompt — Test Coverage

Use **exactly**:

```text
Do we have full unit test coverage without using mocks/fake stuff? What about complete e2e integration test scripts with great, detailed logging? If not, then create a comprehensive and granular set of beads for all this with tasks, subtasks, and dependency structure overlaid with detailed comments.
```

If this prompt creates new beads, feed them back through the swarm via Operate (segment 3) before resuming the review loop.

## The exact prompt — UI/UX Scrutiny

Skip for non-UI projects. Otherwise, use **exactly**:

```text
Great, now I want you to super carefully scrutinize every aspect of the application workflow and implementation and look for things that just seem sub-optimal or even wrong/mistaken to you, things that could very obviously be improved from a user-friendliness and intuitiveness standpoint, places where our UI/UX could be improved and polished to be slicker, more visually appealing, and more premium feeling and just ultra high quality, like Stripe-level apps.
```

## The exact prompt — Deep UI/UX Enhancement

Skip for non-UI projects. Otherwise, use **exactly**:

```text
I still think there are strong opportunities to enhance the UI/UX look and feel and to make everything work better and be more intuitive, user-friendly, visually appealing, polished, slick, and world class in terms of following UI/UX best practices like those used by Stripe, don't you agree? And I want you to carefully consider desktop UI/UX and mobile UI/UX separately while doing this and hyper-optimize for both separately to play to the specifics of each modality. I'm looking for true world-class visual appeal, polish, slickness, etc. that makes people gasp at how stunning and perfect it is in every way. Use ultrathink.
```

This is the *second* UI/UX pass and is intentionally more demanding than the first. Use it after the first pass has settled.

## Steady-state signal

The loop exits when **all of the following are true** for at least one consecutive full rotation:

1. Self-review returns clean — no new bugs, no fixes applied.
2. Cross-review returns clean — no issues found in other agents' code.
3. Random exploration returns clean — no problems found in randomly chosen files.
4. Test coverage prompt either confirms full coverage or creates beads which have themselves been completed and reviewed.
5. (If UI) UI/UX prompts return that the system is at the desired polish level.

Capture this in `06-steady-state-evidence.md`:

```markdown
# Steady-State Evidence

## Final clean rotation (start: <timestamp>, end: <timestamp>)

### Self-review (cycle <NN>)
- Outcome: clean
- Agents involved: <list>

### Cross-review (cycle <NN>)
- Outcome: clean
- Agents involved: <list>

### Random exploration (cycle <NN>)
- Outcome: clean
- Files explored: <count or list>

### Test coverage (cycle <NN>)
- Outcome: <full coverage confirmed | beads created and completed | waived by user>

### UI/UX (cycle <NN>, <NN+1>)
- Outcome: <at desired polish | not applicable>

## Bead state at steady state
- Total beads: <N>
- Closed: <N>
- Open: <N>  (only ideas-marked-future are acceptable here)
- In progress: <should be 0 or near-0>

## Net diff from launch
- Files added/modified/deleted: <counts>
- Tests added: <count>
- Lines of code: <delta>
```

## Anti-pattern: declaring steady state too early

The most common failure here is declaring steady state after one clean cycle. The loop wants **a full rotation clean**, not one prompt clean. A single clean self-review while cross-review still finds issues is not steady state.

If the user is impatient, surface this explicitly:

```text
Self-review came back clean, but we haven't run cross-review or random-exploration since the last batch of changes. I recommend continuing one more full rotation. If you want to ship now anyway, I'll log "steady state declared early" in the evidence file.
```

## Loop quality gates

Do not proceed to Commit and ship until:

1. `06-steady-state-evidence.md` exists and shows a clean full rotation (or an explicit user override).
2. No bead is stuck `in_progress`.
3. The bead graph has no orphan open beads that should be closed.
4. The operator log shows no unresolved escalations.

---

# Segment 5 — Commit and Ship

## Commit goal

Land all of the swarm's work as a series of logically-grouped commits with detailed messages, push to the remote, and leave the codebase in a clean state ready for Phase 5 (deploy and maintenance).

## Procedure

1. Pick one agent to do the commit work — typically the Claude Code agent with the most context on the recent changes. Do not have multiple agents commit in parallel; that creates merge headaches.

2. Send the **exact commit prompt**:

   ```text
   Now, based on your knowledge of the project, commit all changed files now in a series of logically connected groupings with super detailed commit messages for each and then push. Take your time to do it right. Don't edit the code at all. Don't commit obviously ephemeral files. Use ultrathink.
   ```

   Note the explicit "Don't edit the code at all" — this segment is for committing, not for last-minute changes.

3. Watch the agent's progress in `ntm`. When it completes:

   ```bash
   git log --oneline -20 > .flywheel/phase-3-4/07-commit-log.md
   git status --porcelain >> .flywheel/phase-3-4/07-commit-log.md
   ```

4. If the agent committed and pushed cleanly, the segment is done. If it surfaced merge conflicts, ephemeral-file ambiguity, or push-permission errors, surface them to the user — do not let the agent improvise on these.

## Commit quality gates

Do not proceed to Report until:

1. `git status --porcelain` returns clean (or only contains files the user explicitly wants uncommitted).
2. `git log` shows the new commits with substantive messages.
3. The remote has been pushed (or the user has explicitly waived push).

---

# Segment 6 — Generate Report

## Report goal

Produce one human-readable markdown report that lets the user understand what the swarm built, what the review loop changed, and the evidence that the codebase reached a clean steady state — without having to read the operator log, the cycle folders, or any of the agent transcripts.

## Procedure

1. Read:

   * `00-session-info.md`,
   * `03-operator-log.md`,
   * each `04-review-cycles/cycle-NN-*/outcome.md`,
   * `05-bead-progression.md`,
   * `06-steady-state-evidence.md`,
   * `07-commit-log.md`,
   * `git log` since the launch commit.

2. Write `REPORT_FINAL.md` using the template below.

## Report template: `REPORT_FINAL.md`

```markdown
# [Project Name] — Phases 3 & 4 Report

*Generated: [date]. Methodology: Flywheel Phases 3-4 — parallel agent swarm implementation followed by review-test-polish loop run to steady state.*

## 1. Executive Summary

- Project: [name]
- Source bead graph: <count> beads at launch, <count> at steady state
- Swarm composition: <model mix>
- Wall-clock duration: launch <timestamp> → steady state <timestamp>
- Net diff: <files changed>, <lines added/removed>, <tests added>
- Final commits: <count>
- Pushed to: <remote>

## 2. What the Swarm Built

[Narrative paragraph describing what was implemented. Group by major feature or subsystem, not by bead. The reader should be able to walk away understanding what now exists in the codebase.]

### By subsystem

#### <subsystem name>
- Beads completed: <ids>
- Files changed: <high-level list, not exhaustive>
- Notable decisions: <anything material the agents decided that the plan didn't pre-specify>

[Repeat for each subsystem.]

## 3. The Review Loop in Numbers

| Cycle | Type | Outcome | Bugs found | Fixes applied | New beads |
|---|---|---|---|---|---|
| 01 | Self-review | Issues found | <N> | <N> | <N> |
| 02 | Cross-review | Issues found | <N> | <N> | <N> |
| ... | ... | ... | ... | ... | ... |
| <last> | <type> | Clean | 0 | 0 | 0 |

Total cycles run: <N>
Cycles to first clean rotation: <N>

## 4. Notable Issues Caught in Review

[Highlight the most consequential bugs/issues caught by review that would have shipped if the loop had been skipped. This is the section that justifies the cost of the review-to-steady-state loop.]

- <issue>: caught by <cycle type, cycle NN>, fixed by <agent>
- ...

## 5. Steady-State Evidence

[Summarize 06-steady-state-evidence.md in prose. Show the final clean rotation and the bead state at steady state.]

## 6. Operator Interventions

[Summary of significant operator actions from 03-operator-log.md. Examples: agents killed and respawned, post-compaction nudges, communication-purgatory rescues, escalations.]

- Agents killed/respawned during the run: <count>
- Post-compaction nudges sent: <count>
- Communication-purgatory rescues: <count>

## 7. Commits and Push

[List the final commit groupings with their messages, pulled from 07-commit-log.md. Group by logical change. Include the final HEAD commit hash.]

## 8. Open Questions and Watch-Outs for Phase 5

[Anything the swarm or the operator flagged that the user should resolve before deploy. Examples:]

- Configuration that's currently hardcoded and should be environment-variable-driven
- Test gaps the user explicitly waived
- Integration points that are stubbed and need real credentials before deploy
- Performance concerns the swarm noted but did not optimize

## 9. Recommended Next Phase

Phase 5 (Deploy and Maintenance) can now begin.

Suggested first steps:
- [Concrete deploy step appropriate to the stack]
- Run smoke tests on the deployed environment
- Set up the daily autopilot prompts for ongoing maintenance

## 10. Appendix

- `00-session-info.md` — swarm metadata
- `01-launch-prompt.txt` — exact marching orders sent at launch
- `02-prompt-library/` — every canonical prompt used in this run
- `03-operator-log.md` — append-only operator action log
- `04-review-cycles/` — per-cycle artifacts
- `05-bead-progression.md` — bead state snapshots
- `06-steady-state-evidence.md` — evidence that the loop converged
- `07-commit-log.md` — final commit details
```

## Final response when Phases 3-4 are complete

Use this structure when reporting completion to the user:

```markdown
Phases 3 & 4 are complete.

Produced:
- `.flywheel/phase-3-4/00-session-info.md`
- `.flywheel/phase-3-4/01-launch-prompt.txt`
- `.flywheel/phase-3-4/02-prompt-library/` (10 files)
- `.flywheel/phase-3-4/03-operator-log.md`
- `.flywheel/phase-3-4/04-review-cycles/` (<N> cycles)
- `.flywheel/phase-3-4/06-steady-state-evidence.md`
- `.flywheel/phase-3-4/07-commit-log.md`
- `.flywheel/phase-3-4/REPORT_FINAL.md`
- Pushed commits: <count> on <branch>

### Headline numbers
- Beads at launch: <N>; at steady state: <M>
- Cycles run: <N>; cycles to first clean rotation: <K>
- Operator interventions: <kills>, <nudges>, <rescues>
- Net diff: <files>, <+lines/-lines>, <tests added>

### Recommended next step
Read `REPORT_FINAL.md`. When you're satisfied with the result, kick off Phase 5 (Deploy and Maintenance).

Do not deploy unless the user explicitly approves.
```

---

# Global quality gates

Phases 3-4 are complete only when:

* Pre-flight passed cleanly or every failure was explicitly resolved.
* The launch prompt was sent verbatim to every agent.
* `03-operator-log.md` shows steady cadence — not a long silent gap that suggests the operator stopped attending.
* Every review-loop cycle has a captured outcome.
* `06-steady-state-evidence.md` exists and shows a clean full rotation, or the user explicitly waived steady-state with a recorded reason.
* All commits are pushed (or push was explicitly waived).
* `REPORT_FINAL.md` exists and covers what was built, what review caught, and the steady-state evidence.

---

# Failure modes and recovery

## Communication purgatory

Symptom: Two or more agents are sending Agent Mail messages back and forth without anyone actually editing files. Bead state hasn't moved in 20+ minutes.

Recovery: Send the **Move to Next Bead** prompt to each agent in the purgatory thread, individually. Do not broadcast — broadcast triggers thundering-herd. The launch prompt warns against communication purgatory, but it still happens, especially with smaller models.

## Thundering herd on launch

Symptom: All agents grab the same top bead within seconds of launch, then collide on file reservation.

Recovery: This is what the 30-second stagger is for. If it happens, kill all but one agent on the contested bead, then re-broadcast Move to Next Bead to the others.

## Compaction amnesia

Symptom: Agent's responses suddenly look generic; agent forgets to use `br`, forgets file reservations, forgets fellow agents' names.

Recovery: Send the **Post-Compaction** prompt immediately. Short on purpose. If amnesia recurs within the same session, the agent has likely degraded — kill and respawn.

## Agent crash mid-bead

Symptom: NTM session is dead or unresponsive; bead is still marked `in_progress`.

Recovery: Agents are fungible. Spawn a replacement (`ntm spawn ... --cc=1`) and send the launch prompt. The bead remains `in_progress`; another agent (the new one or an existing one) will pick it up.

## Bead graph drift

Symptom: `bv --robot-triage` is recommending beads that no longer make sense; the graph has gotten out of sync with reality.

Recovery: This usually means the swarm is doing things the bead graph didn't anticipate. Pause new bead assignments. Either (a) update the bead graph to match what's actually happening, or (b) reel the swarm back to the planned graph. Do not let the graph and the codebase silently drift further apart.

## Cycles in the bead graph

Symptom: `bv --robot-insights | jq '.Cycles'` returns a non-empty array.

Recovery: STOP. Cycles deadlock the swarm. This should have been caught in Pre-flight. Send the user back to Phase 2 to break the cycle.

## Pre-commit guard rejection

Symptom: An agent tries to commit and is rejected by the pre-commit guard because of a missing or expired file reservation.

Recovery: This is the system working correctly. Have the agent re-reserve the relevant files via Agent Mail and retry the commit.

## Review loop never converges

Symptom: Self-review and cross-review keep finding new issues every rotation, well past the point where progress feels real.

Recovery: This usually means the swarm is finding *legitimate* issues that the original bead graph didn't fully capture. Don't force a steady-state declaration. Either (a) accept that the project is harder than estimated and keep going, or (b) carve off a smaller scope, ship that, and treat the rest as Phase 5 maintenance work. Do not paper over a non-converging review loop with an early "good enough" declaration.

## Steady state declared but tests fail

Symptom: The review loop returned clean but a CI run or local test invocation fails.

Recovery: Steady state was declared prematurely or the test coverage cycle was waived. Run the Test Coverage prompt; create beads for the test gaps; feed them through Operate; then re-run the review loop until clean.

## User wants to skip Phase 4 (review)

Recovery: Do not skip silently. Mark `06-steady-state-evidence.md` as "review waived by user" with a recorded reason. Note this prominently in `REPORT_FINAL.md`. Phase 5 will then ship code the swarm has not audited; that fact should be visible.

## Pushing fails (auth, branch protection, etc.)

Recovery: Surface to the user. Do not have an agent invent a workaround like force-push or branch-rename — those create traceability problems that compound through Phase 5.

---

# Harness implementation notes

## For Hermes (primary target)

* Treat this file as the active procedure for the Phase 3-4 orchestrator.
* Hermes does not run in the agent tmux sessions — it drives them from outside via SSH and `ntm send`.
* Persist the NTM project name and the artifact directory path in Hermes's per-project state so the swarm survives Hermes reconnects.
* The 10-15 minute operator cadence is real wall-clock time. Hermes should sleep between cadence checks rather than busy-looping.
* When sending prompts via `ntm send`, escape carefully — the canonical prompts contain quotes, em-dashes, and "AGENTS dot md" verbatim. Do not let the harness convert smart-quotes or rewrap whitespace.
* Capture every prompt sent to a per-cycle file before sending, so byte-identical replay is possible if a cycle needs to be re-run.

## For OpenClaw / generic skill harnesses

* If the harness has its own multi-session or multi-agent abstraction, use that in place of NTM where the mapping is faithful.
* If the harness cannot drive multiple agent classes (only Claude, no Codex/Gemini), document the constraint in `00-session-info.md` and proceed with a homogenous swarm.
* Persist all artifacts under `.flywheel/phase-3-4/` in the project root.
* Avoid granting code-modification tools to this skill — its scope is the swarm, not the codebase.

## For Claude Code / Codex / Gemini CLI style workflows

* Run from the project root.
* The skill assumes the harness is *outside* the agent sessions. If the harness *is* one of the agents, it cannot also act as operator without conflict — surface this and have the user run the operator role from a separate session.

## For chat-only workflows

* Phases 3-4 are awkward without a multi-session VPS environment but possible for small projects.
* Substitute multiple human-driven sessions for the swarm; the user becomes the de-facto NTM.
* Provide the user with copy/paste packets for every prompt.
* Keep the same artifact structure under `.flywheel/phase-3-4/`.
* Note the substitution prominently in `00-session-info.md` — a one-human swarm has very different dynamics than a six-agent swarm.

## Installation notes

Hermes-style directory example:

```bash
mkdir -p ~/.hermes/skills/ai-agents/flywheel-swarm-implementation-and-polish
cp SKILL.md ~/.hermes/skills/ai-agents/flywheel-swarm-implementation-and-polish/SKILL.md
```

OpenClaw-style directory example:

```bash
mkdir -p ~/.openclaw/skills/flywheel-swarm-implementation-and-polish
cp SKILL.md ~/.openclaw/skills/flywheel-swarm-implementation-and-polish/SKILL.md
```

Workspace-local example:

```bash
mkdir -p ./skills/flywheel-swarm-implementation-and-polish
cp SKILL.md ./skills/flywheel-swarm-implementation-and-polish/SKILL.md
```

Intended slash commands:

```text
/flywheel-swarm-implementation-and-polish
/flywheel-phase-3-4
```
