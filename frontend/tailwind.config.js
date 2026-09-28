/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        // Terminal-ops palette: near-black panels, phosphor green, signal accents.
        ink: {
          950: "#040605",
          900: "#070a09",
          800: "#0c110f",
          700: "#121916",
          600: "#1a2420",
          500: "#243029",
          400: "#2f3d35",
          300: "#3f5046",
        },
        phosphor: {
          DEFAULT: "#39ff8b",
          soft: "#8affbd",
          dim: "#27b566",
          deep: "#0f4a2a",
        },
        // One hue per grader type + the AI mentor, so a chip's color is a
        // stable meaning across the whole app (always paired with a glyph).
        signal: {
          amber: "#ffb454", // flag graders, difficulty, warnings
          red: "#ff5c5c", // failures
          cyan: "#3fd0ff", // network graders / mitmproxy
          rose: "#ff7ab8", // frida graders / runtime hooks
          violet: "#c4a1ff", // AI mentor
        },
      },
      fontFamily: {
        mono: ["'JetBrains Mono'", "'Fira Code'", "ui-monospace", "monospace"],
        sans: ["'Inter'", "ui-sans-serif", "system-ui", "sans-serif"],
      },
      fontSize: {
        // Micro-label scale used by chips, eyebrows and console text.
        "2xs": ["0.625rem", { lineHeight: "0.875rem", letterSpacing: "0.08em" }],
        xs: ["0.75rem", { lineHeight: "1.125rem" }],
      },
      boxShadow: {
        btn: "0 0 0 1px rgba(57,255,139,0.35), 0 8px 20px -10px rgba(57,255,139,0.6)",
        "btn-hover": "0 0 0 1px rgba(57,255,139,0.5), 0 10px 28px -10px rgba(57,255,139,0.75)",
        panel: "inset 0 1px 0 rgba(255,255,255,0.035), 0 12px 32px -20px rgba(0,0,0,0.9)",
      },
      backgroundImage: {
        "panel-sheen": "linear-gradient(180deg, rgba(255,255,255,0.02) 0%, transparent 60%)",
        shimmer:
          "linear-gradient(90deg, rgba(255,255,255,0) 0%, rgba(255,255,255,0.05) 50%, rgba(255,255,255,0) 100%)",
      },
      keyframes: {
        shimmer: {
          "0%": { backgroundPosition: "-200% 0" },
          "100%": { backgroundPosition: "200% 0" },
        },
        rise: {
          from: { opacity: "0", transform: "translateY(6px)" },
          to: { opacity: "1", transform: "translateY(0)" },
        },
      },
      animation: {
        shimmer: "shimmer 1.8s linear infinite",
        rise: "rise 320ms ease-out both",
      },
    },
  },
  plugins: [],
};
