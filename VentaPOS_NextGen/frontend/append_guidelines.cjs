
const fs = require('fs');

let addition = '\n\n### 4. The 40px Overlap Paradox\n';
addition += 'Even with dynamic zoom handling, you might notice that when scrolling to the absolute bottom of the page, the table header disappears under the sticky toolbar.\n';
addition += '**Why?** Because the scrollHeight of the page includes bottom margins/paddings (e.g. mb-3 on the card or p-3 on the page-body). This extra height allows the page to scroll *further up* than the exact height of the table container, pushing the top of the container (and its sticky header) UNDERneath the .sticky-toolbar.\n';
addition += '**The Solution:** Subtract these margins (e.g. 40px) from the maxHeight calculation. This makes the container slightly shorter to absorb the margin scroll gap, preventing it from ever overlapping the sticky elements above it.\n';

const content = fs.readFileSync('TABLE_UX_GUIDELINES.md', 'utf8');
if (!content.includes('Overlap Paradox')) {
  fs.appendFileSync('TABLE_UX_GUIDELINES.md', addition);
}

