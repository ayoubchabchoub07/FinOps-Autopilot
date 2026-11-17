import { fireEvent, render, screen } from "@testing-library/react";
import { expect, test, vi } from "vitest";
import App from "../src/App";

test("shows ready local API and Grafana link without invented costs", async () => {
  vi.stubGlobal(
    "fetch",
    vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({
        status: "ready",
        mode: "local",
        cloud_enabled: false,
      }),
    }),
  );
  render(<App />);
  expect(await screen.findByText("API disponible")).toBeInTheDocument();
  expect(screen.getByRole("link", { name: "Ouvrir Grafana" })).toHaveAttribute(
    "href",
    "/grafana/",
  );
  expect(screen.getByText(/Aucune donnée de coût/)).toBeInTheDocument();
});

test("reports unavailable API and allows a successful retry", async () => {
  const request = vi
    .fn()
    .mockRejectedValueOnce(new Error("offline"))
    .mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        status: "ready",
        mode: "local",
        cloud_enabled: false,
      }),
    });
  vi.stubGlobal("fetch", request);
  render(<App />);
  expect(await screen.findByRole("alert")).toHaveTextContent(
    "API indisponible",
  );
  fireEvent.click(screen.getByRole("button", { name: "Réessayer" }));
  expect(await screen.findByText("API disponible")).toBeInTheDocument();
});

test.each([
  { ok: false, json: async () => ({ status: "not_ready" }) },
  {
    ok: true,
    json: async () => ({
      status: "ready",
      mode: "aws-real",
      cloud_enabled: true,
    }),
  },
])(
  "does not claim readiness on HTTP or invalid configuration responses",
  async (response) => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(response));
    render(<App />);
    expect(await screen.findByRole("alert")).toHaveTextContent(
      "API indisponible",
    );
  },
);
