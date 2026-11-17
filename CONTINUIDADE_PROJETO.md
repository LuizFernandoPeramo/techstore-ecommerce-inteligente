
# TechStore — Documento de Continuidade do Projeto

Atualizado em: 17/11/2026

## 1. Identificação

Nome: TechStore — E-commerce Inteligente

Diretório local: ai-support-hub

Repositório:
https://github.com/LuizFernandoPeramo/techstore-ecommerce-inteligente

Branch principal: main

Último commit confirmado: 8405eb1

Descrição do commit:
fix: integra status dos pedidos ao fluxo de pagamentos e atualiza testes

Data do commit: 15/11/2026

Progresso estimado: 68%

Última execução integral dos testes: 180 aprovados, 1 aviso não bloqueante.

## 2. Objetivo do projeto

Desenvolver uma plataforma de comércio eletrônico voltada à comercialização de produtos de tecnologia, utilizando boas práticas de engenharia de software.

O projeto também tem finalidade de portfólio profissional, demonstrando conhecimentos em desenvolvimento backend, banco de dados, segurança, testes, arquitetura de software, frontend e futuras integrações com inteligência artificial e serviços em nuvem.

O desenvolvimento deve priorizar funcionalidades consistentes, código organizado, segurança, integridade dos dados e evolução incremental.

## 3. Tecnologias

Backend:
- Python 3.13
- FastAPI
- Pydantic
- SQLAlchemy
- psycopg
- Uvicorn

Banco de dados:
- PostgreSQL 17

Segurança:
- Autenticação JWT
- Hash de senhas
- Controle de acesso por perfil
- Verificação de titularidade dos recursos

Testes:
- pytest
- FastAPI TestClient
- httpx

Ambiente:
- Windows
- PowerShell
- Visual Studio Code
- Ambiente virtual .venv
- Git e GitHub

Tecnologias planejadas:
- React e TypeScript
- Amazon Bedrock
- AWS Lambda
- Amazon SQS e DLQ
- Amazon CloudWatch
- Possível utilização de DynamoDB
- n8n

As tecnologias planejadas não devem ser apresentadas como implementadas.

## 4. Arquitetura

O backend está organizado em camadas.

app/core/
Responsável por conexão com banco de dados, autenticação e permissões.

app/routers/
Responsável pelas rotas HTTP, dependências e respostas da API.

app/schemas/
Responsável pelos modelos de entrada e saída e validação de dados.

app/services/
Responsável pelas regras de negócio, consultas ao banco e transações.

migrations/
Contém scripts SQL de evolução da estrutura do banco.

tests/
Contém os testes automatizados do sistema.

O fluxo geral é:

Cliente HTTP
    |
    v
FastAPI / Router
    |
    v
Autenticação e autorização
    |
    v
Schema / Service
    |
    v
SQLAlchemy / psycopg
    |
    v
PostgreSQL

## 5. Funcionalidades implementadas

### 5.1. Clientes

- Cadastro de clientes.
- Consulta e atualização.
- Exclusão lógica.
- Validação de dados.
- Restrições de duplicidade.
- Controle de acesso por titularidade e perfil administrativo.

### 5.2. Produtos

- Cadastro de produtos.
- Listagem e consulta.
- Atualização.
- Exclusão lógica.
- Validação de preço e estoque.
- Controle de disponibilidade.

### 5.3. Autenticação e autorização

- Login com e-mail e senha.
- Emissão e validação de tokens JWT.
- Consulta da conta autenticada.
- Perfis cliente e admin.
- Verificação do perfil atualizado no banco.
- Proteção contra acesso indevido a recursos de outros clientes.

### 5.4. Pedidos

- Criação de pedidos com múltiplos itens.
- Cálculo de valores.
- Verificação e reserva de estoque.
- Transações para preservar integridade.
- Consulta e listagem de pedidos.
- Controle de transições de status.
- Cancelamento de pedidos pendentes com devolução de estoque.

### 5.5. Carrinho e checkout

- Estrutura de carrinho persistente.
- Operações de carrinho implementadas no backend.
- Fluxo de checkout.
- Validação de disponibilidade e estoque.
- Testes de integridade e rollback.

### 5.6. Pagamentos simulados

- Estrutura de pagamentos no PostgreSQL.
- Associação entre pagamento e pedido.
- Métodos simulados de pagamento.
- Controle de status do pagamento.
- Restrições para evitar aprovações duplicadas.
- Simulação de aprovação e recusa.
- Integração entre aprovação do pagamento e status do pedido.
- Testes de autorização e regras transacionais.

Os pagamentos são simulados. Não existe integração confirmada com um provedor real.

## 6. Regras de negócio importantes

### Pedidos e pagamentos

O pedido é inicialmente criado com status pendente.

A mudança para pago deve ocorrer pelo fluxo de aprovação do pagamento, e não por alteração manual do status.

Após o pagamento aprovado, o pedido pode avançar para enviado e entregue, respeitando as permissões e transições implementadas.

O cancelamento de pedido pendente deve restaurar o estoque e cancelar eventual pagamento pendente associado.

Pedidos pagos não podem ser cancelados diretamente enquanto não houver um fluxo de estorno implementado.

Pedidos enviados também não podem ser cancelados diretamente.

### Integridade

- Operações críticas devem utilizar transações.
- Alterações de estoque precisam evitar inconsistências.
- Não deve ocorrer devolução duplicada de estoque.
- Pagamentos não devem ser aprovados em duplicidade.
- O cliente não pode acessar recursos de outro cliente sem autorização.
- Regras de negócio devem ser aplicadas nos serviços e verificadas por testes.

## 7. Banco de dados

Banco de desenvolvimento:
techstore_db

Banco de testes:
techstore_test_db

O banco de testes é utilizado pelas fixtures automatizadas e seus registros podem ser apagados durante a execução.

Nunca utilizar o banco de desenvolvimento ou produção como banco de testes.

Migrações versionadas:

001_adicionar_perfil_clientes.sql
002_criar_carrinho.sql
003_criar_pagamentos.sql

Ainda é necessário consolidar a criação completa do esquema para permitir a instalação do projeto em um ambiente novo.

## 8. Testes automatizados

Última execução integral confirmada:

180 passed, 1 warning

O aviso registrado foi relacionado à compatibilidade do cliente de testes Starlette/httpx e não impediu a aprovação.

Arquivos de testes:

- test_auth.py
- test_autorizacao.py
- test_autorizacao_pedidos.py
- test_banco.py
- test_carrinho.py
- test_checkout.py
- test_checkout_rollback.py
- test_clientes.py
- test_pagamentos.py
- test_pedidos.py
- test_produtos.py
- test_regras_negocio.py
- test_sistema.py
- test_validacao_produtos.py

Comando utilizado no ambiente local:

.\.venv\Scripts\python.exe -m pytest -v

A execução integral deve ocorrer com o banco de testes preparado.

## 9. Estado do Git

Branch: main

Último commit:
8405eb1

Data:
15/11/2026

Publicação no GitHub:
Confirmada para o último commit.

Em 17/11/2026, o comando git status --short não apresentou alterações.

As pastas temporárias backup_seguranca_pedidos e backup_testes foram removidas.

Este documento foi criado após essa verificação e ainda precisará ser versionado.

## 10. Pendências técnicas

### Prioridade imediata

1. Consolidar e versionar requirements.txt com dependências verificadas.
2. Criar .env.example sem credenciais reais.
3. Consolidar scripts de criação integral do banco de dados.
4. Revisar o procedimento de aplicação das migrações.
5. Atualizar o README para refletir carrinho, checkout, pagamentos e 180 testes.

### Evolução do backend

- Revisar paginação e filtros.
- Melhorar padronização das respostas de erro.
- Implementar gestão administrativa segura de contas e perfis.
- Ampliar testes de concorrência e segurança.
- Revisar logs, observabilidade e configurações de implantação.
- Definir fluxo de estorno antes de permitir cancelamento de pedidos pagos.

### Frontend

Desenvolver interface web com React e TypeScript, incluindo:

- Catálogo de produtos.
- Cadastro e login.
- Carrinho de compras.
- Checkout.
- Acompanhamento de pedidos.
- Área administrativa.

### Inteligência artificial

Avaliar integração com Amazon Bedrock para funcionalidades inteligentes do e-commerce.

Os casos de uso deverão ser definidos antes da implementação.

### Infraestrutura e integrações

Avaliar:
- Implantação em nuvem.
- AWS Lambda.
- Amazon SQS e DLQ.
- CloudWatch.
- Automação com n8n.
- Possível uso de DynamoDB.

A adoção de cada serviço dependerá dos requisitos técnicos e da evolução do projeto.

## 11. Próxima etapa recomendada

Iniciar pela consolidação das dependências Python e da configuração de ambiente.

Verificar as bibliotecas realmente utilizadas pelo projeto antes de criar requirements.txt.

Depois preparar .env.example e validar a instalação em ambiente reproduzível.

Em seguida, revisar a criação completa do banco de dados e atualizar o README.

Não avançar para integrações externas antes de concluir essas etapas básicas de manutenção.

## 12. Procedimento de trabalho

O desenvolvimento é conduzido de forma incremental.

Orientações para continuidade:

1. Executar uma etapa ou comando por vez.
2. Aguardar o resultado do usuário antes de avançar.
3. Quando um arquivo de código precisar ser alterado, fornecer sempre o arquivo completo para substituição.
4. Agrupar os testes de uma etapa em uma única execução.
5. Não presumir acesso automático aos arquivos locais.
6. Manter código e documentação com escrita profissional, natural e objetiva.
7. Atualizar o README somente após mudanças relevantes.
8. Antes de commits, verificar testes e estado do Git.
9. Após cada commit, informar o percentual estimado de conclusão do projeto.
10. Não publicar credenciais, tokens ou arquivos .env no GitHub.

## 13. Como retomar em outra conversa

Para continuar o desenvolvimento:

1. Informar que o projeto é o TechStore — E-commerce Inteligente.
2. Disponibilizar este documento atualizado.
3. Informar o último commit e o resultado mais recente dos testes.
4. Confirmar o estado do Git.
5. Retomar a primeira pendência técnica ainda não concluída.

O documento deve ser atualizado após marcos relevantes do desenvolvimento.

## 14. Referências

README.md

Código-fonte versionado no repositório GitHub:
https://github.com/LuizFernandoPeramo/techstore-ecommerce-inteligente

Último commit de referência:
8405eb1

Última verificação:
17/11/2026
