import type { Page } from "@playwright/test";

export async function submitQuestion(page: Page, question: string) {
  await page.getByRole("textbox", { name: "Pertanyaan regulasi" }).fill(question);
  const responsePromise = page.waitForResponse(
    (response) => response.url().endsWith("/v1/queries") && response.request().method() === "POST",
  );
  await page.getByRole("button", { name: "Cari jawaban" }).click();
  const response = await responsePromise;
  if (!response.ok()) {
    throw new Error(`Query API returned ${response.status()}.`);
  }
}
