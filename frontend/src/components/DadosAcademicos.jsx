import { useState } from "react";
import { avisar, confirmar } from "./Avisos";

// Tela do coordenador para cadastrar, renomear e excluir
// disciplinas, turmas e professores (as opcoes do formulario de atividade).
//
// Regras (conferidas no back-end):
// - nao aceita dois nomes iguais;
// - nao exclui se ainda houver atividade marcada para o futuro;
// - se ja teve aula, fica arquivado (some das listas, mas o historico continua certo);
// - professor com conta de acesso nao sai da lista enquanto a conta existir.

const CAMPO =
  "w-full rounded-xl bg-paper px-3.5 py-2.5 text-sm text-ink ring-1 ring-line focus:outline-none focus:ring-2 focus:ring-green";

const LISTAS = [
  { tabela: "disciplinas", titulo: "Disciplinas", um: "disciplina", exemplo: "Ex.: Robótica" },
  { tabela: "turmas", titulo: "Turmas", um: "turma", exemplo: "Ex.: 9º ano C" },
  { tabela: "professores", titulo: "Professores", um: "professor", exemplo: "Ex.: Prof. Joana Lima" },
];

const normalizar = (texto) =>
  String(texto || "").normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase();

function Lista({ api, config, itens, aoAlterar }) {
  const [novo, setNovo] = useState("");
  const [busca, setBusca] = useState("");
  const [editando, setEditando] = useState(null);
  const [enviando, setEnviando] = useState(false);

  async function chamar(url, metodo, corpo) {
    setEnviando(true);
    try {
      const resposta = await fetch(url, {
        method: metodo,
        credentials: "include",
        headers: { "Content-Type": "application/json" },
        body: corpo ? JSON.stringify(corpo) : undefined,
      });
      const resultado = await resposta.json();

      if (!resposta.ok) {
        avisar.erro(resultado.erro);
        return false;
      }

      avisar(resultado.mensagem);
      aoAlterar();
      return true;
    } catch {
      avisar.erro("Erro ao conectar com o servidor.");
      return false;
    } finally {
      setEnviando(false);
    }
  }

  async function cadastrar(e) {
    e.preventDefault();
    const nome = novo.trim();
    if (!nome) return;
    if (await chamar(`${api}/${config.tabela}`, "POST", { nome })) setNovo("");
  }

  async function salvar(e) {
    e.preventDefault();
    const nome = editando.nome.trim();
    if (!nome) return;
    if (await chamar(`${api}/${config.tabela}/${editando.id}`, "PUT", { nome })) setEditando(null);
  }

  async function excluir(item) {
    const certo = await confirmar({
      titulo: `Excluir ${config.um}?`,
      texto:
        `"${item.nome}" vai sair da lista do formulário de atividades.\n` +
        "Se já teve aula, ela continua no histórico. Se ainda houver aula marcada, o sistema não deixa excluir.",
      botao: "Excluir",
      perigo: true,
    });
    if (certo) await chamar(`${api}/${config.tabela}/${item.id}`, "DELETE");
  }

  const filtrados = itens.filter((item) => normalizar(item.nome).includes(normalizar(busca.trim())));

  return (
    <section className="flex flex-col rounded-[24px] bg-card p-5 ring-1 ring-line [box-shadow:0_18px_40px_-28px_rgba(69,61,46,.4)]">
      <div className="mb-4 flex items-baseline justify-between">
        <h3 className="text-base font-semibold">{config.titulo}</h3>
        <span className="text-xs text-mute">{itens.length} cadastrad{config.um === "professor" ? "o" : "a"}{itens.length !== 1 ? "s" : ""}</span>
      </div>

      <form onSubmit={cadastrar} className="flex gap-2">
        <label className="sr-only" htmlFor={`novo-${config.tabela}`}>
          Nome {config.um === "professor" ? "do novo professor" : `da nova ${config.um}`}
        </label>
        <input
          id={`novo-${config.tabela}`}
          value={novo}
          onChange={(e) => setNovo(e.target.value)}
          placeholder={config.exemplo}
          maxLength={100}
          className={CAMPO}
        />
        <button
          type="submit"
          disabled={enviando || !novo.trim()}
          className="shrink-0 rounded-xl bg-[#4f7a63] px-4 py-2.5 text-sm font-semibold text-white disabled:opacity-40"
        >
          Adicionar
        </button>
      </form>

      {itens.length > 6 && (
        <input
          value={busca}
          onChange={(e) => setBusca(e.target.value)}
          placeholder={`Buscar ${config.um}...`}
          aria-label={`Buscar ${config.um}`}
          className={`${CAMPO} mt-3`}
        />
      )}

      <ul className="mt-4 max-h-[420px] space-y-2 overflow-y-auto pr-1">
        {filtrados.length === 0 && (
          <li className="rounded-xl bg-paper px-3 py-3 text-sm text-mute ring-1 ring-line">
            {itens.length === 0 ? "Nada cadastrado ainda." : "Nada encontrado."}
          </li>
        )}

        {filtrados.map((item) =>
          editando?.id === item.id ? (
            <li key={item.id}>
              <form onSubmit={salvar} className="rounded-xl bg-paper p-2 ring-1 ring-green">
                <input
                  autoFocus
                  value={editando.nome}
                  onChange={(e) => setEditando({ ...editando, nome: e.target.value })}
                  maxLength={100}
                  aria-label={`Novo nome de ${item.nome}`}
                  className={`${CAMPO} bg-card`}
                />
                <div className="mt-2 flex justify-end gap-2">
                  <button
                    type="button"
                    onClick={() => setEditando(null)}
                    className="rounded-lg px-3 py-1.5 text-sm font-semibold ring-1 ring-line"
                  >
                    Voltar
                  </button>
                  <button
                    type="submit"
                    disabled={enviando}
                    className="rounded-lg bg-[#4f7a63] px-3 py-1.5 text-sm font-semibold text-white disabled:opacity-40"
                  >
                    Salvar
                  </button>
                </div>
              </form>
            </li>
          ) : (
            <li
              key={item.id}
              className="flex items-center justify-between gap-2 rounded-xl bg-paper px-3 py-2 ring-1 ring-line"
            >
              <span className="min-w-0 truncate text-sm" title={item.nome}>{item.nome}</span>
              <span className="flex shrink-0 gap-1">
                <button
                  type="button"
                  onClick={() => setEditando({ id: item.id, nome: item.nome })}
                  className="rounded-lg px-2.5 py-1 text-xs font-semibold text-[#3f6550] hover:bg-card"
                >
                  Renomear
                </button>
                <button
                  type="button"
                  onClick={() => excluir(item)}
                  disabled={enviando}
                  className="rounded-lg px-2.5 py-1 text-xs font-semibold text-[#8f3f2c] hover:bg-card disabled:opacity-40"
                >
                  Excluir
                </button>
              </span>
            </li>
          )
        )}
      </ul>
    </section>
  );
}

function DadosAcademicos({ api, disciplinas, turmas, professores, aoAlterar }) {
  const dados = { disciplinas, turmas, professores };

  return (
    <div>
      <div className="mb-5">
        <h2 className="text-lg font-semibold">Dados acadêmicos</h2>
        <p className="mt-1 max-w-3xl text-sm text-mute">
          São as opções do formulário de atividade. O que já teve aula não é apagado de verdade: sai da lista,
          mas continua no histórico e no dashboard. Professores que criam conta e são aprovados entram aqui sozinhos.
        </p>
      </div>

      <div className="grid gap-5 lg:grid-cols-3">
        {LISTAS.map((config) => (
          <Lista key={config.tabela} api={api} config={config} itens={dados[config.tabela] || []} aoAlterar={aoAlterar} />
        ))}
      </div>
    </div>
  );
}

export default DadosAcademicos;
