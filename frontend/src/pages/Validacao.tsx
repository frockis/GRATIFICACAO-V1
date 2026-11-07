import { useMemo, useState } from 'react';
import { useApp } from '../context/AppContext';
import { StatusBadge } from '../components/StatusBadge';
import { IndicadorDetalhes } from '../components/IndicadorDetalhes';
import { filtrarRegistrosPorEscopo, labelEscopo } from '../utils/escopo';
import type { RegistroIndicador } from '../types';

type Acao = 'correcao' | 'devolucao' | null;

export function Validacao() {
  const {
    registros,
    perfilAtual,
    competenciaId,
    competencias,
    validarRegistro,
    solicitarCorrecao,
    devolverRegistro,
    cadastro,
  } = useApp();
  const [detalhe, setDetalhe] = useState<RegistroIndicador | null>(null);
  const [acaoAtiva, setAcaoAtiva] = useState<{ tipo: Acao; registro: RegistroIndicador } | null>(null);
  const [motivo, setMotivo] = useState('');

  const competencia = competencias.find((c) => c.id === competenciaId);

  const registrosEscopo = useMemo(
    () =>
      filtrarRegistrosPorEscopo(registros, perfilAtual, cadastro)
        .filter((r) => r.competenciaId === competenciaId)
        .filter((r) => r.status !== 'Rascunho'),
    [registros, perfilAtual, competenciaId, cadastro],
  );

  function nomeUnidade(id: string) {
    return cadastro.unidades.find((u) => u.id === id)?.nome ?? id;
  }
  function nomeDistrito(id: string) {
    return cadastro.distritos.find((d) => d.id === id)?.nome ?? id;
  }

  function abrirAcao(tipo: Acao, registro: RegistroIndicador) {
    setAcaoAtiva({ tipo, registro });
    setMotivo('');
  }

  function confirmarAcao() {
    if (!acaoAtiva) return;
    if (acaoAtiva.tipo === 'correcao') {
      solicitarCorrecao(acaoAtiva.registro.id, motivo || 'Correção solicitada pelo revisor.');
    } else if (acaoAtiva.tipo === 'devolucao') {
      devolverRegistro(acaoAtiva.registro.id, motivo || 'Devolvido para revisão do gestor.');
    }
    setAcaoAtiva(null);
  }

  const etapaAtualLabel =
    perfilAtual === 'coordenador' ? 'Coordenador Distrital' : perfilAtual === 'seab' ? 'SEAB/CAM' : 'Revisor';

  return (
    <div>
      <div className="page-header">
        <div className="page-header-titles">
          <div className="breadcrumb">{labelEscopo(perfilAtual, cadastro)}</div>
          <h1>Validação — {competencia?.label}</h1>
        </div>
      </div>

      <div className="section">
        <div className="section-title">Fluxo de validação</div>
        <div className="flow-track">
          <span className="flow-step done">Gestor</span>
          <span className="flow-arrow">→</span>
          <span className={`flow-step${perfilAtual === 'coordenador' ? ' active' : perfilAtual === 'seab' ? ' done' : ''}`}>
            Coordenador Distrital
          </span>
          <span className="flow-arrow">→</span>
          <span className={`flow-step${perfilAtual === 'seab' ? ' active' : ''}`}>SEAB/CAM</span>
        </div>
        <p className="helper-text" style={{ marginTop: 10 }}>
          Você está atuando como <strong>{etapaAtualLabel}</strong>. Utilize o seletor de perfil no topo para
          simular as demais etapas do fluxo.
        </p>
      </div>

      <div className="section">
        <div className="data-table-wrap">
          <table className="data-table">
            <thead>
              <tr>
                <th>Indicador</th>
                <th>Unidade</th>
                <th className="cell-num">Valor informado</th>
                <th className="cell-num">Valor validado</th>
                <th className="cell-num">Meta</th>
                <th className="cell-num">Pontuação</th>
                <th>Responsável</th>
                <th>Última alteração</th>
                <th>Status</th>
                <th>Ações</th>
              </tr>
            </thead>
            <tbody>
              {registrosEscopo.map((r) => {
                const acionavel = r.status === 'Enviado' || r.status === 'Em revisão';
                return (
                  <tr key={r.id}>
                    <td>
                      <div className="cell-strong">{r.indicadorNome}</div>
                      <div className="cell-muted">{r.indicadorCodigo}</div>
                    </td>
                    <td>
                      {nomeUnidade(r.unidadeId)}
                      <div className="cell-muted">{nomeDistrito(r.distritoId)}</div>
                    </td>
                    <td className="cell-num">{r.valorInformado !== null ? `${r.valorInformado}%` : '—'}</td>
                    <td className="cell-num">{r.valorValidado !== null ? `${r.valorValidado}%` : '—'}</td>
                    <td className="cell-num">{r.meta}%</td>
                    <td className="cell-num">{r.pontuacaoFinal !== null ? r.pontuacaoFinal : '—'}</td>
                    <td>{r.responsavel}</td>
                    <td className="cell-muted">{r.dataAlteracao}</td>
                    <td>
                      <StatusBadge status={r.status} />
                    </td>
                    <td>
                      <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
                        <button
                          className="btn btn-sm btn-primary"
                          type="button"
                          disabled={!acionavel}
                          onClick={() => validarRegistro(r.id)}
                        >
                          Validar
                        </button>
                        <button
                          className="btn btn-sm"
                          type="button"
                          disabled={!acionavel}
                          onClick={() => abrirAcao('correcao', r)}
                        >
                          Solicitar correção
                        </button>
                        <button
                          className="btn btn-sm btn-danger"
                          type="button"
                          disabled={!acionavel}
                          onClick={() => abrirAcao('devolucao', r)}
                        >
                          Devolver
                        </button>
                        <button className="btn-link" type="button" onClick={() => setDetalhe(r)}>
                          Histórico
                        </button>
                      </div>
                    </td>
                  </tr>
                );
              })}
              {registrosEscopo.length === 0 && (
                <tr>
                  <td colSpan={10}>
                    <div className="empty-state">Nenhum indicador aguardando validação neste escopo.</div>
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {detalhe && <IndicadorDetalhes registro={detalhe} onClose={() => setDetalhe(null)} />}

      {acaoAtiva && (
        <div className="modal-overlay" onClick={() => setAcaoAtiva(null)}>
          <div className="modal-panel" style={{ width: 440 }} onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2>{acaoAtiva.tipo === 'correcao' ? 'Solicitar correção' : 'Devolver indicador'}</h2>
              <button className="modal-close" type="button" onClick={() => setAcaoAtiva(null)}>
                ✕
              </button>
            </div>
            <div className="modal-body">
              <p className="helper-text" style={{ marginBottom: 12 }}>
                {acaoAtiva.registro.indicadorNome} — {nomeUnidade(acaoAtiva.registro.unidadeId)}
              </p>
              <div className="form-field">
                <label htmlFor="motivo">Motivo</label>
                <textarea
                  id="motivo"
                  value={motivo}
                  onChange={(e) => setMotivo(e.target.value)}
                  placeholder="Descreva o motivo da solicitação para o gestor da unidade."
                />
              </div>
            </div>
            <div className="modal-footer">
              <button className="btn" type="button" onClick={() => setAcaoAtiva(null)}>
                Cancelar
              </button>
              <button className="btn btn-primary" type="button" onClick={confirmarAcao}>
                Confirmar
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
