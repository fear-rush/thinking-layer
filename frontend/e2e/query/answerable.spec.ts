import { expect, test } from "../fixtures";
import { submitQuestion } from "../helpers";

test("renders an answerable response", async ({ page }) => {
  // 1. Ask a question backed by direct BI evidence.
  await submitQuestion(page, "Apa ketentuan BI tentang penyedia jasa pembayaran?");

  // 2. Preserve the API status, confidence, answer, and citation metadata.
  await expect(page.getByText("Jawaban ditemukan", { exact: true })).toBeVisible();
  await expect(page.getByText("Keyakinan evidence: strong (92%).")).toBeVisible();
  await expect(
    page
      .getByRole("region", { name: "Jawaban" })
      .getByText("Penyedia jasa pembayaran wajib memenuhi ketentuan BI."),
  ).toBeVisible();
  await expect(
    page.getByText(/BI · PBI Penyedia Jasa Pembayaran · hlm\. 1 · Pasal 1/),
  ).toBeVisible();
});
