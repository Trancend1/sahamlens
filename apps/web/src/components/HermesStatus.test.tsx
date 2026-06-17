import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { HermesStatus } from "./HermesStatus";

const MOCK_ENABLED_RUNNING = {
  config: { enabled: true, telegramConfigured: true, providerName: "openrouter", providerConfigured: true },
  process: { running: true, pid: 12345 },
};

const MOCK_ENABLED_STOPPED = {
  config: { enabled: true, telegramConfigured: true, providerName: "openrouter", providerConfigured: true },
  process: { running: false, pid: null },
};

const MOCK_DISABLED = {
  config: { enabled: false, telegramConfigured: false, providerName: "not set", providerConfigured: false },
  process: { running: false, pid: null },
};

describe("HermesStatus", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it("renders running state", async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(MOCK_ENABLED_RUNNING),
    });

    render(<HermesStatus />);

    await waitFor(() => {
      expect(screen.getByText("running")).toBeDefined();
    });
    expect(screen.getByText("PID: 12345")).toBeDefined();
  });

  it("renders stopped state with start button", async () => {
    global.fetch = vi.fn()
      .mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(MOCK_ENABLED_STOPPED),
      });

    render(<HermesStatus />);

    await waitFor(() => {
      expect(screen.getByText("stopped")).toBeDefined();
    });

    const startBtn = screen.getByRole("button", { name: /start/i });
    expect(startBtn).toBeDefined();
  });

  it("renders disabled state", async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(MOCK_DISABLED),
    });

    render(<HermesStatus />);

    await waitFor(() => {
      expect(screen.getByText("disabled")).toBeDefined();
    });
  });

  it("starts hermes on button click", async () => {
    const user = userEvent.setup();

    global.fetch = vi.fn()
      .mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(MOCK_ENABLED_STOPPED),
      })
      .mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ ok: true, message: "Hermes started (PID 99999)." }),
      })
      .mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(MOCK_ENABLED_RUNNING),
      });

    render(<HermesStatus />);

    await waitFor(() => {
      expect(screen.getByText("stopped")).toBeDefined();
    });

    await user.click(screen.getByRole("button", { name: /start/i }));

    await waitFor(() => {
      expect(screen.getByText("running")).toBeDefined();
    });
  });
});
