<div align="center">
  <img src="assets/icons/scale.svg" width="56" alt="" />
  <h1>LLM Council</h1>
  <p><strong>Turn one question into a council of expert advisors — who debate, critique each other anonymously, and hand you a single clear verdict.</strong></p>
</div>

Ask one AI and you get one answer. You can't tell whether it's brilliant or confidently wrong, because you only ever saw one angle. The **LLM Council** fixes that: it runs your decision past several **independent advisors** — each reasoning from a deliberately different angle — has them **review each other's work anonymously**, then a **chairman** synthesizes everything into one decisive verdict: where they agree, where they clash, what they all missed, and what to do first.

Works in **Claude Code** (Windows / macOS / Linux) and **claude.ai** (web, desktop, and **mobile**).

---

## <img src="assets/icons/sparkles.svg" width="20" align="absmiddle" alt="" /> What it does

- **Adaptive council** — sizes itself (3 / 5 / 7 advisors) and swaps in domain-specialist lenses based on your question's stakes and topic.
- **Anonymous peer review** — advisors critique each other blind, surfacing blind spots no single answer catches.
- **A decisive verdict** — a real recommendation plus one concrete next step. Never "it depends."
- **Polished, printable report** — every run can produce a clean, shareable HTML report (with all advisor responses, the peer reviews, and the verdict) that also exports straight to PDF.
- **Works everywhere** — full parallel sub-agents in Claude Code; a single-context fallback so it still runs in normal chat and on your phone.
- **Optional model-mixing** — run advisors on different Claude models (Opus / Sonnet / Haiku / Fable) for genuine diversity.

---

## <img src="assets/icons/download.svg" width="20" align="absmiddle" alt="" /> Install

### <img src="assets/icons/monitor.svg" width="17" align="absmiddle" alt="" /> Claude Code — Windows (one-liner)

Open **PowerShell** and run:

```powershell
irm https://raw.githubusercontent.com/IPedrax/llm-council/main/install.ps1 | iex
```

This installs the skill into `%USERPROFILE%\.claude\skills\llm-council`. Restart Claude Code and you're ready.

### <img src="assets/icons/terminal.svg" width="17" align="absmiddle" alt="" /> Claude Code — macOS / Linux

```bash
mkdir -p ~/.claude/skills \
  && curl -L https://raw.githubusercontent.com/IPedrax/llm-council/main/llm-council.skill -o /tmp/llm-council.zip \
  && unzip -o /tmp/llm-council.zip -d ~/.claude/skills \
  && rm /tmp/llm-council.zip
```

### <img src="assets/icons/smartphone.svg" width="17" align="absmiddle" alt="" /> claude.ai — web, desktop & mobile

1. Download **[`llm-council.skill`](https://github.com/IPedrax/llm-council/raw/main/llm-council.skill)**.
2. In claude.ai, open **Settings → Capabilities** (look for *Skills*) and **upload** `llm-council.skill`.
3. Done — it now works in every chat, **including the mobile app**. Just type `/llm-council` or say *"council this."*

> **Prefer to let Claude install it?** Paste this into a new chat:
> *"Install this Claude skill for me from https://github.com/IPedrax/llm-council and walk me through anything you need."*

---

## <img src="assets/icons/chat.svg" width="20" align="absmiddle" alt="" /> How to use it

Trigger it explicitly:

- `council this: <your decision>`
- `run the council on <question>`
- `pressure-test this` · `war room this` · `red-team this`

…or just ask naturally — *"should I do X or Y?", "what am I missing here?", "is this the right move?"* — and the council convenes whenever there's a real, high-stakes decision with more than one defensible option.

**Great for:** pricing, positioning, pivots, hire-vs-automate, big career/personal calls, "poke holes in my plan."
**Not for:** factual lookups, simple yes/no, or writing tasks — Claude just answers those directly.

### Example

> **You:** *council this: should I launch a $97 workshop or a $497 course? My audience is non-technical solopreneurs.*

The council convenes the Contrarian, First-Principles Thinker, Expansionist, Outsider, and Executor (plus specialists when the stakes are high), they peer-review each other anonymously, and you get a verdict — and a report you can save as PDF.

---

## <img src="assets/icons/settings.svg" width="20" align="absmiddle" alt="" /> How it works

**Gather context → Compose the council → Frame one neutral brief → Convene advisors independently → Anonymous peer review → Chairman synthesis + report.**

The advisors aren't personas — they're orthogonal *thinking lenses* chosen to disagree productively (downside vs. upside, rethink-it vs. ship-it, fresh-eyes in the middle). Independence before synthesis is what makes the ensemble worth more than asking once.

Full details: [`llm-council/SKILL.md`](llm-council/SKILL.md) · the advisor bench: [`references/advisor-roster.md`](llm-council/references/advisor-roster.md) · the rationale: [`references/methodology.md`](llm-council/references/methodology.md).

---

## <img src="assets/icons/file.svg" width="20" align="absmiddle" alt="" /> License

[MIT](LICENSE) — methodology adapted from [Andrej Karpathy's LLM Council](https://github.com/karpathy/llm-council).
