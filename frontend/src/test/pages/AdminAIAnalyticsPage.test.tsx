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
    created_this_month: 13,
    created_last_month: 0,
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
    created_this_month: 7,
    created_last_month: 0,
  },

  activities: {
    total: 9,
    draft: 0,
    published: 9,
    upcoming: 9,
    past: 0,
    created_this_month: 9,
    created_last_month: 0,
  },

  news: {
    total: 8,
    draft: 0,
    published: 8,
    created_this_month: 8,
    created_last_month: 0,
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

const mockRecentActivity = {
  activities: [
    {
      id: "activity-1",
      action: "MEMBER_UPDATED",
      resource_type: "member",
      resource_id:
        "e3863d63-a18f-4829-b4f1-41c65bcec231",
      details: 'Updated member "Testt Test"',
      occurred_at:
        "2026-09-20T13:28:06.369368Z",
      user_id:
        "30ca6978-9186-4de0-9cfb-7d46181a9be4",
    },
    {
      id: "activity-2",
      action: "EVENT_UPDATED",
      resource_type: "event",
      resource_id:
        "b741a583-4069-4ac5-af50-4e823ba3a0a0",
      details:
        'Updated event "Atelier Création de Contenu 1"',
      occurred_at:
        "2026-09-20T13:14:54.113149Z",
      user_id:
        "30ca6978-9186-4de0-9cfb-7d46181a9be4",
    },
    {
      id: "activity-3",
      action: "EVENT_PUBLISHED",
      resource_type: "event",
      resource_id: null,
      details:
        "SEED:2026-09-10: Événement publié #105",
      occurred_at:
        "2026-09-10T14:08:00Z",
      user_id:
        "098d986f-5690-4e01-a095-c6ae49f0ba0f",
    },
  ],
};

const mockRecentBusinessActivityState = {
  data: mockRecentActivity,
  isLoading: false,
  isError: false,
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

    useRecentBusinessActivity: () =>
      mockRecentBusinessActivityState,
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

      mockRecentBusinessActivityState.data =
        mockRecentActivity;

      mockRecentBusinessActivityState.isLoading =
        false;

      mockRecentBusinessActivityState.isError =
        false;
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

        const totalLabels = [
          "Membres",
          "Événements",
          "Activités",
          "Actualités",
        ];

        for (const label of totalLabels) {
          const labelElement = screen.getByText(label, {
            selector: "p",
          });

          const card = labelElement.closest("div.rounded-2xl");

          expect(card).not.toBeNull();

          expect(
            card?.querySelector(
              "p.mt-3.text-4xl.font-black",
            ),
          ).toBeInTheDocument();
        }

        expect(
          screen.getByText("13", {
            selector: "p.mt-3.text-4xl.font-black",
          }),
        ).toBeInTheDocument();

        expect(
          screen.getByText("7", {
            selector: "p.mt-3.text-4xl.font-black",
          }),
        ).toBeInTheDocument();

        expect(
          screen.getByText("9", {
            selector: "p.mt-3.text-4xl.font-black",
          }),
        ).toBeInTheDocument();

        expect(
          screen.getByText("8", {
            selector: "p.mt-3.text-4xl.font-black",
          }),
        ).toBeInTheDocument();
      },
    );

    it(
      "renders recent business activity",
      () => {
        render(
          <AdminAIAnalyticsPage />,
        );

        expect(
          screen.getByRole("heading", {
            name: "Activité récente",
          }),
        ).toBeInTheDocument();

        expect(
          screen.getByText("Membre modifié"),
        ).toBeInTheDocument();

        expect(
          screen.getByText("Événement modifié"),
        ).toBeInTheDocument();

        expect(
          screen.getByText("Événement publié"),
        ).toBeInTheDocument();

        expect(
          screen.getByText(
            'Updated member "Testt Test"',
          ),
        ).toBeInTheDocument();

        expect(
          screen.getByText(
            'Updated event "Atelier Création de Contenu 1"',
          ),
        ).toBeInTheDocument();

        expect(
          screen.getByText(
            "Événement publié #105",
          ),
        ).toBeInTheDocument();

        expect(
          screen.getByRole("link", {
            name: /Voir tous les journaux/i,
          }),
        ).toHaveAttribute(
          "href",
          "/admin/activity-logs",
        );
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

    it(
      "renders the recent activity loading state",
      () => {
        mockRecentBusinessActivityState.isLoading =
          true;

        render(
          <AdminAIAnalyticsPage />,
        );

        expect(
          screen.getByRole("heading", {
            name: "Activité récente",
          }),
        ).toBeInTheDocument();

        expect(
          screen.queryByText(
            "Membre modifié",
          ),
        ).not.toBeInTheDocument();
      },
    );

    it(
      "renders the recent activity error state",
      () => {
        mockRecentBusinessActivityState.isError =
          true;

        render(
          <AdminAIAnalyticsPage />,
        );

        expect(
          screen.getByText(
            /Impossible de charger l'activité récente/i,
          ),
        ).toBeInTheDocument();
      },
    );
  },
);