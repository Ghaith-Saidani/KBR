import {
  test,
  expect,
} from "@playwright/test";

const publicPages = [
  {
    name: "Home",
    path: "/",
  },
  {
    name: "About",
    path: "/about",
  },
  {
    name: "Members",
    path: "/members",
  },
  {
    name: "Events",
    path: "/events",
  },
  {
    name: "News",
    path: "/news",
  },
  {
    name: "Activities",
    path: "/activities",
  },
  {
    name: "Contact",
    path: "/contact",
  },
  {
    name: "Login",
    path: "/login",
  },
  {
    name: "Register",
    path: "/register",
  },
];

for (const page of publicPages) {
  test(`${page.name} page loads`, async ({
    page: browserPage,
  }) => {
    const response =
      await browserPage.goto(
        page.path,
        {
          waitUntil:
            "domcontentloaded",
        },
      );

    expect(response).not.toBeNull();

    expect(
      response?.status(),
    ).toBeLessThan(400);

    await expect(
      browserPage.locator("body"),
    ).toBeVisible();
  });
}