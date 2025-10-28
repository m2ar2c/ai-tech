(function () {
    const slideOrder = [
        "slide_01.html",
        "slide_02.html",
        "slide_03.html",
        "slide_04.html",
        "slide_05.html",
        "slide_06.html",
        "slide_07.html",
        "slide_08.html",
        "slide_09.html",
        "slide_10.html",
        "slide_11.html",
        "slide_12.html"
    ];

    const currentPath = window.location.pathname.split("/").pop() || "";
    const currentIndex = slideOrder.indexOf(currentPath);

    const pageNumberEl = document.querySelector(".page-number");
    if (pageNumberEl && currentIndex >= 0) {
        pageNumberEl.textContent = `幻灯片 ${currentIndex + 1} / ${slideOrder.length}`;
    }

    function navigate(offset) {
        if (currentIndex === -1) {
            return;
        }
        const targetIndex = currentIndex + offset;
        if (targetIndex < 0 || targetIndex >= slideOrder.length) {
            return;
        }
        window.location.href = slideOrder[targetIndex];
    }

    document.addEventListener("keydown", (event) => {
        if (event.key === "ArrowRight" || event.key === "PageDown") {
            navigate(1);
        } else if (event.key === "ArrowLeft" || event.key === "PageUp") {
            navigate(-1);
        }
    });

    function createNavigationOverlay() {
        const overlay = document.createElement("div");
        overlay.className = "nav-overlay";
        overlay.innerHTML = `
            <button class="nav-button prev" data-direction="prev" aria-label="上一张幻灯片">◀</button>
            <div class="nav-hint">使用左右方向键切换幻灯片</div>
            <button class="nav-button next" data-direction="next" aria-label="下一张幻灯片">▶</button>
        `;

        overlay.addEventListener("click", (event) => {
            const target = event.target;
            if (!(target instanceof HTMLElement)) {
                return;
            }
            const direction = target.getAttribute("data-direction");
            if (direction === "prev") {
                navigate(-1);
            }
            if (direction === "next") {
                navigate(1);
            }
        });

        document.body.appendChild(overlay);
    }

    function injectStyles() {
        const style = document.createElement("style");
        style.textContent = `
            .nav-overlay {
                position: fixed;
                bottom: 32px;
                left: 50%;
                transform: translateX(-50%);
                display: flex;
                align-items: center;
                gap: 16px;
                padding: 10px 18px;
                border-radius: 999px;
                background: rgba(6, 16, 36, 0.65);
                border: 1px solid rgba(54, 207, 251, 0.22);
                backdrop-filter: blur(14px);
                color: #D9E4FF;
                font-family: 'Microsoft YaHei', 'Noto Sans SC', 'PingFang SC', sans-serif;
                font-size: 16px;
                letter-spacing: 1px;
                z-index: 999;
            }

            .nav-button {
                width: 44px;
                height: 44px;
                border-radius: 50%;
                border: 1px solid rgba(54, 207, 251, 0.22);
                background: linear-gradient(135deg, rgba(22, 93, 255, 0.35), rgba(114, 46, 209, 0.4));
                color: #F4F8FF;
                font-size: 20px;
                cursor: pointer;
                display: flex;
                align-items: center;
                justify-content: center;
                transition: transform 0.2s ease, box-shadow 0.2s ease;
            }

            .nav-button:hover {
                transform: translateY(-2px);
                box-shadow: 0 10px 20px rgba(22, 93, 255, 0.25);
            }

            .nav-button:disabled {
                opacity: 0.4;
                cursor: default;
                transform: none;
                box-shadow: none;
            }

            .nav-hint {
                opacity: 0.75;
            }
        `;
        document.head.appendChild(style);
    }

    if (currentIndex >= 0) {
        injectStyles();
        createNavigationOverlay();

        const prevButton = document.querySelector(".nav-button.prev");
        const nextButton = document.querySelector(".nav-button.next");
        if (prevButton instanceof HTMLButtonElement && currentIndex === 0) {
            prevButton.disabled = true;
            prevButton.setAttribute("aria-disabled", "true");
        }
        if (nextButton instanceof HTMLButtonElement && currentIndex === slideOrder.length - 1) {
            nextButton.disabled = true;
            nextButton.setAttribute("aria-disabled", "true");
        }
    }
})();
