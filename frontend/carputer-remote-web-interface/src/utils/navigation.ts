import { push } from "svelte-spa-router";

/**
 * Navigate back to the home map page. Extracted from component
 * so unit tests can exercise it without mounting a Svelte component.
 */
export function goBack(): Promise<void> {
  return push("/");
}
