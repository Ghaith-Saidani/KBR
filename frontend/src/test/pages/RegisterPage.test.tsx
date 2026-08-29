import {
  describe,
  expect,
  it,
  vi,
} from "vitest";

import {
  screen,
  fireEvent,
} from "@testing-library/react";

import {
  render,
} from "../test-utils";

import RegisterPage from "../../pages/RegisterPage";

const mockNavigate =
  vi.fn();

vi.mock(
  "react-router-dom",
  async () => {
    const actual =
      await vi.importActual<
        typeof import(
          "react-router-dom"
        )
      >("react-router-dom");

    return {
      ...actual,

      useNavigate: () =>
        mockNavigate,
    };
  },
);

const mockMutate =
  vi.fn();

vi.mock(
  "../../src/features/auth/auth.hooks",
  () => ({
    useRegister: () => ({
      mutate: mockMutate,
      isPending: false,
      isError: false,
      error: null,
    }),
  }),
);

describe("RegisterPage", () => {
  it("renders registration fields", () => {
    render(<RegisterPage />);

    expect(
      screen.getByLabelText(
        "Prénom",
      ),
    ).toBeInTheDocument();

    expect(
      screen.getByLabelText(
        "Nom",
      ),
    ).toBeInTheDocument();

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
      screen.getByLabelText(
        "Confirmer le mot de passe",
      ),
    ).toBeInTheDocument();
  });

  it("rejects mismatching passwords", () => {
    render(<RegisterPage />);

    fireEvent.change(
      screen.getByLabelText(
        "Prénom",
      ),
      {
        target: {
          value: "Test",
        },
      },
    );

    fireEvent.change(
      screen.getByLabelText(
        "Nom",
      ),
      {
        target: {
          value: "User",
        },
      },
    );

    fireEvent.change(
      screen.getByLabelText(
        "Adresse e-mail",
      ),
      {
        target: {
          value: "test@example.com",
        },
      },
    );

    fireEvent.change(
      screen.getByLabelText(
        "Mot de passe",
      ),
      {
        target: {
          value: "Password123!",
        },
      },
    );

    fireEvent.change(
      screen.getByLabelText(
        "Confirmer le mot de passe",
      ),
      {
        target: {
          value: "Different123!",
        },
      },
    );

    fireEvent.submit(
      screen.getByRole(
        "button",
        {
          name: "Créer mon compte",
        },
      ).closest("form")!,
    );

    expect(
      screen.getByText(
        "Les mots de passe ne correspondent pas.",
      ),
    ).toBeInTheDocument();

    expect(
      mockMutate,
    ).not.toHaveBeenCalled();
  });
});