import { UserHave, UserWant } from "../lib/api";
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
          </div>
          <Badge>{item.minimum_condition_grade?.code ?? "ANY"}</Badge>
        </div>
        {item.note ? <p className="text-sm text-slate-600">{item.note}</p> : null}
      </CardContent>
    </Card>
  );
}
