import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation } from "@tanstack/react-query";
import { UserPlus } from "lucide-react";
import { useForm } from "react-hook-form";
import { Link, Navigate, useNavigate } from "react-router-dom";
import { z } from "zod";
import { Alert } from "../components/ui/alert";
import { Button } from "../components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../components/ui/card";
import { Input } from "../components/ui/input";
import { api, getFriendlyError } from "../lib/api";
import { getToken } from "../lib/auth";
import { AuthShell, Field } from "./login";

const schema = z.object({
  email: z.string().email("이메일 형식이 올바르지 않습니다."),
  username: z.string().min(3, "3자 이상 입력하세요.").regex(/^[A-Za-z0-9_.-]+$/, "영문, 숫자, . _ - 만 사용할 수 있습니다."),
  password: z.string().min(8, "8자 이상 입력하세요.")
});

type FormData = z.infer<typeof schema>;

export function SignupPage() {
  const navigate = useNavigate();
  const form = useForm<FormData>({ resolver: zodResolver(schema), defaultValues: { email: "", username: "", password: "" } });
  const mutation = useMutation({
    mutationFn: api.signup,
    onSuccess: () => navigate("/login")
  });

  if (getToken()) return <Navigate to="/dashboard" replace />;

  return (
    <AuthShell>
      <Card>
        <CardHeader>
          <CardTitle>회원가입</CardTitle>
          <CardDescription>텍스트 메타데이터 기반 교환 목록을 시작합니다.</CardDescription>
        </CardHeader>
        <CardContent>
          <form className="grid gap-4" onSubmit={form.handleSubmit((values) => mutation.mutate(values))}>
            {mutation.isError ? <Alert className="border-red-200 bg-red-50 text-red-700">{getFriendlyError(mutation.error)}</Alert> : null}
            <Field label="Email" error={form.formState.errors.email?.message}>
              <Input type="email" autoComplete="email" {...form.register("email")} />
            </Field>
            <Field label="Username" error={form.formState.errors.username?.message}>
              <Input autoComplete="username" {...form.register("username")} />
            </Field>
            <Field label="Password" error={form.formState.errors.password?.message}>
              <Input type="password" autoComplete="new-password" {...form.register("password")} />
            </Field>
            <Button disabled={mutation.isPending}>
              <UserPlus size={16} />
              {mutation.isPending ? "가입 중" : "회원가입"}
            </Button>
            <p className="text-center text-sm text-slate-500">
              이미 계정이 있나요? <Link className="font-medium text-slate-950" to="/login">로그인</Link>
            </p>
          </form>
        </CardContent>
      </Card>
    </AuthShell>
  );
}
