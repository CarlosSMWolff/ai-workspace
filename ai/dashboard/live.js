let currentFile = null;
let refreshTimer = null;
let manifest = {
  home: 'index.md',
  refresh_seconds: 3,
  sections: []
};

const STATIC_FILES = [
  { label: 'Home', path: 'index.md' },
  { label: 'Project brief', path: 'project.md' },
  { label: 'Open questions', path: 'open-questions.md' },
  { label: 'Glossary', path: 'glossary.md' },
  { label: 'Conventions', path: 'conventions.md' }
];

const BROWSE_ROOTS = [
  { label: 'Sessions', path: 'sessions', depth: 3 },
  { label: 'Investigations', path: 'investigations', depth: 3 },
  { label: 'Literature', path: 'literature', depth: 2 },
  { label: 'Simulations', path: 'simulations', depth: 2 },
  { label: 'Code (dev)', path: 'code_dev', depth: 4 }
];

// Extensions that the workspace can display (Markdown rendered; the rest shown
// as a read-only source block). Used to decide which links navigate in-app.
const VIEWABLE_EXT = new Set([
  'md', 'markdown', 'txt', 'py', 'js', 'sh', 'ps1', 'yaml', 'yml',
  'toml', 'json', 'bib', 'cfg', 'ini', 'csv', 'tex', 'html', 'htm'
]);

const fileLabels = new Map();

function normalizePath(path) {
  return (path || '').trim().replace(/^\.?\//, '').replace(/\\/g, '/').replace(/\/+$/, '');
}

function extensionOf(path) {
  const base = path.split('/').pop() || '';
  const dot = base.lastIndexOf('.');
  return dot >= 0 ? base.slice(dot + 1).toLowerCase() : '';
}

function isMarkdown(path) {
  const ext = extensionOf(path);
  return ext === 'md' || ext === 'markdown';
}

// Absolute, root-relative URL for fetching raw file bytes. Must be absolute so
// it resolves correctly even when the page URL is a deep repository path.
function rawUrl(path) {
  const encoded = normalizePath(path).split('/').map(encodeURIComponent).join('/');
  return '/' + encoded + '?raw=1&t=' + Date.now();
}

// Pretty in-address-bar URL for a repository path.
function pageUrl(path) {
  return '/' + normalizePath(path).split('/').map(encodeURIComponent).join('/');
}

function basename(path) {
  const cleanPath = path.replace(/\/$/, '');
  return cleanPath.split('/').pop() || cleanPath;
}

function parentDirectory(path) {
  const index = path.lastIndexOf('/');
  return index >= 0 ? path.slice(0, index + 1) : '';
}

function titleForPath(path) {
  return fileLabels.get(path) || basename(path);
}

function escapeHtml(value) {
  return value
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&#39;');
}

// MathJax runs after marked, so Markdown would otherwise mangle math spans:
// `_` pairs become <em> (subscripts vanish), `*` becomes emphasis, and a line
// holding only `=`/`-`/`+` turns the previous line into a setext heading or list.
// We pull every math span out before marked.parse() and splice it back in
// afterwards, HTML-escaping only the entity characters (&, <, >) so the
// delimiters survive verbatim for MathJax to typeset.
function escapeMathEntities(value) {
  return value
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;');
}

function renderMarkdownWithMath(markdown) {
  const mathSpans = [];
  const stash = (match) => {
    mathSpans.push(match);
    return `MJXMATHPLACEHOLDER${mathSpans.length - 1}ENDMJX`;
  };

  // Display math first so the inline `$...$` pass cannot bite into `$$...$$`.
  const protectedSource = markdown
    .replace(/\$\$[\s\S]+?\$\$/g, stash)
    .replace(/\\\[[\s\S]+?\\\]/g, stash)
    .replace(/\$(?!\s)(?:[^\n$]|\\\$)+?\$/g, stash)
    .replace(/\\\([\s\S]+?\\\)/g, stash);

  const html = marked.parse(protectedSource);

  return html.replace(
    /MJXMATHPLACEHOLDER(\d+)ENDMJX/g,
    (_, index) => escapeMathEntities(mathSpans[Number(index)])
  );
}

// Non-Markdown text files: render as a read-only, fixed-format source block.
function renderSource(text, path) {
  const ext = extensionOf(path) || 'text';
  return (
    `<div class="source-doc">` +
    `<div class="source-meta">${escapeHtml(basename(path))} &middot; ${escapeHtml(ext)}</div>` +
    `<pre class="source-view"><code class="language-${escapeHtml(ext)}">${escapeHtml(text)}</code></pre>` +
    `</div>`
  );
}

async function loadManifest() {
  try {
    const response = await fetch('/dashboard/manifest.json?t=' + Date.now());
    if (response.ok) {
      manifest = { ...manifest, ...(await response.json()) };
    }
  } catch {
    // The dashboard can still run from the built-in defaults.
  }
}

function coreFiles() {
  const byPath = new Map();
  [...STATIC_FILES, ...(manifest.sections || [])].forEach((item) => {
    if (!item.path || !item.path.endsWith('.md')) return;
    const path = normalizePath(item.path);
    byPath.set(path, { type: 'file', label: item.label || basename(path), path });
  });
  return [...byPath.values()];
}

// Sidebar tree now comes from the server's JSON endpoint instead of crawling
// HTML directory listings.
async function fetchTree(path, depth) {
  try {
    const response = await fetch(
      `/__tree__?path=${encodeURIComponent(path)}&depth=${depth}&t=${Date.now()}`
    );
    if (!response.ok) return [];
    return await response.json();
  } catch {
    return [];
  }
}

function renderFileNode(node) {
  const item = document.createElement('li');

  if (node.type === 'directory') {
    const details = document.createElement('details');
    details.className = 'file-directory';
    details.open = true;

    const summary = document.createElement('summary');
    summary.textContent = node.label;
    details.append(summary);

    const list = document.createElement('ul');
    list.className = 'file-list';
    (node.children || []).forEach((child) => list.append(renderFileNode(child)));
    details.append(list);
    item.append(details);
    return item;
  }

  fileLabels.set(node.path, node.label);
  const button = document.createElement('button');
  button.className = 'file-row';
  button.type = 'button';
  button.dataset.filePath = node.path;
  button.title = node.path;
  button.textContent = node.label;
  item.append(button);
  return item;
}

function renderSection(label, nodes, isOpen = true) {
  const details = document.createElement('details');
  details.className = 'file-section';
  details.open = isOpen;

  const summary = document.createElement('summary');
  summary.textContent = label;
  details.append(summary);

  if (!nodes.length) {
    const empty = document.createElement('p');
    empty.className = 'empty-state';
    empty.textContent = 'No files found.';
    details.append(empty);
    return details;
  }

  const list = document.createElement('ul');
  list.className = 'file-list';
  nodes.forEach((node) => list.append(renderFileNode(node)));
  details.append(list);
  return details;
}

async function renderFileTree() {
  const fileTree = document.getElementById('file-tree');
  const fragment = document.createDocumentFragment();

  fragment.append(renderSection('Project', coreFiles(), true));

  const sections = await Promise.all(
    BROWSE_ROOTS.map(async (root) => ({
      label: root.label,
      nodes: await fetchTree(root.path, root.depth)
    }))
  );

  sections.forEach((section) => {
    fragment.append(renderSection(section.label, section.nodes, true));
  });

  fileTree.replaceChildren(fragment);
  setActiveFile(currentFile);
}

function setActiveFile(path) {
  document.querySelectorAll('.file-row.active').forEach((button) => {
    button.classList.remove('active');
  });

  if (!path) return;
  const active = document.querySelector(`.file-row[data-file-path="${CSS.escape(path)}"]`);
  if (active) active.classList.add('active');
}

// Resolve an in-document link (relative to the current file) to a repository
// path, for any viewable file type.
function resolveLocalLink(href, sourceFile) {
  if (!href || href.startsWith('http:') || href.startsWith('https:') || href.startsWith('mailto:')) {
    return null;
  }
  if (href.startsWith('#')) return null;

  const [targetPath, hash] = href.split('#');
  if (!targetPath) return null;
  if (!VIEWABLE_EXT.has(extensionOf(targetPath))) return null;

  const basePath = parentDirectory(sourceFile);
  const url = new URL(targetPath, window.location.origin + '/' + basePath);
  return {
    path: normalizePath(decodeURIComponent(url.pathname)),
    hash: hash || null
  };
}

function rewriteLocalLinks(root, sourceFile) {
  root.querySelectorAll('a[href]').forEach((link) => {
    const target = resolveLocalLink(link.getAttribute('href'), sourceFile);
    if (!target) return;

    link.setAttribute('href', pageUrl(target.path) + (target.hash ? '#' + target.hash : ''));
    link.addEventListener('click', (event) => {
      event.preventDefault();
      loadFile(target.path, { hash: target.hash });
    });
  });
}

function scrollToHash(hash) {
  if (!hash) return;
  const target = document.getElementById(hash);
  if (target) target.scrollIntoView({ block: 'start' });
}

async function loadFile(path, { push = true, hash = null } = {}) {
  const normalizedPath = normalizePath(path) || normalizePath(manifest.home || 'index.md');
  if (!normalizedPath) return;

  currentFile = normalizedPath;
  const content = document.getElementById('content');
  const currentFileEl = document.getElementById('current-file');
  const currentFileTitleEl = document.getElementById('current-file-title');
  const lastLoadedEl = document.getElementById('last-loaded');

  currentFileTitleEl.textContent = titleForPath(normalizedPath);
  currentFileEl.textContent = normalizedPath;
  setActiveFile(normalizedPath);

  // Update the address bar *before* writing content so that relative image
  // links in the rendered Markdown resolve against this file's directory.
  const url = pageUrl(normalizedPath) + (hash ? '#' + hash : '');
  if (push) {
    history.pushState({ path: normalizedPath }, '', url);
  } else {
    history.replaceState({ path: normalizedPath }, '', url);
  }

  try {
    const response = await fetch(rawUrl(normalizedPath));
    if (!response.ok) {
      throw new Error(`Could not load ${normalizedPath} (${response.status})`);
    }

    const text = await response.text();
    if (isMarkdown(normalizedPath)) {
      content.innerHTML = renderMarkdownWithMath(text);
      rewriteLocalLinks(content, normalizedPath);
      if (window.MathJax && MathJax.typesetPromise) {
        await MathJax.typesetPromise([content]);
      }
    } else {
      content.innerHTML = renderSource(text, normalizedPath);
    }

    scrollToHash(hash);
    lastLoadedEl.textContent = 'Loaded ' + new Date().toLocaleTimeString();
  } catch (error) {
    content.innerHTML = `<div class="error"><h1>Error</h1><p>${escapeHtml(error.message)}</p></div>`;
    lastLoadedEl.textContent = 'Load failed ' + new Date().toLocaleTimeString();
  }
}

function pathFromLocation() {
  const path = normalizePath(decodeURIComponent(window.location.pathname));
  // `/`, `/dashboard/` (the old entry URL) and the shell's own assets are not
  // content files -- fall back to the home document for any of them.
  if (!path || path === 'dashboard' || path.startsWith('dashboard/')) {
    return normalizePath(manifest.home || 'index.md');
  }
  return path;
}

function scheduleRefresh() {
  if (refreshTimer) clearInterval(refreshTimer);

  const delay = Math.max(1, Number(manifest.refresh_seconds) || 3) * 1000;
  refreshTimer = setInterval(() => {
    const autoRefresh = document.getElementById('auto-refresh');
    if (autoRefresh.checked && currentFile) {
      loadFile(currentFile, { push: false });
    }
  }, delay);
}

function collapsePanel() {
  document.querySelector('.app-shell').classList.add('panel-collapsed');
}

function expandPanel() {
  document.querySelector('.app-shell').classList.remove('panel-collapsed');
}

function shouldCollapseAfterSelection() {
  return window.matchMedia('(max-width: 980px)').matches;
}

document.addEventListener('DOMContentLoaded', async () => {
  const appShell = document.querySelector('.app-shell');
  const fileTree = document.getElementById('file-tree');
  const openPathForm = document.getElementById('open-path-form');

  if (shouldCollapseAfterSelection()) {
    appShell.classList.add('panel-collapsed');
  }

  document.getElementById('hide-panel').addEventListener('click', collapsePanel);
  document.getElementById('show-panel').addEventListener('click', expandPanel);

  fileTree.addEventListener('click', (event) => {
    const button = event.target.closest('button[data-file-path]');
    if (!button) return;

    loadFile(button.dataset.filePath);
    if (shouldCollapseAfterSelection()) collapsePanel();
  });

  openPathForm.addEventListener('submit', (event) => {
    event.preventDefault();
    const input = document.getElementById('file-input');
    const path = normalizePath(input.value);
    if (path) loadFile(path);
  });

  window.addEventListener('popstate', () => {
    loadFile(pathFromLocation(), { push: false });
  });

  await loadManifest();
  await renderFileTree();
  scheduleRefresh();
  loadFile(pathFromLocation(), { push: false });
});
