import re
with open(r'd:\coding\PROJECTS\rectify-ai\backend\domain\models.go', 'r', encoding='utf-8') as f:
    c = f.read()

new_struct = """type Event struct {
	ID         string    `json:"id"`
	Amount     int64     `json:"amount"`       
	ErrorCode  string    `json:"error_code"`
	OccurredAt time.Time `json:"created_at"`   
	LTV        int64     `json:"ltv,omitempty"`
	SimulateTrai bool    `json:"simulate_trai,omitempty"`
}"""

c = re.sub(r'type Event struct \{.*?SimulateTrai bool    json:"simulate_trai,omitempty"\n\}', new_struct, c, flags=re.DOTALL)

with open(r'd:\coding\PROJECTS\rectify-ai\backend\domain\models.go', 'w', encoding='utf-8') as f:
    f.write(c)
