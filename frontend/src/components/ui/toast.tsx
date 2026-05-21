import { cn } from "../../lib/utils";

export function Toast({
  children,
  variant = "success"
}: {
  children: string;
  variant?: "success" | "error";
}) {
  return (
    <div
      role="status"
      className={cn(
        "fixed bottom-4 right-4 z-50 rounded-md border px-4 py-3 text-sm shadow-lg",
        variant === "success" && "border-green-200 bg-green-50 text-green-700",
        variant === "error" && "border-red-200 bg-red-50 text-red-700"
      )}
    >
      {children}
    </div>
  );
}
