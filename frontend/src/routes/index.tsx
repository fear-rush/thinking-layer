import { createFileRoute, useHydrated } from "@tanstack/react-router";
import { useMutation } from "@tanstack/react-query";
import { BookOpenText, Search } from "lucide-react";
import { Alert, AlertDescription, AlertTitle } from "#/components/ui/alert";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "#/components/ui/card";
import { QuestionForm } from "#/components/question-form";
import { QueryResult } from "#/components/query-result";
import { createQuery } from "#/lib/api";

export const Route = createFileRoute("/")({ component: HomePage });

function HomePage() {
  const hydrated = useHydrated();
  const queryMutation = useMutation({ mutationFn: createQuery });

  async function submitQuestion(question: string) {
    queryMutation.reset();
    await queryMutation.mutateAsync(question);
  }

  const errorMessage = queryMutation.error instanceof Error ? queryMutation.error.message : null;

  return (
    <main className="mx-auto flex min-h-screen w-full max-w-5xl flex-col gap-8 px-4 py-10 sm:px-6 sm:py-16">
      <header className="max-w-3xl space-y-4">
        <div className="flex items-center gap-2 text-sm font-medium text-muted-foreground">
          <BookOpenText className="size-4" aria-hidden="true" />
          Thinking Layer
        </div>
        <h1 className="text-4xl font-semibold tracking-tight text-balance sm:text-5xl">
          Tanya regulasi keuangan Indonesia.
        </h1>
        <p className="max-w-2xl text-base leading-7 text-muted-foreground sm:text-lg">
          Jawaban disusun dari korpus regulasi BI dan OJK yang tersedia secara lokal, dengan sumber
          dan kutipan untuk setiap temuan.
        </p>
      </header>

      <Card>
        <CardHeader>
          <CardTitle>Ajukan pertanyaan</CardTitle>
          <CardDescription>
            Gunakan pertanyaan spesifik agar sistem dapat memilih bukti yang paling relevan.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <QuestionForm
            isReady={hydrated}
            isSubmitting={queryMutation.isPending}
            onSubmit={submitQuestion}
          />
        </CardContent>
      </Card>

      {errorMessage ? (
        <Alert variant="destructive">
          <Search aria-hidden="true" />
          <AlertTitle>Permintaan tidak dapat dikirim</AlertTitle>
          <AlertDescription>{errorMessage}</AlertDescription>
        </Alert>
      ) : null}

      {queryMutation.data ? <QueryResult result={queryMutation.data} /> : null}

      <Alert>
        <BookOpenText aria-hidden="true" />
        <AlertTitle>Batasan korpus lokal</AlertTitle>
        <AlertDescription>
          Sistem hanya menyatakan temuan yang didukung oleh dokumen yang dikutip. Jika buktinya
          tidak cukup, jawaban akan menyatakan bahwa informasi tidak ditemukan.
        </AlertDescription>
      </Alert>
    </main>
  );
}
