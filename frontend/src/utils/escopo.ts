import type { PerfilId, RegistroIndicador, Unidade, Usuario } from '../types';

/** Dados de cadastro usados no escopo (vêm do AppContext: API ou mockData). */
export interface DadosEscopo {
  usuarios: Usuario[];
  unidades: Unidade[];
}

/**
 * Retorna a unidade e o distrito associados ao usuário logado no perfil atual,
 * usado para restringir a visualização conforme o escopo territorial do perfil.
 */
export function usuarioDoPerfil(perfil: PerfilId, dados: DadosEscopo) {
  return dados.usuarios.find((u) => u.perfilId === perfil && u.status === 'Ativo');
}

export function unidadesDoEscopo(perfil: PerfilId, dados: DadosEscopo): Unidade[] {
  const usuario = usuarioDoPerfil(perfil, dados);
  // Sem pessoa ativa vinculada ao perfil, gestor/coordenador não veem nada (nunca o município todo).
  if (perfil === 'gestor') {
    return usuario?.unidadeId ? dados.unidades.filter((u) => u.id === usuario.unidadeId) : [];
  }
  if (perfil === 'coordenador') {
    return usuario?.distritoId ? dados.unidades.filter((u) => u.distritoId === usuario.distritoId) : [];
  }
  // SEAB/CAM e Configurador enxergam todas as unidades do município
  return dados.unidades;
}

export function filtrarRegistrosPorEscopo(
  registros: RegistroIndicador[],
  perfil: PerfilId,
  dados: DadosEscopo,
): RegistroIndicador[] {
  const unidadesIds = new Set(unidadesDoEscopo(perfil, dados).map((u) => u.id));
  return registros.filter((r) => unidadesIds.has(r.unidadeId));
}

export function labelEscopo(perfil: PerfilId, dados: DadosEscopo): string {
  const usuario = usuarioDoPerfil(perfil, dados);
  if (perfil === 'gestor') {
    const unidade = dados.unidades.find((u) => u.id === usuario?.unidadeId);
    return unidade ? `Minha unidade — ${unidade.nome}` : 'Minha unidade';
  }
  if (perfil === 'coordenador') {
    return 'Meu distrito';
  }
  if (perfil === 'seab') {
    return 'Visão municipal';
  }
  return 'Configuração de regras';
}
