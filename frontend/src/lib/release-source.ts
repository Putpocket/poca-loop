import type { Release } from "./api";

const SOURCE_TYPE_LABELS: Record<string, string> = {
  album: "릴리즈",
  preorder_benefit: "POB",
  store_benefit: "스토어 특전",
  lucky_draw: "럭드",
  fansign: "팬싸",
  broadcast: "공방",
  popup: "팝업",
  concert: "콘서트",
  fanmeeting: "팬미팅",
  merch: "MD",
  season_greeting: "시즌그리팅",
  fanclub: "팬클럽",
  collab: "콜라보",
  magazine: "매거진",
  event: "이벤트",
  other: "기타"
};

export function sourceTypeLabel(sourceType?: string | null) {
  if (!sourceType) return "출처 미지정";
  return SOURCE_TYPE_LABELS[sourceType] ?? sourceType;
}

export function releaseSourceSummary(release?: Release | null) {
  if (!release) return "릴리즈/출처 미지정";
  const parts = [
    sourceTypeLabel(release.source_type),
    release.retailer_or_event,
    release.venue,
    release.round,
    release.detail
  ].filter(Boolean);
  return parts.length ? parts.join(" · ") : sourceTypeLabel(release.source_type);
}
