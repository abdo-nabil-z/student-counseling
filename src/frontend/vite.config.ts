import { defineConfig } from "vite";
import react, { reactCompilerPreset } from "@vitejs/plugin-react";
import babel from "@rolldown/plugin-babel";

// https://vite.dev/config/
export default defineConfig({
  plugins: [react(), babel({ presets: [reactCompilerPreset()] })],
  server: {
    host: true, // binds to 0.0.0.0 instead of localhost
    port: 5173,
    proxy: {
      "/api": "http://backend:8000",
    },
  },
});
