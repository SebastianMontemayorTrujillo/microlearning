"use client";
import { useState } from "react";
import {
  ArrowRight,
  Check,
  Code2,
  Globe2,
  Plus,
  Sparkles,
  X,
} from "lucide-react";
import { errorMessage, post } from "@/lib/api";
import type { Settings } from "@/types";
import { Logo } from "./ui";

const subjects = [
  "Computer Science",
  "Mathematics",
  "Physics",
  "Economics",
  "History",
  "Languages",
  "Philosophy",
  "Biology",
];
export function Onboarding({
  settings,
  complete,
  close,
}: {
  settings: Settings;
  complete: (settings: Settings) => void;
  close?: () => void;
}) {
  const [selected, setSelected] = useState(
    settings.subjects.filter((s) => s.selected).map((s) => s.name),
  );
  const [custom, setCustom] = useState("");
  const [level, setLevel] = useState(settings.level);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const choices = [...new Set([...subjects, ...selected])];
  const toggle = (subject: string) =>
    setSelected((old) =>
      old.includes(subject)
        ? old.filter((s) => s !== subject)
        : [...old, subject],
    );
  const add = () => {
    const value = custom.trim();
    if (
      value.length >= 2 &&
      !selected.some((s) => s.toLowerCase() === value.toLowerCase())
    )
      setSelected([...selected, value]);
    setCustom("");
  };
  const submit = async () => {
    setBusy(true);
    setError("");
    try {
      complete(
        await post<Settings>("/onboarding", { subjects: selected, level }),
      );
    } catch (e) {
      setError(errorMessage(e));
    } finally {
      setBusy(false);
    }
  };
  return (
    <div className="onboarding-screen">
      <div className="onboarding-art" aria-hidden="true">
        <div className="orbit orbit-one" />
        <div className="orbit orbit-two" />
        <div className="orbit orbit-three" />
        <span className="orbit-node node-one">
          <Code2 />
        </span>
        <span className="orbit-node node-two">∑</span>
        <span className="orbit-node node-three">
          <Globe2 />
        </span>
        <div className="orbit-center">
          <Sparkles size={50} />
        </div>
        <div className="onboarding-manifesto">
          <span className="eyebrow">A SMALL IDEA. A BIGGER WORLD.</span>
          <h2>
            Follow your
            <br />
            <em>curiosity.</em>
          </h2>
          <p>
            A little learning, every day.
            <br />A lot of possibilities.
          </p>
        </div>
      </div>
      <div className="onboarding-form">
        <div className="onboarding-heading">
          <Logo />
          {close && (
            <button
              className="icon-button"
              aria-label="Close topic settings"
              onClick={close}
            >
              <X />
            </button>
          )}
          <span className="pill">YOUR PERSONAL LEARNING SPACE</span>
        </div>
        <div className="onboarding-content">
          <span className="eyebrow">LET’S MAKE THIS YOURS</span>
          <h1>
            What sparks
            <br />
            your curiosity?
          </h1>
          <p>
            Pick what you want to learn. We’ll connect the dots, one small
            lesson at a time.
          </p>
          <div className="subject-options">
            {choices.map((subject) => (
              <button
                key={subject}
                className={selected.includes(subject) ? "selected" : ""}
                aria-pressed={selected.includes(subject)}
                onClick={() => toggle(subject)}
              >
                {subject}
                {selected.includes(subject) ? (
                  <Check size={15} />
                ) : (
                  <Plus size={15} />
                )}
              </button>
            ))}
          </div>
          <form
            className="custom-subject"
            onSubmit={(e) => {
              e.preventDefault();
              add();
            }}
          >
            <input
              aria-label="Custom subject"
              placeholder="Something else? Add any subject"
              maxLength={100}
              value={custom}
              onChange={(e) => setCustom(e.target.value)}
            />
            <button
              type="submit"
              className="icon-button"
              aria-label="Add custom subject"
              disabled={custom.trim().length < 2}
            >
              <Plus size={19} />
            </button>
          </form>
          <label className="field-label">Where are you starting?</label>
          <div className="level-options">
            {(["beginner", "intermediate", "advanced"] as const).map(
              (value) => (
                <button
                  key={value}
                  className={level === value ? "selected" : ""}
                  aria-pressed={level === value}
                  onClick={() => setLevel(value)}
                >
                  {value}
                </button>
              ),
            )}
          </div>
          <p className="setup-note">
            {settings.ai_available
              ? "AI will build a knowledge map for your subjects in the background."
              : "Computer Science & Mathematics include 100 ready-to-learn cards. Other subjects need an API key, or you can import your own notes."}
          </p>
          {error && (
            <p role="alert" className="error-message">
              {error}
            </p>
          )}
          <button
            className="primary-button onboarding-submit"
            disabled={!selected.length || busy}
            onClick={() => void submit()}
          >
            {busy
              ? "Making room for new ideas…"
              : close
                ? "Update my interests"
                : "Start my learning journey"}
            <ArrowRight size={18} />
          </button>
          <span className="onboarding-footnote">
            Just for you. No followers, no noise.
          </span>
        </div>
      </div>
    </div>
  );
}
