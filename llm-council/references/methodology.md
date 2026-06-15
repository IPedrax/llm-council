# Methodology: why the council works

Optional background. Read this if you want to understand *why* the steps are shaped the way they are, so you can adapt intelligently instead of following the recipe blindly.

## The origin: Karpathy's LLM Council

Andrej Karpathy's [LLM Council](https://github.com/karpathy/llm-council) runs a query through several different frontier models, has each model **rank the others' answers anonymously**, and then a "chairman" model writes the final response using all of it. The interesting finding is that models are often better at *evaluating* answers than at *generating* them — and that they'll frequently rank another model's answer above their own when they can't see who wrote what. The ensemble plus anonymous peer review beats any single model's first answer.

## What we keep, and what we change

This skill reproduces the **structure** of Karpathy's method inside Claude:

| Karpathy's council | This skill |
|---|---|
| Several different models | Sub-agents with different thinking lenses (and optionally different Claude models) |
| Each model answers independently | Each advisor answers in isolation (separate context, or disciplined hat-switching) |
| Anonymous cross-ranking | Anonymous peer review: strongest / biggest blind spot / what all missed |
| Chairman model synthesizes | Chairman pass synthesizes into a structured verdict |

The substitution of **lenses for models** is the key adaptation. Karpathy gets diversity from model architectures; we get it primarily from deliberately conflicting perspectives. The optional model-mixing mode adds back the original source of diversity on top of the lenses.

## Why each step earns its place

- **Independence (before anyone sees anyone else).** The value of an ensemble comes from *errors being uncorrelated*. If advisors see each other first, their mistakes converge — they anchor, defer, and average toward a bland consensus. You'd get the illusion of multiple perspectives with the information content of one. This is why Full Council uses separate contexts and Solo Council demands strict hat-switching: the moment advisor B is influenced by advisor A, you've lost half the method.

- **Diverse lenses (not personas).** The advisors aren't characters; they're orthogonal ways of being right or wrong about a decision. Downside, framing, upside, fresh-eyes, and execution are chosen because a flaw invisible to one is usually glaring to another. A roster that doesn't disagree has redundant lenses — fix the roster, not the prompts.

- **Anonymous peer review (the part people skip).** This is what separates a council from "ask five times and average." Generating a take and judging a set of takes are different skills, and the second is often sharper. Reviewing surfaces the blind spot that every advisor shared, and the quietly-correct answer the loud ones drowned out. Anonymity matters because identity is a shortcut: reviewers defer to lenses they trust ("the Executor is usually right") instead of evaluating the actual argument. Randomized letters force judgment on merit.

- **A chairman, not a vote.** Averaging five opinions throws away the reasoning, and the majority is often wrong in a correlated way. The chairman's job is to weigh *arguments*, not count hands — which is exactly why it should overrule the majority when a lone dissenter has the better case, and why it gets the strongest model in model-mixing mode.

## When the method underperforms

- **Questions with one right answer.** Ensembling doesn't help a lookup; it just adds latency and noise. Don't council these.
- **Pure creation tasks.** "Write the thing" isn't a judgment call between options. (Though "which of these three drafts is strongest?" *is* a council question.)
- **Foregone conclusions.** If the user has decided and wants validation, the council will still do its job and disagree with them — which is the point, but set expectations.
- **No real context.** Five lenses applied to a one-line question with no detail produce five generic takes. The context-gathering step is what prevents this; if there's genuinely nothing to work with, ask one clarifying question first.
