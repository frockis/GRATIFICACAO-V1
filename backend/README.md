# Backend do SGGD (Django)

Monólito modular: cada componente é um app Django em `apps/`, com suas próprias tabelas no mesmo
banco PostgreSQL. Um componente só usa outro pelo módulo público `apps/<componente>/interface.py`
(verificado pelo import-linter).

| App | Componente | Situação |
|---|---|---|
| `acesso` | Controle de Acesso (usuários, papéis, permissões) | implementado |
| `cadastro` | Cadastro de Avaliados e Unidades | implementado |
| `auditoria` | Registro de Auditoria | base mínima (modelo + `registrar()` + listagem), para o responsável evoluir |
| `normativa`, `coleta`, `apuracao`, `recurso`, `publicacao`, `pagamento` | demais componentes | a fazer |

## Requisitos

- Python 3.12+ (testado com 3.13)
- PostgreSQL (testado com a versão 16)

## Configuração

```bash
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate    Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env    # e preencha os valores
```

Variáveis (`backend/.env`, que não vai para o Git):

| Variável | Obrigatória | Descrição |
|---|---|---|
| `DJANGO_SECRET_KEY` | sim | Chave secreta do Django |
| `DJANGO_DEBUG` | não (padrão `0`) | `1` só em desenvolvimento |
| `DJANGO_ALLOWED_HOSTS` | não (padrão `localhost,127.0.0.1`) | Hosts separados por vírgula |
| `SGGD_PERFIL_SIMULADO` | não (padrão `0`) | `1` liga o modo demonstração do protótipo (só com `DJANGO_DEBUG=1`, ver abaixo) |
| `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD` | sim | Banco e credenciais |
| `POSTGRES_HOST`, `POSTGRES_PORT` | não (padrão `localhost`, `5432`) | Servidor |

Criar o banco no PostgreSQL (exemplo, como administrador do servidor):

```sql
CREATE ROLE sggd LOGIN PASSWORD 'senha123' CREATEDB;  -- CREATEDB: para o banco de testes
CREATE DATABASE sggd OWNER sggd;
```

## Comandos

```bash
python manage.py migrate            # aplica as migrações
python manage.py createsuperuser    # primeiro usuário administrador
python manage.py importar_cadastro  # carrega os mesmos dados fictícios do frontend/src/data/mockData.ts
python manage.py runserver          # http://127.0.0.1:8000 (admin em /admin/)
python manage.py test               # testes
lint-imports                        # fronteiras entre componentes
```

Para usar com o front: com o backend rodando, em outro terminal rode `cd frontend && npm run dev`. O Vite
encaminha `/api` para o Django. Com o backend desligado, o front continua funcionando com o `mockData.ts`.

### Modo demonstração (protótipo)

O front ainda não tem login: o seletor de perfil do Header manda o perfil no cabeçalho `X-Perfil` (e o
nome da pessoa em `X-Usuario`). Com `DJANGO_DEBUG=1` e `SGGD_PERFIL_SIMULADO=1`,
`apps/acesso/autenticacao.py` troca esse perfil por um usuário de demonstração (`demo-<perfil>`, criado
na primeira requisição) com o papel equivalente. Quem decide o que pode ser feito é o Controle de Acesso:

| Perfil do front | Papel (Group) | Pode cadastrar unidades/avaliados? |
|---|---|---|
| `configurador` (Configurador SAB) | Configurador | sim |
| `seab` (SEAB/CAM) | CAM/SECOGE | não |
| `gestor`, `coordenador` | Avaliado | não |

Fora desse modo (produção, ou `DEBUG=0`), o cabeçalho é ignorado e vale só a sessão do Django. O modo sai
quando a autenticação institucional (OIDC/SAML) for definida.

## Componente Controle de Acesso (`apps/acesso`)

### O que existe

- **Usuário**: `acesso.Usuario` é o `AUTH_USER_MODEL`. Por enquanto é igual ao usuário padrão do
  Django. Foi criado antes da primeira migração para permitir campos futuros vindos da autenticação
  institucional sem precisar trocar o modelo. Outros apps referenciam o usuário com
  `settings.AUTH_USER_MODEL`, nunca importando o modelo.
- **Papéis**: são `Group` do Django, um por ator do diagrama de casos de uso. Uma pessoa pode ter
  vários papéis (ex.: Técnico e Configurador), e as permissões se somam. A SEGTES é ator externo e não
  tem papel. Não há perfil genérico de administrador.
- **Operações protegidas**: são `Permission` do Django do catálogo `apps.acesso.models.Operacao`
  (modelo sem tabela, só declara as permissões). A operação em si é implementada pelo componente dono;
  o Controle de Acesso define quem pode executá-la. Papéis e permissões (migração
  `0004_permissoes_dos_papeis`):

  | Papel | Permissão (`acesso.<codename>`) | Caso de uso | Componente dono |
  |---|---|---|---|
  | Técnico | `registrar_resultado` | UC01 | `coleta` |
  | Configurador | `cadastrar_indicador`, `configurar_regra_calculo` | UC02 | `normativa` |
  | | `cadastrar_unidade`, `cadastrar_avaliado` (inclui o vínculo com a unidade) | — | `cadastro` |
  | CAM/SECOGE | `homologar_resultado` (conferir, homologar ou devolver) | UC03 | `apuracao` |
  | | `encerrar_ciclo` | — | `apuracao` |
  | | `publicar_resultado` | UC04 | `publicacao` |
  | | `julgar_recurso` | UC05 | `recurso` |
  | | `enviar_resultado_folha` | UC06 | `pagamento` |
  | Avaliado | `consultar_propria_pontuacao` | UC07 | `publicacao` |
  | | `apresentar_recurso` | UC08 | `recurso` |

  Nenhum papel tem permissão para alterar pontuação: ela só é calculada pela apuração.
- **Interface pública** (`apps/acesso/interface.py`):
  - `ExigePermissao`: permission class do DRF. A view declara `permissoes_exigidas`. Sem login a
    resposta é "não autenticado"; logado sem a permissão, 403. Uma view que esquece de declarar as
    permissões gera erro em vez de liberar o acesso.
  - `usuario_tem_permissao(usuario, "app.codename")`: a mesma verificação, para uso fora das views.
- **Padrão da API** (`settings.REST_FRAMEWORK`): toda view exige usuário autenticado
  (`IsAuthenticated`).

Exemplo em outro componente:

```python
# apps/pagamento/views.py
from apps.acesso.interface import ExigePermissao

class EnviarParaFolha(APIView):
    permission_classes = [ExigePermissao]
    permissoes_exigidas = ("acesso.enviar_resultado_folha",)
```

A verificação acontece sempre no servidor. Uma operação nova entra no catálogo por uma migração do
`acesso`, combinada com a dupla do Controle de Acesso.

### Decisões técnicas

- Usar o sistema nativo do Django (usuários, grupos, permissões) em vez de tabelas próprias: atende a
  vários papéis por pessoa e a papéis cadastráveis sem mudar código.
- O código verifica **permissões**, nunca nomes de papéis.
- O catálogo de operações fica no `acesso` (e não no `Meta.permissions` de cada componente) para
  que as permissões possam ser atribuídas aos papéis já agora, sem o `acesso` depender das migrações
  dos componentes de negócio.
- O superusuário do Django passa por todas as permissões. Ele serve só para administração técnica
  (Django Admin), não é um papel do sistema.
- Autenticação da API: provisoriamente, só a sessão do Django (a mesma do admin). A autenticação HTTP
  Basic foi retirada.

### Pendências (dependem de decisão da equipe)

- A história de usuário (ID-01) e seus critérios de aceitação não foram localizados nos documentos.
- O protocolo da autenticação institucional (OIDC ou SAML) e o mecanismo da API (sessão, token).
  Segundo a Elicitação de Requisitos, o sistema não terá fluxo próprio de login, por isso não há
  telas de login, logout ou redefinição de senha.
- Quem cadastra usuários e atribui papéis: os requisitos não definem. Hoje só o superusuário, pelo
  Django Admin.
- Escopo dos dados: o Avaliado só pode consultar a **própria** pontuação, e o Técnico registra só os
  indicadores **sob sua responsabilidade**. A permissão diz que a operação é permitida; quais registros
  cada pessoa alcança depende do vínculo entre usuário e `Avaliado`/`Unidade` (componente `cadastro`)
  e de regras de escopo ainda não definidas. Não implementado.
- Quem mais pode consultar pontuações (ex.: a CAM/SECOGE para homologar, gestores): não definido, por
  isso não há permissão de consulta geral.
- Ordem do fluxo (homologar → publicar → enviar à folha) e o deferimento de recurso pedir recálculo
  à apuração sem alterar a pontuação: são regras de estado dos componentes `apuracao`, `publicacao`,
  `recurso` e `pagamento`. O Controle de Acesso só garante quem pode executar cada etapa.
- Registro de login e de alterações de permissão na auditoria (componente `auditoria`). Hoje as
  alterações feitas pelo Django Admin ficam no histórico do próprio Admin.

## Componente Cadastro de Avaliados e Unidades (`apps/cadastro`)

O que o plano de desenvolvimento pede e onde está:

| Plano | Implementação |
|---|---|
| Define classes Avaliado e Unidade | `apps/cadastro/models.py` (+ Distrito). Campos iguais aos tipos `Usuario`, `Unidade` e `Distrito` do front |
| Cadastra avaliados e unidades por JSON/https | `POST /api/cadastro/importar/` e `python manage.py importar_cadastro arquivo.json` (tudo ou nada) |
| Exibe vínculo unidade-pessoa para apuração | `GET /api/vinculos/?unidadeId=&distritoId=` e `apps.cadastro.interface.vinculos_unidade_pessoa()` |
| Controla o que cada usuário visualiza | `apps/cadastro/escopo.py`: a API só devolve o escopo de quem pede; outros componentes usam `apps.cadastro.interface.escopo_do_request()` (ver [Escopo de visualização](#escopo-de-visualização)) |
| É registrado em auditoria | toda criação/alteração chama `apps.auditoria.interface.registrar()` ("Unidade cadastrada", "Vínculo alterado", "Login vinculado"...) |

Regras (as mesmas do `frontend/src/utils/escopo.ts`):
- **Gestor de Unidade** precisa de unidade; o distrito é o da unidade.
- **Coordenador Distrital** é vinculado a um distrito, sem unidade.
- **SEAB/CAM** e **Configurador** têm visão municipal: sem unidade nem distrito.
- Ninguém é apagado: só **inativado**. Unidade com pessoas ativas não pode ser inativada.
- Ids no padrão do protótipo (`d1`, `u5`, `us10`) para casar com os registros que ainda estão no mock.

O campo `perfil` do Avaliado é o **vínculo** da pessoa (usado no escopo territorial e no cálculo da
gratificação). Ele não dá permissão nenhuma: permissões vêm dos papéis do Controle de Acesso.

### Escopo de visualização

O campo `usuario` (rótulo "login" no Admin) liga o `Avaliado` ao `Usuario` do Controle de Acesso.
Um login só pode estar ligado a uma pessoa. Hoje quem faz a ligação é o superusuário, pelo Django
Admin. A ligação e a remoção ficam na auditoria como "Login vinculado" e "Login desvinculado".

O escopo de quem faz a requisição é calculado assim:

| Quem pede | Vê |
|---|---|
| Tem `acesso.cadastrar_unidade` ou `acesso.cadastrar_avaliado` (Configurador, superusuário) | o município |
| Login ligado a uma pessoa **ativa** SEAB/CAM ou Configurador | o município |
| Login ligado a um Gestor de Unidade ativo | a unidade dele (e o distrito dela) |
| Login ligado a um Coordenador Distrital ativo | o distrito dele |
| Login sem pessoa ligada, ou ligado a pessoa inativa | nada |
| Modo demonstração (`X-Perfil`) | o escopo do 1º Avaliado ativo do perfil, a mesma pessoa que o front usa |

Na API, um registro fora do escopo responde **404**, como se não existisse. Os filtros da query não
ampliam o escopo.

Para outros componentes, como a publicação filtrando resultados:

```python
from apps.cadastro.interface import escopo_do_request

escopo = escopo_do_request(request)    # request do Django ou do DRF
resultados.filter(unidade_id__in=escopo.unidade_ids())
escopo.alcanca_unidade("u3")           # True/False
```

`vinculos_unidade_pessoa()` sem o argumento `escopo` continua devolvendo o município inteiro, para
uso interno (ex.: a apuração).

### API

Leitura: usuário autenticado, recortada pelo [escopo](#escopo-de-visualização). Escrita:
`acesso.cadastrar_unidade` (unidades) e `acesso.cadastrar_avaliado` (pessoas); a importação exige as
duas.

| Método | Rota | |
|---|---|---|
| GET | `/api/distritos/` | |
| GET / POST | `/api/unidades/` | filtros `distritoId`, `tipo`, `status` |
| GET / PATCH | `/api/unidades/{id}/` | sem DELETE |
| POST | `/api/unidades/{id}/inativar/` · `/reativar/` | |
| GET | `/api/unidades/{id}/vinculos/` | avaliados da unidade (404 se a unidade não existe ou está fora do escopo) |
| GET / POST | `/api/usuarios/` | filtros `perfilId`, `status`, `distritoId`, `unidadeId` |
| GET / PATCH | `/api/usuarios/{id}/` | |
| POST | `/api/usuarios/{id}/inativar/` · `/reativar/` | |
| GET | `/api/vinculos/` | vínculo unidade-pessoa dos avaliados ativos (gestores e coordenadores) |
| POST | `/api/cadastro/importar/` | `{"distritos": [], "unidades": [], "usuarios": []}` |
| GET | `/api/auditoria/?componente=cadastro` | formato `AuditoriaEntrada` do front |

### Premissas a validar com a CAM
- Lista de tipos de unidade (hoje: USF, UBT, UPA, Policlínica, CAPS, Outro).
- Fonte oficial para a carga real das unidades e avaliados.
- Quem liga o login à pessoa no uso real (hoje: superusuário pelo Admin), e se a carga JSON deve
  trazer essa ligação.
- Escopo do Técnico, que não é um perfil do cadastro.
- Vínculo com vigência: hoje só existe o vínculo atual. O histórico por competência fica só na
  auditoria.

## Componente Registro de Auditoria (`apps/auditoria`)

Base mínima: modelo `RegistroAuditoria` (campos iguais a `AuditoriaEntrada` do front), a função
`registrar()` exposta em `apps/auditoria/interface.py` e a listagem `GET /api/auditoria/`. Registros não
são editados nem apagados. Pendente: permissão própria para consultar a auditoria (hoje basta estar
autenticado).


## Componente Normativa e Indicadores (`apps/normativa`)

O que apresentar ao time:

- Este componente cadastra a **normativa** (versão da portaria, ex.: CAM 1.2), a **competência**
  (o mês e a versão que vale nele), o **indicador** (e subindicador) e a **regra de cálculo**
  (peso da portaria, peso excepcional, meta, cargo e tipo de unidade).
- Não calcula pontuação: isso continua na apuração. Não grava o valor coletado: isso continua na
  coleta. Não encerra o ciclo: a permissão `encerrar_ciclo` segue na apuração. A competência só
  impede que uma portaria nova reescreva um mês já amarrado a uma versão.
- Quem cadastra é o papel **Configurador**, com as permissões que o Controle de Acesso já tinha:
  `acesso.cadastrar_indicador` (normativa, competência e indicador) e
  `acesso.configurar_regra_calculo` (peso e meta). A importação em massa exige as duas.
- Apuração e coleta **não são importadas** por este app. Elas leem
  `apps.normativa.interface`:
  - `regras_para_apuracao(ano, mes, cargo, tipo_unidade)` — peso vigente, meta e o texto de como
    calcular. O peso vigente é o excepcional, quando ele existe (inclusive zero); senão, o da portaria.
  - `indicadores_para_coleta(ano, mes, cargo, tipo_unidade)` — o que a unidade preenche, com pai e
    filhos.
  - `soma_pesos_de_primeiro_nivel(regras)` — conferência. O peso do subindicador não entra nessa
    soma, porque ele só compõe a nota do pai.
- Cada gravação chama `apps.auditoria.interface.registrar`. O rastro fica em
  `auditoria.RegistroAuditoria` (consulta em `interface.consultar` e no Django Admin, sem edição).
  Foi o mínimo para a normativa conseguir enviar o que cadastrou: o app de auditoria ainda não tinha
  modelo. Quem for fazer a tela de auditoria mantém `registrar` e `consultar`.
- HTTP (usuário autenticado; escrita só com a permissão acima):

  | Método | Rota | Uso |
  |---|---|---|
  | POST/GET | `/api/normativa/normativas/` | versão da portaria |
  | POST/GET | `/api/normativa/competencias/` | mês → normativa |
  | POST/GET | `/api/normativa/indicadores/` | catálogo |
  | PUT | `/api/normativa/indicadores/<id>/` | atualizar indicador |
  | POST | `/api/normativa/indicadores/importar/` | CSV em massa (`arquivo` + `normativa`) |
  | POST/GET | `/api/normativa/regras/` | peso e meta |
  | GET | `/api/normativa/apuracao/regras/?ano=&mes=&cargo=&tipo_unidade=` | leitura da apuração |
  | GET | `/api/normativa/coleta/indicadores/?ano=&mes=&cargo=&tipo_unidade=` | leitura da coleta |

- O modelo de CSV é `apps/normativa/exemplo_indicadores.csv` (separador `;`, UTF-8). Os percentuais
  20/20/20/40 do coordenador de US na USF repetem a leitura do resultado geral da planilha
  anonimizada. O peso excepcional do SnB2 nesse arquivo é só para mostrar que ele substitui o da
  portaria. A planilha inteira não foi importada: o PDF não preserva a coluna de cada unidade.
  Confirme na planilha antes de tratar número como oficial.
- O Diário Oficial nº 131, de 21/09/2024, não traz a portaria dos pesos desta gratificação por
  desempenho. O que ele cita de gratificação é outra (função de supervisor do PSA). Cargos e
  indicadores usados no modelo vêm da planilha anonimizada (CAM 1.2 / CAM 2.0, atualizada em
  10/02/2025): coordenador de US, GG, SnA, SnB1, SnB2; unidades USF, UBT, CAPS, CECON, UCIS, MAC.