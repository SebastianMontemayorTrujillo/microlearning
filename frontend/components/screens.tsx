"use client";

import { useRef, useState } from "react";
import {
  ArrowRight,
  ArrowUpRight,
  BookOpen,
  Bookmark,
  Check,
  ChevronDown,
  Clock3,
  FileText,
  GitBranch,
  Layers3,
  LockKeyhole,
  Moon,
  Plus,
  RefreshCw,
  Sparkles,
  Sun,
  Upload,
  X,
} from "lucide-react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { useResource } from "@/hooks/use-resource";
import { api, errorMessage, percent, post } from "@/lib/api";
import type {
  Card,
  Concept,
  ImportRecord,
  Knowledge,
  Progress,
  Settings,
  Usage,
} from "@/types";
import { EmptyState, ErrorState, Loading } from "./ui";

type LearnProps = {
  learn: (id: string) => void;
  revision: number;
  changed: () => void;
  settings: Settings;
};
export function LearnScreen({
  learn,
  revision,
  changed,
  settings,
}: LearnProps) {
  const graph = useResource<Knowledge>("/knowledge", revision);
  const [tab, setTab] = useState("paths");
  const [expanded, setExpanded] = useState<string | null>(null);
  const [importing, setImporting] = useState(false);
  if (!graph.data)
    return graph.error ? (
      <ErrorState message={graph.error} retry={graph.reload} />
    ) : (
      <Loading />
    );
  const data = graph.data;
  const selected = new Set(
    data.subjects.filter((s) => s.selected).map((s) => s.id),
  );
  return (
    <section className="content-page">
      <header className="page-heading">
        <div>
          <span className="eyebrow">CONNECT THE DOTS</span>
          <h1>
            A path to understanding<span className="heading-dot">.</span>
          </h1>
          <p>Follow a little structure. Leave room for curiosity.</p>
        </div>
        <button
          className="secondary-button"
          onClick={() => setImporting(!importing)}
        >
          <Plus size={17} />
          Teach me this
        </button>
      </header>
      {importing && (
        <ImportPanel
          ai={settings.ai_available && settings.ai_enabled}
          complete={() => {
            changed();
            graph.reload();
          }}
          close={() => setImporting(false)}
        />
      )}
      <div className="page-tabs">
        <button
          className={tab === "paths" ? "active" : ""}
          onClick={() => setTab("paths")}
        >
          <Layers3 size={16} />
          Learning paths
        </button>
        <button
          className={tab === "map" ? "active" : ""}
          onClick={() => setTab("map")}
        >
          <GitBranch size={16} />
          Knowledge map
        </button>
      </div>
      {tab === "paths" ? (
        <div className="path-grid">
          {data.paths
            .filter((p) => selected.has(p.subject_id))
            .map((path, index) => {
              const concepts = path.concept_ids
                .map((id) => data.concepts.find((c) => c.id === id))
                .filter((c): c is Concept => !!c);
              const next = concepts.find((c) => c.id === path.next_concept_id);
              const subject = data.subjects.find(
                (s) => s.id === path.subject_id,
              );
              return (
                <article
                  className={`path-card ${subject?.color || "mint"}`}
                  key={path.id}
                >
                  <div className="path-art" aria-hidden="true">
                    <div className="path-art-grid" />
                    <span>
                      {index % 3 === 0 ? "{ }" : index % 3 === 1 ? "↗" : "P(A)"}
                    </span>
                    <div className="path-art-orbit" />
                  </div>
                  <div className="path-card-body">
                    <span className="eyebrow">
                      {subject?.name} · {concepts.length} CONCEPTS
                    </span>
                    <h2>{path.title}</h2>
                    <p>{path.description}</p>
                    <div className="path-progress-label">
                      <span>Your understanding</span>
                      <b>{percent(path.progress)}</b>
                    </div>
                    <div className="progress-track">
                      <span style={{ width: percent(path.progress) }} />
                    </div>
                    <div className="path-card-actions">
                      <button
                        className="text-button"
                        onClick={() => next && learn(next.id)}
                      >
                        {path.progress > 0
                          ? "Continue learning"
                          : "Begin this path"}
                        <ArrowRight size={16} />
                      </button>
                      <button
                        aria-label={`Show concepts in ${path.title}`}
                        aria-expanded={expanded === path.id}
                        className="icon-button"
                        onClick={() =>
                          setExpanded(expanded === path.id ? null : path.id)
                        }
                      >
                        <ChevronDown size={18} />
                      </button>
                    </div>
                    {expanded === path.id && (
                      <ol className="path-steps">
                        {concepts.map((c, i) => (
                          <li key={c.id}>
                            <span
                              className={`path-step-node ${c.unlocked ? "unlocked" : ""}`}
                            >
                              {c.mastered ? (
                                <Check size={12} />
                              ) : c.unlocked ? (
                                i + 1
                              ) : (
                                <LockKeyhole size={11} />
                              )}
                            </span>
                            <button onClick={() => learn(c.id)}>
                              <span>{c.name}</span>
                              <small>
                                {c.unlocked
                                  ? `${percent(c.mastery.effective_mastery)} mastery`
                                  : "Start with prerequisites"}
                              </small>
                            </button>
                            <ArrowUpRight size={14} />
                          </li>
                        ))}
                      </ol>
                    )}
                  </div>
                </article>
              );
            })}
          {!data.paths.some((p) => selected.has(p.subject_id)) && (
            <EmptyState
              title="Your map starts here"
              description="Custom topics will appear here after AI generation. You can also turn your notes into a learning path."
              action="Import notes"
              onAction={() => setImporting(true)}
            />
          )}
        </div>
      ) : (
        <div className="knowledge-map">
          <p className="map-explainer">
            Each concept builds on the ones before it. A lock means a
            prerequisite needs practice; selecting it starts with that
            foundation.
          </p>
          {data.subjects
            .filter((s) => s.selected)
            .map((subject) => (
              <div className="map-subject" key={subject.id}>
                <h2>
                  <span className={`subject-dot ${subject.color}`} />
                  {subject.name}
                </h2>
                {data.topics
                  .filter((t) => t.subject_id === subject.id)
                  .map((topic) => (
                    <div className="map-topic" key={topic.id}>
                      <h3>{topic.name}</h3>
                      <div className="concept-grid">
                        {data.concepts
                          .filter((c) => c.topic_id === topic.id)
                          .map((c) => (
                            <button
                              key={c.id}
                              className={`concept-node ${c.unlocked ? "unlocked" : "locked"}`}
                              onClick={() => learn(c.id)}
                            >
                              <div>
                                <span>{c.name}</span>
                                {c.unlocked ? (
                                  <ArrowUpRight size={16} />
                                ) : (
                                  <LockKeyhole size={14} />
                                )}
                              </div>
                              <div className="progress-track">
                                <span
                                  style={{
                                    width: percent(
                                      c.mastery.times_seen
                                        ? c.mastery.effective_mastery
                                        : 0,
                                    ),
                                  }}
                                />
                              </div>
                              <small>
                                {c.mastery.times_seen
                                  ? `${percent(c.mastery.effective_mastery)} understanding`
                                  : "Not yet explored"}
                              </small>
                              {c.prerequisites.length > 0 && (
                                <p>
                                  Builds on:{" "}
                                  {c.prerequisites
                                    .map(
                                      (id) =>
                                        data.concepts.find((p) => p.id === id)
                                          ?.name,
                                    )
                                    .join(" · ")}
                                </p>
                              )}
                            </button>
                          ))}
                      </div>
                    </div>
                  ))}
              </div>
            ))}
        </div>
      )}
    </section>
  );
}

function ImportPanel({
  ai,
  complete,
  close,
}: {
  ai: boolean;
  complete: () => void;
  close: () => void;
}) {
  const [title, setTitle] = useState("");
  const [text, setText] = useState("");
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const input = useRef<HTMLInputElement>(null);
  const docs = useResource<{ documents: ImportRecord[] }>("/imports");
  const read = async (file: File) => {
    if (!/\.(md|markdown|txt)$/i.test(file.name)) {
      setError(
        "Choose a .txt, .md, or .markdown file. PDF import is not part of this MVP.",
      );
      return;
    }
    if (file.size > 160000) {
      setError("Choose a smaller excerpt, up to 40,000 characters.");
      return;
    }
    const content = await file.text();
    if (content.length > 40000) {
      setError("Choose a smaller excerpt, up to 40,000 characters.");
      return;
    }
    setText(content);
    setTitle(file.name.replace(/\.[^.]+$/, ""));
    setError("");
  };
  const submit = async () => {
    setBusy(true);
    setError("");
    setMessage("");
    try {
      const result = await post<{ status: string; duplicate: boolean }>(
        "/imports",
        { title, text },
      );
      setMessage(
        result.duplicate
          ? "These notes are already in your library."
          : result.status === "local_excerpts"
            ? "Your excerpts are ready in Learning paths and your feed."
            : "Notes saved. AI will create your map and lessons in the background; this can take a few minutes.",
      );
      docs.reload();
      complete();
    } catch (e) {
      setError(errorMessage(e));
    } finally {
      setBusy(false);
    }
  };
  return (
    <div className="import-panel">
      <div className="section-heading">
        <div>
          <span className="eyebrow">YOUR NOTES, NEW CONNECTIONS</span>
          <h2>Teach me this</h2>
        </div>
        <button
          className="icon-button"
          aria-label="Close import"
          onClick={close}
        >
          <X size={20} />
        </button>
      </div>
      <p>
        {ai
          ? "Turn text or Markdown into concepts, lessons, and questions. Your selected text will be sent to OpenAI for processing."
          : "Turn text or Markdown into excerpt cards you can read and recall. AI analysis and generated quizzes become available with an API key."}
      </p>
      <input
        ref={input}
        type="file"
        accept=".txt,.md,.markdown"
        hidden
        onChange={(e) => {
          const file = e.target.files?.[0];
          if (file) void read(file).catch((e) => setError(errorMessage(e)));
        }}
      />
      <button className="upload-area" onClick={() => input.current?.click()}>
        <Upload size={23} />
        <b>Choose a text or Markdown file</b>
        <span>Or paste an excerpt below · up to 40,000 characters</span>
      </button>
      <label className="field-label" htmlFor="import-title">
        Give your material a title
      </label>
      <input
        id="import-title"
        className="text-input"
        placeholder="e.g. My notes on distributed systems"
        value={title}
        maxLength={150}
        onChange={(e) => setTitle(e.target.value)}
      />
      <textarea
        aria-label="Learning material"
        placeholder="Paste something you want to understand…"
        value={text}
        maxLength={40000}
        onChange={(e) => setText(e.target.value)}
      />
      <div className="import-footer">
        <small>{text.length.toLocaleString()} / 40,000 characters</small>
        <button
          className="primary-button"
          disabled={busy || title.trim().length < 2 || text.trim().length < 50}
          onClick={() => void submit()}
        >
          <Sparkles size={16} />
          {busy ? "Saving your material…" : "Create my learning material"}
        </button>
      </div>
      {error && (
        <p className="error-message" role="alert">
          {error}
        </p>
      )}
      {message && (
        <p className="success-message" role="status">
          {message}
        </p>
      )}
      {!!docs.data?.documents.length && (
        <div className="document-list">
          <h3>Your imports</h3>
          {docs.data.documents.map((doc) => (
            <div key={doc.id}>
              <FileText size={17} />
              <span>{doc.title}</span>
              <small>{doc.status.replaceAll("_", " ")}</small>
            </div>
          ))}
          <button
            className="text-button"
            onClick={() => {
              docs.reload();
              complete();
            }}
          >
            <RefreshCw size={14} />
            Refresh processing status
          </button>
        </div>
      )}
    </div>
  );
}

export function SavedScreen({ open }: { open: (card: Card) => void }) {
  const resource = useResource<{ cards: Card[] }>("/saved");
  const [query, setQuery] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState<string | null>(null);
  const launch = async (card: Card) => {
    setBusy(card.id);
    setError("");
    try {
      open(await post<Card>(`/cards/${card.id}/open`, {}));
    } catch (e) {
      setError(errorMessage(e));
    } finally {
      setBusy(null);
    }
  };
  const remove = async (card: Card) => {
    try {
      await api(`/cards/${card.id}/saved`, {
        method: "PUT",
        body: JSON.stringify({ saved: false }),
      });
      resource.reload();
    } catch (e) {
      setError(errorMessage(e));
    }
  };
  return (
    <section className="content-page">
      <header className="page-heading">
        <div>
          <span className="eyebrow">KEEP THE GOOD IDEAS CLOSE</span>
          <h1>
            Your little library<span className="heading-dot">.</span>
          </h1>
          <p>A place for the ideas you want to return to.</p>
        </div>
        <Bookmark className="page-heading-icon" size={30} />
      </header>
      {resource.loading && !resource.data ? (
        <Loading />
      ) : resource.error ? (
        <ErrorState message={resource.error} retry={resource.reload} />
      ) : !resource.data?.cards.length ? (
        <EmptyState
          title="Some ideas deserve a second look"
          description="Tap the bookmark on any learning card. It will be waiting here whenever you need it."
        />
      ) : (
        <>
          <input
            className="text-input saved-search"
            aria-label="Search saved lessons"
            placeholder="Find an idea, concept, or subject…"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
          />
          <div className="saved-grid">
            {resource.data.cards
              .filter((c) =>
                `${c.title} ${c.subject} ${c.topic}`
                  .toLowerCase()
                  .includes(query.toLowerCase()),
              )
              .map((card) => (
                <article className={`saved-card ${card.color}`} key={card.id}>
                  <div className="saved-card-top">
                    <span className="eyebrow">{card.topic}</span>
                    <button
                      className="icon-button selected"
                      aria-label={`Unsave ${card.title}`}
                      onClick={() => void remove(card)}
                    >
                      <Bookmark size={18} fill="currentColor" />
                    </button>
                  </div>
                  <span className="saved-card-symbol" aria-hidden="true">
                    {card.subject_id === "cs" ? "{ }" : "↗"}
                  </span>
                  <h2>{card.title}</h2>
                  <p>{card.hook}</p>
                  <div>
                    <span>
                      <Clock3 size={13} />
                      {card.estimated_seconds} sec
                    </span>
                    <button
                      className="text-button"
                      disabled={busy === card.id}
                      onClick={() => void launch(card)}
                    >
                      Revisit
                      <ArrowUpRight size={16} />
                    </button>
                  </div>
                </article>
              ))}
          </div>
        </>
      )}
      {error && (
        <p className="error-message" role="alert">
          {error}
        </p>
      )}
    </section>
  );
}

export function ProgressScreen({
  revision,
  learn,
}: {
  revision: number;
  learn: (id: string) => void;
}) {
  const resource = useResource<Progress>("/progress", revision);
  const graph = useResource<Knowledge>("/knowledge", revision);
  if (!resource.data || !graph.data)
    return resource.error || graph.error ? (
      <ErrorState
        message={resource.error || graph.error}
        retry={() => {
          resource.reload();
          graph.reload();
        }}
      />
    ) : (
      <Loading />
    );
  const data = resource.data;
  const concepts = graph.data.concepts;
  const conceptList = (ids: string[], empty: string) =>
    ids.length ? (
      <div className="progress-concepts">
        {ids.map((id) => {
          const c = concepts.find((c) => c.id === id);
          return (
            c && (
              <button key={id} onClick={() => learn(id)}>
                <span>
                  <b>{c.name}</b>
                  <small>
                    {c.mastery.next_review
                      ? `Next review ${new Date(c.mastery.next_review).toLocaleDateString()}`
                      : "Continue exploring"}
                  </small>
                </span>
                <span className="concept-percent">
                  {percent(c.mastery.effective_mastery)}
                  <ArrowUpRight size={14} />
                </span>
              </button>
            )
          );
        })}
      </div>
    ) : (
      <p className="muted small-empty">{empty}</p>
    );
  return (
    <section className="content-page">
      <header className="page-heading">
        <div>
          <span className="eyebrow">UNDERSTANDING THAT STAYS WITH YOU</span>
          <h1>
            See how far you’ve come<span className="heading-dot">.</span>
          </h1>
          <p>Real learning is a collection of small connections.</p>
        </div>
        <span className="pill">
          <Sparkles size={14} />
          {data.streak} day{data.streak === 1 ? "" : "s"} of learning
        </span>
      </header>
      <div className="stat-grid">
        {[
          [data.encountered, "Concepts explored", "Across your knowledge map"],
          [data.mastered, "Concepts mastered", "Proven by spaced retrieval"],
          [data.reviews_due, "Ready to revisit", "A timely memory refresh"],
          [
            `${Math.round(data.total_minutes)}m`,
            "Time well spent",
            "Visible learning time",
          ],
        ].map(([value, label, note]) => (
          <div className="stat-card" key={label}>
            <span>{label}</span>
            <b>{value}</b>
            <small>{note}</small>
          </div>
        ))}
      </div>
      <div className="progress-grid">
        <div className="panel subject-progress">
          <div className="section-heading">
            <h2>Your growing understanding</h2>
            <BookOpen size={19} />
          </div>
          {data.subjects
            .filter((s) => s.selected)
            .map((subject) => (
              <div className="subject-progress-row" key={subject.id}>
                <div>
                  <span>
                    <i className={`subject-dot ${subject.color}`} />
                    {subject.name}
                  </span>
                  <b>{percent(subject.mastery)}</b>
                </div>
                <div className={`progress-track ${subject.color}`}>
                  <span style={{ width: percent(subject.mastery) }} />
                </div>
                <small>{subject.concept_count} concepts in your map</small>
              </div>
            ))}
          <p className="fine-print">
            Mastery combines retrieval, difficulty, and forgetting. Unexplored
            concepts contribute 0%. Mastered means at least 80% estimated
            mastery and three spaced successes.
          </p>
        </div>
        <div className="panel week-panel">
          <div className="section-heading">
            <h2>A little, often</h2>
            <span className="eyebrow">THIS WEEK</span>
          </div>
          <div className="week-chart">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart
                data={data.week}
                margin={{ left: -25, right: 0, top: 15 }}
              >
                <CartesianGrid stroke="var(--line)" vertical={false} />
                <XAxis
                  dataKey="day"
                  tick={{ fill: "var(--muted)", fontSize: 11 }}
                  tickLine={false}
                  axisLine={false}
                />
                <YAxis
                  tick={{ fill: "var(--muted)", fontSize: 10 }}
                  tickLine={false}
                  axisLine={false}
                />
                <Tooltip
                  cursor={{ fill: "var(--hover)" }}
                  contentStyle={{
                    background: "var(--panel)",
                    border: "1px solid var(--line)",
                    borderRadius: 10,
                  }}
                  formatter={(value) => [`${value} min`, "Learning time"]}
                />
                <Bar
                  dataKey="minutes"
                  fill="#aee6bd"
                  radius={[5, 5, 0, 0]}
                  maxBarSize={30}
                />
              </BarChart>
            </ResponsiveContainer>
          </div>
          <p className="fine-print">
            Time spent with a visible card, in your configured timezone. A
            thoughtful answer counts toward your learning streak.
          </p>
        </div>
        <div className="panel">
          <div className="section-heading">
            <h2>Worth another look</h2>
            <RefreshCw size={18} />
          </div>
          {conceptList(
            data.due.length ? data.due : data.weak,
            "Your first lessons will help identify concepts to practice.",
          )}
        </div>
        <div className="panel">
          <div className="section-heading">
            <h2>Recently explored</h2>
            <Sparkles size={18} />
          </div>
          {conceptList(
            data.recent,
            "Your journey starts with one idea. Visit For you to begin.",
          )}
        </div>
      </div>
      <div className="panel topic-mastery">
        <div className="section-heading">
          <h2>Mastery by topic</h2>
          <GitBranch size={18} />
        </div>
        <div className="topic-mastery-grid">
          {data.topics
            .filter((t) =>
              data.subjects.some((s) => s.id === t.subject_id && s.selected),
            )
            .map((topic) => {
              const average = topic.mastery;
              return (
                <div key={topic.id}>
                  <span>
                    {topic.name}
                    <b>{percent(average)}</b>
                  </span>
                  <div className="progress-track">
                    <span style={{ width: percent(average) }} />
                  </div>
                </div>
              );
            })}
        </div>
      </div>
    </section>
  );
}

export function SettingsScreen({
  settings,
  update,
  changeTopics,
}: {
  settings: Settings;
  update: (s: Settings) => void;
  changeTopics: () => void;
}) {
  const usage = useResource<Usage>("/usage");
  const [tab, setTab] = useState("preferences");
  const [minutes, setMinutes] = useState(settings.daily_minutes);
  const [weights, setWeights] = useState(settings.weights);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const save = async (values: Partial<Settings>) => {
    setBusy(true);
    setMessage("");
    setError("");
    try {
      update(
        await api<Settings>("/settings", {
          method: "PATCH",
          body: JSON.stringify(values),
        }),
      );
      setMessage("Preferences saved.");
      usage.reload();
    } catch (e) {
      setError(errorMessage(e));
    } finally {
      setBusy(false);
    }
  };
  return (
    <section className="content-page settings-page">
      <header className="page-heading">
        <div>
          <span className="eyebrow">LEARNING, ON YOUR TERMS</span>
          <h1>
            Make yourself at home<span className="heading-dot">.</span>
          </h1>
          <p>A few thoughtful settings. A space that feels like yours.</p>
        </div>
      </header>
      <div className="page-tabs">
        <button
          className={tab === "preferences" ? "active" : ""}
          onClick={() => setTab("preferences")}
        >
          Preferences
        </button>
        <button
          className={tab === "usage" ? "active" : ""}
          onClick={() => {
            setTab("usage");
            usage.reload();
          }}
        >
          AI & usage
        </button>
        <button
          className={tab === "algorithm" ? "active" : ""}
          onClick={() => setTab("algorithm")}
        >
          Recommendation tuning
        </button>
      </div>
      {message && (
        <p className="success-message" role="status">
          {message}
        </p>
      )}
      {error && (
        <p className="error-message" role="alert">
          {error}
        </p>
      )}
      {tab === "preferences" && (
        <div className="panel settings-panel">
          <div className="setting-row">
            <div>
              <h3>Your interests</h3>
              <p>
                {settings.subjects
                  .filter((s) => s.selected)
                  .map((s) => s.name)
                  .join(" · ")}
              </p>
            </div>
            <button className="secondary-button" onClick={changeTopics}>
              Edit topics
              <ArrowUpRight size={15} />
            </button>
          </div>
          <div className="setting-row">
            <div>
              <h3>Make time for a little learning</h3>
              <p>A gentle daily intention, without locking you out.</p>
            </div>
            <div className="minutes-setting">
              <input
                aria-label="Daily learning minutes"
                type="number"
                min={3}
                max={120}
                value={minutes}
                onChange={(e) => setMinutes(Number(e.target.value))}
              />
              <span>min / day</span>
              <button
                className="text-button"
                disabled={busy || minutes < 3 || minutes > 120}
                onClick={() => void save({ daily_minutes: minutes })}
              >
                Save
              </button>
            </div>
          </div>
          <div className="setting-row">
            <div>
              <h3>Appearance</h3>
              <p>A comfortable place for your eyes.</p>
            </div>
            <div className="theme-options">
              <button
                aria-label="Dark mode"
                aria-pressed={settings.theme === "dark"}
                className={settings.theme === "dark" ? "selected" : ""}
                disabled={busy}
                onClick={() => void save({ theme: "dark" })}
              >
                <Moon size={17} />
                Dark
              </button>
              <button
                aria-label="Light mode"
                aria-pressed={settings.theme === "light"}
                className={settings.theme === "light" ? "selected" : ""}
                disabled={busy}
                onClick={() => void save({ theme: "light" })}
              >
                <Sun size={17} />
                Light
              </button>
            </div>
          </div>
          <div className="setting-row">
            <div>
              <h3>Your space, your progress</h3>
              <p>
                Saved on this backend’s database. One person, one learning
                journey.
              </p>
              <p>
                Learning timezone: {settings.timezone}. Change LEARNING_TIMEZONE
                in .env and restart the backend.
              </p>
            </div>
            <LockKeyhole size={21} />
          </div>
        </div>
      )}
      {tab === "usage" &&
        (usage.error ? (
          <ErrorState message={usage.error} retry={usage.reload} />
        ) : !usage.data ? (
          <Loading />
        ) : (
          <>
            <div className="panel ai-status">
              <div>
                <span className="eyebrow">
                  {usage.data.enabled ? "AI IS CONNECTED" : "LOCAL MODE"}
                </span>
                <h2>
                  {usage.data.enabled
                    ? "A tutor, with room to think."
                    : "Plenty to learn. No key required."}
                </h2>
                <p>
                  {usage.data.enabled
                    ? `Using ${usage.data.model}. New content is prepared in the background.`
                    : "Your seeded lessons, recommendations, reviews, and progress all work locally. Add OPENAI_API_KEY to the root .env file and restart the backend to enable AI."}
                </p>
              </div>
              <button
                role="switch"
                aria-checked={settings.ai_enabled && settings.ai_available}
                aria-label="Enable AI generation and tutoring"
                disabled={busy || !settings.ai_available}
                className={`toggle ${settings.ai_enabled && settings.ai_available ? "on" : ""}`}
                onClick={() => void save({ ai_enabled: !settings.ai_enabled })}
              >
                <span />
              </button>
            </div>
            <div className="stat-grid">
              <div className="stat-card">
                <span>Today’s estimated cost</span>
                <b>${usage.data.today_cost.toFixed(4)}</b>
                <small>
                  ${usage.data.daily_budget.toFixed(2)} daily local budget · UTC
                </small>
              </div>
              <div className="stat-card">
                <span>Cards ready to explore</span>
                <b>{usage.data.buffer_available}</b>
                <small>
                  {usage.data.total_cards} cached · {usage.data.generated_cards}{" "}
                  AI generated
                </small>
              </div>
              <div className="stat-card">
                <span>Tokens used</span>
                <b>
                  {(
                    usage.data.input_tokens + usage.data.output_tokens
                  ).toLocaleString()}
                </b>
                <small>
                  {usage.data.input_tokens.toLocaleString()} input ·{" "}
                  {usage.data.output_tokens.toLocaleString()} output
                </small>
              </div>
              <div className="stat-card">
                <span>Reused AI responses</span>
                <b>{usage.data.cache_hits}</b>
                <small>No new generation charge on a cache hit</small>
              </div>
            </div>
            <div className="panel">
              <div className="section-heading">
                <h2>Generation history</h2>
                <button className="text-button" onClick={usage.reload}>
                  <RefreshCw size={14} />
                  Refresh
                </button>
              </div>
              {usage.data.recent.length ? (
                <div className="usage-table-wrap">
                  <table className="usage-table">
                    <thead>
                      <tr>
                        <th>Request</th>
                        <th>Status</th>
                        <th>Tokens</th>
                        <th>Est. cost</th>
                      </tr>
                    </thead>
                    <tbody>
                      {usage.data.recent.map((row) => (
                        <tr key={row.id}>
                          <td>
                            {row.kind.replaceAll("_", " ")}
                            <small>
                              {new Date(row.created_at).toLocaleString()}
                            </small>
                          </td>
                          <td>
                            {row.status}
                            {row.error && <small>{row.error}</small>}
                          </td>
                          <td>{row.input_tokens + row.output_tokens}</td>
                          <td>${row.estimated_cost.toFixed(4)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : (
                <p className="small-empty muted">
                  No AI requests yet. Swiping through cached cards costs
                  nothing.
                </p>
              )}
              <p className="fine-print">
                Estimates use the input/output rates in .env, not a billing API.
                Failed requests may keep a conservative reservation when usage
                is unknown. Set a provider budget too. Total estimated cost: $
                {usage.data.total_cost.toFixed(4)}.
              </p>
            </div>
          </>
        ))}
      {tab === "algorithm" && (
        <div className="panel weights-panel">
          <h2>What should your feed value?</h2>
          <p>
            Higher weights give a factor more influence. Repetition is
            subtracted; prerequisites remain a requirement regardless of
            weights.
          </p>
          <div className="weight-controls">
            {Object.entries(weights).map(([key, value]) => (
              <label key={key}>
                <span>{key.replaceAll("_", " ")}</span>
                <input
                  type="range"
                  min="0"
                  max="5"
                  step="0.1"
                  value={value}
                  onChange={(e) =>
                    setWeights({ ...weights, [key]: Number(e.target.value) })
                  }
                />
                <b>{value.toFixed(1)}</b>
              </label>
            ))}
          </div>
          <button
            className="primary-button"
            disabled={busy}
            onClick={() => void save({ weights })}
          >
            Save recommendation weights
            <Check size={16} />
          </button>
          <p className="fine-print">
            Changes affect newly selected cards. Open “Why this card?” on the
            feed to inspect its saved score and mastery at selection. Full
            formulas and thresholds are documented in docs/ALGORITHMS.md.
          </p>
        </div>
      )}
    </section>
  );
}
