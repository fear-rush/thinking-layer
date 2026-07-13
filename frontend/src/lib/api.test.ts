import { afterEach, describe, expect, it, vi } from "vitest";
import { ApiError, createQuery } from "./api";

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("createQuery", () => {
  it("posts the question to the local query endpoint", async () => {
    const payload = {
      request_id: "request-1",
      status: "answerable",
      answer: "Jawaban berbasis dokumen.",
      confidence: { label: "strong", score: 0.9, reasons: [] },
      citations: [],
      duration_ms: 24,
    };
    const fetchMock = vi
      .fn()
      .mockResolvedValue(new Response(JSON.stringify(payload), { status: 200 }));
    vi.stubGlobal("fetch", fetchMock);

    await expect(createQuery("Apa ketentuannya?")).resolves.toEqual(payload);
    expect(fetchMock).toHaveBeenCalledWith("/v1/queries", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ question: "Apa ketentuannya?" }),
    });
  });

  it("exposes the API error detail", async () => {
    vi.stubGlobal(
      "fetch",
      vi
        .fn()
        .mockResolvedValue(
          new Response(JSON.stringify({ detail: "question must not be blank" }), { status: 422 }),
        ),
    );

    await expect(createQuery("")).rejects.toEqual(new ApiError("question must not be blank"));
  });
});
