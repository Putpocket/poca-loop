import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { CardForm, type CardFormValues } from "../components/card-form";
import { HaveCardItem } from "../components/card-item";
import { EmptyState, ErrorState, LoadingState } from "../components/state-blocks";
import { Alert } from "../components/ui/alert";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../components/ui/card";
import { api, getFriendlyError } from "../lib/api";

export function HavesPage() {
  const queryClient = useQueryClient();
  const haves = useQuery({ queryKey: ["haves"], queryFn: api.haves });
  const mutation = useMutation({
    mutationFn: (values: CardFormValues) =>
      api.addHave({
        photocard_id: values.photocard_id,
        condition_grade_id: values.grade_id,
        note: values.note || undefined
      }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["haves"] })
  });

  return (
    <div className="grid gap-4 lg:grid-cols-[360px_1fr]">
      <Card>
        <CardHeader>
          <CardTitle>보유 카드 추가</CardTitle>
          <CardDescription>현재 카탈로그 ID를 기준으로 등록합니다.</CardDescription>
        </CardHeader>
        <CardContent className="grid gap-3">
          {mutation.isError ? <Alert className="border-red-200 bg-red-50 text-red-700">{getFriendlyError(mutation.error)}</Alert> : null}
          <CardForm mode="have" pending={mutation.isPending} onSubmit={(values) => mutation.mutate(values)} />
        </CardContent>
      </Card>

      <section className="grid gap-3">
        <div>
          <h1 className="text-xl font-semibold text-slate-950">내 보유 카드</h1>
          <p className="mt-1 text-sm text-slate-500">교환에 내놓을 수 있는 카드입니다.</p>
        </div>
        {haves.isLoading ? <LoadingState /> : null}
        {haves.isError ? <ErrorState message={getFriendlyError(haves.error)} /> : null}
        {haves.data?.length === 0 ? <EmptyState title="아직 보유 카드가 없습니다." description="왼쪽 폼에서 첫 카드를 추가하세요." /> : null}
        <div className="grid gap-3">
          {haves.data?.map((item) => <HaveCardItem key={item.id} item={item} />)}
        </div>
      </section>
    </div>
  );
}
