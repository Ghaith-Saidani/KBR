import {
  render as rtlRender,
  type RenderOptions,
  type RenderResult,
} from "@testing-library/react";

import type { ReactElement } from "react";

import { TestProviders } from "./TestProviders";

export function render(
  ui: ReactElement,
  options?: Omit<
    RenderOptions,
    "wrapper"
  >,
): RenderResult {
  return rtlRender(ui, {
    wrapper: TestProviders,
    ...options,
  });
}