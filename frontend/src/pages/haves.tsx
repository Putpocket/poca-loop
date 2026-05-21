import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { CardForm, type CardFormValues } from "../components/card-form";
import { HaveCardItem } from "../components/card-item";
import { ConditionGuide } from "../components/condition-guide";
import { EmptyState, ErrorState, LoadingState } from "../components/state-blocks";
import { Alert } from "../components/ui/alert";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../components/ui/card";
import { api, getFriendlyError, UserHave } from "../lib/api";

export function HavesPage() {
  const queryClient = useQueryClient();
  const [editing, setEditing] = useState<UserHave | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const haves = useQuery({ queryKey: ["haves"], queryFn: api.haves });
  function refreshUserCards() {
    queryClient.invalidateQueries({ queryKey: ["haves"] });
    queryClient.invalidateQueries({ queryKey: ["directMatches"] });
    queryClient.invalidateQueries({ queryKey: ["threeWayMatches"] });
  }
  const mutation = useMutation({
    mutationFn: (values: CardFormValues) =>
      api.addHave({
        photocard_id: values.photocard_id,
        pending_photocard_id: values.pending_photocard_id,
        condition_grade_id: values.grade_id,
        note: values.note || undefined
      }),
    onSuccess: () => {
      setMessage("보유 카드를 추가했습니다.");
      refreshUserCards();
    }
  });
  const updateMutation = useMutation({
    mutationFn: (values: CardFormValues) => {
      if (!editing) throw new Error("수정할 항목이 없습니다.");
      return api.updateHave(editing.id, {
        photocard_id: values.photocard_id,
        pending_photocard_id: values.pending_photocard_id,
        condition_grade_id: values.grade_id,
        note: values.note ?? null
      });
    },
    onSuccess: () => {
      setEditing(null);
      setMessage("보유 카드를 수정했습니다.");
      refreshUserCards();
    }
  });
  const deleteMutation = useMutation({
    mutationFn: api.deleteHave,
    onSuccess: () => {
      setMessage("보유 카드를 삭제했습니다.");
      refreshUserCards();
    }
  });

  return (
    <div className="grid gap-4 lg:grid-cols-[360px_1fr]">
      <Card>
        <CardHeader>
          <CardTitle>{editing ? "보유 카드 수정" : "보유 카드 추가"}</CardTitle>
          <CardDescription>
            그룹, 멤버, 릴리즈/출처, 포토카드를 순서대로 선택합니다. 교환 완료 후 더 이상 보유하지 않는 카드는 삭제하세요.
          </CardDescription>
        </CardHeader>
        <CardContent className="grid gap-3">
          {mutation.isError ? <Alert className="border-red-200 bg-red-50 text-red-700">{getFriendlyError(mutation.error)}</Alert> : null}
          {updateMutation.isError ? <Alert className="border-red-200 bg-red-50 text-red-700">{getFriendlyError(updateMutation.error)}</Alert> : null}
          {deleteMutation.isError ? <Alert className="border-red-200 bg-red-50 text-red-700">{getFriendlyError(deleteMutation.error)}</Alert> : null}
          {message ? <Alert className="border-green-200 bg-green-50 text-green-700">{message}</Alert> : null}
          <CardForm
            mode="have"
            pending={mutation.isPending || updateMutation.isPending}
            initialValues={
              editing
                ? {
                    photocard_id: editing.photocard_id,
                    pending_photocard_id: editing.pending_photocard_id,
                    grade_id: editing.condition_grade_id,
                    note: editing.note
                  }
                : undefined
            }
            submitLabel={editing ? "수정 저장" : "추가"}
            resetOnSubmit={!editing}
            onCancel={editing ? () => setEditing(null) : undefined}
            onSubmit={(values) => (editing ? updateMutation.mutate(values) : mutation.mutate(values))}
          />
          <ConditionGuide />
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
          {haves.data?.map((item) => (
            <HaveCardItem
              key={item.id}
              item={item}
              deleting={deleteMutation.isPending}
              onEdit={() => {
                setMessage(null);
                setEditing(item);
              }}
              onDelete={() => {
                if (!window.confirm("이 보유 카드를 삭제할까요?")) return;
                setMessage(null);
                deleteMutation.mutate(item.id);
              }}
            />
          ))}
        </div>
      </section>
    </div>
  );
}
