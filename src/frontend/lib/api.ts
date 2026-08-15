const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export interface ServiceStatus {
  service: string;
  status: string;
}

export async function fetchServiceStatus(
  service: string
): Promise<ServiceStatus> {
  const response = await fetch(`${API_URL}/${service}/hello`);
  if (!response.ok) {
    throw new Error(`Erro ao buscar status do serviço ${service}`);
  }
  return response.json();
}

export async function fetchAllServicesStatus(): Promise<
  ServiceStatus[]
> {
  const services = ["gateway", "auth", "mobilidade", "colaboracao"];
  const results = await Promise.allSettled(
    services.map((service) => fetchServiceStatus(service))
  );

  return results.map((result, index) => ({
    service: services[index],
    status: result.status === "fulfilled" ? result.value.status : "error",
  }));
}
