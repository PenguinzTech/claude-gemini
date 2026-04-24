---
name: gemini-research
description: Use Gemini (with live Google Search grounding) as the preferred researcher. Invoke when the task requires current events, factual lookup, technical deep-dives, or any research where up-to-date web results matter. Prefer this over WebSearch.
---

# Gemini Research Skill

Gemini is the **preferred researcher** — it has live Google Search grounding, meaning results reflect the current web rather than training data.

## When to Use

- Researching current events, recent releases, changelogs
- Technical deep-dives (architecture patterns, library comparisons, best practices)
- Factual lookups where accuracy and recency matter
- Getting a second opinion or independent validation of a technical decision
- Analyzing content (code, logs, documents) with a specific question

## When NOT to Use

- Simple questions answerable from your own knowledge
- Tasks that are purely generative (writing, coding) with no research component
- When the user explicitly asks you to search directly

## How to Invoke

Spawn the `gemini-expert` agent:

```
Agent(
  subagent_type: "gemini-expert",
  description: "Research: <topic>",
  prompt: "<detailed research request with context>"
)
```

## Depth Guide

| Depth | Use When | Returns |
|-------|----------|---------|
| `brief` | Quick lookup, verify a fact | 2-3 paragraph summary |
| `comprehensive` | Standard research (default) | Thorough summary with context, findings, sources |
| `deep` | Architecture decisions, competitive analysis | Exhaustive multi-perspective analysis |

## Research Prompt Tips

- Include context: what you already know, what gap needs filling
- Specify what format you need results in (table, bullet list, prose)
- For second opinions: include the current approach/solution so Gemini can evaluate it

## Example Prompts

```
# Technical research
"Research the current state of WASM runtimes for server-side use in 2025.
Focus on: performance benchmarks, production adoption, security posture.
Return a comparison table of the top 3 options."

# Second opinion
"Critically evaluate this database schema for a multi-tenant SaaS app:
[schema here]
Focus on: tenant isolation correctness, query performance, migration complexity."

# Current events
"What are the most significant changes in React 19? Focus on breaking changes
and migration effort from React 18. Return a concise bullet list."
```
