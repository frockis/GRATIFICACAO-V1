// Tipos centrais do protótipo SGGD
// Sistema de Gestão da Gratificação por Desempenho

export type PerfilId = 'gestor' | 'coordenador' | 'seab' | 'configurador';

export interface Perfil {
  id: PerfilId;
  nome: string;
  descricao: string;
}

export type StatusIndicador =
  | 'Rascunho'
  | 'Enviado'
  | 'Em revisão'
  | 'Devolvido'
  | 'Validado'
  | 'Fechado';

export type StatusCompetencia = 'Aberto' | 'Em revisão' | 'Fechado';

export interface Distrito {
  id: string;
  nome: string;
}

export interface Unidade {
  id: string;
  nome: string;
  distritoId: string;
  tipo: string; // Tipo de unidade (ex: USF, UPA, Policlínica)
}

export interface Usuario {
  id: string;
  nome: string;
  email: string;
  perfilId: PerfilId;
  unidadeId?: string;
  distritoId?: string;
  tipoUnidade?: string;
  status: 'Ativo' | 'Inativo';
}

export interface Competencia {
  id: string; // ex: '2026-09'
  label: string; // ex: 'Setembro/2026'
  status: StatusCompetencia;
  dataPrevistaFechamento: string;
}

export interface HistoricoEntrada {
  id: string;
  usuario: string;
  dataHora: string;
  valorAnterior: string;
  novoValor: string;
  motivo: string;
}

export interface IndicadorCatalogo {
  codigo: string;
  nome: string;
  subindicador?: string;
  peso: number; // percentual, ex 20 = 20%
  meta: number; // percentual meta, ex 90
  unidadeMedida: string; // '%'
  formula: string;
  tipoUnidade: string;
  perfilResponsavel: PerfilId;
  status: 'Ativo' | 'Inativo';
  vigenciaId: string;
}

export interface Vigencia {
  id: string;
  nome: string; // 'Portaria — Janeiro a Junho/2026'
  inicio: string;
  fim: string;
  ativa: boolean;
}

export interface RegistroIndicador {
  id: string;
  indicadorCodigo: string;
  indicadorNome: string;
  subindicador?: string;
  unidadeId: string;
  distritoId: string;
  competenciaId: string;
  meta: number;
  valorInformado: number | null;
  valorValidado: number | null;
  peso: number;
  pontos: number | null;
  pontuacaoFinal: number | null;
  status: StatusIndicador;
  responsavel: string;
  dataAlteracao: string;
  observacoes?: string;
  historico: HistoricoEntrada[];
}

export interface AuditoriaEntrada {
  id: string;
  usuario: string;
  data: string;
  horario: string;
  operacao: string;
  registroAfetado: string;
  valorAnterior: string;
  novoValor: string;
  perfil: string;
  localizacao: string; // unidade/distrito
}
