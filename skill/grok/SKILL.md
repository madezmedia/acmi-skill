---
name: acmi-github
description: Operate ACMI against GitHub — bootstrap fleet context, map madezmedia ACMI repos, read/push code, open issues and PRs, then log Profile/Signals/Timeline events. Use when the user mentions ACMI plus GitHub, acmi-mcp, madezmedia/acmi, fleet coordination on a repo, push ACMI code, or Gitea/GitHub CI for agent memory.
metadata:
  type: workflow
  version: "1.0"
  owner: madezmedia
  surface: grok
---

# ACMI GitHub

Bridge the ACMI connector and the GitHub connector so fleet work on ACMI repos is searchable, auditable, and committed.

This file is the Grok-surface variant. Do not replace `skill/SKILL.md` (Claude-universal playbook).

## Defaults

- GitHub owner — `madezmedia` (login from `github___get_me`). Confirm before writing to a different owner.
- Tenant — `madez` on the hosted ACMI connector.
- Protocol — ACMI v1.5 event envelope (`source`, `kind`, `correlationId`, `summary`).
- Brand — ACMI stays Agentic Context Memory Interface. House brand Mad EZ Media.
- Canonical protocol repo — `madezmedia/acmi`.
- Existing Claude-surface skill — `skill/SKILL.md` in this repo. Leave it alone.

Read `references/repo-map.md` before searching the whole GitHub universe.

## Tool sequence

Always discover via `search_connected_tools` if a tool name is uncertain. Then call:

1. `acmi___acmi_bootstrap` with `agentId` (use `grok` unless the user names another agent).
2. `github___get_me` if owner/login is missing.
3. GitHub read tools (`github___get_file_contents`, `github___get_repository_tree`, `github___search_code`, `github___list_branches`, `github___search_pull_requests`).
4. GitHub write tools only after the user asked to change the repo.
5. ACMI write-back (`acmi___acmi_event` and/or `acmi___acmi_work_event`) after a meaningful GitHub action.

If ACMI semantic search returns `cloud_fallback` / local Chroma unavailable, skip it and use GitHub search plus `acmi___acmi_get` / `acmi___acmi_cat`.

## Event discipline

- `namespace` — `work` for a ticket, `agent` for session notes, `thread` for a conversation.
- `source` — `agent:grok` unless another agent is acting.
- `kind` — `coord-note`, `decision`, `handoff-complete`, `step-done`, `research-brief`, `work-update`.
- `summary` — `[kind-tag @recipient] short fact.`
- `correlationId` — camelCase plus timestamp or ticket id.
- Chain follow-ups with `parentCorrelationId`.

Do not delete ACMI keys unless the user explicitly asks. `acmi___acmi_delete` is dry-run until `confirm=true`. Never target protected `acmi:registry:*` or `acmi:notion-sync:*` paths.

## Read a repo

1. Resolve `owner`/`repo` from the user or from `references/repo-map.md`.
2. `github___list_branches` then `github___get_repository_tree`.
3. `github___get_file_contents` for specific files. Prefer `SPEC.md`, `CHANGELOG.md`, `mcp/README.md`, `docs/OPERATOR-GUIDE.md` on `madezmedia/acmi`.
4. Scope code search — `repo:madezmedia/acmi query`.

## Write to a repo

Confirm target repo and branch. Default branch is `main` on the public ACMI repos.

- Single file — fetch `sha` first, then `github___create_or_update_file`.
- Multiple files — `github___push_files` on an explicit branch.
- New work — branch, push, `github___create_pull_request` (`base` usually `main`).

Never invent a SHA. Never force-push. Never commit secrets, Upstash tokens, or Elestio credentials.

After a successful write, log an ACMI event with the commit/PR URL in the summary.
