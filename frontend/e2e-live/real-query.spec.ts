import { expect, test } from "../e2e/fixtures";
import { submitQuestion } from "../e2e/helpers";

test("answers the PJP advertising question from the live corpus and opens its citation", async ({
  context,
  page,
}) => {
  await submitQuestion(
    page,
    "apa saja aturan periklanan yang harus dipenuhi oleh penyedia jasa pembayaran?",
  );

  await expect(page.getByText("Jawaban ditemukan", { exact: true })).toBeVisible();
  const answer = page.getByRole("region", { name: "Jawaban" });
  await expect(
    answer.getByText(/menggunakan bahasa Indonesia yang mudah dimengerti/),
  ).toBeVisible();
  await expect(answer.getByText(/testimoni Konsumen dan anjuran \(endorsement\)/)).toBeVisible();
  await expect(answer.getByText(/berizin dan diawasi oleh Bank Indonesia/)).toBeVisible();

  const citationPagePromise = context.waitForEvent("page");
  await page.getByRole("link", { name: /PADG No\.20 Tahun 2023.*Pasal 7, ayat \(1\)/ }).click();
  const citationPage = await citationPagePromise;
  await citationPage.waitForLoadState();

  await expect(citationPage.locator("body")).toContainText(
    "Penyelenggara dalam melakukan kegiatan pemasaran dan iklan",
  );
});
