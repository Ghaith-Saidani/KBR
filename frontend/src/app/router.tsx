import { createBrowserRouter } from "react-router-dom";

import { ProtectedRoute } from "../components/common/ProtectedRoute";
import { RoleRoute } from "../components/common/RoleRoute";

import MainLayout from "../components/layout/MainLayout";
import PublicLayout from "../components/layout/PublicLayout";

import AccountPage from "../pages/AccountPage";
import AdminDashboardPage from "../pages/AdminDashboardPage";
import AdminEventCreatePage from "../pages/AdminEventCreatePage";
import AdminEventEditPage from "../pages/AdminEventEditPage";
import AdminEventsPage from "../pages/AdminEventsPage";
import AdminMemberEditPage from "../pages/AdminMemberEditPage";
import AdminMembersPage from "../pages/AdminMembersPage";
import AdminNewsCreatePage from "../pages/AdminNewsCreatePage";
import AdminNewsEditPage from "../pages/AdminNewsEditPage";
import AdminNewsPage from "../pages/AdminNewsPage";
import EventDetailsPage from "../pages/EventDetailsPage";
import EventsPage from "../pages/EventsPage";
import HomePage from "../pages/HomePage";
import LoginPage from "../pages/LoginPage";
import MemberProfilePage from "../pages/MemberProfilePage";
import MembersPage from "../pages/MembersPage";
import NewsDetailsPage from "../pages/NewsDetailsPage";
import NewsPage from "../pages/NewsPage";
import NotFoundPage from "../pages/NotFoundPage";
import RegisterPage from "../pages/RegisterPage";

export const router = createBrowserRouter([
  {
    path: "/",
    element: <PublicLayout />,
    errorElement: <NotFoundPage />,

    children: [
      {
        index: true,
        element: <HomePage />,
      },

      {
        path: "login",
        element: <LoginPage />,
      },

      {
        path: "register",
        element: <RegisterPage />,
      },

      {
        path: "members",
        element: <MembersPage />,
      },

      {
        path: "members/:slug",
        element: <MemberProfilePage />,
      },

      {
        path: "events",
        element: <EventsPage />,
      },

      {
        path: "events/:eventId",
        element: <EventDetailsPage />,
      },

      {
        path: "news",
        element: <NewsPage />,
      },

      {
        path: "news/:slug",
        element: <NewsDetailsPage />,
      },

      {
        element: <ProtectedRoute />,

        children: [
          {
            element: <MainLayout />,

            children: [
              {
                path: "account",
                element: <AccountPage />,
              },
            ],
          },
        ],
      },

      {
        element: (
          <RoleRoute
            roles={[
              "staff",
              "admin",
            ]}
          />
        ),

        children: [
          {
            element: <MainLayout />,

            children: [
              {
                path: "admin",
                element: <AdminDashboardPage />,
              },

              {
                path: "admin/members",
                element: <AdminMembersPage />,
              },

              {
                path: "admin/members/:memberId/edit",
                element: <AdminMemberEditPage />,
              },

              {
                path: "admin/events",
                element: <AdminEventsPage />,
              },

              {
                path: "admin/events/new",
                element: <AdminEventCreatePage />,
              },

              {
                path: "admin/events/:eventId/edit",
                element: <AdminEventEditPage />,
              },

              {
                path: "admin/news",
                element: <AdminNewsPage />,
              },

              {
                path: "admin/news/new",
                element: <AdminNewsCreatePage />,
              },

              {
                path: "admin/news/:newsId/edit",
                element: <AdminNewsEditPage />,
              },
            ],
          },
        ],
      },

      {
        path: "*",
        element: <NotFoundPage />,
      },
    ],
  },
]);