import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

# fuso horario do sistema: o servidor na nuvem roda em UTC (3h a frente),
# entao "hoje", "agora" e a hora dos logs passam a ser os do Brasil
FUSO = os.getenv("FUSO_HORARIO", "America/Sao_Paulo")
os.environ.setdefault("TZ", FUSO)
try:
    import time
    time.tzset()
except AttributeError:
    # Windows nao tem tzset; no PC o relogio ja e o do Brasil
    pass


def conectar():
    return psycopg2.connect(
        host=os.getenv("DB_HOST"),
        database=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        port=os.getenv("DB_PORT"),
        # banco na nuvem (Neon) exige conexao segura; no PC fica "prefer"
        sslmode=os.getenv("DB_SSLMODE", "prefer"),
        # CURRENT_DATE, CURRENT_TIME e a data dos logs no horario do Brasil
        options=f"-c timezone={FUSO}"
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

    # aprovacao de cadastro: contas antigas continuam "ativo"
    cursor.execute("""
        ALTER TABLE usuarios
        ADD COLUMN IF NOT EXISTS status VARCHAR(20) NOT NULL DEFAULT 'ativo'
    """)

    # cada professor da lista pode estar ligado a uma conta de login
    cursor.execute("""
        ALTER TABLE professores
        ADD COLUMN IF NOT EXISTS usuario_id INTEGER REFERENCES usuarios(id) ON DELETE SET NULL
    """)

    # contas de professor ja aprovadas que ainda nao estao na lista:
    # liga pelo mesmo nome, ou coloca na lista
    cursor.execute("""
        UPDATE professores p
        SET usuario_id = u.id
        FROM usuarios u
        WHERE p.usuario_id IS NULL
        AND LOWER(p.nome) = LOWER(u.nome)
        AND u.perfil = 'professor'
        AND u.status = 'ativo'
        AND NOT EXISTS (SELECT 1 FROM professores p2 WHERE p2.usuario_id = u.id)
    """)
    cursor.execute("""
        INSERT INTO professores (nome, usuario_id)
        SELECT u.nome, u.id
        FROM usuarios u
        WHERE u.perfil = 'professor'
        AND u.status = 'ativo'
        AND NOT EXISTS (SELECT 1 FROM professores p WHERE p.usuario_id = u.id)
    """)

    banco.commit()
    cursor.close()
    banco.close()
