import { useEffect, useState } from "react";

// Tela do coordenador: pre-cadastros esperando aprovacao.
// Busca pelo e-mail, e um clique da o cargo de professor.

function Solicitacoes({ api, aoAprovar, aberta }) {
  const [busca, setBusca] = useState("");
  const [lista, setLista] = useState([]);
  const [carregando, setCarregando] = useState(false);
  const [mensagem, setMensagem] = useState(null);
  const [confirmarRecusa, setConfirmarRecusa] = useState(null);
  const [enviando, setEnviando] = useState(false);

  async function carregar(texto) {
    setCarregando(true);
    try {
      const resposta = await fetch(
        `${api}/solicitacoes?email=${encodeURIComponent(texto.trim())}`,
        { credentials: "include" }
      );
      const resultado = await resposta.json();
      setLista(resposta.ok && Array.isArray(resultado) ? resultado : []);
    } catch {
      setLista([]);
    } finally {
      setCarregando(false);
    }
  }

  // busca sozinha enquanto digita (espera o usuario parar de digitar)
  useEffect(() => {
    if (!aberta) return undefined;
    const espera = setTimeout(() => carregar(busca), 300);
    return () => clearTimeout(espera);
  }, [busca, aberta]);

  async function aprovar(pessoa) {
    setEnviando(true);
    setMensagem(null);
    try {
      const resposta = await fetch(`${api}/solicitacoes/${pessoa.id}/aprovar`, {
        method: "POST",
        credentials: "include",
      });
      const resultado = await resposta.json();
      if (!resposta.ok) {
        setMensagem({ tipo: "erro", texto: resultado.erro || "Não foi possível aprovar." });
        return;
      }
      setMensagem({ tipo: "ok", texto: `${pessoa.nome} agora é professor e já aparece na lista de professores.` });
      aoAprovar();
      carregar(busca);
    } catch {
      setMensagem({ tipo: "erro", texto: "Erro ao conectar com o servidor." });
    } finally {
      setEnviando(false);
    }
  }

  async function recusar(pessoa) {
    // primeiro clique pede confirmacao; o segundo recusa
    if (confirmarRecusa !== pessoa.id) {
      setConfirmarRecusa(pessoa.id);
      return;
    }
    setConfirmarRecusa(null);
    setEnviando(true);
    setMensagem(null);
    try {
      const resposta = await fetch(`${api}/solicitacoes/${pessoa.id}`, {
        method: "DELETE",
        credentials: "include",
      });
      const resultado = await resposta.json();
      if (!resposta.ok) {
        setMensagem({ tipo: "erro", texto: resultado.erro || "Não foi possível recusar." });
        return;
      }
      setMensagem({ tipo: "ok", texto: `Cadastro de ${pessoa.email} recusado.` });
      carregar(busca);
    } catch {
      setMensagem({ tipo: "erro", texto: "Erro ao conectar com o servidor." });
    } finally {
      setEnviando(false);
    }
  }

  return (
    <section className="rounded-[28px] bg-card p-6 ring-1 ring-line [box-shadow:0_24px_50px_-30px_rgba(69,61,46,.45)] sm:p-8">
      <div className="mb-6 border-b border-line pb-4">
        <h2 className="text-lg font-semibold">Solicitações de cadastro</h2>
        <p className="mt-1 text-sm text-mute">
          Quem cria conta fica aguardando aqui e não consegue entrar no sistema. Busque pelo e-mail do professor e
          clique em "Dar cargo de professor". Ele passa a aparecer na lista de professores e já pode cadastrar
          atividades no próprio nome.
        </p>
      </div>

      <label className="block text-xs font-semibold uppercase tracking-wide text-mute">
        Buscar pelo e-mail
        <input
          type="search"
          value={busca}
          onChange={(e) => setBusca(e.target.value)}
          placeholder="Ex.: mariana@escola.com.br"
          className="mt-1 w-full rounded-xl bg-paper px-3.5 py-2.5 text-sm font-normal normal-case tracking-normal text-ink ring-1 ring-line focus:outline-none focus:ring-2 focus:ring-green"
        />
      </label>

      {mensagem && (
        <p
          role="status"
          className={`mt-4 rounded-xl px-3 py-2 text-sm font-semibold ring-1 ${
            mensagem.tipo === "ok"
              ? "bg-[#e8f0eb] text-[#3f6550] ring-[#c7dccf]"
              : "bg-paper text-[#8f3f2c] ring-line"
          }`}
        >
          {mensagem.texto}
        </p>
      )}

      <div className="mt-5 space-y-3">
        {carregando && lista.length === 0 && <p className="text-sm text-mute">Buscando...</p>}

        {!carregando && lista.length === 0 && (
          <p className="rounded-xl bg-paper px-4 py-6 text-center text-sm text-mute ring-1 ring-line">
            {busca.trim()
              ? `Nenhum pré-cadastro pendente com "${busca.trim()}".`
              : "Nenhum cadastro aguardando aprovação."}
          </p>
        )}

        {lista.map((pessoa) => (
          <div
            key={pessoa.id}
            className="flex flex-wrap items-center justify-between gap-3 rounded-2xl bg-paper px-4 py-3 ring-1 ring-line"
          >
            <div className="min-w-0">
              <p className="font-semibold">{pessoa.nome}</p>
              <p className="text-sm text-mute">
                {pessoa.email}
                {pessoa.identificador ? ` · ${pessoa.identificador}` : ""}
                {pessoa.data ? ` · pediu em ${pessoa.data.slice(0, 10).split("-").reverse().join("/")}` : ""}
              </p>
            </div>
            <div className="flex gap-2">
              <button
                type="button"
                onClick={() => aprovar(pessoa)}
                disabled={enviando}
                className="rounded-lg bg-[#4f7a63] px-4 py-2 text-sm font-semibold text-white transition-colors hover:bg-[#3f6550] disabled:opacity-60"
              >
                Dar cargo de professor
              </button>
              <button
                type="button"
                onClick={() => recusar(pessoa)}
                disabled={enviando}
                className={`rounded-lg px-4 py-2 text-sm font-semibold ring-1 ${
                  confirmarRecusa === pessoa.id
                    ? "bg-[#8f3f2c] text-white ring-[#8f3f2c]"
                    : "bg-card text-[#8f3f2c] ring-line hover:bg-paper"
                }`}
              >
                {confirmarRecusa === pessoa.id ? "Confirmar recusa" : "Recusar"}
              </button>
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}

export default Solicitacoes;
