with open(r"d:\coding\PROJECTS\rectify-ai\backend\domain\models.go", "r", encoding="utf-8") as f:
    c = f.read()

alias = """
func (m *MemoryState) HasValidPreDebitNotice(id string) bool {
	return m.HasEverSentPreDebitNotice(id)
}
"""
c += alias

with open(r"d:\coding\PROJECTS\rectify-ai\backend\domain\models.go", "w", encoding="utf-8") as f:
    f.write(c)
