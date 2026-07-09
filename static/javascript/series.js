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

function toggle_rating_popover() {
    const { popover, slider } = get_rating_elements();
    popover.hidden = !popover.hidden;

    if (!popover.hidden) {
        set_rating(slider.value);
        slider.focus();
    }
}

function close_rating_popover() {
    const { popover } = get_rating_elements();
    popover.hidden = true;
}

document.addEventListener("keydown", function (event) {
    if (event.key === "Escape") {
        close_rating_popover();
    }
});

function active_status(activeStatus, parent) {
    const allDescendants = parent.querySelectorAll('*');
    allDescendants.forEach(el => {
        if (el.classList.contains('active')){
            el.classList.remove('active');
        }
    });
    activeStatus.classList.add('active');
}

function showLog(activate){
    const bg = document.querySelector(".bg-log-editor");
    console.log(bg);
   if (activate){ 
        bg.style.display = 'flex';
   }
   else{
    bg.style.display = 'none';
   }
}