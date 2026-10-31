# TechStore — E-commerce Inteligente

API de e-commerce desenvolvida em Python, FastAPI e PostgreSQL, com foco em organização de código, integridade dos dados, regras de negócio e testes automatizados. O projeto também serve como base para a evolução de uma plataforma de comércio eletrônico com recursos de inteligência artificial e integrações em nuvem.

> **Situação em 31/10/2026:** backend local funcional para produtos, clientes e pedidos; suíte completa com 33 testes automatizados aprovados na Etapa 118. Os componentes de frontend, IA e infraestrutura em nuvem descritos no planejamento **ainda não fazem parte da implementação confirmada**.

## 1. Visão geral

A TechStore simula a operação de uma loja virtual de produtos de tecnologia. O backend permite cadastrar e consultar produtos e clientes, registrar pedidos com vários itens, controlar o estoque e acompanhar a evolução dos pedidos até a entrega ou o cancelamento.

Os objetivos técnicos são:

- Construir uma API REST organizada em camadas.
- Persistir dados relacionais no PostgreSQL.
- Validar entradas com Pydantic e aplicar regras de negócio no serviço.
- Preservar histórico por meio de exclusão lógica.
- Garantir consistência entre pedidos, itens e estoque usando transações.
- Automatizar testes sem modificar os dados do ambiente principal.
- Preparar uma base sólida para frontend, observabilidade, automação e IA.

## 2. Tecnologias utilizadas

| Tecnologia | Utilização |
| --- | --- |
| Python 3.13 | Linguagem principal do backend |
| FastAPI | API HTTP e documentação interativa |
| Pydantic | Schemas e validação de entradas e saídas |
| SQLAlchemy | Conexões e execução de SQL parametrizado |
| psycopg | Driver de conexão com PostgreSQL |
| PostgreSQL 17 | Banco de dados relacional |
| python-dotenv | Carregamento de configurações locais |
| Uvicorn | Servidor ASGI de desenvolvimento |
| pytest | Testes automatizados |
| FastAPI TestClient | Requisições HTTP durante os testes |
| httpx | Dependência do cliente de testes utilizado atualmente |
| VS Code e PowerShell | Ambiente de desenvolvimento no Windows |
| pgAdmin | Administração e inspeção do PostgreSQL |

**Observação:** as versões exatas de todas as bibliotecas não foram consolidadas nesta documentação. Recomenda-se gerar e versionar um arquivo de dependências revisado antes da publicação.

## 3. Organização do projeto

Estrutura identificada durante o desenvolvimento:

```text
ai-support-hub/
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── core/
│   │   ├── __init__.py
│   │   └── database.py
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── produtos.py
│   │   ├── clientes.py
│   │   └── pedidos.py
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── produto.py
│   │   ├── cliente.py
│   │   └── pedido.py
│   └── services/
│       ├── __init__.py
│       ├── produto_service.py
│       ├── cliente_service.py
│       └── pedido_service.py
├── tests/
│   ├── conftest.py
│   ├── test_sistema.py
│   ├── test_banco.py
│   ├── test_produtos.py
│   ├── test_validacao_produtos.py
│   ├── test_clientes.py
│   └── test_pedidos.py
├── backup_refatoracao/        # Backup local criado durante a reorganização
├── .env                       # Configurações locais; não publicar
├── .gitignore
├── .venv/                     # Ambiente virtual local
└── README.md
```

A pasta local continua denominada `ai-support-hub`; **TechStore** é o nome da aplicação. A árvore representa os arquivos e pastas conhecidos até esta etapa, não necessariamente um inventário exaustivo.

### Responsabilidades das camadas

- **`app/main.py`:** instancia o FastAPI, registra os routers e disponibiliza as rotas de sistema.
- **`app/routers/`:** define caminhos, métodos HTTP, schemas e encaminha chamadas para os serviços.
- **`app/schemas/`:** descreve dados esperados e aplica validações com Pydantic.
- **`app/services/`:** implementa consultas SQL, transações e regras de negócio.
- **`app/core/database.py`:** configura o mecanismo de conexão com PostgreSQL.
- **`tests/`:** valida comportamento HTTP, persistência, regras e isolamento dos dados de teste.

### Fluxo de uma requisição

```text
Cliente HTTP / Swagger
        |
        v
     FastAPI
        |
        v
      Router
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

Os schemas validam os dados recebidos antes da execução da operação. Os serviços utilizam SQL parametrizado com `sqlalchemy.text()`.

## 4. Configuração do ambiente local

### Pré-requisitos

- Python 3.13 ou versão compatível com as dependências utilizadas.
- PostgreSQL 17 instalado e acessível.
- VS Code ou outro editor de código.
- Terminal PowerShell no Windows.
- Bancos `techstore_db` e `techstore_test_db` criados e estruturados.

### 4.1. Abrir o projeto

No PowerShell, entre na pasta do projeto. Exemplo do ambiente utilizado:

```powershell
cd "C:\Users\<usuario>\Documents\ai-support-hub"
```

### 4.2. Criar e ativar o ambiente virtual

Se ainda não existir:

```powershell
python -m venv .venv
```

Ativação no PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

### 4.3. Instalar dependências

Se o projeto possuir um `requirements.txt` revisado:

```powershell
python -m pip install -r requirements.txt
```

Caso ainda não exista esse arquivo, as dependências principais identificadas são:

```powershell
python -m pip install fastapi uvicorn sqlalchemy psycopg python-dotenv pydantic email-validator pytest httpx
```

A lista acima serve para preparar o ambiente de desenvolvimento; **não substitui um arquivo de dependências com versões verificadas**.

### 4.4. Configurar variáveis de ambiente

Criar um arquivo `.env` na raiz do projeto com as chaves:

```dotenv
DB_HOST=localhost
DB_PORT=5432
DB_NAME=techstore_db
DB_USER=seu_usuario_postgresql
DB_PASSWORD=sua_senha_postgresql
```

Substitua os valores de exemplo pelos da instalação local. Não publique credenciais reais. O arquivo `.env` deve permanecer fora do controle de versão.

O arquivo `app/core/database.py` utiliza essas variáveis para criar o `engine` do SQLAlchemy com o driver `postgresql+psycopg` e verificação de conexões (`pool_pre_ping=True`).

### 4.5. Iniciar a API

Na raiz do projeto, com o ambiente virtual ativado:

```powershell
python -m uvicorn app.main:app --reload
```

Endereços locais:

| Endereço | Finalidade |
| --- | --- |
| `http://127.0.0.1:8000/` | Mensagem inicial e estado da API |
| `http://127.0.0.1:8000/saude` | Verificação simples de saúde |
| `http://127.0.0.1:8000/docs` | Documentação Swagger UI |
| `http://127.0.0.1:8000/openapi.json` | Especificação OpenAPI |

A opção `--reload` é adequada ao desenvolvimento local, não à execução de produção.

## 5. Bancos de dados

### 5.1. Ambientes separados

| Banco | Utilização |
| --- | --- |
| `techstore_db` | Dados principais de desenvolvimento da aplicação |
| `techstore_test_db` | Execução isolada dos testes automatizados |

Os testes foram configurados para conectar explicitamente ao banco `techstore_test_db`, independentemente do valor de `DB_NAME` no `.env`.

### 5.2. Entidades principais

**`clientes`**

- `id`: identificador único.
- `nome`: nome do cliente.
- `email`: e-mail único.
- `telefone`: telefone opcional.
- `cpf`: CPF opcional, com restrição de unicidade.
- `senha_hash`: campo reservado na estrutura de dados; não há autenticação confirmada nesta etapa.
- `ativo`: indicador de exclusão lógica.
- `criado_em` e `atualizado_em`: informações temporais.

**`produtos`**

- `id`: identificador único.
- `nome`: descrição do produto.
- `categoria`: categoria comercial.
- `preco`: valor monetário.
- `estoque`: quantidade disponível.
- `ativo`: indicador de disponibilidade cadastral.
- `criado_em`: data de criação.

**`pedidos`**

- `id`: identificador único.
- `cliente_id`: referência ao cliente.
- `data_pedido`: data do pedido.
- `status`: etapa atual do pedido.
- `valor_total`: soma dos valores dos itens.

**`itens_pedido`**

- `id`: identificador único.
- `pedido_id`: referência ao pedido.
- `produto_id`: referência ao produto.
- `quantidade`: unidades compradas.
- `preco_unitario`: preço registrado no momento da compra.
- `subtotal`: calculado a partir de quantidade × preço unitário.

### 5.3. Relacionamentos

```text
clientes (1) -------- (N) pedidos
                           |
                           | (1)
                           |
                           +-------- (N) itens_pedido (N) -------- (1) produtos
```

Um cliente pode ter vários pedidos; cada pedido contém itens; cada item referencia um produto.

### 5.4. Restrições de integridade

As regras já identificadas na estrutura incluem:

- E-mail único por cliente e CPF único quando informado.
- Preço de produto maior que zero.
- Estoque de produto maior ou igual a zero.
- Quantidade e preço unitário de item maiores que zero.
- Valor total do pedido não negativo.
- Chaves estrangeiras entre pedidos, clientes, itens e produtos.
- Combinação de pedido e produto sem duplicação na tabela de itens.
- Status do pedido restrito aos valores previstos pelo sistema.

O script de criação/migração do banco ainda precisa ser consolidado no repositório para que terceiros possam reproduzir o esquema do zero.

## 6. Endpoints da API

### 6.1. Sistema

| Método | Rota | Finalidade |
| --- | --- | --- |
| GET | `/` | Mensagem inicial e estado da API |
| GET | `/saude` | Verificação de saúde da aplicação |

A rota `/saude` verifica a disponibilidade do serviço HTTP; **não é um teste completo de conectividade com todos os componentes externos**.

### 6.2. Produtos

| Método | Rota | Finalidade | Sucesso esperado |
| --- | --- | --- | --- |
| GET | `/produtos` | Listar produtos ativos | 200 |
| GET | `/produtos/{produto_id}` | Consultar produto ativo | 200 |
| POST | `/produtos` | Cadastrar produto | 201 |
| PUT | `/produtos/{produto_id}` | Atualizar produto ativo | 200 |
| DELETE | `/produtos/{produto_id}` | Desativar produto | 200 |

**Exemplo de cadastro:**

```json
{
  "nome": "Monitor LG UltraWide",
  "categoria": "Monitores",
  "preco": 1299.90,
  "estoque": 15
}
```

**Validações de `ProdutoCadastro`:**

| Campo | Regra |
| --- | --- |
| `nome` | Obrigatório, de 3 a 100 caracteres |
| `categoria` | Obrigatório, de 3 a 50 caracteres |
| `preco` | Decimal maior que zero, até 10 dígitos e 2 casas decimais |
| `estoque` | Inteiro maior ou igual a zero |

Estoque igual a zero é aceito no cadastro. Uma entrada que viola o schema retorna HTTP **422**.

**Exclusão lógica:** o endpoint `DELETE` executa `UPDATE produtos SET ativo = FALSE`, preservando o registro. Produtos desativados não aparecem na listagem nem na consulta individual. Nova tentativa de desativação retorna **404**.

### 6.3. Clientes

| Método | Rota | Finalidade | Sucesso esperado |
| --- | --- | --- | --- |
| GET | `/clientes` | Listar clientes ativos | 200 |
| GET | `/clientes/{cliente_id}` | Consultar cliente ativo | 200 |
| POST | `/clientes` | Cadastrar cliente | 201 |
| PUT | `/clientes/{cliente_id}` | Atualizar cliente ativo | 200 |
| DELETE | `/clientes/{cliente_id}` | Desativar cliente | 200 |

**Exemplo de cadastro com dados fictícios:**

```json
{
  "nome": "Mariana Oliveira",
  "email": "mariana.oliveira@exemplo.com",
  "telefone": "11987654321",
  "cpf": "12345678901"
}
```

**Validações de `ClienteCadastro`:**

| Campo | Regra |
| --- | --- |
| `nome` | Obrigatório, de 3 a 100 caracteres |
| `email` | Obrigatório, formato de e-mail válido (`EmailStr`) |
| `telefone` | Opcional, até 20 caracteres |
| `cpf` | Opcional, exatamente 11 caracteres numéricos |

O schema verifica **somente o formato do CPF**, não seus dígitos verificadores. O banco impede duplicidade de e-mail e CPF; o serviço retorna **409** quando a inserção ou atualização viola essas restrições.

**Exclusão lógica:** o serviço marca `ativo = FALSE` e atualiza `atualizado_em`. Clientes desativados deixam de aparecer nas consultas públicas; a tentativa de desativá-los novamente retorna **404**.

### 6.4. Pedidos

As operações abaixo foram implementadas, verificadas manualmente e cobertas por testes automatizados na Etapa 118:

| Método | Rota | Finalidade |
| --- | --- | --- |
| POST | `/pedidos` | Criar pedido com itens |
| GET | `/pedidos` | Listar pedidos |
| GET | `/pedidos/{pedido_id}` | Consultar pedido e seus itens |
| PATCH | `/pedidos/{pedido_id}/status` | Alterar status do pedido |

**Regras de negócio identificadas:**

1. O cliente deve existir e estar ativo.
2. Os produtos devem existir e estar ativos.
3. A quantidade solicitada deve ser compatível com o estoque disponível.
4. O mesmo produto não deve aparecer repetido na solicitação de um único pedido.
5. A criação registra pedido e itens e reduz o estoque em uma transação.
6. O serviço utiliza bloqueio de linhas (`SELECT ... FOR UPDATE`) no processamento de estoque.
7. O valor total é calculado a partir dos itens, utilizando operações monetárias com `Decimal`.
8. O cancelamento devolve ao estoque as quantidades reservadas pelo pedido.
9. Operações incompatíveis com o estado atual são rejeitadas.

**Fluxo de status permitido:**

```text
pendente ──> pago ──> enviado ──> entregue
    |          |
    v          v
 cancelado  cancelado
```

- `pendente` pode avançar para `pago` ou `cancelado`.
- `pago` pode avançar para `enviado` ou `cancelado`.
- `enviado` pode avançar para `entregue`.
- `entregue` e `cancelado` são estados finais.

O cancelamento de um pedido já cancelado é rejeitado, evitando devolução duplicada ao estoque. Os testes automatizados cobrem cadastro, consulta, listagem, estoque insuficiente, clientes e produtos indisponíveis, cancelamento, devolução de estoque e transições válidas e inválidas de status.

## 7. Códigos HTTP e tratamento de erros

| Código | Interpretação no projeto |
| --- | --- |
| 200 | Consulta, atualização ou desativação concluída |
| 201 | Recurso criado com sucesso |
| 404 | Recurso não encontrado ou indisponível para a operação |
| 409 | Conflito de integridade ou regra de negócio, conforme a operação |
| 422 | Dados de entrada incompatíveis com o schema |
| 500 | Erro de acesso ao banco ou operação não tratada especificamente |

Os serviços de produtos e clientes utilizam `HTTPException` para respostas de erro e capturam exceções do SQLAlchemy. As mensagens são adequadas à fase atual de desenvolvimento; padronização adicional poderá ser realizada futuramente.

## 8. Testes automatizados

### 8.1. Estratégia

Os testes utilizam `pytest` e `TestClient` para chamar a API sem depender de requisições manuais pelo Swagger.

O arquivo `tests/conftest.py` contém fixtures compartilhadas:

- **`test_engine`**: cria conexão com `techstore_test_db` e verifica o nome do banco.
- **`client`**: fornece o cliente HTTP de testes e substitui os `engine` utilizados pelos serviços pelo mecanismo do banco de testes.
- **`banco_limpo`**: executa `TRUNCATE ... RESTART IDENTITY CASCADE` nas tabelas de teste antes e depois de cada caso que utiliza essa fixture.

**Atenção:** `banco_limpo` apaga todos os registros das quatro tabelas do banco de testes. Não armazene informações importantes em `techstore_test_db`.

### 8.2. Testes implementados e aprovados

Situação confirmada na **Etapa 118, em 31/10/2026**, com execução conjunta da suíte de testes:

| Arquivo | Cobertura | Testes aprovados |
| --- | --- | ---: |
| `tests/test_sistema.py` | Página inicial e saúde da API | 2 |
| `tests/test_banco.py` | Conexão com banco de testes e existência das tabelas | 2 |
| `tests/test_produtos.py` | Cadastro, consulta, atualização e exclusão lógica | 4 |
| `tests/test_validacao_produtos.py` | Sete entradas inválidas e cadastro com estoque zero | 8 |
| `tests/test_clientes.py` | Cadastro, consulta, consulta inexistente, atualização e exclusão lógica | 5 |
| `tests/test_pedidos.py` | Cadastro e baixa de estoque; indisponibilidade de estoque, clientes e produtos; consultas e listagem; cancelamento; devolução de estoque; fluxo de status e transições inválidas | 12 |
| **Total** | | **33** |

**Resultado da execução completa:** `33 passed, 1 warning in 3.89s`, com Python 3.13.11 e pytest 9.1.1. Não houve testes com falha. O aviso de compatibilidade é descrito na seção 8.4.

Os testes de pedidos verificam tanto os códigos HTTP e os dados retornados pela API quanto os registros persistidos e os saldos de estoque no PostgreSQL. A execução utiliza o banco isolado `techstore_test_db`.

### 8.3. Comandos de execução

Executar todos os testes:

```powershell
python -m pytest -v
```

Executar somente os testes de produtos:

```powershell
python -m pytest tests/test_produtos.py -v
```

Executar validações de produtos:

```powershell
python -m pytest tests/test_validacao_produtos.py -v
```

Executar testes de clientes:

```powershell
python -m pytest tests/test_clientes.py -v
```

Executar somente os testes de pedidos:

```powershell
python -m pytest tests/test_pedidos.py -v
```

### 8.4. Aviso de compatibilidade observado

As execuções atuais apresentam o aviso:

```text
StarletteDeprecationWarning: Using `httpx` with `starlette.testclient`
is deprecated; install `httpx2` instead.
```

O aviso **não impediu a aprovação dos testes realizados**. A compatibilidade entre versões do FastAPI, Starlette e clientes HTTP deverá ser avaliada antes da estabilização das dependências. Não é necessário trocar bibliotecas sem testar o impacto.

## 9. Cuidados com integridade e segurança

### Já adotados

- SQL parametrizado para valores de entrada.
- Schemas de validação com Pydantic.
- Restrições de integridade no PostgreSQL.
- Transações para operações de escrita.
- Controle de estoque e cancelamento de pedidos.
- Separação entre banco principal e banco de testes.
- Configuração sensível mantida no `.env` local.

### Pontos a desenvolver antes de uso público

- Autenticação e autorização de usuários.
- Política de armazenamento e verificação de senhas.
- Permissões por perfil para operações administrativas.
- Gestão segura de segredos em ambientes implantados.
- Migrações versionadas do banco de dados.
- Paginação e filtros para listagens.
- Logs estruturados e monitoramento.
- Testes adicionais de concorrência e falhas transacionais.
- Configuração de CORS, limites de requisições e políticas de implantação.

O projeto **não deve ser tratado como pronto para produção** apenas por possuir CRUD e testes básicos.

## 10. Histórico de evolução

### Backend e persistência

- Criação do banco principal `techstore_db` no PostgreSQL.
- Estruturação das tabelas de clientes, produtos, pedidos e itens.
- Organização da aplicação nas camadas `core`, `routers`, `schemas` e `services`.
- Implementação e validação manual do CRUD de produtos e clientes.
- Implementação de pedidos com cálculo de total, controle de estoque e transações.
- Implementação de transições de status e devolução de estoque em cancelamentos.

### Testes

- **Etapas 97–98:** primeiros testes da API e confirmação do banco de testes.
- **Etapas 99–100:** configuração de limpeza de dados e teste de cadastro de produtos.
- **Etapa 101:** teste de consulta de produto.
- **Etapa 102:** teste de atualização de produto.
- **Etapa 103:** teste de exclusão lógica de produto.
- **Etapa 104:** oito cenários de validação de produtos.
- **Etapa 105:** teste de cadastro de cliente, incluindo conferência no PostgreSQL.
- **Etapas 106–108:** testes de consulta, atualização e exclusão lógica de clientes.
- **Etapa 109:** execução da suíte completa anterior, com 21 testes aprovados.
- **Etapas 110–117:** criação de 12 testes automatizados de pedidos, incluindo regras de estoque, disponibilidade de clientes e produtos, consultas, cancelamento e transições de status.
- **Etapa 118:** execução conjunta da suíte, com **33 testes aprovados**, nenhuma falha e um aviso de compatibilidade.

## 11. Próximas etapas

### Curto prazo — preparar o versionamento e ampliar a cobertura

1. Revisar `.gitignore` e conferir se nenhum segredo, ambiente virtual, cache ou backup sensível será publicado.
2. Consolidar e revisar `requirements.txt` e criar `.env.example` sem credenciais reais.
3. Consolidar scripts de criação/migração do esquema PostgreSQL para permitir reprodução do ambiente.
4. Inicializar ou revisar o repositório Git e publicar o estado validado no GitHub.
5. Ampliar testes de entradas inválidas, duplicidade de itens em pedidos, conflitos de clientes e cenários transacionais.

### Médio prazo — consolidar a aplicação

- Gerar e revisar `requirements.txt`.
- Consolidar scripts de criação e migração do banco.
- Criar `.env.example` sem dados sensíveis.
- Implementar autenticação e autorização.
- Organizar logs, tratamento de erros e configuração por ambiente.
- Preparar documentação de implantação e evolução contínua do repositório GitHub.

### Evolução planejada — ainda não implementada nesta versão

- **Frontend:** interface web com React e TypeScript.
- **Inteligência artificial:** integração com Amazon Bedrock para recursos inteligentes e atendimento.
- **Arquitetura orientada a eventos:** AWS Lambda, Amazon SQS e fila de mensagens não processadas (DLQ).
- **Estado e sessões:** avaliação de uso de DynamoDB para componentes específicos.
- **Automações:** fluxos com n8n.
- **Observabilidade:** métricas e logs com Amazon CloudWatch.
- **Publicação:** repositório GitHub e infraestrutura de execução apropriada.

Essas tecnologias fazem parte da direção prevista para o portfólio, mas não devem ser descritas como integrações operacionais no estado atual.

## 12. Estado atual do projeto

**Concluído e verificado:**

- API FastAPI executada localmente.
- Conexão com PostgreSQL.
- Operações de produtos e clientes.
- Operações de pedidos verificadas manualmente e por testes automatizados.
- Exclusão lógica de produtos e clientes.
- Regras de estoque e transições de pedidos.
- Banco de testes separado.
- **33 testes automatizados aprovados em execução conjunta (`python -m pytest -v`).**

**Próximo marco:** preparar o projeto para versionamento seguro no GitHub, preservando a documentação, os testes e o código sem publicar credenciais locais.

---

**TechStore — E-commerce Inteligente**  
Documentação atualizada em **31 de outubro de 2026**, após a conclusão da Etapa 118.
