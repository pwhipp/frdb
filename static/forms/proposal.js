const {
    cancelVerification,
    cleanVerificationCode,
    emailPattern,
    postForm,
    setFormEnabled,
    setVerifyButtonState,
    verificationStatus,
} = window.FRDBVerification;

let proposalRequestId = "";

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
proposalCode.addEventListener("input", () => {
    proposalCode.value = cleanVerificationCode(proposalCode.value);
    setVerifyButtonState(proposalVerify, proposalRequestId, proposalCode.value);
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
    await cancelVerification(proposalRequestId);
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

updateProposalState();
