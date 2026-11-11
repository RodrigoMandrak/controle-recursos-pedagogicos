import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

def conectar():
    return psycopg2.connect(
        host=os.getenv("DB_HOST"),
        database=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        port=os.getenv("DB_PORT"),
        # banco na nuvem (Neon) exige conexao segura; no PC fica "prefer"
        sslmode=os.getenv("DB_SSLMODE", "prefer")
    )


def atualizar_estrutura():
    # ajustes no banco que entraram depois da primeira versao.
    # IF NOT EXISTS: pode rodar toda vez que o sistema liga, sem estragar nada.
    banco = conectar()
    cursor = banco.cursor()

    # estoque do recurso (ex.: 3 notebooks). Recursos antigos ficam com 1.
    cursor.execute("""
        ALTER TABLE recursos
        ADD COLUMN IF NOT EXISTS quantidade INTEGER NOT NULL DEFAULT 1
    """)

    # recurso excluido que ja foi usado fica arquivado (ativo = FALSE),
    # para o historico das aulas que ja aconteceram continuar certo
    cursor.execute("""
        ALTER TABLE recursos
        ADD COLUMN IF NOT EXISTS ativo BOOLEAN NOT NULL DEFAULT TRUE
    """)

    banco.commit()
    cursor.close()
    banco.close()
