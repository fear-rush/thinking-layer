import { afterEach, describe, expect, it, vi } from "vitest";
import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { QuestionForm } from "./question-form";

afterEach(cleanup);

describe("QuestionForm", () => {
  it("keeps the form disabled until client hydration is ready", () => {
    render(<QuestionForm isReady={false} isSubmitting={false} onSubmit={vi.fn()} />);

    expect(screen.getByLabelText("Pertanyaan regulasi")).toHaveProperty("disabled", true);
    expect(screen.getByRole("button", { name: "Cari jawaban" })).toHaveProperty("disabled", true);
  });

  it("requires a question before submission", () => {
    render(<QuestionForm isSubmitting={false} onSubmit={vi.fn()} />);

    fireEvent.click(screen.getByRole("button", { name: "Cari jawaban" }));

    expect(screen.getByText("Masukkan pertanyaan terlebih dahulu.")).toBeTruthy();
  });

  it("submits a trimmed question", () => {
    const onSubmit = vi.fn().mockResolvedValue(undefined);
    render(<QuestionForm isSubmitting={false} onSubmit={onSubmit} />);

    fireEvent.change(screen.getByLabelText("Pertanyaan regulasi"), {
      target: { value: "  Apa aturan PJP?  " },
    });
    fireEvent.click(screen.getByRole("button", { name: "Cari jawaban" }));

    expect(onSubmit).toHaveBeenCalledWith("Apa aturan PJP?");
  });
});
