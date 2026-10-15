
const fs = require('fs');
let addition = '\n\n### 3. Solving the Zoom & Dynamic Wrapping Paradox (JS)\n';
addition += 'A common pitfall with maxHeight: calc(100vh - Xpx) is that it assumes X is constant.\n';
addition += 'However, if the user zooms the browser (or uses an internal document.body.style.zoom), or if the filters wrap to a new line on smaller screens, the height of the sticky elements above the table will change.\n';
addition += 'Additionally, zoom scaling introduces fractional pixels which breaks exact scrollTop === scrollHeight - clientHeight calculations.\n\n';
addition += '**The Solution:**\n';
addition += '1. **Dynamic Max Height**: Use ResizeObserver to measure the exact height of the Navbar + sticky-toolbar dynamically, and inject 	able.style.maxHeight directly.\n';
addition += '2. **Zoom-Tolerant Bottom Detection**: Use a 15px buffer to absorb any sub-pixel fractional rounding errors introduced by zooming.\n';
const content = fs.readFileSync('TABLE_UX_GUIDELINES.md', 'utf8');
if (!content.includes('Solving the Zoom')) {
  fs.appendFileSync('TABLE_UX_GUIDELINES.md', addition);
}

