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

export interface RegistroPayload {
  nome: string;
  email: string;
  senha: string;
  termosAceitos: boolean;
}

export interface RegistroResponse {
  id: string;
  nome: string;
  email: string;
  mensagem: string;
}

export class RegistroError extends Error {}

export async function registrarUsuario(
  dados: RegistroPayload
): Promise<RegistroResponse> {
  const response = await fetch(`${API_URL}/auth/registro`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      nome: dados.nome,
      email: dados.email,
      senha: dados.senha,
      termos_aceitos: dados.termosAceitos,
    }),
  });

  if (response.status === 409) {
    throw new RegistroError("Este e-mail já está em uso.");
  }
  if (!response.ok) {
    throw new RegistroError("Não foi possível concluir o cadastro.");
  }

  return response.json();
}
