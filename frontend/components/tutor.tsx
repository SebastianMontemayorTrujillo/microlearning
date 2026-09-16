"use client";
import { useEffect, useRef, useState } from "react";
import {
  ArrowUp,
  LoaderCircle,
  MessageCircle,
  Sparkles,
  X,
} from "lucide-react";
import { errorMessage, percent, post } from "@/lib/api";
import type { Card, TutorReply } from "@/types";

type Message = { role: "user" | "assistant"; content: string; mode?: string };
export function Tutor({
  card,
  initialPrompt,
  aiAvailable,
  close,
}: {
  card: Card;
  initialPrompt?: string;
  aiAvailable: boolean;
  close: () => void;
}) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [failed, setFailed] = useState("");
  const started = useRef(false);
  const history = useRef<Message[]>([]);
  const bottom = useRef<HTMLDivElement>(null);
  const panel = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const send = async (text: string) => {
    if (!text.trim() || busy) return;
    const previous = history.current;
    const next: Message[] = [...previous, { role: "user", content: text }];
    setMessages(next);
    setInput("");
    setBusy(true);
    setError("");
    setFailed("");
    try {
      const reply = await post<TutorReply>("/tutor", {
        card_id: card.id,
        message: text,
        history: previous
          .slice(-6)
          .map(({ role, content }) => ({ role, content })),
      });
      history.current = [
        ...next,
        {
          role: "assistant",
          content: `${reply.answer}\n\n${reply.follow_up}`,
          mode: reply.mode,
        },
      ];
      setMessages(history.current);
    } catch (e) {
      setError(errorMessage(e));
      setFailed(text);
    } finally {
      setBusy(false);
      inputRef.current?.focus();
    }
  };
  useEffect(() => {
    if (initialPrompt && !started.current) {
      started.current = true;
      void send(initialPrompt);
    }
  }, []); // eslint-disable-line react-hooks/exhaustive-deps
  useEffect(() => {
    bottom.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, busy]);
  useEffect(() => {
    const previous = document.activeElement as HTMLElement | null;
    inputRef.current?.focus();
    const key = (e: KeyboardEvent) => {
      if (e.key === "Escape") close();
      if (e.key === "Tab") {
        const focusable = panel.current?.querySelectorAll<HTMLElement>(
          "button:not(:disabled), input:not(:disabled)",
        );
        if (!focusable?.length) return;
        const first = focusable[0];
        const last = focusable[focusable.length - 1];
        if (e.shiftKey && document.activeElement === first) {
          e.preventDefault();
          last.focus();
        }
        if (!e.shiftKey && document.activeElement === last) {
          e.preventDefault();
          first.focus();
        }
      }
    };
    document.addEventListener("keydown", key);
    return () => {
      document.removeEventListener("keydown", key);
      previous?.focus();
    };
  }, [close]);
  return (
    <div
      className="modal-backdrop"
      onMouseDown={(e) => {
        if (e.target === e.currentTarget) close();
      }}
    >
      <div
        className="tutor-panel"
        ref={panel}
        role="dialog"
        aria-modal="true"
        aria-label="Personal learning tutor"
      >
        <div className="tutor-heading">
          <span className="tutor-avatar">
            <Sparkles size={21} />
          </span>
          <div>
            <h2>A little more clarity</h2>
            <p>
              {aiAvailable
                ? "Your contextual AI tutor"
                : "Your local study guide"}
            </p>
          </div>
          <button
            className="icon-button"
            aria-label="Close tutor"
            onClick={close}
          >
            <X size={20} />
          </button>
        </div>
        <div className="tutor-context">
          <span>{card.concept_name}</span>
          <small>{percent(card.mastery.effective_mastery)} mastery</small>
        </div>
        <div className="tutor-messages" aria-live="polite">
          {!messages.length && (
            <div className="tutor-welcome">
              <MessageCircle size={32} />
              <h3>Stay curious.</h3>
              <p>
                {aiAvailable
                  ? "Ask a question. We’ll work through this idea together, using what you already know."
                  : "Explore the explanation and examples saved with this concept. Add an API key in .env for open-ended AI conversations."}
              </p>
            </div>
          )}
          {messages.map((message, i) => (
            <div className={`message ${message.role}`} key={i}>
              {message.role === "assistant" && (
                <span className="message-author">
                  {message.mode === "local"
                    ? "LOCAL STUDY GUIDE"
                    : "LILT TUTOR"}
                </span>
              )}
              <p>{message.content}</p>
            </div>
          ))}
          {busy && (
            <div className="tutor-thinking">
              <LoaderCircle className="spin" size={16} />
              Connecting the dots…
            </div>
          )}
          {error && (
            <div className="error-message" role="alert">
              {error}
              <button className="text-button" onClick={() => void send(failed)}>
                Retry
              </button>
            </div>
          )}
          <div ref={bottom} />
        </div>
        <div className="tutor-prompts">
          {[
            "Why?",
            "Give me an example",
            "Explain like I’m 12",
            "Make this harder",
            "Explain this visually",
            "Show the proof",
            "Give me a problem",
          ].map((prompt) => (
            <button
              disabled={busy}
              key={prompt}
              onClick={() => void send(prompt)}
            >
              {prompt}
            </button>
          ))}
        </div>
        <form
          className="tutor-input"
          onSubmit={(e) => {
            e.preventDefault();
            void send(input);
          }}
        >
          <input
            ref={inputRef}
            aria-label="Ask a question"
            placeholder="What would you like to understand?"
            value={input}
            maxLength={1000}
            onChange={(e) => setInput(e.target.value)}
          />
          <button
            type="submit"
            aria-label="Send question"
            disabled={busy || !input.trim()}
          >
            <ArrowUp size={19} />
          </button>
        </form>
        <p className="tutor-footnote">
          {aiAvailable
            ? "Only this concept, prerequisites, and recent mistakes are included."
            : "Local answers use saved material. No API calls are made."}
        </p>
      </div>
    </div>
  );
}
