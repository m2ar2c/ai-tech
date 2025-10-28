(function() {
    const TOTAL_SLIDES = 57;

    function getCurrentSlideIndex() {
        const match = window.location.pathname.match(/slide-(\d+)\.html$/);
        if (!match) return 1;
        return parseInt(match[1], 10);
    }

    function goToSlide(index) {
        if (index < 1 || index > TOTAL_SLIDES) return;
        const target = `slide-${String(index).padStart(2, '0')}.html`;
        window.location.href = target;
    }

    document.addEventListener('keydown', (event) => {
        if (event.key === 'ArrowRight') {
            const current = getCurrentSlideIndex();
            if (current < TOTAL_SLIDES) {
                goToSlide(current + 1);
            }
        } else if (event.key === 'ArrowLeft') {
            const current = getCurrentSlideIndex();
            if (current > 1) {
                goToSlide(current - 1);
            }
        }
    });

    document.addEventListener('DOMContentLoaded', () => {
        const current = getCurrentSlideIndex();
        const indicator = document.querySelector('.page-number');
        if (indicator) {
            indicator.textContent = `幻灯片 ${current} / ${TOTAL_SLIDES}`;
        }
    });
})();
