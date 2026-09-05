with open(r"d:\coding\PROJECTS\rectify-ai\backend\domain\models.go", "r", encoding="utf-8") as f:
    c = f.read()

c = c.replace("func (m *MemoryState) AddAtRisk(amount int64) {", "func (m *MemoryState) AddAtRisk(amount float64) {")
c = c.replace("m.totalAtRisk += float64(amount)", "m.totalAtRisk += amount")

c = c.replace("func (m *MemoryState) AddRecovered(amount int64) {", "func (m *MemoryState) AddRecovered(amount float64) {")
c = c.replace("m.totalRecovered += float64(amount)", "m.totalRecovered += amount")

c = c.replace("func (m *MemoryState) AddCost(cost int64) {", "func (m *MemoryState) AddCost(cost float64) {")
c = c.replace("m.totalCost += float64(cost)", "m.totalCost += cost")

with open(r"d:\coding\PROJECTS\rectify-ai\backend\domain\models.go", "w", encoding="utf-8") as f:
    f.write(c)

with open(r"d:\coding\PROJECTS\rectify-ai\backend\main.go", "r", encoding="utf-8") as f:
    c = f.read()

c = c.replace("state.AddAtRisk(evt.Amount)", "state.AddAtRisk(float64(evt.Amount))")
c = c.replace("state.AddCost(cost)", "state.AddCost(float64(cost))")
c = c.replace("state.AddRecovered(evt.Amount)", "state.AddRecovered(float64(evt.Amount))")
c = c.replace("state.AddRecovered(recovered)", "state.AddRecovered(float64(recovered))")

# Add sync import if missing
if '"sync"' not in c:
    c = c.replace('import (', 'import (\n\t"sync"')

with open(r"d:\coding\PROJECTS\rectify-ai\backend\main.go", "w", encoding="utf-8") as f:
    f.write(c)
