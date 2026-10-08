/**
 * StreamMix Studio — Master Application Controller
 * High-performance 1080p 60fps Twitch + YouTube Remix Engine
 * Interactive WYSIWYG Stage, Draggable Avatar, 18 Caption Presets
 */

// Global Reactive State
const STATE = {
  currentTab: 'editor',
  sourceModes: {
    twitch: 'url',
    yt: 'url'
  },
  twitchLocalPath: '',
  ytLocalPath: '',
  ytDuration: 0,
  twitchDuration: 0,

  // Avatar State
  enableAvatar: true,
  avatarPath: 'data/avatars/default_avatar.png',
  avatarUrl: '/avatars/default_avatar.png',
  avatarSize: 350,
  avatarOpacity: 1.0,
  avatarAnchor: 'right',
  avatarFlip: false,
  avatarGlow: 'cyan',
  avatarSway: true,
  avatarSwaySpeed: 0.35,
  avatarBounce: true,

  // Captions State
  enableCaptions: true,
  captionPreset: 'capcut_yellow',
  captionPosition: 'center-left',
  captionSize: 'medium',
  captionCustomSize: 150,
  captionFontFamily: 'default',
  demoCaptionText: 'WAIT... DID HE REALLY?!',
  enableCaptionBg: false,
  captionBgColor: '#000000',
  captionBgOpacity: 75,

  // Custom 1920x1080 Canvas Layout Coordinates
  customLayout: {
    avatar: { x: null, y: null },
    caption: { x: null, y: null, w: null, h: null },
    gridVisible: false
  },

  tasks: [],
  pollTimer: null
};

let _stageDrag = null;

// Presets Palette & Font Mapping for 18 Styles (Imported from ATSAuthor)
const CAPTION_PRESETS = {
  capcut_yellow:    { base: '#ffffff', active: '#ffff00', glow: '#ffcc00', font: "'Montserrat', sans-serif" },
  hormozi_green:    { base: '#ffffff', active: '#00ff66', glow: '#00dd44', font: "Impact, 'Arial Black', sans-serif" },
  mrbeast_punch:    { base: '#ffffff', active: '#fbbf24', glow: '#d97706', font: "'Bangers', cursive, Impact" },
  ali_abdaal:       { base: '#ffffff', active: '#38bdf8', glow: '#0284c7', font: "'Poppins', sans-serif" },
  iman_gadzhi:      { base: '#ffffff', active: '#ffd700', glow: '#f59e0b', font: "'Cinzel', serif" },
  tiktok_violet:    { base: '#ffffff', active: '#d946ef', glow: '#a855f7', font: "'Archivo Black', sans-serif" },
  podcast_pill:     { base: '#ffffff', active: '#00e5ff', glow: '#00b4d8', font: "'Outfit', 'Montserrat', sans-serif" },
  streamer_lime:    { base: '#ffffff', active: '#a3e635', glow: '#84cc16', font: "'Luckiest Guy', cursive, Impact" },
  neon_cyber:       { base: '#00ffff', active: '#ff00ff', glow: '#bf55ec', font: "'Montserrat', sans-serif" },
  red_fire:         { base: '#ffffff', active: '#ff3344', glow: '#ef4444', font: "Impact, 'Arial Black', sans-serif" },
  dark_stoic:       { base: '#cbd5e1', active: '#ffffff', glow: '#94a3b8', font: "'Oswald', 'Arial Black', sans-serif" },
  clean_minimal:    { base: '#ffffff', active: '#ffffff', glow: '#94a3b8', font: "'Inter', sans-serif" },
  retro_vintage:    { base: '#ffa03c', active: '#ffff00', glow: '#f59e0b', font: "'Arial Black', Impact, sans-serif" },
  midnight_blue:    { base: '#ffffff', active: '#38bdf8', glow: '#2563eb', font: "'Montserrat', sans-serif" },
  true_crime:       { base: '#e0e0e0', active: '#ef4444', glow: '#dc2626', font: "'Courier New', monospace" },
  wealth_cash:      { base: '#ffffff', active: '#10df70', glow: '#059669', font: "Impact, 'Arial Black', sans-serif" },
  cosmic_violet:    { base: '#ffffff', active: '#c084fc', glow: '#9333ea', font: "'Montserrat', sans-serif" },
  cinematic_bronze: { base: '#e8f0f8', active: '#f59e0b', glow: '#d97706', font: "'Cinzel', serif" }
};

// Utilities
function escapeHtml(str) {
  if (!str) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}

function formatDuration(seconds) {
  if (!seconds || isNaN(seconds)) return '00:00:00';
  const s = Math.floor(seconds);
  const hrs = Math.floor(s / 3600);
  const mins = Math.floor((s % 3600) / 60);
  const secs = s % 60;
  return `${hrs.toString().padStart(2, '0')}:${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
}

function parseTimeToSeconds(timeStr) {
  if (!timeStr) return 0;
  const parts = timeStr.trim().split(':').map(Number);
  if (parts.length === 3) return parts[0] * 3600 + parts[1] * 60 + parts[2];
  if (parts.length === 2) return parts[0] * 60 + parts[1];
  if (parts.length === 1) return parts[0] || 0;
  return 0;
}

function formatApiError(detail) {
  if (!detail) return 'Unknown error occurred.';
  if (Array.isArray(detail)) {
    return detail.map(item => {
      const field = item.loc ? item.loc[item.loc.length - 1] : '';
      const prefix = field && field !== 'body' ? `[${field}] ` : '';
      return `${prefix}${item.msg || JSON.stringify(item)}`;
    }).join(' | ');
  }
  if (typeof detail === 'object') {
    return JSON.stringify(detail);
  }
  return String(detail);
}

function showToast(message, type = 'info') {
  const toast = document.createElement('div');
  toast.className = `toast toast-${type}`;
  toast.style.cssText = `
    position: fixed;
    top: 24px;
    right: 24px;
    z-index: 100000;
    background: ${type === 'error' ? 'rgba(239, 68, 68, 0.95)' : type === 'success' ? 'rgba(16, 185, 129, 0.95)' : 'rgba(30, 41, 59, 0.95)'};
    color: #ffffff;
    padding: 12px 20px;
    border-radius: 8px;
    font-size: 13px;
    font-weight: 600;
    box-shadow: 0 10px 25px rgba(0,0,0,0.5);
    backdrop-filter: blur(10px);
    border: 1px solid rgba(255,255,255,0.15);
    transition: all 0.3s ease;
    opacity: 0;
    transform: translateY(-10px);
  `;
  toast.textContent = message;
  document.body.appendChild(toast);

  requestAnimationFrame(() => {
    toast.style.opacity = '1';
    toast.style.transform = 'translateY(0)';
  });

  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transform = 'translateY(-10px)';
    setTimeout(() => toast.remove(), 300);
  }, 3500);
}

// App Initialization
document.addEventListener('DOMContentLoaded', async () => {
  initNavigation();
  initDrawer();
  initInteractiveStage();
  initSourcePickers();
  initReactionControls();
  initDurationSync();
  initAvatarControls();
  initCaptionControls();
  initRenderTriggers();
  initMetadataGenerator();
  initSliceModal();
  initSettingsListeners();
  initProAudioAndBitrateControls();
  initLogsModal();

  await checkGpuHealth();
  await loadApiKeys();
  await checkGroqApiHealth();
  await loadStorageStats();
  await loadSettings();
  startTaskPolling();

  syncStage();
});

// Master Navigation Controller
function initNavigation() {
  const tabs = [
    { btn: document.getElementById('tabBtnEditor'), view: document.getElementById('view-editor'), id: 'editor' },
    { btn: document.getElementById('tabBtnPool'), view: document.getElementById('view-keys'), id: 'keys' },
    { btn: document.getElementById('tabBtnSettings'), view: document.getElementById('view-settings'), id: 'settings' }
  ];

  tabs.forEach(t => {
    t.btn?.addEventListener('click', () => {
      tabs.forEach(item => {
        item.btn?.classList.toggle('active', item.id === t.id);
        item.view?.classList.toggle('active', item.id === t.id);
      });
      STATE.currentTab = t.id;
      if (t.id === 'keys') renderKeysTable();
    });
  });
}

// Slide-Out Task Drawer (Off-Canvas, Never blocks buttons!)
function initDrawer() {
  const drawer = document.getElementById('taskDrawer');
  const btnToggle = document.getElementById('btnToggleDrawer');
  const btnClose = document.getElementById('btnCloseDrawer');

  btnToggle?.addEventListener('click', () => drawer?.classList.toggle('open'));
  btnClose?.addEventListener('click', () => drawer?.classList.remove('open'));

  document.getElementById('btnOpenOutputs')?.addEventListener('click', openOutputsFolder);
  document.getElementById('btnDrawerOpenFolder')?.addEventListener('click', openOutputsFolder);
}

async function openOutputsFolder() {
  try {
    const res = await fetch('/api/tasks/open-folder', { method: 'POST' });
    if (!res.ok) showToast('Could not open folder automatically.', 'info');
  } catch (err) {
    showToast('Outputs location: twitchyoutube/data/outputs', 'info');
  }
}

function openDrawer() {
  document.getElementById('taskDrawer')?.classList.add('open');
}

// GPU Health Prober
async function checkGpuHealth() {
  try {
    const res = await fetch('/api/health');
    if (res.ok) {
      const data = await res.json();
      const statusText = document.getElementById('gpuStatusText');
      const badgeHardware = document.getElementById('detected-hardware-badge');
      if (statusText) statusText.textContent = `GPU: ${data.detected_encoder.toUpperCase()}`;
      if (badgeHardware) badgeHardware.textContent = `Auto-Detected: ${data.detected_encoder.toUpperCase()}`;
    }
  } catch (err) {
    console.error('Health check failed', err);
  }
}

// ═══════════════════════════════════════════════════════════════════════════
// WYSIWYG INTERACTIVE STAGE & POINTER DRAGGING SYSTEM (ATSAuthor Core)
// ═══════════════════════════════════════════════════════════════════════════
function initInteractiveStage() {
  const canvas = document.getElementById('stage-canvas');
  if (!canvas) return;

  canvas.addEventListener('pointerdown', onStagePointerDown);
  window.addEventListener('pointermove', onStagePointerMove);
  window.addEventListener('pointerup', onStagePointerUp);

  // Background blur live sync
  document.getElementById('twitch-blur')?.addEventListener('input', (e) => {
    const blur = e.target.value;
    document.getElementById('twitch-blur-val').textContent = `${blur}px`;
    document.getElementById('hud-blur-pill').textContent = `Blur: ${blur}px`;
    const simStream = document.getElementById('bg-sim-stream');
    if (simStream) simStream.style.filter = `blur(${blur}px)`;
  });

  // YouTube opacity live sync
  document.getElementById('yt-opacity')?.addEventListener('input', (e) => {
    const op = e.target.value;
    document.getElementById('yt-opacity-val').textContent = `${op}% ${op >= 70 ? '(Clear Reaction)' : '(Semi-Transparent)'}`;
    document.getElementById('hud-opacity-pill').textContent = `YT: ${op}%`;
    const ytLayer = document.getElementById('stage-yt-layer');
    if (ytLayer) ytLayer.style.opacity = (op / 100).toString();
  });
}

function onStagePointerDown(e) {
  const canvas = document.getElementById('stage-canvas');
  if (!canvas) return;

  const handle = e.target.closest('.stage-resize-handle');
  const element = e.target.closest('.stage-element');

  if (!handle && !element) {
    document.querySelectorAll('.stage-element').forEach(el => el.classList.remove('selected'));
    document.getElementById('stage-inspect-text').textContent = 'Drag Avatar or Captions directly on canvas. Corner handles resize freely!';
    return;
  }

  e.preventDefault();
  const rect = canvas.getBoundingClientRect();
  const targetEl = handle ? handle.closest('.stage-element') : element;

  document.querySelectorAll('.stage-element').forEach(el => el.classList.remove('selected'));
  targetEl.classList.add('selected');

  const elRect = targetEl.getBoundingClientRect();
  const targetId = targetEl.id;

  // Normalized to 1920x1080 canvas
  const normX = ((elRect.left - rect.left) / rect.width) * 1920;
  const normY = ((elRect.top - rect.top) / rect.height) * 1080;
  const normW = (elRect.width / rect.width) * 1920;
  const normH = (elRect.height / rect.height) * 1080;

  _stageDrag = {
    type: handle ? 'resize' : 'move',
    targetId: targetId,
    targetType: targetId.includes('avatar') ? 'avatar' : 'caption',
    handleDir: handle ? (handle.dataset.dir || 'br') : null,
    startX: normX,
    startY: normY,
    startW: normW,
    startH: normH,
    startClientX: e.clientX,
    startClientY: e.clientY,
    canvasRect: rect,
    startAvatarH: STATE.avatarSize || 420
  };

  targetEl.classList.add('dragging');
}

function onStagePointerMove(e) {
  if (!_stageDrag) return;
  e.preventDefault();

  const d = _stageDrag;
  const rect = d.canvasRect;
  const deltaNormX = ((e.clientX - d.startClientX) / rect.width) * 1920;
  const deltaNormY = ((e.clientY - d.startClientY) / rect.height) * 1080;

  const targetEl = document.getElementById(d.targetId);
  if (!targetEl) return;

  if (d.type === 'move') {
    // 2D Free Drag
    let newX = Math.round(d.startX + deltaNormX);
    let newY = Math.round(d.startY + deltaNormY);

    if (d.targetType === 'avatar') {
      // Allow extra move for avatar: can go negative up to -1200 so transparent borders can be pushed offscreen!
      newX = Math.max(-1200, Math.min(2400, newX));
      newY = Math.max(-600, Math.min(1800, newY));
    } else {
      newX = Math.max(0, Math.min(1920 - d.startW, newX));
      newY = Math.max(0, Math.min(1080 - d.startH, newY));
    }

    targetEl.style.left = `${(newX / 1920) * 100}%`;
    targetEl.style.top  = `${(newY / 1080) * 100}%`;
    targetEl.style.right = 'auto';
    targetEl.style.bottom = 'auto';
    targetEl.style.transform = 'none';

    if (d.targetType === 'avatar') {
      STATE.customLayout.avatar.x = newX;
      STATE.customLayout.avatar.y = newY;
      document.getElementById('stage-inspect-text').textContent = `🎯 Avatar Position: X=${newX}px, Y=${newY}px (Custom Canvas Drag)`;
    } else if (d.targetType === 'caption') {
      STATE.customLayout.caption.x = newX;
      STATE.customLayout.caption.y = newY;
      STATE.customLayout.caption.w = Math.round(d.startW);
      STATE.customLayout.caption.h = Math.round(d.startH);
      document.getElementById('stage-inspect-text').textContent = `🎯 Captions Position: X=${newX}px, Y=${newY}px (Custom Canvas Drag)`;
    }
  } else if (d.type === 'resize') {
    // Corner / Edge Resizing
    if (d.targetType === 'avatar') {
      let delta = deltaNormY;
      if (d.handleDir === 'tl' || d.handleDir === 'tr') {
        delta = -deltaNormY;
      }
      const newH = Math.max(200, Math.min(1200, Math.round(d.startAvatarH + delta)));
      STATE.avatarSize = newH;
      targetEl.style.height = `${(newH / 1080) * 100}%`;
      targetEl.style.width = `${(newH / 1080) * 100 * 0.75}%`;

      const slider = document.getElementById('avatar-size');
      const disp = document.getElementById('avatar-size-display');
      if (slider) slider.value = newH;
      if (disp) disp.textContent = `${newH}px (Canvas Drag)`;
      document.getElementById('hud-avatar-pill').textContent = `Avatar: ${newH}px`;
      document.getElementById('stage-inspect-text').textContent = `📏 Avatar Resized: Height=${newH}px`;
    } else if (d.targetType === 'caption') {
      let newW = d.startW;
      let newX = d.startX;
      let newY = d.startY;

      // Horizontal resize
      if (['r', 'tr', 'br'].includes(d.handleDir)) {
        newW = Math.max(260, Math.min(1850, Math.round(d.startW + deltaNormX)));
      } else if (['l', 'tl', 'bl'].includes(d.handleDir)) {
        const potentialW = Math.round(d.startW - deltaNormX);
        if (potentialW >= 260 && potentialW <= 1850) {
          newW = potentialW;
          newX = Math.round(d.startX + deltaNormX);
        }
      }

      // Vertical resize / position
      let newH = d.startH;
      if (['b', 'bl', 'br'].includes(d.handleDir)) {
        newH = Math.max(100, Math.min(1000, Math.round(d.startH + deltaNormY)));
      } else if (['t', 'tl', 'tr'].includes(d.handleDir)) {
        const potentialH = Math.round(d.startH - deltaNormY);
        if (potentialH >= 100 && potentialH <= 1000) {
          newH = potentialH;
          newY = Math.round(d.startY + deltaNormY);
        }
      }

      targetEl.style.width = `${(newW / 1920) * 100}%`;
      targetEl.style.height = `${(newH / 1080) * 100}%`;
      targetEl.style.left = `${(newX / 1920) * 100}%`;
      targetEl.style.top = `${(newY / 1080) * 100}%`;
      STATE.customLayout.caption.w = newW;
      STATE.customLayout.caption.h = newH;
      STATE.customLayout.caption.x = newX;
      STATE.customLayout.caption.y = newY;
      document.getElementById('stage-inspect-text').textContent = `📏 Captions Resized: W=${newW}px, H=${newH}px, X=${newX}px, Y=${newY}px`;
    }
  }
}

function onStagePointerUp(e) {
  if (_stageDrag) {
    const targetEl = document.getElementById(_stageDrag.targetId);
    if (targetEl) targetEl.classList.remove('dragging');
    _stageDrag = null;
  }
}

window.toggleStageGrid = function() {
  const grid = document.getElementById('stage-grid');
  const btn = document.getElementById('btn-toggle-grid');
  STATE.customLayout.gridVisible = !STATE.customLayout.gridVisible;
  if (grid) grid.style.display = STATE.customLayout.gridVisible ? 'flex' : 'none';
  if (btn) btn.classList.toggle('active', STATE.customLayout.gridVisible);
};

window.setCaptionPositionPreset = function(pos) {
  STATE.customLayout.caption.x = null;
  STATE.customLayout.caption.y = null;
  STATE.customLayout.caption.w = null;
  STATE.customLayout.caption.h = null;
  const captionBox = document.getElementById('stage-caption-box');

  ['cap-pos-left', 'cap-pos-right', 'cap-pos-bottom', 'cap-pos-center', 'btn-subs-left', 'btn-subs-right'].forEach(id => {
    document.getElementById(id)?.classList.remove('active');
  });

  if (pos === 'left') {
    STATE.captionPosition = 'center-left';
    document.getElementById('btn-subs-left')?.classList.add('active');
    document.getElementById('cap-pos-left')?.classList.add('active');
    if (captionBox) {
      captionBox.style.left = '8%';
      captionBox.style.width = '36%';
      captionBox.style.top = '48%';
      captionBox.style.height = 'auto';
    }
  } else if (pos === 'right') {
    STATE.captionPosition = 'center-right';
    document.getElementById('btn-subs-right')?.classList.add('active');
    document.getElementById('cap-pos-right')?.classList.add('active');
    if (captionBox) {
      captionBox.style.left = '56%';
      captionBox.style.width = '36%';
      captionBox.style.top = '22%';
      captionBox.style.height = 'auto';
    }
  } else if (pos === 'bottom') {
    STATE.captionPosition = 'bottom';
    document.getElementById('cap-pos-bottom')?.classList.add('active');
    if (captionBox) {
      captionBox.style.left = '20%';
      captionBox.style.width = '60%';
      captionBox.style.top = '65%';
      captionBox.style.height = 'auto';
    }
  } else {
    STATE.captionPosition = 'center';
    document.getElementById('cap-pos-center')?.classList.add('active');
    if (captionBox) {
      captionBox.style.left = '32%';
      captionBox.style.width = '36%';
      captionBox.style.top = '48%';
      captionBox.style.height = 'auto';
    }
  }
  syncStage();
  showToast(`Captions aligned: ${pos.toUpperCase()}`, 'info');
};

window.resetStageLayout = function() {
  STATE.customLayout.avatar.x = null;
  STATE.customLayout.avatar.y = null;
  STATE.customLayout.caption.x = null;
  STATE.customLayout.caption.y = null;
  STATE.customLayout.caption.w = null;
  STATE.customLayout.caption.h = null;
  STATE.captionPosition = 'center-left';
  const captionBox = document.getElementById('stage-caption-box');
  if (captionBox) {
    captionBox.style.width = '36%';
    captionBox.style.height = 'auto';
    captionBox.style.left = '8%';
    captionBox.style.top = '48%';
  }
  const avatarBox = document.getElementById('stage-avatar-box');
  if (avatarBox) {
    avatarBox.style.top = 'auto';
    avatarBox.style.bottom = '0%';
    avatarBox.style.right = '4%';
    avatarBox.style.left = 'auto';
  }
  ['cap-pos-right', 'cap-pos-bottom', 'cap-pos-center', 'btn-subs-right'].forEach(id => {
    document.getElementById(id)?.classList.remove('active');
  });
  document.getElementById('btn-subs-left')?.classList.add('active');
  document.getElementById('cap-pos-left')?.classList.add('active');
  syncStage();
  showToast('Stage layout reset to safe defaults.', 'info');
};

// Synchronize all Visual Elements on the 16:9 Canvas
function syncStage() {
  // 1. Avatar Layer
  const avatarBox = document.getElementById('stage-avatar-box');
  const avatarImg = document.getElementById('stage-avatar-img');

  if (avatarBox && avatarImg) {
    avatarBox.style.display = STATE.enableAvatar ? 'flex' : 'none';

    if (STATE.avatarUrl) {
      avatarImg.src = STATE.avatarUrl;
    }

    // Mirror flip
    avatarImg.style.transform = STATE.avatarFlip ? 'scaleX(-1)' : 'none';

    // Opacity
    avatarImg.style.opacity = STATE.avatarOpacity.toString();

    // Glow Border
    const glows = {
      cyan: 'drop-shadow(0 0 14px rgba(0, 242, 254, 0.75))',
      white: 'drop-shadow(0 0 14px rgba(255, 255, 255, 0.85))',
      gold: 'drop-shadow(0 0 14px rgba(251, 191, 36, 0.75))',
      none: 'none'
    };
    avatarImg.style.filter = glows[STATE.avatarGlow] || glows.cyan;

    // Slow-motion sway animation toggle
    avatarBox.classList.toggle('avatar-animated-sway', STATE.avatarSway);

    // Height & Width
    const heightPct = (STATE.avatarSize / 1080) * 100;
    avatarBox.style.height = `${heightPct}%`;
    avatarBox.style.width = `${heightPct * 0.75}%`;

    // Coordinates: Custom Drag vs Anchor Preset
    if (STATE.customLayout.avatar.x !== null && STATE.customLayout.avatar.y !== null) {
      avatarBox.style.left = `${(STATE.customLayout.avatar.x / 1920) * 100}%`;
      avatarBox.style.top = `${(STATE.customLayout.avatar.y / 1080) * 100}%`;
      avatarBox.style.bottom = 'auto';
      avatarBox.style.right = 'auto';
    } else {
      avatarBox.style.bottom = '0%';
      avatarBox.style.top = 'auto';
      if (STATE.avatarAnchor === 'left') {
        avatarBox.style.left = '4%';
        avatarBox.style.right = 'auto';
      } else if (STATE.avatarAnchor === 'center') {
        avatarBox.style.left = '37.5%';
        avatarBox.style.right = 'auto';
      } else {
        avatarBox.style.right = '4%';
        avatarBox.style.left = 'auto';
      }
    }
  }

  // 2. Captions Layer
  const captionBox = document.getElementById('stage-caption-box');
  const captionContent = document.getElementById('stage-caption-content');

  if (captionBox && captionContent) {
    captionBox.style.display = STATE.enableCaptions ? 'flex' : 'none';

    const pal = CAPTION_PRESETS[STATE.captionPreset] || CAPTION_PRESETS.capcut_yellow;
    captionContent.style.color = pal.base;

    // Font Family: Use custom override if selected, else fallback to template preset font
    if (STATE.captionFontFamily && STATE.captionFontFamily !== 'default') {
      captionContent.style.fontFamily = `"${STATE.captionFontFamily}", ${pal.font}`;
    } else {
      captionContent.style.fontFamily = pal.font;
    }

    // Active words glow
    captionContent.querySelectorAll('.demo-word.active').forEach(w => {
      w.style.color = pal.active;
      w.style.textShadow = `0 0 16px ${pal.glow}, 2px 2px 0 #000, -2px -2px 0 #000`;
    });

    captionContent.querySelectorAll('.demo-word:not(.active)').forEach(w => {
      w.style.color = pal.base;
      w.style.textShadow = '2px 2px 0 #000, -2px -2px 0 #000, 2px -2px 0 #000, -2px 2px 0 #000';
    });

    // Font size: exact 1080p calculation with container query support
    let fs1080 = 115;
    if (STATE.captionSize === 'small') fs1080 = 80;
    else if (STATE.captionSize === 'medium') fs1080 = 95;
    else if (STATE.captionSize === 'large') fs1080 = 115;
    else if (STATE.captionSize === 'huge') fs1080 = 135;
    else if (STATE.captionSize === 'extrahuge') fs1080 = 160;
    else if (STATE.captionSize === 'custom') fs1080 = parseInt(STATE.captionCustomSize) || 150;
    else if (!isNaN(Number(STATE.captionSize))) fs1080 = Number(STATE.captionSize);

    captionContent.style.setProperty('--caption-fs-1080', `${fs1080}`);
    captionContent.style.fontSize = `calc(var(--caption-fs-1080, ${fs1080}) / 1920 * 100cqi)`;

    // Caption Background Box (Custom rounded backdrop box)
    if (STATE.enableCaptionBg) {
      captionBox.classList.add('has-bg-box');
      const hex = (STATE.captionBgColor || '#000000').replace('#', '');
      const r = parseInt(hex.substring(0, 2), 16) || 0;
      const g = parseInt(hex.substring(2, 4), 16) || 0;
      const b = parseInt(hex.substring(4, 6), 16) || 0;
      const a = (STATE.captionBgOpacity !== undefined ? STATE.captionBgOpacity : 75) / 100.0;
      captionBox.style.background = `rgba(${r}, ${g}, ${b}, ${a})`;
      captionBox.style.borderRadius = '14px';
    } else {
      captionBox.classList.remove('has-bg-box');
      captionBox.style.background = 'rgba(0, 0, 0, 0.2)';
      captionBox.style.borderRadius = 'var(--radius-sm)';
    }

    // Position & Dimension
    if (STATE.customLayout.caption.x !== null && STATE.customLayout.caption.y !== null) {
      captionBox.style.left = `${(STATE.customLayout.caption.x / 1920) * 100}%`;
      captionBox.style.top  = `${(STATE.customLayout.caption.y / 1080) * 100}%`;
      if (STATE.customLayout.caption.w) {
        captionBox.style.width = `${(STATE.customLayout.caption.w / 1920) * 100}%`;
      }
      if (STATE.customLayout.caption.h) {
        captionBox.style.height = `${(STATE.customLayout.caption.h / 1080) * 100}%`;
      }
    } else {
      if (STATE.captionPosition === 'center-left') {
        captionBox.style.left = '8%';
        captionBox.style.width = '36%';
        captionBox.style.top = '48%';
      } else if (STATE.captionPosition === 'center-right') {
        captionBox.style.left = '56%';
        captionBox.style.width = '36%';
        captionBox.style.top = '22%';
      } else if (STATE.captionPosition === 'center') {
        captionBox.style.left = '32%';
        captionBox.style.width = '36%';
        captionBox.style.top = '48%';
      } else {
        captionBox.style.left = '20%';
        captionBox.style.width = '60%';
        captionBox.style.top = '65%';
      }
      captionBox.style.height = 'auto';
    }
  }
}

// ═══════════════════════════════════════════════════════════════════════════
// AVATAR & CAPTION CONTROLS (Live Sync)
// ═══════════════════════════════════════════════════════════════════════════
function initAvatarControls() {
  // Toggle switch
  document.getElementById('enable-avatar')?.addEventListener('change', (e) => {
    STATE.enableAvatar = e.target.checked;
    syncStage();
  });

  // Size slider
  document.getElementById('avatar-size')?.addEventListener('input', (e) => {
    STATE.avatarSize = parseInt(e.target.value);
    document.getElementById('avatar-size-display').textContent = `${STATE.avatarSize}px`;
    document.getElementById('hud-avatar-pill').textContent = `Avatar: ${STATE.avatarSize}px`;
    syncStage();
  });

  // Opacity slider
  document.getElementById('avatar-opacity')?.addEventListener('input', (e) => {
    STATE.avatarOpacity = parseInt(e.target.value) / 100;
    document.getElementById('avatar-opacity-display').textContent = `${e.target.value}% ${e.target.value === '100' ? '(Solid)' : '(Transparent)'}`;
    syncStage();
  });

  // Slow sway speed slider
  document.getElementById('avatar-sway-speed')?.addEventListener('input', (e) => {
    STATE.avatarSwaySpeed = parseInt(e.target.value) / 100;
    document.getElementById('avatar-speed-display').textContent = `${STATE.avatarSwaySpeed}x (${STATE.avatarSwaySpeed <= 0.25 ? 'Slow' : STATE.avatarSwaySpeed <= 0.45 ? 'Smooth' : 'Fast'})`;
    const box = document.getElementById('stage-avatar-box');
    if (box) box.style.animationDuration = `${(1.5 / STATE.avatarSwaySpeed).toFixed(1)}s`;
  });

  // Motion checkboxes
  document.getElementById('avatar-sway')?.addEventListener('change', (e) => {
    STATE.avatarSway = e.target.checked;
    syncStage();
  });
  document.getElementById('avatar-bounce')?.addEventListener('change', (e) => {
    STATE.avatarBounce = e.target.checked;
  });

  // Manual Crop Sliders (Sides & Bottom)
  const updateCrop = () => {
    const left = parseInt(document.getElementById('avatar-crop-left')?.value || '0');
    const right = parseInt(document.getElementById('avatar-crop-right')?.value || '0');
    const bottom = parseInt(document.getElementById('avatar-crop-bottom')?.value || '0');
    const disp = document.getElementById('avatar-crop-display');
    if (disp) disp.textContent = `L: ${left}% | R: ${right}% | B: ${bottom}%`;
    const img = document.getElementById('stage-avatar-img');
    if (img) {
      img.style.clipPath = `inset(0% ${right}% ${bottom}% ${left}%)`;
    }
    STATE.avatarCrop = { left, right, bottom };
  };

  document.getElementById('avatar-crop-left')?.addEventListener('input', updateCrop);
  document.getElementById('avatar-crop-right')?.addEventListener('input', updateCrop);
  document.getElementById('avatar-crop-bottom')?.addEventListener('input', updateCrop);

  window.resetAvatarCrop = function() {
    if (document.getElementById('avatar-crop-left')) document.getElementById('avatar-crop-left').value = 0;
    if (document.getElementById('avatar-crop-right')) document.getElementById('avatar-crop-right').value = 0;
    if (document.getElementById('avatar-crop-bottom')) document.getElementById('avatar-crop-bottom').value = 0;
    updateCrop();
    showToast('Avatar crop reset.', 'info');
  };
}

window.setAvatarPresetPos = function(pos) {
  STATE.avatarAnchor = pos;
  STATE.customLayout.avatar.x = null;
  STATE.customLayout.avatar.y = null;
  document.querySelectorAll('#avatar-pos-group .btn-option').forEach(b => b.classList.remove('active'));
  document.getElementById(`pos-${pos}`)?.classList.add('active');
  syncStage();
};

window.setAvatarGlow = function(color) {
  STATE.avatarGlow = color;
  document.querySelectorAll('#avatar-glow-group .btn-option').forEach(b => b.classList.remove('active'));
  event.target.classList.add('active');
  syncStage();
};

window.toggleAvatarFlip = function() {
  STATE.avatarFlip = !STATE.avatarFlip;
  document.getElementById('btn-avatar-flip').textContent = STATE.avatarFlip ? '🔄 Mirrored (Flipped)' : '🔄 Normal (No Flip)';
  syncStage();
};

function initCaptionControls() {
  // Toggle switch
  document.getElementById('enable-captions')?.addEventListener('change', (e) => {
    STATE.enableCaptions = e.target.checked;
    syncStage();
  });
}

window.selectCaptionPreset = function(card) {
  document.querySelectorAll('.preset-card-visual').forEach(c => c.classList.remove('active'));
  card.classList.add('active');
  STATE.captionPreset = card.dataset.preset;
  syncStage();
  showToast(`Applied preset: ${card.querySelector('.preset-name').textContent}`, 'info');
};

window.setCaptionPresetPos = function(pos) {
  setCaptionPositionPreset(pos);
};

window.setCaptionSize = function(size) {
  STATE.captionSize = size;
  const btnMed = document.getElementById('cap-size-medium');
  const btnLrg = document.getElementById('cap-size-large');
  const btnHug = document.getElementById('cap-size-huge');
  const selectMore = document.getElementById('caption-font-size-more');
  const customRow = document.getElementById('custom-font-size-row');

  // Deactivate all first
  [btnMed, btnLrg, btnHug, selectMore].forEach(el => el?.classList.remove('active'));

  if (size === 'medium') {
    btnMed?.classList.add('active');
    if (selectMore) selectMore.value = "";
    customRow?.classList.add('hidden');
  } else if (size === 'large') {
    btnLrg?.classList.add('active');
    if (selectMore) selectMore.value = "";
    customRow?.classList.add('hidden');
  } else if (size === 'huge') {
    btnHug?.classList.add('active');
    if (selectMore) selectMore.value = "";
    customRow?.classList.add('hidden');
  } else if (size === 'extrahuge') {
    selectMore?.classList.add('active');
    if (selectMore) selectMore.value = "extrahuge";
    customRow?.classList.add('hidden');
  } else if (size === 'small') {
    selectMore?.classList.add('active');
    if (selectMore) selectMore.value = "small";
    customRow?.classList.add('hidden');
  } else if (size === 'custom' || !isNaN(Number(size))) {
    selectMore?.classList.add('active');
    if (selectMore) selectMore.value = "custom";
    customRow?.classList.remove('hidden');
    if (!isNaN(Number(size))) STATE.captionCustomSize = parseInt(size);
  }

  updateCaptionSizeBadge();
  syncStage();
};

window.onCaptionMoreSelect = function(val) {
  if (!val) return;
  setCaptionSize(val);
  const labelMap = {
    extrahuge: '💥 Extra Huge (160px)',
    custom: `Custom (${STATE.captionCustomSize || 150}px)`,
    small: 'Small (80px)'
  };
  showToast(`Caption font size: ${labelMap[val] || val}`, 'info');
};

window.onCaptionSizeSelect = function(val) {
  setCaptionSize(val);
};

window.onCustomFontSizeInput = function(val) {
  const num = Math.max(40, Math.min(220, parseInt(val) || 150));
  STATE.captionCustomSize = num;
  STATE.captionSize = 'custom';
  const slider = document.getElementById('custom-font-size-slider');
  const numberInput = document.getElementById('custom-font-size-number');
  const customBadge = document.getElementById('custom-font-size-badge');
  const sizeBadge = document.getElementById('caption-font-size-badge');

  if (slider && slider.value != num) slider.value = num;
  if (numberInput && numberInput.value != num) numberInput.value = num;
  if (customBadge) customBadge.textContent = `${num}px`;
  if (sizeBadge) sizeBadge.textContent = `Custom (${num}px)`;

  const selectMore = document.getElementById('caption-font-size-more');
  if (selectMore) {
    selectMore.classList.add('active');
    selectMore.value = 'custom';
  }
  document.getElementById('cap-size-medium')?.classList.remove('active');
  document.getElementById('cap-size-large')?.classList.remove('active');
  document.getElementById('cap-size-huge')?.classList.remove('active');

  syncStage();
};

function updateCaptionSizeBadge() {
  const badge = document.getElementById('caption-font-size-badge');
  if (!badge) return;
  const size = STATE.captionSize;
  const map = {
    small: 'Small (80px)',
    medium: 'Medium (95px)',
    large: 'Large (115px)',
    huge: 'Huge (135px)',
    extrahuge: '💥 Extra Huge (160px)',
    custom: `Custom (${STATE.captionCustomSize || 150}px)`
  };
  badge.textContent = map[size] || `${size}px`;
}

// Live Preview Caption Text Renderer
window.renderDemoCaptionHtml = function(rawText) {
  const captionContent = document.getElementById('stage-caption-content');
  if (!captionContent) return;
  const text = (rawText || '').trim();
  if (!text) {
    captionContent.innerHTML = `
      <div class="demo-line" data-line="0">
        <span class="demo-word" data-w="0">WAIT...</span>
        <span class="demo-word" data-w="1">DID</span>
        <span class="demo-word" data-w="2">HE</span>
        <span class="demo-word" data-w="3">REALLY</span>
      </div>
      <div class="demo-line" data-line="1">
        <span class="demo-word" data-w="4">GET</span>
        <span class="demo-word" data-w="5">AN</span>
        <span class="demo-word active" data-w="6">UNFAIR</span>
        <span class="demo-word active" data-w="7">ADVANTAGE?!</span>
      </div>
      <div class="demo-line" data-line="2">
        <span class="demo-word" data-w="8">WATCH</span>
        <span class="demo-word" data-w="9">THIS</span>
        <span class="demo-word active" data-w="10">INSANE</span>
        <span class="demo-word" data-w="11">MOMENT!</span>
      </div>
    `;
    return;
  }

  // Split into lines (either newline or 4-5 words per line)
  const lines = [];
  if (text.includes('\n')) {
    text.split('\n').forEach(l => {
      if (l.trim()) lines.push(l.trim().split(/\s+/));
    });
  } else {
    const words = text.split(/\s+/);
    let cur = [];
    words.forEach(w => {
      cur.push(w);
      if (cur.length >= 4) {
        lines.push(cur);
        cur = [];
      }
    });
    if (cur.length > 0) lines.push(cur);
  }

  let wordIndex = 0;
  let html = '';
  lines.forEach((lineWords, lineIdx) => {
    html += `<div class="demo-line" data-line="${lineIdx}">`;
    lineWords.forEach((word) => {
      const cleanWord = escapeHtml(word);
      const isEmphasis = /[!?]$/.test(word) || (word === word.toUpperCase() && word.length > 3) || (wordIndex % 4 === 2);
      const activeClass = isEmphasis ? ' active' : '';
      html += `<span class="demo-word${activeClass}" data-w="${wordIndex}">${cleanWord}</span>\n`;
      wordIndex++;
    });
    html += `</div>\n`;
  });

  captionContent.innerHTML = html;
};

window.onDemoCaptionTextInput = function(text) {
  STATE.demoCaptionText = text;
  renderDemoCaptionHtml(text);
  syncStage();
};

window.resetDemoCaptionText = function() {
  const defaultText = "WAIT... DID HE REALLY GET AN UNFAIR ADVANTAGE?! WATCH THIS INSANE MOMENT!";
  STATE.demoCaptionText = defaultText;
  const input = document.getElementById('demo-caption-input');
  if (input) input.value = defaultText;
  renderDemoCaptionHtml(defaultText);
  syncStage();
  showToast('Live preview caption text reset to default 3-line sample.', 'info');
};

window.onCaptionFontFamilyChange = function(val) {
  STATE.captionFontFamily = val || 'default';
  const badge = document.getElementById('caption-font-family-badge');
  if (badge) {
    badge.textContent = (val && val !== 'default') ? val : 'Default (Template Font)';
  }
  syncStage();
  if (val && val !== 'default') {
    showToast(`Font family overridden: ${val}`, 'info');
  } else {
    showToast('Using template font style.', 'info');
  }
};

window.toggleCaptionBg = function(enabled) {
  STATE.enableCaptionBg = !!enabled;
  const options = document.getElementById('caption-bg-options');
  if (options) {
    options.classList.toggle('hidden', !enabled);
  }
  syncStage();
  showToast(enabled ? 'Caption Background Box enabled!' : 'Caption Background Box disabled.', 'info');
};

window.updateCaptionBgPreview = function() {
  const colorInput = document.getElementById('caption-bg-color');
  const opacityInput = document.getElementById('caption-bg-opacity');
  const colorLabel = document.getElementById('caption-bg-color-label');
  const opacityBadge = document.getElementById('caption-bg-opacity-badge');

  if (colorInput) STATE.captionBgColor = colorInput.value;
  if (opacityInput) STATE.captionBgOpacity = parseInt(opacityInput.value) || 75;

  if (colorLabel && colorInput) colorLabel.textContent = colorInput.value.toUpperCase();
  if (opacityBadge && opacityInput) opacityBadge.textContent = `${STATE.captionBgOpacity}%`;

  syncStage();
};

// Quick-Cut Duration Buttons (No Cut / 5min / 10min / 15min)
window.setQuickCut = function(minutes) {
  const hiddenInput = document.getElementById('twitch-cut-duration');
  if (hiddenInput) hiddenInput.value = minutes;

  // Update button active states
  [0, 5, 10, 15].forEach(m => {
    const btn = document.getElementById(`cut-btn-${m}`);
    if (btn) btn.classList.toggle('active', m === minutes);
  });

  // Clear custom field when a preset button is selected
  const customField = document.getElementById('twitch-cut-duration-custom');
  if (customField) customField.value = '';

  if (minutes === 0) {
    showToast('No cut — full background stream used.', 'info');
  } else {
    showToast(`Cut set to first ${minutes} minutes of background stream.`, 'info');
  }
};

// Custom Cut duration (typed by user, e.g. "20" for 20 minutes)
window.setQuickCutCustom = function(val) {
  const parsed = parseInt(val);
  const hidden = document.getElementById('twitch-cut-duration');

  // Deactivate preset buttons
  [0, 5, 10, 15].forEach(m => {
    const btn = document.getElementById(`cut-btn-${m}`);
    if (btn) btn.classList.remove('active');
  });

  if (!isNaN(parsed) && parsed > 0) {
    if (hidden) hidden.value = parsed;
  } else if (val === '' || val === '0') {
    if (hidden) hidden.value = 0;
    const nocut = document.getElementById('cut-btn-0');
    if (nocut) nocut.classList.add('active');
  }
};

// ═══════════════════════════════════════════════════════════════════════════
// SOURCE PICKERS (Twitch & YouTube, URLs & Local Files)
// ═══════════════════════════════════════════════════════════════════════════
window.switchSourceMode = function(layer, mode) {
  STATE.sourceModes[layer] = mode;
  const isUrl = mode === 'url';

  if (layer === 'twitch') {
    document.getElementById('btnModeTwitchUrl')?.classList.toggle('active', isUrl);
    document.getElementById('btnModeTwitchFile')?.classList.toggle('active', !isUrl);
    document.getElementById('twitch-url-group')?.classList.toggle('hidden', !isUrl);
    document.getElementById('twitch-file-group')?.classList.toggle('hidden', isUrl);
  } else if (layer === 'yt') {
    document.getElementById('btnModeYtUrl')?.classList.toggle('active', isUrl);
    document.getElementById('btnModeYtFile')?.classList.toggle('active', !isUrl);
    document.getElementById('yt-url-group')?.classList.toggle('hidden', !isUrl);
    document.getElementById('yt-file-group')?.classList.toggle('hidden', isUrl);
  }
};

function initSourcePickers() {
  // 1. Twitch / YouTube Background Probe
  const btnTwitchProbe = document.getElementById('btn-twitch-probe');
  btnTwitchProbe?.addEventListener('click', async () => {
    const url = document.getElementById('twitch-path')?.value.trim();
    if (!url) {
      showToast('Please enter a Twitch or YouTube URL to probe.', 'error');
      return;
    }
    btnTwitchProbe.disabled = true;
    btnTwitchProbe.textContent = 'Probing...';
    try {
      const res = await fetch('/api/probe', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ path_or_url: url })
      });
      const data = await res.json();
      if (res.ok) {
        STATE.twitchDuration = data.duration || 0;
        const badge = document.getElementById('twitch-info-badge');
        const isYt = /youtube\.com|youtu\.be/i.test(url);
        const sourceLabel = isYt ? 'YouTube Background Gameplay' : 'Twitch Stream';
        if (badge) {
          badge.textContent = `✓ ${sourceLabel} Verified: ${formatDuration(data.duration)} (Slices required duration automatically)`;
          badge.classList.remove('hidden');
        }
        showToast(`${sourceLabel} verified!`, 'success');
      } else {
        showToast(`Probe error: ${data.detail}`, 'error');
      }
    } catch (err) {
      showToast(`Error: ${err.message}`, 'error');
    } finally {
      btnTwitchProbe.disabled = false;
      btnTwitchProbe.textContent = 'Probe';
    }
  });

  // 2. Twitch Local File Upload
  const twitchFileInput = document.getElementById('twitch-file-input');
  twitchFileInput?.addEventListener('change', async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    const label = document.getElementById('twitch-filename');
    if (label) label.textContent = `Uploading ${file.name}...`;
    const formData = new FormData();
    formData.append('file', file);

    try {
      const res = await fetch('/api/upload/video', { method: 'POST', body: formData });
      const data = await res.json();
      if (res.ok) {
        STATE.twitchLocalPath = data.path;
        STATE.twitchDuration = data.duration || 0;
        if (label) label.textContent = `✓ ${file.name} (${formatDuration(data.duration)})`;
        showToast('Local background gameplay ready!', 'success');
      } else {
        if (label) label.textContent = `✗ Upload failed. Click to re-select.`;
        showToast(`Upload failed: ${data.detail}`, 'error');
      }
    } catch (err) {
      if (label) label.textContent = `✗ Upload failed: ${err.message}`;
      showToast(`Upload error: ${err.message}`, 'error');
    }
  });

  // 3. YouTube Probe
  const btnYtProbe = document.getElementById('btn-yt-probe');
  btnYtProbe?.addEventListener('click', async () => {
    const url = document.getElementById('yt-path')?.value.trim();
    if (!url) {
      showToast('Please enter a YouTube URL to probe.', 'error');
      return;
    }
    btnYtProbe.disabled = true;
    btnYtProbe.textContent = 'Probing...';
    try {
      const res = await fetch('/api/probe', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ path_or_url: url })
      });
      const data = await res.json();
      if (res.ok) {
        STATE.ytDuration = data.duration || 0;
        const badge = document.getElementById('yt-info-badge');
        if (badge) {
          badge.textContent = `YouTube Reaction: ${formatDuration(data.duration)} (${data.title || 'Stream'})`;
          badge.classList.remove('hidden');
        }
        updateDurationSyncUI(data.duration);
        showToast(`YouTube duration detected: ${formatDuration(data.duration)}`, 'success');
      } else {
        showToast(`Probe error: ${data.detail}`, 'error');
      }
    } catch (err) {
      showToast(`Error: ${err.message}`, 'error');
    } finally {
      btnYtProbe.disabled = false;
      btnYtProbe.textContent = 'Probe';
    }
  });

  // 4. YouTube Local File Upload
  const ytFileInput = document.getElementById('yt-file-input');
  ytFileInput?.addEventListener('change', async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    const label = document.getElementById('yt-filename');
    if (label) label.textContent = `Uploading ${file.name}...`;
    const formData = new FormData();
    formData.append('file', file);

    try {
      const res = await fetch('/api/upload/video', { method: 'POST', body: formData });
      const data = await res.json();
      if (res.ok) {
        STATE.ytLocalPath = data.path;
        STATE.ytDuration = data.duration || 0;
        if (label) label.textContent = `✓ ${file.name} (${formatDuration(data.duration)})`;
        updateDurationSyncUI(data.duration);
        showToast('Local YouTube video ready!', 'success');
      } else {
        if (label) label.textContent = `✗ Upload failed. Click to re-select.`;
        showToast(`Upload failed: ${data.detail}`, 'error');
      }
    } catch (err) {
      if (label) label.textContent = `✗ Upload failed: ${err.message}`;
      showToast(`Upload error: ${err.message}`, 'error');
    }
  });

  // 5. Avatar PNG Upload (Immediately visible on 16:9 canvas!)
  const avatarInput = document.getElementById('avatar-file-input');
  avatarInput?.addEventListener('change', async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    const formData = new FormData();
    formData.append('file', file);

    try {
      const res = await fetch('/api/upload/avatar', { method: 'POST', body: formData });
      const data = await res.json();
      if (res.ok) {
        STATE.avatarPath = data.path;
        STATE.avatarUrl = data.url;
        document.getElementById('avatar-path').value = data.path;
        document.getElementById('avatar-filename').textContent = `✓ ${file.name}`;

        const previewImg = document.getElementById('avatar-preview-img');
        if (previewImg) {
          previewImg.src = data.url;
          previewImg.style.display = 'block';
        }

        // Live update on 16:9 stage canvas!
        const stageImg = document.getElementById('stage-avatar-img');
        if (stageImg) stageImg.src = data.url;

        showToast('Avatar loaded onto 16:9 Director Canvas!', 'success');
      }
    } catch (err) {
      showToast('Avatar upload error', 'error');
    }
  });

  // 6. BGM Audio Upload
  const bgmInput = document.getElementById('bgm-file-input');
  bgmInput?.addEventListener('change', async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    const formData = new FormData();
    formData.append('file', file);

    try {
      const res = await fetch('/api/upload/bgm', { method: 'POST', body: formData });
      const data = await res.json();
      if (res.ok) {
        document.getElementById('bgm-path').value = data.path;
        document.getElementById('bgm-filename').textContent = `✓ ${file.name}`;
        showToast('Ambient BGM track loaded!', 'success');
      }
    } catch (err) {
      showToast('BGM upload error', 'error');
    }
  });

  document.getElementById('bgm-volume')?.addEventListener('input', (e) => {
    document.getElementById('bgm-vol-val').textContent = `${e.target.value}%`;
  });
}

function initReactionControls() {
  const bgBlur = document.getElementById('bg-blur');
  const bgBlurVal = document.getElementById('bg-blur-val');
  const bgLayer = document.getElementById('stage-bg-layer');
  const hudBgBlurPill = document.getElementById('hud-bg-blur-pill');

  const ytBlur = document.getElementById('yt-blur');
  const ytBlurVal = document.getElementById('yt-blur-val');
  const ytOpacity = document.getElementById('yt-opacity');
  const ytOpacityVal = document.getElementById('yt-opacity-val');
  const ytLayer = document.getElementById('stage-yt-layer');
  const hudYtBlurPill = document.getElementById('hud-yt-blur-pill');
  const hudOpacityPill = document.getElementById('hud-opacity-pill');

  const updateBgVisuals = () => {
    const blur = parseInt(bgBlur?.value || '0') || 0;
    if (bgBlurVal) bgBlurVal.textContent = `${blur}px`;
    if (hudBgBlurPill) hudBgBlurPill.textContent = `BG Blur: ${blur}px`;
    if (bgLayer) {
      bgLayer.style.filter = blur > 0 ? `blur(${blur}px)` : 'none';
    }
  };

  const updateYtLayerVisuals = () => {
    const blur = parseInt(ytBlur?.value || '0') || 0;
    const opacityPct = parseInt(ytOpacity?.value || '35') || 35;
    const opacity = opacityPct / 100;

    if (ytBlurVal) ytBlurVal.textContent = `${blur}px`;
    if (hudYtBlurPill) hudYtBlurPill.textContent = `YT Blur: ${blur}px`;

    if (ytOpacityVal) {
      ytOpacityVal.textContent = `${opacityPct}% ${opacityPct >= 75 ? '(Clear Reaction)' : opacityPct >= 50 ? '(Balanced)' : '(Subtle Overlay)'}`;
    }
    if (hudOpacityPill) hudOpacityPill.textContent = `YT: ${opacityPct}%`;

    if (ytLayer) {
      ytLayer.style.filter = blur > 0 ? `blur(${blur}px)` : 'none';
      ytLayer.style.opacity = opacity.toFixed(2);
    }
  };

  bgBlur?.addEventListener('input', updateBgVisuals);
  ytBlur?.addEventListener('input', updateYtLayerVisuals);
  ytOpacity?.addEventListener('input', updateYtLayerVisuals);

  updateBgVisuals();
  updateYtLayerVisuals();
}

function initDurationSync() {
  const fullVideoCheck = document.getElementById('yt-full-video');
  const trimRow = document.getElementById('trim-points-row');

  fullVideoCheck?.addEventListener('change', (e) => {
    const useFull = e.target.checked;
    if (trimRow) {
      trimRow.style.opacity = useFull ? '0.5' : '1';
      trimRow.style.pointerEvents = useFull ? 'none' : 'auto';
    }
    if (useFull && STATE.ytDuration > 0) {
      document.getElementById('yt-out-time').value = formatDuration(STATE.ytDuration);
      updateDurationSyncUI(STATE.ytDuration);
    }
  });
}

function updateDurationSyncUI(durationSec) {
  const badge = document.getElementById('durationSyncBadge');
  const lenPill = document.getElementById('yt-detected-len');
  const outInput = document.getElementById('yt-out-time');

  const durStr = formatDuration(durationSec);
  if (badge) badge.textContent = `Master Output: ${durStr}`;
  if (lenPill) lenPill.textContent = durStr;
  if (outInput && (!outInput.value || outInput.value === '00:00:00')) {
    outInput.value = durStr;
  }
}

// ═══════════════════════════════════════════════════════════════════════════
// MASTER RENDER & QUICK 30S SLICE
// ═══════════════════════════════════════════════════════════════════════════
function initRenderTriggers() {
  const btnStartRender = document.getElementById('btn-start-render');
  btnStartRender?.addEventListener('click', async () => {
    const payload = collectPayload(false);
    if (!payload) return;

    btnStartRender.disabled = true;
    btnStartRender.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Dispatching to GPU...';

    try {
      const res = await fetch('/api/render', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      const data = await res.json();
      if (res.ok) {
        showToast(`Master render task #${data.task_id} queued!`, 'success');
        openDrawer();
      } else {
        showToast(`Render failed: ${formatApiError(data.detail)}`, 'error');
      }
    } catch (err) {
      showToast(`Error: ${err.message}`, 'error');
    } finally {
      btnStartRender.disabled = false;
      btnStartRender.innerHTML = '<i class="fas fa-rocket"></i> START 1080P MASTER RENDER';
    }
  });
}

function collectPayload(isPreview = false) {
  const twitchInput = document.getElementById('twitch-path')?.value.trim();
  const ytInput = document.getElementById('yt-path')?.value.trim();

  let twitchPath = '';
  if (STATE.sourceModes.twitch === 'url') {
    twitchPath = twitchInput;
  } else {
    twitchPath = STATE.twitchLocalPath || twitchInput;
  }

  let ytPath = '';
  if (STATE.sourceModes.yt === 'url') {
    ytPath = ytInput;
  } else {
    ytPath = STATE.ytLocalPath || ytInput;
  }

  if (!twitchPath) {
    showToast(STATE.sourceModes.twitch === 'file' ? 'Please upload a local background video file first.' : 'Please enter a Twitch or YouTube background URL.', 'error');
    return null;
  }
  if (!ytPath) {
    showToast(STATE.sourceModes.yt === 'file' ? 'Please upload a local YouTube video file first.' : 'Please enter a YouTube video URL.', 'error');
    return null;
  }

  const ytInSec = 0.0;
  let ytEndSec = STATE.ytDuration > 0 ? STATE.ytDuration : null;

  return {
    title: "StreamMix 1080p Video",
    twitch_bg_path: twitchPath,
    youtube_main_path: ytPath,
    twitch_start_sec: parseTimeToSeconds(document.getElementById('twitch-start-time')?.value),
    twitch_cut_sec: (parseInt(document.getElementById('twitch-cut-duration')?.value) || 0) * 60,
    yt_start_sec: ytInSec,
    yt_end_sec: ytEndSec,
    bg_blur: parseInt(document.getElementById('bg-blur')?.value) || 0,
    yt_blur: parseInt(document.getElementById('yt-blur')?.value) || 0,
    yt_opacity: parseInt(document.getElementById('yt-opacity')?.value) || 35,
    audio_speed: parseFloat(document.getElementById('audio-speed')?.value) || 1.0,
    pitch_semitones: parseFloat(document.getElementById('pitch-semitones')?.value) || (document.getElementById('acoustic-shield')?.checked ? 0.6 : 0.0),
    bitrate_mode: document.getElementById('bitrate-mode')?.value || "6500k",
    copyright_shield: document.getElementById('acoustic-shield')?.checked ?? true,
    
    // Avatar Parameters (Includes custom canvas drag coordinates & crop)
    enable_avatar: STATE.enableAvatar,
    avatar_path: STATE.avatarPath || document.getElementById('avatar-path')?.value || null,
    avatar_anchor: STATE.avatarAnchor,
    avatar_size: STATE.avatarSize,
    avatar_opacity: STATE.avatarOpacity,
    avatar_sway: STATE.avatarSway,
    avatar_sway_speed: STATE.avatarSwaySpeed,
    avatar_bounce: STATE.avatarBounce,
    avatar_flip: STATE.avatarFlip,
    avatar_glow: STATE.avatarGlow || 'cyan',
    avatar_x: STATE.customLayout.avatar.x !== null ? Math.round(Number(STATE.customLayout.avatar.x)) : null,
    avatar_y: STATE.customLayout.avatar.y !== null ? Math.round(Number(STATE.customLayout.avatar.y)) : null,
    avatar_crop_left: Math.round(Number(STATE.avatarCrop?.left || document.getElementById('avatar-crop-left')?.value || 0)),
    avatar_crop_right: Math.round(Number(STATE.avatarCrop?.right || document.getElementById('avatar-crop-right')?.value || 0)),
    avatar_crop_top: Math.round(Number(STATE.avatarCrop?.top || document.getElementById('avatar-crop-top')?.value || 0)),
    avatar_crop_bottom: Math.round(Number(STATE.avatarCrop?.bottom || document.getElementById('avatar-crop-bottom')?.value || 0)),

    // Captions Parameters (With Font Family & Custom Background Box)
    enable_captions: document.getElementById('enable-captions') ? document.getElementById('enable-captions').checked : !!STATE.enableCaptions,
    caption_preset: STATE.captionPreset,
    caption_font_family: STATE.captionFontFamily || 'default',
    caption_size: (STATE.captionSize === 'custom' ? (STATE.captionCustomSize || 150).toString() : (STATE.captionSize || 'large')),
    enable_caption_bg: !!STATE.enableCaptionBg,
    caption_bg_color: STATE.captionBgColor || '#000000',
    caption_bg_opacity: STATE.captionBgOpacity !== undefined ? STATE.captionBgOpacity : 75,
    caption_x: (() => {
      if (STATE.customLayout.caption.x !== null) return Math.round(Number(STATE.customLayout.caption.x));
      if (STATE.captionPosition === 'center-left') return Math.round(1920 * 0.08);
      if (STATE.captionPosition === 'center-right') return Math.round(1920 * 0.56);
      if (STATE.captionPosition === 'center') return Math.round(1920 * 0.32);
      return Math.round(1920 * 0.20);
    })(),
    caption_y: (() => {
      if (STATE.customLayout.caption.y !== null) return Math.round(Number(STATE.customLayout.caption.y));
      if (STATE.captionPosition === 'center-left') return Math.round(1080 * 0.48);
      if (STATE.captionPosition === 'center-right') return Math.round(1080 * 0.22);
      if (STATE.captionPosition === 'center') return Math.round(1080 * 0.48);
      return Math.round(1080 * 0.65);
    })(),
    caption_w: (() => {
      if (STATE.customLayout.caption.w !== null) return Math.round(Number(STATE.customLayout.caption.w));
      if (STATE.captionPosition === 'bottom') return Math.round(1920 * 0.60);
      return Math.round(1920 * 0.36);
    })(),
    caption_h: (() => {
      if (STATE.customLayout.caption.h !== null) return Math.round(Number(STATE.customLayout.caption.h));
      if (STATE.captionPosition === 'bottom') return Math.round(1080 * 0.20);
      return Math.round(1080 * 0.16);
    })(),

    bgm_path: document.getElementById('bgm-path')?.value || null,
    bgm_volume: (parseInt(document.getElementById('bgm-volume')?.value) || 7) / 100
  };
}

// Quick 30s Slice Test Modal (With Minimize & Background Floating Pill)
function initSliceModal() {
  const btnQuickTest = document.getElementById('btn-quick-test');
  const modal = document.getElementById('modal-slice-test');
  const btnClose = document.getElementById('btn-close-slice-modal');
  const btnMinimize = document.getElementById('btn-minimize-slice-modal');
  const pill = document.getElementById('minimized-slice-pill');
  const pillLabel = document.getElementById('minimized-slice-label');
  const player = document.getElementById('slice-video-player');
  const statusText = document.getElementById('slice-modal-status');

  let activeSliceTaskId = null;

  btnMinimize?.addEventListener('click', () => {
    modal?.classList.add('hidden');
    pill?.classList.remove('hidden');
  });

  window.restoreSliceModal = function() {
    modal?.classList.remove('hidden');
    pill?.classList.add('hidden');
    pill?.classList.remove('pill-done');
  };

  btnClose?.addEventListener('click', () => {
    modal?.classList.add('hidden');
    if (player) {
      player.pause();
      if (player.src && player.src.startsWith('blob:')) {
        try { URL.revokeObjectURL(player.src); } catch (_) {}
      }
      player.src = '';
    }
  });

  // Make Minimized Slice / Render Pill Moveable Anywhere on Screen
  if (pill) {
    let isDraggingPill = false;
    let pillStartX = 0;
    let pillStartY = 0;
    let pointerStartX = 0;
    let pointerStartY = 0;
    let pillMoved = false;

    pill.addEventListener('pointerdown', (e) => {
      if (e.button && e.button !== 0) return;
      isDraggingPill = true;
      pillMoved = false;
      pointerStartX = e.clientX;
      pointerStartY = e.clientY;

      const rect = pill.getBoundingClientRect();
      pillStartX = rect.left;
      pillStartY = rect.top;

      pill.classList.add('dragging');

      const onMove = (me) => {
        if (!isDraggingPill) return;
        const dx = me.clientX - pointerStartX;
        const dy = me.clientY - pointerStartY;

        if (!pillMoved && (Math.abs(dx) > 3 || Math.abs(dy) > 3)) {
          pillMoved = true;
        }

        if (pillMoved) {
          me.preventDefault();
          let newX = pillStartX + dx;
          let newY = pillStartY + dy;

          const maxW = window.innerWidth - pill.offsetWidth - 8;
          const maxH = window.innerHeight - pill.offsetHeight - 8;

          newX = Math.max(8, Math.min(maxW, newX));
          newY = Math.max(8, Math.min(maxH, newY));

          pill.style.position = 'fixed';
          pill.style.left = `${newX}px`;
          pill.style.top = `${newY}px`;
          pill.style.right = 'auto';
          pill.style.bottom = 'auto';
        }
      };

      const onUp = () => {
        isDraggingPill = false;
        pill.classList.remove('dragging');
        window.removeEventListener('pointermove', onMove);
        window.removeEventListener('pointerup', onUp);
        window.removeEventListener('pointercancel', onUp);

        // Pure click (did not drag): handle modal or drawer restore
        if (!pillMoved) {
          handlePillClick();
        }
      };

      window.addEventListener('pointermove', onMove, { passive: false });
      window.addEventListener('pointerup', onUp);
      window.addEventListener('pointercancel', onUp);
    });
  }

  function handlePillClick() {
    const modal = document.getElementById('modal-slice-test');
    const player = document.getElementById('slice-video-player');
    if (player && player.src && player.src.includes('/outputs/') && modal && modal.classList.contains('hidden')) {
      modal.classList.remove('hidden');
      player.play();
    } else {
      const drawer = document.getElementById('taskDrawer');
      if (drawer && drawer.classList.contains('open')) {
        drawer.classList.remove('open');
      } else {
        openDrawer();
      }
    }
  }

  btnQuickTest?.addEventListener('click', async () => {
    const payload = collectPayload(true);
    if (!payload) return;

    modal?.classList.remove('hidden');
    pill?.classList.add('hidden');
    pill?.classList.remove('pill-done');
    if (statusText) statusText.textContent = 'Rendering 30s fast slice on GPU (~15s)...';
    if (player) {
      player.style.display = 'none';
      player.src = '';
    }

    try {
      const res = await fetch('/api/preview', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      const data = await res.json();
      if (res.ok) {
        activeSliceTaskId = data.task_id;
        pollSliceTask(data.task_id);
      } else {
        const errorMsg = formatApiError(data.detail);
        if (statusText) {
          statusText.innerHTML = `
            <div style="color: var(--accent-rose); margin-bottom: 8px;">
              <i class="fas fa-exclamation-circle"></i> Slice error: ${errorMsg}
            </div>
            <button type="button" class="btn-modal-action" onclick="openLogsModal()">
              <i class="fas fa-file-waveform"></i> View Logs
            </button>
          `;
        }
      }
    } catch (err) {
      if (statusText) statusText.textContent = `Error: ${err.message}`;
    }
  });

  function pollSliceTask(taskId) {
    const pollInterval = setInterval(async () => {
      try {
        const res = await fetch('/api/tasks');
        if (!res.ok) return;
        const tasks = await res.json();
        const task = tasks.find(t => t.id === taskId);
        if (!task) return;

        if (task.status === 'ACTIVE') {
          const prog = task.progress ? task.progress.toFixed(1) : '0.0';
          const fps = task.fps || 0;
          if (statusText) statusText.textContent = `Rendering: ${prog}% | ${fps} FPS`;
          // Minimized pill status is centrally handled by updatePillMonitor with 3.8s calm cycling
        } else if (task.status === 'COMPLETED' || task.status === 'DONE') {
          clearInterval(pollInterval);
          if (modal) {
            modal.classList.remove('hidden');
          }
          if (pill) {
            pill.classList.add('hidden');
            pill.classList.remove('pill-done');
          }
          if (statusText) statusText.textContent = 'Render Complete! 30s preview playing below:';
          if (player) {
            const filename = task.output_path.split('\\').pop();
            player.src = `/outputs/${encodeURIComponent(filename)}`;
            player.style.display = 'block';
            player.play();
          }
          showToast('⚡ 30s Fast Slice Preview is Ready!', 'success');
        } else if (task.status === 'FAILED' || task.status === 'CANCELLED' || task.status === 'ERROR') {
          clearInterval(pollInterval);
          pill?.classList.add('hidden');
          if (modal) modal.classList.remove('hidden');
          if (statusText) {
            statusText.innerHTML = `
              <div style="color: var(--accent-rose); margin-bottom: 8px;">
                <i class="fas fa-exclamation-triangle"></i> Task Failed: ${task.error || 'Check error log'}
              </div>
              <button type="button" class="btn-modal-action" onclick="openLogsModal()">
                <i class="fas fa-file-waveform"></i> Open Error Log Details
              </button>
            `;
          }
        }
      } catch (err) {
        clearInterval(pollInterval);
      }
    }, 1000);
  }
}

// Background Task Poller & Drawer Renderer
function startTaskPolling() {
  if (STATE.pollTimer) clearInterval(STATE.pollTimer);
  STATE.pollTimer = setInterval(fetchTasks, 1500);
  fetchTasks();
}

async function fetchTasks() {
  try {
    const res = await fetch('/api/tasks');
    if (!res.ok) return;
    const tasks = await res.json();
    STATE.tasks = tasks;
    renderTasksInDrawer(tasks);
    updatePillMonitor(tasks);
  } catch (err) {}
}

let _pillTickerIndex = 0;
let _pillTickerTimer = null;
let _currentPillItems = [];
let _lastPillRenderedText = '';

function updatePillMonitor(tasks) {
  const pill = document.getElementById('minimized-slice-pill');
  const pillLabel = document.getElementById('minimized-slice-label');
  const modal = document.getElementById('modal-slice-test');
  if (!pill || !pillLabel) return;

  const isModalOpen = modal && !modal.classList.contains('hidden');
  const activeTasks = (tasks || []).filter(t => t.status === 'ACTIVE' || t.status === 'QUEUED');
  const completedRecent = (tasks || []).filter(t => t.status === 'COMPLETED' || t.status === 'DONE');

  // If 30s preview modal is open, hide pill
  if (isModalOpen) {
    pill.classList.add('hidden');
    return;
  }

  // If no tasks at all, hide pill
  if (activeTasks.length === 0 && completedRecent.length === 0) {
    pill.classList.add('hidden');
    if (_pillTickerTimer) {
      clearInterval(_pillTickerTimer);
      _pillTickerTimer = null;
    }
    return;
  }

  // Show floating pill for both 30s Slice and Master 1080p
  pill.classList.remove('hidden');

  if (activeTasks.length > 0) {
    pill.classList.remove('pill-done');
    const items = activeTasks.map(t => {
      const tag = t.is_preview ? '30s Slice' : 'Master 1080p';
      const stage = t.stage || (t.progress ? `Compositing ${t.progress.toFixed(0)}%` : 'Running...');
      return `<i class="fas fa-bolt text-accent"></i> <strong>${tag} (#${t.id})</strong>: ${stage}`;
    });

    _currentPillItems = items;
    if (_pillTickerIndex >= items.length) _pillTickerIndex = 0;

    // Only render immediately if empty or changed
    if (!_lastPillRenderedText) {
      renderCurrentPillItem();
    }

    if (!_pillTickerTimer) {
      // 3.8 second calm cycling between background tasks with smooth fade transition
      _pillTickerTimer = setInterval(() => {
        if (_currentPillItems.length > 1) {
          _pillTickerIndex = (_pillTickerIndex + 1) % _currentPillItems.length;
        } else {
          _pillTickerIndex = 0;
        }
        if (pillLabel) {
          pillLabel.style.transition = 'opacity 0.25s ease';
          pillLabel.style.opacity = '0';
          setTimeout(() => {
            renderCurrentPillItem();
            pillLabel.style.opacity = '1';
          }, 250);
        }
      }, 3800);
    }
  } else {
    // Active tasks finished! Show completed badge with clickable action
    if (_pillTickerTimer) {
      clearInterval(_pillTickerTimer);
      _pillTickerTimer = null;
    }
    pill.classList.add('pill-done');
    const latest = completedRecent[0];
    const filename = latest && latest.output_path ? latest.output_path.split('\\').pop() : '';
    pillLabel.innerHTML = `<i class="fas fa-check-circle" style="color:var(--accent-green)"></i> <strong>Ready</strong>: ${filename || 'Render Complete! Click to View'}`;
    _lastPillRenderedText = filename;
  }
}

function renderCurrentPillItem() {
  const pillLabel = document.getElementById('minimized-slice-label');
  if (pillLabel && _currentPillItems.length > 0) {
    const text = _currentPillItems[_pillTickerIndex % _currentPillItems.length];
    pillLabel.innerHTML = text;
    _lastPillRenderedText = text;
  }
}

function renderTasksInDrawer(tasks) {
  const container = document.getElementById('drawerTaskBody');
  const badgeCount = document.getElementById('taskCountBadge');
  if (!container) return;

  const activeCount = tasks.filter(t => t.status === 'ACTIVE' || t.status === 'QUEUED').length;
  if (badgeCount) badgeCount.textContent = activeCount;

  if (tasks.length === 0) {
    container.innerHTML = '<div class="dock-empty">No active rendering tasks.</div>';
    return;
  }

  container.innerHTML = tasks.slice(0, 10).map(task => {
    const isActive = task.status === 'ACTIVE';
    const isDone = task.status === 'COMPLETED' || task.status === 'DONE';
    const isFailed = task.status === 'FAILED';
    const isCancelled = task.status === 'CANCELLED';

    let badgeClass = 'status-processing';
    if (isDone) badgeClass = 'status-completed';
    if (isFailed) badgeClass = 'status-failed';
    if (isCancelled) badgeClass = 'status-cancelled';

    const filename = task.output_path ? task.output_path.split('\\').pop() : '';

    return `
      <div class="task-item">
        <div class="task-item-header">
          <span class="task-title">
            <i class="fas fa-video"></i> ${task.is_preview ? '⚡ 30s Slice' : 'Master 1080p'} (#${task.id})
          </span>
          <span class="task-badge ${badgeClass}">${task.status}</span>
        </div>
        <div class="task-progress-bar-bg">
          <div class="task-progress-bar-fill" style="width: ${Math.min(100, Math.max(0, task.progress))}%"></div>
        </div>

        <!-- Multi-Bar Live Download Monitors (Twitch in Purple, YouTube in Red) -->
        ${(() => {
          const dl = task.downloads || {};
          const tw = dl.twitch || {};
          const yt = dl.youtube || {};
          const twPct = tw.pct !== undefined ? tw.pct : (isDone ? 100 : 0);
          const ytPct = yt.pct !== undefined ? yt.pct : (isDone ? 100 : 0);
          const twStatus = tw.status || (isDone ? '✓ Ready' : (tw.is_local ? '✓ Local File' : 'Waiting...'));
          const ytStatus = yt.status || (isDone ? '✓ Ready' : (yt.is_local ? '✓ Local File' : 'Waiting...'));

          return `
            <div class="task-sub-bars-container">
              <!-- Twitch Stream Download Bar (Purple #9146ff) -->
              <div class="task-sub-bar-row">
                <div class="task-sub-bar-label">
                  <span><i class="fab fa-twitch" style="color: #9146ff"></i> Twitch Stream</span>
                  <span class="sub-bar-val" style="color: ${twPct >= 100 ? 'var(--accent-green)' : '#bf55ec'}">${twStatus}</span>
                </div>
                <div class="task-sub-progress-bg">
                  <div class="task-sub-progress-fill sub-fill-twitch" style="width: ${Math.min(100, Math.max(0, twPct))}%"></div>
                </div>
              </div>

              <!-- YouTube Video Download Bar (Red #ef4444) -->
              <div class="task-sub-bar-row">
                <div class="task-sub-bar-label">
                  <span><i class="fab fa-youtube" style="color: #ef4444"></i> YouTube Main</span>
                  <span class="sub-bar-val" style="color: ${ytPct >= 100 ? 'var(--accent-green)' : '#f87171'}">${ytStatus}</span>
                </div>
                <div class="task-sub-progress-bg">
                  <div class="task-sub-progress-fill sub-fill-youtube" style="width: ${Math.min(100, Math.max(0, ytPct))}%"></div>
                </div>
              </div>
            </div>
          `;
        })()}
        
        <div class="task-status-row">
          <div class="task-progress-large">
            ${task.progress ? task.progress.toFixed(1) : '0.0'}%
          </div>
          <div class="task-stage-badge">
            <span class="stage-text">${task.stage || (isDone ? 'Render Complete!' : task.status)}</span>
            ${isActive && task.fps > 0 ? `<span class="fps-pill">${task.fps} FPS</span>` : ''}
            ${isActive && task.eta && task.eta !== '--:--' ? `<span class="eta-pill">ETA: ${task.eta}</span>` : ''}
          </div>
        </div>

        ${isActive ? `
          <div style="margin-top: 6px;">
            <button class="btn-task-cancel" onclick="cancelTask('${task.id}')">
              <i class="fas fa-stop"></i> Cancel Task
            </button>
          </div>
        ` : ''}

        ${isDone && task.output_path ? `
          <div class="task-done-card">
            <div class="task-ready-name">
              <i class="fas fa-check-circle" style="color:var(--accent-green)"></i> Ready: ${filename}
            </div>
            <div class="task-action-btns">
              <button type="button" class="btn-task-action btn-play" onclick="playTaskVideo('${encodeURIComponent(filename)}')">
                <i class="fas fa-play"></i> ▶ Play Video
              </button>
              <button type="button" class="btn-task-action btn-folder" onclick="openOutputFolder()">
                <i class="fas fa-folder-open"></i> 📁 Open Folder
              </button>
            </div>
          </div>
        ` : ''}

        ${isFailed ? `
          <div style="font-size: 11px; color: var(--accent-rose); margin-top: 6px; display:flex; align-items:center; justify-content:space-between;">
            <span><i class="fas fa-exclamation-triangle"></i> ${task.error ? task.error.substring(0, 45) + '...' : 'Failed'}</span>
            <button class="btn-action-small" onclick="openLogsModal()" style="font-size:10px; padding:2px 6px;">View Log</button>
          </div>
        ` : ''}
      </div>
    `;
  }).join('');
}

window.playTaskVideo = function(encodedFilename) {
  const filename = decodeURIComponent(encodedFilename);
  const modal = document.getElementById('modal-slice-test');
  const player = document.getElementById('slice-video-player');
  const statusText = document.getElementById('slice-modal-status');
  if (modal && player) {
    modal.classList.remove('hidden');
    if (statusText) statusText.textContent = `Playing: ${filename}`;
    player.src = `/outputs/${encodeURIComponent(filename)}`;
    player.style.display = 'block';
    player.play();
  }
};

window.openOutputFolder = async function() {
  try {
    await fetch('/api/open-output', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({})
    });
    showToast('Opening Outputs folder in Windows Explorer...', 'info');
  } catch (err) {
    showToast('Could not open folder automatically.', 'error');
  }
};

window.cancelTask = async function(taskId) {
  if (!confirm('Are you sure you want to cancel this render?')) return;
  try {
    const res = await fetch(`/api/tasks/${taskId}/cancel`, { method: 'POST' });
    if (res.ok) {
      showToast('Task cancelled.', 'info');
      fetchTasks();
    }
  } catch (err) {
    showToast(`Cancel failed: ${err.message}`, 'error');
  }
};

window.clearFinishedTasks = async function() {
  try {
    const res = await fetch('/api/tasks/clear-completed', { method: 'POST' });
    if (res.ok) {
      const data = await res.json();
      showToast(`Cleaned up ${data.cleared_count || 0} completed/cancelled task(s).`, 'success');
      await fetchTasks();
    } else {
      showToast('Could not clear tasks.', 'error');
    }
  } catch (err) {
    showToast(`Clear error: ${err.message}`, 'error');
  }
};

// API Keys Pool
async function loadApiKeys() {
  try {
    const res = await fetch('/api/keys');
    if (res.ok) {
      const data = await res.json();
      STATE.apiKeys = Array.isArray(data) ? data : (data.keys || []);
      renderKeysTable();
    }
  } catch (err) {
    console.error('Failed to load keys', err);
  }
}

function renderKeysTable() {
  const tbody = document.getElementById('keys-table-body');
  if (!tbody) return;

  if (!STATE.apiKeys || STATE.apiKeys.length === 0) {
    tbody.innerHTML = '<tr><td colspan="6" class="text-center py-4">No keys registered in pool. Add one below.</td></tr>';
    return;
  }

  tbody.innerHTML = STATE.apiKeys.map(k => {
    const masked = k.key && k.key.length > 10 ? `${k.key.slice(0, 7)}...${k.key.slice(-4)}` : '••••••••';
    const isHealthy = k.status === 'HEALTHY' || k.status === 'active';
    return `
      <tr>
        <td><strong>${k.label || 'Groq Key'}</strong></td>
        <td><code>${masked}</code></td>
        <td><span class="badge ${isHealthy ? 'badge-success' : 'badge-danger'}">${k.status || 'ACTIVE'}</span></td>
        <td>${k.latency_ms > 0 ? `${k.latency_ms} ms` : 'Not tested'}</td>
        <td>${k.total_transcriptions || 0}</td>
        <td>
          <button class="btn-action-small" onclick="testKey('${k.key}')" title="Test Key Latency">
            <i class="fas fa-tachometer-alt"></i> Ping
          </button>
          <button class="btn-action-small btn-danger" onclick="deleteKey('${k.id || k.key}')" title="Delete Key">
            <i class="fas fa-trash"></i>
          </button>
        </td>
      </tr>
    `;
  }).join('');
}

window.testKey = async function(key) {
  showToast('Testing key latency...', 'info');
  try {
    const res = await fetch('/api/keys/test', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ key })
    });
    const data = await res.json();
    if (res.ok) {
      showToast(`Key Ping: ${data.latency_ms} ms! Status: Healthy`, 'success');
      await loadApiKeys();
    } else {
      showToast(`Key failed: ${data.detail}`, 'error');
    }
  } catch (err) {
    showToast(`Ping error: ${err.message}`, 'error');
  }
};

window.deleteKey = async function(keyId) {
  if (!confirm('Remove this key from the pool?')) return;
  try {
    const res = await fetch(`/api/keys/${encodeURIComponent(keyId)}`, { method: 'DELETE' });
    if (res.ok) {
      showToast('Key removed.', 'info');
      await loadApiKeys();
      await checkGroqApiHealth();
    }
  } catch (err) {
    showToast(`Error: ${err.message}`, 'error');
  }
};

document.getElementById('form-add-key')?.addEventListener('submit', async (e) => {
  e.preventDefault();
  const label = document.getElementById('new-key-label')?.value.trim();
  const key = document.getElementById('new-key-value')?.value.trim();
  if (!key) return;

  try {
    const res = await fetch('/api/keys', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ key, label })
    });
    if (res.ok) {
      showToast('Key added to rotation pool!', 'success');
      document.getElementById('new-key-label').value = '';
      document.getElementById('new-key-value').value = '';
      await loadApiKeys();
      await checkGroqApiHealth();
    } else {
      const d = await res.json();
      showToast(`Error: ${d.detail}`, 'error');
    }
  } catch (err) {
    showToast(`Error: ${err.message}`, 'error');
  }
});

// --- GROQ API HEALTH CHECK & ALERT BANNER ---
async function checkGroqApiHealth() {
  const banner = document.getElementById('groq-health-banner');
  const bannerMsg = document.getElementById('groq-health-msg');
  const bannerTitle = document.getElementById('groq-health-title');
  if (!banner) return;

  try {
    const res = await fetch('/api/keys/status');
    if (!res.ok) return;
    const data = await res.json();

    if (!data.has_working_key || data.healthy_count === 0) {
      banner.classList.remove('hidden');
      if (bannerTitle) bannerTitle.textContent = '⚠️ Groq Whisper API Alert:';
      if (bannerMsg) {
        bannerMsg.innerHTML = data.total_keys === 0
          ? 'No Groq API keys found! Auto-captions & transcriptions will fail. Please click <strong>Update / Replace Key</strong> below.'
          : `${data.message} Please update your key in the API Keys Pool to enable auto-captions.`;
      }
    } else {
      banner.classList.add('hidden');
      console.log(`[GroqPool] Connected & Healthy: ${data.healthy_count} valid key(s).`);
    }
  } catch (err) {
    console.warn('Groq health check note:', err);
  }
}

window.switchToApiKeysTab = function() {
  const tabBtn = document.getElementById('tabBtnPool');
  if (tabBtn) tabBtn.click();
  dismissGroqBanner();
};

window.dismissGroqBanner = function() {
  const banner = document.getElementById('groq-health-banner');
  if (banner) banner.classList.add('hidden');
};

// --- STORAGE & CACHE CLEANER MANAGEMENT ---
async function loadStorageStats(updateModal = false) {
  try {
    const res = await fetch('/api/storage/stats');
    if (!res.ok) return;
    const data = await res.json();
    if (!data.success) return;

    // Update Header Button Badge
    const badge = document.getElementById('storageHeaderBadge');
    if (badge && data.cache_reclaimable) {
      badge.textContent = `Cache: ${data.cache_reclaimable.formatted}`;
    }

    if (updateModal) {
      const tempSize = document.getElementById('storage-temp-size');
      const tempSub = document.getElementById('storage-temp-sub');
      const dlSize = document.getElementById('storage-downloads-size');
      const dlSub = document.getElementById('storage-downloads-sub');
      const outSize = document.getElementById('storage-outputs-size');
      const reclaimTotal = document.getElementById('storage-reclaim-total');

      if (tempSize) tempSize.textContent = data.temp.formatted;
      if (tempSub) tempSub.textContent = `data/temp/ (${data.temp.files} files)`;
      if (dlSize) dlSize.textContent = data.downloads.formatted;
      if (dlSub) dlSub.textContent = `data/downloads/ (${data.downloads.files} files)`;
      if (outSize) outSize.textContent = data.outputs.formatted;
      if (reclaimTotal) reclaimTotal.textContent = data.cache_reclaimable.formatted;
    }
  } catch (err) {
    console.warn('Failed to load storage stats:', err);
  }
}

window.openStorageModal = function() {
  const modal = document.getElementById('modal-storage-cleaner');
  const resBox = document.getElementById('storage-clean-result');
  if (resBox) resBox.classList.add('hidden');
  if (modal) {
    modal.classList.remove('hidden');
    loadStorageStats(true);
  }
};

window.closeStorageModal = function() {
  const modal = document.getElementById('modal-storage-cleaner');
  if (modal) modal.classList.add('hidden');
};

window.executeStorageClean = async function() {
  const cleanTemp = document.getElementById('clean-check-temp')?.checked ?? true;
  const cleanDl = document.getElementById('clean-check-downloads')?.checked ?? true;
  const cleanOut = document.getElementById('clean-check-outputs')?.checked ?? false;

  if (!cleanTemp && !cleanDl && !cleanOut) {
    showToast('Please select at least one cache category to clean.', 'info');
    return;
  }

  if (cleanOut) {
    const confirmOut = confirm('⚠️ WARNING: You selected to delete completed master output videos in data/outputs/. Are you sure you want to delete finished renders?');
    if (!confirmOut) return;
  }

  const btn = document.getElementById('btn-execute-clean');
  if (btn) {
    btn.disabled = true;
    btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Cleaning...';
  }

  try {
    const res = await fetch('/api/storage/clean', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        clean_temp: cleanTemp,
        clean_downloads: cleanDl,
        clean_outputs: cleanOut
      })
    });
    const result = await res.json();
    if (result.success) {
      const resBox = document.getElementById('storage-clean-result');
      if (resBox) {
        resBox.classList.remove('hidden');
        resBox.innerHTML = `
          <strong><i class="fas fa-check-circle"></i> Clean Complete!</strong><br>
          Freed <strong>${result.freed_formatted}</strong> (${result.deleted_count} files removed).
          ${!cleanOut ? '<span>Completed master videos were <strong>safely preserved</strong>.</span>' : ''}
        `;
      }
      showToast(`✓ Freed ${result.freed_formatted} of project cache!`, 'success');
      await loadStorageStats(true);
    } else {
      showToast('Cleanup encountered an issue.', 'error');
    }
  } catch (err) {
    showToast(`Cleanup error: ${err.message}`, 'error');
  } finally {
    if (btn) {
      btn.disabled = false;
      btn.innerHTML = '<i class="fas fa-trash-alt"></i> Purge Selected Cache';
    }
  }
};

// Groq AI SEO Metadata Generator
function initMetadataGenerator() {
  const btn = document.getElementById('btn-generate-metadata');
  btn?.addEventListener('click', async () => {
    const topic = document.getElementById('meta-topic-input')?.value.trim();
    if (!topic) {
      showToast('Please enter a reaction video topic.', 'error');
      return;
    }

    btn.disabled = true;
    btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Generating with Groq Llama-3...';

    try {
      const res = await fetch('/api/metadata/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text_or_topic: topic })
      });
      const data = await res.json();
      if (res.ok) {
        renderMetadata(data);
        showToast('Viral metadata suite generated!', 'success');
      } else {
        showToast(`Metadata error: ${data.detail}`, 'error');
      }
    } catch (err) {
      showToast(`Connection error: ${err.message}`, 'error');
    } finally {
      btn.disabled = false;
      btn.innerHTML = '<i class="fas fa-sparkles"></i> Generate SEO Pack';
    }
  });
}

function renderMetadata(meta) {
  const container = document.getElementById('meta-results-container');
  if (!container) return;

  container.classList.remove('hidden');
  container.innerHTML = `
    <div class="meta-section">
      <h4><span><i class="fas fa-fire text-primary"></i> 5 High-CTR Viral Titles</span> <button class="btn-copy" onclick="copyText('meta-titles-box')">Copy</button></h4>
      <div id="meta-titles-box" class="meta-titles-list">
        ${(meta.titles || []).map(t => `<div>• <strong>${t}</strong></div>`).join('')}
      </div>
    </div>

    <div class="meta-section">
      <h4><span><i class="fas fa-align-left text-primary"></i> SEO Video Description</span> <button class="btn-copy" onclick="copyText('meta-desc-box')">Copy</button></h4>
      <textarea id="meta-desc-box" class="meta-textarea" rows="4" readonly>${meta.description || ''}</textarea>
    </div>

    <div class="meta-section">
      <h4><span><i class="fas fa-bookmark text-primary"></i> YouTube Chapters</span> <button class="btn-copy" onclick="copyText('meta-chapters-box')">Copy</button></h4>
      <textarea id="meta-chapters-box" class="meta-textarea" rows="3" readonly>${meta.chapters || ''}</textarea>
    </div>

    <div class="meta-section">
      <h4><span><i class="fas fa-tags text-primary"></i> Tags</span> <button class="btn-copy" onclick="copyText('meta-tags-box')">Copy</button></h4>
      <div id="meta-tags-box" style="font-size: 11.5px; color: var(--accent-cyan);">
        ${(meta.tags || []).map(tag => `#${tag}`).join('  ')}
      </div>
    </div>
  `;
}

window.copyText = function(id) {
  const el = document.getElementById(id);
  if (!el) return;
  const text = el.value || el.innerText;
  navigator.clipboard.writeText(text).then(() => {
    showToast('Copied to clipboard!', 'success');
  });
};

// Settings
async function loadSettings() {
  try {
    const res = await fetch('/api/settings');
    if (res.ok) {
      const s = await res.json();
      if (document.getElementById('setting-encoder')) document.getElementById('setting-encoder').value = s.hardware_encoder || 'auto';
    }
  } catch (err) {
    console.error('Settings load error', err);
  }
}

function initSettingsListeners() {
  document.getElementById('form-settings')?.addEventListener('submit', async (e) => {
    e.preventDefault();
    const payload = {
      hardware_encoder: document.getElementById('setting-encoder')?.value || 'auto',
      render_crf: parseInt(document.getElementById('setting-crf')?.value) || 19,
      render_preset: document.getElementById('setting-preset')?.value || 'p4'
    };
    try {
      const res = await fetch('/api/settings', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      if (res.ok) {
        showToast('Settings saved successfully.', 'success');
      }
    } catch (err) {
      showToast('Error saving settings', 'error');
    }
  });
}

// ═══════════════════════════════════════════════════════════════════════════
// PRO CONTROLS: BITRATE, PITCH, SPEED & ERROR LOGS SYSTEM
// ═══════════════════════════════════════════════════════════════════════════
window.setBitrateMode = function(mode) {
  const hiddenInput = document.getElementById('bitrate-mode');
  if (hiddenInput) hiddenInput.value = mode;
  document.querySelectorAll('#bitrate-mode-group .btn-option').forEach(btn => {
    btn.classList.toggle('active', btn.getAttribute('data-bitrate') === mode);
  });
};

function initProAudioAndBitrateControls() {
  const speedSlider = document.getElementById('audio-speed');
  const speedVal = document.getElementById('audio-speed-val');
  speedSlider?.addEventListener('input', (e) => {
    const val = parseFloat(e.target.value).toFixed(2);
    let desc = 'Normal';
    if (val < 1.0) desc = 'Slower / Dramatic';
    else if (val > 1.0) desc = 'Faster / Snappy';
    if (speedVal) speedVal.textContent = `${val}x (${desc})`;
  });

  const pitchSlider = document.getElementById('pitch-semitones');
  const pitchVal = document.getElementById('pitch-semitones-val');
  pitchSlider?.addEventListener('input', (e) => {
    const val = parseFloat(e.target.value).toFixed(1);
    let desc = 'Neutral';
    if (val > 0) desc = 'Higher / Timbre Up';
    else if (val < 0) desc = 'Deeper / Gravitas';
    if (pitchVal) pitchVal.textContent = `${val > 0 ? '+' : ''}${val} st (${desc})`;
  });
}

window.openLogsModal = async function() {
  const modal = document.getElementById('modal-logs');
  modal?.classList.remove('hidden');
  await fetchLogs();
};

async function fetchLogs() {
  const pre = document.getElementById('logs-content-pre');
  const pathBar = document.getElementById('logs-file-path');
  if (pre) pre.textContent = 'Fetching latest system logs...';
  try {
    const res = await fetch('/api/logs');
    const data = await res.json();
    if (res.ok) {
      if (pre) pre.textContent = data.logs || 'No errors logged yet. System running smoothly.';
      if (pathBar) pathBar.textContent = `Log File: ${data.log_path || 'data/logs/error.log'}`;
      if (pre) pre.scrollTop = pre.scrollHeight;
    } else {
      if (pre) pre.textContent = 'Failed to load logs.';
    }
  } catch (err) {
    if (pre) pre.textContent = `Error connecting to log API: ${err.message}`;
  }
}

function initLogsModal() {
  document.getElementById('btnOpenLogs')?.addEventListener('click', window.openLogsModal);
  document.getElementById('btnDrawerOpenLogs')?.addEventListener('click', window.openLogsModal);
  document.getElementById('btn-close-logs-modal')?.addEventListener('click', () => {
    document.getElementById('modal-logs')?.classList.add('hidden');
  });
  document.getElementById('btn-refresh-logs')?.addEventListener('click', fetchLogs);
  document.getElementById('btn-copy-logs')?.addEventListener('click', () => {
    const text = document.getElementById('logs-content-pre')?.textContent;
    if (text) {
      navigator.clipboard.writeText(text);
      showToast('Logs copied to clipboard!', 'success');
    }
  });
  document.getElementById('btn-clear-logs')?.addEventListener('click', async () => {
    try {
      await fetch('/api/logs', { method: 'DELETE' });
      await fetchLogs();
      showToast('Error log cleared!', 'success');
    } catch (e) {
      showToast('Could not clear logs', 'error');
    }
  });
}

// ═══════════════════════════════════════════════════════════════════════════
// AUTOMATIC TRANSPARENT PADDING TRIMMER (Clings avatar tightly to frame)
// ═══════════════════════════════════════════════════════════════════════════
window.autoTrimAvatar = async function() {
  const imgEl = document.getElementById('stage-avatar-img');
  if (!imgEl || !imgEl.src || imgEl.src.startsWith('data:image/svg')) {
    showToast('Please upload an avatar image first.', 'error');
    return;
  }

  showToast('Analyzing and cropping blank transparent borders...', 'info');

  const img = new Image();
  img.crossOrigin = 'anonymous';
  img.onload = async function() {
    const canvas = document.createElement('canvas');
    canvas.width = img.naturalWidth || img.width;
    canvas.height = img.naturalHeight || img.height;
    const ctx = canvas.getContext('2d');
    ctx.drawImage(img, 0, 0);

    let imgData;
    try {
      imgData = ctx.getImageData(0, 0, canvas.width, canvas.height);
    } catch (err) {
      showToast('Cannot read image pixels (CORS restriction). Try re-uploading file.', 'error');
      return;
    }

    const data = imgData.data;
    let minX = canvas.width, maxX = 0, minY = canvas.height, maxY = 0;
    let found = false;

    for (let y = 0; y < canvas.height; y++) {
      for (let x = 0; x < canvas.width; x++) {
        const alpha = data[(y * canvas.width + x) * 4 + 3];
        if (alpha > 12) {
          if (x < minX) minX = x;
          if (x > maxX) maxX = x;
          if (y < minY) minY = y;
          if (y > maxY) maxY = y;
          found = true;
        }
      }
    }

    if (!found) {
      showToast('Avatar image appears fully blank/transparent!', 'error');
      return;
    }

    // Safety margins
    minX = Math.max(0, minX - 2);
    minY = Math.max(0, minY - 2);
    maxX = Math.min(canvas.width, maxX + 2);
    maxY = Math.min(canvas.height, maxY + 2);

    const cropW = maxX - minX;
    const cropH = maxY - minY;

    const trimmedCanvas = document.createElement('canvas');
    trimmedCanvas.width = cropW;
    trimmedCanvas.height = cropH;
    const tCtx = trimmedCanvas.getContext('2d');
    tCtx.drawImage(canvas, minX, minY, cropW, cropH, 0, 0, cropW, cropH);

    trimmedCanvas.toBlob(async (blob) => {
      if (!blob) return;
      const formData = new FormData();
      formData.append('file', blob, 'trimmed_avatar.png');
      try {
        const res = await fetch('/api/upload/avatar', { method: 'POST', body: formData });
        const resData = await res.json();
        if (res.ok) {
          STATE.avatarPath = resData.path;
          STATE.avatarUrl = resData.url;
          document.getElementById('avatar-path').value = resData.path;
          document.getElementById('stage-avatar-img').src = resData.url;
          const thumb = document.getElementById('avatar-preview-img');
          if (thumb) { thumb.src = resData.url; thumb.style.display = 'block'; }
          showToast(`✓ Blank margins removed! Cutout fitted to ${cropW}×${cropH}px`, 'success');
        }
      } catch (err) {
        showToast(`Auto-trim upload error: ${err.message}`, 'error');
      }
    }, 'image/png');
  };
  img.src = imgEl.src;
};


