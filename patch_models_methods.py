with open(r"d:\coding\PROJECTS\rectify-ai\backend\domain\models.go", "r", encoding="utf-8") as f:
    c = f.read()

c = c.replace("func (m *MemoryState) GetHistoricalAttempts(id string) int {", "func (m *MemoryState) GetDebitAttempts(id string) int {")
c = c.replace("func (m *MemoryState) HasSettled(id string) bool {", "func (m *MemoryState) IsSettled(id string) bool {")
c = c.replace("func (m *MemoryState) HasValidPreDebitNotice(id string) bool {", "func (m *MemoryState) HasEverSentPreDebitNotice(id string) bool {")
c = c.replace("func (m *MemoryState) HasActivePromise(id string) bool {", "func (m *MemoryState) HasActivePromiseToPay(id string) bool {")

# Also add GetHistoricalAttemptCount if it's different from GetDebitAttempts? Wait, they are probably the same. Let's alias it.
alias = """
func (m *MemoryState) GetHistoricalAttemptCount(id string) int {
	return m.GetDebitAttempts(id)
}
"""
c += alias

with open(r"d:\coding\PROJECTS\rectify-ai\backend\domain\models.go", "w", encoding="utf-8") as f:
    f.write(c)
