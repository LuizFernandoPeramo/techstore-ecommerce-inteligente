
from fastapi import FastAPI

from app.routers.produtos import router as produtos_router
from app.routers.clientes import router as clientes_router
from app.routers.pedidos import router as pedidos_router
from app.routers.auth import router as auth_router
from app.routers.carrinho import router as carrinho_router
from app.routers.pagamentos import router as pagamentos_router


app = FastAPI(
    title="TechStore API",
    description="API do e-commerce inteligente TechStore",
    version="1.3.0"
)


app.include_router(produtos_router)
app.include_router(clientes_router)
app.include_router(pedidos_router)
app.include_router(auth_router)
app.include_router(carrinho_router)
app.include_router(pagamentos_router)


@app.get("/", tags=["Sistema"])
def inicio():
    return {
        "sistema": "TechStore",
        "mensagem": "Bem-vindo a API da TechStore!",
        "status": "online"
    }


@app.get("/saude", tags=["Sistema"])
def verificar_saude():
    return {
        "status": "ok",
        "servico": "TechStore API"
    }
