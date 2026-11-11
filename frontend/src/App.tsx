import { HashRouter, Routes, Route } from 'react-router-dom';
import { AppProvider } from './context/AppContext';
import { Layout } from './components/Layout';
import { Login } from './pages/Login';
import { Dashboard } from './pages/Dashboard';
import { Indicadores } from './pages/Indicadores';
import { Preenchimento } from './pages/Preenchimento';
import { Validacao } from './pages/Validacao';
import { Fechamento } from './pages/Fechamento';
import { ConfiguracaoIndicadores } from './pages/ConfiguracaoIndicadores';
import { UsuariosPermissoes } from './pages/UsuariosPermissoes';
import { Auditoria } from './pages/Auditoria';
import './components/ui.css';

export default function App() {
  return (
    <AppProvider>
      <HashRouter>
        <Routes>
          <Route path="/" element={<Login />} />
          <Route element={<Layout />}>
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/indicadores" element={<Indicadores />} />
            <Route path="/preenchimento" element={<Preenchimento />} />
            <Route path="/validacao" element={<Validacao />} />
            <Route path="/fechamento" element={<Fechamento />} />
            <Route path="/configuracao-indicadores" element={<ConfiguracaoIndicadores />} />
            <Route path="/usuarios-permissoes" element={<UsuariosPermissoes />} />
            <Route path="/auditoria" element={<Auditoria />} />
          </Route>
        </Routes>
      </HashRouter>
    </AppProvider>
  );
}
