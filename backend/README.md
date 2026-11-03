# Backend do SGGD (Django)

Monólito modular: cada componente é um app Django em `apps/`, com suas próprias tabelas no mesmo
banco PostgreSQL. Um componente só usa outro pelo módulo público `apps/<componente>/interface.py`
(verificado pelo import-linter).

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
| `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD` | sim | Banco e credenciais |
| `POSTGRES_HOST`, `POSTGRES_PORT` | não (padrão `localhost`, `5432`) | Servidor |

Criar o banco no PostgreSQL (exemplo, como administrador do servidor):

```sql
CREATE ROLE sggd LOGIN PASSWORD 'senha123' CREATEDB;  -- CREATEDB: para o banco de testes
CREATE DATABASE sggd OWNER sggd;
```

## Comandos

```bash
python manage.py migrate          # aplica as migrações
python manage.py createsuperuser  # primeiro usuário administrador
python manage.py runserver        # http://127.0.0.1:8000 (admin em /admin/)
python manage.py test             # testes
lint-imports                      # fronteiras entre componentes
```

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
