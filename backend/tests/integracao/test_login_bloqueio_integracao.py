"""
Teste de integracao do limite de tentativas de login (por e-mail + IP).

Cenario do apontamento da orientacao: alguem que sabe o e-mail de um professor
erra a senha 5 vezes. Antes a conta inteira ficava bloqueada; agora so o acesso
daquele computador (IP) fica bloqueado, e o dono continua entrando do dele.
"""

from apoio_integracao import consultar, novo_cliente, unico
from models.usuario_model import cadastrar_usuario


def preparar_conta():
    email = f"bloqueio.{unico()}@teste.umc.br"
    cadastrar_usuario("Professor Bloqueio", email, "SenhaForte123", "professor")
    return email


def tentar(base_url, email, senha, ip):
    cliente = novo_cliente()
    resposta = cliente.post(
        f"{base_url}/login",
        json={"email": email, "senha": senha},
        headers={"X-Forwarded-For": ip},
    )
    cliente.close()
    return resposta


def test_cincoSenhasErradas_bloqueiaSoOMesmoIp(base_url):
    email = preparar_conta()

    respostas = [tentar(base_url, email, "senha-errada", "200.0.0.1").status_code for _ in range(5)]

    assert respostas == [401, 401, 401, 401, 429]
    assert tentar(base_url, email, "SenhaForte123", "200.0.0.1").status_code == 429

    # o dono da conta, em outro computador, entra normalmente
    assert tentar(base_url, email, "SenhaForte123", "189.0.0.2").status_code == 200


def test_loginCerto_zeraAsTentativasDaqueleIp(base_url):
    email = preparar_conta()

    for _ in range(3):
        tentar(base_url, email, "senha-errada", "200.0.0.3")

    assert tentar(base_url, email, "SenhaForte123", "200.0.0.3").status_code == 200
    assert consultar(
        "SELECT COUNT(*) FROM tentativas_login WHERE email = %s", (email,)
    )[0][0] == 0
