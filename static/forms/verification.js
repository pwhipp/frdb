(function () {
    const emailPattern = /^[^@\s]+@[^@\s]+\.[^@\s]+$/;

    function cleanVerificationCode(value) {
        return value.replace(/\D/g, "").slice(0, 5);
    }

    function setVerifyButtonState(button, requestId, code) {
        button.disabled = !(requestId && code.trim().length > 0);
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

    async function cancelVerification(requestId) {
        if (!requestId) {
            return;
        }

        const formData = new FormData();
        formData.set("request_id", requestId);
        await postForm("/api/verification/cancel", formData);
    }

    window.FRDBVerification = {
        cancelVerification,
        cleanVerificationCode,
        emailPattern,
        postForm,
        setFormEnabled,
        setVerifyButtonState,
        verificationStatus,
    };
}());
