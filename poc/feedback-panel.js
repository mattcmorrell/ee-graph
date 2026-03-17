/* ================================================================
   EMBEDDED FEEDBACK PANEL
   Adds a push-in feedback drawer to any v4 mock.
   Include via: <script src="feedback-panel.js"></script>

   Requires: .tab-btn elements with data-tab attrs for tab detection.
   Optional: .sub-tab-btn or .sub-tab elements for sub-tab detection.

   Saves feedback to decision-journal-server on port 3334.
   Falls back to localStorage if server is unavailable.
   ================================================================ */
(function() {
  var SAVE_URL = 'http://localhost:3334/save-feedback';
  var GET_URL = 'http://localhost:3334/get-feedback';
  var FILE_PATH = 'poc/' + location.pathname.split('/').pop();
  var LS_KEY = 'feedback-' + FILE_PATH;
  var serverOnline = null;
  var drawerOpen = false;
  var DRAWER_WIDTH = 360;

  var allFeedback = [];

  // ---- Load / Save ----
  function loadFeedback(cb) {
    fetch(GET_URL + '?file=' + encodeURIComponent(FILE_PATH))
      .then(function(r) { serverOnline = true; return r.json(); })
      .then(function(data) {
        if (Array.isArray(data) && data.length > 0) { allFeedback = data; saveLs(); }
        else { loadLs(); }
        if (cb) cb();
      })
      .catch(function() { serverOnline = false; loadLs(); if (cb) cb(); });
  }

  function loadLs() {
    try { var d = localStorage.getItem(LS_KEY); if (d) allFeedback = JSON.parse(d); } catch(e) {}
  }
  function saveLs() {
    try { localStorage.setItem(LS_KEY, JSON.stringify(allFeedback)); } catch(e) {}
  }
  function saveToServer() {
    saveLs();
    fetch(SAVE_URL, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ file: FILE_PATH, feedback: allFeedback })
    })
    .then(function(r) { serverOnline = true; updateStatus(); return r.json(); })
    .catch(function() { serverOnline = false; updateStatus(); });
  }

  // ---- Tab detection ----
  function getActiveTab() {
    var btn = document.querySelector('.tab-btn.active');
    if (btn) return btn.textContent.trim().replace(/\s*\d+\s*$/, '');
    return 'General';
  }
  function getActiveSubTab() {
    var activePanel = document.querySelector('.tab-panel.active, .tab-content.active');
    if (activePanel) {
      var subBtn = activePanel.querySelector('.sub-tab-btn.active, .sub-tab.active');
      if (subBtn) return subBtn.textContent.trim();
    }
    return null;
  }
  function getFullTabName() {
    var tab = getActiveTab();
    var sub = getActiveSubTab();
    return sub ? tab + ' > ' + sub : tab;
  }
  function getFeedbackForTab(tabName) {
    return allFeedback.filter(function(f) { return f.tab === tabName; });
  }

  // ---- Styles ----
  function injectStyles() {
    var css = document.createElement('style');
    css.textContent =
      'body{transition:margin-right 0.3s ease;}' +
      'body.fb-drawer-open{margin-right:' + DRAWER_WIDTH + 'px;}' +

      '#fb-toggle{position:fixed;bottom:20px;right:20px;z-index:9999;width:48px;height:48px;border-radius:50%;' +
        'background:linear-gradient(135deg,#8b5cf6,#6d28d9);border:none;color:#fff;font-size:20px;cursor:pointer;' +
        'box-shadow:0 4px 20px rgba(139,92,246,0.4);transition:all 0.3s;display:flex;align-items:center;justify-content:center;}' +
      '#fb-toggle:hover{transform:scale(1.1);box-shadow:0 6px 28px rgba(139,92,246,0.6);}' +
      '#fb-toggle.has-feedback{background:linear-gradient(135deg,#059669,#10b981);box-shadow:0 4px 20px rgba(16,185,129,0.4);}' +
      'body.fb-drawer-open #fb-toggle{right:' + (DRAWER_WIDTH + 20) + 'px;}' +

      '#fb-drawer{position:fixed;top:0;right:-' + DRAWER_WIDTH + 'px;width:' + DRAWER_WIDTH + 'px;height:100vh;z-index:9998;' +
        'background:#0d0d14;border-left:1px solid rgba(255,255,255,0.08);display:flex;flex-direction:column;' +
        'transition:right 0.3s ease;font-family:"Inter",-apple-system,sans-serif;overflow:hidden;}' +
      '#fb-drawer.open{right:0;}' +
      '#fb-drawer *{box-sizing:border-box;}' +

      '.fb-header{padding:16px 18px;border-bottom:1px solid rgba(255,255,255,0.06);display:flex;align-items:center;justify-content:space-between;flex-shrink:0;}' +
      '.fb-header h3{font-size:13px;font-weight:600;color:#e0e0e8;margin:0;}' +
      '.fb-close{background:none;border:none;color:#666;font-size:18px;cursor:pointer;padding:4px 8px;border-radius:4px;transition:all 0.15s;}' +
      '.fb-close:hover{color:#e0e0e8;background:rgba(255,255,255,0.06);}' +
      '.fb-status{font-size:10px;font-weight:600;padding:3px 8px;border-radius:10px;margin-left:8px;}' +
      '.fb-status.online{background:rgba(16,185,129,0.15);color:#34d399;}' +
      '.fb-status.offline{background:rgba(251,191,36,0.15);color:#fbbf24;}' +

      '.fb-tab-name{padding:10px 18px;font-size:11px;font-weight:600;color:#8b5cf6;text-transform:uppercase;letter-spacing:0.06em;' +
        'border-bottom:1px solid rgba(255,255,255,0.04);background:rgba(139,92,246,0.04);flex-shrink:0;}' +

      '.fb-body{padding:16px 18px;overflow-y:auto;flex:1;}' +
      '.fb-field{margin-bottom:14px;}' +
      '.fb-label{font-size:11px;font-weight:600;color:#888;text-transform:uppercase;letter-spacing:0.05em;margin-bottom:6px;}' +

      '.fb-stars{display:flex;gap:4px;}' +
      '.fb-star{width:28px;height:28px;border-radius:6px;border:1px solid rgba(255,255,255,0.1);background:transparent;' +
        'color:#555;font-size:16px;cursor:pointer;transition:all 0.15s;display:flex;align-items:center;justify-content:center;font-family:inherit;}' +
      '.fb-star:hover,.fb-star.active{background:rgba(251,191,36,0.15);border-color:rgba(251,191,36,0.3);color:#fbbf24;}' +

      '.fb-select{width:100%;background:#1a1a28;border:1px solid rgba(255,255,255,0.1);color:#e0e0e8;font-family:inherit;' +
        'font-size:13px;padding:8px 12px;border-radius:8px;appearance:none;cursor:pointer;}' +
      '.fb-select:focus{outline:none;border-color:rgba(139,92,246,0.4);}' +

      '.fb-textarea{width:100%;background:#1a1a28;border:1px solid rgba(255,255,255,0.1);color:#e0e0e8;font-family:inherit;' +
        'font-size:13px;padding:10px 12px;border-radius:8px;resize:vertical;min-height:80px;line-height:1.5;}' +
      '.fb-textarea:focus{outline:none;border-color:rgba(139,92,246,0.4);}' +
      '.fb-textarea::placeholder{color:#555;}' +

      '.fb-save-btn{width:100%;padding:10px;background:linear-gradient(135deg,#8b5cf6,#6d28d9);border:none;color:#fff;' +
        'font-family:inherit;font-size:13px;font-weight:600;border-radius:8px;cursor:pointer;transition:all 0.2s;margin-top:4px;}' +
      '.fb-save-btn:hover{opacity:0.9;}' +
      '.fb-save-btn:active{transform:scale(0.98);}' +

      '.fb-saved-msg{text-align:center;font-size:12px;color:#34d399;font-weight:600;margin-top:8px;opacity:0;transition:opacity 0.3s;}' +
      '.fb-saved-msg.show{opacity:1;}' +

      '.fb-history{margin-top:16px;border-top:1px solid rgba(255,255,255,0.06);padding-top:12px;}' +
      '.fb-history-toggle{font-size:11px;font-weight:600;color:#666;text-transform:uppercase;letter-spacing:0.05em;' +
        'margin-bottom:8px;cursor:pointer;display:flex;align-items:center;gap:6px;background:none;border:none;padding:0;font-family:inherit;}' +
      '.fb-history-toggle:hover{color:#999;}' +
      '.fb-history-toggle .arrow{transition:transform 0.2s;font-size:10px;}' +
      '.fb-history-toggle .arrow.open{transform:rotate(90deg);}' +
      '.fb-history-list{display:none;}' +
      '.fb-history-list.open{display:block;}' +

      '.fb-entry{padding:10px 12px;background:rgba(255,255,255,0.02);border:1px solid rgba(255,255,255,0.04);' +
        'border-radius:8px;margin-bottom:8px;font-size:12px;color:#999;line-height:1.5;}' +
      '.fb-entry-meta{display:flex;justify-content:space-between;margin-bottom:4px;font-size:11px;color:#666;}' +
      '.fb-entry-stars{color:#fbbf24;font-size:11px;}' +
      '.fb-entry-verdict{font-size:11px;font-weight:600;color:#8b5cf6;}';
    document.head.appendChild(css);
  }

  // ---- Build UI ----
  function buildPanel() {
    // Toggle button
    var toggle = document.createElement('button');
    toggle.id = 'fb-toggle';
    toggle.innerHTML = '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>';
    toggle.title = 'Feedback';
    toggle.onclick = toggleDrawer;
    document.body.appendChild(toggle);

    // Drawer
    var drawer = document.createElement('div');
    drawer.id = 'fb-drawer';
    drawer.innerHTML =
      '<div class="fb-header">' +
        '<h3>Feedback<span class="fb-status" id="fb-status"></span></h3>' +
        '<button class="fb-close" onclick="document.getElementById(\'fb-toggle\').click()">&times;</button>' +
      '</div>' +
      '<div class="fb-tab-name" id="fb-tab-name"></div>' +
      '<div class="fb-body">' +
        '<div class="fb-field">' +
          '<div class="fb-label">Idea</div>' +
          '<div class="fb-stars" id="fb-stars-idea">' +
            '<button class="fb-star" data-v="1">&#9733;</button>' +
            '<button class="fb-star" data-v="2">&#9733;</button>' +
            '<button class="fb-star" data-v="3">&#9733;</button>' +
            '<button class="fb-star" data-v="4">&#9733;</button>' +
            '<button class="fb-star" data-v="5">&#9733;</button>' +
          '</div>' +
        '</div>' +
        '<div class="fb-field">' +
          '<div class="fb-label">Execution</div>' +
          '<div class="fb-stars" id="fb-stars-exec">' +
            '<button class="fb-star" data-v="1">&#9733;</button>' +
            '<button class="fb-star" data-v="2">&#9733;</button>' +
            '<button class="fb-star" data-v="3">&#9733;</button>' +
            '<button class="fb-star" data-v="4">&#9733;</button>' +
            '<button class="fb-star" data-v="5">&#9733;</button>' +
          '</div>' +
        '</div>' +
        '<div class="fb-field">' +
          '<div class="fb-label">Verdict</div>' +
          '<select class="fb-select" id="fb-verdict">' +
            '<option value="">Select...</option>' +
            '<option value="Build Deeper">Build Deeper</option>' +
            '<option value="Fix UX & Keep">Fix UX & Keep</option>' +
            '<option value="Good As-Is">Good As-Is</option>' +
            '<option value="Merge Into Another">Merge Into Another</option>' +
            '<option value="Cut">Cut</option>' +
          '</select>' +
        '</div>' +
        '<div class="fb-field">' +
          '<div class="fb-label">Notes</div>' +
          '<textarea class="fb-textarea" id="fb-notes" placeholder="What works, what doesn\'t, what you\'d change..." rows="4"></textarea>' +
        '</div>' +
        '<button class="fb-save-btn" id="fb-save">Save Feedback</button>' +
        '<div class="fb-saved-msg" id="fb-saved">Saved!</div>' +
        '<div class="fb-history" id="fb-history"></div>' +
      '</div>';
    document.body.appendChild(drawer);

    // Wire stars for both groups
    ['fb-stars-idea', 'fb-stars-exec'].forEach(function(groupId) {
      document.querySelectorAll('#' + groupId + ' .fb-star').forEach(function(star) {
        star.addEventListener('click', function() {
          var val = parseInt(this.dataset.v);
          document.querySelectorAll('#' + groupId + ' .fb-star').forEach(function(s) {
            s.classList.toggle('active', parseInt(s.dataset.v) <= val);
          });
        });
      });
    });

    // Wire save
    document.getElementById('fb-save').addEventListener('click', saveFeedback);

    // Update on tab switch
    document.querySelectorAll('.tab-btn').forEach(function(btn) {
      btn.addEventListener('click', function() { setTimeout(refreshPanel, 50); });
    });
  }

  function toggleDrawer() {
    drawerOpen = !drawerOpen;
    document.getElementById('fb-drawer').classList.toggle('open', drawerOpen);
    document.body.classList.toggle('fb-drawer-open', drawerOpen);
    if (drawerOpen) refreshPanel();
  }

  function refreshPanel() {
    var tabName = getFullTabName();
    var tabEl = document.getElementById('fb-tab-name');
    if (tabEl) tabEl.textContent = tabName;

    // Reset form
    document.querySelectorAll('#fb-stars-idea .fb-star, #fb-stars-exec .fb-star').forEach(function(s) { s.classList.remove('active'); });
    var verdictEl = document.getElementById('fb-verdict');
    if (verdictEl) verdictEl.value = '';
    var notesEl = document.getElementById('fb-notes');
    if (notesEl) notesEl.value = '';
    var savedEl = document.getElementById('fb-saved');
    if (savedEl) savedEl.classList.remove('show');

    updateStatus();
    renderHistory(tabName);
    updateToggle();
  }

  function updateStatus() {
    var el = document.getElementById('fb-status');
    if (!el) return;
    if (serverOnline === true) { el.className = 'fb-status online'; el.textContent = 'saving to file'; }
    else if (serverOnline === false) { el.className = 'fb-status offline'; el.textContent = 'offline - local only'; }
    else { el.className = 'fb-status'; el.textContent = ''; }
  }

  function updateToggle() {
    var btn = document.getElementById('fb-toggle');
    if (!btn) return;
    var tabName = getFullTabName();
    btn.classList.toggle('has-feedback', getFeedbackForTab(tabName).length > 0);
  }

  function renderHistory(tabName) {
    var container = document.getElementById('fb-history');
    if (!container) return;
    var entries = getFeedbackForTab(tabName);
    if (entries.length === 0) { container.innerHTML = ''; return; }

    var html = '<button class="fb-history-toggle" id="fb-hist-toggle">' +
      '<span class="arrow" id="fb-hist-arrow">&#9654;</span> Previous feedback (' + entries.length + ')' +
    '</button><div class="fb-history-list" id="fb-hist-list">';

    entries.slice().reverse().forEach(function(e) {
      // Support both old (rating) and new (ideaRating/execRating) formats
      var ideaR = e.ideaRating || e.rating || 0;
      var execR = e.execRating || 0;
      function starsHtml(n) { var s=''; for(var i=0;i<5;i++) s+=i<n?'&#9733;':'&#9734;'; return s; }
      var date = e.timestamp ? new Date(e.timestamp).toLocaleDateString('en-US', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' }) : '?';
      html += '<div class="fb-entry">' +
        '<div class="fb-entry-meta"><span>' + date + '</span>' +
        (e.verdict ? '<span class="fb-entry-verdict">' + e.verdict + '</span>' : '') +
        '</div>' +
        '<div class="fb-entry-stars">' +
          (ideaR ? '<span title="Idea">&#128161; ' + starsHtml(ideaR) + '</span>' : '') +
          (execR ? '<span title="Execution" style="margin-left:8px;">&#9881; ' + starsHtml(execR) + '</span>' : '') +
        '</div>' +
        (e.notes ? '<div style="margin-top:4px;">' + e.notes.replace(/</g, '&lt;') + '</div>' : '') +
      '</div>';
    });
    html += '</div>';
    container.innerHTML = html;

    // Wire toggle
    var toggleBtn = document.getElementById('fb-hist-toggle');
    if (toggleBtn) {
      toggleBtn.addEventListener('click', function() {
        var arrow = document.getElementById('fb-hist-arrow');
        var list = document.getElementById('fb-hist-list');
        if (arrow) arrow.classList.toggle('open');
        if (list) list.classList.toggle('open');
      });
    }
  }

  function saveFeedback() {
    var tabName = getFullTabName();
    var ideaRating = 0;
    document.querySelectorAll('#fb-stars-idea .fb-star.active').forEach(function() { ideaRating++; });
    var execRating = 0;
    document.querySelectorAll('#fb-stars-exec .fb-star.active').forEach(function() { execRating++; });
    var verdict = document.getElementById('fb-verdict').value;
    var notes = document.getElementById('fb-notes').value.trim();
    if (!ideaRating && !execRating && !verdict && !notes) return;

    allFeedback.push({
      timestamp: new Date().toISOString(),
      tab: tabName,
      ideaRating: ideaRating || null,
      execRating: execRating || null,
      verdict: verdict || null,
      notes: notes || null
    });
    saveToServer();

    var msg = document.getElementById('fb-saved');
    if (msg) { msg.classList.add('show'); setTimeout(function() { msg.classList.remove('show'); }, 2000); }
    refreshPanel();
  }

  // ---- Init ----
  function init() {
    injectStyles();
    loadFeedback(function() {
      buildPanel();
      updateStatus();
      updateToggle();
      // Re-bind sub-tab clicks after dynamic content loads
      setTimeout(function() {
        document.querySelectorAll('.sub-tab-btn, .sub-tab').forEach(function(btn) {
          btn.addEventListener('click', function() { setTimeout(refreshPanel, 100); });
        });
      }, 2000);
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    setTimeout(init, 500);
  }
})();
