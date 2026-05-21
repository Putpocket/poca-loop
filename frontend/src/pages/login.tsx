import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation } from "@tanstack/react-query";
import { LogIn } from "lucide-react";
import type { ReactNode } from "react";
import { useForm } from "react-hook-form";
import { Link, Navigate, useNavigate } from "react-router-dom";
import { z } from "zod";
import { Alert } from "../components/ui/alert";
import { Button } from "../components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../components/ui/card";
import { Input } from "../components/ui/input";
import { api, getFriendlyError } from "../lib/api";
import { getToken, setToken } from "../lib/auth";

const schema = z.object({
  email: z.string().email("이메일 형식이 올바르지 않습니다."),
  password: z.string().min(1, "비밀번호를 입력하세요.")
});

type FormData = z.infer<typeof schema>;

export function LoginPage() {
  const navigate = useNavigate();
  const form = useForm<FormData>({ resolver: zodResolver(schema), defaultValues: { email: "", password: "" } });
  const mutation = useMutation({
    mutationFn: api.login,
    onSuccess: (data) => {
      setToken(data.access_token);
      navigate("/dashboard");
    }
  });

  if (getToken()) return <Navigate to="/dashboard" replace />;

  return (
    <AuthShell>
      <Card>
        <CardHeader>
          <CardTitle>로그인</CardTitle>
          <CardDescription>보유/원함 목록과 매칭 결과를 확인합니다.</CardDescription>
        </CardHeader>
        <CardContent>
          <form className="grid gap-4" onSubmit={form.handleSubmit((values) => mutation.mutate(values))}>
            {mutation.isError ? <Alert className="border-red-200 bg-red-50 text-red-700">{getFriendlyError(mutation.error)}</Alert> : null}
            <Field label="Email" error={form.formState.errors.email?.message}>
              <Input type="email" autoComplete="email" {...form.register("email")} />
            </Field>
            <Field label="Password" error={form.formState.errors.password?.message}>
              <Input type="password" autoComplete="current-password" {...form.register("password")} />
            </Field>
            <Button disabled={mutation.isPending}>
              <LogIn size={16} />
              {mutation.isPending ? "로그인 중" : "로그인"}
            </Button>
            <p className="text-center text-sm text-slate-500">
              계정이 없나요? <Link className="font-medium text-slate-950" to="/signup">회원가입</Link>
            </p>
          </form>
        </CardContent>
      </Card>
    </AuthShell>
  );
}

export function AuthShell({ children }: { children: ReactNode }) {
  return (
    <main className="grid min-h-screen place-items-center bg-slate-50 px-4 py-8">
      <div className="w-full max-w-md">
        <div className="mb-6 text-center">
          <div className="mx-auto mb-3 flex h-12 w-12 items-center justify-center rounded-lg bg-slate-950 text-white">PL</div>
          <h1 className="text-2xl font-semibold text-slate-950">poca-loop</h1>
        </div>
        {children}
      </div>
    </main>
  );
}

export function Field({ label, error, children }: { label: string; error?: string; children: ReactNode }) {
  return (
    <label className="grid gap-1.5">
      <span className="text-sm font-medium text-slate-700">{label}</span>
      {children}
      {error ? <span className="text-sm text-red-600">{error}</span> : null}
    </label>
  );
}
