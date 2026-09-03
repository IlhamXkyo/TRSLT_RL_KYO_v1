/* ==========================================================================
   GAME VOICE TRANSLATOR OVERLAY - CONTROLLER & REAL-TIME AUDIO CLIENT
   ========================================================================== */

document.addEventListener('DOMContentLoaded', () => {
  // DOM Elements
  const widget = document.getElementById('floating-widget');
  const header = document.getElementById('widget-header');
  const resizeGrip = document.getElementById('resize-grip');
  const subtitlesFeed = document.getElementById('subtitles-feed');
  const vadBadge = document.getElementById('vad-status-badge');
  const vadBarContainer = document.querySelector('.vad-activity-bar');
  
  // Action Buttons
  const btnSettings = document.getElementById('btn-settings');
  const btnCloseSettings = document.getElementById('btn-close-settings');
  const settingsDrawer = document.getElementById('settings-drawer');
  const btnLock = document.getElementById('btn-lock');
  const iconLock = document.getElementById('icon-lock');
  const iconUnlock = document.getElementById('icon-unlock');
  const btnClickThrough = document.getElementById('btn-clickthrough');
  const btnClear = document.getElementById('btn-clear');
  
  // Settings Inputs
  const themeBtns = document.querySelectorAll('.theme-card-btn');
  const sliderOpacity = document.getElementById('slider-opacity');
  const valOpacity = document.getElementById('val-opacity');
  const sliderFontsize = document.getElementById('slider-fontsize');
  const valFontsize = document.getElementById('val-fontsize');
  const sliderSensitivity = document.getElementById('slider-sensitivity');
  const valSensitivity = document.getElementById('val-sensitivity');
  const selectLangInput = document.getElementById('select-lang-input');
  const selectLangOutput = document.getElementById('select-lang-output');

  // Application State
  let isLocked = false;
  let isClickThrough = false;
  let isDragging = false;
  let isResizing = false;
  let dragOffset = { x: 0, y: 0 };
  let initialSize = { width: 440, height: 220 };
  let initialMouse = { x: 0, y: 0 };

  /* --------------------------------------------------------------------------
     1. DRAG & DROP LOGIC (Native Windows 1-Shot Drag via Win32)
     -------------------------------------------------------------------------- */
  let startBrowserX = 0, startBrowserY = 0;

  header.addEventListener('mousedown', (e) => {
    if (isLocked || e.target.closest('button')) return;

    // Mode Desktop: Panggil native Windows drag (1-shot Win32 WM_NCLBUTTONDOWN)
    if (window.pywebview && window.pywebview.api && window.pywebview.api.start_drag) {
      window.pywebview.api.start_drag();
      return;
    }

    // Mode Desktop Tauri
    if (window.__TAURI__ && window.__TAURI__.window) {
      window.__TAURI__.window.appWindow.startDragging();
      return;
    }

    // Fallback jika dibuka lewat browser Chrome/Edge biasa
    isDragging = true;
    startBrowserX = e.clientX;
    startBrowserY = e.clientY;
  });

  /* --------------------------------------------------------------------------
     2. CORNER RESIZING (Native Windows 1-Shot Resize via Win32)
     -------------------------------------------------------------------------- */
  resizeGrip.addEventListener('mousedown', (e) => {
    e.stopPropagation();

    // Mode Desktop: Panggil native Windows corner resize (1-shot Win32 HTBOTTOMRIGHT)
    if (window.pywebview && window.pywebview.api && window.pywebview.api.start_resize) {
      window.pywebview.api.start_resize();
      return;
    }

    // Fallback jika dibuka lewat browser biasa
    isResizing = true;
    initialMouse.x = e.clientX;
    initialMouse.y = e.clientY;
    initialSize.width = widget.offsetWidth;
    initialSize.height = widget.offsetHeight;
  });

  document.addEventListener('mousemove', (e) => {
    // Hanya dieksekusi di browser biasa (bukan desktop .exe)
    if (isDragging && !isLocked) {
      const dx = e.clientX - startBrowserX;
      const dy = e.clientY - startBrowserY;
      startBrowserX = e.clientX;
      startBrowserY = e.clientY;
      widget.style.left = `${widget.offsetLeft + dx}px`;
      widget.style.top = `${widget.offsetTop + dy}px`;
    }

    if (isResizing) {
      const deltaX = e.clientX - initialMouse.x;
      const deltaY = e.clientY - initialMouse.y;
      widget.style.width = `${Math.max(300, initialSize.width + deltaX)}px`;
      widget.style.height = `${Math.max(160, initialSize.height + deltaY)}px`;
    }
  });

  document.addEventListener('mouseup', () => {
    isDragging = false;
    isResizing = false;
  });

  /* --------------------------------------------------------------------------
     3. LOCK POSITION (PIN)
     -------------------------------------------------------------------------- */
  btnLock.addEventListener('click', () => {
    isLocked = !isLocked;
    if (isLocked) {
      iconLock.classList.remove('hidden');
      iconUnlock.classList.add('hidden');
      btnLock.classList.add('active-btn');
      header.style.cursor = 'default';
      btnLock.title = "Buka Kunci Posisi";
    } else {
      iconLock.classList.add('hidden');
      iconUnlock.classList.remove('hidden');
      btnLock.classList.remove('active-btn');
      header.style.cursor = 'grab';
      btnLock.title = "Kunci Posisi (Cegah Geser)";
    }
  });

  /* --------------------------------------------------------------------------
     4. CLICK-THROUGH MODE & CLEAR BUTTON
     -------------------------------------------------------------------------- */
  btnClickThrough.addEventListener('click', () => {
    isClickThrough = !isClickThrough;
    if (isClickThrough) {
      btnClickThrough.classList.add('active-btn');
      alert("Mode Tembus Klik Aktif!\nKlik mouse akan menembus ke game di belakang.\nTekan 'Alt + C' untuk menonaktifkan kembali.");
      widget.classList.add('click-through');
    } else {
      btnClickThrough.classList.remove('active-btn');
      widget.classList.remove('click-through');
    }
  });

  // Bersihkan semua subtitle yang sedang tampil di layar
  if (btnClear) {
    btnClear.addEventListener('click', () => {
      subtitlesFeed.innerHTML = `
        <div id="standby-card" class="subtitle-card active-card">
          <div class="card-meta">
            <span class="speaker-tag speaker-teammate">
              <span class="speaker-icon">🎧</span> System Audio Loopback
            </span>
            <span class="time-tag">Mendengarkan</span>
          </div>
          <div class="original-text">Menunggu percakapan berikutnya...</div>
          <div class="translated-text">Suara game / video yang keluar akan otomatis diterjemahkan di sini.</div>
          <div class="hud-accent-line"></div>
        </div>
      `;
    });
  }

  // Global Hotkey
  document.addEventListener('keydown', (e) => {
    if (e.altKey && e.key.toLowerCase() === 'c') {
      btnClickThrough.click();
    }
    if (e.altKey && e.key.toLowerCase() === 'l') {
      btnLock.click();
    }
    if (e.altKey && e.key.toLowerCase() === 't') {
      widget.classList.toggle('hidden');
    }
    if (e.altKey && e.key.toLowerCase() === 'x') {
      if (btnClear) btnClear.click();
    }
  });

  /* --------------------------------------------------------------------------
     5. THEME SWITCHER
     -------------------------------------------------------------------------- */
  themeBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      const selectedTheme = btn.getAttribute('data-theme');
      document.body.className = selectedTheme;
      themeBtns.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
    });
  });

  /* --------------------------------------------------------------------------
     6. SETTINGS DRAWER & DYNAMIC CONFIG SYNC
     -------------------------------------------------------------------------- */
  btnSettings.addEventListener('click', () => {
    settingsDrawer.classList.toggle('hidden');
  });

  btnCloseSettings.addEventListener('click', () => {
    settingsDrawer.classList.add('hidden');
  });

  sliderOpacity.addEventListener('input', (e) => {
    const val = e.target.value;
    valOpacity.textContent = `${val}%`;
    document.documentElement.style.setProperty('--bg-opacity', val / 100);
  });

  sliderFontsize.addEventListener('input', (e) => {
    const val = e.target.value;
    valFontsize.textContent = `${val}px`;
    document.documentElement.style.setProperty('--base-font-size', `${val}px`);
  });

  function syncConfigToBackend() {
    const thresholdVal = parseFloat(sliderSensitivity.value);
    valSensitivity.textContent = `${thresholdVal} RMS`;
    
    fetch('/api/config', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        threshold: thresholdVal,
        source_lang: selectLangInput.value,
        target_lang: selectLangOutput.value
      })
    }).catch(() => {});
  }

  if (sliderSensitivity) {
    sliderSensitivity.addEventListener('input', syncConfigToBackend);
  }
  if (selectLangInput) {
    selectLangInput.addEventListener('change', syncConfigToBackend);
  }
  if (selectLangOutput) {
    selectLangOutput.addEventListener('change', syncConfigToBackend);
  }

  /* --------------------------------------------------------------------------
     7. LIVE SUBTITLE INGESTION & ERROR SANITIZATION
     -------------------------------------------------------------------------- */
  function isErrorText(text) {
    if (!text) return true;
    const lower = text.toLowerCase();
    const badPatterns = [
        "error 500", "server error", "that's an error", 
        "please try again later", "429", "too many requests", 
        "rate limit", "service unavailable", "bad gateway",
        "internal error", "error 403", "forbidden"
    ];
    return badPatterns.some(p => lower.includes(p));
  }

  function displayLiveSubtitle(data) {
    if (!data.original || !data.translated) return;
    
    // Filter error text agar tidak pernah tampil di bubble pengguna
    if (isErrorText(data.translated)) {
      data.translated = data.original; // Fallback ke teks asli jika terjemahan error
    }

    // Hapus kartu status awal standby jika ada
    const standby = document.getElementById('standby-card');
    if (standby) {
      standby.remove();
    }

    // Buat kartu subtitle baru
    const card = document.createElement('div');
    card.className = 'subtitle-card active-card';
    
    card.innerHTML = `
      <div class="card-meta">
        <span class="speaker-tag">
          <span class="speaker-icon">🔊</span> ${data.speaker || 'Game Audio'}
        </span>
        <span class="time-tag">Baru Saja</span>
      </div>
      <div class="original-text">"${data.original}"</div>
      <div class="translated-text">"${data.translated}"</div>
      <div class="hud-accent-line"></div>
    `;
    
    // Turunkan status kartu lama
    const existingCards = subtitlesFeed.querySelectorAll('.subtitle-card');
    existingCards.forEach((c) => {
      c.classList.remove('active-card');
      c.classList.add('history-card');
      const time = c.querySelector('.time-tag');
      if (time && time.textContent === 'Baru Saja') {
        time.textContent = 'beberapa detik lalu';
      }
    });

    subtitlesFeed.insertBefore(card, subtitlesFeed.firstChild);

    // Batasi maksimal 4 kartu di layar agar tetap rapi
    if (subtitlesFeed.children.length > 4) {
      subtitlesFeed.removeChild(subtitlesFeed.lastChild);
    }
  }

  /* --------------------------------------------------------------------------
     8. SSE EVENT STREAM (WASAPI LOOPBACK LISTENER)
     -------------------------------------------------------------------------- */
  try {
    const evtSource = new EventSource('/events');
    
    evtSource.onopen = () => {
      console.log('[OVERLAY] SSE Terhubung ke backend /events');
      vadBadge.textContent = 'WASAPI LIVE';
      vadBadge.classList.remove('speaking');
    };

    evtSource.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        
        if (data.type === 'connected') {
          console.log('[OVERLAY] Server status:', data.status);
          vadBadge.textContent = 'WASAPI LIVE';
          vadBadge.classList.remove('speaking');
          if (data.threshold && sliderSensitivity) {
            sliderSensitivity.value = data.threshold;
            valSensitivity.textContent = `${data.threshold} RMS`;
          }
        } else if (data.type === 'volume') {
          // Visualizer bergerak secara real-time mengikuti volume asli speaker
          vadBarContainer.classList.add('waveform-active');
          
          const curThreshold = sliderSensitivity ? parseFloat(sliderSensitivity.value) : 70;
          if (data.rms > curThreshold) {
            vadBadge.textContent = 'SPEECH DETECTED';
            vadBadge.classList.add('speaking');
          } else {
            vadBadge.textContent = 'AUDIO ACTIVE';
            vadBadge.classList.remove('speaking');
          }
          
          clearTimeout(window.vadResetTimeout);
          window.vadResetTimeout = setTimeout(() => {
            vadBarContainer.classList.remove('waveform-active');
            vadBadge.textContent = 'WASAPI LIVE';
            vadBadge.classList.remove('speaking');
          }, 350);
          
        } else if (data.type === 'subtitle') {
          console.log('[OVERLAY] Subtitle baru diterima:', data);
          // Suara nyata dari game/layar berhasil ditranskrip & diterjemahkan!
          displayLiveSubtitle(data);
        }
      } catch (err) {
        console.log('SSE parsing error:', err);
      }
    };
    
    evtSource.onerror = (e) => {
      console.warn('[OVERLAY] SSE connection error / reconnecting...', e);
      vadBadge.textContent = 'RECONNECTING...';
    };
  } catch (e) {
    console.log('Error initializing EventSource:', e);
  }
});
