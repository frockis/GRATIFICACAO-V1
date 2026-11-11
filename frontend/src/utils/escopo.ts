import type { PerfilId, RegistroIndicador, Unidade } from '../types';
import { USUARIOS, UNIDADES } from '../data/mockData';

/**
 * Retorna a unidade e o distrito associados ao usuário logado no perfil atual,
 * usado para restringir a visualização conforme o escopo territorial do perfil.
 */
export function usuarioDoPerfil(perfil: PerfilId) {
  return USUARIOS.find((u) => u.perfilId === perfil && u.status === 'Ativo');
}

export function unidadesDoEscopo(perfil: PerfilId): Unidade[] {
  const usuario = usuarioDoPerfil(perfil);
  if (perfil === 'gestor' && usuario?.unidadeId) {
    return UNIDADES.filter((u) => u.id === usuario.unidadeId);
  }
  if (perfil === 'coordenador' && usuario?.distritoId) {
    return UNIDADES.filter((u) => u.distritoId === usuario.distritoId);
  }
  // SEAB/CAM e Configurador enxergam todas as unidades do município
  return UNIDADES;
}

export function filtrarRegistrosPorEscopo(
  registros: RegistroIndicador[],
  perfil: PerfilId,
): RegistroIndicador[] {
  const unidadesIds = new Set(unidadesDoEscopo(perfil).map((u) => u.id));
  return registros.filter((r) => unidadesIds.has(r.unidadeId));
}

export function labelEscopo(perfil: PerfilId): string {
  const usuario = usuarioDoPerfil(perfil);
  if (perfil === 'gestor') {
    const unidade = UNIDADES.find((u) => u.id === usuario?.unidadeId);
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
