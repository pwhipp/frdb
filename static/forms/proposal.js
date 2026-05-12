const emailPattern = /^[^@\s]+@[^@\s]+\.[^@\s]+$/;
let proposalRequestId = "";
let proposalCodeCheck = 0;

const proposalForm = document.getElementById("proposalForm");
const proposalEmail = document.getElementById("proposalEmail");
const proposalWorkbook = document.getElementById("proposalWorkbook");
const proposalSubmit = document.getElementById("proposalSubmit");
const proposalCancel = document.getElementById("proposalCancel");
const proposalVerification = document.getElementById("proposalVerification");
const proposalStatus = document.getElementById("proposalStatus");
const proposalCode = document.getElementById("proposalCode");
const proposalVerify = document.getElementById("proposalVerify");
const proposalVerifyCancel = document.getElementById("proposalVerifyCancel");

proposalForm.addEventListener("input", updateProposalState);
proposalForm.addEventListener("change", updateProposalState);
proposalCancel.addEventListener("click", resetProposalForm);
proposalVerifyCancel.addEventListener("click", cancelProposalVerification);
proposalCode.addEventListener("input", async () => {
    proposalCode.value = proposalCode.value.replace(/\D/g, "").slice(0, 5);
    const checkId = ++proposalCodeCheck;
    proposalVerify.disabled = true;
    if (proposalCode.value.length === 5) {
        proposalVerify.disabled = !(await checkCode(proposalRequestId, proposalCode.value, checkId));
    }
});

proposalForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    setStatus("Sending verification code...");
    const formData = new FormData();
    formData.set("email", proposalEmail.value);
    const response = await postForm("/api/propose/start", formData);
    if (!response.ok) {
        setStatus(response.error);
        return;
    }
    proposalRequestId = response.data.request_id;
    proposalVerification.classList.remove("d-none");
    proposalSubmit.disabled = true;
    setFormEnabled(proposalForm, false);
    setStatus(verificationStatus(response.data));
});

proposalVerify.addEventListener("click", async () => {
    const formData = new FormData();
    formData.set("request_id", proposalRequestId);
    formData.set("code", proposalCode.value);
    formData.set("workbook", proposalWorkbook.files[0]);
    setStatus("Uploading...");
    const response = await postForm("/api/propose/verify", formData);
    if (!response.ok) {
        setStatus(response.error);
        return;
    }
    setStatus(response.data.message);
    proposalVerify.disabled = true;
    proposalVerifyCancel.disabled = true;
});

function updateProposalState() {
    const file = proposalWorkbook.files[0];
    proposalSubmit.disabled = !(
        emailPattern.test(proposalEmail.value.trim())
        && file
        && file.name.toLowerCase().endsWith(".xlsx")
    );
}

async function cancelProposalVerification() {
    if (proposalRequestId) {
        const formData = new FormData();
        formData.set("request_id", proposalRequestId);
        await postForm("/api/verification/cancel", formData);
    }
    resetProposalForm();
}

function resetProposalForm() {
    proposalRequestId = "";
    proposalForm.reset();
    proposalCode.value = "";
    proposalVerification.classList.add("d-none");
    proposalVerify.disabled = true;
    proposalVerifyCancel.disabled = false;
    setFormEnabled(proposalForm, true);
    setStatus("");
    updateProposalState();
}

function setStatus(message) {
    proposalStatus.textContent = message || "";
}

function verificationStatus(data) {
    if (data.verification_code) {
        return `Local verification code: ${data.verification_code}`;
    }
    return "A verification code has been emailed to you.";
}

function setFormEnabled(form, enabled) {
    for (const element of form.elements) {
        element.disabled = !enabled;
    }
}

async function postForm(url, formData) {
    try {
        const response = await fetch(url, {
            method: "POST",
            body: formData,
        });
        const data = await response.json();
        return response.ok
            ? { ok: true, data }
            : { ok: false, error: data.error || "Request failed." };
    } catch {
        return { ok: false, error: "Network request failed." };
    }
}

async function checkCode(requestId, code, checkId) {
    const formData = new FormData();
    formData.set("request_id", requestId);
    formData.set("code", code);
    const response = await postForm("/api/verification/check", formData);
    return checkId === proposalCodeCheck && response.ok && response.data.verified;
}

updateProposalState();
