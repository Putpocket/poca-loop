import { getToken } from "./auth";

export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

export type User = {
  id: number;
  username: string;
};

export type Group = {
  id: number;
  name: string;
  slug: string;
};

export type Member = {
  id: number;
  group_id: number;
  name: string;
  stage_name: string | null;
};

export type Photocard = {
  id: number;
  group_id: number;
  member_id: number;
  release_id: number | null;
  name: string;
  version: string | null;
  external_url: string | null;
  notes: string | null;
  release: Release | null;
};

export type Release = {
  id: number;
  group_id: number;
  title: string;
  source_type: string;
  release_type: string;
  retailer_or_event: string | null;
  venue: string | null;
  country: string | null;
  round: string | null;
  detail: string | null;
  start_date: string | null;
  end_date: string | null;
  notes: string | null;
  released_on: string | null;
};

export type ConditionGrade = {
  id: number;
  code: string;
  label: string;
  description: string | null;
  sort_order: number;
};

export type UserHave = {
  id: number;
  photocard_id: number;
  condition_grade_id: number;
  note: string | null;
  photocard: Photocard;
  condition_grade: ConditionGrade;
};

export type UserWant = {
  id: number;
  photocard_id: number;
  minimum_condition_grade_id: number | null;
  note: string | null;
  photocard: Photocard;
  minimum_condition_grade: ConditionGrade | null;
};

export type DirectMatch = {
  match_type: "direct";
  user_a: User;
  user_b: User;
  user_a_gives: { photocard: Photocard; condition_grade: ConditionGrade };
  user_a_receives: { photocard: Photocard; condition_grade: ConditionGrade };
  user_b_gives: { photocard: Photocard; condition_grade: ConditionGrade };
  user_b_receives: { photocard: Photocard; condition_grade: ConditionGrade };
  condition_check: Record<string, boolean | string | null>;
  generated_at: string;
};

export type ThreeWayMatch = {
  match_type: "three_way";
  participants: User[];
  trade_edges: Array<{
    giver: User;
    receiver: User;
    card: Photocard;
    condition_grade: ConditionGrade;
    receiver_min_condition_grade: ConditionGrade | null;
    condition_passed: boolean;
  }>;
  generated_at: string;
};

class ApiError extends Error {
  status: number;

  constructor(message: string, status: number) {
    super(message);
    this.status = status;
  }
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const token = getToken();
  const headers = new Headers(options.headers);
  if (!headers.has("Content-Type") && options.body) {
    headers.set("Content-Type", "application/json");
  }
  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  const response = await fetch(`${API_BASE_URL}${path}`, { ...options, headers });
  if (!response.ok) {
    let message = "요청을 처리하지 못했습니다.";
    try {
      const data = (await response.json()) as { detail?: unknown };
      if (typeof data.detail === "string") {
        message = data.detail;
      }
    } catch {
      message = response.statusText || message;
    }
    throw new ApiError(message, response.status);
  }

  if (response.status === 204) {
    return undefined as T;
  }
  return (await response.json()) as T;
}

export const api = {
  signup: (payload: { email: string; username: string; password: string }) =>
    request<User>("/api/v1/auth/signup", { method: "POST", body: JSON.stringify(payload) }),
  login: (payload: { email: string; password: string }) =>
    request<{ access_token: string; token_type: string }>("/api/v1/auth/login", {
      method: "POST",
      body: JSON.stringify(payload)
    }),
  me: () => request<User>("/api/v1/auth/me"),
  groups: () => request<Group[]>("/api/v1/catalog/groups"),
  members: () => request<Member[]>("/api/v1/catalog/members"),
  releases: () => request<Release[]>("/api/v1/catalog/releases"),
  photocards: () => request<Photocard[]>("/api/v1/catalog/photocards"),
  haves: () => request<UserHave[]>("/api/v1/me/cards/haves"),
  wants: () => request<UserWant[]>("/api/v1/me/cards/wants"),
  conditionGrades: () => request<ConditionGrade[]>("/api/v1/catalog/condition-grades"),
  addHave: (payload: { photocard_id: number; condition_grade_id: number; note?: string }) =>
    request<UserHave>("/api/v1/me/cards/haves", { method: "POST", body: JSON.stringify(payload) }),
  addWant: (payload: { photocard_id: number; minimum_condition_grade_id?: number; note?: string }) =>
    request<UserWant>("/api/v1/me/cards/wants", { method: "POST", body: JSON.stringify(payload) }),
  directMatches: () => request<DirectMatch[]>("/matches/direct"),
  threeWayMatches: () => request<ThreeWayMatch[]>("/matches/three-way"),
  svgUrl: () => `${API_BASE_URL}/templates/me.svg`
};

export function getFriendlyError(error: unknown) {
  if (error instanceof Error) return error.message;
  return "알 수 없는 오류가 발생했습니다.";
}
