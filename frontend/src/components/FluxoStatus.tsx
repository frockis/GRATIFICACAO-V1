import type { StatusIndicador } from '../types';

const ETAPAS: StatusIndicador[] = ['Rascunho', 'Enviado', 'Em revisão', 'Devolvido', 'Validado', 'Fechado'];

export function FluxoStatus({ atual }: { atual: StatusIndicador }) {
  const indexAtual = ETAPAS.indexOf(atual);
  return (
    <div className="flow-track">
      {ETAPAS.map((etapa, idx) => (
        <span key={etapa} style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
          <span
            className={`flow-step${etapa === atual ? ' active' : idx < indexAtual && etapa !== 'Devolvido' ? ' done' : ''}`}
          >
            {etapa}
          </span>
          {idx < ETAPAS.length - 1 && <span className="flow-arrow">→</span>}
        </span>
      ))}
    </div>
  );
}
