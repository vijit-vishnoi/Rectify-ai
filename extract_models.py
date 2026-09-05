import re

log_path = r"C:\Users\vishn\.gemini\antigravity-ide\brain\a5306237-dd81-4817-a390-16d7fcf21caf\.system_generated\logs\transcript_full.jsonl"

best_code = ""

with open(log_path, "r", encoding="utf-8") as f:
    text = f.read()

# We need the last `package domain` block before `func (m *MemoryState)` ends.
matches = re.findall(r"(package domain[\s\S]*?func \(m \*MemoryState\) TotalCost\(\) float64 \{[\s\S]*?\n\})", text)

for match in matches:
    if "IncrementHistoricalAttempts" in match:
        best_code = match

if not best_code and matches:
    best_code = matches[-1]

if best_code:
    if "\\n" in best_code and "\n" not in best_code:
        best_code = best_code.replace("\\n", "\n").replace("\\\"", "\"").replace("\\'", "'")
        
    with open(r"d:\coding\PROJECTS\rectify-ai\backend\domain\models.go", "w", encoding="utf-8") as f:
        f.write(best_code + "\n")
    print("Found and restored models.go!")
else:
    print("Could not find models.go. Dumping all package domain matches.")
    for m in re.findall(r"package domain[\s\S]{100}", text):
        print(m.replace("\n", " ")[:100])
