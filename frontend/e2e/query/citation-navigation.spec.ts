import { expect, test } from "../fixtures";
import { submitQuestion } from "../helpers";

test("opens the cited source block", async ({ context, page }) => {
  // 1. Submit an answerable question and locate its source citation.
  await submitQuestion(page, "Apa ketentuan BI tentang penyedia jasa pembayaran?");
  const citation = page.getByRole("link", {
    name: /Penyedia jasa pembayaran wajib memenuhi ketentuan BI/,
  });

  // 2. Open the citation through the same-origin document-block API route.
  const citationPagePromise = context.waitForEvent("page");
  await citation.click();
  const citationPage = await citationPagePromise;
  await citationPage.waitForLoadState();

  await expect(citationPage).toHaveURL(/\/v1\/documents\/bi-pjp\/blocks\/bi-pjp-1$/);
  await expect(citationPage.locator("body")).toContainText(
    "Penyedia jasa pembayaran wajib memenuhi ketentuan BI.",
  );
});
