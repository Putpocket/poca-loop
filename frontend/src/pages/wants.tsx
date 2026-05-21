import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { CardForm, type CardFormValues } from "../components/card-form";
import { WantCardItem } from "../components/card-item";
import { ConditionGuide } from "../components/condition-guide";
import { EmptyState, ErrorState, LoadingState } from "../components/state-blocks";
import { Alert } from "../components/ui/alert";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../components/ui/card";
import { api, getFriendlyError } from "../lib/api";

export function WantsPage() {
  const queryClient = useQueryClient();
  const wants = useQuery({ queryKey: ["wants"], queryFn: api.wants });
  const mutation = useMutation({
    mutationFn: (values: CardFormValues) =>
      api.addWant({
        photocard_id: values.photocard_id,
        minimum_condition_grade_id: values.grade_id,
        note: values.note || undefined
      }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["wants"] })
  });

  return (
    <div className="grid gap-4 lg:grid-cols-[360px_1fr]">
      <Card>
        <CardHeader>
          <CardTitle>원하는 카드 추가</CardTitle>
          <CardDescription>받고 싶은 카드를 검색/선택하고 최소 허용 등급을 등록합니다.</CardDescription>
        </CardHeader>
        <CardContent className="grid gap-3">
          {mutation.isError ? <Alert className="border-red-200 bg-red-50 text-red-700">{getFriendlyError(mutation.error)}</Alert> : null}
          <CardForm mode="want" pending={mutation.isPending} onSubmit={(values) => mutation.mutate(values)} />
          <ConditionGuide />
        </CardContent>
      </Card>

      <section className="grid gap-3">
        <div>
          <h1 className="text-xl font-semibold text-slate-950">내 원하는 카드</h1>
          <p className="mt-1 text-sm text-slate-500">매칭에서 받을 후보 카드입니다.</p>
        </div>
        {wants.isLoading ? <LoadingState /> : null}
        {wants.isError ? <ErrorState message={getFriendlyError(wants.error)} /> : null}
        {wants.data?.length === 0 ? <EmptyState title="아직 원하는 카드가 없습니다." description="왼쪽 폼에서 원하는 카드를 추가하세요." /> : null}
        <div className="grid gap-3">
          {wants.data?.map((item) => <WantCardItem key={item.id} item={item} />)}
        </div>
      </section>
    </div>
  );
}
