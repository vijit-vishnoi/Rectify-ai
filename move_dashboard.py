with open(r"d:\coding\PROJECTS\rectify-ai\frontend\src\App.jsx", "r", encoding="utf-8") as f:
    c = f.read()

start_marker = "        {/* BATCH DASHBOARD */}"
end_marker = "        </div>\n        </div>\n  \n        {/* LEDGER */}"

if start_marker in c and end_marker in c:
    start_idx = c.find(start_marker)
    end_idx = c.find(end_marker)
    
    # The extracted HTML is from start_marker to the first </div>
    batch_html = c[start_idx:end_idx]
    
    # We want to remove it from here.
    # The structure here is:
    # batch_html
    # </div> (closes col-span-12 mb-4 animated-border-wrapper)
    # </div> (closes the left column!)
    # {/* LEDGER */}
    
    # We remove batch_html and the closing div of the animated-border-wrapper, but keep the closing div of the left column.
    
    # Wait, in the string `batch_html`, the last </div> is actually part of `end_marker`.
    # Let's print exactly what's there to be safe.
