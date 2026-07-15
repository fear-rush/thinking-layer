import { expect, test } from "../fixtures";
import { submitQuestion } from "../helpers";

test("renders a not-found response", async ({ page }) => {
  // 1. Ask a question outside the local regulation corpus.
  await submitQuestion(page, "Apa aturan bank di planet Mars?");

  // 2. Preserve the API refusal state without inventing evidence.
  await expect(page.getByText("Tidak ditemukan", { exact: true })).toBeVisible();
  await expect(page.getByText("Keyakinan evidence: not_found (0%).")).toBeVisible();
  await expect(page.getByText("Tidak ditemukan dalam dokumen yang tersedia.")).toBeVisible();
  await expect(
    page.getByText("Tidak ada kutipan yang dapat ditampilkan untuk hasil ini."),
  ).toBeVisible();
});
