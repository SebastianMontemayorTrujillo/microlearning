"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { api, errorMessage, post } from "@/lib/api";
import type { Card, EventKind, EventResult } from "@/types";

export type FeedFilter = { subject: string; mode: string; concept: string };

export function useFeed(
  filter: FeedFilter,
  initialCard: Card | null,
  onActivity: () => void,
) {
  const [cards, setCards] = useState<Card[]>([]);
  const [index, setIndex] = useState(0);
  const [offset, setOffset] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const cardsRef = useRef<Card[]>([]);
  const indexRef = useRef(0);
  const abortRef = useRef<AbortController | null>(null);
  const loadingRef = useRef(false);
  const generation = useRef(0);
  const exposures = useRef(
    new Map<
      string,
      {
        elapsed: number;
        activeAt: number;
        flushed: boolean;
        cleanup?: ReturnType<typeof setTimeout>;
      }
    >(),
  );
  const activityRef = useRef(onActivity);
  activityRef.current = onActivity;

  const assign = useCallback((next: Card[]) => {
    cardsRef.current = next;
    setCards(next);
  }, []);
  const fetchNext = useCallback(
    async (base?: Card[]) => {
      if (loadingRef.current && base === undefined) return;
      const version = ++generation.current;
      abortRef.current?.abort();
      const controller = new AbortController();
      abortRef.current = controller;
      loadingRef.current = true;
      setLoading(true);
      setError("");
      const history = base ?? cardsRef.current;
      const params = new URLSearchParams({
        limit: "4",
        exclude: history
          .slice(-40)
          .map((c) => c.id)
          .join(","),
        mode: filter.mode,
      });
      if (filter.subject) params.set("subject_id", filter.subject);
      // A path chooses the first concept, then the main recommender can lead onward.
      if (filter.concept && history.length === 0)
        params.set("concept_id", filter.concept);
      try {
        const data = await api<{ cards: Card[] }>(`/feed?${params}`, {
          signal: controller.signal,
        });
        if (version === generation.current) {
          const combined = [
            ...history.map(
              (card) =>
                cardsRef.current.find(
                  (current) => current.presentation_id === card.presentation_id,
                ) || card,
            ),
            ...data.cards,
          ];
          if (combined.length > 60 && indexRef.current >= 40) {
            // Bound mounted charts and DOM nodes during long sessions, retaining
            // at least ten previous interactions for backwards navigation.
            for (const card of combined.slice(0, 30))
              if (card.presentation_id)
                exposures.current.delete(card.presentation_id);
            indexRef.current -= 30;
            setIndex(indexRef.current);
            setOffset((value) => value + 30);
            assign(combined.slice(30));
          } else assign(combined);
        }
      } catch (e) {
        if (
          !(e instanceof DOMException && e.name === "AbortError") &&
          version === generation.current
        )
          setError(errorMessage(e));
      } finally {
        if (version === generation.current) {
          loadingRef.current = false;
          setLoading(false);
        }
      }
    },
    [assign, filter.concept, filter.mode, filter.subject],
  );

  useEffect(() => {
    indexRef.current = 0;
    setIndex(0);
    setOffset(0);
    const first = initialCard ? [initialCard] : [];
    assign(first);
    void fetchNext(first);
    return () => {
      ++generation.current;
      abortRef.current?.abort();
      loadingRef.current = false;
    };
  }, [assign, fetchNext, initialCard]);

  const move = useCallback((next: number) => {
    indexRef.current = next;
    setIndex(next);
  }, []);
  useEffect(() => {
    if (cards.length && index >= cards.length - 2 && !loading && !error)
      void fetchNext();
  }, [cards.length, index, loading, error, fetchNext]);

  const patchCard = useCallback(
    (id: string, patch: Partial<Card>) => {
      assign(
        cardsRef.current.map((c) => (c.id === id ? { ...c, ...patch } : c)),
      );
    },
    [assign],
  );

  const event = useCallback(
    async (
      card: Card,
      kind: EventKind,
      extra: { answer?: number; seconds?: number } = {},
      adapt = false,
    ) => {
      if (!card.presentation_id)
        throw new Error("This card is still opening. Please try again.");
      const result = await post<EventResult>("/interactions", {
        presentation_id: card.presentation_id,
        kind,
        ...extra,
      });
      const updated = cardsRef.current.map((c) =>
        c.concept_id === card.concept_id
          ? { ...c, mastery: result.mastery }
          : c,
      );
      assign(updated);
      activityRef.current();
      if (adapt) {
        // Re-rank only unshown cards after new evidence; preserve the current card and scroll history.
        const past = updated.slice(0, indexRef.current + 1);
        assign(past);
        void fetchNext(past);
      }
      return result;
    },
    [assign, fetchNext],
  );

  const current = cards[index];
  useEffect(() => {
    if (!current?.presentation_id) return;
    const presentation = current.presentation_id;
    let exposure = exposures.current.get(presentation);
    if (!exposure) {
      exposure = { elapsed: 0, activeAt: 0, flushed: false };
      exposures.current.set(presentation, exposure);
    }
    const clock = exposure;
    if (clock.cleanup) clearTimeout(clock.cleanup);
    const wasSeen = clock.flushed;
    void event(current, wasSeen ? "revisited" : "shown").catch((e) =>
      setError(errorMessage(e)),
    );
    clock.activeAt =
      document.visibilityState === "visible" ? performance.now() : 0;
    const pause = () => {
      if (clock.activeAt) {
        clock.elapsed += performance.now() - clock.activeAt;
        clock.activeAt = 0;
      }
    };
    const visibility = () => {
      if (document.visibilityState === "hidden") pause();
      else clock.activeAt = performance.now();
    };
    const flush = () => {
      if (clock.flushed) return;
      clock.flushed = true;
      pause();
      const seconds = Math.min(600, clock.elapsed / 1000);
      const body = JSON.stringify({
        presentation_id: presentation,
        kind: "dwell",
        seconds,
      });
      // keepalive survives a route change or page close; server deduplication makes retries safe.
      void api<EventResult>("/interactions", {
        method: "POST",
        body,
        keepalive: true,
      })
        .then(() => activityRef.current())
        .catch((e) => setError(errorMessage(e)));
      if (seconds < 3)
        void event(current, "skipped").catch((e) => setError(errorMessage(e)));
    };
    document.addEventListener("visibilitychange", visibility);
    window.addEventListener("pagehide", flush);
    return () => {
      document.removeEventListener("visibilitychange", visibility);
      window.removeEventListener("pagehide", flush);
      pause();
      // React's development effect replay can immediately remount the same exposure.
      // Defer finalization one task so that replay cannot persist a zero-second dwell.
      clock.cleanup = setTimeout(flush, 0);
    };
    // An exposure has one timer, independent of mastery and bookmark updates to the card.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [current?.presentation_id]);

  return {
    cards,
    current,
    index,
    offset,
    move,
    loading,
    error,
    retry: () => fetchNext(),
    event,
    patchCard,
  };
}
