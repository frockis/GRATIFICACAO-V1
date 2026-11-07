import type { RegistroIndicador } from '../types';
import { INDICADORES_CATALOGO } from '../data/mockData';
import { useApp } from '../context/AppContext';
import { StatusBadge } from './StatusBadge';

interface Props {
  registro: RegistroIndicador;
  onClose: () => void;
}

export function IndicadorDetalhes({ registro, onClose }: Props) {
  const { cadastro } = useApp();
  const unidade = cadastro.unidades.find((u) => u.id === registro.unidadeId);
  const distrito = cadastro.distritos.find((d) => d.id === registro.distritoId);
  const catalogo = INDICADORES_CATALOGO.find((i) => i.codigo === registro.indicadorCodigo);

  const valorBase = registro.valorValidado ?? registro.valorInformado;
  const atingimento =
    valorBase !== null ? Math.min(valorBase / registro.meta, 1) : null;
  const pontosCalculados =
    atingimento !== null ? Math.round(atingimento * registro.peso * 10) / 10 : null;

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-panel" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <div>
            <div className="helper-text">{registro.indicadorCodigo}</div>
            <h2>{registro.indicadorNome}</h2>
          </div>
          <button className="modal-close" type="button" onClick={onClose} aria-label="Fechar">
            ✕
          </button>
        </div>
        <div className="modal-body">
          <div className="definition-list">
            <div>
              <dt>Unidade</dt>
              <dd>{unidade?.nome}</dd>
            </div>
            <div>
              <dt>Distrito</dt>
              <dd>{distrito?.nome}</dd>
            </div>
            <div>
              <dt>Status</dt>
              <dd>
                <StatusBadge status={registro.status} />
              </dd>
            </div>
            <div>
              <dt>Responsável</dt>
              <dd>{registro.responsavel}</dd>
            </div>
            <div>
              <dt>Valor informado</dt>
              <dd>{registro.valorInformado !== null ? `${registro.valorInformado}%` : '—'}</dd>
            </div>
            <div>
              <dt>Valor validado</dt>
              <dd>{registro.valorValidado !== null ? `${registro.valorValidado}%` : '—'}</dd>
            </div>
            <div>
              <dt>Meta</dt>
              <dd>{registro.meta}%</dd>
            </div>
            <div>
              <dt>Peso</dt>
              <dd>{registro.peso}%</dd>
            </div>
          </div>

          <div className="calc-box">
            <strong style={{ fontSize: 13 }}>Como foi calculado?</strong>
            <div className="calc-steps">
              <span className="step">Valor: {valorBase !== null ? `${valorBase}%` : '—'}</span>
              <span className="arrow">→</span>
              <span className="step">Meta: {registro.meta}%</span>
              <span className="arrow">→</span>
              <span className="step">
                Atingimento: {atingimento !== null ? `${Math.round(atingimento * 100)}%` : '—'}
              </span>
              <span className="arrow">→</span>
              <span className="step">Peso: {registro.peso}%</span>
              <span className="arrow">→</span>
              <span className="step">
                <strong>Pontos: {pontosCalculados !== null ? pontosCalculados : '—'}</strong>
              </span>
            </div>
            <p className="helper-text" style={{ marginTop: 10 }}>
              Fórmula: {catalogo?.formula ?? '—'}. Impacto na pontuação final da unidade:{' '}
              {pontosCalculados !== null ? `${pontosCalculados} pontos` : 'a definir após validação'}.
              {registro.status !== 'Validado' && registro.status !== 'Fechado'
                ? ' Valores ainda não validados são apenas uma estimativa.'
                : ''}
            </p>
          </div>

          {registro.observacoes && (
            <div className="section" style={{ marginBottom: 18 }}>
              <div className="section-title">Observações</div>
              <p className="helper-text">{registro.observacoes}</p>
            </div>
          )}

          <div className="section-title">Histórico do registro</div>
          <div className="data-table-wrap">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Usuário</th>
                  <th>Data/Hora</th>
                  <th>Valor anterior</th>
                  <th>Novo valor</th>
                  <th>Motivo</th>
                </tr>
              </thead>
              <tbody>
                {registro.historico.map((h) => (
                  <tr key={h.id}>
                    <td>{h.usuario}</td>
                    <td className="cell-muted">{h.dataHora}</td>
                    <td>{h.valorAnterior}</td>
                    <td>{h.novoValor}</td>
                    <td className="cell-muted">{h.motivo}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
        <div className="modal-footer">
          <button className="btn" type="button" onClick={onClose}>
            Fechar
          </button>
        </div>
      </div>
    </div>
  );
}
