module.exports = {
  plugins: {
      'postcss-import': {},
      'tailwindcss/nesting': 'postcss-nesting',
      tailwindcss: {},
      autoprefixer: {},
      'cssnano': {
        "preset": [
            "default", {"discardComments": {"removeAll": true}}
        ],
      }
  }
}

