import type { StatusIndicador, StatusCompetencia } from '../types';

const CLASS_MAP: Record<string, string> = {
  Rascunho: 'badge-rascunho',
  Enviado: 'badge-enviado',
  'Em revisão': 'badge-em-revisao',
  Devolvido: 'badge-devolvido',
  Validado: 'badge-validado',
  Fechado: 'badge-fechado',
  Aberto: 'badge-enviado',
};

export function StatusBadge({ status }: { status: StatusIndicador | StatusCompetencia }) {
  const cls = CLASS_MAP[status] ?? 'badge-rascunho';
  return (
    <span className={`badge ${cls}`}>
      <span className="badge-dot" />
      {status}
    </span>
  );
}
