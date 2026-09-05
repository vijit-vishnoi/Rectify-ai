import re
with open(r'd:\coding\PROJECTS\rectify-ai\frontend\vite.config.js', 'r', encoding='utf-8') as f:
    c = f.read()

target = """    proxy: {
      '/webhook': 'http://localhost:8080',
      '/ledger': 'http://localhost:8080'
    }"""

replacement = """    proxy: {
      '/webhook': 'http://localhost:8080',
      '/ledger': 'http://localhost:8080',
      '/batch': 'http://localhost:8080',
      '/metrics': 'http://localhost:8080'
    }"""

c = c.replace(target, replacement)

with open(r'd:\coding\PROJECTS\rectify-ai\frontend\vite.config.js', 'w', encoding='utf-8') as f:
    f.write(c)
