"use client";

import { useEffect, useState } from "react";
import { fetchAllServicesStatus, ServiceStatus } from "@/lib/api";

export default function Home() {
  const [services, setServices] = useState<ServiceStatus[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadServices() {
      try {
        const data = await fetchAllServicesStatus();
        setServices(data);
      } catch (err) {
        setError("Erro ao carregar status dos serviços");
      } finally {
        setLoading(false);
      }
    }

    loadServices();
  }, []);

  return (
    <div className="container">
      <header>
        <h1>Movecity</h1>
        <p className="subtitle">Mobilidade Urbana Colaborativa</p>
      </header>

      <main>
        <h2>Status dos Serviços</h2>

        {loading && <p>Carregando...</p>}

        {error && <p className="status-error">{error}</p>}

        {!loading && !error && (
          <div className="services-grid">
            {services.map((service) => (
              <div key={service.service} className="service-card">
                <h3 className="service-name">{service.service}</h3>
                <span
                  className={`service-status ${
                    service.status === "ok" ? "status-ok" : "status-error"
                  }`}
                >
                  {service.status === "ok" ? "Online" : "Offline"}
                </span>
              </div>
            ))}
          </div>
        )}
      </main>

      <footer>
        <p>Movecity — TCC Grupo Segurança UCB</p>
      </footer>
    </div>
  );
}
