from flask import Flask, jsonify, render_template, request, send_from_directory

from frdb_forms import CONTACT_RECIPIENT, save_verified_upload, validate_code, validate_email, validate_text
from frdb_data import load_research_data
from frdb_mail import EmailDeliveryError, send_email
from frdb_verification import cancel_verification, check_verification, create_verification, pop_verified

app = Flask(__name__)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/propose-additions')
def propose_additions():
    return render_template('propose_additions.html')


@app.route('/contact-us')
def contact_us():
    return render_template('contact_us.html')


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
        request_id, code = create_verification({
            'email': email,
            'subject': subject,
            'message': message,
        })
        send_email(
            email,
            'FRDB contact verification code',
            f'Your FRDB contact verification code is {code}.\n\nThis code expires in 15 minutes.',
        )
    except ValueError as error:
        return jsonify({'error': str(error)}), 400
    except EmailDeliveryError as error:
        return jsonify({'error': str(error)}), 503

    return jsonify({'request_id': request_id})


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
        request_id, code = create_verification({'email': email})
        send_email(
            email,
            'FRDB proposal verification code',
            f'Your FRDB proposal verification code is {code}.\n\nThis code expires in 15 minutes.',
        )
    except ValueError as error:
        return jsonify({'error': str(error)}), 400
    except EmailDeliveryError as error:
        return jsonify({'error': str(error)}), 503

    return jsonify({'request_id': request_id})


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
    except ValueError as error:
        return jsonify({'error': str(error)}), 400

    return jsonify({'message': f'Workbook uploaded for review: {destination.name}'})


@app.post('/api/verification/cancel')
def cancel_pending_verification():
    request_id = request.form.get('request_id', '')
    if request_id:
        cancel_verification(request_id)
    return jsonify({'message': 'Verification cancelled.'})


@app.post('/api/verification/check')
def check_pending_verification():
    try:
        request_id = validate_text(request.form.get('request_id', ''), 'Verification request', 64)
        code = validate_code(request.form.get('code', ''))
    except ValueError:
        return jsonify({'verified': False})

    return jsonify({'verified': check_verification(request_id, code)})


if __name__ == '__main__':
    app.run(debug=True)
