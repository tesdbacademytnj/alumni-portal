/* =========================================================
   CUSTOM DATE PICKER
   Progressively enhances every <input type="date"> into a
   themed dropdown calendar (dd-mm-yyyy display), while the
   original input keeps driving form submission/validation.
   If JS fails to load, the native date input still works and
   is already styled to match (see style.css).
   ========================================================= */
(function () {
  var MONTHS = ['January','February','March','April','May','June','July','August','September','October','November','December'];
  var WEEKDAYS = ['Sun','Mon','Tue','Wed','Thu','Fri','Sat'];

  function pad2(n) { return String(n).padStart(2, '0'); }

  function toISO(d) {
    return d.getFullYear() + '-' + pad2(d.getMonth() + 1) + '-' + pad2(d.getDate());
  }

  function toDisplay(d) {
    return pad2(d.getDate()) + '-' + pad2(d.getMonth() + 1) + '-' + d.getFullYear();
  }

  function parseISO(str) {
    if (!str) return null;
    var m = /^(\d{4})-(\d{2})-(\d{2})$/.exec(str.trim());
    if (!m) return null;
    var d = new Date(parseInt(m[1], 10), parseInt(m[2], 10) - 1, parseInt(m[3], 10));
    return isNaN(d.getTime()) ? null : d;
  }

  function stripTime(d) {
    return new Date(d.getFullYear(), d.getMonth(), d.getDate());
  }

  function sameDay(a, b) {
    return a && b && a.getFullYear() === b.getFullYear() && a.getMonth() === b.getMonth() && a.getDate() === b.getDate();
  }

  function enhance(nativeInput) {
    if (nativeInput.dataset.datepickerInit) return;
    nativeInput.dataset.datepickerInit = 'true';

    var today = stripTime(new Date());
    var minDate = parseISO(nativeInput.getAttribute('min'));
    var maxDate = parseISO(nativeInput.getAttribute('max'));
    if (!minDate && nativeInput.dataset.disablePast === 'true') minDate = today;

    var selected = parseISO(nativeInput.value);
    var view = selected ? new Date(selected.getFullYear(), selected.getMonth(), 1)
                          : new Date((minDate && minDate > today ? minDate : today).getFullYear(), (minDate && minDate > today ? minDate : today).getMonth(), 1);

    // ---- Build markup ----
    var wrapper = document.createElement('div');
    wrapper.className = 'date-field';

    nativeInput.parentNode.insertBefore(wrapper, nativeInput);
    wrapper.appendChild(nativeInput);
    nativeInput.classList.add('date-native-input');
    nativeInput.setAttribute('tabindex', '-1');
    nativeInput.setAttribute('aria-hidden', 'true');
    var wasRequired = nativeInput.required;
    nativeInput.required = false;

    var display = document.createElement('button');
    display.type = 'button';
    display.className = 'form-control date-display';
    if (nativeInput.disabled) display.disabled = true;
    display.setAttribute('aria-haspopup', 'dialog');
    display.setAttribute('aria-expanded', 'false');
    var placeholderText = nativeInput.getAttribute('placeholder') || 'dd-mm-yyyy';
    display.innerHTML =
      '<span class="date-display-text' + (selected ? '' : ' is-placeholder') + '">' +
      (selected ? toDisplay(selected) : placeholderText) + '</span>' +
      '<i class="ph ph-calendar-blank date-display-icon" aria-hidden="true"></i>';
    wrapper.appendChild(display);

    var panel = document.createElement('div');
    panel.className = 'date-panel';
    panel.setAttribute('role', 'dialog');
    panel.hidden = true;
    panel.innerHTML =
      '<div class="date-panel-header">' +
        '<button type="button" class="date-nav-btn" data-nav="prev" aria-label="Previous month"><i class="ph ph-caret-left"></i></button>' +
        '<div class="date-header-selects">' +
          '<select class="date-month-select" aria-label="Month"></select>' +
          '<select class="date-year-select" aria-label="Year"></select>' +
        '</div>' +
        '<button type="button" class="date-nav-btn" data-nav="next" aria-label="Next month"><i class="ph ph-caret-right"></i></button>' +
      '</div>' +
      '<div class="date-weekdays">' + WEEKDAYS.map(function (w) { return '<span>' + w + '</span>'; }).join('') + '</div>' +
      '<div class="date-grid"></div>' +
      '<div class="date-panel-footer">' +
        '<button type="button" class="date-footer-btn" data-action="today">Today</button>' +
        '<button type="button" class="date-footer-btn date-footer-btn-clear" data-action="clear">Clear</button>' +
      '</div>';
    wrapper.appendChild(panel);

    var grid = panel.querySelector('.date-grid');
    var monthSelect = panel.querySelector('.date-month-select');
    var yearSelect = panel.querySelector('.date-year-select');
    var textEl = display.querySelector('.date-display-text');

    MONTHS.forEach(function (m, i) {
      var opt = document.createElement('option');
      opt.value = i;
      opt.textContent = m;
      monthSelect.appendChild(opt);
    });

    var yearFrom = (minDate ? minDate.getFullYear() : today.getFullYear() - 80);
    var yearTo = (maxDate ? maxDate.getFullYear() : today.getFullYear() + 10);
    for (var y = yearFrom; y <= yearTo; y++) {
      var yopt = document.createElement('option');
      yopt.value = y;
      yopt.textContent = y;
      yearSelect.appendChild(yopt);
    }

    function inBounds(d) {
      if (minDate && d < minDate) return false;
      if (maxDate && d > maxDate) return false;
      return true;
    }

    function renderGrid() {
      monthSelect.value = view.getMonth();
      yearSelect.value = view.getFullYear();

      var firstOfMonth = new Date(view.getFullYear(), view.getMonth(), 1);
      var startOffset = firstOfMonth.getDay();
      var gridStart = new Date(view.getFullYear(), view.getMonth(), 1 - startOffset);

      grid.innerHTML = '';
      for (var i = 0; i < 42; i++) {
        var cellDate = new Date(gridStart.getFullYear(), gridStart.getMonth(), gridStart.getDate() + i);
        var btn = document.createElement('button');
        btn.type = 'button';
        btn.className = 'date-cell';
        btn.textContent = cellDate.getDate();
        btn.setAttribute('data-date', toISO(cellDate));

        if (cellDate.getMonth() !== view.getMonth()) btn.classList.add('is-outside');
        if (sameDay(cellDate, today)) btn.classList.add('is-today');
        if (selected && sameDay(cellDate, selected)) btn.classList.add('is-selected');
        if (!inBounds(cellDate)) {
          btn.classList.add('is-disabled');
          btn.disabled = true;
        }
        grid.appendChild(btn);
      }
    }

    function open() {
      renderGrid();
      panel.hidden = false;
      display.setAttribute('aria-expanded', 'true');
      positionPanel();
      document.addEventListener('click', onOutsideClick, true);
      document.addEventListener('keydown', onKeydown, true);
    }

    function close() {
      panel.hidden = true;
      display.setAttribute('aria-expanded', 'false');
      document.removeEventListener('click', onOutsideClick, true);
      document.removeEventListener('keydown', onKeydown, true);
    }

    function positionPanel() {
      panel.style.left = '';
      panel.style.right = '';
      var rect = wrapper.getBoundingClientRect();
      var panelWidth = 300;
      if (rect.left + panelWidth > window.innerWidth - 12) {
        panel.style.right = '0';
      } else {
        panel.style.left = '0';
      }
    }

    function onOutsideClick(e) {
      if (!wrapper.contains(e.target)) close();
    }

    function onKeydown(e) {
      if (e.key === 'Escape') { close(); display.focus(); }
    }

    function selectDate(d) {
      if (!inBounds(d)) return;
      selected = d;
      view = new Date(d.getFullYear(), d.getMonth(), 1);
      nativeInput.value = toISO(d);
      nativeInput.dispatchEvent(new Event('input', { bubbles: true }));
      nativeInput.dispatchEvent(new Event('change', { bubbles: true }));
      textEl.textContent = toDisplay(d);
      textEl.classList.remove('is-placeholder');
      close();
      display.focus();
    }

    display.addEventListener('click', function () {
      if (display.disabled) return;
      panel.hidden ? open() : close();
    });

    panel.querySelector('[data-nav="prev"]').addEventListener('click', function () {
      view = new Date(view.getFullYear(), view.getMonth() - 1, 1);
      renderGrid();
    });
    panel.querySelector('[data-nav="next"]').addEventListener('click', function () {
      view = new Date(view.getFullYear(), view.getMonth() + 1, 1);
      renderGrid();
    });
    monthSelect.addEventListener('change', function () {
      view = new Date(yearSelect.value, parseInt(monthSelect.value, 10), 1);
      renderGrid();
    });
    yearSelect.addEventListener('change', function () {
      view = new Date(parseInt(yearSelect.value, 10), view.getMonth(), 1);
      renderGrid();
    });
    grid.addEventListener('click', function (e) {
      var cell = e.target.closest('.date-cell');
      if (!cell || cell.disabled) return;
      selectDate(parseISO(cell.getAttribute('data-date')));
    });
    panel.querySelector('[data-action="today"]').addEventListener('click', function () {
      if (inBounds(today)) selectDate(today);
    });
    panel.querySelector('[data-action="clear"]').addEventListener('click', function () {
      selected = null;
      nativeInput.value = '';
      nativeInput.dispatchEvent(new Event('input', { bubbles: true }));
      nativeInput.dispatchEvent(new Event('change', { bubbles: true }));
      textEl.textContent = placeholderText;
      textEl.classList.add('is-placeholder');
      close();
    });

    display.addEventListener('keydown', function (e) {
      if (e.key === 'ArrowDown' || e.key === 'Enter' || e.key === ' ') {
        e.preventDefault();
        if (panel.hidden) open();
      }
    });

    // Keep a hidden native "required" contract for form validation
    // by validating on submit if the field was originally required.
    if (wasRequired) {
      var form = nativeInput.closest('form');
      if (form) {
        form.addEventListener('submit', function (e) {
          if (!nativeInput.value) {
            e.preventDefault();
            display.classList.add('is-invalid');
            open();
            display.focus();
          } else {
            display.classList.remove('is-invalid');
          }
        });
      }
      display.addEventListener('click', function () { display.classList.remove('is-invalid'); });
    }
  }

  function init() {
    document.querySelectorAll('input[type="date"]').forEach(enhance);
  }

  document.addEventListener('DOMContentLoaded', init);
})();
