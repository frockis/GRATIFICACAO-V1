import { useMemo, useState } from 'react';
import { useApp } from '../context/AppContext';
import { StatusBadge } from '../components/StatusBadge';
import { FluxoStatus } from '../components/FluxoStatus';
import { filtrarRegistrosPorEscopo, labelEscopo } from '../utils/escopo';
import type { RegistroIndicador } from '../types';

export function Preenchimento() {
  const { registros, perfilAtual, competenciaId, competencias, salvarRascunho, enviarParaRevisao } = useApp();
  const [selecionado, setSelecionado] = useState<RegistroIndicador | null>(null);
  const [valor, setValor] = useState('');
  const [observacoes, setObservacoes] = useState('');
  const [mensagem, setMensagem] = useState<string | null>(null);

  const competencia = competencias.find((c) => c.id === competenciaId);

  const registrosEscopo = useMemo(
    () => filtrarRegistrosPorEscopo(registros, perfilAtual).filter((r) => r.competenciaId === competenciaId),
    [registros, perfilAtual, competenciaId],
  );

  function abrirFormulario(registro: RegistroIndicador) {
    setSelecionado(registro);
    setValor(registro.valorInformado !== null ? String(registro.valorInformado) : '');
    setObservacoes(registro.observacoes ?? '');
    setMensagem(null);
  }

  function fechar() {
    setSelecionado(null);
  }

  const competenciaFechada = competencia?.status === 'Fechado';
  const podeEditar = (r: RegistroIndicador) =>
    !competenciaFechada && (r.status === 'Rascunho' || r.status === 'Devolvido');

  function handleSalvarRascunho() {
    if (!selecionado || valor === '') return;
    salvarRascunho(selecionado.id, Number(valor), observacoes);
    setMensagem('Rascunho salvo com sucesso.');
  }

  function handleEnviar() {
    if (!selecionado || valor === '') return;
    salvarRascunho(selecionado.id, Number(valor), observacoes);
    enviarParaRevisao(selecionado.id);
    setMensagem('Indicador enviado para revisão.');
    setTimeout(() => setSelecionado(null), 600);
  }

  return (
    <div>
      <div className="page-header">
        <div className="page-header-titles">
          <div className="breadcrumb">{labelEscopo(perfilAtual)}</div>
          <h1>Preenchimento de indicadores — {competencia?.label}</h1>
        </div>
      </div>

      {perfilAtual !== 'gestor' && (
        <div className="section">
          <p className="helper-text">
            Esta tela é destinada ao preenchimento pelo Gestor de Unidade. Selecione o perfil "Gestor de Unidade"
            no topo da página para simular o preenchimento.
          </p>
        </div>
      )}

      {competenciaFechada && (
        <div className="section">
          <span className="tag-locked">🔒 Competência fechada — valores bloqueados para alterações operacionais</span>
        </div>
      )}

      <div className="section">
        <div className="data-table-wrap">
          <table className="data-table">
            <thead>
              <tr>
                <th>Indicador</th>
                <th className="cell-num">Meta</th>
                <th className="cell-num">Valor informado</th>
                <th>Status</th>
                <th>Ação</th>
              </tr>
            </thead>
            <tbody>
              {registrosEscopo.map((r) => (
                <tr key={r.id}>
                  <td>
                    <div className="cell-strong">{r.indicadorNome}</div>
                    <div className="cell-muted">{r.indicadorCodigo}</div>
                  </td>
                  <td className="cell-num">{r.meta}%</td>
                  <td className="cell-num">{r.valorInformado !== null ? `${r.valorInformado}%` : '—'}</td>
                  <td>
                    <StatusBadge status={r.status} />
                  </td>
                  <td>
                    <button
                      className="btn btn-sm"
                      type="button"
                      disabled={!podeEditar(r)}
                      onClick={() => abrirFormulario(r)}
                    >
                      {r.status === 'Devolvido' ? 'Corrigir' : 'Preencher'}
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {selecionado && (
        <div className="modal-overlay" onClick={fechar}>
          <div className="modal-panel" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <div>
                <div className="helper-text">{selecionado.indicadorCodigo}</div>
                <h2>{selecionado.indicadorNome}</h2>
              </div>
              <button className="modal-close" type="button" onClick={fechar} aria-label="Fechar">
                ✕
              </button>
            </div>
            <div className="modal-body">
              <FluxoStatus atual={selecionado.status} />

              {selecionado.status === 'Devolvido' && selecionado.observacoes && (
                <div className="section" style={{ marginTop: 16, marginBottom: 0 }}>
                  <div className="section-title">Motivo da devolução</div>
                  <p className="helper-text">{selecionado.observacoes}</p>
                </div>
              )}

              <div className="form-grid" style={{ marginTop: 18 }}>
                <div className="form-field">
                  <label>Nome do indicador</label>
                  <input value={selecionado.indicadorNome} disabled />
                </div>
                <div className="form-field">
                  <label>Competência</label>
                  <input value={competencia?.label ?? ''} disabled />
                </div>
                <div className="form-field">
                  <label>Meta</label>
                  <input value={`${selecionado.meta}%`} disabled />
                </div>
                <div className="form-field">
                  <label>Unidade de medida</label>
                  <input value="%" disabled />
                </div>
                <div className="form-field span-2">
                  <label htmlFor="valor">Valor a informar</label>
                  <input
                    id="valor"
                    type="number"
                    min={0}
                    max={100}
                    value={valor}
                    onChange={(e) => setValor(e.target.value)}
                  />
                  <span className="field-hint">Informe o percentual apurado para a competência atual.</span>
                </div>
                <div className="form-field span-2">
                  <label htmlFor="obs">Observações</label>
                  <textarea
                    id="obs"
                    value={observacoes}
                    onChange={(e) => setObservacoes(e.target.value)}
                    placeholder="Inclua justificativas ou evidências relevantes para a revisão."
                  />
                </div>
              </div>

              {mensagem && (
                <p className="helper-text" style={{ marginTop: 14, color: 'var(--color-success)' }}>
                  {mensagem}
                </p>
              )}
            </div>
            <div className="modal-footer">
              <button className="btn" type="button" onClick={handleSalvarRascunho} disabled={valor === ''}>
                Salvar rascunho
              </button>
              <button className="btn btn-primary" type="button" onClick={handleEnviar} disabled={valor === ''}>
                Enviar para revisão
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
