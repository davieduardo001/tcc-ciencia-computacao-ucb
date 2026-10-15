import {
  Ban,
  Clock,
  Construction,
  LucideIcon,
  ShieldAlert,
  Siren,
  Users,
  Wrench,
} from "lucide-react";
import { TipoOcorrencia } from "@/lib/api";

/**
 * Rótulo e ícone de cada tipo de ocorrência — usados tanto pelo formulário
 * de reportar (US #23) quanto pela listagem (US #24), pra que o mesmo tipo
 * tenha sempre a mesma cara nas duas telas.
 */
export const TIPOS: { id: TipoOcorrencia; label: string; Icone: LucideIcon }[] = [
  { id: "atraso", label: "Atraso", Icone: Clock },
  { id: "nao_passou", label: "Ônibus não passou", Icone: Ban },
  { id: "lotacao", label: "Lotação", Icone: Users },
  { id: "obra_via", label: "Obra na via", Icone: Construction },
  { id: "onibus_quebrou", label: "Ônibus quebrou", Icone: Wrench },
  { id: "acidente", label: "Acidente", Icone: Siren },
  { id: "seguranca", label: "Segurança", Icone: ShieldAlert },
];
