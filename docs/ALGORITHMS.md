# The learning loop

These are understandable MVP heuristics, not a calibrated psychometric or neuroscience model. They are deterministic given the database, time, weights, and random seed. Neither recommendations, mastery updates, nor review scheduling call an LLM.

## 1. State and forgetting

For a concept, store raw mastery `m ∈ [0,1]`, confidence `q ∈ [0,1]`, interest `i ∈ [0,1]`, exposures, retrieval counters, spaced success streak, interval `I`, last review, and next review.

If a concept has a last review, predicted retention at elapsed `t` days is:

```text
R(t) = exp(log(0.8) × max(0,t) / max(0.25,I))
effective_mastery = m × R(t)
```

Before the first review, retention is 1. An interval is the point at which predicted retention is approximately 80%. Negative elapsed times are clamped. Displaying decay does not mutate the database. It affects readiness, progress, and recommendations.

## 2. Evidence updates

An answer uses prior `p = effective_mastery(now)`. Let `d` be the card's difficulty. Let `e = 0.25` if retrieval happened less than 20 hours ago; otherwise `e = 1`.

```text
correct:
  gain = (0.27 + 0.15d) × e
  m = clamp(p + gain × (1-p))

incorrect:
  loss = (0.30 + 0.12(1-d)) × max(0.5,e)
  m = clamp(p × (1-loss))

either answer:
  q = clamp(q + 0.12e × (1-q))
```

Higher-difficulty success is stronger positive evidence. Failure on an easier task is stronger negative evidence. Repeated same-day answers have less influence. After applying the update and scheduling, anchor last reviewed to now to avoid charging the same elapsed decay twice.

Confidence measures how much behavioral evidence the estimate has; it is not self-reported certainty or percentage correct. It is stored and supplied to the tutor. It does not directly multiply the recommendation score in this MVP.

Other signals:

| Interaction | Update |
| --- | --- |
| Shown | Increase times seen, update last seen; no mastery increase |
| Dwell ≥ 12 seconds | At most +0.025 raw mastery, never raising reading-only mastery above 0.25; interest +0.01 |
| “I know this” | +0.08 raw mastery, capped at 0.45; never decreases already higher mastery |
| Tutor, deeper, save | Interest increases by `0.04 × (1-i)`; no mastery increase |
| Skip in < 3 seconds | Interest −0.015; no assumed knowledge failure |
| Revisit | Logged only |

Reading or “known” schedules a first review tomorrow if none exists. No passive event increases a retrieval streak. These caps make self-report useful without certifying expertise. Tutor/deeper interest updates are modest rather than evidence of knowing or not knowing.

The initial level supplies a low-confidence prior only on never-encountered concepts: beginner 0, intermediate 0.1, advanced 0.2. It does not mark concepts encountered or mastered. Changing subjects does not erase existing learning evidence.

## 3. Scheduling

The first correct retrieval schedules tomorrow. Successes separated by at least 20 hours increase a success streak and follow:

```text
1 → 3 → 7 → 14 → 30 days
new_interval = min(90, max(ladder_step, previous_interval × growth))
growth = 2.0 if updated mastery ≥ 0.5, otherwise 1.35
```

After the fifth spaced success, interval multiplication can extend the schedule to 90 days. An immediate repeat cannot move a future review farther out or increase the spaced streak. If a correct early retrieval follows an already overdue short retry, the new interval is at least one day.

Failure resets the streak, reduces the stability interval to `max(0.25, previous_interval × 0.35)`, and schedules a retry in **10 minutes**. The interval and the next due date are intentionally distinct after a lapse: a retry happens sooner than the long-term retention estimate.

Urgency before the due date is `0.25 × (1-R)`. At/after due:

```text
urgency = min(1, 0.7 + 0.3 × days_overdue / max(1,I))
```

“Mastered” in the dashboard requires effective mastery ≥ 0.8 **and** at least three spaced successes. A concept can lose this status as retention decays. Reviews are quiz/challenge presentations of existing content rather than a separate set of duplicated review cards.

## 4. Candidate eligibility

Start with stored cards in selected subjects. Optional subject filters restrict this pool. A concept is eligible when every prerequisite has effective mastery ≥ 0.25. Missing prerequisites count as zero. A fresh concept has readiness 1 when no prerequisites exist.

Selecting a locked concept in a path follows the weakest missing prerequisite recursively until an eligible foundation is found. Validated maps have no cycles. The practice tab restricts candidates to quiz/challenge cards of encountered concepts; when no review is due, it is clearly labeled practice.

## 5. Score

```text
score = Σ(weight × component) − weight_repetition × repetition_penalty
```

| Component | Default weight | Calculation |
| --- | ---: | --- |
| Learning value | 1.2 | `min(1, 0.6(1-m_eff) + 0.1 min(3, dependent_count) + 0.3 retrieval_bonus)` |
| Review urgency | 2.4 | Urgency for quiz/challenge; 12% of urgency for teaching cards |
| Difficulty match | 1.0 | `max(0, 1 - abs(card_difficulty - min(.95,m_eff+.25))/.75)` |
| Interest | 0.7 | The concept's bounded interest state |
| Prerequisite relevance | 0.8 | `min(1,dependent_count/3) × (1-m_eff)` |
| Novelty | 0.8 | 1 for unseen concepts; .3 for a card absent from recent history; otherwise 0 |
| Variety | 0.7 | .6 for a different card type + .4 for a different concept than the previous card |
| Repetition penalty (subtract) | 2.0 | `min(2, .6 × same_concept_in_last_5 + 1 if same_card_in_last_8)` |
| Exploration | 0.2 | Seeded uniform number in [0,1), for small deterministic exploration among eligible ideas |

Here `retrieval_bonus` is 1 only for a quiz/challenge of an encountered concept. A non-microlesson on an unseen concept has learning value multiplied by .25 and novelty by .4. This favors learning before assessment. After two retrieval cards in a row, another retrieval card has zero variety, urgency multiplied by .25, and an extra .7 repetition penalty, blending reviews into new learning.

The selector scores every eligible candidate, picks the highest score, and adds it to temporary recent history before choosing the next card. Ties resolve by stable card ID. The RNG is initialized with `UTC YYYYMMDD + interaction_count` at the API boundary; tests provide an explicit seed and timestamp. No timestamps or random card selection are hidden in the scoring function.

User-visible history is read from the last 20 shown interactions. The client excludes up to 40 buffered/previous IDs. If a finite offline pool is exhausted, it can recycle practice content while still excluding the current card. This provides continued local study; offline mode cannot invent an unlimited number of distinct lessons.

## 6. Adaptation, visibility and auditing

Scores, weights, seed, prerequisite readiness, effective mastery at selection, a human-readable reason, and whether it is due retrieval are persisted in `recommendations`. A card's “Why this card?” panel shows component values. Full metadata is available in API responses and the database.

An actual displayed card creates `shown`; prefetched recommendations do not. Answer events are graded against `questions`, never a client-provided correct flag. The `(presentation_id, kind)` uniqueness constraint makes retry/replay idempotent. Every new answer records a `reviews` row containing the before/after mastery and next interval.

After consequential evidence, the frontend refreshes only the unshown tail. Every new scoring pass therefore sees updated evidence. There can be up to four prefetched cards before another read-only scoring request; an answer explicitly invalidates that tail. There is no LLM in this feedback loop.

## 7. Limitations and tuning

- The coefficients are transparent starting points, not scientifically fitted probabilities.
- Interests are concept-local; selecting a subject makes it eligible but does not impose a fixed subject quota.
- Exploration occurs among prerequisite-eligible concepts in selected subjects, not unrelated subjects.
- Confidence is exposed for interpretation/tutoring; future calibration could make it a separate recommendation factor.
- A single-user process lock and in-process background loop are deliberate simplifications.
- The model evaluates self-report gently but is not designed to resist a user deliberately gaming their own statistics.
- Review due dates are real. The seed never inserts fabricated progress, incorrect answers, streaks, or overdue reviews.

Weights are editable in Settings → Recommendation tuning, persisted to the database, and constrained to finite values 0–10 by the API. The UI offers 0–5. Other thresholds are centralized in `mastery.py`, `spaced_repetition.py`, and `recommender.py`.
