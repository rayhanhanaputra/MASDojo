import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api/endpoints";
import type { SkillMap, SkillNode } from "../api/types";
import { Difficulty, ErrorText, GraderBadge, MasvsBadge, Panel, Spinner, StateDot } from "../components/ui";
import { TargetAppCard } from "../components/TargetAppCard";

export function DashboardPage() {
  const [map, setMap] = useState<SkillMap | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    api.skillMap().then(setMap).catch((e) => setError(e.message));
  }, []);

  const modules = useMemo(() => groupByModule(map?.nodes ?? []), [map]);
  const passed = map?.nodes.filter((n) => n.state === "passed").length ?? 0;
  const total = map?.nodes.length ?? 0;
  const recommended = map?.nodes.find((n) => n.id === map?.recommended_task_id) ?? null;

  if (error) return <ErrorText>{error}</ErrorText>;
  if (!map) return <Spinner label="loading skill map…" />;

  return (
    <div className="space-y-8">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold text-zinc-100">Skill map</h1>
          <p className="mt-1 text-sm text-zinc-500">
            Work the path top to bottom. Each task is graded on a real Android emulator.
          </p>
        </div>
        <div className="font-mono text-sm text-zinc-400">
          <span className="text-phosphor">{passed}</span> / {total} cleared
        </div>
      </div>

      {recommended && (
        <Link to={`/tasks/${recommended.id}`} className="block">
          <div className="panel flex items-center justify-between gap-4 border-phosphor/40 p-5 shadow-glow transition-colors hover:border-phosphor">
            <div>
              <p className="font-mono text-[11px] uppercase tracking-widest text-phosphor-dim">
                recommended next
              </p>
              <p className="mt-1 text-lg font-semibold text-zinc-100">{recommended.title}</p>
              <div className="mt-2 flex flex-wrap items-center gap-2">
                {recommended.masvs.map((c) => (
                  <MasvsBadge key={c} control={c} />
                ))}
                <GraderBadge type={recommended.success_type} />
                <Difficulty level={recommended.difficulty} />
              </div>
            </div>
            <span className="btn-primary shrink-0">Start →</span>
          </div>
        </Link>
      )}

      <TargetAppCard />

      <div className="space-y-6">
        {modules.map(([moduleId, nodes]) => (
          <Panel key={moduleId}>
            <h2 className="mb-4 flex items-center gap-2 font-mono text-sm uppercase tracking-wider text-zinc-500">
              <span className="text-phosphor-dim">module {moduleId}</span>
              <span className="text-zinc-700">·</span>
              <span className="text-zinc-600">{nodes[0]?.domain}</span>
            </h2>
            <ul className="space-y-2">
              {nodes.map((node) => (
                <NodeRow key={node.id} node={node} />
              ))}
            </ul>
          </Panel>
        ))}
      </div>
    </div>
  );
}

function NodeRow({ node }: { node: SkillNode }) {
  // Every task is freely navigable — jump straight to any module. The state dot
  // still shows progress (passed / available / not-yet-recommended); we just
  // never lock or grey out a row.
  const body = (
    <div
      className="flex items-center gap-3 rounded-md border border-ink-500 bg-ink-700/40 px-4 py-3 transition-colors hover:border-phosphor/40"
    >
      <StateDot state={node.state} />
      <div className="min-w-0 flex-1">
        <div className="flex items-center gap-2">
          <span className="truncate text-sm font-medium text-zinc-100">{node.title}</span>
          {node.is_reference && (
            <span className="font-mono text-[10px] text-signal-amber" title="reference task">
              ★
            </span>
          )}
        </div>
        <div className="mt-1.5 flex flex-wrap items-center gap-2">
          {node.masvs.map((c) => (
            <MasvsBadge key={c} control={c} />
          ))}
          <GraderBadge type={node.success_type} />
        </div>
      </div>
      <div className="flex items-center gap-4">
        <Difficulty level={node.difficulty} />
        {node.state === "passed" && (
          <span className="font-mono text-xs text-phosphor">{node.best_score} pts</span>
        )}
      </div>
    </div>
  );
  return (
    <li>
      <Link to={`/tasks/${node.id}`}>{body}</Link>
    </li>
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
