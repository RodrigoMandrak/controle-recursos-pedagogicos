// @lovable.dev/vite-tanstack-config already includes the following — do NOT add them manually
// or the app will break with duplicate plugins:
//   - TanStack devtools (dev-only, first), tanstackStart, viteReact, tailwindcss, tsConfigPaths,
//     nitro (build-only using cloudflare as a default target), VITE_* env injection, @ path alias,
//     React/TanStack dedupe, error logger plugins, and sandbox detection (port/host/strictPort).
// You can pass additional config via defineConfig({ vite: { ... }, etc... }) if needed.
import { defineConfig } from "@lovable.dev/vite-tanstack-config";

export default defineConfig({
  tanstackStart: {
    // Redirect TanStack Start's bundled server entry to src/server.ts (our SSR error wrapper).
    // nitro/vite builds from this
    server: { entry: "server" },
  },
  vite: {
    server: {
      // modo online (iniciar_online.bat): o navegador chama /api/... e o front
      // repassa para o back-end em localhost:5000. Rodando normal, isso nao e usado.
      proxy: {
        "/api": {
          // no servidor (Render) API_ORIGEM e o endereco do back-end hospedado
          target: process.env.API_ORIGEM || "http://localhost:5000",
          changeOrigin: true,
          rewrite: (caminho) => caminho.replace(/^\/api/, ""),
        },
      },
      // libera abrir o front por outro endereco (Render, tunel)
      allowedHosts: true,
      // no Render (variavel RENDER existe) desliga o recarregamento automatico (HMR):
      // ele tenta abrir uma conexao na porta 8080, que o Render nao deixa,
      // e a pagina fica presa em "Carregando..."
      hmr: process.env.RENDER ? false : undefined,
    },
  },
});
