// Cliente da API do backend (backend/, Django).
// O Vite encaminha /api para http://127.0.0.1:8000 (ver vite.config.ts).
// Enquanto não há login real, o perfil escolhido no Header vai no cabeçalho X-Perfil.

import type { AuditoriaEntrada, Distrito, PerfilId, StatusCadastro, Unidade, Usuario } from '../types';

const BASE = '/api';

interface Identidade {
  perfil: PerfilId;
  usuario: string;
}

let identidade: Identidade | null = null;

export function definirIdentidade(nova: Identidade) {
  identidade = nova;
}

export type ErrosCampos = Record<string, string[]>;

export class ErroApi extends Error {
  status: number;
  campos: ErrosCampos;

  constructor(status: number, campos: ErrosCampos) {
    super(Object.values(campos).flat().join(' ') || `Erro ${status} na API`);
    this.status = status;
    this.campos = campos;
  }
}

function normalizarErros(corpo: unknown): ErrosCampos {
  if (corpo && typeof corpo === 'object') {
    return Object.fromEntries(
      Object.entries(corpo as Record<string, unknown>).map(([campo, msg]) => [
        campo,
        Array.isArray(msg) ? msg.map(String) : [String(msg)],
      ]),
    );
  }
  return { detail: ['Não foi possível falar com o servidor.'] };
}

async function requisicao<T>(caminho: string, opcoes: RequestInit = {}): Promise<T> {
  const headers: Record<string, string> = { 'Content-Type': 'application/json' };
  if (identidade) {
    headers['X-Perfil'] = identidade.perfil;
    // Cabeçalho HTTP não aceita acentos: vai codificado e o backend decodifica.
    headers['X-Usuario'] = encodeURIComponent(identidade.usuario);
  }

  const resposta = await fetch(`${BASE}${caminho}`, { ...opcoes, headers });
  const texto = await resposta.text();
  let corpo: unknown = null;
  try {
    corpo = texto ? JSON.parse(texto) : null;
  } catch {
    throw new ErroApi(resposta.status || 503, { detail: ['Backend indisponível.'] });
  }
  if (!resposta.ok) throw new ErroApi(resposta.status, normalizarErros(corpo));
  return corpo as T;
}

// A API devolve null em campos vazios; os tipos do front usam campos opcionais.
function semNulos<T extends object>(obj: T): T {
  return Object.fromEntries(Object.entries(obj).filter(([, v]) => v !== null)) as T;
}

export interface DadosUnidade {
  nome: string;
  distritoId: string;
  tipo: string;
  cnes?: string;
}

export interface DadosUsuario {
  nome: string;
  email: string;
  matricula?: string;
  perfilId: PerfilId;
  unidadeId: string | null;
  distritoId: string | null;
}

const json = (dados: unknown) => JSON.stringify(dados);

export const api = {
  listarDistritos: () => requisicao<Distrito[]>('/distritos/'),
  listarUnidades: () => requisicao<Unidade[]>('/unidades/').then((l) => l.map(semNulos)),
  listarUsuarios: () => requisicao<Usuario[]>('/usuarios/').then((l) => l.map(semNulos)),
  listarAuditoria: () => requisicao<AuditoriaEntrada[]>('/auditoria/'),

  criarUnidade: (dados: DadosUnidade) =>
    requisicao<Unidade>('/unidades/', { method: 'POST', body: json(dados) }).then(semNulos),
  atualizarUnidade: (id: string, dados: Partial<DadosUnidade>) =>
    requisicao<Unidade>(`/unidades/${id}/`, { method: 'PATCH', body: json(dados) }).then(semNulos),
  alterarStatusUnidade: (id: string, status: StatusCadastro) =>
    requisicao<Unidade>(`/unidades/${id}/${status === 'Ativo' ? 'reativar' : 'inativar'}/`, {
      method: 'POST',
    }).then(semNulos),

  criarUsuario: (dados: DadosUsuario) =>
    requisicao<Usuario>('/usuarios/', { method: 'POST', body: json(dados) }).then(semNulos),
  atualizarUsuario: (id: string, dados: Partial<DadosUsuario>) =>
    requisicao<Usuario>(`/usuarios/${id}/`, { method: 'PATCH', body: json(dados) }).then(semNulos),
  alterarStatusUsuario: (id: string, status: StatusCadastro) =>
    requisicao<Usuario>(`/usuarios/${id}/${status === 'Ativo' ? 'reativar' : 'inativar'}/`, {
      method: 'POST',
    }).then(semNulos),
};
