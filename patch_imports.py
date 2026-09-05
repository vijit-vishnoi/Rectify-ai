with open(r"d:\coding\PROJECTS\rectify-ai\backend\domain\models.go", "r", encoding="utf-8") as f:
    c = f.read()

c = c.replace('"crypto/sha256"', '')
c = c.replace('"encoding/hex"', '')
c = c.replace('"fmt"', '')

with open(r"d:\coding\PROJECTS\rectify-ai\backend\domain\models.go", "w", encoding="utf-8") as f:
    f.write(c)
