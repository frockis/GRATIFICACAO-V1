import { useMemo, useState } from 'react';
import { useApp } from '../context/AppContext';
import { StatusBadge } from '../components/StatusBadge';

const ETAPAS = ['Aberto', 'Em revisão', 'Fechado'] as const;

export function Fechamento() {
  const { registros, competenciaId, competencias, fecharCompetencia } = useApp();
  const [confirmando, setConfirmando] = useState(false);

  const competencia = competencias.find((c) => c.id === competenciaId);
  const registrosCompetencia = useMemo(
    () => registros.filter((r) => r.competenciaId === competenciaId),
    [registros, competenciaId],
  );

  const preenchidos = registrosCompetencia.filter((r) => r.valorInformado !== null).length;
  const pendentes = registrosCompetencia.filter((r) => r.status === 'Rascunho' || r.status === 'Devolvido');
  const validados = registrosCompetencia.filter((r) => r.status === 'Validado' || r.status === 'Fechado');

  const indexAtual = competencia ? ETAPAS.indexOf(competencia.status) : 0;
  const jaFechada = competencia?.status === 'Fechado';

  function confirmarFechamento() {
    fecharCompetencia(competenciaId);
    setConfirmando(false);
  }

  return (
    <div>
      <div className="page-header">
        <div className="page-header-titles">
          <div className="breadcrumb">SEAB/CAM — Monitoramento</div>
          <h1>Fechamento da competência — {competencia?.label}</h1>
        </div>
        <div className="page-header-actions">
          <button
            className="btn btn-primary"
            type="button"
            disabled={jaFechada}
            onClick={() => setConfirmando(true)}
          >
            {jaFechada ? 'Competência já fechada' : 'Fechar competência'}
          </button>
        </div>
      </div>

      <div className="section">
        <div className="section-title">Ciclo da competência</div>
        <div className="flow-track">
          {ETAPAS.map((etapa, idx) => (
            <span key={etapa} style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
              <span
                className={`flow-step${etapa === competencia?.status ? ' active' : idx < indexAtual ? ' done' : ''}`}
              >
                {etapa}
              </span>
              {idx < ETAPAS.length - 1 && <span className="flow-arrow">→</span>}
            </span>
          ))}
        </div>
      </div>

      <div className="cards-row">
        <div className="stat-card">
          <div className="stat-label">Indicadores preenchidos</div>
          <div className="stat-value">
            {preenchidos}/{registrosCompetencia.length}
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-label">Pendentes</div>
          <div className="stat-value">{pendentes.length}</div>
        </div>
        <div className="stat-card">
          <div className="stat-label">Validados</div>
          <div className="stat-value">{validados.length}</div>
        </div>
        <div className="stat-card">
          <div className="stat-label">Data prevista</div>
          <div className="stat-value" style={{ fontSize: 18 }}>
            {competencia?.dataPrevistaFechamento}
          </div>
        </div>
      </div>

      {jaFechada && (
        <div className="section">
          <span className="tag-locked">
            🔒 Competência fechada — valores utilizados no cálculo bloqueados para alterações operacionais
          </span>
        </div>
      )}

      <div className="section">
        <div className="section-title">
          Pendências para o fechamento
          <span className="hint">{pendentes.length} indicador(es)</span>
        </div>
        {pendentes.length === 0 ? (
          <div className="empty-state">Todos os indicadores desta competência foram tratados.</div>
        ) : (
          <div className="data-table-wrap">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Indicador</th>
                  <th>Responsável</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {pendentes.map((r) => (
                  <tr key={r.id}>
                    <td>
                      <div className="cell-strong">{r.indicadorNome}</div>
                      <div className="cell-muted">{r.indicadorCodigo}</div>
                    </td>
                    <td>{r.responsavel}</td>
                    <td>
                      <StatusBadge status={r.status} />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {confirmando && (
        <div className="modal-overlay" onClick={() => setConfirmando(false)}>
          <div className="modal-panel" style={{ width: 440 }} onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2>Confirmar fechamento</h2>
              <button className="modal-close" type="button" onClick={() => setConfirmando(false)}>
                ✕
              </button>
            </div>
            <div className="modal-body">
              <p className="helper-text">
                Ao fechar a competência <strong>{competencia?.label}</strong>, os valores utilizados no cálculo da
                pontuação serão bloqueados para alterações operacionais.
                {pendentes.length > 0 && (
                  <>
                    {' '}
                    Ainda existem <strong>{pendentes.length}</strong> indicador(es) pendentes neste município.
                  </>
                )}
              </p>
            </div>
            <div className="modal-footer">
              <button className="btn" type="button" onClick={() => setConfirmando(false)}>
                Cancelar
              </button>
              <button className="btn btn-primary" type="button" onClick={confirmarFechamento}>
                Confirmar fechamento
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
