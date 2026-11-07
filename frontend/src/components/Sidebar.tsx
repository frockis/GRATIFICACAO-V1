import { NavLink } from 'react-router-dom';
import { useApp } from '../context/AppContext';
import './Sidebar.css';

interface NavItem {
  to: string;
  label: string;
  perfis?: string[];
}

const ITENS: NavItem[] = [
  { to: '/dashboard', label: 'Dashboard' },
  { to: '/indicadores', label: 'Indicadores' },
  { to: '/preenchimento', label: 'Preenchimento', perfis: ['gestor'] },
  { to: '/validacao', label: 'Validação', perfis: ['coordenador', 'seab'] },
  { to: '/fechamento', label: 'Fechamento', perfis: ['seab'] },
  { to: '/configuracao-indicadores', label: 'Configuração de Indicadores', perfis: ['configurador'] },
  { to: '/usuarios-permissoes', label: 'Usuários e Permissões', perfis: ['configurador', 'seab'] },
  { to: '/auditoria', label: 'Auditoria' },
];

export function Sidebar() {
  const { perfilAtual, fonteCadastro } = useApp();
  const itensVisiveis = ITENS.filter((item) => !item.perfis || item.perfis.includes(perfilAtual));

  return (
    <aside className="sidebar">
      <div className="sidebar-brand">
        <div className="sidebar-brand-mark">SG</div>
        <div>
          <div className="sidebar-brand-title">SGGD</div>
          <div className="sidebar-brand-sub">Gestão da Gratificação</div>
        </div>
      </div>
      <nav className="sidebar-nav">
        {itensVisiveis.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            className={({ isActive }) => `sidebar-link${isActive ? ' active' : ''}`}
          >
            {item.label}
          </NavLink>
        ))}
      </nav>
      <div className="sidebar-footer">
        <p className="helper-text">
          {fonteCadastro === 'api'
            ? 'Protótipo v1 · cadastro conectado ao backend'
            : 'Protótipo v1 · dados fictícios'}
        </p>
      </div>
    </aside>
  );
}
