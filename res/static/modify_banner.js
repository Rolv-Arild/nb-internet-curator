const default_url = "http://localhost:6969"

async function get(endpoint, query) {
    return fetch(`${default_url}/${endpoint}?${query}`, {
        method: "GET",
        mode: "cors",
        cache: "no-cache",
        credentials: 'same-origin',
        headers: {
            "Content-Type": "text/plain",
            "Origin": "http://localhost/8080"
        },
        referrerPolicy: 'no-referrer'
    })
}

async function post(endpoint, body) {
    return fetch(`${default_url}/${endpoint}`, {
        method: "POST",
        mode: "cors",
        cache: "no-cache",
        credentials: 'same-origin',
        headers: {
            "Content-Type": "application/json",
            "Origin": "http://localhost/8080"
        },
        referrerPolicy: 'no-referrer',
        body: JSON.stringify(body)
    })
}


const main = () => {
    if (window.top !== window) {
        return;
    }

    const spl = window.location.pathname.split("/");
    const sessionData = {
        collection: spl[1],
        date: spl[2],
        url: spl.slice(3).join("/")
    };
    const urlQuery = `collection=${sessionData.collection}&date=${sessionData.date}&url=${sessionData.url}`;
    const currentPagePromise = get("paginate/current", urlQuery);

    window.addEventListener("load", () => {
        const wbTopBanner = document.getElementById("_wb_frame_top_banner");

        const afterButtons = document.getElementById("_wb_ancillary_links");
        // Hack: This seems to make the script run after default_banner.js TODO
        setTimeout(() => {
            const buttonDiv = document.createElement("div");
            buttonDiv.style.margin = "0 30px 0 0px";
            wbTopBanner.insertBefore(buttonDiv, afterButtons);

            const statusDiv = document.createElement("div");
            statusDiv.style.margin = "0 30px 0 0px";

            wbTopBanner.insertBefore(statusDiv, afterButtons);
            const statusIndicator = document.createElement("span");
            statusIndicator.innerText = "Loading...";
            statusIndicator.classList.add("text-info");
            statusDiv.appendChild(statusIndicator);

            currentPagePromise.then(resp => {
                resp.json().then(j => {
                    const v = j.verdict

                    // flush previous classes
                    statusIndicator.classList = []; 

                    if (v === "accepted") {
                        statusIndicator.innerText = "Accepted"
                        statusIndicator.classList.add("text-success");
                    } else if (v === "rejected") {
                        statusIndicator.innerText = "Rejected"
                        statusIndicator.classList.add("text-danger");
                    } else {
                        statusIndicator.innerText = "Undecided"
                        statusIndicator.classList.add("text-info");
                    }
                })
            })  // TODO catch

            const buttonAttrs = [
                {
                    name: "Previous",
                    classes: ["btn", "btn-primary"],
                    onclick: () => {
                        get("paginate/previous", urlQuery).then((resp) => {
                            resp.json().then(j => {
                                window.location.pathname = j.url
                            })
                        }).catch(e => console.log(e))
                    }
                },
                {
                    name: "Next",
                    classes: ["btn", "btn-primary"],
                    onclick: () => {
                        get("paginate/next", urlQuery).then((resp) => {
                            resp.json().then(j => {
                                window.location.pathname = j.url
                            })
                        }).catch(e => console.log(e))
                    }
                },
                {
                    name: "Reject",
                    classes: ["btn", "btn-danger"],
                    onclick: () => {
                        const body = Object.assign(sessionData)
                        body.verdict = "rejected"
                        post("verdicate", body).then(resp => {
                            resp.json().then(j => {
                                window.location.pathname = j.url
                            })
                        }).catch(e => console.log(e))
                    }
                },
                {
                    name: "Accept",
                    classes: ["btn", "btn-success"],
                    onclick: () => {
                        const body = Object.assign(sessionData)
                        body.verdict = "accepted"
                        post("verdicate", body).then(resp => {
                            resp.json().then(j => {
                                window.location.pathname = j.url
                            })
                        }).catch(e => console.log(e))
                    }
                },
            ];
            for (const buttonInfo of buttonAttrs) {
                const newButton = document.createElement("button");
                newButton.type = "button";
                newButton.textContent = buttonInfo.name;
                newButton.classList.add(...buttonInfo.classes);
                newButton.style.margin = "10px 10px 10px 10px";
                newButton.style.paddingTop = "0";
                newButton.style.paddingBottom = "0";
                newButton.onclick = buttonInfo.onclick;
                buttonDiv.appendChild(newButton);
            }
        }, 0);
    })
}

main();