const main = () => {
    if (window.top !== window) {
        return;
    }

    window.addEventListener("load", () => {
        const wbTopBanner = document.getElementById("_wb_capture_info");
        const nextButton = document.createElement("button");
        nextButton.type = "button";
        nextButton.textContent = "Next";
        wbTopBanner.appendChild(nextButton);
        console.log(nextButton, wbTopBanner);
    })
}

main()