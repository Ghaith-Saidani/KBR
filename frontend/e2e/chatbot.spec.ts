import {
  test,
  expect,
} from "@playwright/test";

test.describe("KBR AI Chatbot", () => {
  test.beforeEach(async ({
    page,
  }) => {
    await page.goto("/");
  });

  test("chatbot button is visible", async ({
    page,
  }) => {
    const button =
      page.getByRole(
        "button",
        {
          name: "Ouvrir l'assistant KBR",
        },
      );

    await expect(
      button,
    ).toBeVisible();
  });

  test("chatbot opens", async ({
    page,
  }) => {
    await page
      .getByRole(
        "button",
        {
          name: "Ouvrir l'assistant KBR",
        },
      )
      .click();

    await expect(
      page.getByRole(
        "region",
        {
          name: "Assistant KBR",
        },
      ),
    ).toBeVisible();

    await expect(
      page.getByText(
        "KBR AI",
      ),
    ).toBeVisible();

    await expect(
      page.getByText(
        "Suggestions",
      ),
    ).toBeVisible();
  });

  test("suggestions are displayed", async ({
    page,
  }) => {
    await page
      .getByRole(
        "button",
        {
          name: "Ouvrir l'assistant KBR",
        },
      )
      .click();

    await expect(
      page.getByRole(
        "button",
        {
          name: "Quand est le prochain événement ?",
        },
      ),
    ).toBeVisible();

    await expect(
      page.getByRole(
        "button",
        {
          name: "Comment rejoindre KBR ?",
        },
      ),
    ).toBeVisible();

    await expect(
      page.getByRole(
        "button",
        {
          name: "Quelles activités propose KBR ?",
        },
      ),
    ).toBeVisible();
  });

  test("empty message cannot be submitted", async ({
    page,
  }) => {
    await page
      .getByRole(
        "button",
        {
          name: "Ouvrir l'assistant KBR",
        },
      )
      .click();

    const sendButton =
      page.getByRole(
        "button",
        {
          name: "Envoyer le message",
        },
      );

    await expect(
      sendButton,
    ).toBeDisabled();
  });

test("chatbot can close", async ({
  page,
}) => {
  await page
    .getByRole(
      "button",
      {
        name: "Ouvrir l'assistant KBR",
        exact: true,
      },
    )
    .click();

  await expect(
    page.getByRole(
      "region",
      {
        name: "Assistant KBR",
      },
    ),
  ).toBeVisible();

  await page
    .getByRole(
      "button",
      {
        name: "Fermer l'assistant",
        exact: true,
      },
    )
    .click();

  await expect(
    page.getByRole(
      "button",
      {
        name: "Ouvrir l'assistant KBR",
        exact: true,
      },
    ),
  ).toBeVisible();

  await expect(
    page.getByRole(
      "button",
      {
        name: "Fermer l'assistant",
        exact: true,
      },
    ),
  ).toBeHidden();
});
});