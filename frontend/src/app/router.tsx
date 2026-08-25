import { createBrowserRouter } from "react-router-dom";

import { ProtectedRoute } from "../components/common/ProtectedRoute";
import MainLayout from "../components/layout/MainLayout";
import PublicLayout from "../components/layout/PublicLayout";

import AccountPage from "../pages/AccountPage";
import HomePage from "../pages/HomePage";
import LoginPage from "../pages/LoginPage";
import MemberProfilePage from "../pages/MemberProfilePage";
import MembersPage from "../pages/MembersPage";
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
        path: "*",
        element: <NotFoundPage />,
      },
    ],
  },
]);