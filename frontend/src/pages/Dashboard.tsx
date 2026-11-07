import { useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { useApp } from '../context/AppContext';
import { StatusBadge } from '../components/StatusBadge';
import { filtrarRegistrosPorEscopo, labelEscopo } from '../utils/escopo';

export function Dashboard() {
  const { registros, perfilAtual, competenciaId, competencias, cadastro } = useApp();
  const navigate = useNavigate();
  const competencia = competencias.find((c) => c.id === competenciaId);

  const registrosCompetencia = useMemo(
    () =>
      filtrarRegistrosPorEscopo(registros, perfilAtual, cadastro).filter((r) => r.competenciaId === competenciaId),
    [registros, perfilAtual, competenciaId, cadastro],
  );

  const pendentes = registrosCompetencia.filter((r) => r.status === 'Rascunho' || r.status === 'Devolvido');
  const enviados = registrosCompetencia.filter((r) => r.status === 'Enviado');
  const emRevisao = registrosCompetencia.filter((r) => r.status === 'Em revisão');
  const validados = registrosCompetencia.filter((r) => r.status === 'Validado' || r.status === 'Fechado');

  const pontuacaoProvisoria = useMemo(() => {
    const comPontos = registrosCompetencia.filter((r) => r.pontuacaoFinal !== null);
    if (comPontos.length === 0) return null;
    const total = comPontos.reduce((acc, r) => acc + (r.pontuacaoFinal ?? 0), 0);
    return Math.round((total / registrosCompetencia.length) * 10) / 10;
  }, [registrosCompetencia]);

  function nomeUnidade(unidadeId: string) {
    return cadastro.unidades.find((u) => u.id === unidadeId)?.nome ?? unidadeId;
  }

  function nomeDistrito(distritoId: string) {
    return cadastro.distritos.find((d) => d.id === distritoId)?.nome ?? distritoId;
  }

  return (
    <div>
      <div className="page-header">
        <div className="page-header-titles">
          <div className="breadcrumb">Painel geral</div>
          <h1>Dashboard — {labelEscopo(perfilAtual, cadastro)}</h1>
        </div>
        <div className="page-header-actions">
          <button className="btn" type="button" onClick={() => navigate('/indicadores')}>
            Ver indicadores
          </button>
        </div>
      </div>

      <div className="section">
        <div className="section-title">
          Situação da competência
          <span className="hint">Atualizado conforme os lançamentos recebidos</span>
        </div>
        <div className="definition-list">
          <div>
            <dt>Competência</dt>
            <dd>{competencia?.label}</dd>
          </div>
          <div>
            <dt>Status</dt>
            <dd>
              <StatusBadge status={competencia?.status ?? 'Aberto'} />
            </dd>
          </div>
          <div>
            <dt>Data prevista de fechamento</dt>
            <dd>{competencia?.dataPrevistaFechamento}</dd>
          </div>
          <div>
            <dt>Indicadores no escopo</dt>
            <dd>{registrosCompetencia.length}</dd>
          </div>
        </div>
      </div>

      <div className="cards-row">
        <div className="stat-card accent">
          <div className="stat-label">Pendentes</div>
          <div className="stat-value">{pendentes.length}</div>
          <div className="stat-sub">Rascunho ou devolvidos para correção</div>
        </div>
        <div className="stat-card">
          <div className="stat-label">Enviados</div>
          <div className="stat-value">{enviados.length}</div>
          <div className="stat-sub">Aguardando revisão</div>
        </div>
        <div className="stat-card">
          <div className="stat-label">Em revisão</div>
          <div className="stat-value">{emRevisao.length}</div>
          <div className="stat-sub">Em análise pelo coordenador/SEAB</div>
        </div>
        <div className="stat-card">
          <div className="stat-label">Validados</div>
          <div className="stat-value">{validados.length}</div>
          <div className="stat-sub">Pontuação confirmada</div>
        </div>
      </div>

      <div className="section">
        <div className="section-title">
          Pontuação {competencia?.status === 'Fechado' ? 'final' : 'atual/provisória'}
        </div>
        <div className="stat-card" style={{ maxWidth: 260 }}>
          <div className="stat-label">Pontuação média do escopo</div>
          <div className="stat-value">{pontuacaoProvisoria !== null ? `${pontuacaoProvisoria} pts` : '—'}</div>
          <div className="stat-sub">
            Calculada apenas com os indicadores já validados. Sujeita a alteração até o fechamento.
          </div>
        </div>
      </div>

      <div className="section">
        <div className="section-title">
          Pendências
          <span className="hint">{pendentes.length} indicador(es) aguardando ação</span>
        </div>
        {pendentes.length === 0 ? (
          <div className="empty-state">Nenhuma pendência no momento para este escopo.</div>
        ) : (
          <div className="data-table-wrap">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Indicador</th>
                  <th>Unidade</th>
                  <th>Distrito</th>
                  <th>Status</th>
                  <th>Responsável</th>
                  <th>Última alteração</th>
                </tr>
              </thead>
              <tbody>
                {pendentes.map((r) => (
                  <tr key={r.id} className="is-clickable" onClick={() => navigate('/indicadores')}>
                    <td>
                      <div className="cell-strong">{r.indicadorNome}</div>
                      <div className="cell-muted">{r.indicadorCodigo}</div>
                    </td>
                    <td>{nomeUnidade(r.unidadeId)}</td>
                    <td>{nomeDistrito(r.distritoId)}</td>
                    <td>
                      <StatusBadge status={r.status} />
                    </td>
                    <td>{r.responsavel}</td>
                    <td className="cell-muted">{r.dataAlteracao}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
