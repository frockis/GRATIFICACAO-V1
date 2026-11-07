import { useMemo, useState } from 'react';
import { useApp } from '../context/AppContext';
import { StatusBadge } from '../components/StatusBadge';
import { IndicadorDetalhes } from '../components/IndicadorDetalhes';
import { filtrarRegistrosPorEscopo, labelEscopo, unidadesDoEscopo } from '../utils/escopo';
import type { RegistroIndicador, StatusIndicador } from '../types';

const STATUS_OPCOES: StatusIndicador[] = ['Rascunho', 'Enviado', 'Em revisão', 'Devolvido', 'Validado', 'Fechado'];

export function Indicadores() {
  const { registros, perfilAtual, competenciaId, competencias, cadastro } = useApp();
  const [distritoFiltro, setDistritoFiltro] = useState('todos');
  const [tipoFiltro, setTipoFiltro] = useState('todos');
  const [statusFiltro, setStatusFiltro] = useState('todos');
  const [selecionado, setSelecionado] = useState<RegistroIndicador | null>(null);

  const unidadesEscopo = unidadesDoEscopo(perfilAtual, cadastro);
  const distritosDisponiveis = cadastro.distritos.filter((d) => unidadesEscopo.some((u) => u.distritoId === d.id));
  const tiposDisponiveis = Array.from(new Set(unidadesEscopo.map((u) => u.tipo)));

  const registrosFiltrados = useMemo(() => {
    let lista = filtrarRegistrosPorEscopo(registros, perfilAtual, cadastro).filter(
      (r) => r.competenciaId === competenciaId,
    );
    if (distritoFiltro !== 'todos') lista = lista.filter((r) => r.distritoId === distritoFiltro);
    if (statusFiltro !== 'todos') lista = lista.filter((r) => r.status === statusFiltro);
    if (tipoFiltro !== 'todos') {
      const unidadesTipo = new Set(unidadesEscopo.filter((u) => u.tipo === tipoFiltro).map((u) => u.id));
      lista = lista.filter((r) => unidadesTipo.has(r.unidadeId));
    }
    return lista;
  }, [registros, perfilAtual, competenciaId, distritoFiltro, statusFiltro, tipoFiltro, unidadesEscopo, cadastro]);

  function nomeUnidade(unidadeId: string) {
    return unidadesEscopo.find((u) => u.id === unidadeId)?.nome ?? unidadeId;
  }

  const competencia = competencias.find((c) => c.id === competenciaId);

  return (
    <div>
      <div className="page-header">
        <div className="page-header-titles">
          <div className="breadcrumb">{labelEscopo(perfilAtual, cadastro)}</div>
          <h1>Indicadores — {competencia?.label}</h1>
        </div>
      </div>

      <div className="section">
        <div className="filter-bar">
          <div className="filter-field">
            <label>Distrito</label>
            <select value={distritoFiltro} onChange={(e) => setDistritoFiltro(e.target.value)}>
              <option value="todos">Todos</option>
              {distritosDisponiveis.map((d) => (
                <option key={d.id} value={d.id}>
                  {d.nome}
                </option>
              ))}
            </select>
          </div>
          <div className="filter-field">
            <label>Tipo de unidade</label>
            <select value={tipoFiltro} onChange={(e) => setTipoFiltro(e.target.value)}>
              <option value="todos">Todos</option>
              {tiposDisponiveis.map((t) => (
                <option key={t} value={t}>
                  {t}
                </option>
              ))}
            </select>
          </div>
          <div className="filter-field">
            <label>Status</label>
            <select value={statusFiltro} onChange={(e) => setStatusFiltro(e.target.value)}>
              <option value="todos">Todos</option>
              {STATUS_OPCOES.map((s) => (
                <option key={s} value={s}>
                  {s}
                </option>
              ))}
            </select>
          </div>
        </div>

        <div className="data-table-wrap">
          <table className="data-table">
            <thead>
              <tr>
                <th>Indicador</th>
                <th>Unidade</th>
                <th className="cell-num">Meta</th>
                <th className="cell-num">Valor informado</th>
                <th className="cell-num">Valor validado</th>
                <th className="cell-num">Peso</th>
                <th className="cell-num">Pontos</th>
                <th className="cell-num">Pontuação final</th>
                <th>Competência</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {registrosFiltrados.map((r) => (
                <tr key={r.id} className="is-clickable" onClick={() => setSelecionado(r)}>
                  <td>
                    <div className="cell-strong">{r.indicadorNome}</div>
                    <div className="cell-muted">{r.indicadorCodigo}</div>
                  </td>
                  <td>{nomeUnidade(r.unidadeId)}</td>
                  <td className="cell-num">{r.meta}%</td>
                  <td className="cell-num">{r.valorInformado !== null ? `${r.valorInformado}%` : '—'}</td>
                  <td className="cell-num">{r.valorValidado !== null ? `${r.valorValidado}%` : '—'}</td>
                  <td className="cell-num">{r.peso}%</td>
                  <td className="cell-num">{r.pontos !== null ? r.pontos : '—'}</td>
                  <td className="cell-num">{r.pontuacaoFinal !== null ? r.pontuacaoFinal : '—'}</td>
                  <td className="cell-muted">{competencia?.label}</td>
                  <td>
                    <StatusBadge status={r.status} />
                  </td>
                </tr>
              ))}
              {registrosFiltrados.length === 0 && (
                <tr>
                  <td colSpan={10}>
                    <div className="empty-state">Nenhum indicador encontrado para os filtros selecionados.</div>
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {selecionado && <IndicadorDetalhes registro={selecionado} onClose={() => setSelecionado(null)} />}
    </div>
  );
}
