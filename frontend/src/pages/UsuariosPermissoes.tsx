import { useState } from 'react';
import { USUARIOS, UNIDADES, DISTRITOS, PERFIS } from '../data/mockData';

export function UsuariosPermissoes() {
  const [perfilFiltro, setPerfilFiltro] = useState('todos');
  const [statusFiltro, setStatusFiltro] = useState('todos');

  function nomePerfil(id: string) {
    return PERFIS.find((p) => p.id === id)?.nome ?? id;
  }
  function nomeUnidade(id?: string) {
    return id ? UNIDADES.find((u) => u.id === id)?.nome ?? '—' : '—';
  }
  function nomeDistrito(id?: string) {
    return id ? DISTRITOS.find((d) => d.id === id)?.nome ?? '—' : '—';
  }

  const usuariosFiltrados = USUARIOS.filter((u) => {
    if (perfilFiltro !== 'todos' && u.perfilId !== perfilFiltro) return false;
    if (statusFiltro !== 'todos' && u.status !== statusFiltro) return false;
    return true;
  });

  return (
    <div>
      <div className="page-header">
        <div className="page-header-titles">
          <div className="breadcrumb">Configurador SAB</div>
          <h1>Usuários e Permissões</h1>
        </div>
        <div className="page-header-actions">
          <button className="btn btn-primary" type="button">
            + Novo usuário
          </button>
        </div>
      </div>

      <div className="section">
        <div className="section-title">
          Acesso definido por
          <span className="hint">Papel + Escopo territorial + Tipo de unidade</span>
        </div>
        <div className="calc-steps" style={{ marginTop: 0 }}>
          <span className="step">Papel</span>
          <span className="arrow">+</span>
          <span className="step">Escopo territorial</span>
          <span className="arrow">+</span>
          <span className="step">Tipo de unidade</span>
          <span className="arrow">=</span>
          <span className="step">
            <strong>Visão do sistema</strong>
          </span>
        </div>
      </div>

      <div className="section">
        <div className="filter-bar">
          <div className="filter-field">
            <label>Perfil</label>
            <select value={perfilFiltro} onChange={(e) => setPerfilFiltro(e.target.value)}>
              <option value="todos">Todos</option>
              {PERFIS.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.nome}
                </option>
              ))}
            </select>
          </div>
          <div className="filter-field">
            <label>Status</label>
            <select value={statusFiltro} onChange={(e) => setStatusFiltro(e.target.value)}>
              <option value="todos">Todos</option>
              <option value="Ativo">Ativo</option>
              <option value="Inativo">Inativo</option>
            </select>
          </div>
        </div>

        <div className="data-table-wrap">
          <table className="data-table">
            <thead>
              <tr>
                <th>Usuário</th>
                <th>Perfil</th>
                <th>Unidade</th>
                <th>Distrito</th>
                <th>Tipo de unidade</th>
                <th>Status</th>
                <th>Ações</th>
              </tr>
            </thead>
            <tbody>
              {usuariosFiltrados.map((u) => (
                <tr key={u.id}>
                  <td>
                    <div className="cell-strong">{u.nome}</div>
                    <div className="cell-muted">{u.email}</div>
                  </td>
                  <td>{nomePerfil(u.perfilId)}</td>
                  <td>{nomeUnidade(u.unidadeId)}</td>
                  <td>{nomeDistrito(u.distritoId)}</td>
                  <td>{u.tipoUnidade ?? '—'}</td>
                  <td>
                    <span className={`badge ${u.status === 'Ativo' ? 'badge-validado' : 'badge-rascunho'}`}>
                      <span className="badge-dot" />
                      {u.status}
                    </span>
                  </td>
                  <td>
                    <button className="btn-link" type="button">
                      Editar
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
