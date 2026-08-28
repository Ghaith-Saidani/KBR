import {
  createBrowserRouter,
} from "react-router-dom";

import PublicLayout from "../components/layout/PublicLayout";
import {ProtectedRoute} from "../components/common/ProtectedRoute";
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

export const router = createBrowserRouter([
  {
    path: "/",
    element: <PublicLayout />,
    errorElement: <NotFoundPage />,
    children: [
      // ----------------------------------------
      // PUBLIC
      // ----------------------------------------

      {
        index: true,
        element: <HomePage />,
      },

      {
        path: "about",
        element: <AboutPage />,
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
        path: "events/:slug",
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
        path: "contact",
        element: <ContactPage />,
      },

      {
        path: "activities",
        element: <ActivitiesPage />,
      },

      {
        path: "activities/:slug",
        element: <ActivityDetailsPage />,
      },

      // ----------------------------------------
      // AUTHENTICATION
      // ----------------------------------------

      {
        path: "login",
        element: <LoginPage />,
      },

      {
        path: "register",
        element: <RegisterPage />,
      },

      // ----------------------------------------
      // MEMBER AREA
      // ----------------------------------------

      {
        element: <ProtectedRoute />,
        children: [
          {
            path: "account",
            element: <AccountPage />,
          },
        ],
      },

      // ----------------------------------------
      // ADMIN / STAFF
      // ----------------------------------------

      {
        element: (
          <RoleRoute
            roles={["staff", "admin"]}
          />
        ),
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
            path: "admin/members/:id/edit",
            element: <AdminMemberEditPage />,
          },

          {
            path: "admin/events",
            element: <AdminEventsPage />,
          },

          {
            path: "admin/events/create",
            element: <AdminEventCreatePage />,
          },

          {
            path: "admin/events/:id/edit",
            element: <AdminEventEditPage />,
          },

          {
            path: "admin/news",
            element: <AdminNewsPage />,
          },

          {
            path: "admin/news/create",
            element: <AdminNewsCreatePage />,
          },

          {
            path: "admin/news/:id/edit",
            element: <AdminNewsEditPage />,
          },
          
          {
            path: "admin/contact",
            element: <AdminContactPage />,
          },

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
        ],
      },

      // ----------------------------------------
      // FALLBACK
      // ----------------------------------------

      {
        path: "*",
        element: <NotFoundPage />,
      },
    ],
  },
]);