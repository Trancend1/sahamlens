import { describe, expect, it } from "vitest";
import HomePage from "@/app/page";

describe("HomePage smoke", () => {
  it("renders without throwing and returns a React element", () => {
    const tree = HomePage();
    expect(tree).toBeTruthy();
    expect(tree.type).toBe("main");
  });
});
