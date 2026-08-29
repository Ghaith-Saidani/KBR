import {
  beforeEach,
  describe,
  expect,
  it,
  vi,
} from "vitest";

import {
  screen,
  fireEvent,
  waitFor,
} from "@testing-library/react";

import { render } from "../test-utils";

import LoginPage from "../../pages/LoginPage";

const mockNavigate = vi.fn();

vi.mock(
  "react-router-dom",
  async () => {
    const actual =
      await vi.importActual<
        typeof import("react-router-dom")
      >("react-router-dom");

    return {
      ...actual,

      useNavigate: () =>
        mockNavigate,

      useLocation: () => ({
        pathname: "/login",
        state: null,
      }),
    };
  },
);

const mockMutate = vi.fn();

vi.mock(
  "../../features/auth/auth.hooks",
  () => ({
    useLogin: () => ({
      mutate: mockMutate,
      isPending: false,
      isError: false,
      error: null,
    }),
  }),
);

describe("LoginPage", () => {
    beforeEach(() => {
        vi.clearAllMocks();
        });
  it("renders login form", () => {
    render(<LoginPage />);

    expect(
      screen.getByLabelText(
        "Adresse e-mail",
      ),
    ).toBeInTheDocument();

    expect(
      screen.getByLabelText(
        "Mot de passe",
      ),
    ).toBeInTheDocument();

    expect(
      screen.getByRole("button", {
        name: "Se connecter",
      }),
    ).toBeInTheDocument();
  });

  it("submits credentials", async () => {
    render(<LoginPage />);

    fireEvent.change(
      screen.getByLabelText(
        "Adresse e-mail",
      ),
      {
        target: {
          value: "admin@kbr.tn",
        },
      },
    );

    fireEvent.change(
      screen.getByLabelText(
        "Mot de passe",
      ),
      {
        target: {
          value: "KBRdemo2026!",
        },
      },
    );

    fireEvent.submit(
      screen
        .getByRole("button", {
          name: "Se connecter",
        })
        .closest("form")!,
    );

    await waitFor(() => {
      expect(
        mockMutate,
      ).toHaveBeenCalledWith({
        email: "admin@kbr.tn",
        password: "KBRdemo2026!",
      });
    });
  });
});