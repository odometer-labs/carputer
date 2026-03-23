import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/svelte";
import ErrorPage from "../pages/ErrorPage.svelte";
import type { AppError } from "../stores/errorStore";

function createFatalError(overrides: Partial<AppError> = {}): AppError {
  return {
    id: 1,
    severity: "vital",
    message: "Map renderer crashed",
    source: "home-map-page",
    timestamp: 1704067200000,
    ...overrides,
  };
}

describe("ErrorPage", () => {
  it("renders fatal error details", () => {
    const error = createFatalError();

    render(ErrorPage, {
      props: {
        error,
        onReload: vi.fn(),
      },
    });

    const alert = screen.getByRole("alert");
    expect(
      screen.getByRole("heading", { name: "System Error" }),
    ).toBeInTheDocument();
    expect(screen.getByText(/cannot continue safely/i)).toBeInTheDocument();
    expect(alert).toHaveTextContent(`Message: ${error.message}`);
    expect(alert).toHaveTextContent(`Source: ${error.source}`);
    expect(alert).toHaveTextContent(/Time:/i);
  });

  it("calls onReload when reload button is clicked", async () => {
    const onReload = vi.fn();

    render(ErrorPage, {
      props: {
        error: createFatalError(),
        onReload,
      },
    });

    await fireEvent.click(screen.getByRole("button", { name: /reload app/i }));
    expect(onReload).toHaveBeenCalledTimes(1);
  });

  it("hides source line when source is missing", () => {
    render(ErrorPage, {
      props: {
        error: createFatalError({ source: undefined }),
        onReload: vi.fn(),
      },
    });

    expect(screen.queryByText(/^Source:/i)).not.toBeInTheDocument();
  });
});
