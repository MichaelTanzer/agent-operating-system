---
name: repo-cross-pollinate
description: "Use this skill whenever Michael sends a link to a public GitHub repository, even casually, with no instruction at all, or with prompts like “interesting?”, “what could I do with this?”, “look at this repo”, “apply this somewhere?”, “useful for TanzerBot?”, or “see if this is useful.” The skill examines the external repo in depth, identifies transferable ideas, maps them onto Michael’s existing repositories and idea list, drafts a proposal, runs the proposal past Claude Code and Codex for adversarial review, integrates only the suggestions that genuinely improve the plan, and emails Michael a final write-up with architecture flowcharts."
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [github, repository-analysis, cross-pollination, portfolio, proposals, email]
    related_skills: [github-repo-management, codebase-inspection, claude-code, codex, google-workspace]
---

# Repo Cross-Pollinate

## Purpose

When Michael sends a public GitHub repository link, Hermes should treat it as a research bid.

Michael is usually not asking for a generic repository summary. He wants to know whether the repository contains ideas, architecture, workflows, abstractions, or implementation patterns that should influence something he is already building or considering building.

The output is an emailed technical proposal, not a chat response and not an implementation PR.

The proposal should answer:

```text
What is genuinely interesting in this external repository?
Does any of it apply to Michael’s existing repos or idea list?
Which target project is the strongest fit?
What exactly would change?
What is the smallest useful implementation?
What are the risks?
What did Claude Code and Codex critique?
Which critiques were accepted, partially accepted, or rejected?
What does the architecture look like before and after?
```

---

## Trigger

Run this skill when Michael sends any public GitHub repository URL, including a bare link.

Examples:

```text
https://github.com/foo/bar
interesting? https://github.com/foo/bar
look at this — github.com/foo/bar
could any of this apply to TanzerBot?
what would you do with this repo?
saw this on HN, thoughts?
apply this somewhere?
is this useful for any of my projects?
```

Do **not** run the full pipeline when Michael is clearly asking a narrow factual question, such as:

```text
What license does this repo use?
Is this repo still maintained?
How many stars does this have?
What language is this written in?
Summarize this README only.
```

If Michael explicitly says not to run cross-pollination, obey that instruction.

Default behavior: **run the full pipeline without asking permission**.

---

## Operating Context

Hermes is Michael’s personal agent.

Assume access to some or all of the following, depending on the runtime environment:

```text
Shell
File I/O
Git
GitHub CLI, if installed
Ability to clone public repositories
Claude Code CLI, usually `claude`
Codex CLI, usually `codex`
Email-sending tool exposed by the harness
Michael’s local portfolio context
Michael’s GitHub repositories under MichaelTanzer
Michael’s idea list or portfolio notes
```

Michael’s current portfolio anchor is **TanzerBot**, a multi-agent equity research system. Many strong applications may land there, but Hermes must still check the full portfolio and idea list before assuming TanzerBot is the right target.

---

## Privacy and Safety Rules

Hermes must not execute untrusted code from the external repository unless Michael explicitly asks for that.

Allowed:

```text
Clone the repo
Read files
Inspect documentation
Search source code
Review package manifests
Review tests
Review GitHub Actions and CI files
Review issues or commit history when useful
Analyze static code structure
```

Not allowed without explicit permission:

```text
Running install scripts
Running package-manager lifecycle hooks
Executing binaries
Running unknown test suites
Running containers from the repo
Providing private secrets or credentials to external tools
```

When consulting Claude Code or Codex, Hermes must minimize private context exposure.

Prefer sending:

```text
Summaries of Michael’s repo architecture
Relevant file paths
Interface sketches
Small excerpts necessary for critique
Sanitized implementation notes
```

Avoid sending unless explicitly authorized:

```text
Private source files in full
Secrets
Credentials
Environment variables
Customer data
API keys
Trading logic that Michael treats as confidential
Unrelated private repository details
```

Hermes must not invent facts about Michael’s repositories or idea list. If the current architecture cannot be verified, state the uncertainty clearly and avoid drawing unsupported diagrams.

---

## Stage 0 — Preflight

Before deep analysis, perform a quick validation pass.

### 0.1 Validate the Repository

Confirm:

```text
The URL points to GitHub
The repository is public and reachable
The repository is not empty
The default branch can be inspected
The repo is not obviously malicious or irrelevant
```

If the repo is private, deleted, unreachable, or empty, email Michael or respond with a concise note asking for the correct link.

### 0.2 Create a Scratch Directory

Create a scratch workspace:

```bash
/tmp/xpoll-<repo-name>-<timestamp>
```

All intermediate artifacts should be saved there.

Recommended files:

```text
repo_analysis.md
portfolio_map.md
candidate_scores.md
proposal_v1.md
review_prompt.md
cc_review.json
codex_review.md
review_adjudication.md
proposal_final.md
current.mmd
proposed.mmd
current.png or current.svg
proposed.png or proposed.svg
email.html
```

### 0.3 Locate Michael’s Portfolio Context

Look for portfolio context in this order:

```text
Explicit context in Michael’s message
~/hermes/idea_list.md
~/hermes/portfolio.md
~/hermes/projects.md
Known local repo inventory
GitHub repos under MichaelTanzer, using `gh repo list MichaelTanzer --limit 100` if available
Previously cached Hermes portfolio context
```

If no portfolio context can be found, ask Michael once for the location of his idea list or repo inventory and cache the answer. Do not repeatedly ask.

### 0.4 Check Repository Size

If the external repo is enormous, for example more than roughly 100k lines of meaningful source code, do not pretend to digest the entire project exhaustively.

Instead:

```text
Identify the top-level architecture.
Find the likely focal subsystem.
Focus on docs, entry points, core modules, examples, and tests.
Flag the analysis as scoped.
```

If there is no obvious focal point in a very large repo, ask Michael which subsystem caught his attention.

### 0.5 Early License Scan

Check the external repository’s license.

Flag prominently if the repo uses a license that may constrain Michael’s likely use, especially:

```text
AGPL
GPL
SSPL
Non-commercial licenses
Custom restrictive licenses
No license
```

License constraints do not necessarily prevent learning from architectural ideas, but they may restrict copying code or integrating implementation details.

---

## Stage 1 — Read the External Repo Seriously

Clone the repo into the scratch directory.

Example:

```bash
git clone <repo-url> /tmp/xpoll-<repo-name>-<timestamp>/external
```

Do not rely on the README alone. READMEs often overstate product intent and underdescribe implementation reality.

Inspect at minimum:

```text
README
docs/
examples/
src/ or app/
tests/
package manifests
dependency manifests
configuration files
CI/CD workflows
entry points
API definitions
agent/tool definitions, if present
database or schema files
deployment files
```

Answer these questions in `repo_analysis.md`.

### 1.1 What Problem Does It Actually Solve?

Write one paragraph in Hermes’s own words.

The paragraph should distinguish:

```text
What the repo claims to do
What the code actually appears to do
Who the likely user is
What input it consumes
What output it produces
```

If Hermes cannot restate the problem clearly, continue reading.

### 1.2 Architecture

Identify the top-level decomposition:

```text
Services
Agents
Modules
Pipelines
Data stores
CLI entry points
Web app layers
Workers
Queues
External APIs
Plugin systems
Evaluation loops
State management
```

Sketch the data flow mentally before producing any Mermaid diagrams.

### 1.3 The Novel or Transferable Bits

Most repositories are mostly boilerplate. Find the interesting 20%.

Look for:

```text
Clever abstractions
Routing schemes
Prompting patterns
Memory patterns
Agent orchestration
Evaluation loops
Workflow primitives
Plugin registries
Caching designs
Data modeling choices
Observability patterns
Testing strategies
Human-in-the-loop review
Failure recovery
Developer experience improvements
```

For each interesting idea, record:

```text
Idea name
Where it appears in the repo, including file paths
What problem it solves
Why it is interesting
What assumptions it depends on
Whether it is portable to Michael’s projects
```

### 1.4 Dependencies and Stack

Record:

```text
Languages
Frameworks
Runtime assumptions
Infrastructure dependencies
External APIs
Databases
Queues
Package managers
Deployment assumptions
```

A useful idea trapped in a stack Michael does not use is not automatically disqualified, but the stack mismatch must be treated as an implementation constraint.

### 1.5 Maturity Signals

Check:

```text
Recent commit activity
Contributor count
Test coverage
Issue volume
Open issues that indicate fragility
Documentation completeness
Versioning
Release history
CI status, if visible
```

Classify maturity as one of:

```text
Prototype
Early but usable
Actively maintained project
Mature project
Abandoned or unclear
```

Be cautious about adopting ideas from prototype repos without additional validation.

### Output of Stage 1

Save:

```text
repo_analysis.md
```

This file is internal but should be good enough to attach or link later.

---

## Stage 2 — Map Ideas to Michael’s Portfolio

Load Michael’s repositories and idea list.

Use:

```bash
gh repo list MichaelTanzer --limit 100
```

if available, plus local files such as:

```text
~/hermes/idea_list.md
~/hermes/portfolio.md
~/hermes/projects.md
```

Hermes should inspect candidate target repos enough to understand the relevant architecture. Do not treat Michael’s repo as a black box.

For each transferable idea from Stage 1, ask:

```text
Which Michael project could absorb this?
Is the target an existing repo or an idea-list item?
Where would it land: module, agent, service, layer, workflow, or interface?
What would it change?
Would it add a capability, replace a component, simplify a workflow, improve quality, reduce latency, reduce cost, improve reliability, or improve developer velocity?
What would it cost?
What assumptions are being made?
What risks would it introduce?
```

### Candidate Scoring

Score each candidate application using:

```text
Value: 1–5
Tractability: 1–5
Effort: 1–5
Risk: 1–5
Strategic fit: 1–5
```

Use this rough prioritization formula:

```text
(value × tractability × strategic_fit) ÷ (effort + risk)
```

The formula is not a substitute for judgment. It exists to force disciplined comparison.

Discard weak applications. Michael does not need a laundry list.

Keep:

```text
The single strongest application by default
Up to 3 applications only if they are genuinely independent and comparably strong
```

If no application clears a reasonable bar, that is a legitimate result. Do not manufacture a fit.

### Output of Stage 2

Save:

```text
portfolio_map.md
candidate_scores.md
```

---

## Stage 3 — Draft the Proposal

Create `proposal_v1.md`.

The proposal should be concrete enough for Claude Code and Codex to critique.

Include:

```text
Title
External repository analyzed
Target Michael repo or idea
Thesis
Mechanism
Current target architecture, as verified
Transferable insight from the external repo
Proposed architectural change
Integration plan
Smallest valuable first cut
Risks
Open questions
What is explicitly not being proposed
Expected benefit
Flowchart notes
```

### Required Proposal Content

#### 3.1 Thesis

Write 2–3 sentences.

Example:

```text
The strongest transferable idea from <external_repo> is its memory-block
pattern for separating durable facts from ephemeral reasoning state.
I recommend adapting that idea to TanzerBot’s evidence store so that
analyst agents can share verified, inspectable facts without sharing
full conversation traces or brittle prompt context.
```

#### 3.2 Mechanism

Be specific.

Mention:

```text
Target repo
Relevant files or modules, when known
Existing components affected
New components to add
Interfaces to modify
Data model changes
Workflow changes
```

Avoid vague claims like:

```text
Improve architecture
Make agents smarter
Use this pattern
Add orchestration
```

unless immediately followed by concrete implementation detail.

#### 3.3 Integration Plan

Write a sequenced plan.

Good:

```text
1. Add a small EvidenceBlock type and serializer.
2. Modify the synthesis agent to emit EvidenceBlocks after each source review.
3. Store EvidenceBlocks in the existing evidence store.
4. Add retrieval by ticker, claim, source, and confidence.
5. Update the final memo generator to cite EvidenceBlocks instead of raw notes.
```

Bad:

```text
1. Refactor architecture.
2. Add memory.
3. Improve agents.
```

#### 3.4 Smallest Valuable First Cut

Identify the smallest implementation that would prove or disprove the idea.

This should usually be:

```text
One repo
One subsystem
One feature path
One measurable output
```

#### 3.5 Risks and Open Questions

Include:

```text
Technical risks
Migration risks
Dependency risks
Complexity risks
Testing gaps
Incorrect assumptions
Parts of Michael’s repo that could not be verified
Ways the external repo’s design may not transplant cleanly
```

#### 3.6 What Is Explicitly Not Being Proposed

This section is mandatory.

Examples:

```text
I am not proposing a full rewrite of TanzerBot’s orchestration layer.
I am not proposing copying code from the external repo.
I am not proposing adopting the external repo’s database stack.
I am not proposing replacing the existing analyst agents.
```

This prevents scope creep.

### Output of Stage 3

Save:

```text
proposal_v1.md
```

---

## Stage 4 — Adversarial Review by Claude Code and Codex

This stage must not be skipped.

Hermes is biased toward its own proposal. Claude Code and Codex should be used as adversarial reviewers, not rubber stamps and not copy editors.

Run both reviews, preferably in parallel.

### 4.1 Prepare Review Context

Create `review_prompt.md` containing:

```text
You are reviewing a proposal to apply ideas from <external_repo> to
<Michael_target_repo_or_project>.

Your job is adversarial technical critique.

Do not rewrite the proposal.
Do not restate it back.
Do not pad with generic advice.
Do not praise unless praise is needed to explain why no critique applies.

Find specific weaknesses:
1. Technical errors.
2. Unsupported assumptions.
3. Unconsidered alternatives.
4. Integration issues.
5. Missing risks.
6. Sequencing mistakes.
7. Overengineering.
8. Underengineering.
9. Testing gaps.
10. Places where the external repo’s idea does not actually transfer.

For each critique, return:
(a) the specific claim or design choice being challenged,
(b) why it is wrong, incomplete, risky, or underspecified,
(c) what you would do instead.

If the proposal is solid, say so briefly and give only meaningful critiques.
```

Append or attach:

```text
repo_analysis.md
portfolio_map.md
candidate_scores.md
proposal_v1.md
Relevant target repo architecture notes
Sanitized file paths and excerpts
```

### 4.2 Claude Code Review

Example command:

```bash
claude -p "$(cat review_prompt.md)" --output-format json > cc_review.json
```

If `claude` is unavailable, save an error note to:

```text
cc_review_unavailable.md
```

Do not pretend the review happened.

### 4.3 Codex Review

Example command:

```bash
codex exec "$(cat review_prompt.md)" > codex_review.md
```

If `codex` is unavailable, save an error note to:

```text
codex_review_unavailable.md
```

Do not pretend the review happened.

### 4.4 If Reviews Are Too Generic

If either reviewer only gives vague polish, rerun with a sharper prompt:

```text
Your previous critique was too generic. Identify concrete failure modes,
wrong assumptions, missing implementation details, or architectural weaknesses.
Tie every critique to a specific sentence, component, or step in the proposal.
Return no more than 8 critiques, ranked by importance.
```

### Output of Stage 4

Save:

```text
review_prompt.md
cc_review.json
codex_review.md
```

or explicit unavailable files.

---

## Stage 5 — Intellectually Honest Integration

Hermes must evaluate every distinct suggestion from Claude Code and Codex.

Avoid both failure modes:

```text
Sycophantic capitulation: accepting every suggestion because an external reviewer said it.
Defensive entrenchment: rejecting every suggestion because Hermes wrote the draft.
```

For each suggestion, classify it as:

```text
ACCEPT
PARTIAL
REJECT
NEEDS_MICHAEL_DECISION
```

Use this standard:

```text
ACCEPT if it improves correctness, feasibility, simplicity, safety,
maintainability, sequencing, testability, or user value.

PARTIAL if the suggestion is directionally right but too broad, too expensive,
or needs adaptation.

REJECT if it misunderstands the repo, adds unjustified complexity, conflicts
with Michael’s goals, weakens the plan, relies on unsupported assumptions, or
solves a problem not yet shown to exist.

NEEDS_MICHAEL_DECISION if it depends on preference, strategy, budget, timeline,
or product direction.
```

Create `review_adjudication.md`.

Format:

```text
[ACCEPT] CC#3: Use streaming responses for the synthesis agent.
Reason: Correct. I missed that the target repo already streams intermediate
research output, and the proposal should preserve that behavior.
Change made: Updated integration step 4 to maintain streaming output.

[REJECT] Codex#1: Add Redis for caching.
Reason: Out of scope. No evidence the existing cache is a bottleneck, and
adding Redis would increase operational complexity before the idea is proven.
Change made: None.

[PARTIAL] CC#5: Restructure the workflow as a full DAG.
Reason: Agree that dependency tracking is underspecified, but a full DAG runtime
is too heavy for the first cut.
Change made: Added lightweight dependency edges between research artifacts
without proposing a DAG scheduler.
```

Then revise `proposal_v1.md` into:

```text
proposal_final.md
```

The final proposal must reflect accepted and partially accepted critiques.

If Hermes accepts no suggestions, pause and re-check:

```text
Did the reviewers misunderstand because I gave them poor context?
Was the proposal already unusually strong?
Am I rejecting defensively?
Should one critique be partially adopted?
```

It is acceptable to accept nothing, but only after honest review.

### Output of Stage 5

Save:

```text
review_adjudication.md
proposal_final.md
```

---

## Stage 6 — Create Architecture Flowcharts

The email should include flowcharts that make the architectural diff visible.

### 6.1 Current Architecture Flowchart

Include this only if the proposal targets an existing Michael repository or an existing workflow.

The diagram should show the relevant subsystem as it exists today, not the entire repo.

If Hermes cannot confidently reconstruct the current workflow, do not fabricate it. Write:

```text
I could not confidently reconstruct the current workflow from the available
context, so I am not including a current-state flowchart.
```

### 6.2 Proposed Architecture Flowchart

Include this whenever a concrete proposal is recommended.

The proposed flowchart should use the same scope as the current flowchart so the difference is legible.

### 6.3 Mermaid Style Guide

Use:

```text
flowchart TD
```

for pipelines.

Use:

```text
flowchart LR
```

for service-to-service data flow.

Label important edges with what flows through them:

```mermaid
A[Research Agent] -->|validated claims| B[Evidence Store]
```

Use subgraphs to group layers:

```mermaid
subgraph Agents
    A[Analyst Agent]
    B[Synthesis Agent]
end

subgraph Storage
    C[Evidence Store]
end
```

On proposed diagrams, style changed nodes:

```mermaid
classDef new fill:#1a472a,stroke:#3fb950,color:#fff;
classDef changed fill:#3a2d0a,stroke:#d29922,color:#fff;
classDef removed fill:#3a0a0a,stroke:#f85149,color:#fff,stroke-dasharray:5 5;
```

Use classes:

```mermaid
class NewMemoryLayer new;
class ExistingSynthesisAgent changed;
class OldScratchNotes removed;
```

Keep node labels short. If a node needs a full sentence, the diagram is at the wrong level.

### 6.4 Mermaid Rendering for Email

Email clients generally do not render Mermaid natively.

Preferred path: render diagrams to PNG or SVG and inline them in the email.

Example:

```bash
mmdc -i current.mmd -o current.png -t dark -b transparent
mmdc -i proposed.mmd -o proposed.png -t dark -b transparent
```

If `mmdc` is unavailable, use the fallback:

```text
Include the Mermaid source in a <pre> block.
Include a mermaid.live edit link if the harness supports generating one.
State that the diagram source is included because Mermaid rendering was unavailable.
```

Always include the Mermaid source somewhere in the email, preferably inside:

```html
<details>
  <summary>Mermaid source</summary>
  <pre>...</pre>
</details>
```

### Output of Stage 6

Save:

```text
current.mmd
proposed.mmd
current.png or current.svg, if rendered
proposed.png or proposed.svg, if rendered
```

---

## Stage 7 — Email Delivery

Compose an HTML email.

### Subject Line

Use:

```text
[xpoll] <one-line thesis>
```

Examples:

```text
[xpoll] Apply Letta-style memory blocks to TanzerBot’s evidence store
[xpoll] Use repo-derived workflow checks for TanzerBot analyst handoffs
[xpoll] No strong fit found for <repo>, but one idea is worth saving
```

### Email Structure

The email should be readable in about four minutes.

Use prose, not bullet salad.

Recommended structure:

```text
Hi Michael,

I analyzed <external_repo> and compared its architecture and implementation
patterns against your repos and idea list.

My recommendation: <one-sentence recommendation>.
```

Then include these sections.

---

### Section 1 — The Proposal

Include:

```text
Thesis
Target repo or idea
Mechanism
Smallest valuable first cut
Expected benefit
```

This section should lead with the conclusion.

Do not make Michael hunt for the recommendation.

---

### Section 2 — Why This Repo Was Interesting

Explain the external repo’s most transferable idea.

Mention specific evidence:

```text
File paths
Function names
Modules
Design patterns
Configuration structure
Workflow choices
Tests or examples
```

Avoid vague claims like:

```text
The repo has a clean architecture.
The agents are interesting.
The design is modern.
```

Instead write:

```text
The interesting pattern is that the repo separates planner state from execution
state in <path>, which makes each tool invocation auditable and replayable.
```

---

### Section 3 — Best Fit in Michael’s Work

Include:

```text
Target project
Why this project is the best fit
Other candidates considered briefly
Why they were rejected or ranked lower
```

If TanzerBot is selected, explain why. Do not select it merely because it is the portfolio anchor.

---

### Section 4 — Current Architecture Flowchart

Include only when targeting an existing repo or workflow.

Inline the rendered image if available.

Also include the Mermaid source in a collapsed section.

Example:

```html
<h2>Current architecture</h2>
<p>This is the relevant subsystem as it works today.</p>
<img src="cid:current-architecture">

<details>
  <summary>Mermaid source</summary>
  <pre>flowchart TD ...</pre>
</details>
```

If no current architecture diagram is included, explain why.

---

### Section 5 — Proposed Architecture Flowchart

Include the proposed architecture diagram.

The proposed diagram should visibly mark:

```text
New components
Changed components
Removed components
New data flows
Changed review or evaluation steps
```

Inline the rendered image if available.

Also include Mermaid source in a collapsed section.

---

### Section 6 — Integration Plan

Give a sequenced implementation plan.

The plan should identify:

```text
Step 1: smallest useful first cut
Step 2: integration with existing components
Step 3: validation or testing
Step 4: migration or rollout
Step 5: optional expansion
```

Include likely file paths or module names where possible.

---

### Section 7 — Risks, Tradeoffs, and Scope Boundaries

Include:

```text
What could go wrong
What assumptions are uncertain
What may not transplant cleanly from the external repo
What complexity this adds
What is intentionally out of scope
```

This section must include “what I am not proposing.”

---

### Section 8 — Review Trail

Summarize the Claude Code and Codex review.

Keep it short but concrete.

Example:

```text
I ran the draft through Claude Code and Codex for adversarial review.

Accepted:
- Claude Code pointed out that the proposed evidence layer needed to preserve
  streaming outputs. I updated the plan so streaming remains unchanged.

Partially accepted:
- Codex suggested moving the whole workflow to a DAG. I agreed with the need
  for explicit dependencies but rejected a full DAG runtime for the first cut.
  The revised plan adds lightweight dependency edges instead.

Rejected:
- Codex suggested Redis caching. I rejected this because there is no evidence
  caching is the bottleneck, and it would add infrastructure before the
  proposal is validated.
```

If one review tool was unavailable, say so plainly.

Do not fabricate review results.

---

### Section 9 — Recommendation

End with a clear recommendation:

```text
Build this now.
Prototype this first.
Save this for later.
Do not pursue this.
```

Include the reason.

Example:

```text
My recommendation is to prototype this first in TanzerBot’s evidence pipeline.
The idea is high-leverage, but the first cut should stay narrow: one analyst
workflow, one evidence object type, and one final memo integration.
```

---

### Footer

Include either:

```text
A link to the scratch directory on the VPS
```

or attach:

```text
repo_analysis.md
proposal_final.md
review_adjudication.md
current.mmd
proposed.mmd
rendered diagram images
```

Footer example:

```text
Full working notes are available at:
/tmp/xpoll-<repo-name>-<timestamp>
```

---

## No-Fit Outcome

If no strong application exists, still email Michael.

Subject:

```text
[xpoll] No strong fit found for <repo>
```

The email should explain:

```text
What the repo does
What was interesting
Which Michael projects were considered
Why the ideas do not currently apply
What condition would make the repo worth revisiting
Whether any idea-list item should be updated
```

Do not create architecture diagrams if there is no concrete target proposal.

---

## Abort or Escalate Conditions

### Private, Gone, or Empty Repo

Do not proceed.

Send or return:

```text
I could not analyze this because the repository is private, unavailable, or empty.
Please send the correct public link or grant access.
```

### Enormous Repo With No Focal Point

If the repo is too large and no subsystem stands out, ask Michael which part he found interesting.

Do not manufacture a comprehensive analysis.

### License Conflict

If the repo’s license may be incompatible with Michael’s likely use, flag this prominently.

Example:

```text
The architecture can still inspire a clean-room implementation, but I would not
copy code from this repository because the license appears incompatible with
closed-source commercial reuse.
```

### Deprecated Target

If the best target appears to be a project Michael’s idea list says is deprecated, do not recommend building there.

Mention:

```text
This idea would fit <deprecated_project>, but your portfolio notes indicate that
project is deprecated, so I am not recommending work there.
```

Then either choose another target or issue a no-fit result.

### Tool Failure

If `claude`, `codex`, `gh`, `mmdc`, or email tooling is unavailable:

```text
Record the failure.
Use the best available fallback.
Do not pretend the tool ran.
Include a short note in the final email if the missing tool materially affects confidence.
```

---

## Output Quality Bar

Before sending the email, Hermes must verify:

```text
Could Michael read this once and decide whether to proceed?
Did Hermes cite specific files, modules, functions, or workflow choices from the external repo?
Did Hermes cite specific files, modules, agents, or workflows from Michael’s target repo when available?
Does the proposal identify the smallest valuable first cut?
Does it say what is not being proposed?
Are the risks specific rather than generic?
Did Claude Code and Codex provide real critique rather than polish?
Were accepted and rejected critiques adjudicated honestly?
Does the proposed architecture diagram visibly differ from the current one?
Are new, changed, and removed components marked clearly?
Is the email readable in about four minutes?
```

If any answer is no, fix the proposal before sending.

---

## Anti-Patterns

Hermes must avoid:

```text
Summarizing the external repo without connecting it to Michael’s work
Forcing a fit because the repo is interesting
Treating TanzerBot as the target without checking other projects
Relying on the README alone
Ignoring licensing
Executing untrusted code
Sending private code unnecessarily to external tools
Accepting every Claude Code or Codex suggestion
Rejecting every Claude Code or Codex suggestion
Producing a generic “10 cool ideas” essay
Making diagrams unsupported by verified architecture
Diagramming the whole repo instead of the relevant subsystem
Proposing a rewrite when a narrow integration would work
Adding infrastructure before proving value
Hiding uncertainty
Pretending unavailable tools ran successfully
```

---

## What This Skill Does Not Do

This skill does not:

```text
Implement the proposed changes
Open a pull request
Survey multiple external repos
Produce a generic repo summary
Copy code from the external repo
Bypass license constraints
Run untrusted code
Promise that the proposal is risk-free
```

The deliverable is an opinionated, evidence-backed, reviewed proposal sent by email.

---

## Minimal Email Template

```html
<h1>[xpoll] {{one_line_thesis}}</h1>

<p>Hi Michael,</p>

<p>
I analyzed <strong>{{external_repo}}</strong> and compared its architecture,
workflow, and implementation patterns against your repositories and idea list.
</p>

<p>
<strong>Recommendation:</strong> {{recommendation_summary}}
</p>

<h2>1. The proposal</h2>
<p>{{proposal_thesis}}</p>
<p>{{mechanism}}</p>

<h2>2. Why this repo is interesting</h2>
<p>{{source_repo_insight_with_specific_paths}}</p>

<h2>3. Best fit in your work</h2>
<p>{{target_project_and_reason}}</p>

<h2>4. Current architecture</h2>
<p>{{current_architecture_explanation}}</p>
{{current_architecture_image_or_fallback}}
<details>
  <summary>Mermaid source</summary>
  <pre>{{current_mermaid}}</pre>
</details>

<h2>5. Proposed architecture</h2>
<p>{{proposed_architecture_explanation}}</p>
{{proposed_architecture_image_or_fallback}}
<details>
  <summary>Mermaid source</summary>
  <pre>{{proposed_mermaid}}</pre>
</details>

<h2>6. Integration plan</h2>
<ol>
  <li>{{step_1}}</li>
  <li>{{step_2}}</li>
  <li>{{step_3}}</li>
  <li>{{step_4}}</li>
</ol>

<h2>7. Risks, tradeoffs, and scope boundaries</h2>
<p>{{risks}}</p>
<p><strong>What I am not proposing:</strong> {{not_proposing}}</p>

<h2>8. Review trail</h2>
<p>I ran the draft through Claude Code and Codex for adversarial review.</p>
<p><strong>Accepted:</strong> {{accepted_critiques}}</p>
<p><strong>Partially accepted:</strong> {{partial_critiques}}</p>
<p><strong>Rejected:</strong> {{rejected_critiques}}</p>

<h2>9. Final recommendation</h2>
<p>{{final_recommendation}}</p>

<hr>
<p>
Working notes: {{scratch_dir_or_attachments}}
</p>

<p>Best,<br>Hermes</p>
```

---

## Decision Rule

If the external repository contains a transferable idea that maps strongly to one of Michael’s active repositories or idea-list projects, Hermes should send a concrete proposal with current and proposed architecture diagrams.

If the repository is interesting but does not currently map well to Michael’s work, Hermes should send an honest no-fit analysis.

If the repository is inaccessible, too broad without a focal point, or blocked by missing portfolio context, Hermes should escalate narrowly and avoid pretending to have completed the analysis.
