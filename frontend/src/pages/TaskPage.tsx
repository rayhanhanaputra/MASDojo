import { useCallback, useEffect, useRef, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { api } from "../api/endpoints";
import type { Submission, TaskDetail } from "../api/types";
import {
  Difficulty,
  ErrorText,
  GraderBadge,
  MasvsBadge,
  Panel,
  Spinner,
} from "../components/ui";
import { SubmitForm } from "../components/SubmitForm";
import { ChallengeFiles } from "../components/ChallengeFiles";
import { GradePanel } from "../components/GradePanel";
import { HintPanel } from "../components/HintPanel";

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
  if (!task) return <Spinner label="loading task…" />;

  const passed = submission?.status === "passed" || history.some((s) => s.status === "passed");

  return (
    <div className="space-y-6">
      <div>
        <Link to="/" className="font-mono text-xs text-zinc-500 hover:text-phosphor">
          ← skill map
        </Link>
        <div className="mt-2 flex flex-wrap items-center gap-3">
          <h1 className="text-2xl font-semibold text-zinc-100">{task.title}</h1>
          {task.is_reference && <span className="text-signal-amber" title="reference task">★</span>}
        </div>
        <div className="mt-3 flex flex-wrap items-center gap-2">
          {task.masvs.map((c) => (
            <MasvsBadge key={c} control={c} />
          ))}
          <GraderBadge type={task.success_type} />
          <Difficulty level={task.difficulty} />
          <span className="font-mono text-xs text-zinc-600">~{task.time_estimate_min} min</span>
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
              <p className="mt-3 font-mono text-[11px] text-zinc-600">
                MASTG: {task.mastg_refs.join(", ")}
              </p>
            )}
          </Panel>

          <ChallengeFiles taskId={taskId} />

          <Panel>
            <h2 className="label">Submit your solution</h2>
            <SubmitForm task={task} onSubmit={onSubmit} />
          </Panel>

          <GradePanel submission={submission} taskId={taskId} graderImplemented={task.grader_status === "implemented"} />

          {history.length > 0 && (
            <Panel>
              <h2 className="label">Submission history</h2>
              <ul className="space-y-1 font-mono text-xs">
                {history.slice(0, 8).map((s) => (
                  <li key={s.id} className="flex items-center justify-between text-zinc-500">
                    <span>#{s.id} · {new Date(s.created_at).toLocaleString()}</span>
                    <StatusTag status={s.status} score={s.score} />
                  </li>
                ))}
              </ul>
            </Panel>
          )}
        </div>

        <div className="lg:col-span-1">
          <HintPanel task={task} passed={passed} />
        </div>
      </div>
    </div>
  );
}

function StatusTag({ status, score }: { status: Submission["status"]; score: number }) {
  const styles: Record<string, string> = {
    passed: "text-phosphor",
    failed: "text-signal-red",
    error: "text-signal-amber",
    running: "text-signal-cyan",
    queued: "text-zinc-500",
  };
  return (
    <span className={styles[status]}>
      {status}
      {status === "passed" ? ` · ${score}pts` : ""}
    </span>
  );
}
