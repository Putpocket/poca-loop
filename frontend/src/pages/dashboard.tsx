import { useQuery } from "@tanstack/react-query";
import { Download, FileImage, HeartHandshake, ListChecks, Repeat2, Shuffle } from "lucide-react";
import { useEffect, useMemo, useState, type ComponentType } from "react";
import { Link } from "react-router-dom";
import { ErrorState, LoadingState } from "../components/state-blocks";
import { Alert } from "../components/ui/alert";
import { Badge } from "../components/ui/badge";
import { Button } from "../components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../components/ui/card";
import { API_BASE_URL, api, getFriendlyError } from "../lib/api";
import { getToken } from "../lib/auth";

export function DashboardPage() {
  const haves = useQuery({ queryKey: ["haves"], queryFn: api.haves });
  const wants = useQuery({ queryKey: ["wants"], queryFn: api.wants });
  const direct = useQuery({ queryKey: ["directMatches"], queryFn: api.directMatches });
  const threeWay = useQuery({ queryKey: ["threeWayMatches"], queryFn: api.threeWayMatches });
  const checklist = useQuery({ queryKey: ["shareChecklist"], queryFn: fetchShareChecklist });
  const checklistUrl = useObjectUrl(checklist.data);
  const [downloadError, setDownloadError] = useState<string | null>(null);

  if (haves.isLoading || wants.isLoading || direct.isLoading || threeWay.isLoading) return <LoadingState />;
  if (haves.isError) return <ErrorState message={getFriendlyError(haves.error)} />;
  if (wants.isError) return <ErrorState message={getFriendlyError(wants.error)} />;
  if (direct.isError) return <ErrorState message={getFriendlyError(direct.error)} />;
  if (threeWay.isError) return <ErrorState message={getFriendlyError(threeWay.error)} />;

  function handleSvgDownload() {
    setDownloadError(null);
    if (!checklist.data) {
      setDownloadError("체크리스트를 불러온 뒤 다시 시도해 주세요.");
      return;
    }
    downloadBlob(checklist.data, filenameFor("svg"));
  }

  async function handlePngDownload() {
    setDownloadError(null);
    if (!checklist.data) {
      setDownloadError("체크리스트를 불러온 뒤 다시 시도해 주세요.");
      return;
    }

    try {
      const pngBlob = await svgToPngBlob(checklist.data);
      downloadBlob(pngBlob, filenameFor("png"));
    } catch {
      setDownloadError("PNG 파일을 만들지 못했습니다. 잠시 후 다시 시도해 주세요.");
    }
  }

  return (
    <div className="grid gap-4">
      <section className="rounded-lg border border-slate-200 bg-white p-5">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h1 className="text-2xl font-semibold text-slate-950">Dashboard</h1>
            <p className="mt-1 text-sm text-slate-500">목록을 채우고 가능한 교환 흐름을 확인합니다.</p>
          </div>
          <Button onClick={() => void checklist.refetch()} variant="secondary" disabled={checklist.isFetching}>
            <ListChecks size={16} />
            체크리스트 새로고침
          </Button>
        </div>
      </section>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <MetricCard icon={ListChecks} label="Have" value={haves.data?.length ?? 0} to="/haves" />
        <MetricCard icon={HeartHandshake} label="Want" value={wants.data?.length ?? 0} to="/wants" />
        <MetricCard icon={Repeat2} label="1:1 matches" value={direct.data?.length ?? 0} to="/matches/direct" />
        <MetricCard icon={Shuffle} label="3-way matches" value={threeWay.data?.length ?? 0} to="/matches/three-way" />
      </div>

      <Card>
        <CardHeader>
          <CardTitle>공유용 체크리스트</CardTitle>
          <CardDescription>공개 링크를 만들지 않고, 로그인한 내 목록을 이미지 파일로 저장합니다.</CardDescription>
        </CardHeader>
        <CardContent className="grid gap-4">
          <div className="overflow-hidden rounded-md border border-slate-200 bg-slate-50">
            {checklist.isLoading ? (
              <div className="flex min-h-52 items-center justify-center px-4 text-sm text-slate-500">
                체크리스트 미리보기를 불러오는 중입니다.
              </div>
            ) : checklist.isError ? (
              <div className="flex min-h-52 items-center justify-center px-4 text-center text-sm text-red-600">
                {getFriendlyError(checklist.error)}
              </div>
            ) : checklistUrl ? (
              <img
                src={checklistUrl}
                alt="공유용 체크리스트 미리보기"
                className="block max-h-[520px] w-full object-contain"
              />
            ) : (
              <div className="flex min-h-52 items-center justify-center px-4 text-sm text-slate-500">
                미리보기를 표시할 수 없습니다.
              </div>
            )}
          </div>

          {downloadError ? <Alert className="border-red-200 bg-red-50 text-red-700">{downloadError}</Alert> : null}

          <div className="flex flex-col gap-2 sm:flex-row">
            <Button onClick={handleSvgDownload} disabled={!checklist.data || checklist.isFetching}>
              <Download size={16} />
              SVG 다운로드
            </Button>
            <Button onClick={() => void handlePngDownload()} variant="secondary" disabled={!checklist.data || checklist.isFetching}>
              <FileImage size={16} />
              PNG 다운로드
            </Button>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Next steps</CardTitle>
          <CardDescription>관리자 카탈로그 UI는 아직 없으므로, 등록은 기존 카탈로그 ID를 기준으로 합니다.</CardDescription>
        </CardHeader>
        <CardContent className="grid gap-3 sm:grid-cols-2">
          <LinkCard to="/haves" title="보유 카드 등록" description="내가 줄 수 있는 카드를 상태 등급과 함께 추가합니다." />
          <LinkCard to="/wants" title="원하는 카드 등록" description="받고 싶은 카드와 최소 허용 등급을 추가합니다." />
        </CardContent>
      </Card>
    </div>
  );
}

async function fetchShareChecklist() {
  const response = await fetch(`${API_BASE_URL}/templates/me.svg`, {
    headers: { Authorization: `Bearer ${getToken() ?? ""}` }
  });
  if (!response.ok) {
    throw new Error("공유용 체크리스트를 불러오지 못했습니다.");
  }
  return response.text();
}

function useObjectUrl(svg: string | undefined) {
  const blob = useMemo(() => {
    if (!svg) return undefined;
    return new Blob([svg], { type: "image/svg+xml;charset=utf-8" });
  }, [svg]);
  const [url, setUrl] = useState<string | null>(null);

  useEffect(() => {
    if (!blob) {
      setUrl(null);
      return undefined;
    }
    const objectUrl = URL.createObjectURL(blob);
    setUrl(objectUrl);
    return () => URL.revokeObjectURL(objectUrl);
  }, [blob]);

  return url;
}

function filenameFor(extension: "svg" | "png") {
  const now = new Date();
  const yyyy = now.getFullYear();
  const mm = String(now.getMonth() + 1).padStart(2, "0");
  const dd = String(now.getDate()).padStart(2, "0");
  return `pocaloop-checklist-${yyyy}${mm}${dd}.${extension}`;
}

function downloadBlob(content: BlobPart | Blob, filename: string) {
  const blob = content instanceof Blob ? content : new Blob([content], { type: "image/svg+xml;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = filename;
  document.body.append(anchor);
  anchor.click();
  anchor.remove();
  URL.revokeObjectURL(url);
}

function svgToPngBlob(svg: string) {
  return new Promise<Blob>((resolve, reject) => {
    const svgBlob = new Blob([svg], { type: "image/svg+xml;charset=utf-8" });
    const url = URL.createObjectURL(svgBlob);
    const image = new Image();

    image.onload = () => {
      const width = image.naturalWidth || 980;
      const height = image.naturalHeight || 310;
      const canvas = document.createElement("canvas");
      canvas.width = width;
      canvas.height = height;
      const context = canvas.getContext("2d");
      if (!context) {
        URL.revokeObjectURL(url);
        reject(new Error("Canvas is not available."));
        return;
      }
      context.fillStyle = "#ffffff";
      context.fillRect(0, 0, width, height);
      context.drawImage(image, 0, 0, width, height);
      URL.revokeObjectURL(url);
      canvas.toBlob((blob) => {
        if (!blob) {
          reject(new Error("PNG conversion failed."));
          return;
        }
        resolve(blob);
      }, "image/png");
    };

    image.onerror = () => {
      URL.revokeObjectURL(url);
      reject(new Error("SVG image load failed."));
    };
    image.src = url;
  });
}

function MetricCard({ icon: Icon, label, value, to }: { icon: ComponentType<{ size?: number }>; label: string; value: number; to: string }) {
  return (
    <Link to={to}>
      <Card className="transition hover:border-slate-300">
        <CardContent className="flex items-center justify-between">
          <div>
            <p className="text-sm text-slate-500">{label}</p>
            <p className="mt-1 text-3xl font-semibold text-slate-950">{value}</p>
          </div>
          <Badge className="rounded-md p-2">
            <Icon size={18} />
          </Badge>
        </CardContent>
      </Card>
    </Link>
  );
}

function LinkCard({ to, title, description }: { to: string; title: string; description: string }) {
  return (
    <Link to={to} className="rounded-md border border-slate-200 p-4 transition hover:border-slate-300">
      <p className="font-medium text-slate-950">{title}</p>
      <p className="mt-1 text-sm text-slate-500">{description}</p>
    </Link>
  );
}
