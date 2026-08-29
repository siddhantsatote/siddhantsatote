/**
 * Live Heatmap SVG Generator for GitHub Profile README
 * Fetches real-time contribution data for user and renders an animated SVG contribution graph.
 */
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const USERNAME = process.env.GITHUB_USER || 'siddhantsatote';

const THEME_COLORS = {
  0: '#161b22',
  1: '#0e4429',
  2: '#006d32',
  3: '#26a641',
  4: '#39d353'
};

async function fetchContributions(username) {
  console.log(`📡 Fetching live contributions for ${username}...`);
  const url = `https://github-contributions-api.jogruber.de/v4/${username}?y=last`;
  const res = await fetch(url);
  if (!res.ok) {
    throw new Error(`Failed to fetch contributions: ${res.statusText}`);
  }
  return await res.json();
}

function renderHeatmapSVG(data) {
  const contributions = data.contributions || [];
  if (contributions.length === 0) {
    throw new Error('No contribution data found');
  }

  // Width & dimensions matching the original profile theme
  const cellWidth = 11;
  const cellHeight = 11;
  const gap = 3;
  const colStep = cellWidth + gap; // 14px
  const rowStep = cellHeight + gap; // 14px
  const startX = 34;
  const startY = 20;

  // 52 or 53 weeks
  const totalDays = contributions.length;
  const totalWeeks = Math.ceil(totalDays / 7);
  const svgWidth = startX + (totalWeeks * colStep) + 20;
  const svgHeight = 152;

  const monthNames = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
  const monthLabels = [];
  let lastMonth = -1;

  let cellRects = '';
  let animIndex = 0;

  contributions.forEach((item, index) => {
    const weekIndex = Math.floor(index / 7);
    const dayOfWeek = index % 7; // 0 = Sun, 6 = Sat

    const x = startX + (weekIndex * colStep);
    const y = startY + (dayOfWeek * rowStep);

    // Month label check on first row (Sunday)
    if (dayOfWeek === 0) {
      const dt = new Date(item.date);
      const m = dt.getUTCMonth();
      if (m !== lastMonth) {
        monthLabels.push({ name: monthNames[m], x });
        lastMonth = m;
      }
    }

    const color = THEME_COLORS[item.level] || THEME_COLORS[0];
    const delay = (animIndex * 0.003).toFixed(3);
    const countText = item.count === 1 ? '1 contribution' : `${item.count} contributions`;

    cellRects += `<rect x="${x}" y="${startY - 6}" width="${cellWidth}" height="${cellHeight}" rx="2.5" fill="${color}" opacity="0">
<title>${countText} on ${item.date}</title>
<animate attributeName="opacity" from="0" to="1" begin="${delay}s" dur="0.35s" fill="freeze"/>
<animate attributeName="y" from="${startY - 6}" to="${y}" begin="${delay}s" dur="0.35s" fill="freeze" calcMode="spline" keySplines="0.25 0.1 0.25 1"/>
</rect>\n`;

    animIndex++;
  });

  const monthSvgText = monthLabels.map(m => 
    `<text x="${m.x}" y="13" font-family="monospace" font-size="10" fill="#7d8590">${m.name}</text>`
  ).join('\n');

  const daySvgText = `
<text x="0" y="43" font-family="monospace" font-size="10" fill="#7d8590">Mon</text>
<text x="0" y="71" font-family="monospace" font-size="10" fill="#7d8590">Wed</text>
<text x="0" y="99" font-family="monospace" font-size="10" fill="#7d8590">Fri</text>
`;

  return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${svgWidth} ${svgHeight}" width="${svgWidth}" height="${svgHeight}">
<rect width="100%" height="100%" fill="transparent"/>
${monthSvgText}
${daySvgText}
${cellRects}
</svg>`;
}

async function main() {
  try {
    const data = await fetchContributions(USERNAME);
    const svg = renderHeatmapSVG(data);
    const outputPath = path.join(__dirname, '..', 'contrib-heatmap.svg');
    fs.writeFileSync(outputPath, svg, 'utf-8');
    console.log(`✅ Successfully updated ${outputPath} with live GitHub contributions!`);
  } catch (err) {
    console.error('Error generating heatmap SVG:', err);
    process.exit(1);
  }
}

main();
