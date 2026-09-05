import json

log_path = r"C:\Users\vishn\.gemini\antigravity-ide\brain\a5306237-dd81-4817-a390-16d7fcf21caf\.system_generated\logs\transcript_full.jsonl"

found_call = False
app_code = ""

with open(log_path, "r", encoding="utf-8") as f:
    for line in f:
        data = json.loads(line.strip())
        if data.get("type") == "PLANNER_RESPONSE":
            for call in data.get("tool_calls", []):
                if call.get("tool_action") == "Reading entire App.jsx for accurate Python replacement":
                    found_call = True
        elif found_call and data.get("type") == "TOOL_RESPONSE":
            # This should be the tool response!
            output = data.get("content", "")
            # Wait, tool response content is the string representation. Let's parse it properly.
            if "The command exited with code 0." in output:
                parts = output.split("Output:\n", 1)
                if len(parts) == 2:
                    app_code = parts[1].strip()
                    break
            
if app_code:
    with open(r"d:\coding\PROJECTS\rectify-ai\frontend\src\App.jsx", "w", encoding="utf-8") as out_f:
        out_f.write(app_code + "\n")
    print("Successfully recovered App.jsx!")
else:
    print("Could not find it.")
