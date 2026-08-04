function get_rating_elements() {
    return {
        scoreButton: document.querySelector(".rating-value"),
        popover: document.getElementById("rating-popover"),
        slider: document.getElementById("rating-slider"),
        popoverValue: document.getElementById("rating-popover-value"),
    };
}

function set_rating(rate = null) {
    const { scoreButton, slider, popoverValue } = get_rating_elements();
    const min = Number(slider.min);
    const max = Number(slider.max);
    const nextRate = Math.min(max, Math.max(min, Number(rate)));

    slider.value = nextRate;
    slider.style.setProperty("--rating-progress", `${((nextRate - min) / (max - min)) * 100}%`);
    scoreButton.textContent = nextRate;
    popoverValue.textContent = nextRate;
}

function change_rating(step) {
    const { slider } = get_rating_elements();
    set_rating(Number(slider.value) + step);
}

// Back to top button
(function () {
    const btn = document.getElementById("back-to-top");
    if (!btn) return;

    const toggle = () => btn.classList.toggle("visible", window.scrollY > 400);
    btn.addEventListener("click", () => window.scrollTo({ top: 0, behavior: "smooth" }));
    window.addEventListener("scroll", toggle, { passive: true });
    toggle();
})();
