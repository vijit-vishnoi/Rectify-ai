import json
import re

log_path = r"C:\Users\vishn\.gemini\antigravity-ide\brain\a5306237-dd81-4817-a390-16d7fcf21caf\.system_generated\logs\transcript_full.jsonl"

best_code = None

with open(log_path, "r", encoding="utf-8") as f:
    for line in f:
        try:
            data = json.loads(line.strip())
            # We look for TOOL_RESPONSE
            if data.get("type") == "TOOL_RESPONSE":
                content = data.get("content", "")
                if "export default function App" in content and "</div>" in content:
                    # Parse out the actual code. It usually follows "Output:\n" or "Stdout:\n"
                    parts = content.split("Output:\n")
                    if len(parts) > 1:
                        code = parts[-1].strip()
                        # Verify it has closing divs
                        if code.count("</div>") > 10:
                            best_code = code
                    parts2 = content.split("Stdout:\n")
                    if len(parts2) > 1:
                        code = parts2[-1].strip()
                        if code.count("</div>") > 10:
                            best_code = code
        except Exception as e:
            pass

if best_code:
    # Some extra cleanup if there are any trailing things
    best_code = re.sub(r"The command exited with code \d+\.", "", best_code)
    best_code = best_code.replace("Stderr:", "").strip()
    
    with open(r"d:\coding\PROJECTS\rectify-ai\frontend\src\App.jsx", "w", encoding="utf-8") as f:
        f.write(best_code + "\n")
    print("Successfully restored App.jsx!")
else:
    print("Failed to find valid App.jsx in logs")

