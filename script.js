let requests = [];


// Stores the latest agent response.
// It will only be sent to /completeRequest
// when the Registrar clicks Save.
let currentAgentResult = null;


// ============================================================
// LOAD REQUESTS
// ============================================================

async function loadRequests() {

    try {

        const response = await fetch("/requests");


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
    ).textContent =
        requests.length;



    // No requests

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



    // Render every request

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


    // Find the complete request
    // from the loaded CSV data.

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



    showLoading();



    try {


        // ----------------------------------------------------
        // SEND REQUEST TO YOUR EXISTING AGENT ENDPOINT
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



        const data =
            await response.json();



        if (!response.ok) {

            throw new Error(

                data.detail ||
                "Validation failed"

            );

        }



        // ----------------------------------------------------
        // STORE AGENT JSON
        // ----------------------------------------------------

        currentAgentResult =
            data.agent_result;



        // ----------------------------------------------------
        // SHOW RESULT
        // ----------------------------------------------------

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
// DISPLAY AGENT RESULT
// ============================================================

function showResult(data) {


    const result =
        data.agent_result;



    // Show result panel

    document.getElementById(
        "resultPanel"
    ).classList.remove(
        "hidden"
    );



    // Request ID

    document.getElementById(
        "resultRequestId"
    ).textContent =

        `Request ID: ${
            data.request?.request_id || ""
        }`;



    // Classification

    document.getElementById(
        "classification"
    ).textContent =

        result.classification ||
        "—";



    // Decision

    document.getElementById(
        "decision"
    ).textContent =

        formatDecision(
            result.decision
        );



    // --------------------------------------------------------
    // ACTIONS TAKEN
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


    // Make sure an agent result exists

    if (!currentAgentResult) {

        alert(
            "No validated request available."
        );

        return;

    }



    showLoading();



    try {


        // ----------------------------------------------------
        // SEND THE EXACT AGENT JSON
        // TO /completeRequest
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



        const data =
            await response.json();



        if (!response.ok || !data.success) {

            throw new Error(

                data.message ||
                data.detail ||
                "Failed to save request"

            );

        }



        // ----------------------------------------------------
        // SAVE SUCCESSFUL
        // ----------------------------------------------------


        // Increment validated count

        const validatedCount =
            document.getElementById(
                "validatedCount"
            );


        validatedCount.textContent =
            parseInt(
                validatedCount.textContent || "0"
            ) + 1;



        // ----------------------------------------------------
        // REMOVE FROM LOCAL TABLE
        //
        // Backend has already removed it from
        // incoming_requests.csv.
        // ----------------------------------------------------

        requests =
            requests.filter(

                request =>
                    request.request_id !==
                    currentAgentResult.request_id

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
        // CLEAR CURRENT RESULT
        // ----------------------------------------------------

        currentAgentResult = null;



        alert(
            "Request saved successfully."
        );



    } catch (error) {


        console.error(error);


        alert(

            error.message ||
            "Failed to save completed request."

        );


    } finally {


        hideLoading();

    }

}



// ============================================================
// CLOSE RESULT PANEL
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


    return decision

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
// JAVASCRIPT STRING ESCAPING
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

loadRequests();
