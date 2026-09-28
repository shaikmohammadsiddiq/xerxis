const API_URL = "http://127.0.0.1:8000";


const form =
    document.getElementById("requestForm");


form.addEventListener(
    "submit",
    submitRequest
);


async function submitRequest(event) {

    event.preventDefault();


    const studentId =
        document.getElementById("studentId").value.trim();

    const studentName =
        document.getElementById("studentName").value.trim();

    const studentStatus =
        document.getElementById("studentStatus").value;

    const requestType =
        document.getElementById("requestType").value;

    const requestText =
        document.getElementById("requestText").value.trim();


    if (
        !studentId ||
        !studentName ||
        !studentStatus ||
        !requestText
    ) {

        alert(
            "Please fill in all required fields."
        );

        return;
    }


    showLoading();


    const payload = {

        student_id:
            studentId,

        student_name:
            studentName,

        student_status:
            studentStatus,

        request_type:
            requestType,

        body_text:
            requestText

    };


    try {

        const response =
            await fetch(
                `${API_URL}/submitRequest`,
                {

                    method: "POST",

                    headers: {
                        "Content-Type":
                            "application/json"
                    },

                    body:
                        JSON.stringify(payload)

                }
            );


        const data =
            await response.json();


        console.log(
            "Submit response:",
            data
        );


        if (!response.ok) {

            throw new Error(
                data.detail ||
                data.message ||
                "Failed to submit request."
            );

        }


        if (!data.success) {

            throw new Error(
                data.message ||
                "Request was not submitted."
            );

        }


        /*
         * Your API should return:
         *
         * {
         *   success: true,
         *   request_id: "REQ1020"
         * }
         */


        document.getElementById(
            "requestId"
        ).textContent =
            data.request_id;


        document.getElementById(
            "requestForm"
        ).classList.add(
            "hidden"
        );


        document.getElementById(
            "successPanel"
        ).classList.remove(
            "hidden"
        );


    } catch (error) {

        console.error(
            "Submit error:",
            error
        );


        alert(
            "Unable to submit request.\n\n" +
            error.message
        );

    } finally {

        hideLoading();

    }

}


// NEW REQUEST

function newRequest() {

    document.getElementById(
        "requestForm"
    ).reset();


    document.getElementById(
        "successPanel"
    ).classList.add(
        "hidden"
    );


    document.getElementById(
        "requestForm"
    ).classList.remove(
        "hidden"
    );

}


// LOADING


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
