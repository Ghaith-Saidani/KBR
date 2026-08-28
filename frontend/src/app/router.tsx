import {
  createBrowserRouter,
} from "react-router-dom";

import PublicLayout from "../components/layout/PublicLayout";
import { ProtectedRoute } from "../components/common/ProtectedRoute";
import { RoleRoute } from "../components/common/RoleRoute";

import AboutPage from "../pages/AboutPage";
import HomePage from "../pages/HomePage";
import NotFoundPage from "../pages/NotFoundPage";

import LoginPage from "../pages/LoginPage";
import RegisterPage from "../pages/RegisterPage";
import AccountPage from "../pages/AccountPage";

import ContactPage from "../pages/ContactPage";

import MembersPage from "../pages/MembersPage";
import MemberProfilePage from "../pages/MemberProfilePage";

import EventsPage from "../pages/EventsPage";
import EventDetailsPage from "../pages/EventDetailsPage";

import NewsPage from "../pages/NewsPage";
import NewsDetailsPage from "../pages/NewsDetailsPage";

import ActivitiesPage from "../pages/ActivitiesPage";
import ActivityDetailsPage from "../pages/ActivityDetailsPage";

import NotificationsPage from "../pages/NotificationsPage";

import AdminActivitiesPage from "../pages/AdminActivitiesPage";
import AdminActivityCreatePage from "../pages/AdminActivityCreatePage";
import AdminActivityEditPage from "../pages/AdminActivityEditPage";

import AdminDashboardPage from "../pages/AdminDashboardPage";

import AdminMembersPage from "../pages/AdminMembersPage";
import AdminMemberEditPage from "../pages/AdminMemberEditPage";

import AdminEventsPage from "../pages/AdminEventsPage";
import AdminEventCreatePage from "../pages/AdminEventCreatePage";
import AdminEventEditPage from "../pages/AdminEventEditPage";

import AdminNewsPage from "../pages/AdminNewsPage";
import AdminNewsCreatePage from "../pages/AdminNewsCreatePage";
import AdminNewsEditPage from "../pages/AdminNewsEditPage";

import AdminContactPage from "../pages/AdminContactPage";
import AdminStatisticsPage from "../pages/AdminStatisticsPage";

export const router = createBrowserRouter([
  {
    path: "/",
    element: <PublicLayout />,
    errorElement: <NotFoundPage />,

    children: [
      // ============================================================
      // PUBLIC
      // ============================================================

      {
        index: true,
        element: <HomePage />,
      },

      {
        path: "about",
        element: <AboutPage />,
      },

      // ------------------------------------------------------------
      // MEMBERS
      // ------------------------------------------------------------

      {
        path: "members",
        element: <MembersPage />,
      },

      {
        path: "members/:slug",
        element: <MemberProfilePage />,
      },

      // ------------------------------------------------------------
      // EVENTS
      // ------------------------------------------------------------

      {
        path: "events",
        element: <EventsPage />,
      },

      {
        path: "events/:eventId",
        element: <EventDetailsPage />,
      },

      // ------------------------------------------------------------
      // NEWS
      // ------------------------------------------------------------

      {
        path: "news",
        element: <NewsPage />,
      },

      {
        path: "news/:slug",
        element: <NewsDetailsPage />,
      },

      // ------------------------------------------------------------
      // ACTIVITIES
      // ------------------------------------------------------------

      {
        path: "activities",
        element: <ActivitiesPage />,
      },

      {
        path: "activities/:slug",
        element: <ActivityDetailsPage />,
      },

      // ------------------------------------------------------------
      // CONTACT
      // ------------------------------------------------------------

      {
        path: "contact",
        element: <ContactPage />,
      },

      // ============================================================
      // AUTHENTICATION
      // ============================================================

      {
        path: "login",
        element: <LoginPage />,
      },

      {
        path: "register",
        element: <RegisterPage />,
      },

      // ============================================================
      // AUTHENTICATED MEMBER AREA
      // ============================================================

      {
        element: <ProtectedRoute />,
        children: [
          {
            path: "account",
            element: <AccountPage />,
          },

          {
            path: "notifications",
            element: <NotificationsPage />,
          },
        ],
      },

      // ============================================================
      // ADMIN / STAFF
      // ============================================================

      {
        element: (
          <RoleRoute roles={["staff", "admin"]} />
        ),

        children: [
          // --------------------------------------------------------
          // DASHBOARD
          // --------------------------------------------------------

          {
            path: "admin",
            element: <AdminDashboardPage />,
          },

          // --------------------------------------------------------
          // MEMBERS
          // --------------------------------------------------------

          {
            path: "admin/members",
            element: <AdminMembersPage />,
          },

          {
            path: "admin/members/:memberId/edit",
            element: <AdminMemberEditPage />,
          },

          // --------------------------------------------------------
          // EVENTS
          // --------------------------------------------------------

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

          // --------------------------------------------------------
          // NEWS
          // --------------------------------------------------------

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

          // --------------------------------------------------------
          // ACTIVITIES
          // --------------------------------------------------------

          {
            path: "admin/activities",
            element: <AdminActivitiesPage />,
          },

          {
            path: "admin/activities/create",
            element: <AdminActivityCreatePage />,
          },

          {
            path: "admin/activities/:id/edit",
            element: <AdminActivityEditPage />,
          },

          // --------------------------------------------------------
          // CONTACT
          // --------------------------------------------------------

          {
            path: "admin/contact",
            element: <AdminContactPage />,
          },

          // --------------------------------------------------------
          // STATISTICS
          // --------------------------------------------------------
          
          {
            path: "admin/statistics",
            element: <AdminStatisticsPage />,
          },
        ],
      },

      // ============================================================
      // FALLBACK
      // ============================================================

      {
        path: "*",
        element: <NotFoundPage />,
      },
    ],
  },
]);