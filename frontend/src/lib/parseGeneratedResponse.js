// Split model output into explanations and independently usable code artifacts.
// Preserve incomplete fences so partial streams never look like finished files.
export function parseGeneratedResponse(value = '') {
  const text = typeof value === 'string' ? value : '';
  const fences = /```([^\n`]*)\n([\s\S]*?)(```|$)/g;
  const files = [];
  const prose = [];
  let end = 0;
  let match;
  while ((match = fences.exec(text)) !== null) {
    if (match.index > end) prose.push(text.slice(end, match.index));
    const header = match[1].trim().split(/\s+/).filter(Boolean);
    const language = (header[0] || 'text').replace(/[^a-z0-9+.#_-]/gi, '').slice(0, 25) || 'text';
    const rawName = (header.find(part => part.startsWith('filename=')) || '').replace(/^filename=/, '')
      || header.slice(1).find(part => /\.[a-z0-9]{1,8}$/i.test(part)) || '';
    const filename = rawName.replace(/[^a-z0-9._-]/gi, '').slice(0, 80);
    files.push({language, filename, code:match[2], incomplete:match[3] !== '```'});
    end = fences.lastIndex;
    if (!match[3]) break;
  }
  if (end < text.length) prose.push(text.slice(end));
  // Some small models omit Markdown fences. Only classify obviously code-like
  // standalone responses as code, never a mixed prose explanation.
  if (files.length === 0 && text.trim()) {
    const lines = text.trim().split('\n').filter(line => line.trim());
    const codeLines = lines.filter(line => /^\s*(?:from \w+ import |import \w+|def \w+|class \w+|async def |function \w+|const \w+|let \w+|#include\s*<|public class |fn \w+|package \w+|if\s*\(|for\s*\(|while\s*\(|return\b|[{}]|\w+\s*=\s*[^=]|\/\/|#\s*!)/.test(line)).length;
    if (lines.length >= 4 && codeLines / lines.length > 0.55) {
      return {explanation:'', files:[{language:'text', filename:'', code:text.trim(), incomplete:false}]};
    }
  }
  return {explanation:prose.join('').trim(), files};
}
