import type {
  Perfil,
  Distrito,
  Unidade,
  Usuario,
  Competencia,
  Vigencia,
  IndicadorCatalogo,
  RegistroIndicador,
  AuditoriaEntrada,
} from '../types';

export const PERFIS: Perfil[] = [
  {
    id: 'gestor',
    nome: 'Gestor de Unidade',
    descricao: 'Preenche indicadores da própria unidade e acompanha o histórico.',
  },
  {
    id: 'coordenador',
    nome: 'Coordenador Distrital',
    descricao: 'Acompanha e valida as unidades do seu distrito.',
  },
  {
    id: 'seab',
    nome: 'SEAB/CAM — Monitoramento',
    descricao: 'Visão consolidada do município, validação e fechamento.',
  },
  {
    id: 'configurador',
    nome: 'Configurador SAB',
    descricao: 'Configura indicadores, metas, pesos e vigências das regras.',
  },
];

export const DISTRITOS: Distrito[] = [
  { id: 'd1', nome: 'Distrito I' },
  { id: 'd2', nome: 'Distrito II' },
  { id: 'd3', nome: 'Distrito III' },
];

export const UNIDADES: Unidade[] = [
  { id: 'u1', nome: 'USF Boa Viagem', distritoId: 'd1', tipo: 'USF' },
  { id: 'u2', nome: 'USF Casa Amarela', distritoId: 'd1', tipo: 'USF' },
  { id: 'u3', nome: 'USF Ibura', distritoId: 'd2', tipo: 'USF' },
  { id: 'u4', nome: 'USF Várzea', distritoId: 'd3', tipo: 'USF' },
];

export const USUARIOS: Usuario[] = [
  {
    id: 'us1',
    nome: 'Ana Beatriz Souza',
    email: 'ana.souza@saude.gov.br',
    perfilId: 'gestor',
    unidadeId: 'u1',
    distritoId: 'd1',
    tipoUnidade: 'USF',
    status: 'Ativo',
  },
  {
    id: 'us2',
    nome: 'Carlos Eduardo Lima',
    email: 'carlos.lima@saude.gov.br',
    perfilId: 'gestor',
    unidadeId: 'u2',
    distritoId: 'd1',
    tipoUnidade: 'USF',
    status: 'Ativo',
  },
  {
    id: 'us3',
    nome: 'Fernanda Alves Rocha',
    email: 'fernanda.rocha@saude.gov.br',
    perfilId: 'gestor',
    unidadeId: 'u3',
    distritoId: 'd2',
    tipoUnidade: 'USF',
    status: 'Ativo',
  },
  {
    id: 'us4',
    nome: 'João Pedro Nascimento',
    email: 'joao.nascimento@saude.gov.br',
    perfilId: 'gestor',
    unidadeId: 'u4',
    distritoId: 'd3',
    tipoUnidade: 'USF',
    status: 'Ativo',
  },
  {
    id: 'us5',
    nome: 'Marcela Torres Dias',
    email: 'marcela.dias@saude.gov.br',
    perfilId: 'coordenador',
    distritoId: 'd1',
    status: 'Ativo',
  },
  {
    id: 'us6',
    nome: 'Roberto Cavalcanti',
    email: 'roberto.cavalcanti@saude.gov.br',
    perfilId: 'coordenador',
    distritoId: 'd2',
    status: 'Ativo',
  },
  {
    id: 'us7',
    nome: 'Patrícia Gomes Freitas',
    email: 'patricia.freitas@saude.gov.br',
    perfilId: 'seab',
    status: 'Ativo',
  },
  {
    id: 'us8',
    nome: 'Diego Martins Barros',
    email: 'diego.barros@saude.gov.br',
    perfilId: 'configurador',
    status: 'Ativo',
  },
  {
    id: 'us9',
    nome: 'Luciana Pereira Melo',
    email: 'luciana.melo@saude.gov.br',
    perfilId: 'coordenador',
    distritoId: 'd3',
    status: 'Inativo',
  },
];

export const COMPETENCIAS: Competencia[] = [
  { id: '2026-07', label: 'Julho/2026', status: 'Fechado', dataPrevistaFechamento: '05/08/2026' },
  { id: '2026-08', label: 'Agosto/2026', status: 'Fechado', dataPrevistaFechamento: '05/09/2026' },
  { id: '2026-09', label: 'Setembro/2026', status: 'Em revisão', dataPrevistaFechamento: '05/10/2026' },
];

export const COMPETENCIA_ATUAL_ID = '2026-09';

export const VIGENCIAS: Vigencia[] = [
  {
    id: 'v1',
    nome: 'Portaria — Janeiro a Junho/2026',
    inicio: '01/01/2026',
    fim: '30/06/2026',
    ativa: false,
  },
  {
    id: 'v2',
    nome: 'Portaria — Julho a Dezembro/2026',
    inicio: '01/07/2026',
    fim: '31/12/2026',
    ativa: true,
  },
];

export const INDICADORES_CATALOGO: IndicadorCatalogo[] = [
  {
    codigo: 'IND-01',
    nome: 'Cobertura de acompanhamento',
    peso: 20,
    meta: 90,
    unidadeMedida: '%',
    formula: '(Pacientes acompanhados / Pacientes elegíveis) × 100',
    tipoUnidade: 'USF',
    perfilResponsavel: 'gestor',
    status: 'Ativo',
    vigenciaId: 'v2',
  },
  {
    codigo: 'IND-02',
    nome: 'Visitas domiciliares',
    peso: 15,
    meta: 85,
    unidadeMedida: '%',
    formula: '(Visitas realizadas / Visitas programadas) × 100',
    tipoUnidade: 'USF',
    perfilResponsavel: 'gestor',
    status: 'Ativo',
    vigenciaId: 'v2',
  },
  {
    codigo: 'IND-03',
    nome: 'Acompanhamento de gestantes',
    peso: 25,
    meta: 95,
    unidadeMedida: '%',
    formula: '(Gestantes acompanhadas / Gestantes cadastradas) × 100',
    tipoUnidade: 'USF',
    perfilResponsavel: 'gestor',
    status: 'Ativo',
    vigenciaId: 'v2',
  },
  {
    codigo: 'IND-04',
    nome: 'Controle de hipertensos',
    peso: 20,
    meta: 80,
    unidadeMedida: '%',
    formula: '(Hipertensos controlados / Hipertensos cadastrados) × 100',
    tipoUnidade: 'USF',
    perfilResponsavel: 'gestor',
    status: 'Ativo',
    vigenciaId: 'v2',
  },
  {
    codigo: 'IND-05',
    nome: 'Acompanhamento de diabéticos',
    peso: 20,
    meta: 80,
    unidadeMedida: '%',
    formula: '(Diabéticos acompanhados / Diabéticos cadastrados) × 100',
    tipoUnidade: 'USF',
    perfilResponsavel: 'gestor',
    status: 'Ativo',
    vigenciaId: 'v2',
  },
];

function calcPontos(meta: number, valorValidado: number | null, peso: number) {
  if (valorValidado === null) return null;
  const atingimento = Math.min(valorValidado / meta, 1);
  return Math.round(atingimento * peso * 10) / 10;
}

// Combinação fixa de status por unidade para demonstrar todos os estágios do fluxo
const STATUS_POR_UNIDADE: Record<string, RegistroIndicador['status'][]> = {
  u1: ['Validado', 'Enviado', 'Em revisão', 'Devolvido', 'Rascunho'],
  u2: ['Em revisão', 'Validado', 'Rascunho', 'Enviado', 'Validado'],
  u3: ['Devolvido', 'Rascunho', 'Validado', 'Em revisão', 'Enviado'],
  u4: ['Rascunho', 'Rascunho', 'Enviado', 'Validado', 'Em revisão'],
};

const VALORES_INFORMADOS: Record<string, number[]> = {
  u1: [88, 80, 96, 76, 82],
  u2: [91, 87, 93, 79, 78],
  u3: [70, 60, 90, 65, 74],
  u4: [95, 88, 98, 84, 88],
};

function buildRegistros(): RegistroIndicador[] {
  const registros: RegistroIndicador[] = [];
  let seq = 1;
  for (const unidade of UNIDADES) {
    const statusList = STATUS_POR_UNIDADE[unidade.id];
    const valores = VALORES_INFORMADOS[unidade.id];
    INDICADORES_CATALOGO.forEach((ind, idx) => {
      const status = statusList[idx];
      const informado = ['Rascunho'].includes(status) && idx % 2 === 0 ? null : valores[idx];
      const validado =
        status === 'Validado' || status === 'Fechado' ? valores[idx] - 2 : status === 'Devolvido' ? null : null;
      const pontos = calcPontos(ind.meta, validado, ind.peso);
      const responsavel = USUARIOS.find((u) => u.unidadeId === unidade.id)?.nome ?? '—';

      const historico = [
        {
          id: `h-${seq}-1`,
          usuario: responsavel,
          dataHora: '02/09/2026 09:14',
          valorAnterior: '—',
          novoValor: informado !== null ? `${informado}%` : 'Rascunho salvo',
          motivo: 'Preenchimento inicial do indicador',
        },
      ];
      if (status === 'Devolvido') {
        historico.push({
          id: `h-${seq}-2`,
          usuario: 'Marcela Torres Dias',
          dataHora: '05/09/2026 14:32',
          valorAnterior: `${informado}%`,
          novoValor: '—',
          motivo: 'Divergência com relatório de produção da unidade — solicitada revisão',
        });
      }
      if (status === 'Validado') {
        historico.push({
          id: `h-${seq}-2`,
          usuario: 'Patrícia Gomes Freitas',
          dataHora: '08/09/2026 11:02',
          valorAnterior: `${informado}%`,
          novoValor: `${validado}%`,
          motivo: 'Validado após conferência com sistema de produção',
        });
      }

      registros.push({
        id: `reg-${seq}`,
        indicadorCodigo: ind.codigo,
        indicadorNome: ind.nome,
        unidadeId: unidade.id,
        distritoId: unidade.distritoId,
        competenciaId: COMPETENCIA_ATUAL_ID,
        meta: ind.meta,
        valorInformado: informado,
        valorValidado: validado,
        peso: ind.peso,
        pontos,
        pontuacaoFinal: pontos,
        status,
        responsavel,
        dataAlteracao: '08/09/2026',
        observacoes: status === 'Devolvido' ? 'Necessário reenviar com evidências atualizadas.' : undefined,
        historico,
      });
      seq += 1;
    });
  }
  return registros;
}

export const REGISTROS_INICIAIS: RegistroIndicador[] = buildRegistros();

export const AUDITORIA_INICIAL: AuditoriaEntrada[] = [
  {
    id: 'aud-1',
    usuario: 'Ana Beatriz Souza',
    data: '02/09/2026',
    horario: '09:14',
    operacao: 'Indicador enviado',
    registroAfetado: 'IND-01 · USF Boa Viagem',
    valorAnterior: 'Rascunho',
    novoValor: 'Enviado',
    perfil: 'Gestor de Unidade',
    localizacao: 'USF Boa Viagem — Distrito I',
  },
  {
    id: 'aud-2',
    usuario: 'Marcela Torres Dias',
    data: '05/09/2026',
    horario: '14:32',
    operacao: 'Indicador devolvido',
    registroAfetado: 'IND-04 · USF Boa Viagem',
    valorAnterior: 'Em revisão',
    novoValor: 'Devolvido',
    perfil: 'Coordenador Distrital',
    localizacao: 'USF Boa Viagem — Distrito I',
  },
  {
    id: 'aud-3',
    usuario: 'Patrícia Gomes Freitas',
    data: '08/09/2026',
    horario: '11:02',
    operacao: 'Indicador validado',
    registroAfetado: 'IND-01 · USF Boa Viagem',
    valorAnterior: 'Enviado',
    novoValor: 'Validado',
    perfil: 'SEAB/CAM',
    localizacao: 'Município',
  },
  {
    id: 'aud-4',
    usuario: 'Diego Martins Barros',
    data: '01/07/2026',
    horario: '08:00',
    operacao: 'Regra alterada',
    registroAfetado: 'Vigência — Portaria Julho a Dezembro/2026',
    valorAnterior: 'Portaria Jan-Jun/2026',
    novoValor: 'Portaria Jul-Dez/2026',
    perfil: 'Configurador SAB',
    localizacao: 'Município',
  },
  {
    id: 'aud-5',
    usuario: 'Patrícia Gomes Freitas',
    data: '05/09/2026',
    horario: '18:00',
    operacao: 'Competência fechada',
    registroAfetado: 'Competência Agosto/2026',
    valorAnterior: 'Em revisão',
    novoValor: 'Fechado',
    perfil: 'SEAB/CAM',
    localizacao: 'Município',
  },
];
