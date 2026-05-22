import { useQuery } from "@tanstack/react-query";
import { ArrowRightLeft, Check, RotateCcw, Search, SlidersHorizontal, X } from "lucide-react";
import { useState } from "react";
import { Link } from "react-router-dom";
import { EmptyState, ErrorState, LoadingState } from "../components/state-blocks";
import { Alert } from "../components/ui/alert";
import { Badge } from "../components/ui/badge";
import { Button } from "../components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { Input } from "../components/ui/input";
import { api, ExploreCardEntry, ExploreCardFilters, getFriendlyError } from "../lib/api";
import { sourceTypeLabel } from "../lib/release-source";

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
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [queries, setQueries] = useState({ group: "", member: "", release: "", sourceType: "", photocard: "" });
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
  const groupChoices = (groups.data ?? []).map((group) => ({
    id: group.id,
    title: group.name,
    subtitle: group.slug
  }));
  const memberChoices = groupMembers.map((member) => ({
    id: member.id,
    title: member.stage_name ?? member.name,
    subtitle: member.stage_name ? member.name : undefined
  }));
  const releaseChoices = groupReleases.map((release) => ({
    id: release.id,
    title: release.title,
    subtitle: sourceTypeLabel(release.source_type)
  }));
  const sourceTypeChoices = sourceTypes.map((sourceType) => ({
    id: sourceType,
    title: sourceTypeLabel(sourceType),
    subtitle: sourceType
  }));
  const photocardChoices = filteredPhotocards.map((card) => ({
    id: card.id,
    title: card.name,
    subtitle: card.version ? `ver. ${card.version}` : undefined
  }));

  function patchFilters(next: Partial<ExploreCardFilters>) {
    setFilters((current) => ({ ...current, ...next }));
  }

  function clearFilters() {
    setFilters({ limit: 50 });
    setQueries({ group: "", member: "", release: "", sourceType: "", photocard: "" });
  }

  return (
    <div className="grid gap-4">
      <div>
        <h1 className="text-xl font-semibold text-slate-950">교환 탐색</h1>
        <p className="mt-1 text-sm text-slate-500">다른 사용자가 등록한 보유/원하는 포카를 둘러봅니다.</p>
      </div>

      <Alert className="bg-amber-50 text-amber-900">
        정식 등록된 포카만 보여요. 교환 연락은 외부 채널에서 직접 진행해 주세요.
      </Alert>

      <Card>
        <CardContent className="grid gap-4">
          <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            <div className="inline-flex w-fit rounded-full bg-slate-100 p-1">
              <Button
                variant={filters.entry_type === undefined ? "primary" : "ghost"}
                className="h-8 rounded-full px-4"
                onClick={() => patchFilters({ entry_type: undefined })}
              >
                전체
              </Button>
              <Button
                variant={filters.entry_type === "have" ? "primary" : "ghost"}
                className="h-8 rounded-full px-4"
                onClick={() => patchFilters({ entry_type: "have" })}
              >
                Have
              </Button>
              <Button
                variant={filters.entry_type === "want" ? "primary" : "ghost"}
                className="h-8 rounded-full px-4"
                onClick={() => patchFilters({ entry_type: "want" })}
              >
                Want
              </Button>
            </div>
            <button
              type="button"
              className="inline-flex h-9 w-fit items-center justify-center gap-2 rounded-md border border-slate-200 bg-white px-3 text-sm font-medium text-slate-700 transition hover:bg-slate-50 hover:text-slate-950"
              onClick={() => setShowAdvanced((value) => !value)}
            >
              <SlidersHorizontal size={15} />
              {showAdvanced ? "상세 필터 접기" : "상세 필터"}
            </button>
          </div>

          <div className="grid gap-4 rounded-md border border-slate-200 bg-slate-50 p-3">
            <div className="grid gap-3 sm:grid-cols-2">
              <ChoiceFilter
                label="그룹"
                query={queries.group}
                onQueryChange={(value) => setQueries((current) => ({ ...current, group: value }))}
                choices={groupChoices}
                selectedId={filters.group_id}
                placeholder="그룹 검색"
                emptyText="검색된 그룹이 없어요."
                onSelect={(id) =>
                  patchFilters({
                    group_id: Number(id),
                    member_id: undefined,
                    release_id: undefined,
                    photocard_id: undefined
                  })
                }
                onClear={() =>
                  patchFilters({ group_id: undefined, member_id: undefined, release_id: undefined, photocard_id: undefined })
                }
              />
              <ChoiceFilter
                label="멤버"
                query={queries.member}
                onQueryChange={(value) => setQueries((current) => ({ ...current, member: value }))}
                choices={memberChoices}
                selectedId={filters.member_id}
                placeholder="멤버 검색"
                emptyText={filters.group_id ? "검색된 멤버가 없어요." : "그룹을 고르면 더 쉽게 찾을 수 있어요."}
                onSelect={(id) => patchFilters({ member_id: Number(id), photocard_id: undefined })}
                onClear={() => patchFilters({ member_id: undefined, photocard_id: undefined })}
              />
            </div>

            {showAdvanced ? (
              <div className="grid gap-3 border-t border-slate-200 pt-3 sm:grid-cols-2 lg:grid-cols-4">
                <ChoiceFilter
                  label="릴리즈/출처"
                  query={queries.release}
                  onQueryChange={(value) => setQueries((current) => ({ ...current, release: value }))}
                  choices={releaseChoices}
                  selectedId={filters.release_id}
                  placeholder="릴리즈/출처 검색"
                  emptyText="검색된 릴리즈/출처가 없어요."
                  onSelect={(id) => patchFilters({ release_id: Number(id), photocard_id: undefined })}
                  onClear={() => patchFilters({ release_id: undefined, photocard_id: undefined })}
                />
                <ChoiceFilter
                  label="출처 유형"
                  query={queries.sourceType}
                  onQueryChange={(value) => setQueries((current) => ({ ...current, sourceType: value }))}
                  choices={sourceTypeChoices}
                  selectedId={filters.source_type}
                  placeholder="출처 유형 검색"
                  emptyText="검색된 출처 유형이 없어요."
                  onSelect={(id) => patchFilters({ source_type: String(id) })}
                  onClear={() => patchFilters({ source_type: undefined })}
                />
                <ChoiceFilter
                  label="포카"
                  query={queries.photocard}
                  onQueryChange={(value) => setQueries((current) => ({ ...current, photocard: value }))}
                  choices={photocardChoices}
                  selectedId={filters.photocard_id}
                  placeholder="포카 검색"
                  emptyText="검색된 포카가 없어요."
                  onSelect={(id) => patchFilters({ photocard_id: Number(id) })}
                  onClear={() => patchFilters({ photocard_id: undefined })}
                />
                <SegmentedLimit value={filters.limit ?? 50} onChange={(limit) => patchFilters({ limit })} />
              </div>
            ) : null}

            <div className="flex flex-col gap-2 border-t border-slate-200 pt-3 sm:flex-row sm:items-center sm:justify-between">
              <div className="flex flex-col gap-2 sm:flex-row sm:items-center">
                <Button onClick={() => void query.refetch()} disabled={query.isFetching}>
                  <Search size={16} />
                  다시 조회
                </Button>
                <Button variant="ghost" onClick={clearFilters}>
                  <RotateCcw size={16} />
                  필터 초기화
                </Button>
              </div>
              <Link
                to="/matches/direct"
                className="inline-flex h-10 items-center justify-center gap-2 rounded-md border border-slate-200 bg-white px-4 text-sm font-medium text-slate-950 transition hover:bg-slate-50"
              >
                <ArrowRightLeft size={16} />
                내 매칭 보기
              </Link>
            </div>
          </div>
        </CardContent>
      </Card>

      {query.isLoading ? <LoadingState /> : null}
      {query.isError ? <ErrorState message={getFriendlyError(query.error)} /> : null}
      {query.data?.length === 0 ? <EmptyState title="아직 탐색할 포카가 없어요." description="보유 카드나 원하는 카드를 등록하면 여기에 표시됩니다." /> : null}

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

type FilterChoice = {
  id: number | string;
  title: string;
  subtitle?: string;
};

function ChoiceFilter({
  label,
  query,
  onQueryChange,
  choices,
  selectedId,
  placeholder,
  emptyText,
  onSelect,
  onClear
}: {
  label: string;
  query: string;
  onQueryChange: (value: string) => void;
  choices: FilterChoice[];
  selectedId?: number | string;
  placeholder: string;
  emptyText: string;
  onSelect: (id: number | string) => void;
  onClear: () => void;
}) {
  const [isOpen, setIsOpen] = useState(false);
  const selected = choices.find((choice) => String(choice.id) === String(selectedId));
  const visibleChoices = choices
    .filter((choice) => `${choice.title} ${choice.subtitle ?? ""}`.toLowerCase().includes(query.trim().toLowerCase()))
    .slice(0, 5);
  const showList = !selected && (isOpen || query.trim().length > 0);

  return (
    <section className="relative grid gap-2">
      <span className="text-xs font-medium text-slate-500">{label}</span>
      {selected ? (
        <div className="flex h-11 items-center justify-between gap-2 rounded-lg border border-slate-200 bg-white px-3">
          <span className="flex min-w-0 items-baseline gap-2">
            <span className="truncate text-sm font-medium text-slate-950">{selected.title}</span>
            {selected.subtitle ? <span className="truncate text-xs text-slate-500">{selected.subtitle}</span> : null}
          </span>
          <button
            type="button"
            className="rounded-md p-1 text-slate-400 transition hover:bg-slate-100 hover:text-slate-700"
            onClick={onClear}
            aria-label={`${label} 필터 지우기`}
          >
            <X size={15} />
          </button>
        </div>
      ) : (
        <label className="relative">
          <Search className="pointer-events-none absolute left-3 top-3 text-slate-400" size={16} />
          <Input
            className="h-11 rounded-lg bg-white pl-9"
            placeholder={placeholder}
            value={query}
            onFocus={() => setIsOpen(true)}
            onBlur={() => window.setTimeout(() => setIsOpen(false), 120)}
            onChange={(event) => onQueryChange(event.target.value)}
          />
        </label>
      )}

      {showList ? (
        <div className="absolute left-0 right-0 top-full z-20 mt-1 grid max-h-56 gap-1 overflow-y-auto rounded-lg border border-slate-200 bg-white p-1.5 shadow-lg">
          {visibleChoices.length ? (
            visibleChoices.map((choice) => (
              <button
                key={choice.id}
                type="button"
                className="flex items-start justify-between gap-2 rounded-md px-2 py-2 text-left transition hover:bg-slate-50"
                onMouseDown={(event) => {
                  event.preventDefault();
                  onSelect(choice.id);
                  onQueryChange("");
                  setIsOpen(false);
                }}
              >
                <span className="min-w-0">
                  <span className="block truncate text-sm font-medium text-slate-900">{choice.title}</span>
                  {choice.subtitle ? <span className="block truncate text-xs text-slate-500">{choice.subtitle}</span> : null}
                </span>
                <Check size={15} className="mt-0.5 shrink-0 text-slate-300" />
              </button>
            ))
          ) : (
            <p className="px-2 py-3 text-sm text-slate-500">{emptyText}</p>
          )}
        </div>
      ) : null}
    </section>
  );
}

function SegmentedLimit({ value, onChange }: { value: number; onChange: (value: number) => void }) {
  return (
    <section className="grid content-start gap-2">
      <span className="text-xs font-medium text-slate-500">표시 개수</span>
      <div className="inline-flex w-fit rounded-full bg-white p-1">
        {[25, 50, 100].map((limit) => (
          <button
            key={limit}
            type="button"
            className={
              value === limit
                ? "h-8 rounded-full bg-slate-950 px-3 text-sm font-medium text-white"
                : "h-8 rounded-full px-3 text-sm font-medium text-slate-600 transition hover:bg-slate-100"
            }
            onClick={() => onChange(limit)}
          >
            {limit}
          </button>
        ))}
      </div>
    </section>
  );
}

function numberOrUndefined(value: string) {
  if (!value) return undefined;
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : undefined;
}
