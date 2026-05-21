import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ShieldCheck } from "lucide-react";
import { useState } from "react";
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
  const groups = useQuery({ queryKey: ["groups"], queryFn: api.groups });
  const members = useQuery({ queryKey: ["members"], queryFn: api.members });
  const releases = useQuery({ queryKey: ["releases"], queryFn: api.releases });
  const rejectMutation = useMutation({
    mutationFn: ({ id, reason }: { id: number; reason?: string | null }) =>
      api.rejectPendingPhotocard(id, { reason }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["adminPendingPhotocards"] });
    }
  });
  const approveMutation = useMutation({
    mutationFn: ({
      id,
      payload
    }: {
      id: number;
      payload: Parameters<typeof api.approvePendingPhotocard>[1];
    }) => api.approvePendingPhotocard(id, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["adminPendingPhotocards"] });
      queryClient.invalidateQueries({ queryKey: ["photocards"] });
      queryClient.invalidateQueries({ queryKey: ["haves"] });
      queryClient.invalidateQueries({ queryKey: ["wants"] });
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
      {approveMutation.isError ? (
        <Alert className="border-red-200 bg-red-50 text-red-700">{getFriendlyError(approveMutation.error)}</Alert>
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
            groups={groups.data ?? []}
            members={members.data ?? []}
            releases={releases.data ?? []}
            rejecting={rejectMutation.isPending}
            approving={approveMutation.isPending}
            onReject={(reason) => rejectMutation.mutate({ id: item.id, reason })}
            onApprove={(payload) => approveMutation.mutate({ id: item.id, payload })}
          />
        ))}
      </div>
    </div>
  );
}

function PendingPhotocardReviewCard({
  item,
  groups,
  members,
  releases,
  rejecting,
  approving,
  onApprove,
  onReject
}: {
  item: PendingPhotocard;
  groups: Array<{ id: number; name: string }>;
  members: Array<{ id: number; group_id: number; name: string; stage_name: string | null }>;
  releases: Array<{ id: number; group_id: number; title: string }>;
  rejecting: boolean;
  approving: boolean;
  onApprove: (payload: Parameters<typeof api.approvePendingPhotocard>[1]) => void;
  onReject: (reason?: string | null) => void;
}) {
  const [showApproveForm, setShowApproveForm] = useState(false);
  const [approveDraft, setApproveDraft] = useState({
    group_id: item.group_id ? String(item.group_id) : "",
    member_id: item.member_id ? String(item.member_id) : "",
    release_id: "",
    name: item.card_description,
    version: item.version ?? "",
    notes: compactParts([
      `source: ${item.source_title}`,
      item.retailer_or_event,
      item.venue,
      item.round,
      item.detail
    ]),
    reason: ""
  });
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
  const isApproved = item.catalog_status === "approved";
  const availableMembers = members.filter((member) => !approveDraft.group_id || member.group_id === Number(approveDraft.group_id));
  const availableReleases = releases.filter((release) => !approveDraft.group_id || release.group_id === Number(approveDraft.group_id));

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
        {isRejected ? (
          <div className="rounded-md bg-amber-50 p-3 text-sm text-amber-900">
            <p className="font-medium">카탈로그 반영 거절</p>
            {item.review_reason ? <p className="mt-1">사유: {item.review_reason}</p> : null}
            {item.reviewed_at ? <p className="mt-1 text-xs">처리일: {formatDate(item.reviewed_at)}</p> : null}
          </div>
        ) : null}
        {isApproved ? (
          <div className="rounded-md bg-green-50 p-3 text-sm text-green-800">
            <p className="font-medium">승인됨</p>
            <p className="mt-1">정식 Photocard #{item.approved_photocard_id}</p>
            {item.review_reason ? <p className="mt-1">사유: {item.review_reason}</p> : null}
          </div>
        ) : null}
        <div className="flex flex-wrap items-center gap-2">
          <Button
            type="button"
            variant="secondary"
            disabled={approving || isRejected || isApproved}
            onClick={() => setShowApproveForm((value) => !value)}
          >
            새 정식 포카로 승인
          </Button>
          <Button type="button" variant="danger" disabled={rejecting || isRejected || isApproved} onClick={reject}>
            {isRejected ? "거절됨" : rejecting ? "거절 중" : "거절"}
          </Button>
          <Badge>병합 다음 단계 예정</Badge>
        </div>
        {showApproveForm && !isRejected && !isApproved ? (
          <form
            className="grid gap-3 rounded-md border border-slate-200 p-3"
            onSubmit={(event) => {
              event.preventDefault();
              onApprove({
                group_id: Number(approveDraft.group_id),
                member_id: Number(approveDraft.member_id),
                release_id: approveDraft.release_id ? Number(approveDraft.release_id) : null,
                name: approveDraft.name,
                version: approveDraft.version || null,
                notes: approveDraft.notes || null,
                reason: approveDraft.reason || null
              });
            }}
          >
            <div className="grid gap-2 sm:grid-cols-3">
              <label className="grid gap-1 text-xs text-slate-500">
                그룹
                <select
                  className="rounded-md border border-slate-200 px-3 py-2 text-sm text-slate-950"
                  required
                  value={approveDraft.group_id}
                  onChange={(event) =>
                    setApproveDraft((current) => ({ ...current, group_id: event.target.value, member_id: "", release_id: "" }))
                  }
                >
                  <option value="">선택</option>
                  {groups.map((groupItem) => (
                    <option key={groupItem.id} value={groupItem.id}>
                      {groupItem.name}
                    </option>
                  ))}
                </select>
              </label>
              <label className="grid gap-1 text-xs text-slate-500">
                멤버
                <select
                  className="rounded-md border border-slate-200 px-3 py-2 text-sm text-slate-950"
                  required
                  value={approveDraft.member_id}
                  onChange={(event) => setApproveDraft((current) => ({ ...current, member_id: event.target.value }))}
                >
                  <option value="">선택</option>
                  {availableMembers.map((member) => (
                    <option key={member.id} value={member.id}>
                      {member.stage_name ?? member.name}
                    </option>
                  ))}
                </select>
              </label>
              <label className="grid gap-1 text-xs text-slate-500">
                릴리즈/출처
                <select
                  className="rounded-md border border-slate-200 px-3 py-2 text-sm text-slate-950"
                  value={approveDraft.release_id}
                  onChange={(event) => setApproveDraft((current) => ({ ...current, release_id: event.target.value }))}
                >
                  <option value="">미지정</option>
                  {availableReleases.map((release) => (
                    <option key={release.id} value={release.id}>
                      {release.title}
                    </option>
                  ))}
                </select>
              </label>
            </div>
            <div className="grid gap-2 sm:grid-cols-2">
              <label className="grid gap-1 text-xs text-slate-500">
                포토카드명
                <input
                  className="rounded-md border border-slate-200 px-3 py-2 text-sm text-slate-950"
                  required
                  value={approveDraft.name}
                  onChange={(event) => setApproveDraft((current) => ({ ...current, name: event.target.value }))}
                />
              </label>
              <label className="grid gap-1 text-xs text-slate-500">
                버전
                <input
                  className="rounded-md border border-slate-200 px-3 py-2 text-sm text-slate-950"
                  value={approveDraft.version}
                  onChange={(event) => setApproveDraft((current) => ({ ...current, version: event.target.value }))}
                />
              </label>
            </div>
            <label className="grid gap-1 text-xs text-slate-500">
              notes
              <textarea
                className="min-h-20 rounded-md border border-slate-200 px-3 py-2 text-sm text-slate-950"
                value={approveDraft.notes}
                onChange={(event) => setApproveDraft((current) => ({ ...current, notes: event.target.value }))}
              />
            </label>
            <label className="grid gap-1 text-xs text-slate-500">
              승인 사유
              <input
                className="rounded-md border border-slate-200 px-3 py-2 text-sm text-slate-950"
                value={approveDraft.reason}
                onChange={(event) => setApproveDraft((current) => ({ ...current, reason: event.target.value }))}
              />
            </label>
            <Button type="submit" disabled={approving}>
              {approving ? "승인 중" : "승인 저장"}
            </Button>
          </form>
        ) : null}
        <p className="text-xs text-slate-500">승인하면 새 정식 Photocard가 생성되고 기존 Have/Want는 정식 포카로 이전됩니다. 병합 작업은 다음 단계에서 지원 예정입니다.</p>
      </CardContent>
    </Card>
  );
}
