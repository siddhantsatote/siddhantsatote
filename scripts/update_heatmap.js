/**
 * Live Heatmap SVG Generator for GitHub Profile README (Current Year)
 * Fetches real-time contribution data for user and renders the current year contribution graph.
 */
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const USERNAME = process.env.GITHUB_USER || 'siddhantsatote';
const CURRENT_YEAR = new Date().getFullYear(); // 2026

const THEME_COLORS = {
  0: '#161b22',
  1: '#0e4429',
  2: '#006d32',
  3: '#26a641',
  4: '#39d353'
};

async function fetchContributions(username, year) {
  console.log(`📡 Fetching live contributions for ${username} (Year: ${year})...`);
  const url = `https://github-contributions-api.jogruber.de/v4/${username}?y=${year}`;
  const res = await fetch(url);
  if (!res.ok) {
    throw new Error(`Failed to fetch contributions: ${res.statusText}`);
  }
  return await res.json();
}

function renderHeatmapSVG(data, targetYear) {
  const contributions = data.contributions || [];
  if (contributions.length === 0) {
    throw new Error('No contribution data found');
  }

  const todayStr = new Date().toISOString().split('T')[0];

  // Align to Sunday start
  const firstDay = new Date(contributions[0].date);
  const firstDayOfWeek = firstDay.getUTCDay(); // 0 = Sun

  // Pad leading days if Jan 1 is not Sunday
  const paddedContributions = [];
  for (let p = 0; p < firstDayOfWeek; p++) {
    paddedContributions.push({
      date: '',
      count: 0,
      level: 0,
      isPadding: true
    });
  }
  paddedContributions.push(...contributions);

  const cellWidth = 11;
  const cellHeight = 11;
  const gap = 3;
  const colStep = cellWidth + gap; // 14px
  const rowStep = cellHeight + gap; // 14px
  const startX = 34;
  const startY = 20;

  const totalWeeks = Math.ceil(paddedContributions.length / 7);
  const svgWidth = startX + (totalWeeks * colStep) + 20;
  const svgHeight = 152;

  const monthNames = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
  const monthLabels = [];
  let lastMonth = -1;

  let cellRects = '';
  let animIndex = 0;

  paddedContributions.forEach((item, index) => {
    const weekIndex = Math.floor(index / 7);
    const dayOfWeek = index % 7; // 0 = Sun, 6 = Sat

    const x = startX + (weekIndex * colStep);
    const y = startY + (dayOfWeek * rowStep);

    if (item.isPadding) {
      return; // don't render leading padding cell
    }

    // Month label check on first row (Sunday)
    if (dayOfWeek === 0 && item.date) {
      const dt = new Date(item.date);
      const m = dt.getUTCMonth();
      if (m !== lastMonth) {
        monthLabels.push({ name: monthNames[m], x });
        lastMonth = m;
      }
    }

    const isFuture = item.date > todayStr;
    const level = isFuture ? 0 : (item.level || 0);
    const color = THEME_COLORS[level] || THEME_COLORS[0];
    const delay = (animIndex * 0.0025).toFixed(3);
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
    const data = await fetchContributions(USERNAME, CURRENT_YEAR);
    const svg = renderHeatmapSVG(data, CURRENT_YEAR);
    const outputPath = path.join(__dirname, '..', 'contrib-heatmap.svg');
    fs.writeFileSync(outputPath, svg, 'utf-8');
    console.log(`✅ Successfully updated ${outputPath} with ${CURRENT_YEAR} live contributions!`);
  } catch (err) {
    console.error('Error generating heatmap SVG:', err);
    process.exit(1);
  }
}

main();
