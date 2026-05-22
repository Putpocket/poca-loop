import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { CardForm, type CardFormValues } from "../components/card-form";
import { HaveCardItem } from "../components/card-item";
import { ConditionGuide } from "../components/condition-guide";
import { EmptyState, ErrorState, LoadingState } from "../components/state-blocks";
import { Alert } from "../components/ui/alert";
import { Button } from "../components/ui/button";
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
    <div className="grid items-start gap-4 lg:grid-cols-[minmax(380px,420px)_minmax(520px,1fr)] xl:grid-cols-[minmax(400px,430px)_minmax(0,1fr)]">
      <Card className="w-full">
        <CardHeader>
          <CardTitle>{editing ? "보유 카드 수정" : "보유 카드 추가"}</CardTitle>
          <CardDescription>
            교환에 내놓을 포카를 검색해 추가합니다. 카탈로그에 없으면 텍스트로 임시 등록할 수 있어요.
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
          <ConditionGuide compact />
        </CardContent>
      </Card>

      <Card className="min-w-0 self-start lg:min-h-[460px]">
        <CardHeader>
          <CardTitle>내 보유 카드</CardTitle>
          <CardDescription>교환에 내놓을 수 있는 카드입니다.</CardDescription>
        </CardHeader>
        <CardContent className="grid gap-3">
          {haves.isLoading ? <LoadingState /> : null}
          {haves.isError ? <ErrorState message={getFriendlyError(haves.error)} /> : null}
          {haves.data?.length === 0 ? (
            <div className="grid min-h-80 place-items-center gap-3 rounded-md border border-dashed border-slate-200 bg-slate-50 p-6 text-center">
              <EmptyState title="아직 보유 카드가 없어요." description="교환에 내놓을 카드를 추가해보세요." />
              <Button className="w-fit" type="button" variant="secondary" onClick={() => window.scrollTo({ top: 0, behavior: "smooth" })}>
                보유 카드 추가하기
              </Button>
            </div>
          ) : null}
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
        </CardContent>
      </Card>
    </div>
  );
}
