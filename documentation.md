# Secure Messaging System: Submission Documentation

## 1. System Architecture

### Overview
This system enables secure, bi-directional communication between a customer and a bank. It uses public key cryptography (RSA) for key exchange and digital signatures, and symmetric encryption (AES) for message confidentiality. The architecture is file-based for demonstration, with optional CLI and web interfaces.

**Components:**
- **Customer**: Sends secure messages to the bank and receives replies.
- **Bank**: Receives messages from the customer and sends replies.
- **Key Store**: Stores RSA key pairs for both parties.
- **Message Store**: Stores encrypted messages and nonces for replay protection.

**Data Flow:**
1. Customer/Bank generates RSA key pairs.
2. Customer encrypts a message for the bank, signs it, and stores it in a file.
3. Bank decrypts, verifies, and reads the message, then replies similarly.

---

## 2. Cryptographic Protocol Design

### Key Management
- **RSA 2048-bit** key pairs for both customer and bank.
- Keys are stored in PEM files in the `keys/` directory.
- Key revocation is supported via a `revoked_keys.json` file.

### Message Construction
- **AES-128 (EAX mode)** is used for encrypting the message body.
- The AES key is encrypted with the recipient's RSA public key (using OAEP).
- The ciphertext is signed with the sender's RSA private key (PKCS#1 v1.5, SHA-256).
- Each message includes a nonce and timestamp for replay protection.

### Message Verification
- The recipient decrypts the AES key with their private RSA key.
- The message is decrypted with the AES key.
- The signature is verified using the sender's public key.
- The nonce and timestamp are checked to prevent replay attacks.

---

## 3. How Security Goals Are Achieved

- **Confidentiality**: Messages are encrypted with AES; AES keys are encrypted with RSA.
- **Integrity**: Digital signatures ensure that messages are not tampered with.
- **Authentication**: Only holders of the correct private key can sign valid messages.
- **Replay Protection**: Nonces and timestamps prevent replay attacks.
- **Key Revocation**: Revoked keys are checked before any operation.

---

## 4. Limitations and Future Work

### Limitations
- File-based message and key storage is not suitable for production.
- No real user authentication or session management.
- No certificate authority (CA) or PKI integration in this version.
- No transport security (e.g., HTTPS) for the web interface.

### Future Work
- Integrate a CA for certificate-based trust.
- Move to a database or secure server for message/key storage.
- Add HTTPS and user authentication for the web interface.
- Support for more users and roles.
- Implement audit logging and monitoring.

---

## 5. Source Code

All source code is provided in this repository. The main implementation is in `main.py`. A web interface is available in `app.py` (Flask-based).

---

## 6. README: How to Run the Code

### Dependencies
- Python 3.7+
- [pycryptodome](https://pypi.org/project/pycryptodome/)
- [Flask](https://pypi.org/project/Flask/) (for web UI)

### Setup
```sh
# (Optional) Create and activate a virtual environment
python -m venv venv
.\venv\Scripts\activate  # On Windows

# Install dependencies
pip install pycryptodome flask
```

### Running the CLI
```sh
python main.py
```
Follow the menu prompts to send and receive messages.

### Running the Web UI
```sh
python app.py
```
Visit http://127.0.0.1:5000/ in your browser.

---

## 7. Example Message Exchange Walkthrough

1. **Customer sends message to Bank**
    - Customer enters a message.
    - Message is encrypted, signed, and stored as `messages/to_bank.json`.
2. **Bank reads message**
    - Bank decrypts and verifies the message.
    - Message is displayed if valid.
3. **Bank replies to Customer**
    - Bank enters a reply.
    - Reply is encrypted, signed, and stored as `messages/to_customer.json`.
4. **Customer reads Bank reply**
    - Customer decrypts and verifies the reply.
    - Reply is displayed if valid.

---

## 8. Submission Format

All files are to be submitted via a GitHub repository. Example structure:
```
Crypto/
├── main.py
├── app.py
├── keys/
├── messages/
├── README.md
├── documentation.md  # (this file)
└── ...
```

---

## 9. GitHub Repository Link

> Replace this with your actual repository URL before submission:
>
> https://github.com/your-username/secure-messaging-demo
