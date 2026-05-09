# Security Policy

## Secrets
- Real secrets live in /etc/hermes/hermes.env (640, root:ubuntu) or in deployment platform secrets.
- Never commit .env files. .env.example only, with placeholder values.
- Never paste secrets into agent prompts.
- Never log secret values.
- Never echo environment variables containing API keys.

## Filesystem boundaries
- Agents work only inside their assigned worktree under ~/dev/worktrees/.
- Canonical repos under ~/dev/repos/ are read-only to agents unless explicitly given write access for a session.
- Agents never modify ~/.ssh, /etc/, or anything outside ~/dev/.
- Agents never read files in /home/ubuntu/.ssh/ or /etc/hermes/.

## Network
- Agents may reach declared model providers (Anthropic, OpenAI, Google) and GitHub.
- Outbound traffic to other domains requires explicit approval.
- Agents never `curl ... | sh` or pipe remote content into a shell.

## Incident response
- If a secret leaks: rotate immediately, then run runbooks/rotate-leaked-secret.md.
- If an agent does something unexpected: stop the agent, capture logs, write an incident report.
