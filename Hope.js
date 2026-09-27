let requests = [];


// Stores the agent's structured response after validation.
// It is sent to /completeRequest only when Save is clicked.
let currentAgentResult = null;


// ============================================================
// LOAD REQUESTS
// ============================================================

async function loadRequests() {

    try {

        console.log("Calling /requests...");

        const response = await fetch("/requests");

        console.log(
            "GET /requests status:",
            response.status
        );


        // Read response as text first so errors are visible
        const rawText = await response.text();

        console.log(
            "Raw /requests response:",
            rawText
        );


        if (!response.ok) {

            throw new Error(
                `HTTP ${response.status}: ${rawText}`
            );

        }


        let data;

        try {

            data = JSON.parse(rawText);

        } catch (error) {

            throw new Error(
                "Server did not return valid JSON."
            );

        }


        console.log(
            "Parsed /requests response:",
            data
        );


        if (!data.success) {

            throw new Error(
                data.message ||
                "API returned success=false"
            );

        }


        requests = data.requests || [];


        console.log(
            "Requests loaded:",
            requests
        );


        renderRequests();


    } catch (error) {

        console.error(
            "LOAD REQUESTS ERROR:",
            error
        );


        alert(
            "Unable to load incoming requests.\n\n" +
            error.message
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
    ).textContent =
        requests.length;



    // --------------------------------------------------------
    // NO REQUESTS
    // --------------------------------------------------------

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



    // --------------------------------------------------------
    // RENDER EACH REQUEST
    // --------------------------------------------------------

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


    console.log(
        "Validating request:",
        requestId
    );


    // Find request from current list

    const request =
        requests.find(
            item =>
                item.request_id === requestId
        );


    if (!request) {

        alert(
            "Request not found."
        );

        return;

    }


    console.log(
        "Request being sent to agent:",
        request
    );


    showLoading();


    try {


        // ----------------------------------------------------
        // CALL EXISTING AGENT ENDPOINT
        // ----------------------------------------------------

        const response =
            await fetch(
                "/processRequest",
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


        const rawText =
            await response.text();


        console.log(
            "Raw /processRequest response:",
            rawText
        );


        if (!response.ok) {

            throw new Error(
                `HTTP ${response.status}: ${rawText}`
            );

        }


        let data;

        try {

            data =
                JSON.parse(rawText);

        } catch (error) {

            throw new Error(
                "Agent endpoint did not return valid JSON."
            );

        }


        console.log(
            "Agent response:",
            data
        );


        if (!data.success) {

            throw new Error(
                data.message ||
                "Agent processing failed."
            );

        }


        if (!data.agent_result) {

            throw new Error(
                "Agent response does not contain agent_result."
            );

        }


        // ----------------------------------------------------
        // STORE EXACT AGENT JSON
        // ----------------------------------------------------

        currentAgentResult =
            data.agent_result;


        console.log(
            "Stored agent result:",
            currentAgentResult
        );


        // ----------------------------------------------------
        // DISPLAY RESULT
        // ----------------------------------------------------

        showResult(data);


    } catch (error) {

        console.error(
            "VALIDATION ERROR:",
            error
        );


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


    console.log(
        "Displaying agent result:",
        result
    );


    // Show result panel

    document.getElementById(
        "resultPanel"
    ).classList.remove(
        "hidden"
    );



    // --------------------------------------------------------
    // REQUEST ID
    // --------------------------------------------------------

    document.getElementById(
        "resultRequestId"
    ).textContent =

        `Request ID: ${
            data.request?.request_id ||
            result.request_id ||
            ""
        }`;



    // --------------------------------------------------------
    // CLASSIFICATION
    // --------------------------------------------------------

    document.getElementById(
        "classification"
    ).textContent =

        result.classification ||
        "—";



    // --------------------------------------------------------
    // DECISION
    // --------------------------------------------------------

    document.getElementById(
        "decision"
    ).textContent =

        formatDecision(
            result.decision
        );



    // --------------------------------------------------------
    // ACTIONS
    // --------------------------------------------------------

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

            <span class="check">
                ✓
            </span>

            <span>

                ${escapeHtml(
                    formatAction(action)
                )}

            </span>

        `;


        actions.appendChild(item);

    });



    // --------------------------------------------------------
    // REASON
    // --------------------------------------------------------

    document.getElementById(
        "reason"
    ).textContent =

        result.reason ||
        "No reason provided.";



    // --------------------------------------------------------
    // ENABLE SAVE BUTTON
    // --------------------------------------------------------

    const saveButton =
        document.getElementById(
            "saveButton"
        );


    saveButton.disabled = false;


    saveButton.textContent =
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


    console.log(
        "Saving agent result:",
        currentAgentResult
    );


    showLoading();


    try {


        // ----------------------------------------------------
        // SEND EXACT AGENT JSON
        // ----------------------------------------------------

        const response =
            await fetch(
                "/completeRequest",
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


        const rawText =
            await response.text();


        console.log(
            "Raw /completeRequest response:",
            rawText
        );


        if (!response.ok) {

            throw new Error(
                `HTTP ${response.status}: ${rawText}`
            );

        }


        let data;

        try {

            data =
                JSON.parse(rawText);

        } catch (error) {

            throw new Error(
                "Complete request endpoint did not return valid JSON."
            );

        }


        console.log(
            "Complete request response:",
            data
        );


        if (!data.success) {

            throw new Error(
                data.message ||
                "Failed to save request."
            );

        }



        // ----------------------------------------------------
        // UPDATE VALIDATED COUNT
        // ----------------------------------------------------

        const validatedCount =
            document.getElementById(
                "validatedCount"
            );


        validatedCount.textContent =
            parseInt(
                validatedCount.textContent ||
                "0"
            ) + 1;



        // ----------------------------------------------------
        // HUMAN REVIEW COUNT
        // ----------------------------------------------------

        if (

            currentAgentResult.decision &&

            currentAgentResult.decision
                .toLowerCase()
                .includes("human")

        ) {

            const reviewCount =
                document.getElementById(
                    "reviewCount"
                );


            reviewCount.textContent =
                parseInt(
                    reviewCount.textContent ||
                    "0"
                ) + 1;

        }



        // ----------------------------------------------------
        // REMOVE FROM CURRENT TABLE
        //
        // The backend has already removed the request
        // from incoming_requests.csv.
        // ----------------------------------------------------

        const completedRequestId =
            currentAgentResult.request_id;


        requests =
            requests.filter(
                request =>
                    request.request_id !==
                    completedRequestId
            );


        renderRequests();



        // ----------------------------------------------------
        // UPDATE SAVE BUTTON
        // ----------------------------------------------------

        const saveButton =
            document.getElementById(
                "saveButton"
            );


        saveButton.disabled = true;


        saveButton.textContent =
            "Saved ✓";



        // ----------------------------------------------------
        // CLEAR STORED RESULT
        // ----------------------------------------------------

        currentAgentResult = null;


        alert(
            "Request saved successfully."
        );


    } catch (error) {

        console.error(
            "SAVE ERROR:",
            error
        );


        alert(
            error.message ||
            "Failed to save completed request."
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
// FORMAT DECISION
// ============================================================

function formatDecision(decision) {

    if (!decision) {

        return "—";

    }


    return String(decision)

        .replaceAll(
            "_",
            " "
        )

        .replace(
            /\b\w/g,
            char =>
                char.toUpperCase()
        );

}



// ============================================================
// FORMAT ACTION
// ============================================================

function formatAction(action) {

    return String(action)

        .replaceAll(
            "_",
            " "
        )

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
// HTML ESCAPING
// ============================================================

function escapeHtml(value) {

    return String(value)

        .replaceAll(
            "&",
            "&amp;"
        )

        .replaceAll(
            "<",
            "&lt;"
        )

        .replaceAll(
            ">",
            "&gt;"
        )

        .replaceAll(
            '"',
            "&quot;"
        )

        .replaceAll(
            "'",
            "&#039;"
        );

}



// ============================================================
// JAVASCRIPT ESCAPING
// ============================================================

function escapeJs(value) {

    return String(value)

        .replaceAll(
            "\\",
            "\\\\"
        )

        .replaceAll(
            "'",
            "\\'"
        )

        .replaceAll(
            "\n",
            "\\n"
        )

        .replaceAll(
            "\r",
            "\\r"
        );

}



// ============================================================
// INITIAL LOAD
// ============================================================

console.log(
    "Registrar dashboard loaded."
);


loadRequests();
