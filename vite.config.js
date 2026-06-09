import { defineConfig } from "vite";

export default defineConfig({
    root: "src",
    base: "./",

    build: {
        outDir: "../bundle",
        emptyOutDir: true,

        rollupOptions: {
            external: [
                "/static/anna-apps/_sdk/latest/index.js"
            ]
        }
    }
});