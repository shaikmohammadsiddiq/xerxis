let requests = [];


// ============================================================
// LOAD REQUESTS
// ============================================================

async function loadRequests() {

    try {

        const response = await fetch(
            "/api/registrar/requests"
        );

        if (!response.ok) {
            throw new Error(
                "Failed to load requests"
            );
        }

        const data = await response.json();

        requests = data.requests || [];

        renderRequests();

    } catch (error) {

        console.error(error);

        alert(
            "Unable to load incoming requests."
        );
    }
}


// ============================================================
// RENDER REQUEST TABLE
// ============================================================

function renderRequests() {

    const table =
        document.getElementById(
            "requestTable"
        );

    table.innerHTML = "";

    document.getElementById(
        "incomingCount"
    ).textContent = requests.length;


    if (requests.length === 0) {

        table.innerHTML = `
            <tr>
                <td
                    colspan="6"
                    class="empty"
                >
                    No incoming requests.
                </td>
            </tr>
        `;

        return;
    }


    requests.forEach(request => {

        const row =
            document.createElement("tr");


        row.innerHTML = `

            <td>
                <strong>
                    ${escapeHtml(
                        request.request_id || ""
                    )}
                </strong>
            </td>

            <td>
                ${escapeHtml(
                    request.student_name || ""
                )}
            </td>

            <td>
                <span class="status-badge new">
                    ${escapeHtml(
                        request.status || "NEW"
                    )}
                </span>
            </td>

            <td>
                ${escapeHtml(
                    request.submitted_at || ""
                )}
            </td>

            <td class="request-text">
                ${escapeHtml(
                    request.body_text || ""
                )}
            </td>

            <td>

                <button
                    class="validate-button"
                    onclick="validateRequest(
                        '${escapeJs(
                            request.request_id
                        )}'
                    )"
                >
                    Validate
                </button>

            </td>

        `;

        table.appendChild(row);

    });
}


// ============================================================
// VALIDATE REQUEST
// ============================================================

async function validateRequest(
    requestId
) {

    showLoading();


    try {

        const response = await fetch(
            `/api/registrar/requests/${encodeURIComponent(
                requestId
            )}/validate`,
            {
                method: "POST"
            }
        );


        const data =
            await response.json();


        if (!response.ok) {

            throw new Error(
                data.detail ||
                "Validation failed"
            );

        }


        showResult(
            data
        );


        // Remove successfully processed
        // request from current list

        requests = requests.filter(
            request =>
                request.request_id !==
                requestId
        );

        renderRequests();


    } catch (error) {

        console.error(error);

        alert(
            error.message ||
            "Agent validation failed."
        );

    } finally {

        hideLoading();

    }
}


// ============================================================
// DISPLAY AGENT RESULT
// ============================================================

function showResult(data) {

    const result =
        data.agent_result;


    document.getElementById(
        "resultPanel"
    ).classList.remove(
        "hidden"
    );


    document.getElementById(
        "resultRequestId"
    ).textContent =
        `Request ID: ${
            data.request?.request_id || ""
        }`;


    document.getElementById(
        "classification"
    ).textContent =
        result.classification ||
        "—";


    document.getElementById(
        "decision"
    ).textContent =
        formatDecision(
            result.decision
        );


    const actions =
        document.getElementById(
            "actions"
        );

    actions.innerHTML = "";


    const actionList =
        result.actions_taken || [];


    actionList.forEach(action => {

        const item =
            document.createElement(
                "div"
            );

        item.className =
            "action-item";


        item.innerHTML = `
            <span class="check">✓</span>
            <span>
                ${escapeHtml(
                    formatAction(action)
                )}
            </span>
        `;


        actions.appendChild(item);

    });


    document.getElementById(
        "reason"
    ).textContent =
        result.reason ||
        "No reason provided.";


    document.getElementById(
        "validatedCount"
    ).textContent =
        parseInt(
            document.getElementById(
                "validatedCount"
            ).textContent
        ) + 1;


    if (
        result.decision &&
        result.decision
            .toLowerCase()
            .includes("human")
    ) {

        document.getElementById(
            "reviewCount"
        ).textContent =
            parseInt(
                document.getElementById(
                    "reviewCount"
                ).textContent
            ) + 1;
    }

}


// ============================================================
// FORMATTING
// ============================================================

function formatDecision(
    decision
) {

    if (!decision) {
        return "—";
    }

    return decision
        .replaceAll("_", " ")
        .replace(
            /\b\w/g,
            char => char.toUpperCase()
        );
}


function formatAction(
    action
) {

    return action
        .replaceAll("_", " ")
        .replace(
            /\b\w/g,
            char => char.toUpperCase()
        );
}


// ============================================================
// LOADING
// ============================================================

function showLoading() {

    document.getElementById(
        "loading"
    ).classList.remove(
        "hidden"
    );

}


function hideLoading() {

    document.getElementById(
        "loading"
    ).classList.add(
        "hidden"
    );

}


// ============================================================
// CLOSE RESULT
// ============================================================

function closeResult() {

    document.getElementById(
        "resultPanel"
    ).classList.add(
        "hidden"
    );

}


// ============================================================
// SECURITY / HTML ESCAPING
// ============================================================

function escapeHtml(
    value
) {

    return String(value)
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");

}


function escapeJs(
    value
) {

    return String(value)
        .replaceAll("\\", "\\\\")
        .replaceAll("'", "\\'")
        .replaceAll("\n", "\\n")
        .replaceAll("\r", "\\r");

}


// ============================================================
// INITIAL LOAD
// ============================================================

loadRequests();
