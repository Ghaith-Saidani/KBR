import {
  test,
  expect,
} from "@playwright/test";

test.describe(
  "Protected routes",
  () => {
    const routes = [
      "/account",
      "/notifications",
      "/admin",
      "/admin/members",
      "/admin/events",
      "/admin/news",
      "/admin/activities",
      "/admin/contact",
      "/admin/statistics",
    ];

    for (const route of routes) {
      test(`${route} redirects unauthenticated users`, async ({
        page,
      }) => {
        await page.goto(route);

        await expect(
          page,
        ).toHaveURL(
          /\/login/,
        );
      });
    }
  },
);