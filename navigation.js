(function () {
  const TOTAL_SLIDES = 50;
  const filePattern = /slide_(\d+)\.html$/i;
  const pathName = window.location.pathname;
  const match = pathName.match(filePattern);
  const currentIndex = match ? Math.min(Math.max(parseInt(match[1], 10), 1), TOTAL_SLIDES) : 1;

  function findOrCreateIndicator() {
    let indicator = document.querySelector('.page-indicator');
    if (!indicator) {
      indicator = document.createElement('div');
      indicator.className = 'page-indicator';
      document.body.appendChild(indicator);
    }
    return indicator;
  }

  function updatePageIndicator() {
    const indicator = findOrCreateIndicator();
    indicator.textContent = `第 ${currentIndex} / ${TOTAL_SLIDES} 页`;
    indicator.setAttribute('aria-label', `当前为第 ${currentIndex} 页，共 ${TOTAL_SLIDES} 页`);
  }

  function updateProgressBar() {
    const progressBar = document.querySelector('.progress-bar');
    if (!progressBar) return;
    const progress = Math.max(0, Math.min(1, currentIndex / TOTAL_SLIDES));
    progressBar.style.width = `${(progress * 100).toFixed(2)}%`;
  }

  function goToSlide(index) {
    if (index === currentIndex || index < 1 || index > TOTAL_SLIDES) {
      return;
    }
    const basePath = pathName.replace(filePattern, '');
    const target = `slide_${String(index).padStart(2, '0')}.html`;
    window.location.href = `${basePath}${target}`;
  }

  function handleKeyNavigation(event) {
    if (event.defaultPrevented) return;
    if (event.key === 'ArrowRight' || event.key === 'PageDown') {
      event.preventDefault();
      goToSlide(currentIndex + 1);
    } else if (event.key === 'ArrowLeft' || event.key === 'PageUp') {
      event.preventDefault();
      goToSlide(currentIndex - 1);
    }
  }

  document.addEventListener('keydown', handleKeyNavigation, false);

  // expose minimal API
  window.HTMLPPTNavigation = Object.freeze({
    current: currentIndex,
    total: TOTAL_SLIDES,
    goTo: goToSlide,
  });

  updatePageIndicator();
  updateProgressBar();
})();
