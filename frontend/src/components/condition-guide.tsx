import { Alert } from "./ui/alert";
import { Badge } from "./ui/badge";

export const conditionGuide = [
  { code: "S", description: "미개봉 또는 하자 없는 최상급" },
  { code: "A", description: "눈에 띄는 하자 없음, 아주 미세한 생활 기스 가능" },
  { code: "B", description: "작은 스크래치/찍힘/인쇄 밀림 등 경미한 하자 있음" },
  { code: "C", description: "눈에 띄는 찍힘, 눌림, 모서리 손상, 표면 흠집 있음" },
  { code: "D", description: "접힘, 오염, 큰 찍힘, 물결, 심한 손상 있음" }
];

export function ConditionGuide({ compact = false }: { compact?: boolean }) {
  return (
    <Alert className="grid gap-3 bg-slate-50">
      <div>
        <p className="font-medium text-slate-950">상태 등급 안내</p>
        <p className="mt-1 text-slate-500">최종 상태 판단은 교환 당사자끼리 외부 채팅에서 실물 사진으로 확인하세요.</p>
      </div>
      <div className={compact ? "flex flex-wrap gap-2" : "grid gap-2"}>
        {conditionGuide.map((item) => (
          <div key={item.code} className="flex items-start gap-2">
            <Badge>{item.code}</Badge>
            <span className="text-sm text-slate-600">{item.description}</span>
          </div>
        ))}
      </div>
    </Alert>
  );
}
