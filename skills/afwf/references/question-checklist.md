# AFWF question checklist

Sweep these categories during the Ask phase. Only turn an item into a question if recon cannot answer it and no obvious default exists.

## Goal & success
- What does "done" look like? How will user judge it?
- Must-haves vs. nice-to-haves.
- Any example, reference, or prior art to match?

## Scope
- What is explicitly out of scope?
- Which files, modules, systems, or people may be touched?
- One deliverable or several? Partial delivery acceptable?

## Constraints
- Language, framework, library, version requirements.
- Style, naming, formatting, tone conventions not visible in repo.
- Performance, compatibility, budget, deadline limits.

## Output
- Format (file type, PR vs. commit vs. local only, doc vs. chat).
- Location (path, branch, folder, destination service).
- Audience (self, team, public).

## Environment & access
- Credentials, API keys, accounts needed?
- Which environment: local, staging, production?
- Tools to install? Allowed to install them?

## Risky actions (ask permission up front)
- Deleting or overwriting files/data.
- Force-push, history rewrite, branch deletion.
- Deploys, releases, publishing.
- Sending messages, emails, comments, notifications.
- Paid or rate-limited API usage.
- Database migrations, schema changes.
- Dependency upgrades with breaking potential.

## Trade-offs
- Speed vs. thoroughness.
- Minimal change vs. clean refactor.
- Follow existing pattern vs. introduce better one.

## After completion
- Commit / push / open PR automatically?
- Run full test suite or targeted checks only?
- Clean up temporary files, branches, resources?
