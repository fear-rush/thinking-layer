import { expect, test } from "../fixtures";
import { submitQuestion } from "../helpers";

test("submits optional feedback with the query request id", async ({ page }) => {
  // 1. Submit a question and add an optional feedback comment.
  await submitQuestion(page, "Apa ketentuan BI tentang penyedia jasa pembayaran?");
  await page.getByRole("textbox", { name: "Komentar opsional" }).fill("Kutipannya jelas.");

  // 2. Submit negative feedback and verify the API request contract.
  const feedbackRequestPromise = page.waitForRequest(
    (request) => request.url().endsWith("/v1/feedback") && request.method() === "POST",
  );
  await page.getByRole("button", { name: "Belum membantu" }).click();
  const feedbackRequest = await feedbackRequestPromise;

  expect(feedbackRequest.postDataJSON()).toEqual({
    request_id: "browser-answerable",
    helpful: false,
    comment: "Kutipannya jelas.",
  });
  await expect(
    page.getByText("Terima kasih. Umpan balik Anda sudah dicatat secara lokal."),
  ).toBeVisible();
});
