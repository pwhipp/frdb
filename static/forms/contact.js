const {
    cancelVerification,
    cleanVerificationCode,
    postForm,
    setFormEnabled,
    setVerifyButtonState,
    submitCooldownRemaining,
    verificationStatus,
} = window.FRDBVerification;

let contactRequestId = "";
let lastContactSubmitAt = 0;

const contactForm = document.getElementById("contactForm");
const contactEmail = document.getElementById("contactEmail");
const contactSubject = document.getElementById("contactSubject");
const contactMessage = document.getElementById("contactMessage");
const contactSubmit = document.getElementById("contactSubmit");
const contactCancel = document.getElementById("contactCancel");
const contactVerification = document.getElementById("contactVerification");
const contactStatus = document.getElementById("contactStatus");
const contactCode = document.getElementById("contactCode");
const contactVerify = document.getElementById("contactVerify");
const contactVerifyCancel = document.getElementById("contactVerifyCancel");

contactForm.addEventListener("input", updateContactState);
contactForm.addEventListener("change", updateContactState);
contactSubject.addEventListener("input", () => updateCounter("subjectCount", contactSubject.value.length));
contactMessage.addEventListener("input", () => updateCounter("messageCount", contactMessage.value.length));
contactCancel.addEventListener("click", resetContactForm);
contactVerifyCancel.addEventListener("click", cancelContactVerification);
contactCode.addEventListener("input", () => {
    contactCode.value = cleanVerificationCode(contactCode.value);
    setVerifyButtonState(contactVerify, contactRequestId, contactCode.value);
});

contactForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    if (!isContactFormReady()) {
        updateContactState();
        return;
    }
    const remainingSeconds = submitCooldownRemaining(lastContactSubmitAt);
    if (remainingSeconds > 0) {
        setStatus(`You must wait ${remainingSeconds} seconds before submitting again`);
        return;
    }

    lastContactSubmitAt = Date.now();
    setStatus("Sending verification code...");
    const response = await postForm("/api/contact/start", new FormData(contactForm));
    if (!response.ok) {
        setStatus(response.error);
        return;
    }
    contactRequestId = response.data.request_id;
    contactVerification.classList.remove("d-none");
    contactSubmit.disabled = true;
    setFormEnabled(contactForm, false);
    setStatus(verificationStatus(response.data));
});

contactVerify.addEventListener("click", async () => {
    const formData = new FormData();
    formData.set("request_id", contactRequestId);
    formData.set("code", contactCode.value);
    setStatus("Verifying...");
    const response = await postForm("/api/contact/verify", formData);
    if (!response.ok) {
        setStatus(response.error);
        return;
    }
    setStatus(response.data.message);
    contactVerify.disabled = true;
    contactVerifyCancel.disabled = true;
});

function updateContactState() {
    contactSubmit.disabled = !isContactFormReady();
}

function isContactFormReady() {
    return (
        contactEmail.value.trim().length > 0
        && contactEmail.value.trim().length <= 254
        && contactSubject.value.trim().length > 0
        && contactSubject.value.trim().length <= 132
        && contactMessage.value.trim().length > 0
        && contactMessage.value.trim().length <= 1000
    );
}

async function cancelContactVerification() {
    await cancelVerification(contactRequestId);
    resetContactForm();
}

function resetContactForm() {
    contactRequestId = "";
    contactForm.reset();
    contactCode.value = "";
    contactVerification.classList.add("d-none");
    contactVerify.disabled = true;
    contactVerifyCancel.disabled = false;
    setFormEnabled(contactForm, true);
    setStatus("");
    updateCounter("subjectCount", 0);
    updateCounter("messageCount", 0);
    updateContactState();
}

function setStatus(message) {
    contactStatus.textContent = message || "";
}

function updateCounter(id, count) {
    document.getElementById(id).textContent = count;
}

updateContactState();
