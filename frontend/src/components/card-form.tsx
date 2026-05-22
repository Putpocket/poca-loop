import { useQueries } from "@tanstack/react-query";
import { Search } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { api, Group, Member, PendingPhotocard, Photocard, Release } from "../lib/api";
import { releaseSourceSummary, sourceTypeLabel } from "../lib/release-source";
import { cn } from "../lib/utils";
import { Button } from "./ui/button";
import { Input } from "./ui/input";
import { Select } from "./ui/select";

export type CardFormValues = {
  photocard_id?: number;
  pending_photocard_id?: number;
  grade_id: number;
  note?: string;
};

export type CardFormInitialValues = {
  photocard_id?: number | null;
  pending_photocard_id?: number | null;
  grade_id: number | null;
  note?: string | null;
};

type CatalogChoice<T> = {
  item: T;
  title: string;
  subtitle?: string;
  meta?: string;
};

type CardChoice =
  | CatalogChoice<Photocard> & { kind: "official" }
  | CatalogChoice<PendingPhotocard> & { kind: "pending" };

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
  const [pendingPhotocardId, setPendingPhotocardId] = useState<number | null>(null);
  const [gradeId, setGradeId] = useState("");
  const [note, setNote] = useState("");
  const [queries, setQueries] = useState({ group: "", member: "", release: "", photocard: "" });
  const [showPendingForm, setShowPendingForm] = useState(false);
  const [pendingDraft, setPendingDraft] = useState({
    group: "",
    member: "",
    source_type: "other",
    source_title: "",
    retailer_or_event: "",
    venue: "",
    round: "",
    detail: "",
    card_description: "",
    version: "",
    memo: ""
  });
  const [pendingError, setPendingError] = useState<string | null>(null);

  const [
    groupsQuery,
    membersQuery,
    releasesQuery,
    photocardsQuery,
    pendingPhotocardsQuery,
    gradesQuery
  ] = useQueries({
    queries: [
      { queryKey: ["catalog", "groups"], queryFn: api.groups },
      { queryKey: ["catalog", "members"], queryFn: api.members },
      { queryKey: ["catalog", "releases"], queryFn: api.releases },
      { queryKey: ["catalog", "photocards"], queryFn: api.photocards },
      { queryKey: ["pendingPhotocards"], queryFn: api.pendingPhotocards },
      { queryKey: ["conditionGrades"], queryFn: api.conditionGrades }
    ]
  });

  const groups = groupsQuery.data ?? [];
  const members = membersQuery.data ?? [];
  const releases = releasesQuery.data ?? [];
  const photocards = photocardsQuery.data ?? [];
  const pendingPhotocards = pendingPhotocardsQuery.data ?? [];
  const grades = gradesQuery.data ?? [];
  const selectedGroup = groups.find((group) => group.id === groupId);
  const selectedMember = members.find((member) => member.id === memberId);
  const selectedRelease = releases.find((release) => release.id === releaseId);
  const selectedPhotocard = photocards.find((card) => card.id === photocardId);
  const selectedPendingPhotocard = pendingPhotocards.find((card) => card.id === pendingPhotocardId);

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

  const photocardChoices = useMemo<CardChoice[]>(
    () => {
      const officialChoices: CardChoice[] = photocards
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
            kind: "official",
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
        });
      const pendingChoices: CardChoice[] = pendingPhotocards
        .filter((card) => (groupId ? card.group_id === groupId || card.group_name === selectedGroup?.name : true))
        .filter((card) => (memberId ? card.member_id === memberId || card.member_name === selectedMember?.name : true))
        .filter((card) => (releaseId ? card.source_title === selectedRelease?.title : true))
        .filter((card) =>
          includesText(
            compactParts([
              card.group_name ?? selectedGroup?.name,
              card.member_name ?? selectedMember?.name,
              card.source_title,
              sourceTypeLabel(card.source_type),
              card.card_description,
              card.version
            ]),
            queries.photocard
          )
        )
        .map((card) => ({
          kind: "pending",
          item: card,
          title: card.card_description,
          subtitle: compactParts([
            card.group_name ?? selectedGroup?.name,
            card.member_name ?? selectedMember?.name,
            card.source_title,
            sourceTypeLabel(card.source_type)
          ]),
          meta: compactParts(["임시 등록 항목", card.version ? `ver. ${card.version}` : null])
        }));
      return [...officialChoices, ...pendingChoices];
    },
    [
      groupById,
      groupId,
      memberById,
      memberId,
      pendingPhotocards,
      photocards,
      queries.photocard,
      releaseById,
      releaseId,
      selectedGroup?.name,
      selectedMember?.name,
      selectedRelease?.title
    ]
  );

  const loading =
    groupsQuery.isLoading ||
    membersQuery.isLoading ||
    releasesQuery.isLoading ||
    photocardsQuery.isLoading ||
    pendingPhotocardsQuery.isLoading ||
    gradesQuery.isLoading;
  const error =
    groupsQuery.error ||
    membersQuery.error ||
    releasesQuery.error ||
    photocardsQuery.error ||
    pendingPhotocardsQuery.error ||
    gradesQuery.error;
  const canSubmit = Boolean((photocardId || pendingPhotocardId) && gradeId) && !pending;

  useEffect(() => {
    if (!initialValues) return;
    setGradeId(initialValues.grade_id ? String(initialValues.grade_id) : "");
    setNote(initialValues.note ?? "");
    if (initialValues.photocard_id && photocards.length) {
      const card = photocards.find((item) => item.id === initialValues.photocard_id);
      setPhotocardId(initialValues.photocard_id);
      setPendingPhotocardId(null);
      if (card) {
        setGroupId(card.group_id);
        setMemberId(card.member_id);
        setReleaseId(card.release_id);
      }
    }
    if (initialValues.pending_photocard_id && pendingPhotocards.length) {
      const card = pendingPhotocards.find((item) => item.id === initialValues.pending_photocard_id);
      setPhotocardId(null);
      setPendingPhotocardId(initialValues.pending_photocard_id);
      if (card) {
        setGroupId(card.group_id);
        setMemberId(card.member_id);
        const release = releases.find((item) => item.title === card.source_title);
        setReleaseId(release?.id ?? null);
      }
    }
  }, [initialValues, pendingPhotocards, photocards, releases]);

  function selectGroup(group: Group) {
    setGroupId(group.id);
    setMemberId(null);
    setReleaseId(null);
    setPhotocardId(null);
    setPendingPhotocardId(null);
    setQueries((current) => ({ ...current, group: "", member: "", release: "", photocard: "" }));
  }

  function selectMember(member: Member) {
    setMemberId(member.id);
    setPhotocardId(null);
    setPendingPhotocardId(null);
    setQueries((current) => ({ ...current, member: "", photocard: "" }));
  }

  function selectRelease(release: Release) {
    setReleaseId(release.id);
    setPhotocardId(null);
    setPendingPhotocardId(null);
    setQueries((current) => ({ ...current, release: "", photocard: "" }));
    setPendingDraft((current) => ({
      ...current,
      group: selectedGroup?.name ?? current.group,
      member: selectedMember?.name ?? current.member,
      source_type: release.source_type,
      source_title: release.title,
      retailer_or_event: release.retailer_or_event ?? "",
      venue: release.venue ?? "",
      round: release.round ?? "",
      detail: release.detail ?? ""
    }));
  }

  function resetAfterSubmit() {
    setPhotocardId(null);
    setPendingPhotocardId(null);
    setGradeId("");
    setNote("");
  }

  function selectCardChoice(choice: CardChoice) {
    if (choice.kind === "official") {
      setPhotocardId(choice.item.id);
      setPendingPhotocardId(null);
      setQueries((current) => ({ ...current, photocard: "" }));
      return;
    }
    setPhotocardId(null);
    setPendingPhotocardId(choice.item.id);
    setQueries((current) => ({ ...current, photocard: "" }));
  }

  async function createPendingPhotocard() {
    if (!pendingDraft.source_title.trim() || !pendingDraft.card_description.trim()) {
      setPendingError("릴리즈/출처명과 카드 설명은 필수입니다.");
      return;
    }
    setPendingError(null);
    try {
      const pendingCard = await api.createPendingPhotocard({
        group_id: selectedGroup?.id,
        group_name: pendingDraft.group || selectedGroup?.name,
        member_id: selectedMember?.id,
        member_name: pendingDraft.member || selectedMember?.name,
        source_type: pendingDraft.source_type,
        source_title: pendingDraft.source_title,
        retailer_or_event: pendingDraft.retailer_or_event || undefined,
        venue: pendingDraft.venue || undefined,
        round: pendingDraft.round || undefined,
        detail: pendingDraft.detail || undefined,
        card_description: pendingDraft.card_description,
        version: pendingDraft.version || undefined,
        memo: pendingDraft.memo || undefined
      });
      await pendingPhotocardsQuery.refetch();
      setPhotocardId(null);
      setPendingPhotocardId(pendingCard.id);
      setShowPendingForm(false);
    } catch (error) {
      setPendingError(error instanceof Error ? error.message : "임시 포카를 등록하지 못했습니다.");
    }
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
        if ((!photocardId && !pendingPhotocardId) || !gradeId) return;
        onSubmit({
          photocard_id: photocardId ?? undefined,
          pending_photocard_id: pendingPhotocardId ?? undefined,
          grade_id: Number(gradeId),
          note: note || undefined
        });
        if (resetOnSubmit) {
          resetAfterSubmit();
        }
      }}
    >
      <div className="grid gap-3 sm:grid-cols-2">
        <ChoiceStep
          title="1. 그룹"
          query={queries.group}
          onQueryChange={(value) => setQueries((current) => ({ ...current, group: value }))}
          choices={groupChoices}
          selectedChoice={
            selectedGroup ? { item: selectedGroup, title: selectedGroup.name, subtitle: selectedGroup.slug } : null
          }
          selectedId={groupId}
          onSelect={(choice) => selectGroup(choice.item)}
          emptyText="검색된 그룹이 없습니다."
        />

        <ChoiceStep
          title="2. 멤버"
          query={queries.member}
          onQueryChange={(value) => setQueries((current) => ({ ...current, member: value }))}
          choices={memberChoices}
          selectedChoice={
            selectedMember
              ? {
                  item: selectedMember,
                  title: selectedMember.name,
                  subtitle: selectedMember.stage_name ?? selectedGroup?.name
                }
              : null
          }
          selectedId={memberId}
          onSelect={(choice) => selectMember(choice.item)}
          disabled={!selectedGroup}
          emptyText={selectedGroup ? "검색된 멤버가 없습니다." : "먼저 그룹을 선택하세요."}
        />
      </div>

      <ChoiceStep
        title="3. 릴리즈/출처"
        query={queries.release}
        onQueryChange={(value) => setQueries((current) => ({ ...current, release: value }))}
        choices={releaseChoices}
        selectedChoice={
          selectedRelease
            ? {
                item: selectedRelease,
                title: selectedRelease.title,
                subtitle: releaseSourceSummary(selectedRelease),
                meta: sourceTypeLabel(selectedRelease.source_type)
              }
            : null
        }
        selectedId={releaseId}
        onSelect={(choice) => selectRelease(choice.item)}
        disabled={!selectedGroup}
        emptyText={selectedGroup ? "검색된 릴리즈/출처가 없습니다." : "먼저 그룹을 선택하세요."}
      />

      <ChoiceStep
        title="4. 포토카드"
        query={queries.photocard}
        onQueryChange={(value) => setQueries((current) => ({ ...current, photocard: value }))}
        choices={photocardChoices}
        selectedChoice={
          selectedPhotocard
            ? {
                kind: "official",
                item: selectedPhotocard,
                title: selectedPhotocard.name,
                subtitle: compactParts([selectedGroup?.name, selectedMember?.name, selectedRelease?.title]),
                meta: selectedPhotocard.version ? `ver. ${selectedPhotocard.version}` : undefined
              }
            : selectedPendingPhotocard
              ? {
                  kind: "pending",
                  item: selectedPendingPhotocard,
                  title: selectedPendingPhotocard.card_description,
                  subtitle: compactParts([
                    selectedPendingPhotocard.group_name ?? selectedGroup?.name,
                    selectedPendingPhotocard.member_name ?? selectedMember?.name,
                    selectedPendingPhotocard.source_title
                  ]),
                  meta: "임시 등록 항목"
                }
              : null
        }
        selectedId={photocardId ?? pendingPhotocardId}
        onSelect={selectCardChoice}
        disabled={!selectedMember || !selectedRelease}
        emptyText={
          selectedMember && selectedRelease
            ? "조건에 맞는 포토카드가 없습니다."
            : "멤버와 릴리즈/출처를 선택하세요."
        }
      />

      {selectedMember && selectedRelease && photocardChoices.length === 0 ? (
        <div className="grid gap-2 rounded-md border border-amber-200 bg-amber-50 p-3">
          <p className="text-sm text-amber-900">
            찾는 포카가 없으면 사진 없이 텍스트로 임시 등록할 수 있어요. 임시 등록 항목은 매칭에서 제한될 수 있습니다.
          </p>
          <Button
            type="button"
            variant="secondary"
            onClick={() => {
              setPendingDraft((current) => ({
                ...current,
                group: selectedGroup?.name ?? current.group,
                member: selectedMember?.name ?? current.member,
                source_type: selectedRelease?.source_type ?? current.source_type,
                source_title: selectedRelease?.title ?? current.source_title,
                card_description: queries.photocard || current.card_description
              }));
              setShowPendingForm((value) => !value);
            }}
          >
            카탈로그에 없는 포카로 임시 등록
          </Button>
        </div>
      ) : null}

      {showPendingForm ? (
        <PendingPhotocardForm
          draft={pendingDraft}
          error={pendingError}
          onChange={(field, value) => setPendingDraft((current) => ({ ...current, [field]: value }))}
          onSubmit={createPendingPhotocard}
          onCancel={() => setShowPendingForm(false)}
        />
      ) : null}

      <div className="grid gap-3 sm:grid-cols-[minmax(0,0.9fr)_minmax(0,1.1fr)]">
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
      </div>

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

function ChoiceStep<T extends CatalogChoice<{ id: number }>>({
  title,
  query,
  onQueryChange,
  choices,
  selectedChoice,
  selectedId,
  onSelect,
  disabled,
  emptyText
}: {
  title: string;
  query: string;
  onQueryChange: (value: string) => void;
  choices: T[];
  selectedChoice?: T | null;
  selectedId: number | null;
  onSelect: (choice: T) => void;
  disabled?: boolean;
  emptyText: string;
}) {
  const [editing, setEditing] = useState(false);
  const [focused, setFocused] = useState(false);
  const visibleChoices = choices.slice(0, 20);
  const showChoices = !disabled && (editing || focused || Boolean(query));
  const inputValue = editing || focused ? query : selectedChoice?.title ?? query;

  useEffect(() => {
    if (!selectedId) setEditing(false);
  }, [selectedId]);

  return (
    <section className={cn("grid gap-2", disabled && "opacity-60")}>
      <div className="flex h-5 items-center">
        <h3 className="truncate text-sm font-semibold leading-5 text-slate-800">{title}</h3>
      </div>
      <div className="relative">
        <label className="relative block">
          <Search className="pointer-events-none absolute left-3 top-2.5 text-slate-400" size={16} />
          <Input
            className="pl-9"
            placeholder={disabled ? "이전 단계 필요" : "검색"}
            value={inputValue}
            disabled={disabled}
            onFocus={() => {
              setFocused(true);
              setEditing(true);
              onQueryChange("");
            }}
            onBlur={() => {
              window.setTimeout(() => {
                setFocused(false);
                if (!query) setEditing(false);
              }, 120);
            }}
            onChange={(event) => {
              setEditing(true);
              onQueryChange(event.target.value);
            }}
          />
        </label>
        {showChoices ? (
          <div className="absolute left-0 right-0 top-full z-20 mt-2 grid max-h-56 gap-2 overflow-y-auto rounded-md border border-slate-200 bg-white p-2 shadow-lg">
            {visibleChoices.length ? (
              visibleChoices.map((choice) => (
                <button
                  type="button"
                  key={choice.item.id}
                  onMouseDown={(event) => event.preventDefault()}
                  onClick={() => {
                    onSelect(choice);
                    setEditing(false);
                    setFocused(false);
                  }}
                  className={cn(
                    "rounded-md border bg-white p-2.5 text-left transition hover:border-slate-300 hover:bg-slate-50",
                    selectedId === choice.item.id ? "border-slate-900 ring-2 ring-slate-100" : "border-slate-200"
                  )}
                >
                  <span className="block truncate text-sm font-medium text-slate-950">{choice.title}</span>
                  {choice.subtitle ? <span className="mt-1 block truncate text-xs text-slate-500">{choice.subtitle}</span> : null}
                  {choice.meta ? <span className="mt-1 inline-flex text-xs text-slate-600">{choice.meta}</span> : null}
                </button>
              ))
            ) : (
              <p className="px-2 py-3 text-sm text-slate-500">{emptyText}</p>
            )}
            {choices.length > visibleChoices.length ? (
              <p className="px-2 py-1 text-xs text-slate-500">검색어를 더 입력하면 결과를 좁힐 수 있습니다.</p>
            ) : null}
          </div>
        ) : null}
      </div>
    </section>
  );
}

function PendingPhotocardForm({
  draft,
  error,
  onChange,
  onSubmit,
  onCancel
}: {
  draft: {
    group: string;
    member: string;
    source_type: string;
    source_title: string;
    retailer_or_event: string;
    venue: string;
    round: string;
    detail: string;
    card_description: string;
    version: string;
    memo: string;
  };
  error: string | null;
  onChange: (field: keyof typeof draft, value: string) => void;
  onSubmit: () => void;
  onCancel: () => void;
}) {
  return (
    <div className="grid gap-3 rounded-md border border-slate-200 bg-white p-3">
      <div>
        <p className="text-sm font-semibold text-slate-900">임시 포카 등록</p>
        <p className="mt-1 text-xs text-slate-500">
          사진은 업로드하지 않습니다. 임시 등록 항목은 정식 반영 전까지 매칭에서 제한될 수 있어요.
        </p>
      </div>
      {error ? <p className="rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">{error}</p> : null}
      <div className="grid gap-2 sm:grid-cols-2">
        <Input placeholder="그룹" value={draft.group} onChange={(event) => onChange("group", event.target.value)} />
        <Input placeholder="멤버" value={draft.member} onChange={(event) => onChange("member", event.target.value)} />
        <Select value={draft.source_type} onChange={(event) => onChange("source_type", event.target.value)}>
          <option value="album">릴리즈</option>
          <option value="preorder_benefit">POB</option>
          <option value="store_benefit">스토어 특전</option>
          <option value="lucky_draw">럭드</option>
          <option value="fansign">팬싸</option>
          <option value="broadcast">공방</option>
          <option value="popup">팝업</option>
          <option value="concert">콘서트</option>
          <option value="fanmeeting">팬미팅</option>
          <option value="merch">MD</option>
          <option value="event">이벤트</option>
          <option value="other">기타</option>
        </Select>
        <Input
          placeholder="대략적인 릴리즈/출처명"
          value={draft.source_title}
          onChange={(event) => onChange("source_title", event.target.value)}
        />
        <Input
          placeholder="판매처/이벤트"
          value={draft.retailer_or_event}
          onChange={(event) => onChange("retailer_or_event", event.target.value)}
        />
        <Input placeholder="장소" value={draft.venue} onChange={(event) => onChange("venue", event.target.value)} />
        <Input placeholder="회차" value={draft.round} onChange={(event) => onChange("round", event.target.value)} />
        <Input placeholder="상세 설명" value={draft.detail} onChange={(event) => onChange("detail", event.target.value)} />
        <Input
          placeholder="카드 설명"
          value={draft.card_description}
          onChange={(event) => onChange("card_description", event.target.value)}
        />
        <Input placeholder="버전" value={draft.version} onChange={(event) => onChange("version", event.target.value)} />
      </div>
      <Input placeholder="메모" value={draft.memo} onChange={(event) => onChange("memo", event.target.value)} />
      <div className="flex flex-col gap-2 sm:flex-row">
        <Button type="button" onClick={onSubmit}>
          임시 등록 후 선택
        </Button>
        <Button type="button" variant="secondary" onClick={onCancel}>
          취소
        </Button>
      </div>
    </div>
  );
}
