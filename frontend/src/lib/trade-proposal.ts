import type { DirectMatch, ThreeWayMatch, User } from "./api";

function cardLabel(card: { name: string; version?: string | null }) {
  return [card.name, card.version].filter(Boolean).join(" / ");
}

export function buildDirectProposalText(match: DirectMatch) {
  return [
    "[poca-loop 교환 제안]",
    "",
    "제가 줄 카드:",
    `${cardLabel(match.user_a_gives.photocard)} / 상태 ${match.user_a_gives.condition_grade.code}`,
    "",
    "제가 받을 카드:",
    `${cardLabel(match.user_a_receives.photocard)} / 상태 ${match.user_a_receives.condition_grade.code}`,
    "",
    "교환 전 실물 사진과 상태를 외부 채팅에서 직접 확인해 주세요.",
    "주소, 계좌, 실명 정보는 poca-loop에 입력하지 마세요.",
    "poca-loop은 거래, 배송, 결제를 중개하지 않는 매칭 보조 도구입니다."
  ].join("\n");
}

export function buildThreeWayProposalText(match: ThreeWayMatch, currentUser?: User | null) {
  const myGive = currentUser ? match.trade_edges.find((edge) => edge.giver.id === currentUser.id) : undefined;
  const myReceive = currentUser ? match.trade_edges.find((edge) => edge.receiver.id === currentUser.id) : undefined;
  const participants = match.participants.map((user) => `@${user.username}`).join(" → ");

  return [
    "[poca-loop 3자 교환 제안]",
    "",
    `참여 후보: ${participants}`,
    "",
    "제가 줄 카드:",
    myGive ? `${cardLabel(myGive.card)} / 상태 ${myGive.condition_grade.code}` : "매칭 화면의 순환 경로를 확인해 주세요.",
    "",
    "제가 받을 카드:",
    myReceive ? `${cardLabel(myReceive.card)} / 상태 ${myReceive.condition_grade.code}` : "매칭 화면의 순환 경로를 확인해 주세요.",
    "",
    "전체 교환 흐름:",
    ...match.trade_edges.map(
      (edge) => `@${edge.giver.username} → @${edge.receiver.username}: ${cardLabel(edge.card)} / 상태 ${edge.condition_grade.code}`
    ),
    "",
    "교환 전 실물 사진과 상태를 외부 채팅에서 직접 확인해 주세요.",
    "주소, 계좌, 실명 정보는 poca-loop에 입력하지 마세요.",
    "poca-loop은 거래, 배송, 결제를 중개하지 않는 매칭 보조 도구입니다."
  ].join("\n");
}

export async function copyTextToClipboard(text: string) {
  if (navigator.clipboard?.writeText) {
    await navigator.clipboard.writeText(text);
    return;
  }

  const textarea = document.createElement("textarea");
  textarea.value = text;
  textarea.setAttribute("readonly", "true");
  textarea.style.position = "fixed";
  textarea.style.left = "-9999px";
  document.body.appendChild(textarea);
  textarea.select();
  const copied = document.execCommand("copy");
  document.body.removeChild(textarea);
  if (!copied) {
    throw new Error("클립보드에 복사하지 못했습니다.");
  }
}
