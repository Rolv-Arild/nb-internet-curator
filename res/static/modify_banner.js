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

            const commentPrompt = document.createElement("div");

            commentPrompt.innerHTML = document.getElementById("comment-prompt").innerHTML;

            const body = document.getElementsByTagName("body")[0];

            body.appendChild(commentPrompt);

            const commentCancel = document.getElementById("comment-cancel");
            const commentSubmit = document.getElementById("comment-submit");
            const commentArea = document.getElementById("comment-area");

            commentPrompt.style.display = "none"


            const spawnAlert = e => {
                const div = document.createElement("div");
                div.classList.add("alert", "alert-warning")
                div.innerText = "Got error: " + e;
                div.style.position = "absolute";
                div.style.top = "50px";
                div.style.left = "20px";
                div.style.width = "calc(100vw - 40px)";
                body.appendChild(div);
                setTimeout(() => {
                    body.removeChild(div);
                }, 10000);
            }

            currentPagePromise.then(resp => {
                // flush previous classes
                statusIndicator.classList = [];
                if (resp.status >= 300) {
                    statusIndicator.innerText = "Error";
                    statusIndicator.classList.add("text-danger");
                } else {
                    resp.json().then(j => {
                        const v = j.verdict;

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

                        commentArea.value = j.comment;
                    })
                }
            }).catch(e => spawnAlert(e))

            const responseAction = (resp) => {
                if (resp.status >= 300) {
                    resp.text().then(s => spawnAlert(s))
                } else {
                    resp.json().then(j => {
                        window.location.pathname = j.url
                    })
                }
            }

            const toggleCommentPrompt = () => {
                if (commentPrompt.style.display === "none") {
                    commentPrompt.style.display = "block"
                } else {
                    commentPrompt.style.display = "none"
                }
            }

            commentCancel.onclick = toggleCommentPrompt;
            commentSubmit.onclick = () => {
                const comment = commentArea.value;
                const body = Object.assign(sessionData)
                body.comment = comment
                post("commentate", body).then(resp => {
                    if (resp.status >= 300) {
                        resp.text().then(s => {
                            spawnAlert(s)
                        })
                    }
                })
                toggleCommentPrompt()
            }

            const buttonAttrs = [
                {
                    name: "Comment",
                    classes: ["btn", "btn-secondary"],
                    onclick: toggleCommentPrompt,
                    key: "c"
                },
                {
                    name: "Previous",
                    classes: ["btn", "btn-primary"],
                    onclick: () => {
                        get("paginate/previous", urlQuery).then(responseAction).catch(e => console.log(e))
                    },
                    key: ","
                },
                {
                    name: "Next",
                    classes: ["btn", "btn-primary"],
                    onclick: () => {
                        get("paginate/next", urlQuery).then(responseAction).catch(e => console.log(e))
                    },
                    key: "."
                },
                {
                    name: "Reject",
                    classes: ["btn", "btn-danger"],
                    onclick: () => {
                        const body = Object.assign(sessionData)
                        body.verdict = "rejected"
                        post("verdicate", body).then(responseAction).catch(e => console.log(e))
                    },
                    key: "r"
                },
                {
                    name: "Accept",
                    classes: ["btn", "btn-success"],
                    onclick: () => {
                        const body = Object.assign(sessionData)
                        body.verdict = "accepted"
                        post("verdicate", body).then(responseAction).catch(e => console.log(e))
                    },
                    key: "a"
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

                document.addEventListener("keypress", (ev) => {
                    if (ev.key !== buttonInfo.key) {
                        return
                    }
                    if (commentPrompt.style.display !== "none") {
                        return;
                    }
                    buttonInfo.onclick();
                });
            }
        }, 0);
    })
}

main();