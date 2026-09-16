export type Mastery = {
  concept_id: string;
  mastery: number;
  effective_mastery: number;
  confidence: number;
  retention: number;
  times_seen: number;
  correct_answers: number;
  incorrect_answers: number;
  last_reviewed: string | null;
  next_review: string | null;
  interval_days: number;
  retrieval_streak: number;
};
export type Visual = {
  type: "array_elimination" | "vector" | "growth" | "steps";
  values: number[];
  labels: string[];
  caption: string;
};
export type CardKind =
  | "micro_lesson"
  | "quiz"
  | "flashcard"
  | "visualization"
  | "example"
  | "challenge";
export type Card = {
  id: string;
  concept_id: string;
  concept_name: string;
  type: CardKind;
  title: string;
  hook: string;
  explanation: string;
  takeaway: string;
  difficulty: number;
  estimated_seconds: number;
  steps: string[];
  equation: string | null;
  code: string | null;
  visualization: Visual | null;
  quiz: { question: string; answers: string[] } | null;
  source: string;
  subject: string;
  subject_id: string;
  topic: string;
  color: string;
  saved: boolean;
  mastery: Mastery;
  presentation_id: string | null;
  recommendation_reason: {
    label: string;
    is_review: boolean;
    [key: string]: unknown;
  } | null;
};
export type Subject = {
  id: string;
  name: string;
  color: string;
  selected: boolean;
};
export type Settings = {
  onboarded: boolean;
  level: "beginner" | "intermediate" | "advanced";
  theme: "dark" | "light";
  daily_minutes: number;
  ai_enabled: boolean;
  ai_available: boolean;
  model: string;
  timezone: string;
  subjects: Subject[];
  weights: Record<string, number>;
};
export type Concept = {
  id: string;
  topic_id: string;
  name: string;
  summary: string;
  difficulty: number;
  prerequisites: string[];
  unlocked: boolean;
  mastered: boolean;
  mastery: Mastery;
};
export type LearningPath = {
  id: string;
  subject_id: string;
  title: string;
  description: string;
  concept_ids: string[];
  next_concept_id: string | null;
  progress: number;
};
export type Knowledge = {
  subjects: Subject[];
  topics: { id: string; subject_id: string; name: string }[];
  concepts: Concept[];
  paths: LearningPath[];
};
export type Progress = {
  encountered: number;
  mastered: number;
  reviews_due: number;
  streak: number;
  total_minutes: number;
  today_minutes: number;
  total_concepts: number;
  week: { date: string; day: string; minutes: number }[];
  subjects: (Subject & { mastery: number; concept_count: number })[];
  topics: { id: string; name: string; subject_id: string; mastery: number }[];
  recent: string[];
  weak: string[];
  due: string[];
};
export type EventKind =
  | "shown"
  | "dwell"
  | "answer"
  | "known"
  | "deeper"
  | "tutor"
  | "skipped"
  | "revisited"
  | "saved";
export type EventResult = {
  mastery: Mastery;
  correct?: boolean;
  correct_answer?: number;
  explanation?: string;
  duplicate: boolean;
};
export type Usage = {
  enabled: boolean;
  model: string;
  daily_budget: number;
  today_cost: number;
  total_cost: number;
  input_tokens: number;
  output_tokens: number;
  cache_hits: number;
  buffer_available: number;
  total_cards: number;
  generated_cards: number;
  recent: {
    id: string;
    kind: string;
    status: string;
    model: string;
    input_tokens: number;
    output_tokens: number;
    estimated_cost: number;
    error: string | null;
    created_at: string;
  }[];
};
export type ImportRecord = {
  id: string;
  title: string;
  status: string;
  created_at: string;
};
export type TutorReply = {
  answer: string;
  follow_up: string;
  mode: "local" | "ai";
};
