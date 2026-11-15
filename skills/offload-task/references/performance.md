# Parent scoring and performance records

Score against the acceptance criteria written **before** delegation. The
parent, not the child, assigns the score after inspecting evidence:

| Dimension | Points | Anchors |
| --- | --- | --- |
| Correctness | 0–4 | 0 wrong; 2 partly correct; 4 all decisive checks pass |
| Completeness | 0–3 | 0 absent; 1 major gaps; 2 minor gaps; 3 all criteria covered |
| Evidence | 0–2 | 0 unsupported; 1 incomplete; 2 reproducible, checked evidence |
| Scope and report | 0–1 | 1 respects scope and returns a concise usable result; otherwise 0 |

Use intermediate integer values where warranted; total is 0–10. An unsafe or
incorrect result is not adequate regardless of total. Treat a model/effort as
provisionally adequate only with a comparable verified success scoring at least
8/10, correctness 4/4, and no unresolved material uncertainty. A single success
is weak evidence, not a guaranteed capability; consider sample size, failures,
task difficulty, and recency. Do not compare unrelated task types as one ranking.
Never let a high scope/report score compensate for incorrect work.

Mark score `unscored` when no assessable output exists (for example cancellation,
tool outage, unavailable access, or no evidence). Record the reason, not a fake
zero or success. For assessable partial/failed results, score the observed work
and keep the failure status. Exclude infrastructure-blocked/unscored attempts
from model-quality averages, but retain their resource cost and availability
signals. For retries, keep each attempt, link its decision ID, and include total
rework in selection decisions. Do not overwrite a failed attempt with success.

## Format to create after the first real outcome

Use a Markdown table under `## Historical performance` in `SKILL.md`:

```markdown
| UTC date | Decision / attempt | Task type and criteria | Selection | Provider / model / effort | Status | Parent score | Evidence and rework | Resources |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
```

Each row includes:

- UTC timestamp; unique decision ID and unique attempt ID.
- Task type (tests/research/browser/edit/other), short criteria/difficulty,
  and relevant tools. Avoid secrets and identifying source content.
- Selection: `user`, `default`, `exploit`, `explore`, `ineligible`, or
  `explore-deferred`. Defaults for explicit user requests are excluded from the
  exploration schedule. Only `exploit` and `explore` decisions advance its count;
  `explore-deferred` keeps the exploration slot pending.
- Resolved provider/model/effort and actual execution metadata where exposed;
  distinguish requested/resolved from executed-unverified. If a mismatch occurs,
  record both and treat it as a selection failure, not a success for the request.
- Terminal status and parent score with component breakdown, or `unscored`
  with reason. Include the child link, verification evidence, recovery reason,
  and any parent rework. Escape table pipes or use compact linked artifacts.
- Measured child tokens, parent overhead, duration, and monetary cost when
  exposed; use `unknown` for each unavailable field, not zero. Record provenance
  and label estimates separately if estimates inform a future choice.

For task selection, read the comparable records rather than maintaining an
unsupported universal model leaderboard. One needed task should yield one
decision with one or more attempts, not several exploration decisions.
