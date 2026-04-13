import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/svelte";
import ErrorPopup from "../assets/components/ErrorPopup.svelte";
import type { AppError } from "../stores/errorStore";

function createNonFatalError(overrides: Partial<AppError> = {}): AppError {
  return {
    id: 42,
    severity: "non-vital",
    message: "GPS signal lost",
    source: "gps-service",
    timestamp: 1704067200000,
    ...overrides,
  };
}

describe("ErrorPopup", () => {
  it("renders warning information", () => {
    const error = createNonFatalError();

    render(ErrorPopup, {
      props: {
        error,
        onClose: vi.fn(),
      },
    });

    expect(screen.getByRole("alert")).toBeInTheDocument();
    expect(screen.getByText("Warning")).toBeInTheDocument();
    expect(screen.getByText(error.message)).toBeInTheDocument();
    expect(screen.getByText(`Source: ${error.source}`)).toBeInTheDocument();
    expect(screen.getByText(/^Time:/i)).toBeInTheDocument();
  });

  it("calls onClose with error id when dismiss button is clicked", async () => {
    const onClose = vi.fn();
    const error = createNonFatalError({ id: 99 });

    render(ErrorPopup, {
      props: {
        error,
        onClose,
      },
    });

    await fireEvent.click(
      screen.getByRole("button", { name: /dismiss warning/i }),
    );
    expect(onClose).toHaveBeenCalledWith(99);
    expect(onClose).toHaveBeenCalledTimes(1);
  });

  it("hides source line when source is missing", () => {
    render(ErrorPopup, {
      props: {
        error: createNonFatalError({ source: undefined }),
        onClose: vi.fn(),
      },
    });

    expect(screen.queryByText(/^Source:/i)).not.toBeInTheDocument();
  });
});
