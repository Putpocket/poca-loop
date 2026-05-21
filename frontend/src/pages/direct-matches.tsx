import { useQuery } from "@tanstack/react-query";
import { Repeat2 } from "lucide-react";
import { EmptyState, ErrorState, LoadingState } from "../components/state-blocks";
import { Badge } from "../components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { api, DirectMatch, getFriendlyError } from "../lib/api";

export function DirectMatchesPage() {
  const query = useQuery({ queryKey: ["directMatches"], queryFn: api.directMatches });

  return (
    <div className="grid gap-4">
      <div>
        <h1 className="text-xl font-semibold text-slate-950">1:1 매칭</h1>
        <p className="mt-1 text-sm text-slate-500">서로의 Want를 바로 교환할 수 있는 후보입니다.</p>
      </div>
      {query.isLoading ? <LoadingState /> : null}
      {query.isError ? <ErrorState message={getFriendlyError(query.error)} /> : null}
      {query.data?.length === 0 ? <EmptyState title="아직 1:1 매칭이 없습니다." description="Have와 Want를 더 채우면 후보가 생길 수 있습니다." /> : null}
      <div className="grid gap-3">
        {query.data?.map((match, index) => <DirectMatchCard key={`${match.user_b.id}-${index}`} match={match} />)}
      </div>
    </div>
  );
}

function DirectMatchCard({ match }: { match: DirectMatch }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Repeat2 size={18} />
          @{match.user_b.username}
        </CardTitle>
      </CardHeader>
      <CardContent className="grid gap-4 sm:grid-cols-2">
        <TradePanel title="내가 주는 카드" card={match.user_a_gives.photocard.name} grade={match.user_a_gives.condition_grade.code} />
        <TradePanel title="내가 받는 카드" card={match.user_a_receives.photocard.name} grade={match.user_a_receives.condition_grade.code} />
      </CardContent>
    </Card>
  );
}

function TradePanel({ title, card, grade }: { title: string; card: string; grade: string }) {
  return (
    <div className="rounded-md border border-slate-200 p-3">
      <p className="text-sm text-slate-500">{title}</p>
      <p className="mt-1 font-medium text-slate-950">{card}</p>
      <Badge className="mt-2">{grade}</Badge>
    </div>
  );
}
