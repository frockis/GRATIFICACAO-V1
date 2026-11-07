// Regras do cadastro de pessoas e unidades no front.
// São as mesmas do backend (backend/cadastro/models.py): validar aqui dá retorno
// imediato no formulário e mantém o modo offline (mockData) coerente.

import type { DadosUnidade, DadosUsuario, ErrosCampos } from '../services/api';
import type { Unidade, Usuario } from '../types';

export const TIPOS_UNIDADE = ['USF', 'UBT', 'UPA', 'Policlínica', 'CAPS', 'Outro'];

export function validarUnidade(
  dados: DadosUnidade,
  unidades: Unidade[],
  usuarios: Usuario[],
  id?: string,
): ErrosCampos {
  const erros: ErrosCampos = {};
  if (!dados.nome.trim()) erros.nome = ['Informe o nome.'];
  if (!dados.distritoId) erros.distritoId = ['Escolha o distrito.'];
  if (!dados.tipo) erros.tipo = ['Escolha o tipo.'];
  if (dados.cnes && !/^\d{7}$/.test(dados.cnes)) erros.cnes = ['O CNES deve ter 7 dígitos.'];
  const repetida = unidades.some(
    (u) => u.id !== id && u.distritoId === dados.distritoId && u.nome.trim() === dados.nome.trim(),
  );
  if (repetida) erros.nome = ['Já existe uma unidade com esse nome no distrito.'];
  const atual = unidades.find((u) => u.id === id);
  if (atual && atual.distritoId !== dados.distritoId && usuarios.some((p) => p.unidadeId === id)) {
    erros.distritoId = ['A unidade tem pessoas vinculadas. Mude o vínculo delas antes de trocar o distrito.'];
  }
  return erros;
}

export function validarUsuario(dados: DadosUsuario, unidades: Unidade[], usuarios: Usuario[], id?: string) {
  const erros: ErrosCampos = {};
  if (!dados.nome.trim()) erros.nome = ['Informe o nome.'];
  if (!/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(dados.email)) erros.email = ['Informe um e-mail válido.'];
  else if (usuarios.some((u) => u.id !== id && u.email.toLowerCase() === dados.email.toLowerCase())) {
    erros.email = ['Já existe uma pessoa com esse e-mail.'];
  }

  if (dados.perfilId === 'gestor') {
    const unidade = unidades.find((u) => u.id === dados.unidadeId);
    if (!unidade) erros.unidadeId = ['Gestor de Unidade precisa estar vinculado a uma unidade.'];
    else if (unidade.status === 'Inativo') erros.unidadeId = ['Não é possível vincular a uma unidade inativa.'];
  } else if (dados.perfilId === 'coordenador') {
    if (!dados.distritoId) erros.distritoId = ['Coordenador Distrital precisa estar vinculado a um distrito.'];
  }
  return erros;
}

/** Ajusta unidade/distrito conforme o perfil (gestor herda o distrito da unidade). */
export function normalizarVinculo(dados: DadosUsuario, unidades: Unidade[]): DadosUsuario {
  if (dados.perfilId === 'gestor') {
    const unidade = unidades.find((u) => u.id === dados.unidadeId);
    return { ...dados, distritoId: unidade?.distritoId ?? null };
  }
  if (dados.perfilId === 'coordenador') return { ...dados, unidadeId: null };
  return { ...dados, unidadeId: null, distritoId: null };
}

/** Próximo id no padrão do protótipo (u5, us10...). */
export function proximoId(prefixo: string, ids: string[]): string {
  const numeros = ids
    .map((id) => new RegExp(`^${prefixo}(\\d+)$`).exec(id))
    .filter((m): m is RegExpExecArray => m !== null)
    .map((m) => Number(m[1]));
  return `${prefixo}${Math.max(0, ...numeros) + 1}`;
}
