import type { QuadroHorarios } from "@/lib/api";

/**
 * US #118 — a que horas a linha passa. Mostra o estado de hoje (operando,
 * fora do horário, não opera hoje), a próxima partida e o quadro por dias
 * da semana. Backend antigo (sem `quadro`) não renderiza nada.
 */
export default function QuadroDeHorarios({ quadro }: { quadro?: QuadroHorarios | null }) {
  if (!quadro) return null;

  if (quadro.estado === "sem_horario") {
    return (
      <section className="mapa-horarios" aria-label="Horários da linha">
        <div className="mapa-painel-titulo">Horários</div>
        <p className="mapa-painel-sem-veiculo">
          Não há horário publicado para esta linha.
        </p>
      </section>
    );
  }

  const proxima = quadro.proximaPartida;
  const quando =
    proxima && (proxima.quando === "hoje" ? "hoje" : proxima.quando);

  return (
    <section className="mapa-horarios" aria-label="Horários da linha">
      <div className="mapa-painel-titulo">Horários</div>

      {quadro.estado === "fora_do_horario" && (
        <p className="mapa-horarios-estado">Fora de operação agora.</p>
      )}
      {quadro.estado === "nao_opera_hoje" && (
        <p className="mapa-horarios-estado">Esta linha não opera hoje.</p>
      )}
      {proxima && (
        <p className="mapa-horarios-proxima">
          Próxima partida: <strong>{proxima.horario}</strong> ({quando})
        </p>
      )}
      {quadro.tempoPercursoMin !== null && (
        <p className="mapa-painel-sem-veiculo">
          Viagem completa: cerca de {quadro.tempoPercursoMin} min.
        </p>
      )}

      {quadro.grupos.map((grupo) => (
        <div key={grupo.rotulo} className="mapa-horarios-grupo">
          <strong>
            {grupo.rotulo}
            {grupo.hoje ? " (hoje)" : ""}
          </strong>
          <ul className="mapa-horarios-lista">
            {grupo.horarios.map((h) => {
              const destaque =
                grupo.hoje && proxima?.quando === "hoje" && proxima.horario === h;
              return (
                <li
                  key={h}
                  className={destaque ? "mapa-horario proximo" : "mapa-horario"}
                  aria-current={destaque ? "time" : undefined}
                >
                  {h}
                </li>
              );
            })}
          </ul>
        </div>
      ))}
    </section>
  );
}
