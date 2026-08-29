import {
  test,
  expect,
} from "@playwright/test";

test.describe("Authentication", () => {
  test("login page displays authentication form", async ({
    page,
  }) => {
    await page.goto("/login");

    await expect(
      page.getByLabel(
        "Adresse e-mail",
        { exact: true },
      ),
    ).toBeVisible();

    await expect(
      page.getByLabel(
        "Mot de passe",
        { exact: true },
      ),
    ).toBeVisible();

    await expect(
      page.getByRole(
        "button",
        {
          name: "Se connecter",
          exact: true,
        },
      ),
    ).toBeVisible();

    await expect(
      page.getByRole(
        "link",
        {
          name: "Créer un compte",
          exact: true,
        },
      ),
    ).toBeVisible();
  });

  test("register page displays registration form", async ({
    page,
  }) => {
    await page.goto("/register");

    await expect(
      page.getByLabel(
        "Prénom",
        { exact: true },
      ),
    ).toBeVisible();

    await expect(
      page.getByLabel(
        "Nom",
        { exact: true },
      ),
    ).toBeVisible();

    await expect(
      page.getByLabel(
        "Adresse e-mail",
        { exact: true },
      ),
    ).toBeVisible();

    await expect(
    page.getByLabel(
        "Téléphone (facultatif)",
        { exact: true },
    ),
    ).toBeVisible();

    await expect(
      page.getByLabel(
        "Mot de passe",
        { exact: true },
      ),
    ).toBeVisible();

    await expect(
      page.getByLabel(
        "Confirmer le mot de passe",
        { exact: true },
      ),
    ).toBeVisible();
  });

  test("register validates mismatched passwords", async ({
    page,
  }) => {
    await page.goto("/register");

    await page
      .getByLabel(
        "Prénom",
        { exact: true },
      )
      .fill("Test");

    await page
      .getByLabel(
        "Nom",
        { exact: true },
      )
      .fill("User");

    await page
      .getByLabel(
        "Adresse e-mail",
        { exact: true },
      )
      .fill(
        `test-${Date.now()}@example.com`,
      );

    await page
      .getByLabel(
        "Mot de passe",
        { exact: true },
      )
      .fill("Password123!");

    await page
      .getByLabel(
        "Confirmer le mot de passe",
        { exact: true },
      )
      .fill("Different123!");

    await page
      .getByRole(
        "button",
        {
          name: "Créer mon compte",
          exact: true,
        },
      )
      .click();

    await expect(
      page.getByText(
        "Les mots de passe ne correspondent pas.",
        { exact: true },
      ),
    ).toBeVisible();
  });

  test("protected account redirects unauthenticated user", async ({
    page,
  }) => {
    await page.goto("/account");

    await expect(page).toHaveURL(
      /\/login$/,
    );
  });

  test("protected notifications redirects unauthenticated user", async ({
    page,
  }) => {
    await page.goto(
      "/notifications",
    );

    await expect(page).toHaveURL(
      /\/login$/,
    );
  });

  test("admin page redirects unauthenticated user", async ({
    page,
  }) => {
    await page.goto("/admin");

    await expect(page).toHaveURL(
      /\/login$/,
    );
  });
});