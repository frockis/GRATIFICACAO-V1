import { useState } from 'react';
import { PERFIS } from '../data/mockData';
import { useApp } from '../context/AppContext';
import type { ResultadoCadastro } from '../context/AppContext';
import type { DadosUnidade, DadosUsuario, ErrosCampos } from '../services/api';
import type { PerfilId, StatusCadastro, Unidade, Usuario } from '../types';
import { TIPOS_UNIDADE } from '../utils/cadastro';

type Aba = 'pessoas' | 'unidades';

function ErroCampo({ erros, campo }: { erros: ErrosCampos; campo: string }) {
  if (!erros[campo]) return null;
  return (
    <span className="field-hint" style={{ color: 'var(--color-danger)' }}>
      {erros[campo].join(' ')}
    </span>
  );
}

/** Mostra os erros que não têm um campo próprio no formulário (ex.: regra do backend). */
function ErrosGerais({ erros, campos }: { erros: ErrosCampos; campos: string[] }) {
  const outros = Object.entries(erros).filter(([campo]) => !campos.includes(campo));
  if (outros.length === 0) return null;
  return (
    <p className="helper-text" style={{ color: 'var(--color-danger)', marginTop: 12 }}>
      {outros.map(([, msgs]) => msgs.join(' ')).join(' ')}
    </p>
  );
}

function StatusCadastroBadge({ status }: { status: StatusCadastro }) {
  return (
    <span className={`badge ${status === 'Ativo' ? 'badge-validado' : 'badge-rascunho'}`}>
      <span className="badge-dot" />
      {status}
    </span>
  );
}

export function UsuariosPermissoes() {
  const { cadastro, fonteCadastro, alterarStatusUsuario, alterarStatusUnidade } = useApp();
  const [aba, setAba] = useState<Aba>('pessoas');
  const [perfilFiltro, setPerfilFiltro] = useState('todos');
  const [statusFiltro, setStatusFiltro] = useState('todos');
  const [distritoFiltro, setDistritoFiltro] = useState('todos');
  const [editandoUsuario, setEditandoUsuario] = useState<Usuario | 'novo' | null>(null);
  const [editandoUnidade, setEditandoUnidade] = useState<Unidade | 'nova' | null>(null);
  const [aviso, setAviso] = useState<string | null>(null);

  function nomePerfil(id: string) {
    return PERFIS.find((p) => p.id === id)?.nome ?? id;
  }
  function nomeUnidade(id?: string) {
    return id ? cadastro.unidades.find((u) => u.id === id)?.nome ?? '—' : '—';
  }
  function nomeDistrito(id?: string) {
    return id ? cadastro.distritos.find((d) => d.id === id)?.nome ?? '—' : '—';
  }

  async function mudarStatus(acao: Promise<ResultadoCadastro>) {
    const resultado = await acao;
    setAviso(resultado.ok ? null : Object.values(resultado.erros).flat().join(' '));
  }

  const usuariosFiltrados = cadastro.usuarios.filter((u) => {
    if (perfilFiltro !== 'todos' && u.perfilId !== perfilFiltro) return false;
    if (statusFiltro !== 'todos' && u.status !== statusFiltro) return false;
    if (distritoFiltro !== 'todos' && u.distritoId !== distritoFiltro) return false;
    return true;
  });

  const unidadesFiltradas = cadastro.unidades.filter((u) => {
    if (statusFiltro !== 'todos' && (u.status ?? 'Ativo') !== statusFiltro) return false;
    if (distritoFiltro !== 'todos' && u.distritoId !== distritoFiltro) return false;
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
          {aba === 'pessoas' ? (
            <button className="btn btn-primary" type="button" onClick={() => setEditandoUsuario('novo')}>
              + Novo usuário
            </button>
          ) : (
            <button className="btn btn-primary" type="button" onClick={() => setEditandoUnidade('nova')}>
              + Nova unidade
            </button>
          )}
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
        {fonteCadastro === 'mock' && (
          <p className="helper-text" style={{ marginTop: 12 }}>
            Backend desligado: usando os dados fictícios. As alterações valem só nesta sessão.
          </p>
        )}
      </div>

      <div className="section">
        <div className="filter-bar">
          <div className="filter-field">
            <label>Cadastro</label>
            <div style={{ display: 'flex', gap: 6 }}>
              <button
                className={`btn btn-sm${aba === 'pessoas' ? ' btn-primary' : ''}`}
                type="button"
                onClick={() => setAba('pessoas')}
              >
                Pessoas ({cadastro.usuarios.length})
              </button>
              <button
                className={`btn btn-sm${aba === 'unidades' ? ' btn-primary' : ''}`}
                type="button"
                onClick={() => setAba('unidades')}
              >
                Unidades ({cadastro.unidades.length})
              </button>
            </div>
          </div>
          {aba === 'pessoas' && (
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
          )}
          <div className="filter-field">
            <label>Distrito</label>
            <select value={distritoFiltro} onChange={(e) => setDistritoFiltro(e.target.value)}>
              <option value="todos">Todos</option>
              {cadastro.distritos.map((d) => (
                <option key={d.id} value={d.id}>
                  {d.nome}
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

        {aviso && (
          <p className="helper-text" style={{ color: 'var(--color-danger)', marginBottom: 12 }}>
            {aviso}
          </p>
        )}

        {aba === 'pessoas' ? (
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
                      <StatusCadastroBadge status={u.status} />
                    </td>
                    <td style={{ whiteSpace: 'nowrap' }}>
                      <button className="btn-link" type="button" onClick={() => setEditandoUsuario(u)}>
                        Editar
                      </button>{' '}
                      ·{' '}
                      <button
                        className="btn-link"
                        type="button"
                        onClick={() =>
                          mudarStatus(alterarStatusUsuario(u.id, u.status === 'Ativo' ? 'Inativo' : 'Ativo'))
                        }
                      >
                        {u.status === 'Ativo' ? 'Inativar' : 'Reativar'}
                      </button>
                    </td>
                  </tr>
                ))}
                {usuariosFiltrados.length === 0 && (
                  <tr>
                    <td colSpan={7}>
                      <div className="empty-state">Nenhuma pessoa encontrada para os filtros selecionados.</div>
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="data-table-wrap">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Unidade</th>
                  <th>Tipo</th>
                  <th>Distrito</th>
                  <th>CNES</th>
                  <th className="cell-num">Pessoas ativas</th>
                  <th>Status</th>
                  <th>Ações</th>
                </tr>
              </thead>
              <tbody>
                {unidadesFiltradas.map((u) => {
                  const status = u.status ?? 'Ativo';
                  const vinculadas = cadastro.usuarios.filter(
                    (p) => p.unidadeId === u.id && p.status === 'Ativo',
                  ).length;
                  return (
                    <tr key={u.id}>
                      <td className="cell-strong">{u.nome}</td>
                      <td>{u.tipo}</td>
                      <td>{nomeDistrito(u.distritoId)}</td>
                      <td className="cell-muted">{u.cnes ?? '—'}</td>
                      <td className="cell-num">{vinculadas}</td>
                      <td>
                        <StatusCadastroBadge status={status} />
                      </td>
                      <td style={{ whiteSpace: 'nowrap' }}>
                        <button className="btn-link" type="button" onClick={() => setEditandoUnidade(u)}>
                          Editar
                        </button>{' '}
                        ·{' '}
                        <button
                          className="btn-link"
                          type="button"
                          onClick={() =>
                            mudarStatus(alterarStatusUnidade(u.id, status === 'Ativo' ? 'Inativo' : 'Ativo'))
                          }
                        >
                          {status === 'Ativo' ? 'Inativar' : 'Reativar'}
                        </button>
                      </td>
                    </tr>
                  );
                })}
                {unidadesFiltradas.length === 0 && (
                  <tr>
                    <td colSpan={7}>
                      <div className="empty-state">Nenhuma unidade encontrada para os filtros selecionados.</div>
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {editandoUsuario && (
        <FormUsuario
          usuario={editandoUsuario === 'novo' ? undefined : editandoUsuario}
          onClose={() => setEditandoUsuario(null)}
        />
      )}
      {editandoUnidade && (
        <FormUnidade
          unidade={editandoUnidade === 'nova' ? undefined : editandoUnidade}
          onClose={() => setEditandoUnidade(null)}
        />
      )}
    </div>
  );
}

function FormUsuario({ usuario, onClose }: { usuario?: Usuario; onClose: () => void }) {
  const { cadastro, salvarUsuario } = useApp();
  const [dados, setDados] = useState<DadosUsuario>({
    nome: usuario?.nome ?? '',
    email: usuario?.email ?? '',
    matricula: usuario?.matricula ?? '',
    perfilId: usuario?.perfilId ?? 'gestor',
    unidadeId: usuario?.unidadeId ?? null,
    distritoId: usuario?.distritoId ?? null,
  });
  const [erros, setErros] = useState<ErrosCampos>({});
  const [salvando, setSalvando] = useState(false);

  const unidadesAtivas = cadastro.unidades.filter((u) => (u.status ?? 'Ativo') === 'Ativo' || u.id === dados.unidadeId);

  async function salvar() {
    setSalvando(true);
    const resultado = await salvarUsuario(dados, usuario?.id);
    setSalvando(false);
    if (resultado.ok) onClose();
    else setErros(resultado.erros);
  }

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-panel" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <div>
            <div className="helper-text">{usuario ? usuario.id : 'Novo cadastro'}</div>
            <h2>{usuario ? 'Editar usuário' : 'Novo usuário'}</h2>
          </div>
          <button className="modal-close" type="button" onClick={onClose} aria-label="Fechar">
            ✕
          </button>
        </div>
        <div className="modal-body">
          <div className="form-grid">
            <div className="form-field span-2">
              <label>Nome</label>
              <input value={dados.nome} onChange={(e) => setDados({ ...dados, nome: e.target.value })} />
              <ErroCampo erros={erros} campo="nome" />
            </div>
            <div className="form-field">
              <label>E-mail</label>
              <input
                type="email"
                value={dados.email}
                onChange={(e) => setDados({ ...dados, email: e.target.value })}
              />
              <ErroCampo erros={erros} campo="email" />
            </div>
            <div className="form-field">
              <label>Matrícula</label>
              <input
                value={dados.matricula ?? ''}
                onChange={(e) => setDados({ ...dados, matricula: e.target.value })}
              />
              <span className="field-hint">Opcional</span>
              <ErroCampo erros={erros} campo="matricula" />
            </div>
            <div className="form-field span-2">
              <label>Perfil</label>
              <select
                value={dados.perfilId}
                onChange={(e) => setDados({ ...dados, perfilId: e.target.value as PerfilId })}
              >
                {PERFIS.map((p) => (
                  <option key={p.id} value={p.id}>
                    {p.nome}
                  </option>
                ))}
              </select>
              <span className="field-hint">{PERFIS.find((p) => p.id === dados.perfilId)?.descricao}</span>
              <ErroCampo erros={erros} campo="perfilId" />
            </div>

            {dados.perfilId === 'gestor' && (
              <div className="form-field span-2">
                <label>Unidade</label>
                <select
                  value={dados.unidadeId ?? ''}
                  onChange={(e) => setDados({ ...dados, unidadeId: e.target.value || null })}
                >
                  <option value="">Selecione…</option>
                  {unidadesAtivas.map((u) => (
                    <option key={u.id} value={u.id}>
                      {u.nome} — {cadastro.distritos.find((d) => d.id === u.distritoId)?.nome}
                    </option>
                  ))}
                </select>
                <span className="field-hint">O distrito é o da unidade.</span>
                <ErroCampo erros={erros} campo="unidadeId" />
              </div>
            )}

            {dados.perfilId === 'coordenador' && (
              <div className="form-field span-2">
                <label>Distrito</label>
                <select
                  value={dados.distritoId ?? ''}
                  onChange={(e) => setDados({ ...dados, distritoId: e.target.value || null })}
                >
                  <option value="">Selecione…</option>
                  {cadastro.distritos.map((d) => (
                    <option key={d.id} value={d.id}>
                      {d.nome}
                    </option>
                  ))}
                </select>
                <ErroCampo erros={erros} campo="distritoId" />
              </div>
            )}

            {(dados.perfilId === 'seab' || dados.perfilId === 'configurador') && (
              <p className="helper-text" style={{ gridColumn: 'span 2' }}>
                Perfil com visão municipal: não é vinculado a unidade ou distrito.
              </p>
            )}
          </div>
          <ErrosGerais
            erros={erros}
            campos={[
              'nome',
              'email',
              'matricula',
              'perfilId',
              ...(dados.perfilId === 'gestor' ? ['unidadeId'] : []),
              ...(dados.perfilId === 'coordenador' ? ['distritoId'] : []),
            ]}
          />
        </div>
        <div className="modal-footer">
          <button className="btn" type="button" onClick={onClose}>
            Cancelar
          </button>
          <button className="btn btn-primary" type="button" onClick={salvar} disabled={salvando}>
            {salvando ? 'Salvando…' : 'Salvar'}
          </button>
        </div>
      </div>
    </div>
  );
}

function FormUnidade({ unidade, onClose }: { unidade?: Unidade; onClose: () => void }) {
  const { cadastro, salvarUnidade } = useApp();
  const [dados, setDados] = useState<DadosUnidade>({
    nome: unidade?.nome ?? '',
    distritoId: unidade?.distritoId ?? '',
    tipo: unidade?.tipo ?? 'USF',
    cnes: unidade?.cnes ?? '',
  });
  const [erros, setErros] = useState<ErrosCampos>({});
  const [salvando, setSalvando] = useState(false);

  async function salvar() {
    setSalvando(true);
    const resultado = await salvarUnidade(dados, unidade?.id);
    setSalvando(false);
    if (resultado.ok) onClose();
    else setErros(resultado.erros);
  }

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-panel" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <div>
            <div className="helper-text">{unidade ? unidade.id : 'Novo cadastro'}</div>
            <h2>{unidade ? 'Editar unidade' : 'Nova unidade'}</h2>
          </div>
          <button className="modal-close" type="button" onClick={onClose} aria-label="Fechar">
            ✕
          </button>
        </div>
        <div className="modal-body">
          <div className="form-grid">
            <div className="form-field span-2">
              <label>Nome</label>
              <input value={dados.nome} onChange={(e) => setDados({ ...dados, nome: e.target.value })} />
              <ErroCampo erros={erros} campo="nome" />
            </div>
            <div className="form-field">
              <label>Distrito</label>
              <select value={dados.distritoId} onChange={(e) => setDados({ ...dados, distritoId: e.target.value })}>
                <option value="">Selecione…</option>
                {cadastro.distritos.map((d) => (
                  <option key={d.id} value={d.id}>
                    {d.nome}
                  </option>
                ))}
              </select>
              <ErroCampo erros={erros} campo="distritoId" />
            </div>
            <div className="form-field">
              <label>Tipo de unidade</label>
              <select value={dados.tipo} onChange={(e) => setDados({ ...dados, tipo: e.target.value })}>
                {TIPOS_UNIDADE.map((t) => (
                  <option key={t} value={t}>
                    {t}
                  </option>
                ))}
              </select>
              <ErroCampo erros={erros} campo="tipo" />
            </div>
            <div className="form-field">
              <label>CNES</label>
              <input
                value={dados.cnes ?? ''}
                maxLength={7}
                onChange={(e) => setDados({ ...dados, cnes: e.target.value.replace(/\D/g, '') })}
              />
              <span className="field-hint">7 dígitos · opcional</span>
              <ErroCampo erros={erros} campo="cnes" />
            </div>
          </div>
          <ErrosGerais erros={erros} campos={['nome', 'distritoId', 'tipo', 'cnes']} />
        </div>
        <div className="modal-footer">
          <button className="btn" type="button" onClick={onClose}>
            Cancelar
          </button>
          <button className="btn btn-primary" type="button" onClick={salvar} disabled={salvando}>
            {salvando ? 'Salvando…' : 'Salvar'}
          </button>
        </div>
      </div>
    </div>
  );
}
