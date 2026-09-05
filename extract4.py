import json
import re

log_path = r"C:\Users\vishn\.gemini\antigravity-ide\brain\a5306237-dd81-4817-a390-16d7fcf21caf\.system_generated\logs\transcript_full.jsonl"

best_code = ""

with open(log_path, "r", encoding="utf-8") as f:
    text = f.read()
    
# Let's just find the big chunk of code!
matches = re.findall(r"(import React, { useState, useEffect } from 'react';.*?export default function App\(\) \{.*?\}\);?\s*\})", text, re.DOTALL)

for match in matches:
    if match.count("</div>") > 15:
        # We found a valid one! We want the earliest one (the original) or the one before the destructive edit.
        best_code = match
        break

if best_code:
    # Decode json escapes if they exist (they shouldn't if we matched literally, but maybe \n is escaped as literal backslash n?)
    if "\\n" in best_code and "\n" not in best_code:
        best_code = best_code.replace("\\n", "\n").replace("\\\"", "\"").replace("\\'", "'")
        
    with open(r"d:\coding\PROJECTS\rectify-ai\frontend\src\App.jsx", "w", encoding="utf-8") as f:
        f.write(best_code + "\n")
    print("Found it via regex!")
else:
    print("Still failed to find it")
