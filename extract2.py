import json
log_path = r"C:\Users\vishn\.gemini\antigravity-ide\brain\a5306237-dd81-4817-a390-16d7fcf21caf\.system_generated\logs\transcript_full.jsonl"

found_code = None

with open(log_path, "r", encoding="utf-8") as f:
    for line in f:
        try:
            data = json.loads(line.strip())
            # Search every string field
            s = json.dumps(data)
            if "export default function App() {" in s and "return (" in s and "batch_dashboard" not in s.lower():
                # this might be the content!
                # let's dig it out
                pass
        except:
            pass

# An easier way: just regex search the file for the raw text!
import re
with open(log_path, "r", encoding="utf-8") as f:
    content = f.read()

# We want to find the first large block of App.jsx in the output.
matches = re.findall(r"(import React,.*?export default function App\(\).*?\}\);?\s*\})", content, re.DOTALL)
if matches:
    # Get the longest match to ensure we get the full file and not a snippet
    best_match = max(matches, key=len)
    
    # We need to unescape it if it's JSON encoded
    # Actually if we matched it from raw JSON, it has \n and \" escaped.
    # Let's decode it safely.
    # To do that, we find the "output": "..." block that contains it.
