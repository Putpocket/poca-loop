import { useQuery } from "@tanstack/react-query";
import { ArrowRightLeft, Search } from "lucide-react";
import { useState } from "react";
import { Link } from "react-router-dom";
import { EmptyState, ErrorState, LoadingState } from "../components/state-blocks";
import { Alert } from "../components/ui/alert";
import { Badge } from "../components/ui/badge";
import { Button } from "../components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { Select } from "../components/ui/select";
import { api, ExploreCardEntry, ExploreCardFilters, getFriendlyError } from "../lib/api";

const sourceTypes = [
  "album",
  "preorder_benefit",
  "store_benefit",
  "lucky_draw",
  "fansign",
  "broadcast",
  "popup",
  "concert",
  "fanmeeting",
  "merch",
  "season_greeting",
  "fanclub",
  "collab",
  "magazine",
  "event",
  "other"
];

export function ExplorePage() {
  const groups = useQuery({ queryKey: ["groups"], queryFn: api.groups });
  const members = useQuery({ queryKey: ["members"], queryFn: api.members });
  const releases = useQuery({ queryKey: ["releases"], queryFn: api.releases });
  const photocards = useQuery({ queryKey: ["photocards"], queryFn: api.photocards });
  const [filters, setFilters] = useState<ExploreCardFilters>({ limit: 50 });
  const query = useQuery({ queryKey: ["exploreCards", filters], queryFn: () => api.exploreCards(filters) });

  const groupMembers = members.data?.filter((member) => !filters.group_id || member.group_id === filters.group_id) ?? [];
  const groupReleases = releases.data?.filter((release) => !filters.group_id || release.group_id === filters.group_id) ?? [];
  const filteredPhotocards =
    photocards.data?.filter((card) => {
      if (filters.group_id && card.group_id !== filters.group_id) return false;
      if (filters.member_id && card.member_id !== filters.member_id) return false;
      if (filters.release_id && card.release_id !== filters.release_id) return false;
      return true;
    }) ?? [];

  function patchFilters(next: Partial<ExploreCardFilters>) {
    setFilters((current) => ({ ...current, ...next }));
  }

  function clearFilters() {
    setFilters({ limit: 50 });
  }

  return (
    <div className="grid gap-4">
      <div>
        <h1 className="text-xl font-semibold text-slate-950">교환 탐색</h1>
        <p className="mt-1 text-sm text-slate-500">로그인한 사용자만 볼 수 있는 정식 포카 Have/Want 목록입니다.</p>
      </div>

      <Alert className="bg-amber-50 text-amber-900">
        이 목록은 연락이나 거래 중개가 아니라 탐색용입니다. 임시 포카는 정식 승인 또는 병합 전까지 표시되지 않으며, 연락처와 거래 버튼은 제공하지 않습니다.
      </Alert>

      <Card>
        <CardContent className="grid gap-3">
          <div className="flex flex-wrap gap-2">
            <Button
              variant={filters.entry_type === undefined ? "primary" : "secondary"}
              onClick={() => patchFilters({ entry_type: undefined })}
            >
              전체
            </Button>
            <Button
              variant={filters.entry_type === "have" ? "primary" : "secondary"}
              onClick={() => patchFilters({ entry_type: "have" })}
            >
              Have
            </Button>
            <Button
              variant={filters.entry_type === "want" ? "primary" : "secondary"}
              onClick={() => patchFilters({ entry_type: "want" })}
            >
              Want
            </Button>
          </div>

          <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
            <Select
              value={filters.group_id ?? ""}
              onChange={(event) =>
                patchFilters({
                  group_id: numberOrUndefined(event.target.value),
                  member_id: undefined,
                  release_id: undefined,
                  photocard_id: undefined
                })
              }
            >
              <option value="">전체 그룹</option>
              {groups.data?.map((group) => (
                <option key={group.id} value={group.id}>
                  {group.name}
                </option>
              ))}
            </Select>
            <Select
              value={filters.member_id ?? ""}
              onChange={(event) =>
                patchFilters({ member_id: numberOrUndefined(event.target.value), photocard_id: undefined })
              }
            >
              <option value="">전체 멤버</option>
              {groupMembers.map((member) => (
                <option key={member.id} value={member.id}>
                  {member.stage_name ?? member.name}
                </option>
              ))}
            </Select>
            <Select
              value={filters.release_id ?? ""}
              onChange={(event) =>
                patchFilters({ release_id: numberOrUndefined(event.target.value), photocard_id: undefined })
              }
            >
              <option value="">전체 릴리즈/출처</option>
              {groupReleases.map((release) => (
                <option key={release.id} value={release.id}>
                  {release.title}
                </option>
              ))}
            </Select>
            <Select
              value={filters.photocard_id ?? ""}
              onChange={(event) => patchFilters({ photocard_id: numberOrUndefined(event.target.value) })}
            >
              <option value="">전체 포카</option>
              {filteredPhotocards.map((card) => (
                <option key={card.id} value={card.id}>
                  {card.name}
                  {card.version ? ` (${card.version})` : ""}
                </option>
              ))}
            </Select>
            <Select
              value={filters.source_type ?? ""}
              onChange={(event) => patchFilters({ source_type: event.target.value || undefined })}
            >
              <option value="">전체 출처 유형</option>
              {sourceTypes.map((sourceType) => (
                <option key={sourceType} value={sourceType}>
                  {sourceType}
                </option>
              ))}
            </Select>
            <Select
              value={filters.limit ?? 50}
              onChange={(event) => patchFilters({ limit: numberOrUndefined(event.target.value) ?? 50 })}
            >
              <option value="25">25개</option>
              <option value="50">50개</option>
              <option value="100">100개</option>
            </Select>
          </div>

          <div className="flex flex-col gap-2 sm:flex-row">
            <Button onClick={() => void query.refetch()} disabled={query.isFetching}>
              <Search size={16} />
              다시 조회
            </Button>
            <Button variant="secondary" onClick={clearFilters}>
              필터 초기화
            </Button>
            <Link
              to="/matches/direct"
              className="inline-flex h-10 items-center justify-center gap-2 rounded-md px-4 text-sm font-medium text-slate-700 transition hover:bg-slate-100"
            >
              <ArrowRightLeft size={16} />
              내 매칭 보기
            </Link>
          </div>
        </CardContent>
      </Card>

      {query.isLoading ? <LoadingState /> : null}
      {query.isError ? <ErrorState message={getFriendlyError(query.error)} /> : null}
      {query.data?.length === 0 ? <EmptyState title="탐색 목록이 비어 있습니다." description="정식 포카 기반 Have/Want가 등록되면 여기에 표시됩니다." /> : null}

      <div className="grid gap-3 sm:grid-cols-2">
        {query.data?.map((item, index) => (
          <ExploreCard key={`${item.entry_type}-${item.username}-${item.photocard.id}-${index}`} item={item} />
        ))}
      </div>
    </div>
  );
}

function ExploreCard({ item }: { item: ExploreCardEntry }) {
  const releaseParts = [
    item.release_source?.title,
    item.release_source?.retailer_or_event,
    item.release_source?.round,
    item.release_source?.detail
  ].filter(Boolean);
  const grade = item.entry_type === "have" ? item.condition_grade?.code : item.minimum_condition_grade?.code;

  return (
    <Card>
      <CardHeader>
        <div className="flex items-start justify-between gap-3">
          <div>
            <CardTitle className="text-base">{item.photocard.name}</CardTitle>
            <p className="mt-1 text-sm text-slate-500">@{item.username}</p>
          </div>
          <Badge>{item.entry_type === "have" ? "Have" : "Want"}</Badge>
        </div>
      </CardHeader>
      <CardContent className="grid gap-2 text-sm">
        <Info label="그룹" value={item.group.name} />
        <Info label="멤버" value={item.member.stage_name ?? item.member.name} />
        <Info label="릴리즈/출처" value={releaseParts.join(" / ") || "미지정"} />
        <Info label="출처 유형" value={item.release_source?.source_type ?? "미지정"} />
        <Info label="버전" value={item.photocard.version ?? "미지정"} />
        <Info label={item.entry_type === "have" ? "상태 등급" : "최소 등급"} value={grade ?? "ANY"} />
      </CardContent>
    </Card>
  );
}

function Info({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-start justify-between gap-3">
      <span className="text-slate-500">{label}</span>
      <span className="text-right font-medium text-slate-900">{value}</span>
    </div>
  );
}

function numberOrUndefined(value: string) {
  if (!value) return undefined;
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : undefined;
}
