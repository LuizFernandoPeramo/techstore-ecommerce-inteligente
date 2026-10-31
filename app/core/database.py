
import os

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL


load_dotenv()


DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")


if not all([DB_NAME, DB_USER, DB_PASSWORD]):
    raise RuntimeError(
        "Configuracoes do banco incompletas no arquivo .env"
    )


DATABASE_URL = URL.create(
    drivername="postgresql+psycopg",
    username=DB_USER,
    password=DB_PASSWORD,
    host=DB_HOST,
    port=int(DB_PORT),
    database=DB_NAME
)


engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True
)


def testar_conexao():
    try:
        with engine.connect() as conexao:
            resultado = conexao.execute(
                text("SELECT current_database()")
            )

            banco = resultado.scalar_one()

            print("Conexao com PostgreSQL realizada com sucesso!")
            print(f"Banco de dados: {banco}")

            return True

    except Exception as erro:
        print(f"Falha na conexao: {type(erro).__name__}")
        return False


if __name__ == "__main__":
    testar_conexao()
