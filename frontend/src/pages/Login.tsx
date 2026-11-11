import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useApp } from '../context/AppContext';
import './Login.css';

export function Login() {
  const { entrar } = useApp();
  const navigate = useNavigate();
  const [email, setEmail] = useState('ana.souza@saude.gov.br');
  const [senha, setSenha] = useState('••••••••');

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    entrar();
    navigate('/dashboard');
  }

  return (
    <div className="login-screen">
      <div className="login-card">
        <div className="login-brand">
          <div className="login-brand-mark">SG</div>
          <div>
            <div className="login-brand-title">SGGD</div>
            <div className="login-brand-sub">Sistema de Gestão da Gratificação por Desempenho</div>
          </div>
        </div>

        <form onSubmit={handleSubmit} className="login-form">
          <div className="form-field">
            <label htmlFor="email">Usuário / e-mail institucional</label>
            <input
              id="email"
              type="text"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              autoComplete="username"
            />
          </div>
          <div className="form-field">
            <label htmlFor="senha">Senha</label>
            <input
              id="senha"
              type="password"
              value={senha}
              onChange={(e) => setSenha(e.target.value)}
              autoComplete="current-password"
            />
          </div>
          <button type="submit" className="btn btn-primary login-submit">
            Entrar
          </button>
        </form>

        <p className="login-institucional">
          Ambiente de protótipo — Secretaria de Saúde. Dados fictícios utilizados exclusivamente para
          demonstração do fluxo de avaliação, validação e cálculo da gratificação por desempenho.
        </p>
      </div>
    </div>
  );
}
