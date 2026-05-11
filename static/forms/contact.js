const emailPattern = /^[^@\s]+@[^@\s]+\.[^@\s]+$/;
let contactRequestId = "";
let contactCodeCheck = 0;

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
contactSubject.addEventListener("input", () => updateCounter("subjectCount", contactSubject.value.length));
contactMessage.addEventListener("input", () => updateCounter("messageCount", contactMessage.value.length));
contactCancel.addEventListener("click", resetContactForm);
contactVerifyCancel.addEventListener("click", cancelContactVerification);
contactCode.addEventListener("input", async () => {
    contactCode.value = contactCode.value.replace(/\D/g, "").slice(0, 5);
    const checkId = ++contactCodeCheck;
    contactVerify.disabled = true;
    if (contactCode.value.length === 5) {
        contactVerify.disabled = !(await checkCode(contactRequestId, contactCode.value, checkId));
    }
});

contactForm.addEventListener("submit", async (event) => {
    event.preventDefault();
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
    setStatus("A verification code has been emailed to you.");
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
    contactSubmit.disabled = !(
        emailPattern.test(contactEmail.value.trim())
        && contactSubject.value.trim().length > 0
        && contactSubject.value.trim().length <= 132
        && contactMessage.value.trim().length > 0
        && contactMessage.value.trim().length <= 1000
    );
}

async function cancelContactVerification() {
    if (contactRequestId) {
        const formData = new FormData();
        formData.set("request_id", contactRequestId);
        await postForm("/api/verification/cancel", formData);
    }
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
    return checkId === contactCodeCheck && response.ok && response.data.verified;
}

updateContactState();
