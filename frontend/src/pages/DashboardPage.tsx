import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api/endpoints";
import type { SkillMap, SkillNode } from "../api/types";
import {
  Difficulty,
  ErrorText,
  GraderBadge,
  GraderPipeline,
  MasvsBadge,
  PageHeader,
  Skeleton,
  SkeletonRow,
  StateDot,
} from "../components/ui";
import { TargetAppCard } from "../components/TargetAppCard";

export function DashboardPage() {
  const [map, setMap] = useState<SkillMap | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    api.skillMap().then(setMap).catch((e) => setError(e.message));
  }, []);

  const modules = useMemo(() => groupByModule(map?.nodes ?? []), [map]);
  const titles = useMemo(
    () => new Map((map?.nodes ?? []).map((n) => [n.id, n.title] as const)),
    [map],
  );
  const passed = map?.nodes.filter((n) => n.state === "passed").length ?? 0;
  const total = map?.nodes.length ?? 0;
  const pct = total ? Math.round((passed / total) * 100) : 0;
  const recommended = map?.nodes.find((n) => n.id === map?.recommended_task_id) ?? null;

  if (error) return <ErrorText>{error}</ErrorText>;
  if (!map) return <DashboardSkeleton />;

  return (
    <div className="space-y-8">
      <PageHeader
        eyebrow={`curriculum · ${modules.length} modules · ${total} tasks`}
        title="Skill map"
        subtitle="Work the path top to bottom. Every task is graded live on a real Android emulator."
        aside={
          <div className="min-w-[14rem]" aria-label={`${passed} of ${total} tasks cleared`}>
            <div className="flex items-baseline justify-between font-mono text-xs text-zinc-400">
              <span className="eyebrow">progress</span>
              <span>
                <span className="text-lg font-bold text-phosphor">{passed}</span>
                <span className="text-zinc-500"> / {total} cleared</span>
              </span>
            </div>
            <div className="mt-1.5 h-1.5 overflow-hidden rounded-full bg-ink-600">
              <div
                className="h-full rounded-full bg-gradient-to-r from-phosphor-dim to-phosphor transition-[width] duration-700"
                style={{ width: `${pct}%` }}
              />
            </div>
          </div>
        }
      />

      {recommended && <RecommendedHero node={recommended} />}

      <TargetAppCard />

      <div className="relative">
        <div aria-hidden className="rail" />
        <div className="space-y-6">
          {modules.map(([moduleId, nodes]) => (
            <ModuleSection
              key={moduleId}
              moduleId={moduleId}
              nodes={nodes}
              recommendedId={map.recommended_task_id}
              titles={titles}
            />
          ))}
        </div>
      </div>
    </div>
  );
}

/* ------------------------------------------------------------------ */

function RecommendedHero({ node }: { node: SkillNode }) {
  return (
    <Link
      to={`/tasks/${node.id}`}
      className="group block rounded-xl"
      aria-label={`Start recommended task: ${node.title}`}
    >
      <div className="panel relative overflow-hidden border-phosphor/40 p-6 transition-colors duration-200 group-hover:border-phosphor/70 sm:p-7">
        <div className="relative flex flex-wrap items-center justify-between gap-6">
          <div className="min-w-0 flex-1">
            <p className="inline-flex items-center gap-2 font-mono text-2xs font-semibold uppercase text-phosphor">
              <span aria-hidden className="h-1.5 w-1.5 rounded-full bg-phosphor" />
              recommended next
              <span className="text-zinc-500">· module {node.module} · {node.domain}</span>
            </p>
            <h2 className="mt-2 text-2xl font-semibold tracking-tight text-zinc-50 sm:text-3xl">
              {node.title}
            </h2>
            <div className="mt-3 flex flex-wrap items-center gap-2">
              {node.masvs.map((c) => (
                <MasvsBadge key={c} control={c} />
              ))}
              <GraderBadge type={node.success_type} />
              <span className="ml-1">
                <Difficulty level={node.difficulty} />
              </span>
            </div>
            <div className="mt-4 hidden sm:block">
              <GraderPipeline type={node.success_type} />
            </div>
          </div>
          <span className="btn-primary shrink-0 px-6 py-3 text-base group-hover:shadow-btn-hover">
            Start
            <span aria-hidden className="transition-transform group-hover:translate-x-0.5">→</span>
          </span>
        </div>
      </div>
    </Link>
  );
}

/* ------------------------------------------------------------------ */

function ModuleSection({
  moduleId,
  nodes,
  recommendedId,
  titles,
}: {
  moduleId: string;
  nodes: SkillNode[];
  recommendedId: string | null;
  titles: Map<string, string>;
}) {
  const cleared = nodes.filter((n) => n.state === "passed").length;
  const complete = cleared === nodes.length && nodes.length > 0;
  const num = moduleId.padStart(2, "0");

  return (
    <section className="relative pl-11" aria-labelledby={`module-${moduleId}`}>
      {/* module node on the rail */}
      <span
        aria-hidden
        className={`absolute left-0 top-3 grid h-8 w-8 place-items-center rounded-full border font-mono text-2xs font-bold ${
          complete
            ? "border-phosphor bg-phosphor text-ink-900"
            : cleared > 0
              ? "border-phosphor/60 bg-ink-800 text-phosphor"
              : "border-ink-300 bg-ink-800 text-zinc-400"
        }`}
      >
        {num}
      </span>

      <div className="panel overflow-hidden">
        <header className="flex flex-wrap items-center justify-between gap-3 border-b border-ink-500/60 bg-ink-800/60 px-5 py-3">
          <h2 id={`module-${moduleId}`} className="flex items-baseline gap-2 font-mono text-xs uppercase">
            <span className="text-phosphor-dim">module {num}</span>
            <span aria-hidden className="text-zinc-600">·</span>
            <span className="text-sm font-semibold tracking-wide text-zinc-100">{nodes[0]?.domain}</span>
          </h2>
          <div className="flex items-center gap-3 font-mono text-2xs uppercase text-zinc-400">
            <span>
              <span className={complete ? "text-phosphor" : "text-zinc-200"}>{cleared}</span>
              <span className="text-zinc-500">/{nodes.length}</span> cleared
            </span>
            <span className="flex items-center gap-[3px]" aria-hidden>
              {nodes.map((n) => (
                <span
                  key={n.id}
                  className={`h-1.5 w-3 rounded-sm ${
                    n.state === "passed" ? "bg-phosphor" : "bg-ink-400"
                  }`}
                />
              ))}
            </span>
          </div>
        </header>
        <ul className="divide-y divide-ink-500/40">
          {nodes.map((node) => (
            <NodeRow
              key={node.id}
              node={node}
              isNext={node.id === recommendedId}
              prereqTitle={
                node.state === "locked" && node.prereqs.length > 0
                  ? (titles.get(node.prereqs[0]) ?? null)
                  : null
              }
            />
          ))}
        </ul>
      </div>
    </section>
  );
}

/* ------------------------------------------------------------------ */

function NodeRow({
  node,
  isNext,
  prereqTitle,
}: {
  node: SkillNode;
  isNext: boolean;
  prereqTitle: string | null;
}) {
  // Every task is freely navigable — jump straight to any module. The state
  // treatment shows progress (passed / available / prereq-gated) but never
  // disables the row: locked rows only dim their leading edge and name the
  // prerequisite so the learner knows what the path expects first.
  const passed = node.state === "passed";
  const locked = node.state === "locked";

  const rowCls = passed
    ? "bg-phosphor/[0.04] hover:bg-phosphor/[0.07]"
    : isNext
      ? "bg-ink-700/50 hover:bg-ink-700/80"
      : "hover:bg-ink-700/60";

  const edgeCls = passed
    ? "bg-phosphor"
    : isNext
      ? "bg-phosphor/70"
      : locked
        ? "bg-transparent border-l border-dashed border-ink-300"
        : "bg-ink-400/0 group-hover:bg-phosphor/40";

  return (
    <li>
      <Link
        to={`/tasks/${node.id}`}
        className={`group relative flex items-center gap-4 px-5 py-3 transition-colors focus-visible:outline-offset-[-2px] ${rowCls}`}
      >
        <span aria-hidden className={`absolute inset-y-0 left-0 w-0.5 transition-colors ${edgeCls}`} />
        <StateDot state={node.state} />

        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2">
            <span
              className={`truncate text-sm font-medium ${
                locked ? "text-zinc-300" : "text-zinc-100"
              } group-hover:text-white`}
            >
              {node.title}
            </span>
            {node.is_reference && (
              <span className="font-mono text-xs text-signal-amber" title="reference task — live grader implemented">
                ★
              </span>
            )}
            {isNext && (
              <span className="chip-pass hidden sm:inline-flex">
                <span aria-hidden>›</span>next
              </span>
            )}
          </div>
          <div className="mt-1.5 flex flex-wrap items-center gap-1.5">
            {node.masvs.map((c) => (
              <MasvsBadge key={c} control={c} />
            ))}
            <GraderBadge type={node.success_type} />
            {prereqTitle && (
              <span className="ml-1 truncate font-mono text-2xs text-zinc-500" title={`prerequisite: ${prereqTitle}`}>
                after · {prereqTitle}
              </span>
            )}
          </div>
        </div>

        <div className="flex shrink-0 items-center gap-4">
          <Difficulty level={node.difficulty} />
          <span className="w-16 text-right font-mono text-xs">
            {passed ? (
              <span className="font-semibold text-phosphor">{node.best_score} pts</span>
            ) : node.attempts > 0 ? (
              <span className="text-zinc-500">{node.attempts} {node.attempts === 1 ? "try" : "tries"}</span>
            ) : (
              <span aria-hidden className="text-zinc-600 transition-colors group-hover:text-phosphor">→</span>
            )}
          </span>
        </div>
      </Link>
    </li>
  );
}

/* ------------------------------------------------------------------ */

function DashboardSkeleton() {
  return (
    <div className="space-y-8" role="status" aria-label="loading skill map">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div className="space-y-2">
          <Skeleton className="h-3 w-40" />
          <Skeleton className="h-7 w-48" />
          <Skeleton className="h-3.5 w-80 max-w-full" />
        </div>
        <div className="w-56 space-y-2">
          <Skeleton className="h-4 w-full" />
          <Skeleton className="h-1.5 w-full rounded-full" />
        </div>
      </div>
      <div className="panel space-y-3 border-phosphor/20 p-7">
        <Skeleton className="h-3 w-36" />
        <Skeleton className="h-8 w-2/3" />
        <div className="flex gap-2">
          <Skeleton className="h-5 w-24" />
          <Skeleton className="h-5 w-16" />
        </div>
      </div>
      {[0, 1].map((i) => (
        <div key={i} className="panel space-y-2 p-4">
          <Skeleton className="mb-3 h-3.5 w-52" />
          <SkeletonRow />
          <SkeletonRow />
          <SkeletonRow />
        </div>
      ))}
    </div>
  );
}

function groupByModule(nodes: SkillNode[]): [string, SkillNode[]][] {
  const groups = new Map<string, SkillNode[]>();
  for (const n of nodes) {
    if (!groups.has(n.module)) groups.set(n.module, []);
    groups.get(n.module)!.push(n);
  }
  return Array.from(groups.entries()).sort((a, b) => Number(a[0]) - Number(b[0]));
}
