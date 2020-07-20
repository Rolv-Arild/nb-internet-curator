const default_url = "http://localhost:6969"

async function get(endpoint, query) {
    return fetch(default_url + "/" + endpoint + "?" + query, {
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
    return fetch(default_url + "/" + endpoint, {
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
    const collection = spl[1];
    const date = spl[2];
    const url = spl.slice(3).join("/");
    const urlBody = {collection, date, url}
    const urlQuery = "collection=" + collection + "&date=" + date + "&url=" + url;
    const eventual = get("paginate/current", urlQuery)

    window.addEventListener("load", () => {
        const wbTopBanner = document.getElementById("_wb_frame_top_banner");
        // const previousButton = document.createElement("button");
        const afterButtons = document.getElementById("_wb_ancillary_links");
        // Hack: This seems to make the script run after default_banner.js TODO
        setTimeout(function () {
            const buttonDiv = document.createElement("div");
            buttonDiv.style.margin = "0 30px 0 0px";
            wbTopBanner.insertBefore(buttonDiv, afterButtons);
            const statusDiv = document.createElement("div");
            statusDiv.style.margin = "0 30px 0 0px";
            wbTopBanner.insertBefore(statusDiv, afterButtons);
            const statusIndicator = document.createElement("span");
            statusIndicator.innerText = "Loading...";
            statusIndicator.style.color = "#8a9df2";
            statusDiv.appendChild(statusIndicator);
            eventual.then(resp => {
                resp.json().then(j => {
                    console.log(j.verdict);
                    const v = j.verdict
                    if (v === "accepted") {
                        statusIndicator.innerText = "Accepted"
                        statusIndicator.style.color = "#44bd4a"
                    } else if (v === "rejected") {
                        statusIndicator.innerText = "Rejected"
                        statusIndicator.style.color = "#e83535"
                    } else {
                        statusIndicator.innerText = "Undecided"
                        statusIndicator.style.color = "#8a9df2"
                    }
                })
            })

            const buttonAttrs = [
                {
                    name: "Previous",
                    color: "#8a9df2",
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
                    color: "#8a9df2",
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
                    color: "#e83535",
                    onclick: () => {
                        const body = Object.assign(urlBody)
                        body.verdict = "rejected"
                        post("verdicate", body).then(resp => {
                            resp.json().then(j => {
                                window.location.pathname = j.url
                            })
                        })
                    }
                },
                {
                    name: "Accept",
                    color: "#44bd4a",
                    onclick: () => {
                        const body = Object.assign(urlBody)
                        body.verdict = "accepted"
                        post("verdicate", body).then(resp => {
                            resp.json().then(j => {
                                window.location.pathname = j.url
                            })
                        })
                    }
                },
            ];
            for (const buttonInfo of buttonAttrs) {
                const newButton = document.createElement("button");
                newButton.type = "button";
                newButton.textContent = buttonInfo.name;
                newButton.style.backgroundColor = buttonInfo.color;
                newButton.style.margin = "0 10px 0 10px";
                newButton.onclick = buttonInfo.onclick;
                buttonDiv.appendChild(newButton);
            }
        }, 0);
    })
}


main()