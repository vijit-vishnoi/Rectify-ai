with open(r"d:\coding\PROJECTS\rectify-ai\backend\engine\guardrails.go", "r", encoding="utf-8") as f:
    c = f.read()

old_coldstart = """func (r ColdStartRule) Check(state *domain.MemoryState, evt domain.Event, action domain.Action) (bool, string) {
	if action == domain.ActionStop || action == domain.ActionSendPreDebitNotice || action == domain.ActionNudge || action == domain.ActionWait {
		return true, ""
	}"""

new_coldstart = """func (r ColdStartRule) Check(state *domain.MemoryState, evt domain.Event, action domain.Action) (bool, string) {
	if action == domain.ActionStop || action == domain.ActionSendPreDebitNotice || action == domain.ActionNudge || action == domain.ActionWait || action == domain.ActionSendDiscount5 || action == domain.ActionSendDiscount10 {
		return true, ""
	}"""

c = c.replace(old_coldstart, new_coldstart)

with open(r"d:\coding\PROJECTS\rectify-ai\backend\engine\guardrails.go", "w", encoding="utf-8") as f:
    f.write(c)
