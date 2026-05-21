import { useQuery } from "@tanstack/react-query";
import { ExternalLink, HeartHandshake, ListChecks, Repeat2, Shuffle } from "lucide-react";
import type { ComponentType } from "react";
import { Link } from "react-router-dom";
import { ErrorState, LoadingState } from "../components/state-blocks";
import { Badge } from "../components/ui/badge";
import { Button } from "../components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../components/ui/card";
import { API_BASE_URL, api, getFriendlyError } from "../lib/api";
import { getToken } from "../lib/auth";

export function DashboardPage() {
  const haves = useQuery({ queryKey: ["haves"], queryFn: api.haves });
  const wants = useQuery({ queryKey: ["wants"], queryFn: api.wants });
  const direct = useQuery({ queryKey: ["directMatches"], queryFn: api.directMatches });
  const threeWay = useQuery({ queryKey: ["threeWayMatches"], queryFn: api.threeWayMatches });

  if (haves.isLoading || wants.isLoading || direct.isLoading || threeWay.isLoading) return <LoadingState />;
  if (haves.isError) return <ErrorState message={getFriendlyError(haves.error)} />;
  if (wants.isError) return <ErrorState message={getFriendlyError(wants.error)} />;
  if (direct.isError) return <ErrorState message={getFriendlyError(direct.error)} />;
  if (threeWay.isError) return <ErrorState message={getFriendlyError(threeWay.error)} />;

  async function openSvgChecklist() {
    const response = await fetch(`${API_BASE_URL}/templates/me.svg`, {
      headers: { Authorization: `Bearer ${getToken() ?? ""}` }
    });
    if (!response.ok) return;
    const blob = await response.blob();
    const url = URL.createObjectURL(blob);
    window.open(url, "_blank", "noopener,noreferrer");
    window.setTimeout(() => URL.revokeObjectURL(url), 60_000);
  }

  return (
    <div className="grid gap-4">
      <section className="rounded-lg border border-slate-200 bg-white p-5">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h1 className="text-2xl font-semibold text-slate-950">Dashboard</h1>
            <p className="mt-1 text-sm text-slate-500">목록을 채우고 가능한 교환 흐름을 확인합니다.</p>
          </div>
          <Button onClick={openSvgChecklist}>
            <ExternalLink size={16} />
            SVG 열기
          </Button>
        </div>
      </section>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <MetricCard icon={ListChecks} label="Have" value={haves.data?.length ?? 0} to="/haves" />
        <MetricCard icon={HeartHandshake} label="Want" value={wants.data?.length ?? 0} to="/wants" />
        <MetricCard icon={Repeat2} label="1:1 matches" value={direct.data?.length ?? 0} to="/matches/direct" />
        <MetricCard icon={Shuffle} label="3-way matches" value={threeWay.data?.length ?? 0} to="/matches/three-way" />
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Next steps</CardTitle>
          <CardDescription>관리자 카탈로그 UI는 아직 없으므로, 등록은 기존 카탈로그 ID를 기준으로 합니다.</CardDescription>
        </CardHeader>
        <CardContent className="grid gap-3 sm:grid-cols-2">
          <LinkCard to="/haves" title="보유 카드 등록" description="내가 줄 수 있는 카드를 상태 등급과 함께 추가합니다." />
          <LinkCard to="/wants" title="원하는 카드 등록" description="받고 싶은 카드와 최소 허용 등급을 추가합니다." />
        </CardContent>
      </Card>
    </div>
  );
}

function MetricCard({ icon: Icon, label, value, to }: { icon: ComponentType<{ size?: number }>; label: string; value: number; to: string }) {
  return (
    <Link to={to}>
      <Card className="transition hover:border-slate-300">
        <CardContent className="flex items-center justify-between">
          <div>
            <p className="text-sm text-slate-500">{label}</p>
            <p className="mt-1 text-3xl font-semibold text-slate-950">{value}</p>
          </div>
          <Badge className="rounded-md p-2">
            <Icon size={18} />
          </Badge>
        </CardContent>
      </Card>
    </Link>
  );
}

function LinkCard({ to, title, description }: { to: string; title: string; description: string }) {
  return (
    <Link to={to} className="rounded-md border border-slate-200 p-4 transition hover:border-slate-300">
      <p className="font-medium text-slate-950">{title}</p>
      <p className="mt-1 text-sm text-slate-500">{description}</p>
    </Link>
  );
}
