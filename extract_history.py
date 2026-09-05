import json
import re

log_path = r"C:\Users\vishn\.gemini\antigravity-ide\brain\a5306237-dd81-4817-a390-16d7fcf21caf\.system_generated\logs\transcript_full.jsonl"

file_states = {
    "main.go": None,
    "models.go": None,
    "App.jsx": None
}

with open(log_path, "r", encoding="utf-8") as f:
    for line in f:
        try:
            entry = json.loads(line)
        except:
            continue
            
        if "tool_calls" in entry and entry["tool_calls"]:
            for tc in entry["tool_calls"]:
                tool_name = tc.get("name", "")
                args = tc.get("arguments", {})
                
                if tool_name in ["write_to_file", "replace_file_content", "default_api:write_to_file", "default_api:replace_file_content", "default_api:multi_replace_file_content"]:
                    target = args.get("TargetFile", "")
                    content = args.get("CodeContent", "")
                    
                    if not content and "ReplacementContent" in args:
                        # If it's a replace, this script is too simple to apply diffs correctly.
                        # I'll just print out when it was edited so I know if I have the full file.
                        pass
                    elif content:
                        if "main.go" in target:
                            file_states["main.go"] = content
                        elif "models.go" in target:
                            file_states["models.go"] = content
                        elif "App.jsx" in target:
                            file_states["App.jsx"] = content

        if "content" in entry and entry["content"] and "Implementation plan for Checkout drop-off recovery" in str(entry["content"]):
            print("Reached Checkout Drop-off Recovery plan, stopping.")
            break

for filename, content in file_states.items():
    if content:
        with open(filename, "w", encoding="utf-8") as out:
            out.write(content)
        print(f"Restored {filename}")
    else:
        print(f"Could not find a full write_to_file state for {filename}")
