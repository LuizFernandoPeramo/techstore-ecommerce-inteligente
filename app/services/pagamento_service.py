
import os

from fastapi import HTTPException
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.core.database import engine
from app.schemas.pagamento import PagamentoCadastro


def criar_pagamento(
    dados: PagamentoCadastro,
    cliente_autenticado: dict
):
    try:
        with engine.begin() as conexao:
            pedido = conexao.execute(
                text("""
                    SELECT id, cliente_id, status, valor_total
                    FROM pedidos
                    WHERE id = :pedido_id
                    FOR UPDATE
                """),
                {"pedido_id": dados.pedido_id}
            ).mappings().first()

            if pedido is None:
                raise HTTPException(
                    status_code=404,
                    detail="Pedido nao encontrado"
                )

            if (
                cliente_autenticado["perfil"] != "admin"
                and pedido["cliente_id"] != cliente_autenticado["id"]
            ):
                raise HTTPException(
                    status_code=403,
                    detail="Voce nao pode pagar este pedido"
                )

            if pedido["status"] != "pendente":
                raise HTTPException(
                    status_code=409,
                    detail="O pedido nao esta pendente"
                )

            if pedido["valor_total"] <= 0:
                raise HTTPException(
                    status_code=409,
                    detail="O pedido possui valor invalido"
                )

            pagamento_existente = conexao.execute(
                text("""
                    SELECT id
                    FROM pagamentos
                    WHERE pedido_id = :pedido_id
                      AND status IN ('pendente', 'aprovado')
                    LIMIT 1
                """),
                {"pedido_id": dados.pedido_id}
            ).first()

            if pagamento_existente is not None:
                raise HTTPException(
                    status_code=409,
                    detail="O pedido ja possui pagamento ativo"
                )

            pagamento = conexao.execute(
                text("""
                    INSERT INTO pagamentos (
                        pedido_id,
                        valor,
                        metodo,
                        status
                    )
                    VALUES (
                        :pedido_id,
                        :valor,
                        :metodo,
                        'pendente'
                    )
                    RETURNING
                        id,
                        pedido_id,
                        valor,
                        metodo,
                        status,
                        referencia_externa,
                        criado_em,
                        atualizado_em
                """),
                {
                    "pedido_id": pedido["id"],
                    "valor": pedido["valor_total"],
                    "metodo": dados.metodo
                }
            ).mappings().one()

            return dict(pagamento)

    except SQLAlchemyError:
        raise HTTPException(
            status_code=500,
            detail="Erro ao criar pagamento"
        )


def simular_pagamento(
    pagamento_id: int,
    resultado: str
):
    ambiente = os.getenv(
        "APP_ENV",
        ""
    ).strip().lower()

    if ambiente not in ("development", "testing"):
        raise HTTPException(
            status_code=403,
            detail="Simulacao indisponivel neste ambiente"
        )

    if resultado not in ("aprovado", "recusado"):
        raise HTTPException(
            status_code=422,
            detail="Resultado de pagamento invalido"
        )

    try:
        with engine.begin() as conexao:
            identificacao = conexao.execute(
                text("""
                    SELECT pedido_id
                    FROM pagamentos
                    WHERE id = :pagamento_id
                """),
                {"pagamento_id": pagamento_id}
            ).mappings().first()

            if identificacao is None:
                raise HTTPException(
                    status_code=404,
                    detail="Pagamento nao encontrado"
                )

            pedido = conexao.execute(
                text("""
                    SELECT id, status, valor_total
                    FROM pedidos
                    WHERE id = :pedido_id
                    FOR UPDATE
                """),
                {"pedido_id": identificacao["pedido_id"]}
            ).mappings().first()

            if pedido is None:
                raise HTTPException(
                    status_code=404,
                    detail="Pedido nao encontrado"
                )

            pagamento = conexao.execute(
                text("""
                    SELECT
                        id,
                        pedido_id,
                        valor,
                        metodo,
                        status
                    FROM pagamentos
                    WHERE id = :pagamento_id
                    FOR UPDATE
                """),
                {"pagamento_id": pagamento_id}
            ).mappings().first()

            if pagamento["status"] != "pendente":
                raise HTTPException(
                    status_code=409,
                    detail="O pagamento ja foi processado"
                )

            if pedido["status"] != "pendente":
                raise HTTPException(
                    status_code=409,
                    detail="O pedido nao esta pendente"
                )

            if pagamento["valor"] != pedido["valor_total"]:
                raise HTTPException(
                    status_code=409,
                    detail="Valor do pagamento divergente"
                )

            pagamento_atualizado = conexao.execute(
                text("""
                    UPDATE pagamentos
                    SET
                        status = :resultado,
                        atualizado_em = CURRENT_TIMESTAMP
                    WHERE id = :pagamento_id
                    RETURNING
                        id,
                        pedido_id,
                        valor,
                        metodo,
                        status,
                        referencia_externa,
                        criado_em,
                        atualizado_em
                """),
                {
                    "resultado": resultado,
                    "pagamento_id": pagamento_id
                }
            ).mappings().one()

            if resultado == "aprovado":
                conexao.execute(
                    text("""
                        UPDATE pedidos
                        SET status = 'pago'
                        WHERE id = :pedido_id
                    """),
                    {"pedido_id": pedido["id"]}
                )

            mensagem = (
                "Pagamento aprovado com sucesso"
                if resultado == "aprovado"
                else "Pagamento recusado"
            )

            return {
                **dict(pagamento_atualizado),
                "mensagem": mensagem
            }

    except SQLAlchemyError:
        raise HTTPException(
            status_code=500,
            detail="Erro ao processar pagamento"
        )
