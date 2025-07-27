from flask import Flask, render_template_string, request, redirect, url_for, flash
import os
import json
from pathlib import Path
from main import (
    KEYS_DIR, MSG_DIR, is_key_revoked, construct_secure_message, 
    decrypt_and_verify_message, load_key, load_json
)

app = Flask(__name__)
app.secret_key = 'supersecretkey'  # Change for production

# Base template with improved styling
BASE_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Secure Messaging System</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        
        .container {
            max-width: 800px;
            margin: 0 auto;
            background: white;
            border-radius: 15px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            overflow: hidden;
        }
        
        .header {
            background: linear-gradient(135deg, #2c3e50 0%, #34495e 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }
        
        .header h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
            font-weight: 300;
        }
        
        .header p {
            opacity: 0.8;
            font-size: 1.1em;
        }
        
        .content {
            padding: 40px;
        }
        
        .nav-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .nav-card {
            background: #f8f9fa;
            border: 2px solid #e9ecef;
            border-radius: 10px;
            padding: 25px;
            text-decoration: none;
            color: #2c3e50;
            transition: all 0.3s ease;
            display: block;
        }
        
        .nav-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 10px 25px rgba(0,0,0,0.1);
            border-color: #667eea;
            text-decoration: none;
            color: #2c3e50;
        }
        
        .nav-card h3 {
            font-size: 1.3em;
            margin-bottom: 10px;
            color: #2c3e50;
        }
        
        .nav-card p {
            color: #6c757d;
            line-height: 1.5;
        }
        
        .form-container {
            background: #f8f9fa;
            border-radius: 10px;
            padding: 30px;
            margin-bottom: 20px;
        }
        
        .form-group {
            margin-bottom: 20px;
        }
        
        .form-group label {
            display: block;
            margin-bottom: 8px;
            font-weight: 600;
            color: #2c3e50;
        }
        
        .form-control {
            width: 100%;
            padding: 12px 15px;
            border: 2px solid #e9ecef;
            border-radius: 8px;
            font-size: 16px;
            transition: border-color 0.3s ease;
            font-family: inherit;
        }
        
        .form-control:focus {
            outline: none;
            border-color: #667eea;
            box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
        }
        
        .btn {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            padding: 12px 30px;
            border-radius: 8px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
            text-decoration: none;
            display: inline-block;
        }
        
        .btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(0,0,0,0.2);
            color: white;
            text-decoration: none;
        }
        
        .btn-secondary {
            background: #6c757d;
            margin-left: 10px;
        }
        
        .alert {
            padding: 15px 20px;
            border-radius: 8px;
            margin-bottom: 20px;
            font-weight: 500;
        }
        
        .alert-success {
            background: #d4edda;
            color: #155724;
            border: 1px solid #c3e6cb;
        }
        
        .alert-error {
            background: #f8d7da;
            color: #721c24;
            border: 1px solid #f5c6cb;
        }
        
        .message-display {
            background: #e3f2fd;
            border-left: 4px solid #2196f3;
            padding: 20px;
            border-radius: 0 8px 8px 0;
            margin: 20px 0;
        }
        
        .message-display h3 {
            color: #1976d2;
            margin-bottom: 15px;
        }
        
        .message-content {
            background: white;
            padding: 15px;
            border-radius: 5px;
            font-family: 'Courier New', monospace;
            white-space: pre-wrap;
            word-wrap: break-word;
        }
        
        .error-display {
            background: #ffebee;
            border-left: 4px solid #f44336;
            padding: 20px;
            border-radius: 0 8px 8px 0;
            margin: 20px 0;
        }
        
        .error-display h3 {
            color: #c62828;
            margin-bottom: 15px;
        }
        
        .back-link {
            margin-top: 20px;
        }
        
        @media (max-width: 768px) {
            .container {
                margin: 10px;
                border-radius: 10px;
            }
            
            .content {
                padding: 20px;
            }
            
            .header {
                padding: 20px;
            }
            
            .header h1 {
                font-size: 2em;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        {% block content %}{% endblock %}
    </div>
</body>
</html>
'''

@app.route('/')
def index():
    return render_template_string(BASE_TEMPLATE + '''
    {% block content %}
    <div class="header">
        <h1>🔐 Secure Messaging System</h1>
        <p>End-to-end encrypted communication between Customer and Bank</p>
    </div>
    <div class="content">
        <div class="nav-grid">
            <a href="{{ url_for('customer_send') }}" class="nav-card">
                <h3>📤 Send Message</h3>
                <p>Customer: Send a secure message to the bank with encryption and digital signature</p>
            </a>
            <a href="{{ url_for('bank_read') }}" class="nav-card">
                <h3>📥 Read Message</h3>
                <p>Bank: Read and verify the message received from customer</p>
            </a>
            <a href="{{ url_for('bank_reply') }}" class="nav-card">
                <h3>💬 Send Reply</h3>
                <p>Bank: Send a secure reply back to the customer</p>
            </a>
            <a href="{{ url_for('customer_read') }}" class="nav-card">
                <h3>📨 Read Reply</h3>
                <p>Customer: Read the bank's reply and verify its authenticity</p>
            </a>
        </div>
    </div>
    {% endblock %}
    ''')

@app.route('/customer/send', methods=['GET', 'POST'])
def customer_send():
    if request.method == 'POST':
        if is_key_revoked('bank_public.pem'):
            flash('Bank key has been revoked. Cannot send message.', 'error')
        else:
            msg = request.form['message']
            cust_priv = load_key(KEYS_DIR / 'customer_private.pem')
            bank_pub = load_key(KEYS_DIR / 'bank_public.pem')
            message_payload = construct_secure_message(cust_priv, bank_pub, msg)
            MSG_DIR.joinpath('to_bank.json').write_text(json.dumps(message_payload, indent=2))
            flash('Message successfully sent to bank!', 'success')
        return redirect(url_for('customer_send'))
    
    return render_template_string(BASE_TEMPLATE + '''
    {% block content %}
    <div class="header">
        <h1>📤 Send Message to Bank</h1>
        <p>Customer Portal</p>
    </div>
    <div class="content">
        {% with messages = get_flashed_messages(with_categories=true) %}
            {% if messages %}
                {% for category, message in messages %}
                    <div class="alert alert-{{ category }}">{{ message }}</div>
                {% endfor %}
            {% endif %}
        {% endwith %}
        
        <div class="form-container">
            <form method="post">
                <div class="form-group">
                    <label for="message">Your Message:</label>
                    <textarea id="message" name="message" class="form-control" rows="6" 
                              placeholder="Enter your secure message to the bank..." required></textarea>
                </div>
                <button type="submit" class="btn">🔒 Send Secure Message</button>
                <a href="/" class="btn btn-secondary">← Back to Home</a>
            </form>
        </div>
    </div>
    {% endblock %}
    ''')

@app.route('/bank/read')
def bank_read():
    if is_key_revoked('customer_public.pem'):
        return render_template_string(BASE_TEMPLATE + '''
        {% block content %}
        <div class="header">
            <h1>📥 Read Customer Message</h1>
            <p>Bank Portal</p>
        </div>
        <div class="content">
            <div class="error-display">
                <h3>⚠️ Access Denied</h3>
                <p>Customer key has been revoked. Cannot receive message.</p>
            </div>
            <div class="back-link">
                <a href="/" class="btn">← Back to Home</a>
            </div>
        </div>
        {% endblock %}
        ''')
    
    try:
        msg_data = load_json(MSG_DIR / 'to_bank.json')
        bank_priv = load_key(KEYS_DIR / 'bank_private.pem')
        cust_pub = load_key(KEYS_DIR / 'customer_public.pem')
        plaintext = decrypt_and_verify_message(bank_priv, cust_pub, msg_data)
        
        return render_template_string(BASE_TEMPLATE + '''
        {% block content %}
        <div class="header">
            <h1>📥 Customer Message</h1>
            <p>Bank Portal</p>
        </div>
        <div class="content">
            <div class="message-display">
                <h3>✅ Message Successfully Verified</h3>
                <div class="message-content">{{ message }}</div>
            </div>
            <div class="back-link">
                <a href="/" class="btn">← Back to Home</a>
                <a href="{{ url_for('bank_reply') }}" class="btn">💬 Reply to Customer</a>
            </div>
        </div>
        {% endblock %}
        ''', message=plaintext)
        
    except Exception as e:
        return render_template_string(BASE_TEMPLATE + '''
        {% block content %}
        <div class="header">
            <h1>📥 Read Customer Message</h1>
            <p>Bank Portal</p>
        </div>
        <div class="content">
            <div class="error-display">
                <h3>❌ Message Verification Failed</h3>
                <div class="message-content">{{ error }}</div>
            </div>
            <div class="back-link">
                <a href="/" class="btn">← Back to Home</a>
            </div>
        </div>
        {% endblock %}
        ''', error=str(e))

@app.route('/bank/reply', methods=['GET', 'POST'])
def bank_reply():
    if request.method == 'POST':
        if is_key_revoked('customer_public.pem'):
            flash('Customer key has been revoked. Cannot send message.', 'error')
        else:
            msg = request.form['message']
            bank_priv = load_key(KEYS_DIR / 'bank_private.pem')
            cust_pub = load_key(KEYS_DIR / 'customer_public.pem')
            message_payload = construct_secure_message(bank_priv, cust_pub, msg)
            MSG_DIR.joinpath('to_customer.json').write_text(json.dumps(message_payload, indent=2))
            flash('Reply successfully sent to customer!', 'success')
        return redirect(url_for('bank_reply'))
    
    return render_template_string(BASE_TEMPLATE + '''
    {% block content %}
    <div class="header">
        <h1>💬 Reply to Customer</h1>
        <p>Bank Portal</p>
    </div>
    <div class="content">
        {% with messages = get_flashed_messages(with_categories=true) %}
            {% if messages %}
                {% for category, message in messages %}
                    <div class="alert alert-{{ category }}">{{ message }}</div>
                {% endfor %}
            {% endif %}
        {% endwith %}
        
        <div class="form-container">
            <form method="post">
                <div class="form-group">
                    <label for="message">Your Reply:</label>
                    <textarea id="message" name="message" class="form-control" rows="6" 
                              placeholder="Enter your secure reply to the customer..." required></textarea>
                </div>
                <button type="submit" class="btn">🔒 Send Secure Reply</button>
                <a href="/" class="btn btn-secondary">← Back to Home</a>
            </form>
        </div>
    </div>
    {% endblock %}
    ''')

@app.route('/customer/read')
def customer_read():
    if is_key_revoked('bank_public.pem'):
        return render_template_string(BASE_TEMPLATE + '''
        {% block content %}
        <div class="header">
            <h1>📨 Read Bank Reply</h1>
            <p>Customer Portal</p>
        </div>
        <div class="content">
            <div class="error-display">
                <h3>⚠️ Access Denied</h3>
                <p>Bank key has been revoked. Cannot receive message.</p>
            </div>
            <div class="back-link">
                <a href="/" class="btn">← Back to Home</a>
            </div>
        </div>
        {% endblock %}
        ''')
    
    try:
        msg_data = load_json(MSG_DIR / 'to_customer.json')
        cust_priv = load_key(KEYS_DIR / 'customer_private.pem')
        bank_pub = load_key(KEYS_DIR / 'bank_public.pem')
        plaintext = decrypt_and_verify_message(cust_priv, bank_pub, msg_data)
        
        return render_template_string(BASE_TEMPLATE + '''
        {% block content %}
        <div class="header">
            <h1>📨 Bank Reply</h1>
            <p>Customer Portal</p>
        </div>
        <div class="content">
            <div class="message-display">
                <h3>✅ Reply Successfully Verified</h3>
                <div class="message-content">{{ message }}</div>
            </div>
            <div class="back-link">
                <a href="/" class="btn">← Back to Home</a>
                <a href="{{ url_for('customer_send') }}" class="btn">📤 Send New Message</a>
            </div>
        </div>
        {% endblock %}
        ''', message=plaintext)
        
    except Exception as e:
        return render_template_string(BASE_TEMPLATE + '''
        {% block content %}
        <div class="header">
            <h1>📨 Read Bank Reply</h1>
            <p>Customer Portal</p>
        </div>
        <div class="content">
            <div class="error-display">
                <h3>❌ Message Verification Failed</h3>
                <div class="message-content">{{ error }}</div>
            </div>
            <div class="back-link">
                <a href="/" class="btn">← Back to Home</a>
            </div>
        </div>
        {% endblock %}
        ''', error=str(e))

if __name__ == '__main__':
    app.run(debug=True)
