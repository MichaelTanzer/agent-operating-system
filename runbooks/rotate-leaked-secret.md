# Rotate Leaked Secret

## When to use this runbook

A secret (API key, token, password, DB credential) has been exposed —
committed to git, pasted into a prompt, written to a log, or otherwise leaked.

## Steps

### 1. Stop the bleeding

- [ ] Revoke the exposed secret at the provider (Anthropic, OpenAI, Google, GitHub, etc.).
- [ ] Confirm revocation took effect (try using the old key; should fail).

### 2. Generate replacement

- [ ] Generate new secret at the provider.
- [ ] Store in /etc/hermes/hermes.env (640, root:ubuntu) — never commit.
- [ ] If used in deployment platform: rotate there too (GitHub Secrets, Vercel, etc.).

### 3. Restart consumers

- [ ] Restart Hermes:sudo systemctl restart hermes
- [ ] Restart any other systemd services that read the env file.
- [ ] Test that the new secret works.

### 4. Scrub the leak

- [ ] If committed to git: rotate first, then rewrite history with `git filter-repo` or BFG.
- [ ] Force-push the rewritten history (this requires temporarily relaxing branch protection).
- [ ] Notify any collaborators that history was rewritten.
- [ ] If pasted into an agent prompt: clear any persisted memory (Gbrain, conversation history).
- [ ] If logged: rotate logs and confirm log retention is bounded.

### 5. Audit blast radius

- [ ] Check provider audit logs for unauthorized usage between leak and rotation.
- [ ] If billing irregularity: contact provider support.

### 6. Post-incident

- [ ] Write INCIDENT_REPORT.md.
- [ ] Update SECURITY_POLICY.md if policy gaps contributed.
- [ ] Update agent skills if an agent caused the leak.

## Verification

- Old secret is dead (provider returns auth error)
- New secret works in production path
- No secret remains in git history
- Incident is documented

## Common failures

(Fill in as encountered.)
