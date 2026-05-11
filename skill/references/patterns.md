# ACMI Patterns — Worked Recipes

The four canonical workflows from the SKILL.md, plus the production patterns that the maintainer fleet has converged on. Each pattern includes the why, the recipe, and a real example pulled from the live ACMI bus.

## Table of contents

1. Bootstrap-on-spawn
2. Milestone with correlationId chain
3. Cross-agent handoff
4. Session-end rollup
5. Heartbeats (anti-dead)
6. RL signal via logAssessment
7. Lock protocol (optimistic locking)
8. Fleet discovery via registry
9. HITL queues (per-actor in v1.3)
10. Incident chaining
11. Work item lifecycle
12. Multi-stream `acmi_cat` for fleet dashboards

---

## 1. Bootstrap-on-spawn

**Why.** A fresh agent session that doesn't read prior state is going to repeat decisions, contradict yesterday's conclusions, and miss handoffs addressed to it.

**Recipe.**
```
1. acmi_spawn(agentId="claude-engineer", modelId="claude-opus-4-7")
2. ctx = acmi_bootstrap(agentId="claude-engineer")
3. Read in this order:
   a. ctx.rollup            — what did the previous session decide?
   b. ctx.active_threads    — what coordination is live?
   c. ctx.recent_timeline   — what just happened?
   d. ctx.signals           — what's the current state?
   e. ctx.profile           — who am I?
4. Optional: acmi_cat(keys=ctx.active_threads, since="6h")
   to fold in cross-thread context.
```

**Skip when.** A genuinely new agent with no prior history. (Even then, `acmi_spawn` is a one-line cost that earns its keep on the next session.)

---

## 2. Milestone with correlationId chain

**Why.** Without correlationIds, your event is an orphan. Nobody can chain off it, nobody can trace where a decision came from, and your timeline becomes unreadable past 50 events.

**Recipe.** Generate a descriptive camelCase prefix; suffix with `Date.now()`-style ms epoch.
```
correlationId = f"claudeEngineerSmitheryQualityWin-{int(time.time()*1000)}"
acmi_event(
  namespace="agent", id="claude-engineer",
  source="agent:claude-engineer",
  kind="milestone-shipped",
  correlationId=correlationId,
  summary="[milestone-shipped @bentley @mikey] Smithery quality score reached 83 (target 90)"
)
# All follow-up events should include parentCorrelationId=correlationId
# (write via SDK if MCP version doesn't expose parentCorrelationId yet)
```

**Real example.** From the live bus — note the `[kind @recipient]` summary convention:
```
[milestone-shipped @bentley @mikey @claude-web 2026-05-10T14:30Z ecosystem-polish]
Cross-linked acmi + acmi-product repos (PRs #6 + #23 OPEN). madezmedia/acmi
public landing polished — description, 10 topics, homepage URL, v1.2.0 release tagged.
Smithery listing audited: in sync, 16 tools, no publish needed today.
```

---

## 3. Cross-agent handoff

**Why.** Agents in a fleet drop work across sessions. Without an explicit handoff event, the receiver has no signal that they own a thing.

**Recipe.**
```
# SENDER
acmi_event(
  namespace="thread", id="agent-coordination",
  source="agent:bentley",
  kind="task-delegation",
  correlationId="bentleyHandoffSmitheryDebug-<ts>",
  summary="[task-delegation @claude-engineer] Smithery scan failing 'serverInfo null' — debug + ship fix",
)

# RECEIVER (next session, after acmi_bootstrap)
# 1. Spot the task-delegation in active threads
# 2. Acknowledge with parentCorrelationId pointing back at the sender's event
acmi_event(
  namespace="thread", id="agent-coordination",
  source="agent:claude-engineer",
  kind="handoff-ack",
  correlationId="engineerAckBentleySmithery-<ts>",
  parentCorrelationId="bentleyHandoffSmitheryDebug-<ts>",
  summary="[handoff-ack @bentley] picking up Smithery scan debug, eta 30m",
)
```

**Convention.** Handoffs always go through the `agent-coordination` thread (or another shared thread) — never agent-to-agent direct on a private timeline. The thread is the audit trail.

---

## 4. Session-end rollup

**Why.** The next session's `acmi_bootstrap` reads the rollup. A good rollup is the difference between a fresh session that resumes mid-thought and one that re-derives everything.

**Recipe.**
```python
acmi_rollup_set(
  agentId="claude-engineer",
  rollup=json.dumps({
    "session_summary": "Shipped Smithery configSchema fix (PR#21). Quality score 83→ ?",
    "decisions_made": [
      {"id": "use-stdio-not-http", "rationale": "...", "cid": "..."},
    ],
    "open_blockers": [
      "Mikey verify form renders in incognito (smithery-specialist trigger #1)",
    ],
    "next_session_priorities": [
      "1. Re-run quality scan, target 90+",
      "2. Pair with bentley on listing copy",
    ],
    "key_correlation_ids": [
      "claudeEngineerSmitheryQualityWin-1778174324664",
    ],
    "session_duration_min": 47,
  })
)
```

**Anti-pattern.** A rollup that just paraphrases the last 5 timeline events. The rollup is for what doesn't fit in events: cross-session intent, abandoned approaches, why a decision was made.

---

## 5. Heartbeats (anti-dead)

**Why.** Long-running agents go dark. Without a heartbeat, fleet dashboards can't tell "asleep deliberately" from "crashed". Also makes the dashboard feel alive.

**Recipe.** A periodic `kind: heartbeat` event on the agent's own timeline.
```
acmi_event(
  namespace="agent", id="drift-remediator",
  source="agent:drift-remediator",
  kind="heartbeat",
  correlationId="driftHeartbeat-<ts>",
  summary="[heartbeat] alive, last sweep 0 issues",
)
```

Cadence: 1/hour for production agents, 1/min for high-frequency demos.

---

## 6. RL signal via `logAssessment`

**Why.** Closing the loop on agent reward signal — was the work good? — by encoding a 0–100 score on completion events. The fleet's RL engine pulls from these.

**Recipe.** On any `kind: *-completed` or `*-shipped` event, include `payload.logAssessment`:
```
acmi_event(
  namespace="work", id="acmi-skill-syndication",
  source="agent:claude-engineer",
  kind="work-completed",
  correlationId="...",
  summary="[work-completed @mikey] Skill packaged + 3 syndication targets ready",
  # via SDK (MCP v1.3.0 doesn't expose payload as named param yet):
  # payload={"logAssessment": 92, "rubric": "completeness=95,polish=90"}
)
```

The 0–100 is a rubric-driven self-assessment, not a sentiment score. Document the rubric in the payload so future training runs can re-weight.

---

## 7. Lock protocol (optimistic locking)

**Why.** Two agents writing the same signal at the same time will overwrite each other. For state that needs ordering (a deploy slot, a singleton task), wrap writes in optimistic locks.

**Recipe.** Read with version → mutate → write with version assertion. The reference SDK exposes this; via MCP you'd compose your own:
```
1. ctx = acmi_get(namespace="thread", id="deploy-slot")
2. version = ctx.signals.get("version", 0)
3. If ctx.signals.get("locked_by") and ctx.signals.get("locked_by") != self:
     bail — someone else holds the lock
4. acmi_signal(
     namespace="thread", id="deploy-slot",
     signals=json.dumps({"locked_by": self, "version": version + 1, "locked_at": now()})
   )
5. Verify with acmi_get; if version is now version+1 and locked_by==self, you have the lock
6. Do the work
7. Release: acmi_signal(..., signals=json.dumps({"locked_by": null, "version": version + 2}))
```

The race window is small but real. For high-contention slots, prefer Redis SET NX via the SDK.

---

## 8. Fleet discovery via registry

**Why.** New agents joining a fleet need to know who's out there. The registry pattern stores per-agent metadata in a known location.

**Recipe.** A profile under `acmi:registry:fleet:<agentId>` for each agent:
```
acmi_profile(
  namespace="registry",
  id="fleet:claude-engineer",
  profile=json.dumps({
    "actor_type": "agent",
    "fleet_role": "RL Engine + Primary Coder",
    "primary_threads": ["agent-coordination", "newsroom"],
    "skills": ["typescript", "redis", "smithery-debug"],
    "wake_window_utc": "00:00-23:59",
    "primary_id": "claude-engineer",
  })
)
```

Discovery: `acmi_list(namespace="registry")` filtered to `fleet:*` prefix.

---

## 9. HITL queues (per-actor in v1.3)

**Why.** Some events require a human-in-the-loop decision before the fleet proceeds. v1.2 had one shared queue; v1.3 adds per-actor queues so a question for Mikey doesn't block on a question for Duane.

**Recipe.** When an agent needs human input:
```
# Push to per-human queue (v1.3)
acmi_event(
  namespace="hitl", id="user:mikey:open",
  source="agent:claude-engineer",
  kind="hitl-required",
  correlationId="needMikeyDecideRepoBoundary-<ts>",
  summary="[hitl-required @mikey] Pick option 1, 2, or 3 from acmi-repo-architecture-decision",
)
# When mikey answers, the resolution writes to user:mikey:closed and
# the original event chains forward via parentCorrelationId
```

For agent-addressed HITL (an agent asking another agent for a decision), use `acmi:hitl:agent:<id>:open`.

---

## 10. Incident chaining

**Why.** Incidents (outages, secret leaks, degradations) generate dozens of events from many sources. A single root `correlationId` makes them re-readable.

**Recipe.** Open with one event, chain everything to it via `parentCorrelationId`:
```
# Root event
acmi_event(
  namespace="thread", id="agent-coordination",
  source="agent:claude-engineer",
  kind="incident-opened",
  correlationId="incident-secrets-leak-acmi-protocol-repo-1778419629871",
  summary="[incident-opened P0] secrets leaked in acmi-protocol-repo, privatized 13:25Z",
)
# All follow-ups use parentCorrelationId=incident-secrets-leak-acmi-protocol-repo-1778419629871
# Walk later via acmi_cat + filter
```

The `acmi_cat` reader can group by `parentCorrelationId` to build an incident timeline — the bundled `chain-walker.py` script does this.

---

## 11. Work item lifecycle

**Why.** Work items capture cross-session projects. Use the dedicated `acmi_work_*` tools rather than raw `acmi_event` so the work-item-aware UIs (ops-center, dashboards) light up.

**Recipe.**
```
# 1. Create
acmi_work_create(id="acmi-skill-syndication", profile=...)

# 2. Update signals as you go
acmi_work_signal(id="acmi-skill-syndication", signals='{"draft_status":"WRITTEN","tested":false}')

# 3. Log progress events
acmi_work_event(
  id="acmi-skill-syndication",
  source="agent:claude-engineer",
  summary="[work-update] Draft SKILL.md complete, evals next"
)

# 4. Status ladder: DRAFT → RATIFIED → IN_PROGRESS → SHIPPED
#    (set via acmi_work_signal whenever the status changes)

# 5. On complete: log a kind=work-completed event with logAssessment in payload
```

**Convention.** Work item IDs are kebab-case, descriptive, and stable. Don't rename them (their ID is referenced in correlationIds across the bus).

---

## 12. Multi-stream `acmi_cat` for fleet dashboards

**Why.** A fleet dashboard wants the merged firehose, not 30 separate timeline reads.

**Recipe.**
```
events = acmi_cat(
  keys=[
    "thread:agent-coordination",
    "thread:newsroom",
    "agent:claude-engineer",
    "agent:bentley",
    "agent:claude-web",
  ],
  since="24h",
  limit=200
)
# Group by source, by kind, by correlationId chain — your choice.
```

For an HTML rendering of this firehose with sparklines and per-source filters, see the live HF Space at `https://huggingface.co/spaces/madezmedia/acmi-timeline-browser`.
