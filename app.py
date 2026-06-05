import time

from flask import Flask, jsonify, render_template, request, send_from_directory

from local_settings import CONTACT_RECIPIENT
from frdb import (
    CODE_TTL_MINUTES,
    EmailDeliveryError,
    cancel_verification,
    create_verification,
    load_filter_highlight_terms,
    load_research_data,
    pop_verified,
    save_verified_upload,
    send_email,
    validate_code,
    validate_email,
    validate_text,
)

app = Flask(__name__)

VERIFICATION_EMAIL_COOLDOWN_SECONDS = 10
verification_email_last_sent_at: dict[str, float] = {}


class VerificationEmailCooldownError(Exception):
    pass


@app.route('/')
def index():
    return render_template('index.html', filter_highlight_terms=load_filter_highlight_terms())


@app.route('/propose-additions')
def propose_additions():
    return render_template('propose_additions.html')


@app.route('/contact-us')
def contact_us():
    return render_template('contact_us.html')


@app.route('/about')
def about():
    return render_template('about.html')


@app.route('/assets/example.xlsx')
def example_workbook():
    return send_from_directory('assets', 'example.xlsx', as_attachment=True)


@app.route('/api/research-data')
def research_data():
    return jsonify(load_research_data())


@app.post('/api/contact/start')
def start_contact():
    try:
        email = validate_email(request.form.get('email', ''))
        subject = validate_text(request.form.get('subject', ''), 'Subject', 132)
        message = validate_text(request.form.get('message', ''), 'Message', 1000)
        request_id = start_email_verification('contact', {
            'email': email,
            'subject': subject,
            'message': message,
        })
    except VerificationEmailCooldownError as error:
        return jsonify({'error': str(error)}), 429
    except ValueError as error:
        return jsonify({'error': str(error)}), 400
    except EmailDeliveryError as error:
        return jsonify({'error': str(error)}), 503

    return verification_start_response(request_id)


@app.post('/api/contact/verify')
def verify_contact():
    try:
        request_id = validate_text(request.form.get('request_id', ''), 'Verification request', 64)
        code = validate_code(request.form.get('code', ''))
    except ValueError as error:
        return jsonify({'error': str(error)}), 400

    payload = pop_verified(request_id, code)
    if payload is None:
        return jsonify({'error': 'Verification code is incorrect or expired.'}), 400

    try:
        send_email(
            CONTACT_RECIPIENT,
            f"FRDB contact: {payload['subject']}",
            f"From: {payload['email']}\n\n{payload['message']}",
        )
    except EmailDeliveryError as error:
        return jsonify({'error': str(error)}), 503

    return jsonify({'message': 'Your message has been sent.'})


@app.post('/api/propose/start')
def start_proposal():
    try:
        email = validate_email(request.form.get('email', ''))
        request_id = start_email_verification('proposal', {'email': email})
    except VerificationEmailCooldownError as error:
        return jsonify({'error': str(error)}), 429
    except ValueError as error:
        return jsonify({'error': str(error)}), 400
    except EmailDeliveryError as error:
        return jsonify({'error': str(error)}), 503

    return verification_start_response(request_id)


@app.post('/api/propose/verify')
def verify_proposal():
    try:
        request_id = validate_text(request.form.get('request_id', ''), 'Verification request', 64)
        code = validate_code(request.form.get('code', ''))
    except ValueError as error:
        return jsonify({'error': str(error)}), 400

    payload = pop_verified(request_id, code)
    if payload is None:
        return jsonify({'error': 'Verification code is incorrect or expired.'}), 400

    try:
        destination = save_verified_upload(request.files.get('workbook'), payload['email'])
        send_proposal_upload_notification(destination.name, payload['email'])
    except ValueError as error:
        return jsonify({'error': str(error)}), 400
    except EmailDeliveryError as error:
        return jsonify({'error': str(error)}), 503

    return jsonify({'message': f'Workbook uploaded for review: {destination.name}'})


@app.post('/api/verification/cancel')
def cancel_pending_verification():
    request_id = request.form.get('request_id', '')
    if request_id:
        cancel_verification(request_id)
    return jsonify({'message': 'Verification cancelled.'})


def verification_start_response(request_id: str):
    return jsonify({'request_id': request_id})


def start_email_verification(purpose: str, payload: dict) -> str:
    enforce_verification_email_cooldown()
    request_id, code = create_verification(payload)
    send_email(
        payload['email'],
        f'FRDB {purpose} verification code',
        verification_email_body(purpose, code),
    )
    verification_email_last_sent_at[verification_cooldown_key()] = time.monotonic()
    return request_id


def verification_email_body(purpose: str, code: str) -> str:
    return (
        f'Your FRDB {purpose} verification code is {code}.'
        f'\n\nThis code expires in {CODE_TTL_MINUTES} minutes.'
    )


def enforce_verification_email_cooldown() -> None:
    last_sent_at = verification_email_last_sent_at.get(verification_cooldown_key())
    if last_sent_at is None:
        return

    remaining_seconds = VERIFICATION_EMAIL_COOLDOWN_SECONDS - (time.monotonic() - last_sent_at)
    if remaining_seconds > 0:
        raise VerificationEmailCooldownError(
            f'Wait {int(remaining_seconds) + 1} seconds before requesting another verification code.'
        )


def verification_cooldown_key() -> str:
    return request.remote_addr or 'unknown'


def send_proposal_upload_notification(filename: str, uploader_email: str) -> None:
    send_email(
        CONTACT_RECIPIENT,
        'FRDB proposal workbook uploaded',
        f'Workbook uploaded for review: {filename}\n\nUploader: {uploader_email}',
    )


if __name__ == '__main__':
    app.run(debug=True)
