import psycopg2

def conectar():
    return psycopg2.connect(
        host="localhost",
        database="controle_recursos",
        user="postgres",
        password="123",
        port="5433"
    )