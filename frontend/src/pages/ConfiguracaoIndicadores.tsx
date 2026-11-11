import { INDICADORES_CATALOGO, VIGENCIAS, PERFIS } from '../data/mockData';

export function ConfiguracaoIndicadores() {
  function nomePerfil(id: string) {
    return PERFIS.find((p) => p.id === id)?.nome ?? id;
  }

  return (
    <div>
      <div className="page-header">
        <div className="page-header-titles">
          <div className="breadcrumb">Configurador SAB</div>
          <h1>Configuração de Indicadores</h1>
        </div>
        <div className="page-header-actions">
          <button className="btn btn-primary" type="button">
            + Novo indicador
          </button>
        </div>
      </div>

      <div className="section">
        <div className="section-title">
          Catálogo de indicadores
          <span className="hint">Vigência atual aplicada por padrão aos novos cadastros</span>
        </div>
        <div className="data-table-wrap">
          <table className="data-table">
            <thead>
              <tr>
                <th>Código</th>
                <th>Nome</th>
                <th className="cell-num">Peso</th>
                <th className="cell-num">Meta</th>
                <th>Fórmula</th>
                <th>Tipo de unidade</th>
                <th>Perfil responsável</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {INDICADORES_CATALOGO.map((ind) => (
                <tr key={ind.codigo}>
                  <td className="cell-strong">{ind.codigo}</td>
                  <td>{ind.nome}</td>
                  <td className="cell-num">{ind.peso}%</td>
                  <td className="cell-num">{ind.meta}%</td>
                  <td className="cell-muted">{ind.formula}</td>
                  <td>{ind.tipoUnidade}</td>
                  <td>{nomePerfil(ind.perfilResponsavel)}</td>
                  <td>
                    <span className={`badge ${ind.status === 'Ativo' ? 'badge-validado' : 'badge-rascunho'}`}>
                      <span className="badge-dot" />
                      {ind.status}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      <div className="section">
        <div className="section-title">Vigência / Versionamento</div>
        <p className="helper-text" style={{ marginBottom: 14 }}>
          Diferentes regras podem existir em períodos diferentes. Competências antigas continuam vinculadas à
          versão da regra utilizada no momento — uma nova versão não altera silenciosamente períodos já fechados.
        </p>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
          {VIGENCIAS.map((v) => (
            <div
              key={v.id}
              className="section"
              style={{
                margin: 0,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                borderLeft: v.ativa ? '3px solid var(--color-accent)' : undefined,
              }}
            >
              <div>
                <div className="cell-strong">{v.nome}</div>
                <div className="cell-muted">
                  {v.inicio} até {v.fim}
                </div>
              </div>
              <span className={`badge ${v.ativa ? 'badge-validado' : 'badge-rascunho'}`}>
                <span className="badge-dot" />
                {v.ativa ? 'Vigência ativa' : 'Encerrada'}
              </span>
            </div>
          ))}
        </div>
        <div style={{ marginTop: 14 }}>
          <button className="btn" type="button">
            + Criar nova versão da regra
          </button>
        </div>
      </div>
    </div>
  );
}
