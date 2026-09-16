"use client";

import { useState } from "react";
import {
  ArrowDown,
  ArrowUpRight,
  Bookmark,
  Check,
  CheckCheck,
  ChevronDown,
  ChevronUp,
  Clock3,
  Code2,
  Eye,
  Lightbulb,
  MessageCircle,
  RotateCcw,
  Sparkles,
  X,
} from "lucide-react";
import { api, errorMessage, percent } from "@/lib/api";
import type { Card, EventKind, EventResult } from "@/types";
import { MathBlock } from "./math";
import { Visualization } from "./visualizations";

const labels = {
  micro_lesson: "MICROLESSON",
  quiz: "QUICK CHECK",
  flashcard: "RECALL",
  visualization: "EXPLORE VISUALLY",
  example: "WORKED EXAMPLE",
  challenge: "A LITTLE CHALLENGE",
};
type Props = {
  card: Card;
  position: number;
  active: boolean;
  event: (
    card: Card,
    kind: EventKind,
    extra?: { answer?: number; seconds?: number },
    adapt?: boolean,
  ) => Promise<EventResult>;
  patch: (id: string, data: Partial<Card>) => void;
  tutor: (card: Card, prompt?: string) => void;
  next: () => void;
  previous: () => void;
};

export function LearningCard({
  card,
  position,
  active,
  event,
  patch,
  tutor,
  next,
  previous,
}: Props) {
  const [revealed, setRevealed] = useState(false);
  const [more, setMore] = useState(false);
  const [reason, setReason] = useState(false);
  const [answer, setAnswer] = useState<number | null>(null);
  const [result, setResult] = useState<EventResult | null>(null);
  const [busy, setBusy] = useState(false);
  const [saving, setSaving] = useState(false);
  const [known, setKnown] = useState(false);
  const [error, setError] = useState("");
  const isQuiz = card.type === "quiz" || card.type === "challenge";
  const isFlash = card.type === "flashcard";
  const save = async () => {
    setSaving(true);
    setError("");
    try {
      const value = await api<{ saved: boolean }>(`/cards/${card.id}/saved`, {
        method: "PUT",
        body: JSON.stringify({ saved: !card.saved }),
      });
      patch(card.id, value);
      if (value.saved) await event(card, "saved");
    } catch (e) {
      setError(errorMessage(e));
    } finally {
      setSaving(false);
    }
  };
  const submit = async (choice: number) => {
    if (busy || result) return;
    setBusy(true);
    setAnswer(choice);
    setError("");
    try {
      setResult(await event(card, "answer", { answer: choice }, true));
    } catch (e) {
      setError(errorMessage(e));
      setAnswer(null);
    } finally {
      setBusy(false);
    }
  };
  const markKnown = async () => {
    setBusy(true);
    setError("");
    try {
      await event(card, "known", {}, true);
      setKnown(true);
    } catch (e) {
      setError(errorMessage(e));
    } finally {
      setBusy(false);
    }
  };
  return (
    <article
      className={`learning-card ${card.color} ${active ? "is-active" : ""}`}
      aria-label={card.title}
      data-presentation-id={card.presentation_id}
    >
      <div className="card-top">
        <div className="subject-chip">
          {card.subject_id === "cs" ? (
            <Code2 size={14} />
          ) : (
            <span className="math-symbol">∑</span>
          )}
          {card.subject}
          <span>/</span>
          {card.topic}
        </div>
        <button
          aria-label={card.saved ? "Remove bookmark" : "Bookmark card"}
          title={card.saved ? "Remove bookmark" : "Save for later"}
          className={`icon-button bookmark ${card.saved ? "selected" : ""}`}
          onClick={() => void save()}
          disabled={saving}
        >
          <Bookmark size={20} fill={card.saved ? "currentColor" : "none"} />
        </button>
      </div>
      <div className="card-scroll">
        <div className="card-kicker">
          <span className="tiny-dot" />
          {card.recommendation_reason?.is_review
            ? "TIME TO REVISIT"
            : labels[card.type]}
          {card.source === "ai" ? (
            <span>· AI</span>
          ) : card.source === "notes" ? (
            <span>· YOUR NOTES</span>
          ) : null}
          <span className="duration">
            <Clock3 size={12} />
            {card.estimated_seconds} sec
          </span>
        </div>
        <h2>{card.title}</h2>
        <p className="card-hook">{card.hook}</p>
        {isQuiz && card.quiz ? (
          <div className="quiz-area">
            <h3>{card.quiz.question}</h3>
            <div className="quiz-options">
              {card.quiz.answers.map((choice, i) => (
                <button
                  key={i}
                  disabled={busy || !!result}
                  onClick={() => void submit(i)}
                  className={`quiz-option ${answer === i ? "chosen" : ""} ${result?.correct_answer === i ? "correct" : ""} ${result && answer === i && !result.correct ? "incorrect" : ""}`}
                >
                  <span className="option-letter">
                    {String.fromCharCode(65 + i)}
                  </span>
                  <span>{choice}</span>
                  {result?.correct_answer === i ? (
                    <Check size={18} />
                  ) : result && answer === i ? (
                    <X size={18} />
                  ) : null}
                </button>
              ))}
            </div>
            {result && (
              <div
                role="status"
                className={`answer-feedback ${result.correct ? "success" : "try-again"}`}
              >
                <b>
                  {result.correct
                    ? "That’s it. A little more connected."
                    : "A useful mistake. Let’s untangle it."}
                </b>
                <p>{result.explanation}</p>
                <small>
                  {result.correct
                    ? "Your mastery and review schedule have been updated."
                    : "This concept will return for another try."}
                </small>
              </div>
            )}
          </div>
        ) : isFlash ? (
          <div className={`flashcard-body ${revealed ? "flipped" : ""}`}>
            <span className="eyebrow">
              {revealed
                ? "THE IDEA, REVEALED"
                : "PAUSE. RETRIEVE. THEN REVEAL."}
            </span>
            {revealed ? (
              <>
                <p>{card.explanation}</p>
                {card.equation && <MathBlock equation={card.equation} />}
              </>
            ) : (
              <>
                <div className="flash-symbol">↺</div>
                <p>
                  Try answering from memory.
                  <br />
                  Even the effort helps it stick.
                </p>
              </>
            )}
            <button
              className="secondary-button"
              onClick={() => setRevealed(!revealed)}
            >
              {revealed ? <RotateCcw size={16} /> : <Eye size={16} />}{" "}
              {revealed ? "Try recalling again" : "Reveal explanation"}
            </button>
          </div>
        ) : (
          <>
            {card.visualization && (
              <Visualization visual={card.visualization} />
            )}
            <p className="lesson-explanation">{card.explanation}</p>
            {card.equation && <MathBlock equation={card.equation} />}
            {card.code && (
              <pre className="code-block">
                <code>{card.code}</code>
              </pre>
            )}
            {card.steps.length > 0 && (
              <div className="worked-example">
                <button onClick={() => setMore(!more)} aria-expanded={more}>
                  <Lightbulb size={16} />
                  <span>Make it concrete</span>
                  {more ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
                </button>
                {more && (
                  <div>
                    {card.steps.map((step, i) => (
                      <p key={i}>{step}</p>
                    ))}
                  </div>
                )}
              </div>
            )}
          </>
        )}
        {(!isQuiz || result) && (!isFlash || revealed) && (
          <div className="takeaway">
            <span>THE TAKEAWAY</span>
            <p>{card.takeaway}</p>
          </div>
        )}
        {error && (
          <p className="error-message" role="alert">
            {error}
          </p>
        )}
        <div className="card-actions">
          <button
            onClick={() => void markKnown()}
            disabled={busy || known}
            className={known ? "known" : ""}
          >
            <CheckCheck size={17} />
            {known ? "Noted for your next review" : "I know this"}
          </button>
          <button
            onClick={() =>
              tutor(
                card,
                "Go deeper. Explain the underlying reasoning and give me a more challenging example.",
              )
            }
          >
            <ArrowUpRight size={17} />
            Go deeper
          </button>
        </div>
      </div>
      <div className="card-footer">
        <button
          className="why-button"
          onClick={() => setReason(!reason)}
          aria-expanded={reason}
        >
          <Sparkles size={14} />
          <span>
            {card.recommendation_reason?.label ||
              "Chosen for your learning journey"}
          </span>
          <ChevronDown size={13} />
        </button>
        <button className="ask-button" onClick={() => tutor(card)}>
          <MessageCircle size={17} />
          <span>Ask tutor</span>
        </button>
      </div>
      {reason && (
        <div className="reason-panel">
          <div>
            <b>Why this card?</b>
            <button
              aria-label="Close recommendation explanation"
              className="icon-button"
              onClick={() => setReason(false)}
            >
              <X size={16} />
            </button>
          </div>
          <p>
            {card.recommendation_reason?.label}. Mastery when selected:{" "}
            {percent(
              Number(
                card.recommendation_reason?.mastery_at_selection ??
                  card.mastery.effective_mastery,
              ),
            )}
            .
          </p>
          <dl>
            {[
              "learning_value",
              "review_urgency",
              "difficulty_match",
              "interest",
              "novelty",
              "variety",
              "repetition_penalty",
            ].map(
              (key) =>
                typeof card.recommendation_reason?.[key] === "number" && (
                  <div key={key}>
                    <dt>{key.replaceAll("_", " ")}</dt>
                    <dd>
                      {Number(card.recommendation_reason[key]).toFixed(2)}
                    </dd>
                  </div>
                ),
            )}
          </dl>
          <small>
            Scores come from your learning history. No AI call is needed to
            choose this card.
          </small>
        </div>
      )}
      <div className="card-number" aria-hidden="true">
        {String(position + 1).padStart(2, "0")}
      </div>
      <div className="mobile-swipe">
        <button
          aria-label="Previous card"
          onClick={previous}
          disabled={position === 0}
        >
          <ChevronUp size={16} />
        </button>
        <span>Swipe to keep learning</span>
        <button aria-label="Next card" onClick={next}>
          <ArrowDown size={16} />
        </button>
      </div>
    </article>
  );
}
