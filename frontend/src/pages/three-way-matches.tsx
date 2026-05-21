import { useQuery } from "@tanstack/react-query";
import { Copy, Shuffle } from "lucide-react";
import { useState } from "react";
import { ConditionGuide } from "../components/condition-guide";
import { EmptyState, ErrorState, LoadingState } from "../components/state-blocks";
import { Alert } from "../components/ui/alert";
import { Badge } from "../components/ui/badge";
import { Button } from "../components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { Toast } from "../components/ui/toast";
import { api, getFriendlyError, ThreeWayMatch } from "../lib/api";
import { buildThreeWayProposalText, copyTextToClipboard } from "../lib/trade-proposal";

export function ThreeWayMatchesPage() {
  const query = useQuery({ queryKey: ["threeWayMatches"], queryFn: api.threeWayMatches });
  const me = useQuery({ queryKey: ["me"], queryFn: api.me });

  return (
    <div className="grid gap-4">
      <div>
        <h1 className="text-xl font-semibold text-slate-950">3자 매칭</h1>
        <p className="mt-1 text-sm text-slate-500">A → B → C → A 순환 교환 후보입니다.</p>
      </div>
      <ConditionGuide compact />
      <Alert className="bg-amber-50 text-amber-900">
        poca-loop은 채팅, 거래, 배송, 결제를 중개하지 않습니다. 제안문에는 내부 ID나 이메일을 넣지 않으며, 실제 대화는 외부 채널에서 진행하세요.
        임시 등록 포카는 자동 매칭이 제한될 수 있습니다.
      </Alert>
      {query.isLoading ? <LoadingState /> : null}
      {query.isError ? <ErrorState message={getFriendlyError(query.error)} /> : null}
      {query.data?.length === 0 ? <EmptyState title="아직 3자 매칭이 없습니다." description="더 많은 사용자와 카드 목록이 쌓이면 후보가 생길 수 있습니다." /> : null}
      <div className="grid gap-3">
        {query.data?.map((match, index) => <ThreeWayMatchCard key={index} match={match} currentUser={me.data} />)}
      </div>
    </div>
  );
}

function ThreeWayMatchCard({ match, currentUser }: { match: ThreeWayMatch; currentUser?: { id: number; username: string } }) {
  const [copyState, setCopyState] = useState<"idle" | "success" | "error">("idle");

  async function copyProposal() {
    try {
      await copyTextToClipboard(buildThreeWayProposalText(match, currentUser));
      setCopyState("success");
    } catch {
      setCopyState("error");
    }
    window.setTimeout(() => setCopyState("idle"), 2500);
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <CardTitle className="flex items-center gap-2">
            <Shuffle size={18} />
            {match.participants.map((user) => `@${user.username}`).join(" · ")}
          </CardTitle>
          <Button variant="secondary" onClick={copyProposal}>
            <Copy size={16} />
            교환 제안 복사
          </Button>
        </div>
      </CardHeader>
      <CardContent className="grid gap-3">
        {copyState === "success" ? <Toast>교환 제안문을 복사했습니다.</Toast> : null}
        {copyState === "error" ? <Toast variant="error">클립보드 복사에 실패했습니다.</Toast> : null}
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
