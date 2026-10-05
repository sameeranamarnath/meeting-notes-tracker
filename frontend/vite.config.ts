import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// https://vitejs.dev/config/
export default defineConfig({
  // Base path to deploy to GitHub Pages
  base: "/meeting-notes-tracker/",
  plugins: [react()],
});

