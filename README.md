# TechStore — E-commerce Inteligente

API REST de e-commerce desenvolvida em Python, FastAPI e PostgreSQL, com foco em organização de código, integridade dos dados, regras de negócio, autenticação, autorização e testes automatizados. O projeto é a base de uma futura plataforma de comércio eletrônico com recursos de inteligência artificial e integrações em nuvem.

> **Situação em 07/11/2026:** backend local funcional para produtos, clientes e pedidos; autenticação JWT e autorização por perfis implementadas; **88 testes automatizados aprovados**, sem falhas. Frontend, IA e infraestrutura em nuvem permanecem planejados, não implementados nesta versão.

## 1. Visão geral

A TechStore simula uma loja virtual de produtos de tecnologia. O backend permite cadastrar e consultar produtos e clientes, registrar pedidos com vários itens, controlar o estoque e acompanhar pedidos até a entrega ou cancelamento.

Objetivos técnicos:

- Construir uma API REST organizada em camadas.
- Persistir dados relacionais no PostgreSQL.
- Validar entradas com Pydantic e aplicar regras de negócio nos serviços.
- Preservar histórico por exclusão lógica.
- Garantir consistência entre pedidos, itens e estoque por transações.
- Autenticar clientes e restringir operações conforme identidade e perfil.
- Automatizar testes em banco separado do ambiente de desenvolvimento.
- Preparar a base para frontend, observabilidade, automação e IA.

## 2. Tecnologias utilizadas

| Tecnologia | Utilização |
| --- | --- |
| Python 3.13 | Linguagem do backend |
| FastAPI | API HTTP, dependências de segurança e documentação interativa |
| Pydantic | Schemas e validação de entradas e saídas |
| SQLAlchemy | Conexões e SQL parametrizado |
| psycopg | Driver PostgreSQL |
| PostgreSQL 17 | Persistência relacional |
| python-dotenv | Configurações locais |
| Uvicorn | Servidor ASGI de desenvolvimento |
| JWT e hash de senhas | Autenticação e proteção de credenciais |
| pytest, FastAPI TestClient e httpx | Testes automatizados |
| VS Code, PowerShell e pgAdmin | Desenvolvimento e administração local |

As versões exatas das bibliotecas e os respectivos pacotes de segurança devem ser consultados nas dependências efetivamente instaladas. A consolidação de um arquivo de dependências reproduzível continua sendo uma tarefa de manutenção.

## 3. Organização do projeto

Estrutura resumida, considerando os arquivos identificados durante o desenvolvimento:

```text
ai-support-hub/
├── app/
│   ├── main.py
│   ├── core/
│   │   ├── database.py
│   │   ├── security.py
│   │   └── permissions.py
│   ├── routers/
│   │   ├── auth.py
│   │   ├── clientes.py
│   │   ├── produtos.py
│   │   └── pedidos.py
│   ├── schemas/
│   │   ├── auth.py
│   │   ├── cliente.py
│   │   ├── produto.py
│   │   └── pedido.py
│   └── services/
│       ├── auth_service.py
│       ├── cliente_service.py
│       ├── produto_service.py
│       └── pedido_service.py
├── migrations/
│   └── 001_adicionar_perfil_clientes.sql
├── tests/
│   ├── conftest.py
│   ├── test_auth.py
│   ├── test_autorizacao.py
│   ├── test_banco.py
│   ├── test_clientes.py
│   ├── test_pedidos.py
│   ├── test_produtos.py
│   ├── test_regras_negocio.py
│   ├── test_sistema.py
│   └── test_validacao_produtos.py
├── .env                 # Local; não versionar
├── .gitignore
└── README.md
```

A pasta de trabalho permanece denominada `ai-support-hub`; **TechStore** é o nome da aplicação. A árvore é ilustrativa e não pretende listar todos os arquivos locais.

### Responsabilidades

- `app/main.py`: inicialização da API e registro de rotas.
- `app/routers/`: endpoints, parâmetros, dependências e respostas HTTP.
- `app/schemas/`: validações de entrada e saída com Pydantic.
- `app/services/`: acesso aos dados e regras de negócio.
- `app/core/database.py`: conexão PostgreSQL.
- `app/core/security.py`: hash de senha e operações com token.
- `app/core/permissions.py`: autorização por perfil e propriedade da conta.
- `migrations/`: alterações incrementais de esquema.
- `tests/`: testes HTTP, de persistência, regras e autorização.

### Fluxo de uma requisição

```text
Cliente HTTP / Swagger
         |
         v
       FastAPI
         |
         v
Router + autenticação/autorização (quando exigidas)
         |
         v
   Schema Pydantic
         |
         v
       Service
         |
         v
SQLAlchemy + psycopg
         |
         v
     PostgreSQL
```

Os serviços utilizam SQL parametrizado com `sqlalchemy.text()`.

## 4. Configuração do ambiente local

### Pré-requisitos

- Python 3.13 ou versão compatível com as dependências.
- PostgreSQL 17 acessível.
- VS Code ou outro editor e terminal PowerShell.
- Bancos `techstore_db` e `techstore_test_db` criados e estruturados.

### 4.1. Abrir o projeto

```powershell
cd "C:\Users\<usuario>\Documents\ai-support-hub"
```

### 4.2. Criar e ativar o ambiente virtual

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 4.3. Instalar dependências

Se houver um `requirements.txt` revisado:

```powershell
python -m pip install -r requirements.txt
```

Além das dependências de API e banco, a autenticação exige as bibliotecas efetivamente utilizadas por `app/core/security.py`. Não considere suficiente uma lista genérica de pacotes sem conferir esse arquivo. É necessário consolidar e versionar dependências verificadas para reprodução integral.

### 4.4. Configurar variáveis de ambiente

Exemplo das variáveis de conexão do `.env`:

```dotenv
DB_HOST=localhost
DB_PORT=5432
DB_NAME=techstore_db
DB_USER=seu_usuario_postgresql
DB_PASSWORD=sua_senha_postgresql
```

A configuração de segurança JWT deve seguir os nomes de variáveis exigidos pelo código de `app/core/security.py`, com segredo forte mantido fora do Git. Nunca publique o `.env`, senhas ou tokens reais.

### 4.5. Iniciar a API

```powershell
python -m uvicorn app.main:app --reload
```

| Endereço | Finalidade |
| --- | --- |
| `http://127.0.0.1:8000/` | Página inicial da API |
| `http://127.0.0.1:8000/saude` | Saúde básica do serviço HTTP |
| `http://127.0.0.1:8000/docs` | Swagger UI |
| `http://127.0.0.1:8000/openapi.json` | OpenAPI |

`--reload` é indicado para desenvolvimento, não para produção. A rota `/saude` não comprova a disponibilidade de todas as dependências externas.

## 5. Bancos de dados

### 5.1. Ambientes separados

| Banco | Utilização |
| --- | --- |
| `techstore_db` | Desenvolvimento da aplicação |
| `techstore_test_db` | Testes automatizados isolados |

As fixtures verificam o nome do banco antes de limpar as tabelas de teste. **O banco `techstore_test_db` tem seus registros apagados pelos testes e não deve conter dados importantes.**

### 5.2. Entidades principais

**`clientes`:** `id`, `nome`, `email`, `telefone`, `cpf`, `senha_hash`, `perfil`, `ativo`, `criado_em`, `atualizado_em`. O campo `perfil` aceita `cliente` e `admin`; novos cadastros recebem `cliente` por padrão. Senhas são armazenadas como hash, não em texto puro.

**`produtos`:** `id`, `nome`, `categoria`, `preco`, `estoque`, `ativo`, `criado_em`.

**`pedidos`:** `id`, `cliente_id`, `data_pedido`, `status`, `valor_total`.

**`itens_pedido`:** `id`, `pedido_id`, `produto_id`, `quantidade`, `preco_unitario`, `subtotal`.

### 5.3. Relacionamentos

```text
clientes (1) ---- (N) pedidos (1) ---- (N) itens_pedido (N) ---- (1) produtos
```

Um cliente pode realizar vários pedidos; cada pedido possui itens, que referenciam produtos.

### 5.4. Restrições de integridade

- E-mail único e CPF único quando informado.
- Preço maior que zero e estoque não negativo.
- Quantidade e preço unitário dos itens maiores que zero.
- Total do pedido não negativo.
- Chaves estrangeiras entre clientes, pedidos, itens e produtos.
- Sem repetição do mesmo produto no mesmo pedido.
- Status de pedido limitado aos valores previstos.
- Perfil de cliente limitado a `cliente` e `admin`.

### 5.5. Migração de perfis

Arquivo versionável: `migrations/001_adicionar_perfil_clientes.sql`.

A migração acrescenta a coluna `perfil`, preenche valores nulos com `cliente`, define o padrão e a obrigatoriedade e cria uma restrição `CHECK` para os valores permitidos. A alteração já foi aplicada localmente em `techstore_db` e `techstore_test_db` e foi registrada no arquivo SQL em 07/11/2026.

**Não execute a migração sem verificar o ambiente de destino e realizar backup.** O arquivo é uma migração incremental: pressupõe que a tabela `clientes` já exista. O script de criação integral das quatro tabelas ainda precisa ser consolidado para permitir uma instalação do zero.

## 6. Endpoints da API

### 6.1. Sistema

| Método | Rota | Finalidade |
| --- | --- | --- |
| GET | `/` | Página inicial |
| GET | `/saude` | Verificação básica do serviço |

### 6.2. Produtos

| Método | Rota | Finalidade | Sucesso |
| --- | --- | --- | --- |
| GET | `/produtos` | Listar produtos ativos | 200 |
| GET | `/produtos/{produto_id}` | Consultar produto | 200 |
| POST | `/produtos` | Cadastrar produto | 201 |
| PUT | `/produtos/{produto_id}` | Atualizar produto | 200 |
| DELETE | `/produtos/{produto_id}` | Desativar produto | 200 |

Exemplo de cadastro:

```json
{
  "nome": "Monitor LG UltraWide",
  "categoria": "Monitores",
  "preco": 1299.90,
  "estoque": 15
}
```

`ProdutoCadastro` exige nome de 3 a 100 caracteres, categoria de 3 a 50 caracteres, preço positivo com até duas casas decimais e estoque inteiro não negativo. Entradas incompatíveis com o schema retornam 422. A exclusão é lógica (`ativo = FALSE`).

### 6.3. Clientes e autorização

| Método | Rota | Permissão | Sucesso |
| --- | --- | --- | --- |
| POST | `/clientes` | Público; perfil inicial `cliente` | 201 |
| GET | `/clientes` | Somente `admin` | 200 |
| GET | `/clientes/{cliente_id}` | Titular ou `admin` | 200 |
| PUT | `/clientes/{cliente_id}` | Titular ou `admin` | 200 |
| DELETE | `/clientes/{cliente_id}` | Titular ou `admin` | 200 |

Exemplo de cadastro:

```json
{
  "nome": "Mariana Oliveira",
  "email": "mariana.oliveira@exemplo.com",
  "telefone": "11987654321",
  "cpf": "12345678901",
  "senha": "ExemploDeSenhaForte123"
}
```

O cadastro aceita nome de 3 a 100 caracteres, e-mail válido, telefone opcional até 20 caracteres, CPF opcional com 11 dígitos numéricos e senha opcional de 8 a 128 caracteres. O CPF é validado quanto ao formato, não quanto aos dígitos verificadores. A ausência de senha impede login até que uma senha seja configurada por mecanismo autorizado.

O cadastro público não permite atribuir privilégios administrativos. Tentativas de incluir `perfil: "admin"` não concedem esse perfil. Duplicidades de e-mail e CPF retornam 409.

A exclusão é lógica. Depois da desativação, o token do próprio cliente deixa de autorizar acesso à conta e retorna 401. Um administrador autenticado que consultar o registro inativo recebe 404.

### 6.4. Autenticação

| Método | Rota | Finalidade | Sucesso |
| --- | --- | --- | --- |
| POST | `/auth/login` | Autenticar por e-mail e senha; emitir token JWT | 200 |
| GET | `/auth/me` | Consultar dados da conta autenticada | 200 |

Exemplo de login:

```json
{
  "email": "mariana.oliveira@exemplo.com",
  "senha": "ExemploDeSenhaForte123"
}
```

Nas rotas protegidas, envie o token recebido no cabeçalho HTTP `Authorization: Bearer <token>`, ou utilize o botão **Authorize** do Swagger. Tokens ausentes, inválidos ou expirados não concedem acesso.

O token identifica o cliente, enquanto o perfil e o estado ativo são consultados no PostgreSQL durante a autenticação das requisições protegidas. Isso permite revogar o acesso administrativo de uma conta sem esperar o vencimento do JWT.

### 6.5. Pedidos

| Método | Rota | Finalidade |
| --- | --- | --- |
| POST | `/pedidos` | Criar pedido com itens |
| GET | `/pedidos` | Listar pedidos |
| GET | `/pedidos/{pedido_id}` | Consultar pedido e seus itens |
| PATCH | `/pedidos/{pedido_id}/status` | Alterar status |

Regras de negócio implementadas:

1. O cliente deve existir e estar ativo.
2. Os produtos devem existir e estar ativos.
3. A quantidade solicitada não pode ultrapassar o estoque.
4. Um produto não pode se repetir no mesmo pedido.
5. A criação do pedido registra os itens e baixa o estoque em transação.
6. O processamento de estoque utiliza `SELECT ... FOR UPDATE`.
7. O total é calculado com `Decimal`.
8. O cancelamento devolve as quantidades ao estoque.
9. Transições incompatíveis com o estado atual são rejeitadas.

Fluxo permitido:

```text
pendente ---> pago ---> enviado ---> entregue
   |           |
   v           v
cancelado   cancelado
```

`entregue` e `cancelado` são estados finais. Um pedido cancelado não pode ser reativado; cancelar duas vezes não pode devolver estoque em duplicidade.

## 7. Códigos HTTP e tratamento de erros

| Código | Interpretação |
| --- | --- |
| 200 | Consulta ou operação concluída |
| 201 | Recurso criado |
| 401 | Ausência de autenticação válida ou conta inativa |
| 403 | Conta autenticada sem permissão para a operação |
| 404 | Recurso inexistente ou indisponível |
| 409 | Conflito de integridade ou regra de negócio |
| 422 | Dados incompatíveis com o schema |
| 500 | Erro interno ou de acesso ao banco |

Os serviços utilizam `HTTPException` e tratamento de exceções do SQLAlchemy. A padronização das respostas de erro poderá ser ampliada.

## 8. Testes automatizados

### 8.1. Estratégia

Os testes utilizam `pytest` e `TestClient`. Em `tests/conftest.py`:

- `test_engine` conecta ao banco `techstore_test_db` e verifica seu nome.
- `client` injeta o mecanismo do banco de testes nos serviços.
- `banco_limpo` executa `TRUNCATE ... RESTART IDENTITY CASCADE` antes e depois dos testes que utilizam a fixture.
- `cliente_autenticado` facilita a obtenção de tokens para testes HTTP.

**Atenção:** a limpeza apaga registros das tabelas `clientes`, `produtos`, `pedidos` e `itens_pedido` no banco de testes.

### 8.2. Resultado confirmado

Em **07/11/2026**, a execução integral de `python -m pytest -v` com Python 3.13.11 e pytest 9.1.1 apresentou:

```text
88 passed, 1 warning in 18.75s
```

| Arquivo | Casos aprovados | Cobertura principal |
| --- | ---: | --- |
| `test_auth.py` | 25 | Cadastro com senha, login, hash, tokens e conta inativa |
| `test_autorizacao.py` | 17 | Autorização de cliente e administrador; revogação de privilégios |
| `test_banco.py` | 2 | Banco de testes e tabelas |
| `test_clientes.py` | 5 | CRUD, consulta autenticada e exclusão lógica |
| `test_pedidos.py` | 6 | Pedidos, estoque e disponibilidade |
| `test_produtos.py` | 4 | CRUD de produtos |
| `test_regras_negocio.py` | 19 | Validações, integridade, cancelamento e status |
| `test_sistema.py` | 2 | Página inicial e saúde |
| `test_validacao_produtos.py` | 8 | Validações de cadastro |
| **Total** | **88** | **Todos aprovados** |

### 8.3. Executar os testes

```powershell
python -m pytest -v
```

Execute a suíte somente com `techstore_test_db` preparado para ser limpo.

### 8.4. Aviso de compatibilidade

A execução registrou um aviso `StarletteDeprecationWarning` relativo ao uso de `httpx` pelo `starlette.testclient`. O aviso não provocou falhas. A compatibilidade entre FastAPI, Starlette e cliente de testes deverá ser revisada ao fixar as versões das dependências.

## 9. Cuidados com integridade e segurança

### Já adotados

- SQL parametrizado e validação de entrada com Pydantic.
- Restrições de integridade e transações PostgreSQL.
- Exclusão lógica e regras de estoque e cancelamento.
- Senhas armazenadas com hash e autenticação JWT.
- Autorização por titularidade da conta e perfil administrativo.
- Consulta do perfil atualizado no banco para evitar privilégios antigos no token.
- Cadastro público sem concessão de perfil `admin`.
- Banco de testes isolado e credenciais locais fora do Git.

### Pontos a desenvolver antes de uso público

- Consolidação de dependências e gestão segura de segredos em implantação.
- Scripts completos de criação do esquema e procedimento formal de migração.
- Administração segura do ciclo de vida de contas e perfis, sem atualização manual do banco.
- Revisão de permissões para outras áreas da API, conforme os requisitos do produto.
- Paginação, filtros e políticas de exposição de dados pessoais.
- Logs estruturados, monitoramento, CORS e limitação de requisições.
- Testes adicionais de concorrência, segurança e falhas transacionais.
- Procedimentos de backup, implantação e recuperação.

**A aprovação dos testes não significa que a aplicação esteja pronta para produção.**

## 10. Histórico de evolução

### Backend e persistência

- Criação dos bancos de desenvolvimento e testes.
- Modelagem de clientes, produtos, pedidos e itens.
- Organização nas camadas `core`, `routers`, `schemas` e `services`.
- CRUD de produtos e clientes com exclusão lógica.
- Pedidos com cálculo de total, controle de estoque, transações e fluxo de status.
- Implementação de autenticação com senha e JWT.
- Implementação de autorização por titularidade e perfis `cliente` e `admin`.
- Registro da migração `001_adicionar_perfil_clientes.sql`.

### Testes e versionamento

- Etapas 97–118: criação da base de testes, chegando a 33 casos aprovados em 31/10/2026.
- Evolução posterior: testes de autenticação, segurança, regras de negócio e autorização.
- Em 07/11/2026: suíte completa com **88 testes aprovados**, nenhuma falha e um aviso de compatibilidade.
- Repositório GitHub: `https://github.com/LuizFernandoPeramo/techstore-ecommerce-inteligente`.

A migração e os ajustes de RBAC descritos nesta atualização estavam preparados localmente para revisão e commit; não se presume que já tenham sido publicados no GitHub.

## 11. Próximas etapas

### Curto prazo

1. Revisar `.gitignore` e conferir arquivos modificados e novos.
2. Versionar a migração de perfis e a documentação atualizada.
3. Consolidar `requirements.txt` e `.env.example` sem segredos.
4. Consolidar scripts de criação completa do banco para novos ambientes.
5. Criar commit e publicar a evolução validada no GitHub.

### Médio prazo

- Definir gestão administrativa de usuários e perfis por operações seguras.
- Revisar políticas de acesso às demais rotas.
- Melhorar logs, observabilidade, tratamento de erros e testes de segurança.
- Preparar implantação e documentação operacional.

### Evolução planejada — ainda não implementada

- **Frontend:** React e TypeScript.
- **IA:** Amazon Bedrock para recursos inteligentes e atendimento.
- **Eventos:** AWS Lambda, Amazon SQS e DLQ.
- **Estado e sessões:** possível uso de DynamoDB.
- **Automações:** n8n.
- **Observabilidade em nuvem:** Amazon CloudWatch.
- **Infraestrutura:** ambiente de execução e publicação apropriado.

Essas tecnologias são direções de evolução do portfólio, não integrações confirmadas nesta versão.

## 12. Estado atual do projeto

**Concluído e verificado:**

- API FastAPI executada localmente.
- Persistência PostgreSQL para produtos, clientes, pedidos e itens.
- Regras de estoque, transições de pedidos e exclusão lógica.
- Autenticação JWT e consulta da conta autenticada.
- Controle de acesso por perfil e propriedade da conta.
- Migração incremental de perfis registrada em SQL.
- Banco de testes separado.
- **88 testes automatizados aprovados em execução conjunta.**

**Próximo marco:** concluir a revisão dos arquivos, atualizar a documentação versionada e publicar as alterações validadas no GitHub, sem expor credenciais locais.

---

**TechStore — E-commerce Inteligente**  
Documentação atualizada em **7 de novembro de 2026**.
