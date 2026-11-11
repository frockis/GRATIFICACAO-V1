import { useNavigate } from 'react-router-dom';
import { useApp, PERFIS } from '../context/AppContext';
import type { PerfilId } from '../types';
import './Header.css';

export function Header() {
  const { perfilAtual, definirPerfil, usuarioAtual, competenciaId, competencias, definirCompetencia, sair } =
    useApp();
  const navigate = useNavigate();
  const competenciaAtual = competencias.find((c) => c.id === competenciaId);
  const perfilInfo = PERFIS.find((p) => p.id === perfilAtual);

  function handleSair() {
    sair();
    navigate('/');
  }

  return (
    <header className="app-header">
      <div className="app-header-left">
        <label className="header-field">
          <span>Competência</span>
          <select value={competenciaId} onChange={(e) => definirCompetencia(e.target.value)}>
            {competencias.map((c) => (
              <option key={c.id} value={c.id}>
                {c.label}
              </option>
            ))}
          </select>
        </label>
        {competenciaAtual && (
          <span className={`header-comp-status header-comp-status--${competenciaAtual.status
            .toLowerCase()
            .replace(/\s+/g, '-')}`}
          >
            {competenciaAtual.status}
          </span>
        )}
      </div>

      <div className="app-header-right">
        <label className="header-field header-field--profile">
          <span>Perfil de visualização</span>
          <select value={perfilAtual} onChange={(e) => definirPerfil(e.target.value as PerfilId)}>
            {PERFIS.map((p) => (
              <option key={p.id} value={p.id}>
                {p.nome}
              </option>
            ))}
          </select>
        </label>

        <button className="header-notif" title="Notificações" type="button">
          🔔
          <span className="header-notif-dot" />
        </button>

        <div className="header-user">
          <div className="header-user-avatar">{usuarioAtual.charAt(0)}</div>
          <div className="header-user-info">
            <div className="header-user-name">{usuarioAtual}</div>
            <div className="header-user-role">{perfilInfo?.nome}</div>
          </div>
        </div>
        <button className="btn btn-sm" type="button" onClick={handleSair}>
          Sair
        </button>
      </div>
    </header>
  );
}
