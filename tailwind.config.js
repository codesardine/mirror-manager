/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./src/templates/*.html"],
  plugins: [require("daisyui")],
  daisyui: {
    themes: ["forest"],
    base: true, 
    styled: true, 
    utils: true, 
  },
}

