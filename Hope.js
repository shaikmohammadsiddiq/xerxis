let requests = [];

let currentAgentResult = null;


// ============================================================
// FASTAPI URL
// ============================================================

const API_URL = "http://127.0.0.1:8000";


// ============================================================
// LOAD REQUESTS
// ============================================================

async function loadRequests() {

    try {

        const response =
            await fetch(`${API_URL}/requests`);

        if (!response.ok) {

            throw new Error(
                `HTTP ${response.status}`
            );

        }

        const data =
            await response.json();

        requests =
            data.requests || [];

        renderRequests();

    } catch (error) {

        console.error(error);

        alert(
            "Unable to load incoming requests.\n\n" +
            error.message
        );

    }

}


// ============================================================
// RENDER REQUESTS
// ============================================================

function renderRequests() {

    const table =
        document.getElementById(
            "requestTable"
        );

    table.innerHTML = "";


    document.getElementById(
        "incomingCount"
    ).textContent =
        requests.length;


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
                    onclick="
                        validateRequest(
                            '${escapeJs(
                                request.request_id
                            )}'
                        )
                    "
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

async function validateRequest(requestId) {

    const request =
        requests.find(
            item =>
                item.request_id === requestId
        );


    if (!request) {

        alert("Request not found.");

        return;

    }


    showLoading();


    try {

        const response =
            await fetch(
                `${API_URL}/processRequest`,
                {

                    method: "POST",

                    headers: {
                        "Content-Type":
                            "application/json"
                    },

                    body: JSON.stringify({

                        request_id:
                            request.request_id,

                        student_name:
                            request.student_name,

                        student_status:
                            request.student_status,

                        body_text:
                            request.body_text

                    })

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


        currentAgentResult =
            data.agent_result;


        showResult(data);


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
// SHOW AGENT RESULT
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
            data.request?.request_id ||
            result.request_id ||
            ""
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
        "saveButton"
    ).disabled = false;


    document.getElementById(
        "saveButton"
    ).textContent =
        "Save to Completed";

}


// ============================================================
// SAVE COMPLETED REQUEST
// ============================================================

async function saveCompletedRequest() {

    if (!currentAgentResult) {

        alert(
            "No validated request available."
        );

        return;

    }


    showLoading();


    try {

        const response =
            await fetch(
                `${API_URL}/completeRequest`,
                {

                    method: "POST",

                    headers: {
                        "Content-Type":
                            "application/json"
                    },

                    body: JSON.stringify(
                        currentAgentResult
                    )

                }
            );


        const data =
            await response.json();


        if (!response.ok || !data.success) {

            throw new Error(
                data.message ||
                data.detail ||
                "Failed to save request"
            );

        }


        // --------------------------------------------
        // UPDATE COUNTERS
        // --------------------------------------------

        document.getElementById(
            "validatedCount"
        ).textContent =

            parseInt(
                document.getElementById(
                    "validatedCount"
                ).textContent || "0"
            ) + 1;


        if (

            currentAgentResult.decision &&

            currentAgentResult.decision
                .toLowerCase()
                .includes("human")

        ) {

            document.getElementById(
                "reviewCount"
            ).textContent =

                parseInt(
                    document.getElementById(
                        "reviewCount"
                    ).textContent || "0"
                ) + 1;

        }


        // --------------------------------------------
        // REMOVE FROM TABLE
        // --------------------------------------------

        const completedId =
            currentAgentResult.request_id;


        requests =
            requests.filter(
                request =>
                    request.request_id !==
                    completedId
            );


        renderRequests();


        // --------------------------------------------
        // UPDATE BUTTON
        // --------------------------------------------

        const saveButton =
            document.getElementById(
                "saveButton"
            );


        saveButton.disabled = true;

        saveButton.textContent =
            "Saved ✓";


        currentAgentResult = null;


        alert(
            "Request saved successfully."
        );


    } catch (error) {

        console.error(error);

        alert(
            error.message ||
            "Failed to save request."
        );

    } finally {

        hideLoading();

    }

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
// FORMATTING
// ============================================================

function formatDecision(decision) {

    if (!decision) {
        return "—";
    }

    return String(decision)
        .replaceAll("_", " ")
        .replace(
            /\b\w/g,
            char =>
                char.toUpperCase()
        );

}


function formatAction(action) {

    return String(action)
        .replaceAll("_", " ")
        .replace(
            /\b\w/g,
            char =>
                char.toUpperCase()
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
// ESCAPING
// ============================================================

function escapeHtml(value) {

    return String(value)
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");

}


function escapeJs(value) {

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
