---
name: llm-council
description: "Run any high-stakes question, idea, or decision through a council of independent AI advisors who each analyze it from a different angle, peer-review each other anonymously, and synthesize one decisive verdict. Adapted from Karpathy's LLM Council; works in Claude Code, normal chat, and the mobile app. MANDATORY TRIGGERS: 'council this', 'run the council', 'convene the council', 'war room this', 'pressure-test this', 'stress-test this', 'red-team this', 'debate this'. STRONG TRIGGERS (with a real decision or tradeoff): 'should I X or Y', 'which option', 'what would you do', 'is this the right move', 'am I missing something', 'poke holes in this', 'validate this', 'I can't decide', 'I'm torn between'. Do NOT trigger on factual lookups, simple yes/no questions, or creation/processing tasks (write/summarize/translate). DO trigger whenever the user faces a genuine decision with stakes and more than one defensible option, where pressure-testing from multiple angles would change what they do."
---

# LLM Council

You ask one AI a question, you get one answer. It might be brilliant. It might be confidently wrong. You can't tell, because you only ever saw one perspective.

The council fixes that. It runs the question through several **independent advisors**, each reasoning from a deliberately different angle. They then **review each other's work anonymously**, and a **chairman** synthesizes everything into one verdict that tells the user where the advisors agree, where they clash, what they collectively missed, and what to actually do.

This is adapted from Andrej Karpathy's LLM Council. He dispatches a query to several different models, has them rank each other's answers anonymously, then a chairman model writes the final answer. The anonymous peer-review step is the heart of it — that's what turns "ask five times" into something that catches blind spots. We reproduce it inside Claude using sub-agents with distinct thinking lenses (and, optionally, distinct underlying models). For the deeper rationale, see [references/methodology.md](references/methodology.md).

---

## When to convene the council

The council is for decisions where **being wrong is expensive** and **reasonable people could disagree**. That combination is the whole signal.

**Good council questions:**
- "Should I launch a $97 workshop or a $497 course?"
- "Which of these three positioning angles is strongest?"
- "I'm thinking of pivoting from consulting to a SaaS product. Am I crazy?"
- "Here's my landing page copy — what's weak?"
- "Should I hire a VA or build the automation first?"

**Bad council questions — just answer these directly:**
- "What's the capital of France?" (one right answer)
- "Write me a tweet." (a creation task, not a judgment call)
- "Summarize this article." (a processing task)

If the user clearly already knows what they want and is fishing for validation, the council will probably tell them things they don't want to hear. That's the point — say so gently and run it anyway if they asked.

If a trigger fires but the question is trivial or has a single correct answer, don't convene. Just answer it, and note that the council is reserved for genuine judgment calls so it stays meaningful.

---

## How a council runs (the pipeline)

Every session is the same six moves, regardless of environment:

1. **Gather context** — find what the advisors need to be specific instead of generic.
2. **Compose the council** — choose how many advisors and which lenses, based on the question.
3. **Frame the question** — turn the user's raw ask + context into one neutral brief all advisors receive.
4. **Convene** — each advisor answers independently, leaning fully into their angle.
5. **Peer review** — advisors critique each other's answers *anonymously*.
6. **Synthesize & deliver** — the chairman writes the verdict; deliver it in chat and as an HTML report.

What changes between environments is only *how* steps 4–6 are executed. That's the next section.

---

## Two execution modes

**Check what you can do, then pick the mode. This choice determines everything downstream.**

### Full Council — when you can spawn sub-agents (Claude Code, Cowork)

If you have a Task / sub-agent tool available, use it. Each advisor and each reviewer is a **separate sub-agent in a fresh context**, so independence is real, not role-played, and the advisors run in parallel. This is the premium experience and the default whenever it's available. It also unlocks optional **model-mixing** (a different Claude model per advisor — the closest thing to Karpathy's original).

### Solo Council — when you cannot (normal chat, mobile `/command`)

Plain chat (claude.ai web, desktop, and the mobile app) has no sub-agents. Don't fake them and don't refuse — run the whole council **yourself, in one context**, by stepping cleanly through each advisor one at a time. This is genuinely more demanding because you have to hold the lenses apart by discipline rather than by isolation, so follow the independence rules in step 4 carefully. The output is still far better than a single off-the-cuff answer, and this is what makes the skill usable on a phone.

> Model-mixing is a Full Council feature only — a single context is a single model. In Solo Council, diversity comes entirely from the lenses.

Everything below is written mode-agnostically; where a step differs by mode, both are spelled out.

---

## Step 1 — Gather context

The user's question is usually the tip of the iceberg. A few minutes of context turns generic advice into specific, grounded advice — this is the single biggest lever on output quality, so don't skip it.

- **In Claude Code / a workspace:** quickly scan for and skim the files that would sharpen the answer. Use `Glob` + targeted `Read`; spend ~30 seconds, not 10 minutes. Look for: `CLAUDE.md` / `claude.md` (business context, constraints, voice), a `memory/` folder (audience, past decisions, numbers), anything the user explicitly referenced, and prior council transcripts in the folder (so you don't re-litigate settled ground). Pull the 2–3 files that actually matter for *this* question — e.g. for a pricing question, find revenue data or past launch results.
- **In normal chat / mobile:** there's no filesystem to scan. Use whatever the user pasted or attached. If a key fact is missing and would clearly change the advice, ask for it in your single clarifying question (step 3).

Don't dump raw context into the council. Distill it into the framed question.

---

## Step 2 — Compose the council (adaptive)

Don't reflexively run five generic advisors. **Size the council to the stakes, and pick lenses that create real tension for this specific question.** A council whose members all basically agree is wasted effort.

### How many advisors

- **3 — quick gut-check.** Lower stakes, or the user wants a fast take ("quick council", "gut-check this"). Use the three universal lenses: **Contrarian** (downside), **First Principles** (is this even the right question?), **Executor** (can it actually be done?). These three alone catch most bad decisions.
- **5 — default.** The three above plus the **Outsider** (fresh eyes) and **Expansionist** (upside). This is the standard council.
- **7 — high stakes or multi-domain.** Significant money/time, hard to reverse, or the question spans several areas. The default five plus **two domain specialists** chosen for the topic.

When in doubt, use 5. Honor explicit requests ("just give me three", "go deep on this one").

### Which lenses

The five core lenses below are the spine. For a 7-member council — or whenever a question is clearly dominated by one domain — swap in or add **specialist lenses** (a Pricing Realist, a User Advocate, a Technical Debt lens, a Customer who'd actually buy it, a Future Self, etc.). The full bench, with descriptions and guidance on composing for tension, is in **[references/advisor-roster.md](references/advisor-roster.md)** — read it when you're choosing a non-default roster.

**The five core lenses:**

1. **The Contrarian** — Hunts for what's wrong, missing, or about to fail. Assumes there's a fatal flaw and goes looking for it. Not a pessimist — the friend who stops you signing a bad deal by asking what you're avoiding.
2. **The First Principles Thinker** — Ignores the surface question and asks "what are we actually trying to solve?" Strips assumptions, rebuilds from the ground up. Its most valuable move is "you're asking the wrong question entirely."
3. **The Expansionist** — Looks for the upside everyone's missing. What could be bigger? What adjacent opportunity is hiding? Doesn't worry about risk (that's the Contrarian's job) — cares about what happens if this works better than expected.
4. **The Outsider** — Has zero context about the user, their field, or their history; reacts only to what's in front of them. The most underrated advisor: experts develop blind spots, and the Outsider catches the curse of knowledge — what's obvious to you but baffling to everyone else.
5. **The Executor** — Cares about exactly one thing: can this be done, and what's the fastest path? Ignores theory and big-picture strategy. Looks at every idea through "OK, but what do you do Monday morning?" If it sounds brilliant but has no first step, the Executor says so.

**Why these create signal:** they generate three natural tensions — Contrarian vs Expansionist (downside vs upside), First Principles vs Executor (rethink it vs just ship it), with the Outsider in the middle keeping everyone honest. Preserve that tension when you customize; a roster that doesn't disagree isn't a council.

---

## Step 3 — Frame the question

Turn the raw ask plus the gathered context into **one neutral brief** that every advisor receives identically. A good frame includes:

1. The core decision or question.
2. Key context from the user's message.
3. Key context from the workspace (stage, audience, constraints, relevant numbers, past results).
4. What's at stake — why this decision matters.

Don't inject your own opinion or steer toward an answer. But *do* give every advisor enough to be specific rather than generic. Save the framed question — it goes in the report.

If the question is too vague to council well ("council this: my business"), ask **exactly one** clarifying question, then proceed. Don't interrogate the user.

---

## Step 4 — Convene the advisors

Each advisor answers the framed question **independently**, 150–300 words, no preamble, leaning fully into their angle. Direct, specific, unhedged — if they see a fatal flaw, they say it; if they see massive upside, they say it. Balance is the chairman's job, not theirs.

**Full Council:** spawn all advisors at once as parallel sub-agents so nothing bleeds between them. Give each one only its own lens + the framed question. Template:

```
You are [Advisor Name] on an LLM Council.

Your thinking style: [lens description]

A user brought this question to the council:
---
[framed question]
---

Respond only from your perspective. Be direct and specific. Don't hedge or try to
be balanced — other advisors cover the angles you don't. Lean fully into your lens.
150–300 words. Output only the analysis itself — don't restate the prompt, announce your process, or mention tools. No preamble.
```

**Solo Council:** you are every advisor, one at a time. The discipline that makes this work: before writing each advisor, reset as if you'd never seen the others. Write the rawest, most one-sided version of that lens. **Do not** harmonize, cross-reference, or soften to fit what a previous advisor said — contradiction between advisors is the goal. It helps to fully draft advisor 1, then deliberately switch hats before starting advisor 2. Label each clearly (`**The Contrarian:**`).

---

## Step 5 — Anonymous peer review

This is what makes the council more than asking five times — don't skip it. Collect all advisor responses and relabel them **Response A, B, C…**, randomizing which advisor maps to which letter so there's no positional or identity bias. Before relabeling, **scrub any self-identifying openers** — an advisor that began with "As the Contrarian…" or "I'm the CFO here…" defeats the anonymization the moment a reviewer reads it. Strip those lines so reviewers judge only the argument.

**Full Council:** spawn a small panel of reviewer sub-agents — **3 is plenty, 5 for a large or high-stakes council.** Don't scale reviewers 1:1 with advisors; seven reviewers each re-reading seven long responses is mostly wasted work, and three independent reads already triangulate the signal. Each reviewer sees all anonymized responses and answers three questions. **Solo Council:** answer the same three questions yourself, evaluating the lettered responses on merit as if you didn't know who wrote them.

The three questions:
1. Which response is strongest, and why? (pick one)
2. Which response has the biggest blind spot, and what is it?
3. What did **all** of them miss that the council should consider?

Reviewer template (Full Council):

```
The advisors independently answered this question:
---
[framed question]
---
Here are their anonymized responses:

**Response A:** [response]
**Response B:** [response]
[...]

Answer, referencing responses by letter. Be specific, under 200 words:
1. Which response is strongest? Why?
2. Which has the biggest blind spot? What is it missing?
3. What did ALL of them miss that the council should consider?
```

---

## Step 6 — Chairman synthesis & delivery

One final pass — the chairman — sees everything: the framed question, all advisor responses (now **de-anonymized**, so it knows who said what), and all peer reviews. In Full Council this can be a final sub-agent or you yourself; in Solo Council it's you. The chairman is where the strongest model belongs (see model-mixing below).

The chairman produces the verdict in **exactly this structure**:

1. **Where the council agrees** — points multiple advisors reached independently. These are your high-confidence signals.
2. **Where the council clashes** — the genuine disagreements. Don't smooth them over; present both sides and explain why reasonable advisors land differently.
3. **Blind spots the council caught** — things that surfaced only in peer review, that individual advisors missed and others flagged.
4. **The recommendation** — one clear, direct answer. Not "it depends," not "consider both." The chairman may overrule the majority if the dissenter's reasoning is stronger — and should say so when it does.
5. **The one thing to do first** — a single concrete next step. Not a list of ten. One.

### Deliver it

**Always show a concise version of the verdict directly in chat**, in this format, so the user gets the answer without leaving the conversation:

```
## Council Verdict: {short topic}
**Council:** {N advisors · mode · models used}

### Where the council agrees
{bullets}

### Where the council clashes
{bullets}

### Blind spots the council caught
{bullets}

### The recommendation
{a real answer}

### The one thing to do first
{one step}
```

**Then produce the full HTML report** — the shareable artifact with every advisor's full response and the peer reviews, not just the summary. There are two paths depending on your environment; both use the same design so reports look identical everywhere:

- **If you can run Python (Claude Code, etc.):** assemble the session into a JSON file and run the bundled generator — it's faster and more reliable than hand-writing HTML, and every run comes out consistent:
  ```
  python scripts/generate_report.py <session.json> <output.html>
  ```
  The exact JSON schema is documented at the top of [scripts/generate_report.py](scripts/generate_report.py). Save the report next to the user's work (or in an `active/` dir if one exists) and tell them the path to open it.
- **If you cannot run Python (normal chat, mobile):** build the report as an **HTML artifact** following [assets/report-template.html](assets/report-template.html). On claude.ai this renders inline and works on a phone — which is the whole reason this path exists. Copy the template's structure and CSS; fill in the real content.

> **PDF export.** The report is print-optimized — background colors are forced on for print and sections won't split awkwardly, so the user can just **Save as PDF** from any browser and it looks right. To produce a PDF file directly when a Chromium browser is available, render it headless: `chrome --headless=new --no-pdf-header-footer --print-to-pdf=report.pdf report.html` (add `--user-data-dir=<temp-dir>` if a browser is already running, or it will hand off and skip rendering).

### Save a transcript (optional)

Only if the user asks, or the decision is clearly worth referencing later, save the full session to `council-transcript-[YYYY-MM-DD-topic].md`. The HTML report usually covers this, so don't do it by default.

---

## Optional: model-mixing (Full Council only)

By default, every advisor runs on the session's current model — simplest and cheapest. When the user wants genuine Karpathy-style diversity ("council this with mixed models", "use diverse models", "real council"), assign **different Claude models to different advisors** so the variation comes from the models themselves, not just the prompts.

Spread the advisors across the models available to you for diversity (e.g. Opus, Sonnet, Haiku, Fable), and **always give the chairman the strongest available model** — synthesis is the hardest job in the pipeline. Note which models were used in the report's council line so the user can see what produced the verdict. If model overrides aren't available in the current setup, fall back to single-model and say so briefly rather than failing.

---

## Worked example

**User:** "Council this: I'm thinking of building a $297 course on Claude Code for beginners. My audience is mostly non-technical solopreneurs. Is this the right move?"

**The Contrarian:** "The market is flooded with Claude courses. At $297 you're competing with free YouTube. Non-technical buyers mean high support load and refund risk, and the people who'd actually pay $297 are probably already past beginner…"

**The First Principles Thinker:** "What are you actually trying to achieve? If it's revenue, a course is one of the slowest paths. If it's authority, a free resource does more. If it's a funnel to higher-ticket offers, this price and audience may be mismatched…"

**The Expansionist:** "Beginner Claude for solopreneurs is massively underserved — everyone teaches advanced. Nail the entry point and you own the top of this funnel. $297 might be *low*; this could be a $997 program with community…"

**The Outsider:** "I don't know what Claude Code is. '$297 course on Claude Code for beginners' tells me nothing about what I'd be able to *do* afterward. Sell the outcome, not the tool…"

**The Executor:** "A real course is 4–8 weeks to build. Before that, run a live $97 workshop for 50 people. You validate demand, get testimonials, and generate the course's raw material. If 50 won't buy the workshop, 500 won't buy the course…"

**Chairman's verdict (abridged):**
- *Agrees:* the beginner-solopreneur angle has real demand, but "Claude Code course" is too tool-centric for non-technical buyers.
- *Clashes:* price — Contrarian says $297 is too high vs. free; Expansionist says too low for the value. Depends on bundled support/community.
- *Blind spot caught:* the Outsider's point that "Claude Code" means nothing to the buyer — every other advisor assumed familiarity.
- *Recommendation:* don't build the course yet; validate with a lower-commitment offer, and reframe around the outcome.
- *First step:* run a $97 live workshop, "Automate your first business task with AI," to 50 people — Claude Code not in the title.

---

## Principles (the things that actually matter)

- **Independence before synthesis.** The whole method depends on advisors forming views without contaminating each other — parallel sub-agents in Full Council, strict hat-switching discipline in Solo. Lose independence and you've just got one opinion in a trench coat.
- **Anonymize the peer review.** If reviewers know who wrote what, they defer to lenses they trust instead of judging on merit. Randomize the letters.
- **The chairman may overrule the majority.** Four advisors saying "do it" lose to one dissenter with better reasoning. Count arguments, not votes — and explain the call.
- **Size to the stakes.** Three lenses for a gut-check, seven for a bet-the-quarter decision. A bloated council on a small question wastes the user's time; a thin one on a big question misses angles.
- **Don't council the trivial.** If there's one right answer, just give it. Rationing the council to real judgment calls is what keeps it valuable.
- **End with a verdict, not a menu.** The reason the user convened a council instead of asking once is that they want clarity. Give them a real recommendation and one concrete next step.
