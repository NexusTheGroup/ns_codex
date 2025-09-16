import { readFileSync, existsSync } from "node:fs";
import { it, expect } from "vitest";

it("blueprint.md exists & has content", () => {
  expect(existsSync("blueprint.md")).toBe(true);
  const buf = readFileSync("blueprint.md");
  expect(buf.byteLength).toBeGreaterThan(50);
});

it("docs folder exists", () => {
  expect(existsSync("docs")).toBe(true);
});
