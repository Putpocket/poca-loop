import { useQuery } from "@tanstack/react-query";
import { ShieldCheck } from "lucide-react";
import { EmptyState, ErrorState, LoadingState } from "../components/state-blocks";
import { Alert } from "../components/ui/alert";
import { Badge } from "../components/ui/badge";
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
  const query = useQuery({
    queryKey: ["adminPendingPhotocards"],
    queryFn: () => api.adminPendingPhotocards()
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
        이번 화면은 조회 전용입니다. 승인, 병합, 거절은 다음 단계에서 지원 예정이며 아직 실행되지 않습니다.
      </Alert>

      {query.isLoading ? <LoadingState /> : null}
      {query.isError ? (
        <ErrorState message={needsAdmin ? "관리자 권한이 필요합니다." : getFriendlyError(query.error)} />
      ) : null}
      {query.data?.length === 0 ? (
        <EmptyState title="검토할 임시 포카가 없습니다." description="새 임시 포카가 등록되면 이곳에 표시됩니다." />
      ) : null}

      <div className="grid gap-3">
        {query.data?.map((item) => <PendingPhotocardReviewCard key={item.id} item={item} />)}
      </div>
    </div>
  );
}

function PendingPhotocardReviewCard({ item }: { item: PendingPhotocard }) {
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
            <Badge>{item.catalog_status}</Badge>
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
        <div className="flex flex-wrap gap-2">
          <Badge>승인 예정</Badge>
          <Badge>병합 예정</Badge>
          <Badge>거절 예정</Badge>
        </div>
        <p className="text-xs text-slate-500">승인/병합/거절 작업은 다음 단계에서 지원 예정입니다.</p>
      </CardContent>
    </Card>
  );
}
