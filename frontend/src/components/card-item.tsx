import { UserHave, UserWant } from "../lib/api";
import { releaseSourceSummary } from "../lib/release-source";
import { Badge } from "./ui/badge";
import { Card, CardContent } from "./ui/card";

export function HaveCardItem({ item }: { item: UserHave }) {
  return (
    <Card>
      <CardContent className="grid gap-2">
        <div className="flex items-start justify-between gap-3">
          <div>
            <p className="font-medium text-slate-950">{item.photocard.name}</p>
            <p className="text-sm text-slate-500">Photocard #{item.photocard.id}</p>
            <p className="mt-1 text-xs text-slate-500">
              릴리즈/출처: {item.photocard.release?.title ?? "미지정"}
            </p>
            <p className="text-xs text-slate-500">{releaseSourceSummary(item.photocard.release)}</p>
          </div>
          <Badge>{item.condition_grade.code}</Badge>
        </div>
        {item.note ? <p className="text-sm text-slate-600">{item.note}</p> : null}
      </CardContent>
    </Card>
  );
}

export function WantCardItem({ item }: { item: UserWant }) {
  return (
    <Card>
      <CardContent className="grid gap-2">
        <div className="flex items-start justify-between gap-3">
          <div>
            <p className="font-medium text-slate-950">{item.photocard.name}</p>
            <p className="text-sm text-slate-500">Photocard #{item.photocard.id}</p>
            <p className="mt-1 text-xs text-slate-500">
              릴리즈/출처: {item.photocard.release?.title ?? "미지정"}
            </p>
            <p className="text-xs text-slate-500">{releaseSourceSummary(item.photocard.release)}</p>
          </div>
          <Badge>{item.minimum_condition_grade?.code ?? "ANY"}</Badge>
        </div>
        {item.note ? <p className="text-sm text-slate-600">{item.note}</p> : null}
      </CardContent>
    </Card>
  );
}
