import { useCallback, useEffect, useRef, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { api } from "../api/endpoints";
import type { Submission, TaskDetail } from "../api/types";
import {
  Difficulty,
  ErrorText,
  GraderBadge,
  GraderPipeline,
  MasvsBadge,
  MentorMark,
  Panel,
  Skeleton,
  SkeletonRow,
  StatusChip,
} from "../components/ui";
import { SubmitForm } from "../components/SubmitForm";
import { ChallengeFiles } from "../components/ChallengeFiles";
import { GradePanel } from "../components/GradePanel";
import { HintPanel } from "../components/HintPanel";
import { AiAttemptPanel } from "../components/AiAttemptPanel";

const TERMINAL = new Set(["passed", "failed", "error"]);

export function TaskPage() {
  const { taskId = "" } = useParams();
  const [task, setTask] = useState<TaskDetail | null>(null);
  const [error, setError] = useState("");
  const [submission, setSubmission] = useState<Submission | null>(null);
  const [history, setHistory] = useState<Submission[]>([]);
  const pollRef = useRef<number | null>(null);

  const refreshHistory = useCallback(() => {
    api.listSubmissions(taskId).then(setHistory).catch(() => undefined);
  }, [taskId]);

  useEffect(() => {
    setTask(null);
    setSubmission(null);
    api.getTask(taskId).then(setTask).catch((e) => setError(e.message));
    refreshHistory();
    return () => {
      if (pollRef.current) window.clearInterval(pollRef.current);
    };
  }, [taskId, refreshHistory]);

  function pollSubmission(id: number) {
    if (pollRef.current) window.clearInterval(pollRef.current);
    pollRef.current = window.setInterval(async () => {
      try {
        const s = await api.getSubmission(id);
        setSubmission(s);
        if (TERMINAL.has(s.status)) {
          window.clearInterval(pollRef.current!);
          pollRef.current = null;
          refreshHistory();
        }
      } catch {
        window.clearInterval(pollRef.current!);
        pollRef.current = null;
      }
    }, 1500);
  }

  async function onSubmit(payload: Record<string, unknown>) {
    const created = await api.submit(taskId, payload);
    setSubmission(created);
    pollSubmission(created.id);
  }

  if (error) return <ErrorText>{error}</ErrorText>;
  if (!task) return <TaskSkeleton />;

  const passed = submission?.status === "passed" || history.some((s) => s.status === "passed");
  const bestScore = history.reduce((m, s) => (s.status === "passed" ? Math.max(m, s.score) : m), 0);

  return (
    <div className="space-y-6">
      {/* ---------- header ---------- */}
      <div className="panel overflow-hidden p-6">
        <nav className="flex flex-wrap items-center gap-2 font-mono text-2xs uppercase text-zinc-400" aria-label="breadcrumb">
          <Link to="/" className="rounded text-zinc-400 transition-colors hover:text-phosphor">
            ← skill map
          </Link>
          <span aria-hidden>/</span>
          <span>module {task.module.padStart(2, "0")}</span>
          <span aria-hidden>/</span>
          <span className="text-zinc-200">{task.domain}</span>
        </nav>

        <div className="mt-3 flex flex-wrap items-start justify-between gap-4">
          <div className="min-w-0">
            <div className="flex flex-wrap items-center gap-3">
              <h1 className="text-2xl font-semibold tracking-tight text-zinc-50 sm:text-3xl">
                {task.title}
              </h1>
              {task.is_reference && (
                <span className="chip-flag" title="reference task — live grader implemented">
                  <span aria-hidden>★</span>reference
                </span>
              )}
              {passed && (
                <span className="chip-pass">
                  <span aria-hidden>✓</span>cleared
                </span>
              )}
            </div>
            <div className="mt-3 flex flex-wrap items-center gap-2">
              {task.masvs.map((c) => (
                <MasvsBadge key={c} control={c} />
              ))}
              <GraderBadge type={task.success_type} />
              <span className="mx-1">
                <Difficulty level={task.difficulty} />
              </span>
              <span className="font-mono text-2xs uppercase text-zinc-400">
                ~{task.time_estimate_min} min
              </span>
            </div>
          </div>

          {bestScore > 0 && (
            <div className="text-right">
              <p className="eyebrow">best score</p>
              <p className="font-mono text-2xl font-bold text-phosphor">
                {bestScore}
                <span className="ml-1 text-xs font-medium text-zinc-500">pts</span>
              </p>
            </div>
          )}
        </div>

        <div className="mt-5 border-t border-ink-500/60 pt-4">
          <p className="eyebrow mb-2">
            how this task is graded
            <span className="ml-2 normal-case tracking-normal">
              — a real emulator runs every submission
            </span>
          </p>
          <GraderPipeline type={task.success_type} status={submission?.status ?? null} />
        </div>
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        <div className="space-y-6 lg:col-span-2">
          <Panel>
            <h2 className="label">Objective</h2>
            <p className="whitespace-pre-line text-sm leading-relaxed text-zinc-200">
              {task.objective}
            </p>
            {task.mastg_refs.length > 0 && (
              <div className="mt-4 flex flex-wrap items-center gap-1.5 border-t border-ink-500/50 pt-3">
                <span className="eyebrow mr-1">MASTG</span>
                {task.mastg_refs.map((r) => (
                  <span key={r} className="chip-masvs normal-case">
                    {r}
                  </span>
                ))}
              </div>
            )}
          </Panel>

          <ChallengeFiles taskId={taskId} />

          <Panel className={submission ? "" : "border-phosphor/25"}>
            <div className="mb-3 flex items-center justify-between">
              <h2 className="label mb-0">Submit your solution</h2>
              <span className="inline-flex items-center gap-1.5 font-mono text-2xs uppercase text-zinc-400">
                <span aria-hidden className="h-1.5 w-1.5 rounded-full bg-phosphor" />
                emulator grader
              </span>
            </div>
            <SubmitForm task={task} onSubmit={onSubmit} />
          </Panel>

          <GradePanel submission={submission} taskId={taskId} graderImplemented={task.grader_status === "implemented"} />

          {history.length > 0 && (
            <Panel>
              <h2 className="label">Submission history</h2>
              <ul className="divide-y divide-ink-500/40 font-mono text-xs">
                {history.slice(0, 8).map((s) => (
                  <li key={s.id} className="flex items-center justify-between gap-3 py-2">
                    <span className="flex items-center gap-2 text-zinc-400">
                      <span className="text-zinc-400">#{s.id}</span>
                      {new Date(s.created_at).toLocaleString()}
                      {s.ai_generated && <MentorMark>ai attempt</MentorMark>}
                    </span>
                    <StatusChip status={s.status} score={s.score} />
                  </li>
                ))}
              </ul>
            </Panel>
          )}
        </div>

        <div className="space-y-6 lg:col-span-1">
          <HintPanel task={task} passed={passed} />
          <Panel className="border-signal-violet/25">
            <div className="mb-2 flex items-center justify-between">
              <h2 className="label mb-0">AI vs the grader</h2>
              <MentorMark>adversary</MentorMark>
            </div>
            <p className="text-xs leading-relaxed text-zinc-400">
              Let the AI attempt this task with no access to your files, then watch the emulator
              grader judge its answer. The grader is the source of truth — not the model.
            </p>
            <AiAttemptPanel taskId={taskId} />
          </Panel>
        </div>
      </div>
    </div>
  );
}

function TaskSkeleton() {
  return (
    <div className="space-y-6" role="status" aria-label="loading task">
      <div className="panel space-y-3 p-6">
        <Skeleton className="h-3 w-48" />
        <Skeleton className="h-8 w-2/3" />
        <div className="flex gap-2">
          <Skeleton className="h-5 w-28" />
          <Skeleton className="h-5 w-20" />
          <Skeleton className="h-5 w-12" />
        </div>
        <Skeleton className="mt-2 h-6 w-full max-w-xl" />
      </div>
      <div className="grid gap-6 lg:grid-cols-3">
        <div className="space-y-6 lg:col-span-2">
          <div className="panel space-y-2 p-5">
            <Skeleton className="h-3 w-20" />
            <Skeleton className="h-3.5 w-full" />
            <Skeleton className="h-3.5 w-5/6" />
            <Skeleton className="h-3.5 w-2/3" />
          </div>
          <div className="panel space-y-2 p-5">
            <Skeleton className="h-3 w-32" />
            <SkeletonRow />
          </div>
        </div>
        <div className="panel space-y-3 p-5">
          <Skeleton className="h-3 w-16" />
          <div className="flex gap-2">
            <Skeleton className="h-8 w-16" />
            <Skeleton className="h-8 w-16" />
            <Skeleton className="h-8 w-20" />
          </div>
          <Skeleton className="h-14 w-full" />
        </div>
      </div>
    </div>
  );
}
