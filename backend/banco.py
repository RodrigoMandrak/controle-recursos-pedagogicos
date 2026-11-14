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

    # disciplina, turma ou professor excluido que ja teve aula fica arquivado
    # (ativo = FALSE): some das listas, mas o historico continua certo
    for tabela in ("disciplinas", "turmas", "professores"):
        cursor.execute(f"""
            ALTER TABLE {tabela}
            ADD COLUMN IF NOT EXISTS ativo BOOLEAN NOT NULL DEFAULT TRUE
        """)

    # limite de tentativas de login (senha errada varias vezes bloqueia por alguns minutos)
    cursor.execute("""
        ALTER TABLE usuarios
        ADD COLUMN IF NOT EXISTS tentativas_login INTEGER NOT NULL DEFAULT 0
    """)
    cursor.execute("""
        ALTER TABLE usuarios
        ADD COLUMN IF NOT EXISTS bloqueado_ate TIMESTAMP
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

    # logs antigos guardavam so numeros ("atividade 51 e recurso 3"):
    # troca pelos nomes, para a auditoria ser legivel
    traduzir_logs_antigos(cursor)

    banco.commit()
    cursor.close()
    banco.close()


# "Banco de Dados · 7A · 22/09/2026 08:00-10:00 · Prof. Ana" (mesmo texto do descrever_atividade)
ROTULO_SQL = """
    d.nome || ' · ' || t.nome || ' · ' || TO_CHAR(a.data, 'DD/MM/YYYY') || ' '
    || TO_CHAR(a.hora_inicio, 'HH24:MI') || '-' || TO_CHAR(a.hora_fim, 'HH24:MI') || ' · ' || p.nome
"""

JUNTA_ATIVIDADE = """
    JOIN disciplinas d ON d.id = a.disciplina_id
    JOIN turmas t ON t.id = a.turma_id
    JOIN professores p ON p.id = a.professor_id
"""


def traduzir_logs_antigos(cursor):
    # so mexe nos textos que ainda estao no formato antigo, entao pode rodar sempre
    cursor.execute(f"""
        UPDATE logs l
        SET detalhes = r.nome || ' reservado para ' || {ROTULO_SQL}
        FROM recursos r, atividades a {JUNTA_ATIVIDADE}
        WHERE l.acao = 'ALOCACAO_RECURSO'
        AND l.detalhes ~ '^Recurso [0-9]+ alocado na atividade [0-9]+$'
        AND r.id = (REGEXP_MATCH(l.detalhes, '^Recurso ([0-9]+)'))[1]::int
        AND a.id = (REGEXP_MATCH(l.detalhes, 'atividade ([0-9]+)$'))[1]::int
    """)

    cursor.execute(f"""
        UPDATE logs l
        SET detalhes = 'Reserva de ' || r.nome || ' cancelada em ' || {ROTULO_SQL}
        FROM recursos r, atividades a {JUNTA_ATIVIDADE}
        WHERE l.acao = 'CANCELAMENTO_ALOCACAO'
        AND l.detalhes ~ '^Alocacao [0-9]+ da atividade [0-9]+ e recurso [0-9]+ foi cancelada$|^Alocacao da atividade [0-9]+ e recurso [0-9]+ foi cancelada$'
        AND r.id = (REGEXP_MATCH(l.detalhes, 'recurso ([0-9]+) foi cancelada$'))[1]::int
        AND a.id = (REGEXP_MATCH(l.detalhes, 'atividade ([0-9]+) e recurso'))[1]::int
    """)

    cursor.execute("""
        UPDATE logs l
        SET detalhes = 'Recurso trocado de ' || r1.nome || ' para ' || r2.nome
        FROM recursos r1, recursos r2
        WHERE l.acao = 'ALTERACAO_ALOCACAO'
        AND l.detalhes ~ '^Alocacao [0-9]+ alterada do recurso [0-9]+ para [0-9]+$'
        AND r1.id = (REGEXP_MATCH(l.detalhes, 'do recurso ([0-9]+)'))[1]::int
        AND r2.id = (REGEXP_MATCH(l.detalhes, 'para ([0-9]+)$'))[1]::int
    """)

    cursor.execute("""
        UPDATE logs l
        SET detalhes = d.nome || ' · ' || t.nome || ' · ' || p.nome
        FROM disciplinas d, turmas t, professores p
        WHERE l.acao = 'CADASTRO_ATIVIDADE'
        AND l.detalhes ~ '^Disciplina [0-9]+, turma [0-9]+, professor [0-9]+'
        AND d.id = (REGEXP_MATCH(l.detalhes, '^Disciplina ([0-9]+)'))[1]::int
        AND t.id = (REGEXP_MATCH(l.detalhes, 'turma ([0-9]+)'))[1]::int
        AND p.id = (REGEXP_MATCH(l.detalhes, 'professor ([0-9]+)'))[1]::int
    """)

    cursor.execute("""
        UPDATE logs l
        SET detalhes = 'Recurso ' || r.nome || SUBSTRING(l.detalhes FROM '^Recurso [0-9]+(.*)$')
        FROM recursos r
        WHERE l.acao IN ('ALTERACAO_RECURSO', 'EXCLUSAO_RECURSO')
        AND l.detalhes ~ '^Recurso [0-9]+ (alterado|excluido)'
        AND r.id = (REGEXP_MATCH(l.detalhes, '^Recurso ([0-9]+)'))[1]::int
    """)
