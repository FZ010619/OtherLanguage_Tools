// ==UserScript==
// @name         Bilibili Feed Cleaner
// @namespace    https://github.com/local/bilibili-feed-cleaner
// @version      0.3.0
// @description  只处理 B 站视频详情页右侧推荐栏：弱化小于 5 分钟的视频，并显示 UP 主粉丝数。
// @author       You
// @match        https://www.bilibili.com/video/*
// @icon         https://www.bilibili.com/favicon.ico
// @grant        GM_getValue
// @grant        GM_setValue
// @grant        GM_registerMenuCommand
// @run-at       document-idle
// ==/UserScript==

(function () {
  'use strict';

  const SCRIPT_NAME = 'BFC';
  const SETTINGS_KEY = 'bfc_simple_settings_v1';
  const FOLLOWER_CACHE_KEY = 'bfc_follower_cache_v1';
  const PROCESSED_ATTR = 'data-bfc-processed';
  const SHORT_CLASS = 'bfc-short-video';
  const BADGE_CLASS = 'bfc-follower-badge';
  const SCAN_DEBOUNCE_MS = 500;

  const DEFAULT_SETTINGS = {
    enabled: true,
    debug: false,
    // 想调整“多长算短视频”，直接改这里的秒数；比如 300 表示 5 分钟以下会被弱化。
    shortVideoSeconds: 300,
    cacheDays: 7,
    maxRequestsPerPage: 10,
    opacity: 0.38,
  };

  const RECOMMEND_CONTAINER_SELECTORS = [
    '.recommend-list',
    '#reco_list',
    '.right-container',
    '.right-container .recommend-list',
    '.right',
    '.right .recommend-list',
    '.video-page__right',
  ];

  // 视频详情页右侧推荐卡片选择器。
  const VIDEO_PAGE_CARD_SELECTORS = [
    '.video-page-card-small',
    '.rec-list',
    '.video-card',
    '[class*="video-page-card-small"]',
    '[class*="rec-list"]',
  ].join(',');

  const TITLE_SELECTORS = [
    '.title',
    '.info .title',
    '.video-title',
    '.video-name',
    'a[href*="/video/"]',
  ];

  const DURATION_SELECTORS = [
    '.duration',
    '.length',
    '.time',
    '.video-duration',
    '.cover .duration',
    '.pic .duration',
  ];

  let settings = loadSettings();
  let followerCache = loadFollowerCache();
  let scanTimer = 0;
  let observer = null;
  let requestsUsedThisPage = 0;
  const pendingFollowerRequests = new Map();
  const failedMidsThisPage = new Set();

  init();

  // 脚本入口：准备样式、菜单、首次扫描和动态监听。
  function init() {
    injectStyle();
    registerMenu();
    scheduleScan();
    // B 站详情页有时会分批渲染右侧推荐，这里多安排两次轻量扫描，避免脚本启动太早而漏掉卡片。
    window.setTimeout(scheduleScan, 1500);
    window.setTimeout(scheduleScan, 3500);
    startObserver();
  }

  function loadSettings() {
    const saved = safeGetValue(SETTINGS_KEY, {});
    return normalizeSettings({ ...DEFAULT_SETTINGS, ...(isPlainObject(saved) ? saved : {}) });
  }

  function saveSettings(nextSettings) {
    settings = normalizeSettings({ ...DEFAULT_SETTINGS, ...nextSettings });
    GM_setValue(SETTINGS_KEY, settings);
  }

  function normalizeSettings(rawSettings) {
    return {
      enabled: Boolean(rawSettings.enabled),
      debug: Boolean(rawSettings.debug),
      shortVideoSeconds: toFiniteNumber(rawSettings.shortVideoSeconds, DEFAULT_SETTINGS.shortVideoSeconds),
      cacheDays: toFiniteNumber(rawSettings.cacheDays, DEFAULT_SETTINGS.cacheDays),
      maxRequestsPerPage: toFiniteNumber(rawSettings.maxRequestsPerPage, DEFAULT_SETTINGS.maxRequestsPerPage),
      opacity: toFiniteNumber(rawSettings.opacity, DEFAULT_SETTINGS.opacity),
    };
  }

  function safeGetValue(key, fallback) {
    try {
      return GM_getValue(key, fallback);
    } catch (error) {
      console.warn(`[${SCRIPT_NAME}] 读取 Tampermonkey 存储失败`, error);
      return fallback;
    }
  }

  function toFiniteNumber(value, fallback) {
    const number = Number(value);
    return Number.isFinite(number) ? number : fallback;
  }

  function isPlainObject(value) {
    return Object.prototype.toString.call(value) === '[object Object]';
  }

  function registerMenu() {
    GM_registerMenuCommand('启用 / 停用脚本', toggleEnabled);
    GM_registerMenuCommand('开启 / 关闭 debug', toggleDebug);
    GM_registerMenuCommand('清空粉丝数缓存', clearFollowerCache);
    GM_registerMenuCommand('查看说明', showHelp);
  }

  function toggleEnabled() {
    saveSettings({ ...settings, enabled: !settings.enabled });
    if (settings.enabled) {
      scheduleScan();
    } else {
      restoreMarkedCards();
    }
    window.alert(`脚本已${settings.enabled ? '启用' : '停用'}。`);
  }

  function toggleDebug() {
    saveSettings({ ...settings, debug: !settings.debug });
    window.alert(`debug 已${settings.debug ? '开启' : '关闭'}。`);
  }

  // 清空粉丝数缓存：遇到数据不准或想重新请求时可以手动点这个菜单。
  function clearFollowerCache() {
    followerCache = {};
    saveFollowerCache(followerCache);
    pendingFollowerRequests.clear();
    failedMidsThisPage.clear();
    requestsUsedThisPage = 0;
    document.querySelectorAll(`[${PROCESSED_ATTR}]`).forEach((card) => {
      if (card instanceof HTMLElement) {
        card.removeAttribute(PROCESSED_ATTR);
        setFollowerBadge(card, '短视频｜粉丝加载中');
      }
    });
    scheduleScan();
    window.alert('粉丝数缓存已清空。');
  }

  function showHelp() {
    window.alert(
      [
        'Bilibili Feed Cleaner 只处理 B 站视频详情页右侧推荐栏。',
        '小于 5 分钟的视频会变浅显示，不会被隐藏。',
        '只有短视频会请求并显示 UP 主粉丝数。',
        '粉丝数会缓存 7 天，每页最多请求 10 个 UP，避免占用过高。',
      ].join('\n'),
    );
  }

  function injectStyle() {
    const style = document.createElement('style');
    style.textContent = `
      .${SHORT_CLASS} {
        position: relative !important;
      }

      .${SHORT_CLASS} > :not(.${BADGE_CLASS}) {
        opacity: ${settings.opacity} !important;
        filter: grayscale(0.6) !important;
      }

      .${SHORT_CLASS}:hover > :not(.${BADGE_CLASS}) {
        opacity: 0.9 !important;
      }

      .${BADGE_CLASS} {
        position: absolute !important;
        right: 6px !important;
        bottom: 6px !important;
        z-index: 999 !important;
        max-width: min(150px, calc(100% - 12px)) !important;
        box-sizing: border-box !important;
        padding: 2px 5px !important;
        border: 1px solid rgba(255, 210, 64, 0.78) !important;
        border-radius: 4px !important;
        background: rgba(22, 18, 0, 0.76) !important;
        color: #ffe66d !important;
        box-shadow: 0 1px 5px rgba(0, 0, 0, 0.26) !important;
        font-size: 11px !important;
        font-weight: 700 !important;
        line-height: 15px !important;
        white-space: nowrap !important;
        overflow: hidden !important;
        text-overflow: ellipsis !important;
        pointer-events: none !important;
      }
    `;
    document.documentElement.appendChild(style);
  }

  // 扫描入口：只扫描视频详情页右侧推荐栏。
  function scanRecommendList() {
    if (!settings.enabled) {
      return;
    }

    const cards = collectRecommendCards();
    debugLog(`扫描视频详情页右侧推荐：找到 ${cards.length} 张候选卡片`);

    cards.forEach((card) => {
      if (card.getAttribute(PROCESSED_ATTR) === '1') {
        return;
      }

      const info = extractVideoInfo(card);

      // 如果标题或时长暂时没提取到，不打“已处理”标记。B 站可能稍后才把时长渲染出来，后续扫描还能再试。
      if (!info) {
        return;
      }

      if (!isShortVideo(info.durationSeconds)) {
        card.setAttribute(PROCESSED_ATTR, '1');
        return;
      }

      card.setAttribute(PROCESSED_ATTR, '1');
      markShortVideo(card);
      setFollowerBadge(card, '短视频｜粉丝加载中');
      loadAndRenderFollower(card, info);
    });
  }

  // 收集推荐视频卡片：只处理视频详情页右侧推荐。
  function collectRecommendCards() {
    const cards = new Set();
    RECOMMEND_CONTAINER_SELECTORS.forEach((selector) => {
      document.querySelectorAll(selector).forEach((container) => {
        if (!(container instanceof HTMLElement)) {
          return;
        }
        collectCardsFromContainer(container, VIDEO_PAGE_CARD_SELECTORS).forEach((card) => cards.add(card));
      });
    });

    // 兜底：如果新版页面没有命中推荐容器，就只在页面右半边的视频链接里找推荐卡片。
    // 这仍然比全页面处理安全，因为正文视频和评论区通常不在这个右侧区域。
    if (cards.size === 0) {
      collectCardsFromRightSideLinks().forEach((card) => cards.add(card));
    }

    return Array.from(cards);
  }

  function collectCardsFromContainer(container, cardSelectors) {
    const cards = new Set();

    container.querySelectorAll(cardSelectors).forEach((card) => {
      if (card instanceof HTMLElement && isUsableRecommendCard(card) && !hasRecommendCardAncestor(card, container, cardSelectors)) {
        cards.add(card);
      }
    });

    // 有些新版卡片类名不稳定，但卡片里一定会有视频链接。这里从视频链接往上找最像卡片的外层。
    container.querySelectorAll('a[href*="/video/"]').forEach((link) => {
      const card = findCardFromVideoLink(link, container);
      if (card) {
        cards.add(card);
      }
    });

    return Array.from(cards);
  }

  function collectCardsFromRightSideLinks() {
    const cards = new Set();
    document.querySelectorAll('a[href*="/video/"]').forEach((link) => {
      if (!(link instanceof HTMLElement) || !isElementOnRightSide(link)) {
        return;
      }
      const card = findCardFromVideoLink(link, document.body);
      if (card && isElementOnRightSide(card) && isUsableRecommendCard(card)) {
        cards.add(card);
      }
    });
    return Array.from(cards);
  }

  function isElementOnRightSide(element) {
    const rect = element.getBoundingClientRect();
    return rect.width > 0 && rect.height > 0 && rect.left > window.innerWidth * 0.45 && rect.top > 60;
  }

  function findCardFromVideoLink(link, boundary) {
    let current = link instanceof HTMLElement ? link : null;
    while (current && current !== boundary && current !== document.body) {
      if (isUsableRecommendCard(current)) {
        return current;
      }
      current = current.parentElement;
    }
    return null;
  }

  // 判断一个元素是不是真的“单张推荐卡片”，避免把推荐列表容器整体变浅。
  function isUsableRecommendCard(element) {
    if (!(element instanceof HTMLElement)) {
      return false;
    }

    const rect = element.getBoundingClientRect();
    const videoLinks = Array.from(element.querySelectorAll('a[href*="/video/"]'));
    const hasVideoLink = videoLinks.length > 0;
    const hasDuration = Boolean(cleanText(element.textContent).match(/(?:\d{1,2}:)?\d{1,2}:\d{2}/));
    const isSingleCardSize = rect.width >= 150 && rect.width <= 720 && rect.height >= 45 && rect.height <= 360;
    const isNotLargeList = videoLinks.length <= 3;

    return hasVideoLink && hasDuration && isSingleCardSize && isNotLargeList;
  }

  function looksLikeRecommendCard(element) {
    return isUsableRecommendCard(element);
  }

  function hasRecommendCardAncestor(card, container, cardSelectors) {
    let parent = card.parentElement;
    while (parent && parent !== container) {
      if (parent.matches(cardSelectors)) {
        return true;
      }
      parent = parent.parentElement;
    }
    return false;
  }

  // 从卡片中提取标题、时长、UP 主链接、mid；拿不到时长就不处理。
  function extractVideoInfo(card) {
    const title = getTextBySelectors(card, TITLE_SELECTORS);
    const durationText = getDurationText(card);
    const durationSeconds = parseDuration(durationText);
    if (!title || !durationText || durationSeconds === null) {
      return null;
    }

    return {
      title,
      durationText,
      durationSeconds,
      uploaderUrl: getUploaderUrl(card),
      mid: extractMidFromCard(card),
    };
  }

  function getTextBySelectors(root, selectors) {
    for (const selector of selectors) {
      const element = root.querySelector(selector);
      const text = cleanText(element && element.textContent);
      if (text) {
        return text;
      }
    }

    const videoLink = root.querySelector('a[href*="/video/"]');
    const linkTitle = cleanText(videoLink && (videoLink.getAttribute('title') || videoLink.getAttribute('aria-label')));
    if (linkTitle) {
      return linkTitle;
    }

    return '';
  }

  function getDurationText(card) {
    for (const selector of DURATION_SELECTORS) {
      const matched = Array.from(card.querySelectorAll(selector))
        .map((element) => cleanText(element.textContent))
        .find((text) => parseDuration(text) !== null);
      if (matched) {
        return matched;
      }
    }

    const matched = cleanText(card.textContent).match(/(?:\d{1,2}:)?\d{1,2}:\d{2}/);
    return matched ? matched[0] : '';
  }

  // 把 04:32 或 01:02:33 转成秒，解析失败返回 null。
  function parseDuration(text) {
    const clean = cleanText(text);
    if (!/^(?:\d{1,2}:)?\d{1,2}:\d{2}$/.test(clean)) {
      return null;
    }

    const parts = clean.split(':').map((part) => Number(part));
    if (parts.some((part) => !Number.isFinite(part))) {
      return null;
    }

    if (parts.length === 2) {
      return parts[0] * 60 + parts[1];
    }
    if (parts.length === 3) {
      return parts[0] * 3600 + parts[1] * 60 + parts[2];
    }
    return null;
  }

  // 判断是否小于配置里的短视频阈值，默认 300 秒。
  function isShortVideo(durationSeconds) {
    return durationSeconds < settings.shortVideoSeconds;
  }

  // 给短视频卡片添加变浅样式，用户 hover 时仍然能看清。
  function markShortVideo(card) {
    card.classList.add(SHORT_CLASS);
  }

  // 从 UP 主空间链接中提取 mid，例如 https://space.bilibili.com/123456。
  function extractMidFromCard(card) {
    const uploaderUrl = getUploaderUrl(card);
    const matched = uploaderUrl.match(/space\.bilibili\.com\/(\d+)/);
    return matched ? matched[1] : '';
  }

  function getUploaderUrl(card) {
    const link = card.querySelector('a[href*="space.bilibili.com"], a[href*="//space.bilibili.com"], a[href^="/space/"]');
    return link ? normalizeUrl(link.getAttribute('href')) : '';
  }

  function normalizeUrl(url) {
    if (!url) {
      return '';
    }
    if (url.startsWith('//')) {
      return `${location.protocol}${url}`;
    }
    if (url.startsWith('/space/')) {
      return `https://space.bilibili.com/${url.replace('/space/', '')}`;
    }
    if (url.startsWith('/')) {
      return `${location.origin}${url}`;
    }
    return url;
  }

  async function loadAndRenderFollower(card, info) {
    if (!info.mid) {
      setFollowerBadge(card, '短视频｜粉丝未知');
      debugLog('发现短视频', info, '未知', '变浅并显示粉丝数');
      return;
    }

    const follower = await getFollowerCount(info.mid);
    if (follower === null) {
      setFollowerBadge(card, '短视频｜粉丝未知');
      debugLog('发现短视频', info, '未知', '变浅并显示粉丝数');
      return;
    }

    setFollowerBadge(card, `短视频｜粉丝 ${formatFollowerCount(follower)}`);
    debugLog('发现短视频', info, follower, '变浅并显示粉丝数');
  }

  // 先查缓存；缓存没有或过期，再请求接口。每页请求数和同 mid 请求都会被限制。
  async function getFollowerCount(mid) {
    const cached = followerCache[mid];
    if (cached && !isCacheExpired(cached.updatedAt)) {
      return Number.isFinite(Number(cached.follower)) ? Number(cached.follower) : null;
    }

    if (failedMidsThisPage.has(mid)) {
      return null;
    }

    if (pendingFollowerRequests.has(mid)) {
      return pendingFollowerRequests.get(mid);
    }

    if (requestsUsedThisPage >= settings.maxRequestsPerPage) {
      debugLog(`跳过粉丝数请求：已达到每页上限 ${settings.maxRequestsPerPage}`);
      return null;
    }

    requestsUsedThisPage += 1;
    const request = fetchFollowerCount(mid)
      .then((follower) => {
        if (follower === null) {
          failedMidsThisPage.add(mid);
          return null;
        }
        followerCache[mid] = {
          follower,
          updatedAt: Date.now(),
        };
        saveFollowerCache(followerCache);
        return follower;
      })
      .catch((error) => {
        failedMidsThisPage.add(mid);
        debugLog(`粉丝数请求失败：mid=${mid}`, error);
        return null;
      })
      .finally(() => {
        pendingFollowerRequests.delete(mid);
      });

    pendingFollowerRequests.set(mid, request);
    return request;
  }

  // 请求 B 站粉丝数接口；credentials: include 用来带上当前登录态 cookie。
  async function fetchFollowerCount(mid) {
    const response = await fetch(`https://api.bilibili.com/x/relation/stat?vmid=${encodeURIComponent(mid)}`, {
      credentials: 'include',
    });

    if (!response.ok) {
      return null;
    }

    const json = await response.json();
    const follower = json && json.data && Number(json.data.follower);
    return Number.isFinite(follower) ? follower : null;
  }

  // 更新卡片上的粉丝数标签；没有标签就创建一个。
  function setFollowerBadge(card, text) {
    let badge = card.querySelector(`:scope > .${BADGE_CLASS}`);
    if (!badge) {
      badge = document.createElement('span');
      badge.className = BADGE_CLASS;
      card.prepend(badge);
    }
    badge.textContent = text;
  }

  // 把粉丝数格式化成 3682、2.3万、123.4万。
  function formatFollowerCount(count) {
    const number = Number(count);
    if (!Number.isFinite(number)) {
      return '未知';
    }
    if (number < 10000) {
      return String(number);
    }
    return `${(number / 10000).toFixed(1)}万`;
  }

  // 读取粉丝数缓存；结构是 { "mid": { follower, updatedAt } }。
  function loadFollowerCache() {
    const cache = safeGetValue(FOLLOWER_CACHE_KEY, {});
    return isPlainObject(cache) ? cache : {};
  }

  // 保存粉丝数缓存，避免 7 天内重复请求同一个 UP。
  function saveFollowerCache(cache) {
    GM_setValue(FOLLOWER_CACHE_KEY, cache);
  }

  function isCacheExpired(updatedAt) {
    const cacheMs = settings.cacheDays * 24 * 60 * 60 * 1000;
    return !Number.isFinite(Number(updatedAt)) || Date.now() - Number(updatedAt) > cacheMs;
  }

  // 使用 MutationObserver 监听右侧推荐动态变化；B 站会异步加载推荐列表。
  function startObserver() {
    if (observer) {
      observer.disconnect();
    }

    observer = new MutationObserver((mutations) => {
      if (mutations.some(hasRelevantMutation)) {
        scheduleScan();
      }
    });

    observer.observe(document.body || document.documentElement, {
      childList: true,
      subtree: true,
    });
  }

  function hasRelevantMutation(mutation) {
    return Array.from(mutation.addedNodes).some((node) => {
      if (!(node instanceof Element)) {
        return false;
      }

      const containerChanged = RECOMMEND_CONTAINER_SELECTORS.some((selector) => (
        node.matches(selector) || Boolean(node.querySelector(selector))
      ));
      const cardChanged = node.matches(VIDEO_PAGE_CARD_SELECTORS) || Boolean(node.querySelector(VIDEO_PAGE_CARD_SELECTORS));
      return containerChanged || cardChanged;
    });
  }

  // 防抖扫描：页面连续变化时，只在 500ms 后真正扫描一次。
  function scheduleScan() {
    window.clearTimeout(scanTimer);
    scanTimer = window.setTimeout(scanRecommendList, SCAN_DEBOUNCE_MS);
  }

  function restoreMarkedCards() {
    document.querySelectorAll(`[${PROCESSED_ATTR}], .${SHORT_CLASS}`).forEach((card) => {
      if (!(card instanceof HTMLElement)) {
        return;
      }
      card.removeAttribute(PROCESSED_ATTR);
      card.classList.remove(SHORT_CLASS);
      const badge = card.querySelector(`:scope > .${BADGE_CLASS}`);
      if (badge) {
        badge.remove();
      }
    });
  }

  function cleanText(text) {
    return String(text || '')
      .replace(/\s+/g, ' ')
      .trim();
  }

  // debug 模式下输出信息；默认关闭，避免控制台刷屏。
  function debugLog(message, info, follower, action) {
    if (!settings.debug) {
      return;
    }

    if (info && typeof info === 'object' && 'title' in info) {
      console.debug(
        [
          `[${SCRIPT_NAME}] ${message}`,
          `标题：${info.title}`,
          `时长：${info.durationText}`,
          `UP主mid：${info.mid || '未知'}`,
          `粉丝数：${follower}`,
          `处理：${action}`,
        ].join('\n'),
      );
      return;
    }

    console.debug(`[${SCRIPT_NAME}] ${message}`, info || '');
  }
})();
