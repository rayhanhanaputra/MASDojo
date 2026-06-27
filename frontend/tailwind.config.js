/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        // Terminal-ops palette: near-black panels, phosphor green, signal amber.
        ink: {
          900: "#070a09",
          800: "#0c110f",
          700: "#121916",
          600: "#1a2420",
          500: "#243029",
        },
        phosphor: {
          DEFAULT: "#39ff8b",
          dim: "#1f9e57",
        },
        signal: {
          amber: "#ffb454",
          red: "#ff5c5c",
          cyan: "#3fd0ff",
        },
      },
      fontFamily: {
        mono: ["'JetBrains Mono'", "'Fira Code'", "ui-monospace", "monospace"],
        sans: ["'Inter'", "ui-sans-serif", "system-ui", "sans-serif"],
      },
      boxShadow: {
        glow: "0 0 0 1px rgba(57,255,139,0.15), 0 0 24px -8px rgba(57,255,139,0.25)",
      },
    },
  },
  plugins: [],
};
