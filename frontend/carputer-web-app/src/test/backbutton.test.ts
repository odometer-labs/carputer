import { vi, describe, it, expect } from "vitest";
import { goBack } from "../utils/navigation";
import * as router from "svelte-spa-router";

// mock the push function from router
vi.spyOn(router, "push").mockImplementation(() => Promise.resolve());

describe("BackButton logic", () => {
  it('goBack() calls push("/")', () => {
    goBack();
    expect(router.push).toHaveBeenCalledWith("/");
  });
});
