import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{ts,tsx}",
    "./components/**/*.{ts,tsx}",
    "./lib/**/*.{ts,tsx}"
  ],
  theme: {
    extend: {
      colors: {
        ivory: "#f8f5ef",
        blush: "#ead9dc",
        gold: "#c8a977",
        ink: "#10211d",
        mist: "#d8d9d4",
        amethyst: "#8670a6"
      },
      boxShadow: {
        soft: "0 10px 40px rgba(16, 33, 29, 0.08)"
      },
      fontFamily: {
        sans: ["Avenir Next", "PingFang SC", "Microsoft YaHei", "sans-serif"],
        serif: ["Cormorant Garamond", "STSong", "serif"]
      },
      backgroundImage: {
        "hero-glow": "radial-gradient(circle at 20% 30%, rgba(200,169,119,0.22), transparent 38%), radial-gradient(circle at 80% 20%, rgba(134,112,166,0.2), transparent 40%), linear-gradient(135deg, #f8f5ef 0%, #f5f1ea 44%, #e9ece7 100%)"
      }
    }
  },
  plugins: []
};

export default config;
