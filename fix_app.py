import re

with open(r'd:\coding\PROJECTS\rectify-ai\frontend\src\App.jsx', 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_lines = []
skip = False
for i in range(len(lines)):
    if 'const [traiQuietHours, setTraiQuietHours] = useState(false);' in lines[i]:
        if not skip:
            new_lines.append(lines[i])
            skip = True # skip the next occurrence
    else:
        new_lines.append(lines[i])

with open(r'd:\coding\PROJECTS\rectify-ai\frontend\src\App.jsx', 'w', encoding='utf-8') as f:
    f.writelines(new_lines)
