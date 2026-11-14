import { useEffect, useRef, useState } from "react";

// Avisos e confirmacoes dentro da propria tela, no lugar do alert() e do confirm()
// do navegador (que mudam de aparencia em cada navegador e travam a pagina).
//
// Uso em qualquer arquivo:
//   avisar("Atividade cadastrada!")             -> aviso verde
//   avisar.erro("Recurso indisponivel")         -> aviso de erro
//   if (await confirmar({ texto: "Cancelar?" })) { ... }
//
// O componente <Avisos /> fica uma vez so na pagina e mostra tudo.

let ouvinte = null;
let proximoId = 1;

export function avisar(texto, tipo = "ok") {
  if (ouvinte) ouvinte({ tipo: "aviso", estilo: tipo, texto: String(texto || "") });
}

avisar.erro = (texto) => avisar(texto || "Algo deu errado. Tente novamente.", "erro");

export function confirmar({
  titulo = "Confirmar",
  texto = "",
  botao = "Confirmar",
  voltar = "Voltar",
  perigo = false,
} = {}) {
  return new Promise((resolve) => {
    if (!ouvinte) {
      resolve(false);
      return;
    }
    ouvinte({ tipo: "confirmar", titulo, texto, botao, voltar, perigo, resolve });
  });
}

function Avisos() {
  const [avisos, setAvisos] = useState([]);
  const [pergunta, setPergunta] = useState(null);
  const botaoVoltar = useRef(null);

  useEffect(() => {
    ouvinte = (evento) => {
      if (evento.tipo === "confirmar") {
        setPergunta(evento);
        return;
      }

      const id = proximoId++;
      setAvisos((lista) => [...lista.slice(-3), { ...evento, id }]);
      // erro fica um pouco mais na tela para dar tempo de ler
      setTimeout(
        () => setAvisos((lista) => lista.filter((aviso) => aviso.id !== id)),
        evento.estilo === "erro" ? 8000 : 4500
      );
    };

    return () => {
      ouvinte = null;
    };
  }, []);

  // Esc fecha a confirmacao como "Voltar"; o foco vai para o botao seguro
  useEffect(() => {
    if (!pergunta) return undefined;
    botaoVoltar.current?.focus();

    function tecla(e) {
      if (e.key === "Escape") responder(false);
    }

    window.addEventListener("keydown", tecla);
    return () => window.removeEventListener("keydown", tecla);
  }, [pergunta]);

  function responder(resposta) {
    if (pergunta) pergunta.resolve(resposta);
    setPergunta(null);
  }

  return (
    <>
      <div
        aria-live="polite"
        className="pointer-events-none fixed inset-x-4 bottom-4 z-[70] flex flex-col items-center gap-2 sm:inset-x-auto sm:right-6 sm:items-end"
      >
        {avisos.map((aviso) => (
          <div
            key={aviso.id}
            role={aviso.estilo === "erro" ? "alert" : "status"}
            className={`pointer-events-auto flex w-full max-w-sm items-start gap-3 rounded-2xl px-4 py-3 text-sm font-semibold ring-1 [box-shadow:0_18px_40px_-20px_rgba(40,36,28,.55)] animate-[rise_.35s_cubic-bezier(.32,.72,0,1)_both] ${
              aviso.estilo === "erro"
                ? "bg-[#fbf1ee] text-[#8f3f2c] ring-[#ecd2c9]"
                : "bg-[#e8f0eb] text-[#3f6550] ring-[#c7dccf]"
            }`}
          >
            <span aria-hidden="true" className="mt-px text-base leading-none">
              {aviso.estilo === "erro" ? "!" : "✓"}
            </span>
            <p className="min-w-0 flex-1 leading-snug">{aviso.texto}</p>
            <button
              type="button"
              onClick={() => setAvisos((lista) => lista.filter((item) => item.id !== aviso.id))}
              aria-label="Fechar aviso"
              className="-mr-1 rounded-md px-1.5 text-base leading-none opacity-60 hover:opacity-100"
            >
              ×
            </button>
          </div>
        ))}
      </div>

      {pergunta && (
        <div
          className="fixed inset-0 z-[80] flex items-center justify-center bg-black/35 p-4"
          onClick={() => responder(false)}
        >
          <div
            role="alertdialog"
            aria-modal="true"
            aria-labelledby="confirmar-titulo"
            aria-describedby="confirmar-texto"
            onClick={(e) => e.stopPropagation()}
            className="w-full max-w-md rounded-[24px] bg-card p-6 ring-1 ring-line [box-shadow:0_24px_50px_-24px_rgba(40,36,28,.6)] animate-[pop_.3s_cubic-bezier(.32,.72,0,1)_both]"
          >
            <h2 id="confirmar-titulo" className="text-lg font-bold">
              {pergunta.titulo}
            </h2>
            <p id="confirmar-texto" className="mt-2 whitespace-pre-line text-sm leading-relaxed text-ink/80">
              {pergunta.texto}
            </p>

            <div className="mt-6 flex flex-col-reverse gap-2 sm:flex-row sm:justify-end">
              <button
                ref={botaoVoltar}
                type="button"
                onClick={() => responder(false)}
                className="rounded-xl bg-paper px-4 py-2.5 text-sm font-semibold ring-1 ring-line hover:bg-card"
              >
                {pergunta.voltar}
              </button>
              <button
                type="button"
                onClick={() => responder(true)}
                className={`rounded-xl px-4 py-2.5 text-sm font-semibold text-white ${
                  pergunta.perigo ? "bg-[#a24a33] hover:bg-[#8f3f2c]" : "bg-[#4f7a63] hover:bg-[#3f6550]"
                }`}
              >
                {pergunta.botao}
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}

export default Avisos;
