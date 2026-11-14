import { useState } from "react";
import { avisar } from "./Avisos";

// Janela para alterar uma atividade que ainda nao aconteceu.
// O back-end confere de novo: data, horario, conflito de professor/turma
// e se os recursos ja reservados cabem no horario novo.

const CAMPO =
  "mt-1 w-full rounded-xl bg-paper px-3.5 py-2.5 text-sm font-normal normal-case tracking-normal text-ink ring-1 ring-line focus:outline-none focus:ring-2 focus:ring-green";
const ROTULO = "text-xs font-semibold uppercase tracking-wide text-mute";

const hora = (texto) => String(texto || "").slice(0, 5);

function EditarAtividade({ api, atividade, disciplinas, turmas, professores, souCoordenador, fechar, aoSalvar }) {
  const [form, setForm] = useState({
    disciplina_id: String(atividade.disciplinaId || ""),
    turma_id: String(atividade.turmaId || ""),
    professor_id: String(atividade.professorId || ""),
    data: atividade.data,
    hora_inicio: hora(atividade.horarioInicial),
    hora_fim: hora(atividade.horarioFinal),
    descricao: atividade.descricao || "",
  });
  const [erro, setErro] = useState("");
  const [enviando, setEnviando] = useState(false);

  const mudar = (e) => setForm({ ...form, [e.target.name]: e.target.value });

  async function salvar(e) {
    e.preventDefault();
    setErro("");

    if (form.hora_fim <= form.hora_inicio) {
      setErro("O horário final precisa ser depois do inicial.");
      return;
    }

    setEnviando(true);
    try {
      const resposta = await fetch(`${api}/atividades/${atividade.id}`, {
        method: "PUT",
        credentials: "include",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          ...form,
          disciplina_id: Number(form.disciplina_id),
          turma_id: Number(form.turma_id),
          professor_id: Number(form.professor_id),
        }),
      });
      const resultado = await resposta.json();

      if (!resposta.ok) {
        setErro(resultado.erro || "Não foi possível alterar a atividade.");
        return;
      }

      avisar("Atividade alterada.");
      aoSalvar();
      fechar();
    } catch {
      setErro("Erro ao conectar com o servidor.");
    } finally {
      setEnviando(false);
    }
  }

  // se a disciplina/turma/professor foi arquivado, ainda aparece aqui para a pessoa trocar
  const comAtual = (lista, id, nome) =>
    lista.some((item) => String(item.id) === String(id)) || !id ? lista : [{ id, nome: `${nome} (excluído)` }, ...lista];

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/35 p-4" onClick={fechar}>
      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby="editar-atividade-titulo"
        onClick={(e) => e.stopPropagation()}
        className="max-h-[90vh] w-full max-w-2xl overflow-y-auto rounded-[28px] bg-card p-6 ring-1 ring-line sm:p-8"
      >
        <div className="mb-5 flex items-start justify-between gap-4 border-b border-line pb-4">
          <div>
            <h2 id="editar-atividade-titulo" className="text-xl font-bold">
              Alterar atividade
            </h2>
            <p className="mt-1 text-sm text-mute">Os recursos reservados continuam na atividade.</p>
          </div>
          <button
            type="button"
            onClick={fechar}
            className="rounded-xl bg-paper px-3 py-2 text-sm font-semibold ring-1 ring-line"
          >
            Fechar
          </button>
        </div>

        <form onSubmit={salvar} className="grid gap-4 sm:grid-cols-2">
          <label className={ROTULO}>
            Disciplina
            <select name="disciplina_id" value={form.disciplina_id} onChange={mudar} className={CAMPO} required>
              {comAtual(disciplinas, atividade.disciplinaId, atividade.disciplina).map((item) => (
                <option key={item.id} value={item.id}>
                  {item.nome}
                </option>
              ))}
            </select>
          </label>

          <label className={ROTULO}>
            Turma
            <select name="turma_id" value={form.turma_id} onChange={mudar} className={CAMPO} required>
              {comAtual(turmas, atividade.turmaId, atividade.turma).map((item) => (
                <option key={item.id} value={item.id}>
                  {item.nome}
                </option>
              ))}
            </select>
          </label>

          <label className={`${ROTULO} sm:col-span-2`}>
            Professor
            <select
              name="professor_id"
              value={form.professor_id}
              onChange={mudar}
              disabled={!souCoordenador}
              className={`${CAMPO} disabled:opacity-70`}
              required
            >
              {comAtual(professores, atividade.professorId, atividade.professor).map((item) => (
                <option key={item.id} value={item.id}>
                  {item.nome}
                </option>
              ))}
            </select>
          </label>

          <label className={ROTULO}>
            Data
            <input type="date" name="data" value={form.data} onChange={mudar} className={CAMPO} required />
          </label>

          <div className="grid grid-cols-2 gap-3">
            <label className={ROTULO}>
              Início
              <input type="time" name="hora_inicio" value={form.hora_inicio} onChange={mudar} className={CAMPO} required />
            </label>
            <label className={ROTULO}>
              Fim
              <input type="time" name="hora_fim" value={form.hora_fim} onChange={mudar} className={CAMPO} required />
            </label>
          </div>

          <label className={`${ROTULO} sm:col-span-2`}>
            Descrição
            <textarea
              name="descricao"
              value={form.descricao}
              onChange={mudar}
              rows={3}
              maxLength={500}
              className={CAMPO}
            />
          </label>

          {erro && (
            <p role="alert" className="rounded-xl bg-paper px-3 py-2 text-sm font-semibold text-[#8f3f2c] ring-1 ring-line sm:col-span-2">
              {erro}
            </p>
          )}

          <div className="flex justify-end gap-2 sm:col-span-2">
            <button type="button" onClick={fechar} className="rounded-xl bg-paper px-4 py-2.5 text-sm font-semibold ring-1 ring-line">
              Voltar
            </button>
            <button
              type="submit"
              disabled={enviando}
              className="rounded-xl bg-[#4f7a63] px-4 py-2.5 text-sm font-semibold text-white disabled:opacity-40"
            >
              {enviando ? "Salvando..." : "Salvar alterações"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

export default EditarAtividade;
