// ============================================================
// CONFIGURATION
// ============================================================

const API_URL = "http://127.0.0.1:8000";


// ============================================================
// LOAD REPORTS
// ============================================================

async function loadReports() {

    showLoading();

    try {

        const response =
            await fetch(`${API_URL}/reports`);


        if (!response.ok) {

            const errorText =
                await response.text();

            throw new Error(
                errorText ||
                `Failed to load reports. HTTP ${response.status}`
            );

        }


        const data =
            await response.json();


        console.log("Reports response:", data);


        if (!data.success) {

            throw new Error(
                data.message ||
                "Failed to load reports."
            );

        }


        // ----------------------------------------------------
        // SUMMARY
        // ----------------------------------------------------

        updateSummary(data);


        // ----------------------------------------------------
        // CLASSIFICATION
        // ----------------------------------------------------

        renderClassification(
            data.classification_counts || {}
        );


        // ----------------------------------------------------
        // DECISIONS
        // ----------------------------------------------------

        renderDecisionSummary(
            data.requests || [],
            data.summary || {}
        );


        // ----------------------------------------------------
        // REQUEST TABLE
        // ----------------------------------------------------

        renderRequests(
            data.requests || []
        );


    } catch (error) {

        console.error(
            "Reports loading error:",
            error
        );

        alert(
            "Unable to load reports.\n\n" +
            error.message
        );

    } finally {

        hideLoading();

    }

}


// ============================================================
// UPDATE SUMMARY
// ============================================================

function updateSummary(data) {

    const summary =
        data.summary || {};

    document.getElementById(
        "totalCompleted"
    ).textContent =
        summary.total_completed || 0;


    document.getElementById(
        "humanReview"
    ).textContent =
        summary.human_review || 0;


    document.getElementById(
        "courtesyResolution"
    ).textContent =
        summary.courtesy_resolution || 0;


    const classifications =
        data.classification_counts || {};

    document.getElementById(
        "requestTypes"
    ).textContent =
        Object.keys(classifications).length;
}


// ============================================================
// CLASSIFICATION REPORT
// ============================================================

function renderClassification(classifications) {

    const container =
        document.getElementById(
            "classificationReport"
        );


    container.innerHTML = "";


    const entries =
        Object.entries(classifications);


    if (entries.length === 0) {

        container.innerHTML = `
            <div class="empty">
                No completed requests available.
            </div>
        `;

        return;
    }


    // Find largest category
    const maxCount =
        Math.max(
            ...entries.map(
                ([, count]) => Number(count) || 0
            ),
            1
        );


    // Sort highest first
    entries.sort(
        (a, b) =>
            Number(b[1]) - Number(a[1])
    );


    entries.forEach(
        ([classification, count]) => {

            const percentage =
                ((Number(count) / maxCount) * 100)
                .toFixed(1);


            const row =
                document.createElement("div");

            row.className =
                "classification-row";


            row.innerHTML = `

                <div class="classification-header">

                    <span class="classification-name">
                        ${escapeHtml(classification)}
                    </span>

                    <span class="classification-count">
                        ${Number(count) || 0}
                    </span>

                </div>


                <div class="progress-background">

                    <div
                        class="progress-bar"
                        style="width: ${percentage}%"
                    ></div>

                </div>

            `;


            container.appendChild(row);

        }
    );

}


// ============================================================
// DECISION SUMMARY
// ============================================================

function renderDecisionSummary(
    requests,
    summary
) {

    let automated = 0;
    let humanReview = 0;
    let acknowledged = 0;


    requests.forEach(request => {

        const decision =
            String(
                request.decision || ""
            ).toLowerCase();


        if (
            decision.includes("human") ||
            decision.includes("review")
        ) {

            humanReview++;

        }
        else if (
            decision.includes("acknowledge")
        ) {

            acknowledged++;

        }
        else {

            automated++;

        }

    });


    // If backend provides human review count,
    // prefer it when there are no request records.

    if (
        requests.length === 0 &&
        summary.human_review
    ) {

        humanReview =
            Number(summary.human_review);

    }


    document.getElementById(
        "automatedCount"
    ).textContent =
        automated;


    document.getElementById(
        "decisionReviewCount"
    ).textContent =
        humanReview;


    document.getElementById(
        "acknowledgedCount"
    ).textContent =
        acknowledged;
}


// ============================================================
// REQUEST TABLE
// ============================================================

function renderRequests(requests) {

    const table =
        document.getElementById(
            "requestTable"
        );


    table.innerHTML = "";


    document.getElementById(
        "tableCount"
    ).textContent =
        `${requests.length} request${
            requests.length === 1 ? "" : "s"
        }`;


    if (requests.length === 0) {

        table.innerHTML = `

            <tr>

                <td
                    colspan="6"
                    class="empty"
                >
                    No completed requests found.
                </td>

            </tr>

        `;

        return;
    }


    requests.forEach(request => {

        const row =
            document.createElement("tr");


        const actions =
            formatActions(
                request.actions_taken
            );


        row.innerHTML = `

            <td>

                <span class="request-id">

                    ${escapeHtml(
                        request.request_id || ""
                    )}

                </span>

            </td>


            <td>

                <span class="classification-cell">

                    ${escapeHtml(
                        request.classification || "—"
                    )}

                </span>

            </td>


            <td>

                <span class="decision-badge">

                    ${escapeHtml(
                        formatDecision(
                            request.decision
                        )
                    )}

                </span>

            </td>


            <td>

                <div class="actions-cell">

                    ${escapeHtml(actions)}

                </div>

            </td>


            <td>

                <div class="reason-cell">

                    ${escapeHtml(
                        request.reason || "—"
                    )}

                </div>

            </td>


            <td>

                <div class="completed-cell">

                    ${escapeHtml(
                        request.completed_at || "—"
                    )}

                </div>

            </td>

        `;


        table.appendChild(row);

    });

}


// ============================================================
// FORMAT ACTIONS
// ============================================================

function formatActions(actions) {

    if (!actions) {
        return "—";
    }


    // Backend may return:
    // "action1;action2;action3"

    if (typeof actions === "string") {

        return actions
            .split(";")
            .map(action => formatAction(action))
            .join(" • ");

    }


    // Or an array

    if (Array.isArray(actions)) {

        return actions
            .map(action => formatAction(action))
            .join(" • ");

    }


    return String(actions);
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
// INITIAL LOAD
// ============================================================

loadReports();
