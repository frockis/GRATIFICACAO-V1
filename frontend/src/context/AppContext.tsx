import React, { createContext, useContext, useState } from 'react';
import type { PerfilId, RegistroIndicador, AuditoriaEntrada, HistoricoEntrada } from '../types';
import {
  PERFIS,
  USUARIOS,
  COMPETENCIAS,
  COMPETENCIA_ATUAL_ID,
  REGISTROS_INICIAIS,
  AUDITORIA_INICIAL,
} from '../data/mockData';

interface AppContextValue {
  autenticado: boolean;
  perfilAtual: PerfilId;
  usuarioAtual: string;
  competenciaId: string;
  competencias: typeof COMPETENCIAS;
  registros: RegistroIndicador[];
  auditoria: AuditoriaEntrada[];
  entrar: () => void;
  sair: () => void;
  definirPerfil: (perfil: PerfilId) => void;
  definirCompetencia: (id: string) => void;
  salvarRascunho: (id: string, valor: number, observacoes?: string) => void;
  enviarParaRevisao: (id: string) => void;
  validarRegistro: (id: string) => void;
  solicitarCorrecao: (id: string, motivo: string) => void;
  devolverRegistro: (id: string, motivo: string) => void;
  fecharCompetencia: (competenciaId: string) => void;
}

const AppContext = createContext<AppContextValue | undefined>(undefined);

function nomeUsuarioPorPerfil(perfil: PerfilId): string {
  const usuario = USUARIOS.find((u) => u.perfilId === perfil && u.status === 'Ativo');
  return usuario?.nome ?? 'Usuário';
}

function agora(): string {
  const d = new Date();
  const pad = (n: number) => String(n).padStart(2, '0');
  return `${pad(d.getDate())}/${pad(d.getMonth() + 1)}/${d.getFullYear()} ${pad(d.getHours())}:${pad(
    d.getMinutes(),
  )}`;
}

export function AppProvider({ children }: { children: React.ReactNode }) {
  const [autenticado, setAutenticado] = useState(false);
  const [perfilAtual, setPerfilAtual] = useState<PerfilId>('gestor');
  const [competenciaId, setCompetenciaId] = useState(COMPETENCIA_ATUAL_ID);
  const [registros, setRegistros] = useState<RegistroIndicador[]>(REGISTROS_INICIAIS);
  const [auditoria, setAuditoria] = useState<AuditoriaEntrada[]>(AUDITORIA_INICIAL);
  const [competencias, setCompetencias] = useState(COMPETENCIAS);

  const usuarioAtual = nomeUsuarioPorPerfil(perfilAtual);

  function registrarAuditoria(entrada: Omit<AuditoriaEntrada, 'id' | 'data' | 'horario'>) {
    const [data, horario] = agora().split(' ');
    setAuditoria((prev) => [
      { ...entrada, id: `aud-${prev.length + 1}-${Date.now()}`, data, horario },
      ...prev,
    ]);
  }

  function atualizarRegistro(
    id: string,
    updater: (r: RegistroIndicador) => RegistroIndicador,
  ) {
    setRegistros((prev) => prev.map((r) => (r.id === id ? updater(r) : r)));
  }

  function addHistorico(r: RegistroIndicador, entrada: Omit<HistoricoEntrada, 'id'>): HistoricoEntrada[] {
    return [{ ...entrada, id: `h-${r.id}-${r.historico.length + 1}` }, ...r.historico];
  }

  const value: AppContextValue = {
    autenticado,
    perfilAtual,
    usuarioAtual,
    competenciaId,
    competencias,
    registros,
    auditoria,
    entrar: () => setAutenticado(true),
    sair: () => setAutenticado(false),
    definirPerfil: (perfil) => setPerfilAtual(perfil),
    definirCompetencia: (id) => setCompetenciaId(id),
    salvarRascunho: (id, valor, observacoes) => {
      atualizarRegistro(id, (r) => ({
        ...r,
        valorInformado: valor,
        observacoes,
        status: 'Rascunho',
        dataAlteracao: agora().split(' ')[0],
        historico: addHistorico(r, {
          usuario: usuarioAtual,
          dataHora: agora(),
          valorAnterior: r.valorInformado !== null ? `${r.valorInformado}%` : '—',
          novoValor: `${valor}% (rascunho)`,
          motivo: 'Rascunho salvo pelo gestor',
        }),
      }));
    },
    enviarParaRevisao: (id) => {
      const registro = registros.find((r) => r.id === id);
      atualizarRegistro(id, (r) => ({
        ...r,
        status: 'Enviado',
        dataAlteracao: agora().split(' ')[0],
        historico: addHistorico(r, {
          usuario: usuarioAtual,
          dataHora: agora(),
          valorAnterior: 'Rascunho',
          novoValor: 'Enviado',
          motivo: 'Enviado para revisão do coordenador distrital',
        }),
      }));
      if (registro) {
        registrarAuditoria({
          usuario: usuarioAtual,
          operacao: 'Indicador enviado',
          registroAfetado: `${registro.indicadorCodigo} · ${registro.indicadorNome}`,
          valorAnterior: 'Rascunho',
          novoValor: 'Enviado',
          perfil: PERFIS.find((p) => p.id === perfilAtual)?.nome ?? '',
          localizacao: registro.unidadeId,
        });
      }
    },
    validarRegistro: (id) => {
      const registro = registros.find((r) => r.id === id);
      atualizarRegistro(id, (r) => ({
        ...r,
        status: 'Validado',
        valorValidado: r.valorInformado,
        pontos: r.valorInformado !== null ? Math.round(Math.min(r.valorInformado / r.meta, 1) * r.peso * 10) / 10 : null,
        pontuacaoFinal: r.valorInformado !== null ? Math.round(Math.min(r.valorInformado / r.meta, 1) * r.peso * 10) / 10 : null,
        dataAlteracao: agora().split(' ')[0],
        historico: addHistorico(r, {
          usuario: usuarioAtual,
          dataHora: agora(),
          valorAnterior: r.status,
          novoValor: 'Validado',
          motivo: 'Validado após conferência dos dados enviados',
        }),
      }));
      if (registro) {
        registrarAuditoria({
          usuario: usuarioAtual,
          operacao: 'Indicador validado',
          registroAfetado: `${registro.indicadorCodigo} · ${registro.indicadorNome}`,
          valorAnterior: registro.status,
          novoValor: 'Validado',
          perfil: PERFIS.find((p) => p.id === perfilAtual)?.nome ?? '',
          localizacao: registro.unidadeId,
        });
      }
    },
    solicitarCorrecao: (id, motivo) => {
      const registro = registros.find((r) => r.id === id);
      atualizarRegistro(id, (r) => ({
        ...r,
        status: 'Em revisão',
        observacoes: motivo,
        dataAlteracao: agora().split(' ')[0],
        historico: addHistorico(r, {
          usuario: usuarioAtual,
          dataHora: agora(),
          valorAnterior: r.status,
          novoValor: 'Em revisão',
          motivo,
        }),
      }));
      if (registro) {
        registrarAuditoria({
          usuario: usuarioAtual,
          operacao: 'Correção solicitada',
          registroAfetado: `${registro.indicadorCodigo} · ${registro.indicadorNome}`,
          valorAnterior: registro.status,
          novoValor: 'Em revisão',
          perfil: PERFIS.find((p) => p.id === perfilAtual)?.nome ?? '',
          localizacao: registro.unidadeId,
        });
      }
    },
    devolverRegistro: (id, motivo) => {
      const registro = registros.find((r) => r.id === id);
      atualizarRegistro(id, (r) => ({
        ...r,
        status: 'Devolvido',
        observacoes: motivo,
        dataAlteracao: agora().split(' ')[0],
        historico: addHistorico(r, {
          usuario: usuarioAtual,
          dataHora: agora(),
          valorAnterior: r.status,
          novoValor: 'Devolvido',
          motivo,
        }),
      }));
      if (registro) {
        registrarAuditoria({
          usuario: usuarioAtual,
          operacao: 'Indicador devolvido',
          registroAfetado: `${registro.indicadorCodigo} · ${registro.indicadorNome}`,
          valorAnterior: registro.status,
          novoValor: 'Devolvido',
          perfil: PERFIS.find((p) => p.id === perfilAtual)?.nome ?? '',
          localizacao: registro.unidadeId,
        });
      }
    },
    fecharCompetencia: (compId) => {
      setCompetencias((prev) =>
        prev.map((c) => (c.id === compId ? { ...c, status: 'Fechado' } : c)),
      );
      registrarAuditoria({
        usuario: usuarioAtual,
        operacao: 'Competência fechada',
        registroAfetado: `Competência ${compId}`,
        valorAnterior: 'Em revisão',
        novoValor: 'Fechado',
        perfil: PERFIS.find((p) => p.id === perfilAtual)?.nome ?? '',
        localizacao: 'Município',
      });
    },
  };

  return <AppContext.Provider value={value}>{children}</AppContext.Provider>;
}

export function useApp(): AppContextValue {
  const ctx = useContext(AppContext);
  if (!ctx) throw new Error('useApp deve ser usado dentro de AppProvider');
  return ctx;
}

export { PERFIS };
