import { expect, test } from "./fixtures";

test("opens the citation-first query page", async ({ page }) => {
  await expect(
    page.getByRole("heading", { name: "Tanya regulasi keuangan Indonesia." }),
  ).toBeVisible();
});
