import { ExternalLink, FileText, Timer } from "lucide-react";
import { FeedbackControls } from "#/components/feedback-controls";
import { Badge } from "#/components/ui/badge";
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "#/components/ui/card";
import { Separator } from "#/components/ui/separator";
import type { Citation, QueryResponse } from "#/lib/api";

const statusCopy = {
  answerable: { label: "Jawaban ditemukan", variant: "default" as const },
  partial: { label: "Jawaban sebagian", variant: "secondary" as const },
  not_found: { label: "Tidak ditemukan", variant: "outline" as const },
};

function citationHref(citation: Citation, blockId = citation.block_id) {
  if (!citation.file_id || !blockId) {
    return null;
  }

  return `/v1/documents/${encodeURIComponent(citation.file_id)}/blocks/${encodeURIComponent(blockId)}`;
}

function citationPages(citation: Citation) {
  const start = citation.page_start ?? citation.page;
  const end = citation.page_end ?? start;
  if (!start) return null;
  return end && end !== start ? `hlm. ${start}–${end}` : `hlm. ${start}`;
}

function citationMetadata(citation: Citation) {
  return [
    citation.issuer,
    citation.document,
    citationPages(citation),
    citation.pasal,
    citation.ayat,
    citation.unit_path.length ? citation.unit_path.join(" · ") : null,
  ]
    .filter(Boolean)
    .join(" · ");
}

function citationBlockIds(citation: Citation) {
  const ids = citation.source_block_ids.length ? citation.source_block_ids : [citation.block_id];
  return ids.filter((blockId): blockId is string => Boolean(blockId));
}

function compactExcerpt(citation: Citation) {
  const text = citation.assembled_text || citation.excerpt;
  if (!text || text.length <= 520) return text;
  return `${text.slice(0, 517).trimEnd()}…`;
}

export function QueryResult({ result }: { result: QueryResponse }) {
  const status = statusCopy[result.status];
  const confidencePercent = Math.round(result.confidence.score * 100);
  const hasStructuredFindings = result.findings.length > 0;
  const citationsById = new Map(
    result.citations
      .filter((citation) => citation.id)
      .map((citation) => [citation.id as string, citation]),
  );

  return (
    <Card aria-live="polite">
      <CardHeader>
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div className="space-y-2">
            <Badge variant={status.variant}>{status.label}</Badge>
            <CardTitle>Hasil pencarian</CardTitle>
          </div>
          <div className="flex items-center gap-1.5 text-sm text-muted-foreground">
            <Timer className="size-4" aria-hidden="true" />
            {result.duration_ms} ms
          </div>
        </div>
        <CardDescription>
          Keyakinan evidence: {result.confidence.label} ({confidencePercent}%).
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        <section className="space-y-4 text-sm leading-7 text-foreground" aria-label="Jawaban">
          {hasStructuredFindings ? (
            <>
              <p className="text-base leading-7">{result.summary}</p>
              <ol className="space-y-3">
                {result.findings.map((finding) => (
                  <li key={finding.id} className="rounded-lg border p-4">
                    <p>{finding.text}</p>
                    <div className="mt-2 flex flex-wrap gap-2 text-sm">
                      {finding.citation_ids.map((citationId) =>
                        citationsById.has(citationId) ? (
                          <a
                            key={citationId}
                            className="font-medium underline underline-offset-4"
                            href={`#citation-${citationId}`}
                          >
                            [{citationId}]
                          </a>
                        ) : (
                          <span key={citationId} className="text-muted-foreground">
                            [kutipan tidak tersedia]
                          </span>
                        ),
                      )}
                    </div>
                  </li>
                ))}
              </ol>
              {result.limitations.length ? (
                <p className="text-muted-foreground">{result.limitations.join(" ")}</p>
              ) : null}
              {result.related_documents.length ? (
                <details className="rounded-lg border p-4 text-muted-foreground">
                  <summary className="cursor-pointer font-medium text-foreground">
                    Regulasi terkait
                  </summary>
                  <ul className="mt-2 list-disc space-y-1 pl-5">
                    {result.related_documents.map((document) => (
                      <li key={`${document.issuer}-${document.document}`}>
                        {[document.issuer, document.document].filter(Boolean).join(" · ")}
                      </li>
                    ))}
                  </ul>
                </details>
              ) : null}
            </>
          ) : (
            <p className="whitespace-pre-wrap">{result.answer}</p>
          )}
        </section>

        <section className="space-y-3" aria-labelledby="citations-heading">
          <h2 id="citations-heading" className="text-base font-semibold">
            Kutipan sumber
          </h2>
          {result.citations.length ? (
            <ul className="space-y-3">
              {result.citations.map((citation, index) => {
                const href = citationHref(citation);
                const metadata = citationMetadata(citation);
                const blockIds = citationBlockIds(citation);
                const excerpt = compactExcerpt(citation);

                return (
                  <li
                    key={`${citation.file_id}-${citation.block_id}-${index}`}
                    id={citation.id ? `citation-${citation.id}` : undefined}
                    className="rounded-lg border p-4"
                  >
                    <div className="flex gap-3">
                      <FileText
                        className="mt-0.5 size-4 shrink-0 text-muted-foreground"
                        aria-hidden="true"
                      />
                      <div className="min-w-0 space-y-1">
                        {href ? (
                          <a
                            className="inline-flex items-center gap-1 font-medium underline underline-offset-4"
                            href={href}
                            target="_blank"
                            rel="noreferrer"
                          >
                            {citation.text || metadata || "Buka kutipan"}
                            <ExternalLink className="size-3.5" aria-hidden="true" />
                          </a>
                        ) : (
                          <p className="font-medium">
                            {citation.text || metadata || "Kutipan tidak tersedia"}
                          </p>
                        )}
                        {metadata ? (
                          <p className="text-sm text-muted-foreground">{metadata}</p>
                        ) : null}
                        {excerpt ? (
                          <details className="pt-1 text-sm leading-6">
                            <summary className="cursor-pointer font-medium text-foreground">
                              Lihat kutipan
                            </summary>
                            <p className="mt-2 text-muted-foreground">{excerpt}</p>
                          </details>
                        ) : null}
                        {blockIds.length > 1 ? (
                          <div className="flex flex-wrap gap-x-2 gap-y-1 text-xs text-muted-foreground">
                            <span>Blok sumber:</span>
                            {blockIds.map((blockId) => {
                              const sourceHref = citationHref(citation, blockId);
                              return sourceHref ? (
                                <a
                                  key={blockId}
                                  className="underline underline-offset-4"
                                  href={sourceHref}
                                  target="_blank"
                                  rel="noreferrer"
                                >
                                  {blockId}
                                </a>
                              ) : (
                                <span key={blockId}>{blockId}</span>
                              );
                            })}
                          </div>
                        ) : null}
                      </div>
                    </div>
                  </li>
                );
              })}
            </ul>
          ) : (
            <p className="text-sm text-muted-foreground">
              Tidak ada kutipan yang dapat ditampilkan untuk hasil ini.
            </p>
          )}
        </section>
      </CardContent>
      <CardFooter className="flex-col items-stretch gap-5 border-t">
        <Separator />
        <FeedbackControls requestId={result.request_id} />
      </CardFooter>
    </Card>
  );
}
