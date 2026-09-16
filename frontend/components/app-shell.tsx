"use client";

import Link from "next/link";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { useCallback, useEffect, useRef, useState } from "react";
import {
  ArrowRight,
  Bookmark,
  BookOpen,
  ChartNoAxesCombined,
  ChevronRight,
  CircleHelp,
  Compass,
  Leaf,
  Settings2,
  Sparkles,
} from "lucide-react";
import { useResource } from "@/hooks/use-resource";
import { percent } from "@/lib/api";
import type { Card, Knowledge, Progress, Settings } from "@/types";
import { Feed } from "./feed";
import { Onboarding } from "./onboarding";
import {
  LearnScreen,
  ProgressScreen,
  SavedScreen,
  SettingsScreen,
} from "./screens";
import { ErrorState, Loading, Logo } from "./ui";

const navigation = [
  { href: "/", label: "For you", icon: Compass },
  { href: "/learn", label: "Learn", icon: BookOpen },
  { href: "/saved", label: "Saved", icon: Bookmark },
  { href: "/progress", label: "Progress", icon: ChartNoAxesCombined },
  { href: "/settings", label: "Settings", icon: Settings2 },
];

export function LearningApp() {
  const pathname = usePathname();
  const params = useSearchParams();
  const router = useRouter();
  const preferences = useResource<Settings>("/settings");
  const [revision, setRevision] = useState(0);
  const progress = useResource<Progress>("/progress", revision);
  const knowledge = useResource<Knowledge>("/knowledge", revision);
  const [editTopics, setEditTopics] = useState(false);
  const [openedCard, setOpenedCard] = useState<Card | null>(null);
  const [showHelp, setShowHelp] = useState(false);
  const pending = useRef<ReturnType<typeof setTimeout> | null>(null);
  const activity = useCallback(() => {
    if (pending.current) clearTimeout(pending.current);
    pending.current = setTimeout(() => setRevision((r) => r + 1), 500);
  }, []);
  useEffect(
    () => () => {
      if (pending.current) clearTimeout(pending.current);
    },
    [],
  );
  useEffect(() => {
    if (preferences.data)
      document.documentElement.dataset.theme = preferences.data.theme;
  }, [preferences.data?.theme]);
  if (!preferences.data)
    return (
      <main className="boot-screen">
        <Logo />
        {preferences.error ? (
          <ErrorState message={preferences.error} retry={preferences.reload} />
        ) : (
          <Loading message="Opening your learning space…" />
        )}
      </main>
    );
  const settings = preferences.data;
  const updated = (value: Settings) => {
    preferences.setData(value);
    activity();
  };
  const changeTopics = () => setEditTopics(true);
  if (!settings.onboarded || editTopics)
    return (
      <Onboarding
        settings={settings}
        complete={(value) => {
          updated(value);
          setEditTopics(false);
        }}
        close={settings.onboarded ? () => setEditTopics(false) : undefined}
      />
    );
  const learn = (id: string) => {
    setOpenedCard(null);
    router.push(`/?concept=${encodeURIComponent(id)}`);
  };
  const isFeed = pathname === "/";
  const activeRoute = navigation.find((n) => n.href === pathname);
  const graph = knowledge.data;
  const firstPath = graph?.paths.find((p) =>
    graph.subjects.some((s) => s.id === p.subject_id && s.selected),
  );
  const nextConcept = graph?.concepts.find(
    (c) => c.id === firstPath?.next_concept_id,
  );
  const dailyProgress = Math.min(
    100,
    ((progress.data?.today_minutes || 0) / settings.daily_minutes) * 100,
  );
  return (
    <div className={`app-shell ${isFeed ? "feed-layout" : "page-layout"}`}>
      <aside className="sidebar">
        <Link
          href="/"
          className="brand-link"
          aria-label="Lilt home"
          onClick={() => setOpenedCard(null)}
        >
          <Logo />
        </Link>
        <span className="sidebar-tagline">A little wiser.</span>
        <nav className="main-nav" aria-label="Main navigation">
          {navigation.map(({ href, label, icon: Icon }) => (
            <Link
              key={href}
              href={href}
              className={pathname === href ? "active" : ""}
              onClick={() => setOpenedCard(null)}
              aria-current={pathname === href ? "page" : undefined}
            >
              <Icon size={21} strokeWidth={1.7} />
              <span>{label}</span>
              {pathname === href && <span className="nav-active-dot" />}
            </Link>
          ))}
        </nav>
        <div className="sidebar-bottom">
          <div className="sidebar-note">
            <Leaf size={22} />
            <p>
              Less scrolling.
              <br />
              <span>More understanding.</span>
            </p>
          </div>
          <button
            className="help-button"
            onClick={() => setShowHelp(!showHelp)}
          >
            <CircleHelp size={17} />
            <span>A quick guide</span>
          </button>
          <div className="personal-profile">
            <span className="profile-avatar">Y</span>
            <div>
              <b>Your space</b>
              <small>
                {settings.ai_available && settings.ai_enabled
                  ? "AI learning enabled"
                  : "Learning locally"}
              </small>
            </div>
            <span className="online-dot" />
          </div>
        </div>
      </aside>
      <div className="mobile-top">
        <Link href="/" aria-label="Lilt home">
          <Logo />
        </Link>
        <span className="pill">
          <span className="online-dot" />
          {settings.ai_available && settings.ai_enabled
            ? "AI enabled"
            : "Local mode"}
        </span>
      </div>
      <main className={isFeed ? "main-content feed-main" : "main-content"}>
        {isFeed ? (
          <Feed
            key={`${params.get("concept") || "feed"}-${openedCard?.presentation_id || ""}-${settings.subjects
              .filter((s) => s.selected)
              .map((s) => s.id)
              .join(",")}`}
            settings={settings}
            initialCard={openedCard}
            focus={params.get("concept") || ""}
            onActivity={activity}
            changeTopics={changeTopics}
          />
        ) : pathname === "/learn" ? (
          <LearnScreen
            settings={settings}
            learn={learn}
            revision={revision}
            changed={activity}
          />
        ) : pathname === "/saved" ? (
          <SavedScreen
            open={(card) => {
              setOpenedCard(card);
              router.push("/");
            }}
          />
        ) : pathname === "/progress" ? (
          <ProgressScreen learn={learn} revision={revision} />
        ) : pathname === "/settings" ? (
          <SettingsScreen
            settings={settings}
            update={updated}
            changeTopics={changeTopics}
          />
        ) : (
          <div className="empty-state">
            <h1>This page hasn’t been written yet.</h1>
            <Link className="primary-button" href="/">
              Back to learning
              <ArrowRight size={16} />
            </Link>
          </div>
        )}
      </main>
      {isFeed && (
        <aside className="learning-rail">
          <div className="rail-top">
            <span className="pill">
              <span className="online-dot" />
              {settings.ai_available && settings.ai_enabled
                ? "AI learning enabled"
                : "Local learning mode"}
            </span>
          </div>
          <div className="rhythm-panel">
            <div className="section-heading">
              <h3>Your daily moment</h3>
              <Leaf size={17} />
            </div>
            <div
              className="daily-ring"
              style={{
                background: `conic-gradient(var(--accent) ${dailyProgress}%, var(--line) 0)`,
              }}
            >
              <div>
                <b>
                  {Math.round(progress.data?.today_minutes || 0)}
                  <small> / {settings.daily_minutes}</small>
                </b>
                <span>MINUTES TODAY</span>
              </div>
            </div>
            <p>
              {dailyProgress >= 100
                ? "A good moment to pause. Let those ideas settle."
                : "A little consistency goes a long way."}
            </p>
            <div className="daily-stats">
              <div>
                <b>{progress.data?.encountered || 0}</b>
                <span>ideas explored</span>
              </div>
              <div>
                <b>{progress.data?.streak || 0}</b>
                <span>day streak</span>
              </div>
            </div>
          </div>
          <div className="rail-section">
            <div className="section-heading">
              <h3>Your next connection</h3>
              <Sparkles size={16} />
            </div>
            {firstPath && (
              <button
                className="next-path"
                onClick={() =>
                  nextConcept ? learn(nextConcept.id) : router.push("/learn")
                }
              >
                <span className="path-mini-art">
                  {firstPath.subject_id === "cs" ? "{ }" : "↗"}
                </span>
                <span>
                  <small>KEEP BUILDING</small>
                  <b>{firstPath.title}</b>
                  <span className="progress-track">
                    <span style={{ width: percent(firstPath.progress) }} />
                  </span>
                </span>
                <ChevronRight size={16} />
              </button>
            )}
            <Link className="text-button" href="/learn">
              Explore learning paths
              <ArrowRight size={14} />
            </Link>
          </div>
          <div className="rail-section topics-rail">
            <div className="section-heading">
              <h3>Following your curiosity</h3>
              <button className="text-button" onClick={changeTopics}>
                Edit
              </button>
            </div>
            <div>
              {settings.subjects
                .filter((s) => s.selected)
                .map((subject) => (
                  <span key={subject.id}>
                    <i className={`subject-dot ${subject.color}`} />
                    {subject.name}
                  </span>
                ))}
            </div>
          </div>
          <div className="rail-quote">
            <span>“</span>
            <p>
              The beautiful thing about learning is that nobody can take it away
              from you.
            </p>
            <small>KEEP A LITTLE CURIOSITY CLOSE.</small>
          </div>
        </aside>
      )}
      <nav className="mobile-nav" aria-label="Mobile navigation">
        {navigation.map(({ href, label, icon: Icon }) => (
          <Link
            key={href}
            href={href}
            className={pathname === href ? "active" : ""}
            aria-current={pathname === href ? "page" : undefined}
            onClick={() => setOpenedCard(null)}
          >
            <Icon size={20} />
            <span>{label}</span>
          </Link>
        ))}
      </nav>
      {showHelp && (
        <div className="help-toast" role="status">
          <b>Your little guide</b>
          <p>
            Swipe or scroll vertically to explore. Use ↑ and ↓ on desktop.
            Answer a quiz to strengthen your learning model. Save an idea, or
            ask the tutor to make it clearer.
          </p>
          <p>
            Progress lives in your database.{" "}
            {activeRoute?.label === "For you"
              ? "Tap the sparkle explanation at the bottom of a card to see why it was selected."
              : "Your feed and learning paths use the same mastery data."}
          </p>
          <button className="text-button" onClick={() => setShowHelp(false)}>
            Got it
            <CheckIcon />
          </button>
        </div>
      )}
    </div>
  );
}

function CheckIcon() {
  return <ArrowRight size={15} />;
}
