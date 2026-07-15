import { afterEach, describe, expect, it } from "vitest";
import { cleanup, render, screen } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { QueryResult } from "./query-result";
import type { QueryResponse } from "#/lib/api";

afterEach(cleanup);

const result: QueryResponse = {
  request_id: "request-1",
  status: "answerable",
  answer: "Ketentuan yang paling relevan ditemukan.",
  summary: "Ketentuan yang paling relevan ditemukan.",
  findings: [
    {
      id: "f1",
      text: "Penyedia Jasa Pembayaran wajib memperoleh persetujuan Bank Indonesia.",
      citation_ids: ["c1"],
      kind: "direct_rule",
      status: "supported",
    },
  ],
  related_documents: [],
  limitations: [],
  confidence: { label: "strong", score: 0.93, reasons: [] },
  citations: [
    {
      id: "c1",
      file_id: "bi-pjp",
      block_id: "bi-pjp-4-2",
      source_block_ids: ["bi-pjp-4-2", "bi-pjp-5-1"],
      issuer: "BI",
      document: "PBI Penyedia Jasa Pembayaran",
      page: 4,
      page_start: 4,
      page_end: 5,
      pasal: "Pasal 2",
      ayat: "(1)",
      huruf: null,
      unit_path: ["Pasal 2", "ayat (1)"],
      legal_path: null,
      anchors: [],
      source_spans: [],
      text: "PBI Penyedia Jasa Pembayaran, hlm. 4–5, Pasal 2, ayat (1)",
      excerpt: "Penyedia Jasa Pembayaran wajib memperoleh persetujuan.",
      assembled_text:
        "Penyedia Jasa Pembayaran wajib memperoleh persetujuan Bank Indonesia sebelum beroperasi.",
      quality: "document_page_pasal_ayat",
    },
  ],
  duration_ms: 15,
};

function renderResult() {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={queryClient}>
      <QueryResult result={result} />
    </QueryClientProvider>,
  );
}

describe("QueryResult", () => {
  it("renders a compact supported claim with the complete citation range and source block links", () => {
    renderResult();

    expect(screen.getByText(result.findings[0].text)).toBeTruthy();
    expect(screen.getByRole("link", { name: "[c1]" })).toHaveProperty("hash", "#citation-c1");
    expect(
      screen.getByText(
        (_, element) =>
          element?.tagName === "P" && (element.textContent?.includes("hlm. 4–5") ?? false),
      ),
    ).toBeTruthy();
    expect(screen.getByText("Lihat kutipan")).toBeTruthy();
    expect(screen.getByRole("link", { name: "bi-pjp-5-1" })).toHaveProperty(
      "pathname",
      "/documents/bi-pjp/blocks/bi-pjp-5-1",
    );
  });
});
