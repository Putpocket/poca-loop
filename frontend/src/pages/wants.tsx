import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { CardForm, type CardFormValues } from "../components/card-form";
import { WantCardItem } from "../components/card-item";
import { ConditionGuide } from "../components/condition-guide";
import { EmptyState, ErrorState, LoadingState } from "../components/state-blocks";
import { Alert } from "../components/ui/alert";
import { Button } from "../components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../components/ui/card";
import { api, getFriendlyError, UserWant } from "../lib/api";

export function WantsPage() {
  const queryClient = useQueryClient();
  const [editing, setEditing] = useState<UserWant | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const wants = useQuery({ queryKey: ["wants"], queryFn: api.wants });
  function refreshUserCards() {
    queryClient.invalidateQueries({ queryKey: ["wants"] });
    queryClient.invalidateQueries({ queryKey: ["directMatches"] });
    queryClient.invalidateQueries({ queryKey: ["threeWayMatches"] });
  }
  const mutation = useMutation({
    mutationFn: (values: CardFormValues) =>
      api.addWant({
        photocard_id: values.photocard_id,
        pending_photocard_id: values.pending_photocard_id,
        minimum_condition_grade_id: values.grade_id,
        note: values.note || undefined
      }),
    onSuccess: () => {
      setMessage("원하는 카드를 추가했습니다.");
      refreshUserCards();
    }
  });
  const updateMutation = useMutation({
    mutationFn: (values: CardFormValues) => {
      if (!editing) throw new Error("수정할 항목이 없습니다.");
      return api.updateWant(editing.id, {
        photocard_id: values.photocard_id,
        pending_photocard_id: values.pending_photocard_id,
        minimum_condition_grade_id: values.grade_id,
        note: values.note ?? null
      });
    },
    onSuccess: () => {
      setEditing(null);
      setMessage("원하는 카드를 수정했습니다.");
      refreshUserCards();
    }
  });
  const deleteMutation = useMutation({
    mutationFn: api.deleteWant,
    onSuccess: () => {
      setMessage("원하는 카드를 삭제했습니다.");
      refreshUserCards();
    }
  });

  return (
    <div className="grid items-start gap-4 lg:grid-cols-[minmax(380px,420px)_minmax(520px,1fr)] xl:grid-cols-[minmax(400px,430px)_minmax(0,1fr)]">
      <Card className="w-full">
        <CardHeader>
          <CardTitle>{editing ? "원하는 카드 수정" : "원하는 카드 추가"}</CardTitle>
          <CardDescription>
            받고 싶은 포카를 검색해 추가합니다. 최소 등급을 고르면 매칭 조건에 반영돼요.
          </CardDescription>
        </CardHeader>
        <CardContent className="grid gap-3">
          {mutation.isError ? <Alert className="border-red-200 bg-red-50 text-red-700">{getFriendlyError(mutation.error)}</Alert> : null}
          {updateMutation.isError ? <Alert className="border-red-200 bg-red-50 text-red-700">{getFriendlyError(updateMutation.error)}</Alert> : null}
          {deleteMutation.isError ? <Alert className="border-red-200 bg-red-50 text-red-700">{getFriendlyError(deleteMutation.error)}</Alert> : null}
          {message ? <Alert className="border-green-200 bg-green-50 text-green-700">{message}</Alert> : null}
          <CardForm
            mode="want"
            pending={mutation.isPending || updateMutation.isPending}
            initialValues={
              editing
                ? {
                    photocard_id: editing.photocard_id,
                    pending_photocard_id: editing.pending_photocard_id,
                    grade_id: editing.minimum_condition_grade_id,
                    note: editing.note
                  }
                : undefined
            }
            submitLabel={editing ? "수정 저장" : "추가"}
            resetOnSubmit={!editing}
            onCancel={editing ? () => setEditing(null) : undefined}
            onSubmit={(values) => (editing ? updateMutation.mutate(values) : mutation.mutate(values))}
          />
          <ConditionGuide compact />
        </CardContent>
      </Card>

      <Card className="min-w-0 self-start lg:min-h-[460px]">
        <CardHeader>
          <CardTitle>내 원하는 카드</CardTitle>
          <CardDescription>매칭에서 받고 싶은 카드입니다.</CardDescription>
        </CardHeader>
        <CardContent className="grid gap-3">
          {wants.isLoading ? <LoadingState /> : null}
          {wants.isError ? <ErrorState message={getFriendlyError(wants.error)} /> : null}
          {wants.data?.length === 0 ? (
            <div className="grid min-h-80 place-items-center gap-3 rounded-md border border-dashed border-slate-200 bg-slate-50 p-6 text-center">
              <EmptyState title="아직 원하는 카드가 없어요." description="받고 싶은 카드를 추가해보세요." />
              <Button className="w-fit" type="button" variant="secondary" onClick={() => window.scrollTo({ top: 0, behavior: "smooth" })}>
                원하는 카드 추가하기
              </Button>
            </div>
          ) : null}
          <div className="grid gap-3">
            {wants.data?.map((item) => (
              <WantCardItem
                key={item.id}
                item={item}
                deleting={deleteMutation.isPending}
                onEdit={() => {
                  setMessage(null);
                  setEditing(item);
                }}
                onDelete={() => {
                  if (!window.confirm("이 원하는 카드를 삭제할까요?")) return;
                  setMessage(null);
                  deleteMutation.mutate(item.id);
                }}
              />
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
