import { Fragment, useState } from "react";

// Tela do coordenador para cadastrar recursos e controlar o estoque.
// Ex.: "Notebooks" com quantidade 3 -> ate 3 atividades no mesmo horario.

const TIPOS = [
  { valor: "sala", nome: "Sala" },
  { valor: "laboratorio", nome: "Laboratório" },
  { valor: "equipamento", nome: "Equipamento" },
  { valor: "material", nome: "Material" },
  { valor: "outro", nome: "Outro" },
];

const FORM_VAZIO = { nome: "", tipo: "equipamento", quantidade: 1 };

const campo =
  "mt-1 w-full rounded-xl bg-paper px-3.5 py-2.5 text-sm text-ink ring-1 ring-line focus:outline-none focus:ring-2 focus:ring-green";
const rotulo = "text-xs font-semibold uppercase tracking-wide text-mute";

function nomeDoTipo(valor) {
  return TIPOS.find((tipo) => tipo.valor === valor)?.nome || valor;
}

function Recursos({ api, recursos, aoAlterar }) {
  const [form, setForm] = useState(FORM_VAZIO);
  const [editando, setEditando] = useState(null);
  const [mensagem, setMensagem] = useState(null);
  const [enviando, setEnviando] = useState(false);
  // id do recurso esperando o segundo clique em "Excluir" (confirmacao)
  const [confirmarExclusao, setConfirmarExclusao] = useState(null);
  // recurso com a lista de proximas reservas aberta
  const [verReservas, setVerReservas] = useState(null);
  const [reservas, setReservas] = useState([]);
  // texto digitado na busca da tabela
  const [busca, setBusca] = useState("");

  // ignora maiusculas e acentos: "laboratorio" acha "Laboratório"
  const normalizar = (texto) =>
    String(texto || "").normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLowerCase();
  const recursosFiltrados = recursos.filter((recurso) =>
    normalizar(`${recurso.nome} ${recurso.tipo}`).includes(normalizar(busca.trim()))
  );

  // mesma regra do back-end, conferida antes de mandar
  function validar(dados) {
    const nome = String(dados.nome || "").trim();
    const quantidade = Number(dados.quantidade);
    if (nome.length < 2) return "Informe o nome do recurso.";
    if (!Number.isInteger(quantidade) || quantidade < 1 || quantidade > 999) {
      return "A quantidade precisa ser um número inteiro entre 1 e 999.";
    }
    return "";
  }

  async function enviar(url, metodo, dados, textoSucesso) {
    const erro = validar(dados);
    if (erro) {
      setMensagem({ tipo: "erro", texto: erro });
      return false;
    }

    setEnviando(true);
    try {
      const resposta = await fetch(url, {
        method: metodo,
        credentials: "include",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ ...dados, nome: String(dados.nome).trim(), quantidade: Number(dados.quantidade) }),
      });
      const resultado = await resposta.json();

      if (!resposta.ok) {
        setMensagem({ tipo: "erro", texto: resultado.erro || "Não foi possível salvar o recurso." });
        return false;
      }

      setMensagem({ tipo: "ok", texto: textoSucesso });
      aoAlterar();
      return true;
    } catch {
      setMensagem({ tipo: "erro", texto: "Erro ao conectar com o servidor." });
      return false;
    } finally {
      setEnviando(false);
    }
  }

  async function cadastrar(e) {
    e.preventDefault();
    const deuCerto = await enviar(`${api}/recursos`, "POST", form, "Recurso cadastrado.");
    if (deuCerto) setForm(FORM_VAZIO);
  }

  async function abrirReservas(recurso) {
    if (verReservas === recurso.id) {
      setVerReservas(null);
      return;
    }

    setVerReservas(recurso.id);
    setReservas([]);
    try {
      const resposta = await fetch(`${api}/recursos/${recurso.id}/reservas`, { credentials: "include" });
      const resultado = await resposta.json();
      setReservas(resposta.ok && Array.isArray(resultado) ? resultado : []);
    } catch {
      setReservas([]);
    }
  }

  async function excluir(recurso) {
    // primeiro clique pede confirmacao; o segundo exclui
    if (confirmarExclusao !== recurso.id) {
      setConfirmarExclusao(recurso.id);
      return;
    }

    setConfirmarExclusao(null);
    setEnviando(true);
    try {
      const resposta = await fetch(`${api}/recursos/${recurso.id}`, {
        method: "DELETE",
        credentials: "include",
      });
      const resultado = await resposta.json();

      if (!resposta.ok) {
        setMensagem({ tipo: "erro", texto: resultado.erro || "Não foi possível excluir o recurso." });
        return;
      }

      setMensagem({ tipo: "ok", texto: `Recurso "${recurso.nome}" excluído.` });
      aoAlterar();
    } catch {
      setMensagem({ tipo: "erro", texto: "Erro ao conectar com o servidor." });
    } finally {
      setEnviando(false);
    }
  }

  async function salvarEdicao(e) {
    e.preventDefault();
    const deuCerto = await enviar(
      `${api}/recursos/${editando.id}`,
      "PUT",
      editando,
      "Recurso atualizado."
    );
    if (deuCerto) setEditando(null);
  }

  return (
    <div className="space-y-6">
      <section className="rounded-[28px] bg-card p-6 ring-1 ring-line [box-shadow:0_24px_50px_-30px_rgba(69,61,46,.45)] sm:p-8">
        <div className="mb-6 border-b border-line pb-4">
          <h2 className="text-lg font-semibold">Cadastrar recurso</h2>
          <p className="mt-1 text-sm text-mute">
            Informe quantas unidades existem. Quando todas estiverem reservadas no mesmo horário, o sistema
            avisa que o recurso não está disponível. Quando a aula termina, a unidade volta a ficar livre.
          </p>
        </div>

        <form onSubmit={cadastrar} className="grid gap-4 sm:grid-cols-[2fr_1.2fr_1fr_auto] sm:items-end">
          <label className={rotulo}>
            Nome
            <input
              type="text"
              value={form.nome}
              onChange={(e) => setForm({ ...form, nome: e.target.value })}
              placeholder="Ex.: Notebooks"
              maxLength={150}
              className={`${campo} font-normal normal-case tracking-normal`}
              required
            />
          </label>
          <label className={rotulo}>
            Tipo
            <select
              value={form.tipo}
              onChange={(e) => setForm({ ...form, tipo: e.target.value })}
              className={`${campo} font-normal normal-case tracking-normal`}
            >
              {TIPOS.map((tipo) => (
                <option key={tipo.valor} value={tipo.valor}>
                  {tipo.nome}
                </option>
              ))}
            </select>
          </label>
          <label className={rotulo}>
            Quantidade
            <input
              type="number"
              min="1"
              max="999"
              value={form.quantidade}
              onChange={(e) => setForm({ ...form, quantidade: e.target.value })}
              className={`${campo} font-normal normal-case tracking-normal`}
              required
            />
          </label>
          <button
            type="submit"
            disabled={enviando}
            className="rounded-xl bg-[#4f7a63] px-5 py-2.5 text-sm font-semibold text-white transition-colors hover:bg-[#3f6550] disabled:opacity-60"
          >
            Cadastrar
          </button>
        </form>

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
      </section>

      <section className="rounded-[28px] bg-card p-6 ring-1 ring-line sm:p-8">
        <div className="mb-4 flex flex-wrap items-end justify-between gap-3">
          <div>
            <h2 className="text-lg font-semibold">Recursos cadastrados</h2>
            <span className="text-sm text-mute">
              {busca.trim() ? `${recursosFiltrados.length} de ${recursos.length}` : `${recursos.length} no total`}
            </span>
          </div>
          <label className="w-full text-xs font-semibold uppercase tracking-wide text-mute sm:w-72">
            Pesquisar recurso
            <input
              type="search"
              value={busca}
              onChange={(e) => setBusca(e.target.value)}
              placeholder="Ex.: notebook"
              className={`${campo} font-normal normal-case tracking-normal`}
            />
          </label>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full min-w-[760px] text-left text-sm">
            <thead>
              <tr className="border-b border-line text-xs uppercase tracking-wide text-mute">
                <th className="py-2 pr-3 font-semibold">Recurso</th>
                <th className="py-2 pr-3 font-semibold">Tipo</th>
                <th className="py-2 pr-3 font-semibold">Quantidade</th>
                <th className="py-2 pr-3 font-semibold">Em uso agora</th>
                <th className="py-2 pr-3 font-semibold">Próximas reservas</th>
                <th className="py-2 pr-3 font-semibold">Situação</th>
                <th className="py-2 font-semibold"><span className="sr-only">Ações</span></th>
              </tr>
            </thead>
            <tbody>
              {recursosFiltrados.length === 0 && (
                <tr>
                  <td colSpan={7} className="py-6 text-center text-sm text-mute">
                    Nenhum recurso encontrado para "{busca.trim()}".
                  </td>
                </tr>
              )}
              {recursosFiltrados.map((recurso) =>
                editando?.id === recurso.id ? (
                  <tr key={recurso.id} className="border-b border-line align-top">
                    <td className="py-2 pr-3">
                      <input
                        aria-label="Nome do recurso"
                        value={editando.nome}
                        onChange={(e) => setEditando({ ...editando, nome: e.target.value })}
                        className="w-full rounded-lg bg-paper px-2 py-1.5 ring-1 ring-line"
                      />
                    </td>
                    <td className="py-2 pr-3">
                      <select
                        aria-label="Tipo do recurso"
                        value={editando.tipo}
                        onChange={(e) => setEditando({ ...editando, tipo: e.target.value })}
                        className="w-full rounded-lg bg-paper px-2 py-1.5 ring-1 ring-line"
                      >
                        {TIPOS.map((tipo) => (
                          <option key={tipo.valor} value={tipo.valor}>
                            {tipo.nome}
                          </option>
                        ))}
                      </select>
                    </td>
                    <td className="py-2 pr-3">
                      <input
                        aria-label="Quantidade"
                        type="number"
                        min="1"
                        max="999"
                        value={editando.quantidade}
                        onChange={(e) => setEditando({ ...editando, quantidade: e.target.value })}
                        className="w-20 rounded-lg bg-paper px-2 py-1.5 ring-1 ring-line"
                      />
                    </td>
                    <td className="py-2 pr-3 tabular-nums">{recurso.em_uso_agora ?? 0}</td>
                    <td className="py-2 pr-3 tabular-nums">{recurso.reservas_futuras ?? 0}</td>
                    <td className="py-2 pr-3">
                      <select
                        aria-label="Situação"
                        value={editando.status}
                        onChange={(e) => setEditando({ ...editando, status: e.target.value })}
                        className="w-full rounded-lg bg-paper px-2 py-1.5 ring-1 ring-line"
                      >
                        <option value="disponivel">Disponível</option>
                        <option value="manutencao">Em manutenção</option>
                      </select>
                    </td>
                    <td className="py-2">
                      <div className="flex gap-2">
                        <button
                          type="button"
                          onClick={salvarEdicao}
                          disabled={enviando}
                          className="rounded-lg bg-[#4f7a63] px-3 py-1.5 font-semibold text-white"
                        >
                          Salvar
                        </button>
                        <button
                          type="button"
                          onClick={() => setEditando(null)}
                          className="rounded-lg bg-paper px-3 py-1.5 font-semibold ring-1 ring-line"
                        >
                          Cancelar
                        </button>
                      </div>
                    </td>
                  </tr>
                ) : (
                  <Fragment key={recurso.id}>
                  <tr className="border-b border-line">
                    <td className="py-3 pr-3 font-semibold">{recurso.nome}</td>
                    <td className="py-3 pr-3">{nomeDoTipo(recurso.tipo)}</td>
                    <td className="py-3 pr-3 tabular-nums">{recurso.quantidade ?? 1}</td>
                    <td className="py-3 pr-3 tabular-nums">
                      {recurso.em_uso_agora ?? 0} de {recurso.quantidade ?? 1}
                    </td>
                    <td className="py-3 pr-3 tabular-nums">
                      {(recurso.reservas_futuras ?? 0) > 0 ? (
                        <button
                          type="button"
                          onClick={() => abrirReservas(recurso)}
                          aria-expanded={verReservas === recurso.id}
                          className="font-semibold text-[#4f7a63] underline underline-offset-2 hover:text-[#3f6550]"
                        >
                          {recurso.reservas_futuras} {verReservas === recurso.id ? "· fechar" : "· ver dias"}
                        </button>
                      ) : (
                        0
                      )}
                    </td>
                    <td className="py-3 pr-3">
                      {recurso.status === "manutencao" ? (
                        <span className="rounded-full bg-[#f7ead0] px-2.5 py-1 text-xs font-semibold text-[#74501a]">
                          Em manutenção
                        </span>
                      ) : (
                        <span className="rounded-full bg-[#e8f0eb] px-2.5 py-1 text-xs font-semibold text-[#3f6550]">
                          Disponível
                        </span>
                      )}
                    </td>
                    <td className="whitespace-nowrap py-3 text-right">
                      <button
                        type="button"
                        onClick={() => {
                          setMensagem(null);
                          setEditando({
                            id: recurso.id,
                            nome: recurso.nome,
                            tipo: TIPOS.some((t) => t.valor === String(recurso.tipo).toLowerCase())
                              ? String(recurso.tipo).toLowerCase()
                              : "equipamento",
                            quantidade: recurso.quantidade ?? 1,
                            status: recurso.status || "disponivel",
                          });
                        }}
                        className="rounded-lg bg-paper px-3 py-1.5 font-semibold ring-1 ring-line hover:bg-card"
                      >
                        Editar
                      </button>
                      <button
                        type="button"
                        onClick={() => excluir(recurso)}
                        disabled={enviando}
                        className={`ml-2 rounded-lg px-3 py-1.5 font-semibold ring-1 ${
                          confirmarExclusao === recurso.id
                            ? "bg-[#8f3f2c] text-white ring-[#8f3f2c]"
                            : "bg-paper text-[#8f3f2c] ring-line hover:bg-card"
                        }`}
                      >
                        {confirmarExclusao === recurso.id ? "Confirmar exclusão" : "Excluir"}
                      </button>
                    </td>
                  </tr>
                  {verReservas === recurso.id && (
                    <tr className="border-b border-line bg-paper/60">
                      <td colSpan={7} className="px-3 py-3">
                        <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-mute">
                          Próximas reservas de {recurso.nome}
                        </p>
                        {reservas.length === 0 ? (
                          <p className="text-sm text-mute">Carregando...</p>
                        ) : (
                          <ul className="space-y-1.5 text-sm">
                            {reservas.map((reserva, indice) => (
                              <li key={indice} className="flex flex-wrap gap-x-3">
                                <span className="font-semibold tabular-nums">
                                  {reserva.data.split("-").reverse().join("/")} · {reserva.hora_inicio}–{reserva.hora_fim}
                                </span>
                                <span>
                                  {reserva.disciplina || "Atividade"}
                                  {reserva.turma ? ` · ${reserva.turma}` : ""}
                                  {reserva.professor ? ` · ${reserva.professor}` : ""}
                                </span>
                              </li>
                            ))}
                          </ul>
                        )}
                      </td>
                    </tr>
                  )}
                  </Fragment>
                )
              )}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}

export default Recursos;
