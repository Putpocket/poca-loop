import { useQuery } from "@tanstack/react-query";
import { Shuffle } from "lucide-react";
import { EmptyState, ErrorState, LoadingState } from "../components/state-blocks";
import { Badge } from "../components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { api, getFriendlyError, ThreeWayMatch } from "../lib/api";

export function ThreeWayMatchesPage() {
  const query = useQuery({ queryKey: ["threeWayMatches"], queryFn: api.threeWayMatches });

  return (
    <div className="grid gap-4">
      <div>
        <h1 className="text-xl font-semibold text-slate-950">3자 매칭</h1>
        <p className="mt-1 text-sm text-slate-500">A → B → C → A 순환 교환 후보입니다.</p>
      </div>
      {query.isLoading ? <LoadingState /> : null}
      {query.isError ? <ErrorState message={getFriendlyError(query.error)} /> : null}
      {query.data?.length === 0 ? <EmptyState title="아직 3자 매칭이 없습니다." description="더 많은 사용자와 카드 목록이 쌓이면 후보가 생길 수 있습니다." /> : null}
      <div className="grid gap-3">
        {query.data?.map((match, index) => <ThreeWayMatchCard key={index} match={match} />)}
      </div>
    </div>
  );
}

function ThreeWayMatchCard({ match }: { match: ThreeWayMatch }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Shuffle size={18} />
          {match.participants.map((user) => `@${user.username}`).join(" · ")}
        </CardTitle>
      </CardHeader>
      <CardContent className="grid gap-3">
        {match.trade_edges.map((edge, index) => (
          <div key={index} className="rounded-md border border-slate-200 p-3">
            <div className="flex flex-wrap items-center gap-2 text-sm text-slate-500">
              <span>@{edge.giver.username}</span>
              <span>→</span>
              <span>@{edge.receiver.username}</span>
              <Badge>{edge.condition_grade.code}</Badge>
            </div>
            <p className="mt-2 font-medium text-slate-950">{edge.card.name}</p>
            <p className="mt-1 text-sm text-slate-500">
              최소 허용 등급: {edge.receiver_min_condition_grade?.code ?? "ANY"}
            </p>
          </div>
        ))}
      </CardContent>
    </Card>
  );
}
