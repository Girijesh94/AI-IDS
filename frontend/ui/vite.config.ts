import { defineConfig } from "vite";
export default defineConfig({
  base: "/static/dist/",
  build: {
    outDir: "../dist",
    emptyOutDir: true,
    rollupOptions: {
      input: "src/main.tsx",
      output: {
        entryFileNames: "assets/app.js",
        assetFileNames: (asset) =>
          asset.names.some((n) => n.endsWith(".css"))
            ? "assets/app.css"
            : "assets/[name]-[hash][extname]",
      },
    },
  },
  server: {
    proxy: {
      "/api": "http://127.0.0.1:5000",
      "/static": "http://127.0.0.1:5000",
    },
  },
});
