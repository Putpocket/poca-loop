import { useQueries } from "@tanstack/react-query";
import { Search } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { api, Group, Member, Photocard, Release } from "../lib/api";
import { releaseSourceSummary, sourceTypeLabel } from "../lib/release-source";
import { cn } from "../lib/utils";
import { Badge } from "./ui/badge";
import { Button } from "./ui/button";
import { Input } from "./ui/input";
import { Select } from "./ui/select";

export type CardFormValues = {
  photocard_id: number;
  grade_id: number;
  note?: string;
};

export type CardFormInitialValues = {
  photocard_id: number;
  grade_id: number | null;
  note?: string | null;
};

type CatalogChoice<T> = {
  item: T;
  title: string;
  subtitle?: string;
  meta?: string;
};

function includesText(value: string, query: string) {
  return value.toLowerCase().includes(query.trim().toLowerCase());
}

function compactParts(parts: Array<string | null | undefined>) {
  return parts.filter(Boolean).join(" · ");
}

export function CardForm({
  mode,
  pending,
  onSubmit,
  initialValues,
  submitLabel,
  onCancel,
  resetOnSubmit = true
}: {
  mode: "have" | "want";
  pending: boolean;
  onSubmit: (values: CardFormValues) => void;
  initialValues?: CardFormInitialValues;
  submitLabel?: string;
  onCancel?: () => void;
  resetOnSubmit?: boolean;
}) {
  const [groupId, setGroupId] = useState<number | null>(null);
  const [memberId, setMemberId] = useState<number | null>(null);
  const [releaseId, setReleaseId] = useState<number | null>(null);
  const [photocardId, setPhotocardId] = useState<number | null>(null);
  const [gradeId, setGradeId] = useState("");
  const [note, setNote] = useState("");
  const [queries, setQueries] = useState({ group: "", member: "", release: "", photocard: "" });

  const [
    groupsQuery,
    membersQuery,
    releasesQuery,
    photocardsQuery,
    gradesQuery
  ] = useQueries({
    queries: [
      { queryKey: ["catalog", "groups"], queryFn: api.groups },
      { queryKey: ["catalog", "members"], queryFn: api.members },
      { queryKey: ["catalog", "releases"], queryFn: api.releases },
      { queryKey: ["catalog", "photocards"], queryFn: api.photocards },
      { queryKey: ["conditionGrades"], queryFn: api.conditionGrades }
    ]
  });

  const groups = groupsQuery.data ?? [];
  const members = membersQuery.data ?? [];
  const releases = releasesQuery.data ?? [];
  const photocards = photocardsQuery.data ?? [];
  const grades = gradesQuery.data ?? [];
  const selectedGroup = groups.find((group) => group.id === groupId);
  const selectedMember = members.find((member) => member.id === memberId);
  const selectedRelease = releases.find((release) => release.id === releaseId);
  const selectedPhotocard = photocards.find((card) => card.id === photocardId);

  const memberById = useMemo(() => new Map(members.map((member) => [member.id, member])), [members]);
  const groupById = useMemo(() => new Map(groups.map((group) => [group.id, group])), [groups]);
  const releaseById = useMemo(() => new Map(releases.map((release) => [release.id, release])), [releases]);

  const groupChoices = useMemo(
    () =>
      groups
        .filter((group) => includesText(`${group.name} ${group.slug}`, queries.group))
        .map((group) => ({ item: group, title: group.name, subtitle: group.slug })),
    [groups, queries.group]
  );

  const memberChoices = useMemo(
    () =>
      members
        .filter((member) => (groupId ? member.group_id === groupId : true))
        .filter((member) => includesText(`${member.name} ${member.stage_name ?? ""}`, queries.member))
        .map((member) => ({
          item: member,
          title: member.name,
          subtitle: member.stage_name ?? groupById.get(member.group_id)?.name
        })),
    [groupById, groupId, members, queries.member]
  );

  const releaseChoices = useMemo(
    () =>
      releases
        .filter((release) => (groupId ? release.group_id === groupId : true))
        .filter((release) =>
          includesText(
            compactParts([
              release.title,
              sourceTypeLabel(release.source_type),
              release.retailer_or_event,
              release.venue,
              release.round,
              release.detail
            ]),
            queries.release
          )
        )
        .map((release) => ({
          item: release,
          title: release.title,
          subtitle: releaseSourceSummary(release),
          meta: sourceTypeLabel(release.source_type)
        })),
    [groupId, queries.release, releases]
  );

  const photocardChoices = useMemo(
    () =>
      photocards
        .filter((card) => (groupId ? card.group_id === groupId : true))
        .filter((card) => (memberId ? card.member_id === memberId : true))
        .filter((card) => (releaseId ? card.release_id === releaseId : true))
        .filter((card) => {
          const group = groupById.get(card.group_id);
          const member = memberById.get(card.member_id);
          const release = card.release ?? (card.release_id ? releaseById.get(card.release_id) : null);
          return includesText(
            compactParts([
              group?.name,
              member?.name,
              release?.title,
              release ? sourceTypeLabel(release.source_type) : null,
              card.name,
              card.version
            ]),
            queries.photocard
          );
        })
        .map((card) => {
          const group = groupById.get(card.group_id);
          const member = memberById.get(card.member_id);
          const release = card.release ?? (card.release_id ? releaseById.get(card.release_id) : null);
          return {
            item: card,
            title: card.name,
            subtitle: compactParts([
              group?.name,
              member?.name,
              release?.title,
              release ? sourceTypeLabel(release.source_type) : null
            ]),
            meta: card.version ? `ver. ${card.version}` : undefined
          };
        }),
    [groupById, groupId, memberById, memberId, photocards, queries.photocard, releaseById, releaseId]
  );

  const loading =
    groupsQuery.isLoading ||
    membersQuery.isLoading ||
    releasesQuery.isLoading ||
    photocardsQuery.isLoading ||
    gradesQuery.isLoading;
  const error =
    groupsQuery.error ||
    membersQuery.error ||
    releasesQuery.error ||
    photocardsQuery.error ||
    gradesQuery.error;
  const canSubmit = Boolean(photocardId && gradeId) && !pending;

  useEffect(() => {
    if (!initialValues || !photocards.length) return;
    const card = photocards.find((item) => item.id === initialValues.photocard_id);
    setPhotocardId(initialValues.photocard_id);
    setGradeId(initialValues.grade_id ? String(initialValues.grade_id) : "");
    setNote(initialValues.note ?? "");
    if (card) {
      setGroupId(card.group_id);
      setMemberId(card.member_id);
      setReleaseId(card.release_id);
    }
  }, [initialValues, photocards]);

  function selectGroup(group: Group) {
    setGroupId(group.id);
    setMemberId(null);
    setReleaseId(null);
    setPhotocardId(null);
  }

  function selectMember(member: Member) {
    setMemberId(member.id);
    setPhotocardId(null);
  }

  function selectRelease(release: Release) {
    setReleaseId(release.id);
    setPhotocardId(null);
  }

  function resetAfterSubmit() {
    setPhotocardId(null);
    setGradeId("");
    setNote("");
  }

  if (loading) {
    return <p className="rounded-md bg-slate-50 px-3 py-2 text-sm text-slate-500">카탈로그를 불러오는 중입니다.</p>;
  }

  if (error) {
    return <p className="rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">카탈로그를 불러오지 못했습니다.</p>;
  }

  return (
    <form
      className="grid gap-4"
      onSubmit={(event) => {
        event.preventDefault();
        if (!photocardId || !gradeId) return;
        onSubmit({ photocard_id: photocardId, grade_id: Number(gradeId), note: note || undefined });
        if (resetOnSubmit) {
          resetAfterSubmit();
        }
      }}
    >
      <ChoiceStep
        title="1. 그룹 선택"
        query={queries.group}
        onQueryChange={(value) => setQueries((current) => ({ ...current, group: value }))}
        choices={groupChoices}
        selectedId={groupId}
        onSelect={selectGroup}
        emptyText="검색된 그룹이 없습니다."
      />

      <ChoiceStep
        title="2. 멤버 선택"
        query={queries.member}
        onQueryChange={(value) => setQueries((current) => ({ ...current, member: value }))}
        choices={memberChoices}
        selectedId={memberId}
        onSelect={selectMember}
        disabled={!selectedGroup}
        emptyText={selectedGroup ? "검색된 멤버가 없습니다." : "먼저 그룹을 선택하세요."}
      />

      <ChoiceStep
        title="3. 릴리즈/출처 선택"
        query={queries.release}
        onQueryChange={(value) => setQueries((current) => ({ ...current, release: value }))}
        choices={releaseChoices}
        selectedId={releaseId}
        onSelect={selectRelease}
        disabled={!selectedGroup}
        emptyText={selectedGroup ? "검색된 릴리즈/출처가 없습니다." : "먼저 그룹을 선택하세요."}
      />

      <ChoiceStep
        title="4. 포토카드 선택"
        query={queries.photocard}
        onQueryChange={(value) => setQueries((current) => ({ ...current, photocard: value }))}
        choices={photocardChoices}
        selectedId={photocardId}
        onSelect={(card) => setPhotocardId(card.id)}
        disabled={!selectedMember || !selectedRelease}
        emptyText={
          selectedMember && selectedRelease
            ? "조건에 맞는 포토카드가 없습니다."
            : "멤버와 릴리즈/출처를 선택하세요."
        }
      />

      {selectedPhotocard ? (
        <div className="rounded-md border border-slate-200 bg-slate-50 p-3 text-sm">
          <p className="font-medium text-slate-950">선택한 카드: {selectedPhotocard.name}</p>
          <p className="mt-1 text-slate-600">
            {compactParts([
              selectedGroup?.name,
              selectedMember?.name,
              selectedRelease?.title,
              selectedRelease ? sourceTypeLabel(selectedRelease.source_type) : null,
              selectedPhotocard.version
            ])}
          </p>
        </div>
      ) : null}

      <label className="grid gap-1.5">
        <span className="text-sm font-medium text-slate-700">{mode === "have" ? "상태 등급" : "최소 허용 등급"}</span>
        <Select value={gradeId} onChange={(event) => setGradeId(event.target.value)}>
          <option value="">등급 선택</option>
          {grades.map((grade) => (
            <option key={grade.id} value={grade.id}>
              {grade.code} - {grade.label}
            </option>
          ))}
        </Select>
      </label>

      <label className="grid gap-1.5">
        <span className="text-sm font-medium text-slate-700">{mode === "have" ? "메모 / 하자 태그" : "메모"}</span>
        <Input
          placeholder={mode === "have" ? "예: corner ding" : "선택 입력"}
          value={note}
          maxLength={500}
          onChange={(event) => setNote(event.target.value)}
        />
      </label>

      <div className="flex flex-col gap-2 sm:flex-row">
        <Button className="flex-1" disabled={!canSubmit}>
          {pending ? "저장 중" : submitLabel ?? "추가"}
        </Button>
        {onCancel ? (
          <Button type="button" variant="secondary" onClick={onCancel}>
            취소
          </Button>
        ) : null}
      </div>
    </form>
  );
}

function ChoiceStep<T extends { id: number }>({
  title,
  query,
  onQueryChange,
  choices,
  selectedId,
  onSelect,
  disabled,
  emptyText
}: {
  title: string;
  query: string;
  onQueryChange: (value: string) => void;
  choices: Array<CatalogChoice<T>>;
  selectedId: number | null;
  onSelect: (item: T) => void;
  disabled?: boolean;
  emptyText: string;
}) {
  const visibleChoices = choices.slice(0, 20);

  return (
    <section className={cn("grid gap-2", disabled && "opacity-60")}>
      <div className="flex items-center justify-between gap-2">
        <h3 className="text-sm font-semibold text-slate-800">{title}</h3>
        {selectedId ? <Badge>선택됨</Badge> : null}
      </div>
      <label className="relative">
        <Search className="pointer-events-none absolute left-3 top-2.5 text-slate-400" size={16} />
        <Input
          className="pl-9"
          placeholder="검색"
          value={query}
          disabled={disabled}
          onChange={(event) => onQueryChange(event.target.value)}
        />
      </label>
      <div className="grid max-h-72 gap-2 overflow-y-auto rounded-md border border-slate-100 bg-slate-50 p-2">
        {!disabled && visibleChoices.length ? (
          visibleChoices.map((choice) => (
            <button
              type="button"
              key={choice.item.id}
              onClick={() => onSelect(choice.item)}
              className={cn(
                "rounded-md border bg-white p-3 text-left transition hover:border-slate-300 hover:bg-slate-50",
                selectedId === choice.item.id ? "border-slate-900 ring-2 ring-slate-100" : "border-slate-200"
              )}
            >
              <span className="block text-sm font-medium text-slate-950">{choice.title}</span>
              {choice.subtitle ? <span className="mt-1 block text-xs text-slate-500">{choice.subtitle}</span> : null}
              {choice.meta ? <span className="mt-2 inline-flex text-xs text-slate-600">{choice.meta}</span> : null}
            </button>
          ))
        ) : (
          <p className="px-2 py-3 text-sm text-slate-500">{emptyText}</p>
        )}
        {!disabled && choices.length > visibleChoices.length ? (
          <p className="px-2 py-1 text-xs text-slate-500">검색어를 더 입력하면 결과를 좁힐 수 있습니다.</p>
        ) : null}
      </div>
    </section>
  );
}
