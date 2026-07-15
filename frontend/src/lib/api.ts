export type QueryStatus = "answerable" | "partial" | "not_found";

export interface Citation {
  id: string | null;
  file_id: string | null;
  block_id: string | null;
  source_block_ids: string[];
  issuer: string | null;
  document: string | null;
  page: number | null;
  page_start: number | null;
  page_end: number | null;
  pasal: string | null;
  ayat: string | null;
  huruf: string | null;
  unit_path: string[];
  legal_path: Record<string, unknown> | null;
  anchors: Array<Record<string, unknown>>;
  source_spans: Array<Record<string, unknown>>;
  text: string | null;
  excerpt: string | null;
  assembled_text: string | null;
  quality: string | null;
}

export interface Finding {
  id: string;
  text: string;
  citation_ids: string[];
  kind: "direct_rule" | "definition" | "scope" | "sanction" | "other";
  status: "supported";
}

export interface RelatedDocument {
  document: string;
  issuer: string | null;
  direct: boolean;
}

export interface QueryResponse {
  request_id: string;
  status: QueryStatus;
  answer: string;
  summary: string | null;
  findings: Finding[];
  related_documents: RelatedDocument[];
  limitations: string[];
  confidence: {
    label: "strong" | "partial" | "weak" | "not_found";
    score: number;
    reasons: string[];
  };
  citations: Citation[];
  duration_ms: number;
}

interface ApiErrorBody {
  detail?: string;
}

export class ApiError extends Error {}

async function responseJson<T>(response: Response): Promise<T> {
  const body = (await response.json().catch(() => null)) as T | ApiErrorBody | null;

  if (!response.ok) {
    const detail = body && typeof body === "object" && "detail" in body ? body.detail : null;
    throw new ApiError(detail || `Permintaan gagal (${response.status}).`);
  }

  return body as T;
}

export async function createQuery(question: string): Promise<QueryResponse> {
  const response = await fetch("/v1/queries", {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ question }),
  });

  return responseJson<QueryResponse>(response);
}

export async function createFeedback(input: {
  requestId: string;
  helpful: boolean;
  comment?: string;
}): Promise<void> {
  const response = await fetch("/v1/feedback", {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({
      request_id: input.requestId,
      helpful: input.helpful,
      comment: input.comment || null,
    }),
  });

  await responseJson(response);
}
