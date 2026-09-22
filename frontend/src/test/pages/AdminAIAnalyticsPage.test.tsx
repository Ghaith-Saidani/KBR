import {
  beforeEach,
  describe,
  expect,
  it,
  vi,
} from "vitest";

import {
  fireEvent,
  screen,
  waitFor,
} from "@testing-library/react";

import { render } from "../test-utils";

import AdminAIAnalyticsPage from "../../pages/AdminAIAnalyticsPage";

const {
  mockAnalyticsMutate,
  mockAnalyticsState,
} = vi.hoisted(() => ({
  mockAnalyticsMutate: vi.fn(),

  mockAnalyticsState: {
    data: null as unknown,
    isPending: false,
    isError: false,
  },
}));

const mockOverview = {
  members: {
    total: 13,
    pending: 0,
    active: 13,
    suspended: 0,
    inactive: 0,
    archived: 0,
  },

  users: {
    total: 14,
    members: 13,
    staff: 1,
    admins: 1,
  },

  events: {
    total: 7,
    draft: 0,
    published: 7,
    cancelled: 0,
    upcoming: 7,
    past: 0,
  },

  activities: {
    total: 9,
    draft: 0,
    published: 9,
    upcoming: 9,
    past: 0,
  },

  news: {
    total: 8,
    draft: 0,
    published: 8,
  },
};

const mockTrends = {
  months: [
    {
      month: "2026-04",
      members: 0,
      events: 0,
      activities: 0,
      news: 0,
    },
    {
      month: "2026-05",
      members: 0,
      events: 0,
      activities: 0,
      news: 0,
    },
    {
      month: "2026-06",
      members: 0,
      events: 0,
      activities: 0,
      news: 0,
    },
    {
      month: "2026-07",
      members: 0,
      events: 0,
      activities: 0,
      news: 0,
    },
    {
      month: "2026-08",
      members: 13,
      events: 7,
      activities: 9,
      news: 8,
    },
    {
      month: "2026-09",
      members: 0,
      events: 0,
      activities: 0,
      news: 0,
    },
  ],
};

vi.mock(
  "../../features/statistics/statistics.hooks",
  () => ({
    useStatisticsOverview: () => ({
      data: mockOverview,
      isLoading: false,
      isError: false,
    }),

    useStatisticsTrends: () => ({
      data: mockTrends,
      isLoading: false,
      isError: false,
    }),
  }),
);

vi.mock(
  "../../features/analytics/analytics.hooks",
  () => ({
    useAnalyticsQuery: () => ({
      mutate: mockAnalyticsMutate,
      data: mockAnalyticsState.data,
      isPending: mockAnalyticsState.isPending,
      isError: mockAnalyticsState.isError,
    }),
  }),
);

describe(
  "AdminAIAnalyticsPage",
  () => {
    beforeEach(() => {
      mockAnalyticsMutate.mockReset();

      mockAnalyticsState.data = null;
      mockAnalyticsState.isPending = false;
      mockAnalyticsState.isError = false;
    });

    it(
      "renders the analytics page",
      () => {
        render(
          <AdminAIAnalyticsPage />,
        );

        expect(
          screen.getByRole("heading", {
            name: "AI Analytics",
          }),
        ).toBeInTheDocument();

        expect(
          screen.getByRole("heading", {
            name: "Indicateurs clés",
          }),
        ).toBeInTheDocument();

        expect(
          screen.getByRole("heading", {
            name: "Évolution mensuelle",
          }),
        ).toBeInTheDocument();

        expect(
          screen.getByText(
            "Membres enregistrés",
          ),
        ).toBeInTheDocument();

        expect(
          screen.getByText(
            "Événements enregistrés",
          ),
        ).toBeInTheDocument();

        expect(
          screen.getByText(
            "Activités enregistrées",
          ),
        ).toBeInTheDocument();

        expect(
          screen.getByText(
            "Articles enregistrés",
          ),
        ).toBeInTheDocument();
      },
    );

    it(
      "renders the current KPI values",
      () => {
        render(
          <AdminAIAnalyticsPage />,
        );

        expect(
          screen.getByText("13", {
            selector: "p",
          }),
        ).toBeInTheDocument();

        expect(
          screen.getByText("7", {
            selector: "p",
          }),
        ).toBeInTheDocument();

        expect(
          screen.getByText("9", {
            selector: "p",
          }),
        ).toBeInTheDocument();

        expect(
          screen.getByText("8", {
            selector: "p",
          }),
        ).toBeInTheDocument();
      },
    );

    it(
      "renders the analyst section",
      () => {
        render(
          <AdminAIAnalyticsPage />,
        );

        expect(
          screen.getByRole("heading", {
            name: "Interroger les données KBR",
          }),
        ).toBeInTheDocument();

        expect(
          screen.getByPlaceholderText(
            "Ex. Combien d'événements avons-nous ?",
          ),
        ).toBeInTheDocument();

        expect(
          screen.getByRole("button", {
            name: "Analyser",
          }),
        ).toBeInTheDocument();

        expect(
          screen.getByText(
            "Questions rapides",
          ),
        ).toBeInTheDocument();
      },
    );

    it(
      "submits a natural-language query",
      async () => {
        render(
          <AdminAIAnalyticsPage />,
        );

        const input =
          screen.getByPlaceholderText(
            "Ex. Combien d'événements avons-nous ?",
          );

        fireEvent.change(
          input,
          {
            target: {
              value:
                "Combien d'événements KBR compte-t-il ?",
            },
          },
        );

        fireEvent.submit(
          input.closest("form")!,
        );

        await waitFor(() => {
          expect(
            mockAnalyticsMutate,
          ).toHaveBeenCalledWith(
            "Combien d'événements KBR compte-t-il ?",
          );
        });
      },
    );

    it(
      "submits a quick question",
      async () => {
        render(
          <AdminAIAnalyticsPage />,
        );

        fireEvent.click(
          screen.getByRole(
            "button",
            {
              name:
                "Combien d'événements KBR compte-t-il ?",
            },
          ),
        );

        await waitFor(() => {
          expect(
            mockAnalyticsMutate,
          ).toHaveBeenCalledWith(
            "Combien d'événements KBR compte-t-il ?",
          );
        });
      },
    );

    it(
      "renders the initial analyst state",
      () => {
        render(
          <AdminAIAnalyticsPage />,
        );

        expect(
          screen.getByText(
            /Posez une question sur KBR/i,
          ),
        ).toBeInTheDocument();
      },
    );

    it(
        "does not invent an analytics result",
        () => {
            mockAnalyticsState.data = null;
            mockAnalyticsState.isPending = false;
            mockAnalyticsState.isError = false;

            render(
            <AdminAIAnalyticsPage />,
            );

            expect(
            screen.getByText(
                /Posez une question sur KBR/i,
            ),
            ).toBeInTheDocument();

            /*
            * "Résultat vérifié" is also the title of the
            * architecture step, so it cannot be used to
            * determine whether an analytics result exists.
            *
            * "Requête analysée" only appears after a query
            * has actually been submitted.
            */
            expect(
            screen.queryByText(
                "Requête analysée",
            ),
            ).not.toBeInTheDocument();

            expect(
            screen.queryByText(
                "Tendance vérifiée",
            ),
            ).not.toBeInTheDocument();

            expect(
            screen.queryByText(
                "Comparaison vérifiée",
            ),
            ).not.toBeInTheDocument();

            expect(
            screen.queryByText(
                "Cette statistique n'est pas encore supportée.",
            ),
            ).not.toBeInTheDocument();
        },
        );

    it(
      "renders the loading state",
      () => {
        mockAnalyticsState.isPending = true;

        render(
          <AdminAIAnalyticsPage />,
        );

        expect(
          screen.getByText(
            /Analyse.*cours/i,
          ),
        ).toBeInTheDocument();
      },
    );

    it(
      "renders the error state",
      () => {
        mockAnalyticsState.isError = true;

        render(
          <AdminAIAnalyticsPage />,
        );

        expect(
          screen.getByText(
            /Impossible d'exécuter cette analyse/i,
          ),
        ).toBeInTheDocument();
      },
    );
  },
);