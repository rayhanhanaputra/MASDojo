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
        glow: "0 0 0 1px rgba(57,255,139,0.18), 0 0 28px -8px rgba(57,255,139,0.35)",
        "glow-lg":
          "0 0 0 1px rgba(57,255,139,0.28), 0 0 60px -12px rgba(57,255,139,0.45), 0 24px 48px -24px rgba(0,0,0,0.8)",
        "glow-red": "0 0 0 1px rgba(255,92,92,0.25), 0 0 28px -8px rgba(255,92,92,0.35)",
        btn: "0 0 0 1px rgba(57,255,139,0.35), 0 8px 20px -10px rgba(57,255,139,0.6)",
        "btn-hover": "0 0 0 1px rgba(57,255,139,0.5), 0 10px 28px -10px rgba(57,255,139,0.75)",
        panel: "inset 0 1px 0 rgba(255,255,255,0.035), 0 12px 32px -20px rgba(0,0,0,0.9)",
        hero: "inset 0 1px 0 rgba(138,255,189,0.12), 0 30px 60px -30px rgba(0,0,0,0.9)",
        console: "inset 0 0 60px -20px rgba(57,255,139,0.18)",
      },
      backgroundImage: {
        "hero-glow":
          "radial-gradient(120% 140% at 0% 0%, rgba(57,255,139,0.14) 0%, rgba(57,255,139,0.04) 40%, transparent 70%)",
        "panel-sheen": "linear-gradient(180deg, rgba(255,255,255,0.02) 0%, transparent 60%)",
        shimmer:
          "linear-gradient(90deg, rgba(255,255,255,0) 0%, rgba(255,255,255,0.05) 50%, rgba(255,255,255,0) 100%)",
      },
      keyframes: {
        shimmer: {
          "0%": { backgroundPosition: "-200% 0" },
          "100%": { backgroundPosition: "200% 0" },
        },
        blink: {
          "0%, 100%": { opacity: "1" },
          "50%": { opacity: "0" },
        },
        rise: {
          from: { opacity: "0", transform: "translateY(6px)" },
          to: { opacity: "1", transform: "translateY(0)" },
        },
        stamp: {
          "0%": { opacity: "0", transform: "scale(1.5) rotate(-8deg)" },
          "65%": { opacity: "1", transform: "scale(0.96) rotate(-3deg)" },
          "100%": { opacity: "1", transform: "scale(1) rotate(-3deg)" },
        },
        scan: {
          from: { transform: "translateY(-100%)" },
          to: { transform: "translateY(100%)" },
        },
        pulseRing: {
          "0%": { boxShadow: "0 0 0 0 rgba(57,255,139,0.5)" },
          "100%": { boxShadow: "0 0 0 10px rgba(57,255,139,0)" },
        },
      },
      animation: {
        shimmer: "shimmer 1.8s linear infinite",
        blink: "blink 1.1s steps(2, start) infinite",
        rise: "rise 320ms ease-out both",
        stamp: "stamp 480ms cubic-bezier(0.2, 0.9, 0.3, 1.15) both",
        scan: "scan 7s linear infinite",
        "pulse-ring": "pulseRing 1.8s ease-out infinite",
      },
    },
  },
  plugins: [],
};
