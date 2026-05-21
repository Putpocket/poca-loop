import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ShieldCheck } from "lucide-react";
import { EmptyState, ErrorState, LoadingState } from "../components/state-blocks";
import { Alert } from "../components/ui/alert";
import { Badge } from "../components/ui/badge";
import { Button } from "../components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../components/ui/card";
import { api, getFriendlyError, PendingPhotocard } from "../lib/api";
import { sourceTypeLabel } from "../lib/release-source";

function compactParts(parts: Array<string | number | null | undefined>) {
  return parts.filter((part) => part !== null && part !== undefined && String(part).trim() !== "").join(" · ");
}

function formatDate(value: string) {
  return new Intl.DateTimeFormat("ko-KR", {
    dateStyle: "medium",
    timeStyle: "short"
  }).format(new Date(value));
}

export function AdminPendingPhotocardsPage() {
  const queryClient = useQueryClient();
  const query = useQuery({
    queryKey: ["adminPendingPhotocards"],
    queryFn: () => api.adminPendingPhotocards()
  });
  const rejectMutation = useMutation({
    mutationFn: ({ id, reason }: { id: number; reason?: string | null }) =>
      api.rejectPendingPhotocard(id, { reason }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["adminPendingPhotocards"] });
    }
  });
  const errorMessage = query.isError ? getFriendlyError(query.error) : "";
  const needsAdmin = errorMessage.includes("Admin permission");

  return (
    <div className="grid gap-4">
      <div>
        <h1 className="text-xl font-semibold text-slate-950">임시 포카 검토</h1>
        <p className="mt-1 text-sm text-slate-500">사용자가 사진 없이 등록한 카탈로그 승인 대기 항목입니다.</p>
      </div>

      <Alert className="bg-amber-50 text-amber-900">
        거절은 임시 포카를 정식 카탈로그에 반영하지 않는다는 표시만 남깁니다. 사용자의 Have/Want는 자동 삭제되지 않습니다.
        승인과 병합은 다음 단계에서 지원 예정입니다.
      </Alert>
      {rejectMutation.isError ? (
        <Alert className="border-red-200 bg-red-50 text-red-700">{getFriendlyError(rejectMutation.error)}</Alert>
      ) : null}

      {query.isLoading ? <LoadingState /> : null}
      {query.isError ? (
        <ErrorState message={needsAdmin ? "관리자 권한이 필요합니다." : getFriendlyError(query.error)} />
      ) : null}
      {query.data?.length === 0 ? (
        <EmptyState title="검토할 임시 포카가 없습니다." description="새 임시 포카가 등록되면 이곳에 표시됩니다." />
      ) : null}

      <div className="grid gap-3">
        {query.data?.map((item) => (
          <PendingPhotocardReviewCard
            key={item.id}
            item={item}
            rejecting={rejectMutation.isPending}
            onReject={(reason) => rejectMutation.mutate({ id: item.id, reason })}
          />
        ))}
      </div>
    </div>
  );
}

function PendingPhotocardReviewCard({
  item,
  rejecting,
  onReject
}: {
  item: PendingPhotocard;
  rejecting: boolean;
  onReject: (reason?: string | null) => void;
}) {
  const group = item.group_name ?? (item.group_id ? `Group #${item.group_id}` : "그룹 미지정");
  const member = item.member_name ?? (item.member_id ? `Member #${item.member_id}` : "멤버 미지정");
  const source = compactParts([
    sourceTypeLabel(item.source_type),
    item.source_title,
    item.retailer_or_event,
    item.venue,
    item.country,
    item.round,
    item.detail
  ]);
  const isRejected = item.catalog_status === "rejected";

  function reject() {
    if (isRejected) return;
    const reason = window.prompt("거절 사유를 입력하세요. 비워두면 사유 없이 거절합니다.");
    if (reason === null) return;
    onReject(reason.trim() || null);
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
          <div>
            <CardTitle className="flex items-center gap-2">
              <ShieldCheck size={18} />
              {item.card_description}
            </CardTitle>
            <CardDescription>{compactParts([group, member, item.version ? `ver. ${item.version}` : null])}</CardDescription>
          </div>
          <div className="flex flex-wrap gap-2">
            <Badge>#{item.id}</Badge>
            <Badge>{isRejected ? "rejected" : "pending"}</Badge>
          </div>
        </div>
      </CardHeader>
      <CardContent className="grid gap-3 text-sm">
        <div>
          <p className="text-slate-500">릴리즈/출처</p>
          <p className="mt-1 font-medium text-slate-950">{source || "출처 미지정"}</p>
        </div>
        {item.memo ? (
          <div>
            <p className="text-slate-500">메모</p>
            <p className="mt-1 text-slate-700">{item.memo}</p>
          </div>
        ) : null}
        <div className="grid gap-2 rounded-md bg-slate-50 p-3 text-xs text-slate-600 sm:grid-cols-3">
          <span>등록자 ID: {item.created_by_user_id}</span>
          <span>등록일: {formatDate(item.created_at)}</span>
          <span>수정일: {formatDate(item.updated_at)}</span>
        </div>
        {isRejected ? (
          <div className="rounded-md bg-amber-50 p-3 text-sm text-amber-900">
            <p className="font-medium">카탈로그 반영 거절</p>
            {item.review_reason ? <p className="mt-1">사유: {item.review_reason}</p> : null}
            {item.reviewed_at ? <p className="mt-1 text-xs">처리일: {formatDate(item.reviewed_at)}</p> : null}
          </div>
        ) : null}
        <div className="flex flex-wrap items-center gap-2">
          <Button type="button" variant="danger" disabled={rejecting || isRejected} onClick={reject}>
            {isRejected ? "거절됨" : rejecting ? "거절 중" : "거절"}
          </Button>
          <Badge>승인 다음 단계 예정</Badge>
          <Badge>병합 다음 단계 예정</Badge>
        </div>
        <p className="text-xs text-slate-500">거절은 Have/Want를 삭제하지 않습니다. 승인/병합 작업은 다음 단계에서 지원 예정입니다.</p>
      </CardContent>
    </Card>
  );
}
