import { Alert } from "./ui/alert";

export function LoadingState({ label = "불러오는 중입니다." }: { label?: string }) {
  return <Alert className="animate-pulse">{label}</Alert>;
}

export function ErrorState({ message }: { message: string }) {
  return <Alert className="border-red-200 bg-red-50 text-red-700">{message}</Alert>;
}

export function EmptyState({ title, description }: { title: string; description: string }) {
  return (
    <Alert className="bg-slate-50">
      <p className="font-medium text-slate-800">{title}</p>
      <p className="mt-1 text-slate-500">{description}</p>
    </Alert>
  );
}
