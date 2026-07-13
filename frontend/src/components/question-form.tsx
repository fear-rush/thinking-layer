import { useState, type FormEvent } from "react";
import { LoaderCircle, Search } from "lucide-react";
import { Button } from "#/components/ui/button";
import { Label } from "#/components/ui/label";
import { Textarea } from "#/components/ui/textarea";

interface QuestionFormProps {
  isSubmitting: boolean;
  onSubmit: (question: string) => Promise<void>;
}

export function QuestionForm({ isSubmitting, onSubmit }: QuestionFormProps) {
  const [question, setQuestion] = useState("");
  const [validationError, setValidationError] = useState<string | null>(null);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const normalizedQuestion = question.trim();

    if (!normalizedQuestion) {
      setValidationError("Masukkan pertanyaan terlebih dahulu.");
      return;
    }

    setValidationError(null);
    await onSubmit(normalizedQuestion);
  }

  return (
    <form className="space-y-4" onSubmit={handleSubmit} noValidate>
      <div className="space-y-2">
        <Label htmlFor="question">Pertanyaan regulasi</Label>
        <Textarea
          id="question"
          name="question"
          value={question}
          onChange={(event) => setQuestion(event.target.value)}
          placeholder="Contoh: Apa ketentuan BI tentang penyedia jasa pembayaran?"
          aria-describedby={validationError ? "question-error" : undefined}
          aria-invalid={Boolean(validationError)}
          disabled={isSubmitting}
          rows={5}
        />
        {validationError ? (
          <p id="question-error" className="text-sm text-destructive">
            {validationError}
          </p>
        ) : null}
      </div>
      <Button type="submit" disabled={isSubmitting}>
        {isSubmitting ? (
          <LoaderCircle className="animate-spin" aria-hidden="true" />
        ) : (
          <Search aria-hidden="true" />
        )}
        {isSubmitting ? "Mencari bukti…" : "Cari jawaban"}
      </Button>
    </form>
  );
}
