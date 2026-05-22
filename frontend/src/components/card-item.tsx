import { UserHave, UserWant } from "../lib/api";
import { releaseSourceSummary } from "../lib/release-source";
import { Badge } from "./ui/badge";
import { Button } from "./ui/button";
import { Card, CardContent } from "./ui/card";

export function HaveCardItem({
  item,
  onEdit,
  onDelete,
  deleting
}: {
  item: UserHave;
  onEdit?: () => void;
  onDelete?: () => void;
  deleting?: boolean;
}) {
  const cardName = item.photocard?.name ?? item.pending_photocard?.card_description ?? "Unknown card";
  const releaseTitle = item.photocard?.release?.title ?? item.pending_photocard?.source_title ?? "미지정";
  const sourceSummary = item.photocard
    ? releaseSourceSummary(item.photocard.release)
    : [
        item.pending_photocard?.retailer_or_event,
        item.pending_photocard?.venue,
        item.pending_photocard?.round,
        item.pending_photocard?.detail
      ]
        .filter(Boolean)
        .join(" · ");
  const isRejected = item.pending_photocard?.catalog_status === "rejected";
  return (
    <Card>
      <CardContent className="grid gap-2">
        <div className="flex items-start justify-between gap-3">
          <div>
            <p className="font-medium text-slate-950">{cardName}</p>
            <p className="text-sm text-slate-500">
              {item.photocard ? "정식 등록 포카" : "임시 등록 포카"}
            </p>
            <p className="mt-1 text-xs text-slate-500">
              릴리즈/출처: {releaseTitle}
            </p>
            {sourceSummary ? <p className="text-xs text-slate-500">{sourceSummary}</p> : null}
            {item.pending_photocard ? (
              <div className="mt-2 flex flex-wrap gap-2">
                <Badge>{isRejected ? "카탈로그 반영 거절" : "카탈로그 승인 대기"}</Badge>
                <Badge>자동 매칭 제한 가능</Badge>
              </div>
            ) : null}
          </div>
          <Badge>{item.condition_grade.code}</Badge>
        </div>
        {isRejected ? (
          <p className="rounded-md bg-amber-50 px-3 py-2 text-sm text-amber-900">
            이 항목은 정식 카탈로그에 반영되지 않았습니다. 필요하면 삭제하거나 다른 포카로 수정하세요.
          </p>
        ) : null}
        {item.note ? <p className="text-sm text-slate-600">{item.note}</p> : null}
        <div className="flex flex-wrap gap-2 border-t border-slate-100 pt-2">
          <Button type="button" variant="secondary" onClick={onEdit}>
            수정
          </Button>
          <Button type="button" variant="danger" disabled={deleting} onClick={onDelete}>
            {deleting ? "삭제 중" : "삭제"}
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}

export function WantCardItem({
  item,
  onEdit,
  onDelete,
  deleting
}: {
  item: UserWant;
  onEdit?: () => void;
  onDelete?: () => void;
  deleting?: boolean;
}) {
  const cardName = item.photocard?.name ?? item.pending_photocard?.card_description ?? "Unknown card";
  const releaseTitle = item.photocard?.release?.title ?? item.pending_photocard?.source_title ?? "미지정";
  const sourceSummary = item.photocard
    ? releaseSourceSummary(item.photocard.release)
    : [
        item.pending_photocard?.retailer_or_event,
        item.pending_photocard?.venue,
        item.pending_photocard?.round,
        item.pending_photocard?.detail
      ]
        .filter(Boolean)
        .join(" · ");
  const isRejected = item.pending_photocard?.catalog_status === "rejected";
  return (
    <Card>
      <CardContent className="grid gap-2">
        <div className="flex items-start justify-between gap-3">
          <div>
            <p className="font-medium text-slate-950">{cardName}</p>
            <p className="text-sm text-slate-500">
              {item.photocard ? "정식 등록 포카" : "임시 등록 포카"}
            </p>
            <p className="mt-1 text-xs text-slate-500">
              릴리즈/출처: {releaseTitle}
            </p>
            {sourceSummary ? <p className="text-xs text-slate-500">{sourceSummary}</p> : null}
            {item.pending_photocard ? (
              <div className="mt-2 flex flex-wrap gap-2">
                <Badge>{isRejected ? "카탈로그 반영 거절" : "카탈로그 승인 대기"}</Badge>
                <Badge>자동 매칭 제한 가능</Badge>
              </div>
            ) : null}
          </div>
          <Badge>{item.minimum_condition_grade?.code ?? "ANY"}</Badge>
        </div>
        {isRejected ? (
          <p className="rounded-md bg-amber-50 px-3 py-2 text-sm text-amber-900">
            이 항목은 정식 카탈로그에 반영되지 않았습니다. 필요하면 삭제하거나 다른 포카로 수정하세요.
          </p>
        ) : null}
        {item.note ? <p className="text-sm text-slate-600">{item.note}</p> : null}
        <div className="flex flex-wrap gap-2 border-t border-slate-100 pt-2">
          <Button type="button" variant="secondary" onClick={onEdit}>
            수정
          </Button>
          <Button type="button" variant="danger" disabled={deleting} onClick={onDelete}>
            {deleting ? "삭제 중" : "삭제"}
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}
