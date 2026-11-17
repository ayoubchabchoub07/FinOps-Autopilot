import { useCallback, useEffect, useState } from "react";

type Connection = "loading" | "ready" | "error";

export default function App() {
  const [connection, setConnection] = useState<Connection>("loading");

  const checkHealth = useCallback(async (signal?: AbortSignal) => {
    setConnection("loading");
    try {
      const response = await fetch("/api/health/ready", {
        signal: signal ?? AbortSignal.timeout(8000),
      });
      if (!response.ok) throw new Error("API not ready");
      const health = await response.json();
      if (
        health.status !== "ready" ||
        health.mode !== "local" ||
        health.cloud_enabled !== false
      ) {
        throw new Error("Unsupported API response");
      }
      setConnection("ready");
    } catch {
      if (!signal?.aborted) setConnection("error");
    }
  }, []);

  useEffect(() => {
    const controller = new AbortController();
    const timeout = setTimeout(() => {
      controller.abort();
      setConnection("error");
    }, 8000);
    void checkHealth(controller.signal).finally(() => clearTimeout(timeout));
    return () => {
      clearTimeout(timeout);
      controller.abort();
    };
  }, [checkHealth]);

  return (
    <main>
      <header>
        <a className="brand" href="/">
          FinOps Autopilot
        </a>
        <span className="badge">LOCAL · DEMO</span>
      </header>
      <section className="intro">
        <p className="eyebrow">Votre espace de travail</p>
        <h1>Les fondations de votre suivi cloud.</h1>
        <p className="description">
          Un environnement local pour préparer l’analyse de vos dépenses, sans
          connexion à un compte cloud.
        </p>
      </section>
      <section className="service-grid" aria-label="Services locaux">
        <article className="card">
          <p className="eyebrow">Connexion</p>
          <h2>Service de données</h2>
          {connection === "loading" && (
            <p role="status">Vérification de l’API…</p>
          )}
          {connection === "ready" && (
            <p className="success" role="status">
              API disponible
            </p>
          )}
          {connection === "error" && (
            <div>
              <p role="alert">
                API indisponible. Vérifiez que les services locaux sont
                démarrés.
              </p>
              <button onClick={() => void checkHealth()}>Réessayer</button>
            </div>
          )}
        </article>
        <article className="card">
          <p className="eyebrow">Visualisation</p>
          <h2>Grafana</h2>
          <p>
            Accédez à votre espace local avec vos identifiants de développement.
          </p>
          <a className="action" href="/grafana/">
            Ouvrir Grafana
          </a>
        </article>
      </section>
      <aside className="empty-state">
        <h2>Les données viendront ensuite</h2>
        <p>
          Aucune donnée de coût n’est connectée à cette interface pour le
          moment.
        </p>
        <p>
          Les jeux de démonstration restent distincts de vos futures données
          réelles.
        </p>
      </aside>
      <footer>FinOps Autopilot · Environnement de développement local</footer>
    </main>
  );
}
