const NAV_ITEMS = [
  { title: 'Overview', tab: 'overview', icon: 'overview' },
  { separator: true },
  { title: 'Cron Jobs', tab: 'cron', icon: 'cron' },
  { title: 'Sessions', tab: 'sessions', icon: 'sessions' },
  { separator: true },
  { title: 'MCP', tab: 'mcp', icon: 'mcp' },
  { title: 'Skills', tab: 'skills', icon: 'skills' },
  { title: 'Plugins', tab: 'plugins', icon: 'plugins' },
];

const VALID_TABS = NAV_ITEMS.flatMap((item) => {
  if (item.separator) return [];
  return [item.tab, ...(item.children || []).map(child => child.tab)].filter(Boolean);
});
const SIDEBAR_STORAGE_KEY = 'assistant-sidebar-expanded';

function renderIcon(name) {
  const icons = {
    overview: '<svg class="sidebar__item-icon" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true"><path d="M3 4a1 1 0 011-1h5v6H3V4zm8-1h5a1 1 0 011 1v3h-6V3zM3 11h6v6H4a1 1 0 01-1-1v-5zm8-2h6v7a1 1 0 01-1 1h-5V9z"/></svg>',
    cron: '<svg class="sidebar__item-icon" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true"><path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-12a1 1 0 10-2 0v4a1 1 0 00.293.707l2.5 2.5a1 1 0 001.414-1.414L11 9.586V6z" clip-rule="evenodd"/></svg>',
    sessions: '<svg class="sidebar__item-icon" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true"><path d="M13 6a3 3 0 11-6 0 3 3 0 016 0zM18 8a2 2 0 11-4 0 2 2 0 014 0zM14 15a4 4 0 00-8 0v1h8v-1zM6 8a2 2 0 11-4 0 2 2 0 014 0zM16 16v-1a5.972 5.972 0 00-.75-2.906A3.005 3.005 0 0119 15v1h-3zM4.75 12.094A5.973 5.973 0 004 15v1H1v-1a3 3 0 013.75-2.906z"/></svg>',
    mcp: '<svg class="sidebar__item-icon" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true"><path fill-rule="evenodd" d="M11.3 1.046A1 1 0 0112 2v5h4a1 1 0 01.82 1.573l-7 10A1 1 0 018 18v-5H4a1 1 0 01-.82-1.573l7-10a1 1 0 011.12-.38z" clip-rule="evenodd"/></svg>',
    skills: '<svg class="sidebar__item-icon" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true"><path fill-rule="evenodd" d="M6 2a1 1 0 00-1 1v1H4a2 2 0 00-2 2v2h16V6a2 2 0 00-2-2h-1V3a1 1 0 10-2 0v1H7V3a1 1 0 00-1-1zM18 10H2v4a2 2 0 002 2h12a2 2 0 002-2v-4z" clip-rule="evenodd"/></svg>',
    plugins: '<svg class="sidebar__item-icon" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true"><path d="M5 3a2 2 0 00-2 2v2h4V3H5zM9 3v4h4V3H9zM15 3v4h2V5a2 2 0 00-2-2zM17 9h-2v4h2V9zM13 13V9H9v4h4zM7 9H3v4h4V9zM3 15v0a2 2 0 002 2h2v-2H3zM9 17h4v-2H9v2zM15 17a2 2 0 002-2h-2v2z"/></svg>',
  };
  return icons[name] || '';
}

function renderSidebar() {
  const nav = document.getElementById('sidebar-nav');
  if (!nav) return;

  nav.innerHTML = NAV_ITEMS.map((item) => {
    if (item.separator) return '<div class="sidebar__separator"></div>';

    const children = item.children || [];
    const childMarkup = children.length > 0
      ? `<div class="sidebar__children">${children.map(child => `<a class="sidebar__child" href="#${child.tab}" data-sidebar-tab="${child.tab}">${child.title}</a>`).join('')}</div>`
      : '';

    return `
      <div class="sidebar__item-wrap" data-sidebar-tab="${item.tab}">
        <a class="sidebar__item" href="${item.tab === 'overview' ? '#' : `#${item.tab}`}" title="${item.title}" data-has-children="${children.length > 0}">
          ${renderIcon(item.icon)}
          <span class="sidebar__item-label">${item.title}</span>
        </a>
        ${childMarkup}
      </div>
    `;
  }).join('');
}

function hasTabContent(tabName) {
  return Boolean(document.querySelector(`#tab-${tabName}`));
}

function getDisplayTab(tabName) {
  if (hasTabContent(tabName)) return tabName;

  const parent = NAV_ITEMS.find(item => (item.children || []).some(child => child.tab === tabName));
  if (parent?.tab && hasTabContent(parent.tab)) return parent.tab;

  return 'overview';
}

function getStoredSidebarExpanded() {
  try {
    return localStorage.getItem(SIDEBAR_STORAGE_KEY) === 'true';
  } catch {
    return false;
  }
}

function storeSidebarExpanded(expanded) {
  try {
    localStorage.setItem(SIDEBAR_STORAGE_KEY, String(expanded));
  } catch {
    // Ignore blocked storage; navigation state still works for this session.
  }
}

function updateSidebarActive(tabName) {
  document.querySelectorAll('.sidebar__item-wrap').forEach((wrap) => {
    const childTabs = Array.from(wrap.querySelectorAll('.sidebar__child')).map(child => child.dataset.sidebarTab);
    const isActive = wrap.dataset.sidebarTab === tabName;
    const isChildActive = childTabs.includes(tabName);
    const item = wrap.querySelector('.sidebar__item');
    wrap.classList.toggle('sidebar__item-wrap--open', isActive || isChildActive);
    item?.classList.toggle('sidebar__item--active', isActive || isChildActive);
    if (isActive) {
      item?.setAttribute('aria-current', 'page');
    } else {
      item?.removeAttribute('aria-current');
    }
  });

  document.querySelectorAll('.sidebar__child').forEach((child) => {
    const isActive = child.dataset.sidebarTab === tabName;
    child.classList.toggle('sidebar__child--active', isActive);
    if (isActive) {
      child.setAttribute('aria-current', 'page');
    } else {
      child.removeAttribute('aria-current');
    }
  });
}

function initSidebarToggle() {
  const toggle = document.getElementById('sidebar-toggle');
  const expanded = getStoredSidebarExpanded();

  document.body.classList.toggle('sidebar-expanded', expanded);
  toggle?.setAttribute('aria-expanded', String(expanded));
  toggle?.setAttribute('aria-label', expanded ? '收起导航' : '展开导航');

  toggle?.addEventListener('click', () => {
    const nextExpanded = !document.body.classList.contains('sidebar-expanded');
    document.body.classList.toggle('sidebar-expanded', nextExpanded);
    storeSidebarExpanded(nextExpanded);
    toggle.setAttribute('aria-expanded', String(nextExpanded));
    toggle.setAttribute('aria-label', nextExpanded ? '收起导航' : '展开导航');
  });
}

export function switchTab(name, updateHash = true) {
  const tabName = VALID_TABS.includes(name) ? name : 'overview';
  const displayTab = getDisplayTab(tabName);
  const tabEl = document.querySelector(`#tab-${displayTab}`);

  document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
  tabEl?.classList.add('active');
  updateSidebarActive(tabName);
  if (updateHash) location.hash = tabName === 'overview' ? '' : tabName;
}

export function getTabFromHash() {
  const hash = location.hash.replace('#', '');
  return VALID_TABS.includes(hash) ? hash : 'overview';
}

export function initNavigation() {
  renderSidebar();
  initSidebarToggle();
  window.addEventListener('hashchange', () => switchTab(getTabFromHash(), false));
  switchTab(getTabFromHash(), false);
}
