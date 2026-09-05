with open(r"d:\coding\PROJECTS\rectify-ai\frontend\src\App.jsx", "r", encoding="utf-8") as f:
    c = f.read()

start_marker = "        {/* BATCH DASHBOARD */}"
end_marker = "        {/* LEDGER */}"

start_idx = c.find(start_marker)
end_idx = c.find(end_marker)

# The chunk from start_marker to end_marker looks roughly like:
#         {/* BATCH DASHBOARD */}
#         <div className="col-span-12 mb-4 animated-border-wrapper">
#             ...
#         </div>
#         </div>  <-- closing the left column
#   
#         {/* LEDGER */}

chunk = c[start_idx:end_idx]

# I want to isolate just the BATCH DASHBOARD div and its children.
# I will find the last </div> before the end of the chunk (which closes the left column),
# and the </div> before that (which closes the animated-border-wrapper).
parts = chunk.rsplit("</div>", 2)
# parts[0] contains everything up to the inside of the dashboard
# parts[0] + "</div>" is the exact dashboard element!
# Let's verify.
batch_element = parts[0] + "</div>"

# Remove the batch_element from the original document
new_c = c.replace(batch_element, "")

# Now I need to inject it into the LEDGER column.
# Find where the LEDGER column starts:
#         {/* LEDGER */}
#         <div className="col-span-12 lg:col-span-9">

ledger_col = """        {/* LEDGER */}
        <div className="col-span-12 lg:col-span-9">"""

injection_idx = new_c.find(ledger_col) + len(ledger_col)

# I will create a flex-col wrapper for the right column to hold both dashboard and ledger.
# I also need to change the Batch Dashboard's outer classes a bit so it fits the new wide column nicely.
batch_element_wide = batch_element.replace('col-span-12 mb-4 animated-border-wrapper', 'w-full mb-6 shrink-0 animated-border-wrapper')
batch_element_wide = batch_element_wide.strip()

# Adjust the Ledger's wrapper. Currently it is:
# <div className="glass-panel rounded-xl shadow-xl flex flex-col h-[calc(100vh-140px)] relative overflow-hidden">
# I'll change the height to flex-1 so it takes up remaining space.
new_c = new_c.replace('h-[calc(100vh-140px)]', 'flex-1 min-h-[500px]')

# Inject the dashboard into the right column
injection = f"""
          <div className="flex flex-col h-[calc(100vh-80px)]">
            {batch_element_wide}
"""
new_c = new_c[:injection_idx] + injection + new_c[injection_idx:]

# But wait, since I wrapped it in a new div (`<div className="flex flex-col h-[calc(100vh-80px)]">`), 
# I need to close this new div at the end of the LEDGER column.
# The LEDGER column ends near the end of the file:
#         </div>
#       </div>
#     );
#   }
# I can just add an extra </div> before `</div>\n    );\n  }`
new_c = new_c.replace("      </div>\n    );\n  }", "      </div>\n      </div>\n    );\n  }")

with open(r"d:\coding\PROJECTS\rectify-ai\frontend\src\App.jsx", "w", encoding="utf-8") as f:
    f.write(new_c)

