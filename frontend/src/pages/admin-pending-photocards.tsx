import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ShieldCheck } from "lucide-react";
import { useState } from "react";
import { EmptyState, ErrorState, LoadingState } from "../components/state-blocks";
import { Alert } from "../components/ui/alert";
import { Badge } from "../components/ui/badge";
import { Button } from "../components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../components/ui/card";
import { api, getFriendlyError, PendingPhotocard, Photocard } from "../lib/api";
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
  const photocards = useQuery({ queryKey: ["photocards"], queryFn: api.photocards });
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
  const mergeMutation = useMutation({
    mutationFn: ({
      id,
      payload
    }: {
      id: number;
      payload: Parameters<typeof api.mergePendingPhotocard>[1];
    }) => api.mergePendingPhotocard(id, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["adminPendingPhotocards"] });
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
        승인과 병합은 Have/Want를 정식 Photocard로 이전합니다.
      </Alert>
      {rejectMutation.isError ? (
        <Alert className="border-red-200 bg-red-50 text-red-700">{getFriendlyError(rejectMutation.error)}</Alert>
      ) : null}
      {approveMutation.isError ? (
        <Alert className="border-red-200 bg-red-50 text-red-700">{getFriendlyError(approveMutation.error)}</Alert>
      ) : null}
      {mergeMutation.isError ? (
        <Alert className="border-red-200 bg-red-50 text-red-700">{getFriendlyError(mergeMutation.error)}</Alert>
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
            photocards={photocards.data ?? []}
            rejecting={rejectMutation.isPending}
            approving={approveMutation.isPending}
            merging={mergeMutation.isPending}
            onReject={(reason) => rejectMutation.mutate({ id: item.id, reason })}
            onApprove={(payload) => approveMutation.mutate({ id: item.id, payload })}
            onMerge={(payload) => mergeMutation.mutate({ id: item.id, payload })}
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
  photocards,
  rejecting,
  approving,
  merging,
  onApprove,
  onMerge,
  onReject
}: {
  item: PendingPhotocard;
  groups: Array<{ id: number; name: string }>;
  members: Array<{ id: number; group_id: number; name: string; stage_name: string | null }>;
  releases: Array<{ id: number; group_id: number; title: string }>;
  photocards: Photocard[];
  rejecting: boolean;
  approving: boolean;
  merging: boolean;
  onApprove: (payload: Parameters<typeof api.approvePendingPhotocard>[1]) => void;
  onMerge: (payload: Parameters<typeof api.mergePendingPhotocard>[1]) => void;
  onReject: (reason?: string | null) => void;
}) {
  const [showApproveForm, setShowApproveForm] = useState(false);
  const [showMergeForm, setShowMergeForm] = useState(false);
  const [mergeSearch, setMergeSearch] = useState("");
  const [mergeDraft, setMergeDraft] = useState({
    photocard_id: "",
    reason: ""
  });
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
  const isMerged = item.catalog_status === "merged";
  const isTerminal = isRejected || isApproved || isMerged;
  const availableMembers = members.filter((member) => !approveDraft.group_id || member.group_id === Number(approveDraft.group_id));
  const availableReleases = releases.filter((release) => !approveDraft.group_id || release.group_id === Number(approveDraft.group_id));
  const groupById = new Map(groups.map((group) => [group.id, group.name]));
  const memberById = new Map(members.map((member) => [member.id, member.stage_name ?? member.name]));
  const releaseById = new Map(releases.map((release) => [release.id, release.title]));
  const photocardOptions = photocards
    .map((photocard) => ({
      item: photocard,
      label: compactParts([
        groupById.get(photocard.group_id) ?? `Group #${photocard.group_id}`,
        memberById.get(photocard.member_id) ?? `Member #${photocard.member_id}`,
        photocard.release_id ? releaseById.get(photocard.release_id) ?? `Release #${photocard.release_id}` : "릴리즈 미지정",
        photocard.name,
        photocard.version ? `ver. ${photocard.version}` : null
      ])
    }))
    .filter(({ label }) => label.toLowerCase().includes(mergeSearch.trim().toLowerCase()))
    .slice(0, 80);

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
        {isMerged ? (
          <div className="rounded-md bg-sky-50 p-3 text-sm text-sky-800">
            <p className="font-medium">병합됨</p>
            <p className="mt-1">정식 Photocard #{item.merged_photocard_id}</p>
            {item.review_reason ? <p className="mt-1">사유: {item.review_reason}</p> : null}
            {item.reviewed_at ? <p className="mt-1 text-xs">처리일: {formatDate(item.reviewed_at)}</p> : null}
          </div>
        ) : null}
        <div className="flex flex-wrap items-center gap-2">
          <Button
            type="button"
            variant="secondary"
            disabled={approving || isTerminal}
            onClick={() => setShowApproveForm((value) => !value)}
          >
            새 정식 포카로 승인
          </Button>
          <Button
            type="button"
            variant="secondary"
            disabled={merging || isTerminal}
            onClick={() => setShowMergeForm((value) => !value)}
          >
            기존 포카에 병합
          </Button>
          <Button type="button" variant="danger" disabled={rejecting || isTerminal} onClick={reject}>
            {isRejected ? "거절됨" : rejecting ? "거절 중" : "거절"}
          </Button>
        </div>
        {showApproveForm && !isTerminal ? (
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
        {showMergeForm && !isTerminal ? (
          <form
            className="grid gap-3 rounded-md border border-slate-200 p-3"
            onSubmit={(event) => {
              event.preventDefault();
              onMerge({
                photocard_id: Number(mergeDraft.photocard_id),
                reason: mergeDraft.reason || null
              });
            }}
          >
            <label className="grid gap-1 text-xs text-slate-500">
              정식 Photocard 검색
              <input
                className="rounded-md border border-slate-200 px-3 py-2 text-sm text-slate-950"
                placeholder="그룹, 멤버, 릴리즈, 포카명으로 검색"
                value={mergeSearch}
                onChange={(event) => setMergeSearch(event.target.value)}
              />
            </label>
            <label className="grid gap-1 text-xs text-slate-500">
              병합 대상
              <select
                className="rounded-md border border-slate-200 px-3 py-2 text-sm text-slate-950"
                required
                value={mergeDraft.photocard_id}
                onChange={(event) => setMergeDraft((current) => ({ ...current, photocard_id: event.target.value }))}
              >
                <option value="">선택</option>
                {photocardOptions.map(({ item: photocard, label }) => (
                  <option key={photocard.id} value={photocard.id}>
                    {label}
                  </option>
                ))}
              </select>
            </label>
            <label className="grid gap-1 text-xs text-slate-500">
              병합 사유
              <input
                className="rounded-md border border-slate-200 px-3 py-2 text-sm text-slate-950"
                value={mergeDraft.reason}
                onChange={(event) => setMergeDraft((current) => ({ ...current, reason: event.target.value }))}
              />
            </label>
            <Button type="submit" disabled={merging}>
              {merging ? "병합 중" : "병합 저장"}
            </Button>
          </form>
        ) : null}
        <p className="text-xs text-slate-500">승인하면 새 정식 Photocard가 생성되고, 병합하면 기존 정식 Photocard로 Have/Want가 이전됩니다.</p>
      </CardContent>
    </Card>
  );
}
