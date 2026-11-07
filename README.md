# SGGD — Sistema de Gestão da Gratificação por Desempenho

Protótipo navegável (frontend, dados mockados) para apoiar o processo de avaliação, validação e
cálculo da gratificação por desempenho de equipes de saúde. O objetivo desta versão é demonstrar o
fluxo completo do sistema — do preenchimento dos indicadores pelo gestor de unidade até a validação,
o cálculo da pontuação e o fechamento mensal da competência — para discussão com a equipe.

**Não há backend, banco de dados ou autenticação real.** Todos os dados são fictícios e o estado das
telas vive apenas na memória do navegador durante a sessão (ao recarregar a página, os dados voltam
ao ponto inicial).

## O que o protótipo cobre

- **Login** simples (qualquer clique em "Entrar" acessa o sistema).
- **Seletor de perfil** no topo, para alternar entre os quatro papéis sem precisar de múltiplos
  logins:
  - **Gestor de Unidade** — preenche indicadores da própria unidade, salva rascunhos e envia para
    revisão.
  - **Coordenador Distrital** — acompanha e valida as unidades do seu distrito.
  - **SEAB/CAM (Monitoramento)** — visão consolidada do município, validação final e fechamento da
    competência.
  - **Configurador SAB** — administra o catálogo de indicadores, pesos, metas e vigências das regras.
- **Dashboard** com indicadores pendentes/enviados/em revisão/validados e pontuação provisória,
  variando conforme o perfil selecionado.
- **Indicadores** — tabela com filtros (competência, distrito, tipo de unidade, status) e painel de
  detalhes com o cálculo da pontuação explicado ("Como foi calculado?") e histórico do registro.
- **Preenchimento** — formulário do gestor, com fluxo de status Rascunho → Enviado → Em revisão →
  Devolvido → Validado → Fechado.
- **Validação** — tela do coordenador e do SEAB/CAM, com ações de validar, solicitar correção e
  devolver, representando o fluxo Gestor → Coordenador Distrital → SEAB/CAM.
- **Fechamento** — ciclo Aberto → Em revisão → Fechado da competência, com bloqueio visual dos
  valores após o fechamento.
- **Configuração de Indicadores** — catálogo de indicadores e seção de vigência/versionamento das
  regras (ex.: Portaria Jan-Jun/2026 vs. Jul-Dez/2026).
- **Usuários e Permissões** — listagem de usuários e explicação do modelo de acesso (Papel + Escopo
  territorial + Tipo de unidade).
- **Auditoria** — histórico de operações do sistema, para rastreabilidade.

Todas as ações (salvar rascunho, enviar, validar, devolver, solicitar correção, fechar competência)
atualizam o estado do protótipo em tempo real e ficam registradas na tela de Auditoria.

## Tecnologia

- [Vite](https://vitejs.dev/) + [React](https://react.dev/) + TypeScript
- [React Router](https://reactrouter.com/) (`HashRouter`) para a navegação entre telas
- CSS puro, organizado por componente/página (sem framework de UI)
- Estado da aplicação em memória via React Context (`src/context/AppContext.tsx`), sem persistência

## Estrutura do projeto

```
src/
  types/         Tipos TypeScript compartilhados (indicadores, usuários, competências, etc.)
  data/          Dados mockados centralizados (distritos, unidades, usuários, catálogo, registros)
  context/       AppContext — perfil atual, competência atual e ações sobre os indicadores
  utils/         Regras de escopo territorial (quem vê o quê, conforme o perfil)
  components/    Sidebar, Header, Layout, badges de status, tabela de detalhes, fluxo de status
  pages/         Uma página por tela do sistema (Login, Dashboard, Indicadores, Preenchimento, ...)
  App.tsx        Rotas da aplicação
  main.tsx       Ponto de entrada
```

## Como rodar localmente

Pré-requisitos: [Node.js](https://nodejs.org/) 18 ou superior (o protótipo foi criado e testado com
Node 22) e o npm correspondente.

1. Abra a pasta do projeto no terminal (ou use o terminal integrado do VS Code).
2. Instale as dependências (só é necessário na primeira vez, ou quando o `package.json` mudar):

   ```bash
   npm install
   ```

3. Inicie o servidor de desenvolvimento:

   ```bash
   npm run dev
   ```

4. Abra o endereço mostrado no terminal (por padrão [http://localhost:5173](http://localhost:5173))
   no navegador.

Para gerar uma build de produção (arquivos estáticos otimizados) e conferir que tudo compila sem
erros:

```bash
npm run build
```

Os arquivos gerados ficam em `dist/`. Para servi-los localmente e conferir o resultado:

```bash
npm run preview
```

## Backend (em construção)

A pasta [`backend/`](backend/README.md) tem o backend em Django, um app por componente do plano de
desenvolvimento. Já existe o componente **Cadastro de Avaliados e Unidades**: com o backend rodando
(`python manage.py runserver` em `backend/`), distritos, unidades e usuários passam a vir da API e a tela
**Usuários e Permissões** cadastra, edita e inativa pessoas e unidades de verdade, com registro na
**Auditoria**. Sem o backend, o front continua usando o `mockData.ts`. Instruções em `backend/README.md`.

## Como navegar no protótipo

1. Na tela de login, clique em **Entrar** (não é necessário preencher usuário/senha reais).
2. Você começa como **Gestor de Unidade**. Vá até **Preenchimento**, clique em **Preencher** em um
   indicador, informe um valor e escolha **Salvar rascunho** ou **Enviar para revisão**.
3. No topo da tela, troque o **perfil de visualização** para **Coordenador Distrital** (ou
   **SEAB/CAM**) e acesse **Validação** para validar, solicitar correção ou devolver o indicador que
   você acabou de enviar.
4. Como **SEAB/CAM**, acesse **Fechamento** para acompanhar pendências e fechar a competência atual.
5. Como **Configurador SAB**, acesse **Configuração de Indicadores** para ver o catálogo e as
   vigências das regras, e **Usuários e Permissões** para ver o modelo de acesso.
6. A qualquer momento, acesse **Auditoria** para ver o histórico de todas as ações realizadas durante
   a sessão.

## Limitações conhecidas (por ser um protótipo)

- Não há persistência: recarregar a página reinicia os dados para o estado inicial mockado.
- Não há autenticação, permissões de segurança ou integração com sistemas externos reais.
- O cálculo da pontuação é ilustrativo, não reflete a fórmula jurídica/oficial da gratificação.
- O foco é desktop (telas a partir de 1366×768); não há otimização para dispositivos móveis.

## Próximos passos sugeridos

- Conectar um backend real (API) para persistir indicadores, usuários e histórico.
- Implementar autenticação e controle de acesso reais.
- Refinar as regras de cálculo com a fórmula oficial da gratificação.
- Adicionar exportação de dados (ex.: planilha ou PDF) a partir das telas de Indicadores e Auditoria.
