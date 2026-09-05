import re

with open("main.go", "r", encoding="utf-8") as f:
    c = f.read()

# Strip out the broken part
c = re.sub(r'if rand\.Float32\(\) > 0\.5 \{\s*state\.IncrementHistoricalAttempts\(evt\.ID\)\s*state\.SetPreDebitNoticeSentAt\(evt\.ID, time\.Now\(\)\.Add\(-25 \* time\.Hour\)\)\s*\} // \?10\.00 to \?50\.00', '', c)

# Inject the new logic after the event creation
def replacement(m):
    return m.group(0) + """
				if rand.Float32() > 0.5 {
					state.IncrementHistoricalAttempts(evt.ID)
					state.SetPreDebitNoticeSentAt(evt.ID, time.Now().Add(-25 * time.Hour))
				}"""

c = re.sub(r'LTV:\s*1000000,\s*\}', replacement, c)

with open("main.go", "w", encoding="utf-8") as f:
    f.write(c)

