import { useQuery } from "@tanstack/react-query";
import { Copy, Repeat2 } from "lucide-react";
import { useState } from "react";
import { ConditionGuide } from "../components/condition-guide";
import { EmptyState, ErrorState, LoadingState } from "../components/state-blocks";
import { Alert } from "../components/ui/alert";
import { Badge } from "../components/ui/badge";
import { Button } from "../components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { Toast } from "../components/ui/toast";
import { api, DirectMatch, getFriendlyError } from "../lib/api";
import { buildDirectProposalText, copyTextToClipboard } from "../lib/trade-proposal";

export function DirectMatchesPage() {
  const query = useQuery({ queryKey: ["directMatches"], queryFn: api.directMatches });

  return (
    <div className="grid gap-4">
      <div>
        <h1 className="text-xl font-semibold text-slate-950">1:1 매칭</h1>
        <p className="mt-1 text-sm text-slate-500">서로의 Want를 바로 교환할 수 있는 후보입니다.</p>
      </div>
      <ConditionGuide compact />
      <Alert className="bg-amber-50 text-amber-900">
        poca-loop은 내장 채팅을 제공하지 않습니다. 교환 제안문을 복사한 뒤, 실제 대화와 실물 사진 확인은 사용자가 선택한 외부 채널에서 진행하세요.
        임시 등록 포카는 자동 매칭이 제한될 수 있습니다.
      </Alert>
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
  const [copyState, setCopyState] = useState<"idle" | "success" | "error">("idle");

  async function copyProposal() {
    try {
      await copyTextToClipboard(buildDirectProposalText(match));
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
            <Repeat2 size={18} />
            @{match.user_b.username}
          </CardTitle>
          <Button variant="secondary" onClick={copyProposal}>
            <Copy size={16} />
            교환 제안 복사
          </Button>
        </div>
      </CardHeader>
      <CardContent className="grid gap-4">
        {copyState === "success" ? <Toast>교환 제안문을 복사했습니다.</Toast> : null}
        {copyState === "error" ? <Toast variant="error">클립보드 복사에 실패했습니다.</Toast> : null}
        <div className="grid gap-4 sm:grid-cols-2">
          <TradePanel title="내가 주는 카드" card={match.user_a_gives.photocard.name} grade={match.user_a_gives.condition_grade.code} />
          <TradePanel title="내가 받는 카드" card={match.user_a_receives.photocard.name} grade={match.user_a_receives.condition_grade.code} />
        </div>
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
