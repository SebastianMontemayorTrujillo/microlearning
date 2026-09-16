"use client";
import {
  useCallback,
  useEffect,
  useLayoutEffect,
  useRef,
  useState,
} from "react";
import {
  ArrowDown,
  ArrowUp,
  ChevronDown,
  CircleHelp,
  SlidersHorizontal,
  Sparkles,
} from "lucide-react";
import { useFeed, type FeedFilter } from "@/hooks/use-feed";
import type { Card, Settings } from "@/types";
import { LearningCard } from "./learning-card";
import { EmptyState, ErrorState, Loading } from "./ui";
import { Tutor } from "./tutor";
import { errorMessage } from "@/lib/api";

export function Feed({
  settings,
  initialCard,
  focus,
  onActivity,
  changeTopics,
}: {
  settings: Settings;
  initialCard: Card | null;
  focus: string;
  onActivity: () => void;
  changeTopics: () => void;
}) {
  const [filter, setFilter] = useState<FeedFilter>({
    subject: "",
    mode: "for-you",
    concept: focus,
  });
  const feed = useFeed(filter, initialCard, onActivity);
  const scroller = useRef<HTMLDivElement>(null);
  const [tutorState, setTutorState] = useState<{
    card: Card;
    prompt?: string;
  } | null>(null);
  const [error, setError] = useState("");
  const closeTutor = useCallback(() => setTutorState(null), []);
  useLayoutEffect(() => {
    const el = scroller.current;
    if (el && feed.offset) el.scrollTop = feed.index * el.clientHeight;
    // Only adjust scroll when old history is pruned, never on ordinary navigation.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [feed.offset]);
  const navigate = useCallback(
    (delta: number) => {
      const el = scroller.current;
      if (!el) return;
      const next = Math.min(
        feed.cards.length - 1,
        Math.max(0, feed.index + delta),
      );
      el.scrollTo({
        top: next * el.clientHeight,
        behavior: window.matchMedia("(prefers-reduced-motion: reduce)").matches
          ? "instant"
          : "smooth",
      });
    },
    [feed.cards.length, feed.index],
  );
  useEffect(() => {
    const key = (e: KeyboardEvent) => {
      if (
        tutorState ||
        e.target instanceof HTMLInputElement ||
        e.target instanceof HTMLTextAreaElement ||
        e.target instanceof HTMLSelectElement ||
        (e.target instanceof Element && e.target.closest("button"))
      )
        return;
      if (e.key === "ArrowDown" || e.key === "PageDown") {
        e.preventDefault();
        navigate(1);
      }
      if (e.key === "ArrowUp" || e.key === "PageUp") {
        e.preventDefault();
        navigate(-1);
      }
    };
    document.addEventListener("keydown", key);
    return () => document.removeEventListener("keydown", key);
  }, [navigate, tutorState]);
  useEffect(() => {
    scroller.current?.scrollTo({ top: 0 });
  }, [filter]);
  const openTutor = (card: Card, prompt?: string) => {
    setTutorState({ card, prompt });
    void feed
      .event(card, prompt ? "deeper" : "tutor", {}, true)
      .catch((e) => setError(errorMessage(e)));
  };
  return (
    <section className="feed-section">
      <header className="page-heading feed-heading">
        <div>
          <span className="eyebrow">A LITTLE WISER, EVERY DAY</span>
          <h1>
            For you<span className="heading-dot">.</span>
          </h1>
          <p>Small lessons. Lasting understanding.</p>
        </div>
        <span className="personal-badge">
          <Sparkles size={14} />
          Made for your mind
        </span>
      </header>
      <div className="feed-tabs">
        <div role="tablist" aria-label="Feed mode">
          <button
            role="tab"
            aria-selected={filter.mode === "for-you"}
            className={filter.mode === "for-you" ? "active" : ""}
            onClick={() =>
              setFilter({ ...filter, mode: "for-you", concept: "" })
            }
          >
            Discover
          </button>
          <button
            role="tab"
            aria-selected={filter.mode === "reviews"}
            className={filter.mode === "reviews" ? "active" : ""}
            onClick={() =>
              setFilter({ ...filter, mode: "reviews", concept: "" })
            }
          >
            Practice & review
          </button>
        </div>
        <label className="subject-filter">
          <SlidersHorizontal size={14} />
          <select
            aria-label="Filter by subject"
            value={filter.subject}
            onChange={(e) =>
              setFilter({ ...filter, subject: e.target.value, concept: "" })
            }
          >
            <option value="">All my topics</option>
            {settings.subjects
              .filter((s) => s.selected)
              .map((s) => (
                <option key={s.id} value={s.id}>
                  {s.name}
                </option>
              ))}
          </select>
          <ChevronDown size={12} />
        </label>
      </div>
      {error && (
        <div className="inline-error" role="alert">
          {error}
          <button onClick={() => setError("")}>Dismiss</button>
        </div>
      )}
      <div className="feed-frame">
        <div
          className="feed-scroller"
          ref={scroller}
          aria-label="Vertical learning feed"
          onScroll={() => {
            const el = scroller.current;
            if (el)
              feed.move(
                Math.max(
                  0,
                  Math.min(
                    feed.cards.length - 1,
                    Math.round(el.scrollTop / el.clientHeight),
                  ),
                ),
              );
          }}
        >
          {feed.cards.map((card, i) => (
            <div className="feed-slide" key={card.presentation_id}>
              <LearningCard
                card={card}
                position={i}
                active={i === feed.index}
                event={feed.event}
                patch={feed.patchCard}
                tutor={openTutor}
                next={() => navigate(1)}
                previous={() => navigate(-1)}
              />
            </div>
          ))}
          {!feed.cards.length &&
            (feed.loading ? (
              <Loading />
            ) : feed.error ? (
              <ErrorState
                message={feed.error}
                retry={() => void feed.retry()}
              />
            ) : (
              <EmptyState
                title={
                  filter.mode === "reviews"
                    ? "A fresh start for your memory"
                    : "Room for your next idea"
                }
                description={
                  filter.mode === "reviews"
                    ? "Read a few lessons first. Then come back to practice recalling them. Scheduled reviews will join your feed when they are due."
                    : settings.ai_available
                      ? "Your selected topics are being prepared in the background. Refresh shortly, or explore the included Computer Science and Mathematics lessons."
                      : "Choose Computer Science or Mathematics for the included curriculum, or import your own notes from Learn."
                }
                action={
                  filter.mode === "reviews"
                    ? "Discover a lesson"
                    : "Choose topics"
                }
                onAction={
                  filter.mode === "reviews"
                    ? () => setFilter({ ...filter, mode: "for-you" })
                    : changeTopics
                }
              />
            ))}
        </div>
        <div className="feed-navigation">
          <button
            aria-label="Previous card"
            title="Previous card (↑)"
            disabled={feed.index === 0}
            onClick={() => navigate(-1)}
          >
            <ArrowUp size={19} />
          </button>
          <span>{String(feed.index + 1).padStart(2, "0")}</span>
          <button
            aria-label="Next card"
            title="Next card (↓)"
            disabled={feed.index >= feed.cards.length - 1}
            onClick={() => navigate(1)}
          >
            <ArrowDown size={19} />
          </button>
        </div>
      </div>
      <div className="feed-bottom-note">
        <span>
          <CircleHelp size={13} />
          Scroll, swipe, or use ↑ ↓ to explore
        </span>
        <span>
          {feed.loading && feed.cards.length
            ? "Preparing what’s next…"
            : "A feed that learns with you"}
        </span>
      </div>
      {feed.error && !!feed.cards.length && (
        <div className="inline-error" role="alert">
          {feed.error}
          <button onClick={() => void feed.retry()}>Retry</button>
        </div>
      )}
      {tutorState && (
        <Tutor
          key={tutorState.card.presentation_id}
          card={tutorState.card}
          initialPrompt={tutorState.prompt}
          aiAvailable={settings.ai_available && settings.ai_enabled}
          close={closeTutor}
        />
      )}
    </section>
  );
}
