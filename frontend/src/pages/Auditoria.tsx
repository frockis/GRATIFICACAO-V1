import { useState } from 'react';
import { useApp } from '../context/AppContext';

export function Auditoria() {
  const { auditoria } = useApp();
  const [operacaoFiltro, setOperacaoFiltro] = useState('todas');

  const operacoes = Array.from(new Set(auditoria.map((a) => a.operacao)));
  const listaFiltrada = auditoria.filter((a) => operacaoFiltro === 'todas' || a.operacao === operacaoFiltro);

  return (
    <div>
      <div className="page-header">
        <div className="page-header-titles">
          <div className="breadcrumb">Rastreabilidade</div>
          <h1>Auditoria / Histórico</h1>
        </div>
      </div>

      <div className="section">
        <p className="helper-text">
          Registro completo de operações realizadas no sistema, para fins de rastreabilidade e auditabilidade.
          Esta tela não determina automaticamente fraude — apenas apresenta o histórico de alterações.
        </p>
      </div>

      <div className="section">
        <div className="filter-bar">
          <div className="filter-field">
            <label>Operação</label>
            <select value={operacaoFiltro} onChange={(e) => setOperacaoFiltro(e.target.value)}>
              <option value="todas">Todas</option>
              {operacoes.map((op) => (
                <option key={op} value={op}>
                  {op}
                </option>
              ))}
            </select>
          </div>
        </div>

        <div className="data-table-wrap">
          <table className="data-table">
            <thead>
              <tr>
                <th>Usuário</th>
                <th>Data</th>
                <th>Horário</th>
                <th>Operação</th>
                <th>Registro afetado</th>
                <th>Valor anterior</th>
                <th>Novo valor</th>
                <th>Perfil</th>
                <th>Unidade/Distrito</th>
              </tr>
            </thead>
            <tbody>
              {listaFiltrada.map((a) => (
                <tr key={a.id}>
                  <td className="cell-strong">{a.usuario}</td>
                  <td className="cell-muted">{a.data}</td>
                  <td className="cell-muted">{a.horario}</td>
                  <td>{a.operacao}</td>
                  <td>{a.registroAfetado}</td>
                  <td className="cell-muted">{a.valorAnterior}</td>
                  <td>{a.novoValor}</td>
                  <td>{a.perfil}</td>
                  <td className="cell-muted">{a.localizacao}</td>
                </tr>
              ))}
              {listaFiltrada.length === 0 && (
                <tr>
                  <td colSpan={9}>
                    <div className="empty-state">Nenhum registro encontrado.</div>
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
