import { expect, test } from "../fixtures";
import { submitQuestion } from "../helpers";

test("renders a partial response", async ({ page }) => {
  // 1. Ask for a cross-regulator comparison with direct evidence from only one issuer.
  await submitQuestion(page, "Bandingkan aturan PJP BI dan OJK.");

  // 2. Preserve the API's partial status and refusal wording.
  await expect(page.getByText("Jawaban sebagian", { exact: true })).toBeVisible();
  await expect(page.getByText("Keyakinan evidence: partial (55%).")).toBeVisible();
  await expect(
    page.getByText("Bukti langsung tersedia untuk BI, tetapi belum ditemukan untuk OJK."),
  ).toBeVisible();
});
