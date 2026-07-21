// ===== CITY DROPDOWN WITH "OTHERS" =====
function initCitySelect(selectId, otherId) {
  const sel = document.getElementById(selectId);
  const otherInput = document.getElementById(otherId);
  if (!sel || !otherInput) return;
  sel.addEventListener('change', function() {
    if (this.value === 'Others') {
      otherInput.style.display = 'block';
      otherInput.required = true;
    } else {
      otherInput.style.display = 'none';
      otherInput.required = false;
      otherInput.value = '';
    }
  });
}

// ===== EXPERIENCE FIELD =====
function initExperienceSelect(selectId, yearsId) {
  const sel = document.getElementById(selectId);
  const yearsInput = document.getElementById(yearsId);
  if (!sel || !yearsInput) return;
  sel.addEventListener('change', function() {
    if (this.value === 'Experienced') {
      yearsInput.style.display = 'block';
      yearsInput.required = true;
    } else {
      yearsInput.style.display = 'none';
      yearsInput.required = false;
      yearsInput.value = '';
    }
  });
}

// ===== ALERTS AUTO-DISMISS =====
function initAlerts() {
  const alerts = document.querySelectorAll('.alert-auto');
  alerts.forEach(a => {
    setTimeout(() => {
      a.style.opacity = '0';
      a.style.transition = 'opacity 0.4s';
      setTimeout(() => a.remove(), 400);
    }, 4000);
  });
}

// ===== YEARS AUTO-SUFFIX =====
function initYearsAutoSuffix(inputId) {
  var inp = document.getElementById(inputId);
  if (!inp) return;
  inp.addEventListener('blur', function() {
    var v = this.value.trim();
    if (v && /^\d+(\.\d+)?$/.test(v) && !/year/i.test(v)) {
      this.value = v + (v === '1' ? ' Year' : ' Years');
    }
  });
}

document.addEventListener('DOMContentLoaded', function() {
  initCitySelect('citySelect', 'cityOther');
  initCitySelect('citySelectEdit', 'cityOtherEdit');
  initCitySelect('jobCity', 'jobCityOther');
  initExperienceSelect('jobExp', 'jobYearsExp');
  initExperienceSelect('seekExp', 'seekYearsExp');
  initYearsAutoSuffix('jobYearsExp');
  initYearsAutoSuffix('seekYearsExp');
  initYearsAutoSuffix('id_experience_years');
  initAlerts();
});

// ===== CUSTOM ALERT / CONFIRM DIALOGS (replaces native browser popups) =====
(function () {
  var overlay, iconEl, titleEl, msgEl, footerEl, resolveFn = null;

  function ensureDialog() {
    if (overlay) return;
    overlay = document.createElement('div');
    overlay.className = 'cdlg-overlay';
    overlay.innerHTML =
      '<div class="cdlg-box" role="alertdialog" aria-modal="true" aria-labelledby="cdlgTitle">' +
        '<div class="cdlg-icon" id="cdlgIcon"><i class="ph-fill ph-info"></i></div>' +
        '<div class="cdlg-title" id="cdlgTitle"></div>' +
        '<div class="cdlg-message" id="cdlgMessage"></div>' +
        '<div class="cdlg-footer" id="cdlgFooter"></div>' +
      '</div>';
    document.body.appendChild(overlay);
    iconEl = overlay.querySelector('#cdlgIcon');
    titleEl = overlay.querySelector('#cdlgTitle');
    msgEl = overlay.querySelector('#cdlgMessage');
    footerEl = overlay.querySelector('#cdlgFooter');

    overlay.addEventListener('click', function (e) {
      if (e.target === overlay) dismiss(false);
    });
    document.addEventListener('keydown', function (e) {
      if (!overlay.classList.contains('is-open')) return;
      if (e.key === 'Escape') dismiss(false);
    });
  }

  function dismiss(result) {
    overlay.classList.remove('is-open');
    document.body.style.overflow = '';
    if (resolveFn) { var fn = resolveFn; resolveFn = null; fn(result); }
  }

  var ICONS = {
    info:     { icon: 'ph-info',         cls: 'cdlg-icon-info' },
    success:  { icon: 'ph-check-circle', cls: 'cdlg-icon-success' },
    warning:  { icon: 'ph-warning',      cls: 'cdlg-icon-warning' },
    danger:   { icon: 'ph-x-circle',     cls: 'cdlg-icon-danger' },
    question: { icon: 'ph-question',     cls: 'cdlg-icon-question' }
  };

  function open(opts) {
    ensureDialog();
    var meta = ICONS[opts.type] || ICONS.info;
    iconEl.className = 'cdlg-icon ' + meta.cls;
    iconEl.innerHTML = '<i class="ph-fill ' + meta.icon + '"></i>';
    titleEl.textContent = opts.title || '';
    titleEl.style.display = opts.title ? '' : 'none';
    msgEl.textContent = opts.message || '';

    footerEl.innerHTML = '';
    if (opts.showCancel) {
      var cancelBtn = document.createElement('button');
      cancelBtn.type = 'button';
      cancelBtn.className = 'btn btn-outline-secondary cdlg-btn-cancel';
      cancelBtn.textContent = opts.cancelText || 'Cancel';
      cancelBtn.onclick = function () { dismiss(false); };
      footerEl.appendChild(cancelBtn);
    }
    var okBtn = document.createElement('button');
    okBtn.type = 'button';
    okBtn.className = 'btn cdlg-btn-ok ' + (opts.danger ? 'btn-danger' : 'btn-primary');
    okBtn.textContent = opts.okText || 'OK';
    okBtn.onclick = function () { dismiss(true); };
    footerEl.appendChild(okBtn);

    overlay.classList.add('is-open');
    document.body.style.overflow = 'hidden';
    setTimeout(function () { okBtn.focus(); }, 50);

    return new Promise(function (resolve) { resolveFn = resolve; });
  }

  /** Drop-in replacement for window.alert(). Returns a Promise that resolves when dismissed. */
  window.customAlert = function (message, opts) {
    opts = opts || {};
    return open({
      type: opts.type || 'info',
      title: opts.title || 'Notice',
      message: message,
      okText: opts.okText || 'OK',
      showCancel: false
    });
  };

  /** Drop-in replacement for window.confirm(). Returns a Promise<boolean>. */
  window.customConfirm = function (message, opts) {
    opts = opts || {};
    return open({
      type: opts.type || 'question',
      title: opts.title || 'Please Confirm',
      message: message,
      okText: opts.okText || 'Yes',
      cancelText: opts.cancelText || 'Cancel',
      danger: opts.danger || false,
      showCancel: true
    });
  };
})();
