import re

# 1. Update models.go
with open(r'd:\coding\PROJECTS\rectify-ai\backend\domain\models.go', 'r') as f:
    c = f.read()

c = c.replace('LTV        int64     json:"ltv,omitempty"\n}', 'LTV        int64     json:"ltv,omitempty"\n\tSimulateTrai bool    json:"simulate_trai,omitempty"\n}')

with open(r'd:\coding\PROJECTS\rectify-ai\backend\domain\models.go', 'w') as f:
    f.write(c)

# 2. Update guardrails.go
with open(r'd:\coding\PROJECTS\rectify-ai\backend\engine\guardrails.go', 'r') as f:
    c = f.read()

new_trai_rule = '''func (r TRAIQuietHoursRule) Check(state *domain.MemoryState, evt domain.Event, action domain.Action) (bool, string) {
	if action != domain.ActionNudge {
		return true, ""
	}

	loc, err := time.LoadLocation("Asia/Kolkata")
	if err != nil {
		return false, "timezone_load_error"
	}

	hour := time.Now().In(loc).Hour()
	if evt.SimulateTrai {
		hour = 22 // Force quiet hours
	}'''

c = re.sub(r'func \(r TRAIQuietHoursRule\) Check.*?hour := istTime\.Hour\(\)', new_trai_rule, c, flags=re.DOTALL)

with open(r'd:\coding\PROJECTS\rectify-ai\backend\engine\guardrails.go', 'w') as f:
    f.write(c)

# 3. Update main.go
with open(r'd:\coding\PROJECTS\rectify-ai\backend\main.go', 'r') as f:
    c = f.read()

# Update ShadowModeEnabled
c = c.replace('var ShadowModeEnabled = false', 'var ShadowModeEnabled = os.Getenv("SHADOW_MODE") == "true"')

# Update mapping in webhook
evt_struct = '''		evt := domain.Event{
			ID:         entity.ID,
			Amount:     entity.Amount,
			ErrorCode:  entity.ErrorCode,
			OccurredAt: time.Unix(entity.CreatedAt, 0),
			LTV:        1000000, 
			SimulateTrai: payload.SimulateTrai,
		}'''

c = re.sub(r'evt := domain\.Event\{.*?LTV:\s*1000000,\s*\}', evt_struct, c, flags=re.DOTALL)

with open(r'd:\coding\PROJECTS\rectify-ai\backend\main.go', 'w') as f:
    f.write(c)

