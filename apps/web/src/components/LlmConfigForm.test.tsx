import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { LlmConfigForm } from "./LlmConfigForm";

vi.mock("sonner", () => ({
  toast: { success: vi.fn(), error: vi.fn() },
}));

import { toast } from "sonner";

describe("LlmConfigForm", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it("renders form fields with fetched config", async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({ section: "llm", config: { provider: "openrouter", baseUrl: "https://openrouter.ai/api/v1", model: "claude-sonnet" } }),
    });

    render(<LlmConfigForm />);

    await waitFor(() => {
      expect(screen.getByDisplayValue("openrouter")).toBeDefined();
    });
  });

  it("saves and shows success toast", async () => {
    const user = userEvent.setup();

    global.fetch = vi.fn()
      .mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ section: "llm", config: { provider: "openrouter", baseUrl: "", model: "" } }),
      })
      .mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ ok: true, section: "llm" }),
      });

    render(<LlmConfigForm />);

    await waitFor(() => screen.getByDisplayValue("openrouter"));

    const providerInput = screen.getByLabelText(/provider/i);
    await user.clear(providerInput);
    await user.type(providerInput, "anthropic");

    await user.click(screen.getByRole("button", { name: /save/i }));

    await waitFor(() => {
      expect(toast.success).toHaveBeenCalledWith("LLM configuration saved.");
    });
  });
});
