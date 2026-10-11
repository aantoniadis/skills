import {readFileSync} from 'node:fs';
import {renderMermaidSVG} from 'beautiful-mermaid';

const source = readFileSync(0, 'utf8');
// This renderer turns termination crosses into ordinary arrows; require an explicit rewrite or Mermaid.
if (/^\s*\S+\s*--?x\s*\S+\s*:/m.test(source)) throw new Error('Termination crosses are unsupported; use --diagram-renderer mermaid.');
const svg = renderMermaidSVG(source, {
  bg: '#eeebe3', fg: '#29333c', line: '#657680', accent: '#416b80',
  muted: '#52616a', surface: '#dce4e3', border: '#87969a',
  font: 'Manrope', padding: 32, transparent: true,
});
// The report already embeds its font; remote font imports would break portable output.
process.stdout.write(svg.replace(/[ \t]*@import\s+url\([^)]*\);?/g, ''));
