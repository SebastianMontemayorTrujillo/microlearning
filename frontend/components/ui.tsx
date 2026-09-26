"use client";

import { ArrowRight, LoaderCircle, RefreshCw, Sparkles } from "lucide-react";

export function Logo() {
  return (
    <span className="logo">
      <span className="logo-mark">
        <Sparkles size={22} />
      </span>
      lilt<span className="logo-period">.</span>
    </span>
  );
}
export function Loading({
  message = "Gathering a few good ideas…",
}: {
  message?: string;
}) {
  return (
    <div className="empty-state">
      <LoaderCircle className="spin" size={25} />
      <p>{message}</p>
    </div>
  );
}
export function ErrorState({
  message,
  retry,
}: {
  message: string;
  retry: () => void;
}) {
  return (
    <div className="empty-state">
      <p role="alert">{message}</p>
      <button className="secondary-button" onClick={retry}>
        <RefreshCw size={16} />
        Try again
      </button>
    </div>
  );
}
export function EmptyState({
  title,
  description,
  action,
  onAction,
}: {
  title: string;
  description: string;
  action?: string;
  onAction?: () => void;
}) {
  return (
    <div className="empty-state">
      <div className="empty-symbol">
        <Sparkles size={30} />
      </div>
      <h3>{title}</h3>
      <p>{description}</p>
      {action && (
        <button className="primary-button" onClick={onAction}>
          {action}
          <ArrowRight size={16} />
        </button>
      )}
    </div>
  );
}
