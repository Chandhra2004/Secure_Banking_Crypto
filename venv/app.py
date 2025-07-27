from flask import Flask, render_template_string, request, redirect, url_for, flash
import os
import json
from pathlib import Path
from main import (
    KEYS_DIR, MSG_DIR, is_key_revoked, construct_secure_message, decrypt_and_verify_message, load_key, load_json
)

app = Flask(__name__)
app.secret_key = 'supersecretkey'  # Change for production

@app.route('/')
def index():
    return render_template_string('''
    <h2>Secure Messaging Web UI</h2>
    <ul>
      <li><a href="{{ url_for('customer_send') }}">Customer: Send Message to Bank</a></li>
      <li><a href="{{ url_for('bank_read') }}">Bank: Read Message from Customer</a></li>
      <li><a href="{{ url_for('bank_reply') }}">Bank: Reply to Customer</a></li>
      <li><a href="{{ url_for('customer_read') }}">Customer: Read Bank Reply</a></li>
    </ul>
    ''')

@app.route('/customer/send', methods=['GET', 'POST'])
def customer_send():
    if request.method == 'POST':
        if is_key_revoked('bank_public.pem'):
            flash('Bank key revoked. Cannot send message.', 'error')
        else:
            msg = request.form['message']
            cust_priv = load_key(KEYS_DIR / 'customer_private.pem')
            bank_pub = load_key(KEYS_DIR / 'bank_public.pem')
            message_payload = construct_secure_message(cust_priv, bank_pub, msg)
            MSG_DIR.joinpath('to_bank.json').write_text(json.dumps(message_payload, indent=2))
            flash('Message sent to bank.', 'success')
        return redirect(url_for('customer_send'))
    return render_template_string('''
    <h3>Customer: Send Message to Bank</h3>
    <form method="post">
      <textarea name="message" rows="4" cols="50" required></textarea><br>
      <button type="submit">Send</button>
    </form>
    <a href="/">Back</a>
    {% with messages = get_flashed_messages(with_categories=true) %}
      {% if messages %}
        <ul>
        {% for category, message in messages %}
          <li style="color:{{ 'red' if category=='error' else 'green' }}">{{ message }}</li>
        {% endfor %}
        </ul>
      {% endif %}
    {% endwith %}
    ''')

@app.route('/bank/read')
def bank_read():
    if is_key_revoked('customer_public.pem'):
        return '<p>Customer key revoked. Cannot receive message.</p><a href="/">Back</a>'
    msg_data = load_json(MSG_DIR / 'to_bank.json')
    bank_priv = load_key(KEYS_DIR / 'bank_private.pem')
    cust_pub = load_key(KEYS_DIR / 'customer_public.pem')
    try:
        plaintext = decrypt_and_verify_message(bank_priv, cust_pub, msg_data)
        return f'<h3>Bank: Received message</h3><p>{plaintext}</p><a href="/">Back</a>'
    except Exception as e:
        return f'<h3>Bank: Message rejected</h3><p>{e}</p><a href="/">Back</a>'

@app.route('/bank/reply', methods=['GET', 'POST'])
def bank_reply():
    if request.method == 'POST':
        if is_key_revoked('customer_public.pem'):
            flash('Customer key revoked. Cannot send message.', 'error')
        else:
            msg = request.form['message']
            bank_priv = load_key(KEYS_DIR / 'bank_private.pem')
            cust_pub = load_key(KEYS_DIR / 'customer_public.pem')
            message_payload = construct_secure_message(bank_priv, cust_pub, msg)
            MSG_DIR.joinpath('to_customer.json').write_text(json.dumps(message_payload, indent=2))
            flash('Reply sent to customer.', 'success')
        return redirect(url_for('bank_reply'))
    return render_template_string('''
    <h3>Bank: Reply to Customer</h3>
    <form method="post">
      <textarea name="message" rows="4" cols="50" required></textarea><br>
      <button type="submit">Send Reply</button>
    </form>
    <a href="/">Back</a>
    {% with messages = get_flashed_messages(with_categories=true) %}
      {% if messages %}
        <ul>
        {% for category, message in messages %}
          <li style="color:{{ 'red' if category=='error' else 'green' }}">{{ message }}</li>
        {% endfor %}
        </ul>
      {% endif %}
    {% endwith %}
    ''')

@app.route('/customer/read')
def customer_read():
    if is_key_revoked('bank_public.pem'):
        return '<p>Bank key revoked. Cannot receive message.</p><a href="/">Back</a>'
    msg_data = load_json(MSG_DIR / 'to_customer.json')
    cust_priv = load_key(KEYS_DIR / 'customer_private.pem')
    bank_pub = load_key(KEYS_DIR / 'bank_public.pem')
    try:
        plaintext = decrypt_and_verify_message(cust_priv, bank_pub, msg_data)
        return f'<h3>Customer: Received reply from Bank</h3><p>{plaintext}</p><a href="/">Back</a>'
    except Exception as e:
        return f'<h3>Customer: Message rejected</h3><p>{e}</p><a href="/">Back</a>'

if __name__ == '__main__':
    app.run(debug=True)
