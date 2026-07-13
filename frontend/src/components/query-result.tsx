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

function citationHref(citation: Citation) {
  if (!citation.file_id || !citation.block_id) {
    return null;
  }

  return `/v1/documents/${encodeURIComponent(citation.file_id)}/blocks/${encodeURIComponent(citation.block_id)}`;
}

function citationMetadata(citation: Citation) {
  return [
    citation.issuer,
    citation.document,
    citation.page ? `hlm. ${citation.page}` : null,
    citation.pasal,
    citation.ayat,
  ]
    .filter(Boolean)
    .join(" · ");
}

export function QueryResult({ result }: { result: QueryResponse }) {
  const status = statusCopy[result.status];
  const confidencePercent = Math.round(result.confidence.score * 100);

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
        <div className="whitespace-pre-wrap text-sm leading-7 text-foreground">{result.answer}</div>

        <section className="space-y-3" aria-labelledby="citations-heading">
          <h2 id="citations-heading" className="text-base font-semibold">
            Kutipan sumber
          </h2>
          {result.citations.length ? (
            <ul className="space-y-3">
              {result.citations.map((citation, index) => {
                const href = citationHref(citation);
                const metadata = citationMetadata(citation);

                return (
                  <li
                    key={`${citation.file_id}-${citation.block_id}-${index}`}
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
