import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { LoaderCircle, ThumbsDown, ThumbsUp } from "lucide-react";
import { createFeedback } from "#/lib/api";
import { Button } from "#/components/ui/button";
import { Label } from "#/components/ui/label";
import { Textarea } from "#/components/ui/textarea";

interface FeedbackControlsProps {
  requestId: string;
}

export function FeedbackControls({ requestId }: FeedbackControlsProps) {
  const [comment, setComment] = useState("");
  const feedbackMutation = useMutation({ mutationFn: createFeedback });

  function submitFeedback(helpful: boolean) {
    feedbackMutation.reset();
    feedbackMutation.mutate({ requestId, helpful, comment: comment.trim() || undefined });
  }

  const feedbackError =
    feedbackMutation.error instanceof Error ? feedbackMutation.error.message : null;

  return (
    <section className="space-y-3" aria-label="Umpan balik jawaban">
      <p className="text-sm font-medium">Apakah jawaban ini membantu?</p>
      <div className="flex flex-wrap gap-2">
        <Button
          type="button"
          variant="outline"
          disabled={feedbackMutation.isPending}
          onClick={() => submitFeedback(true)}
        >
          {feedbackMutation.isPending ? (
            <LoaderCircle className="animate-spin" aria-hidden="true" />
          ) : (
            <ThumbsUp aria-hidden="true" />
          )}
          Membantu
        </Button>
        <Button
          type="button"
          variant="outline"
          disabled={feedbackMutation.isPending}
          onClick={() => submitFeedback(false)}
        >
          <ThumbsDown aria-hidden="true" />
          Belum membantu
        </Button>
      </div>
      <div className="space-y-2">
        <Label htmlFor="feedback-comment">Komentar opsional</Label>
        <Textarea
          id="feedback-comment"
          value={comment}
          onChange={(event) => setComment(event.target.value)}
          placeholder="Bagian mana yang perlu diperbaiki?"
          disabled={feedbackMutation.isPending}
          rows={3}
        />
      </div>
      {feedbackMutation.isSuccess ? (
        <p className="text-sm text-muted-foreground">
          Terima kasih. Umpan balik Anda sudah dicatat secara lokal.
        </p>
      ) : null}
      {feedbackError ? <p className="text-sm text-destructive">{feedbackError}</p> : null}
    </section>
  );
}
