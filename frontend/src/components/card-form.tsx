import { zodResolver } from "@hookform/resolvers/zod";
import { useQuery } from "@tanstack/react-query";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { api } from "../lib/api";
import { Button } from "./ui/button";
import { Input } from "./ui/input";
import { Select } from "./ui/select";

const schema = z.object({
  photocard_id: z.string().min(1, "카드 ID를 입력하세요.").transform(Number).pipe(z.number().int().positive("카드 ID를 입력하세요.")),
  grade_id: z.string().min(1, "등급을 선택하세요.").transform(Number).pipe(z.number().int().positive("등급을 선택하세요.")),
  note: z.string().max(500).optional()
});

export type CardFormValues = z.infer<typeof schema>;
type CardFormInput = z.input<typeof schema>;

export function CardForm({
  mode,
  pending,
  onSubmit
}: {
  mode: "have" | "want";
  pending: boolean;
  onSubmit: (values: CardFormValues) => void;
}) {
  const grades = useQuery({ queryKey: ["conditionGrades"], queryFn: api.conditionGrades });
  const form = useForm<CardFormInput, unknown, CardFormValues>({
    resolver: zodResolver(schema),
    defaultValues: { photocard_id: "", grade_id: "", note: "" }
  });

  return (
    <form
      className="grid gap-3"
      onSubmit={form.handleSubmit((values) => {
        onSubmit(values);
        form.reset({ photocard_id: "", grade_id: "", note: "" });
      })}
    >
      <label className="grid gap-1.5">
        <span className="text-sm font-medium text-slate-700">Photocard ID</span>
        <Input type="number" min={1} {...form.register("photocard_id")} />
        {form.formState.errors.photocard_id ? (
          <span className="text-sm text-red-600">{form.formState.errors.photocard_id.message}</span>
        ) : null}
      </label>
      <label className="grid gap-1.5">
        <span className="text-sm font-medium text-slate-700">{mode === "have" ? "상태 등급" : "최소 허용 등급"}</span>
        <Select {...form.register("grade_id")}>
          <option value="">등급 선택</option>
          {grades.data?.map((grade) => (
            <option key={grade.id} value={grade.id}>
              {grade.code} - {grade.label}
            </option>
          ))}
        </Select>
        {form.formState.errors.grade_id ? (
          <span className="text-sm text-red-600">{form.formState.errors.grade_id.message}</span>
        ) : null}
      </label>
      <label className="grid gap-1.5">
        <span className="text-sm font-medium text-slate-700">{mode === "have" ? "메모 / 하자 태그" : "메모"}</span>
        <Input placeholder={mode === "have" ? "예: corner ding" : "선택 입력"} {...form.register("note")} />
      </label>
      <Button disabled={pending || grades.isLoading}>{pending ? "저장 중" : "추가"}</Button>
    </form>
  );
}
