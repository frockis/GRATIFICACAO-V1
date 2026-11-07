import React, { createContext, useContext, useEffect, useState } from 'react';
import type {
  PerfilId,
  RegistroIndicador,
  AuditoriaEntrada,
  HistoricoEntrada,
  Distrito,
  Unidade,
  Usuario,
  StatusCadastro,
} from '../types';
import {
  PERFIS,
  USUARIOS,
  DISTRITOS,
  UNIDADES,
  COMPETENCIAS,
  COMPETENCIA_ATUAL_ID,
  REGISTROS_INICIAIS,
  AUDITORIA_INICIAL,
} from '../data/mockData';
import { api, definirIdentidade, ErroApi } from '../services/api';
import type { DadosUnidade, DadosUsuario, ErrosCampos } from '../services/api';
import { normalizarVinculo, proximoId, validarUnidade, validarUsuario } from '../utils/cadastro';

/** Cadastro de distritos, unidades e pessoas (componente "cadastro" do backend). */
export interface DadosCadastro {
  distritos: Distrito[];
  unidades: Unidade[];
  usuarios: Usuario[];
}

/** 'api' = dados do backend; 'mock' = backend desligado, usando o mockData nesta sessão. */
export type FonteCadastro = 'carregando' | 'api' | 'mock';

export type ResultadoCadastro = { ok: true } | { ok: false; erros: ErrosCampos };

const CADASTRO_MOCK: DadosCadastro = { distritos: DISTRITOS, unidades: UNIDADES, usuarios: USUARIOS };

const AINDA_CARREGANDO: ResultadoCadastro = {
  ok: false,
  erros: { detail: ['Ainda carregando os dados do cadastro. Tente novamente em instantes.'] },
};

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
  cadastro: DadosCadastro;
  fonteCadastro: FonteCadastro;
  salvarUnidade: (dados: DadosUnidade, id?: string) => Promise<ResultadoCadastro>;
  alterarStatusUnidade: (id: string, status: StatusCadastro) => Promise<ResultadoCadastro>;
  salvarUsuario: (dados: DadosUsuario, id?: string) => Promise<ResultadoCadastro>;
  alterarStatusUsuario: (id: string, status: StatusCadastro) => Promise<ResultadoCadastro>;
}

const AppContext = createContext<AppContextValue | undefined>(undefined);

function nomeUsuarioPorPerfil(perfil: PerfilId, usuarios: Usuario[]): string {
  const usuario = usuarios.find((u) => u.perfilId === perfil && u.status === 'Ativo');
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
  const [cadastro, setCadastro] = useState<DadosCadastro>(CADASTRO_MOCK);
  const [fonteCadastro, setFonteCadastro] = useState<FonteCadastro>('carregando');
  const [auditoriaApi, setAuditoriaApi] = useState<AuditoriaEntrada[]>([]);

  const usuarioAtual = nomeUsuarioPorPerfil(perfilAtual, cadastro.usuarios);

  // Carrega o cadastro do backend; se ele não estiver rodando, segue com o mockData.
  useEffect(() => {
    let ativo = true;
    Promise.all([api.listarDistritos(), api.listarUnidades(), api.listarUsuarios(), api.listarAuditoria()])
      .then(([distritos, unidades, usuarios, aud]) => {
        if (!ativo) return;
        setCadastro({ distritos, unidades, usuarios });
        setAuditoriaApi(aud);
        setFonteCadastro('api');
      })
      .catch(() => {
        if (ativo) setFonteCadastro('mock');
      });
    return () => {
      ativo = false;
    };
  }, []);

  // Enquanto não há login real, o backend sabe quem está operando por estes cabeçalhos.
  useEffect(() => {
    definirIdentidade({ perfil: perfilAtual, usuario: usuarioAtual });
  }, [perfilAtual, usuarioAtual]);

  const nomePerfilAtual = PERFIS.find((p) => p.id === perfilAtual)?.nome ?? '';

  function erroDaApi(e: unknown): ResultadoCadastro {
    if (e instanceof ErroApi) return { ok: false, erros: e.campos };
    return { ok: false, erros: { detail: ['Não foi possível falar com o servidor.'] } };
  }

  function substituir<T extends { id: string }>(lista: T[], item: T): T[] {
    return lista.some((x) => x.id === item.id) ? lista.map((x) => (x.id === item.id ? item : x)) : [...lista, item];
  }

  function atualizarAuditoriaApi() {
    api.listarAuditoria().then(setAuditoriaApi).catch(() => undefined);
  }

  function localizacaoUnidade(unidadeId?: string) {
    const unidade = cadastro.unidades.find((u) => u.id === unidadeId);
    const distrito = cadastro.distritos.find((d) => d.id === unidade?.distritoId);
    return unidade ? `${unidade.nome} — ${distrito?.nome ?? ''}` : 'Município';
  }

  async function salvarUnidade(dados: DadosUnidade, id?: string): Promise<ResultadoCadastro> {
    if (fonteCadastro === 'carregando') return AINDA_CARREGANDO;
    const erros = validarUnidade(dados, cadastro.unidades, cadastro.usuarios, id);
    if (Object.keys(erros).length > 0) return { ok: false, erros };

    if (fonteCadastro === 'api') {
      try {
        const salva = id ? await api.atualizarUnidade(id, dados) : await api.criarUnidade(dados);
        setCadastro((c) => ({ ...c, unidades: substituir(c.unidades, salva) }));
        atualizarAuditoriaApi();
        return { ok: true };
      } catch (e) {
        return erroDaApi(e);
      }
    }

    // Modo offline: grava só nesta sessão, como o restante do protótipo.
    const anterior = cadastro.unidades.find((u) => u.id === id);
    const unidade: Unidade = {
      ...anterior,
      ...dados,
      cnes: dados.cnes || undefined,
      id: id ?? proximoId('u', cadastro.unidades.map((u) => u.id)),
      status: anterior?.status ?? 'Ativo',
    };
    setCadastro((c) => ({ ...c, unidades: substituir(c.unidades, unidade) }));
    registrarAuditoria({
      usuario: usuarioAtual,
      operacao: anterior ? 'Unidade alterada' : 'Unidade cadastrada',
      registroAfetado: `Unidade ${unidade.id} · ${unidade.nome}`,
      valorAnterior: anterior ? anterior.nome : '—',
      novoValor: unidade.nome,
      perfil: nomePerfilAtual,
      localizacao: cadastro.distritos.find((d) => d.id === unidade.distritoId)?.nome ?? '',
    });
    return { ok: true };
  }

  async function alterarStatusUnidade(id: string, status: StatusCadastro): Promise<ResultadoCadastro> {
    if (fonteCadastro === 'carregando') return AINDA_CARREGANDO;
    if (fonteCadastro === 'api') {
      try {
        const salva = await api.alterarStatusUnidade(id, status);
        setCadastro((c) => ({ ...c, unidades: substituir(c.unidades, salva) }));
        atualizarAuditoriaApi();
        return { ok: true };
      } catch (e) {
        return erroDaApi(e);
      }
    }
    const unidade = cadastro.unidades.find((u) => u.id === id);
    if (!unidade) return { ok: false, erros: { detail: ['Unidade não encontrada.'] } };
    if (status === 'Inativo' && cadastro.usuarios.some((u) => u.unidadeId === id && u.status === 'Ativo')) {
      return {
        ok: false,
        erros: { status: ['A unidade ainda tem pessoas ativas vinculadas. Mude o vínculo delas antes de inativar.'] },
      };
    }
    setCadastro((c) => ({ ...c, unidades: substituir(c.unidades, { ...unidade, status }) }));
    registrarAuditoria({
      usuario: usuarioAtual,
      operacao: status === 'Ativo' ? 'Unidade reativada' : 'Unidade inativada',
      registroAfetado: `Unidade ${unidade.id} · ${unidade.nome}`,
      valorAnterior: unidade.status ?? 'Ativo',
      novoValor: status,
      perfil: nomePerfilAtual,
      localizacao: localizacaoUnidade(id),
    });
    return { ok: true };
  }

  async function salvarUsuario(dadosBrutos: DadosUsuario, id?: string): Promise<ResultadoCadastro> {
    if (fonteCadastro === 'carregando') return AINDA_CARREGANDO;
    const dados = normalizarVinculo(dadosBrutos, cadastro.unidades);
    const erros = validarUsuario(dados, cadastro.unidades, cadastro.usuarios, id);
    if (Object.keys(erros).length > 0) return { ok: false, erros };

    if (fonteCadastro === 'api') {
      try {
        const salvo = id ? await api.atualizarUsuario(id, dados) : await api.criarUsuario(dados);
        setCadastro((c) => ({ ...c, usuarios: substituir(c.usuarios, salvo) }));
        atualizarAuditoriaApi();
        return { ok: true };
      } catch (e) {
        return erroDaApi(e);
      }
    }

    const anterior = cadastro.usuarios.find((u) => u.id === id);
    const unidade = cadastro.unidades.find((u) => u.id === dados.unidadeId);
    const usuario: Usuario = {
      id: id ?? proximoId('us', cadastro.usuarios.map((u) => u.id)),
      nome: dados.nome,
      email: dados.email,
      matricula: dados.matricula || undefined,
      perfilId: dados.perfilId,
      unidadeId: dados.unidadeId ?? undefined,
      distritoId: dados.distritoId ?? undefined,
      tipoUnidade: unidade?.tipo,
      status: anterior?.status ?? 'Ativo',
    };
    setCadastro((c) => ({ ...c, usuarios: substituir(c.usuarios, usuario) }));
    const mudouVinculo =
      anterior &&
      (anterior.perfilId !== usuario.perfilId ||
        anterior.unidadeId !== usuario.unidadeId ||
        anterior.distritoId !== usuario.distritoId);
    registrarAuditoria({
      usuario: usuarioAtual,
      operacao: !anterior ? 'Avaliado cadastrado' : mudouVinculo ? 'Vínculo alterado' : 'Avaliado alterado',
      registroAfetado: `Avaliado ${usuario.id} · ${usuario.nome}`,
      valorAnterior: anterior ? localizacaoUnidade(anterior.unidadeId) : '—',
      novoValor: localizacaoUnidade(usuario.unidadeId),
      perfil: nomePerfilAtual,
      localizacao: localizacaoUnidade(usuario.unidadeId),
    });
    return { ok: true };
  }

  async function alterarStatusUsuario(id: string, status: StatusCadastro): Promise<ResultadoCadastro> {
    if (fonteCadastro === 'carregando') return AINDA_CARREGANDO;
    if (fonteCadastro === 'api') {
      try {
        const salvo = await api.alterarStatusUsuario(id, status);
        setCadastro((c) => ({ ...c, usuarios: substituir(c.usuarios, salvo) }));
        atualizarAuditoriaApi();
        return { ok: true };
      } catch (e) {
        return erroDaApi(e);
      }
    }
    const usuario = cadastro.usuarios.find((u) => u.id === id);
    if (!usuario) return { ok: false, erros: { detail: ['Pessoa não encontrada.'] } };
    const unidadeDoUsuario = cadastro.unidades.find((u) => u.id === usuario.unidadeId);
    if (status === 'Ativo' && unidadeDoUsuario?.status === 'Inativo') {
      return { ok: false, erros: { unidadeId: ['Não é possível vincular a uma unidade inativa.'] } };
    }
    setCadastro((c) => ({ ...c, usuarios: substituir(c.usuarios, { ...usuario, status }) }));
    registrarAuditoria({
      usuario: usuarioAtual,
      operacao: status === 'Ativo' ? 'Avaliado reativado' : 'Avaliado inativado',
      registroAfetado: `Avaliado ${usuario.id} · ${usuario.nome}`,
      valorAnterior: usuario.status,
      novoValor: status,
      perfil: nomePerfilAtual,
      localizacao: localizacaoUnidade(usuario.unidadeId),
    });
    return { ok: true };
  }

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
    // Registros do backend (cadastro) primeiro, depois os desta sessão (indicadores etc.).
    auditoria: [...auditoriaApi, ...auditoria],
    cadastro,
    fonteCadastro,
    salvarUnidade,
    alterarStatusUnidade,
    salvarUsuario,
    alterarStatusUsuario,
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
