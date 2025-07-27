# Secure Bi-Directional Messaging System

This project implements a secure, bi-directional communication system between a customer and a bank using modern cryptographic techniques. It is written in Python and uses the `pycryptodome` library for cryptographic operations.

## Features
- **RSA Key Pair Generation** for both customer and bank
- **AES Encryption** for message confidentiality
- **RSA Encryption** for secure AES key exchange
- **Digital Signatures** for message authenticity and integrity
- **Replay Attack Protection** using nonces and timestamps
- **Key Revocation** support
- **Simple CLI Interface** for sending and receiving messages

## Project Structure
```
Crypto/
├── venv/                # (Your Python virtual environment)
├── main.py              # Main script for secure messaging
├── keys/                # Stores RSA key pairs and revoked keys list
│   ├── bank_private.pem
│   ├── bank_public.pem
│   ├── customer_private.pem
│   ├── customer_public.pem
│   └── revoked_keys.json
├── messages/            # Stores message payloads and used nonces
│   ├── to_bank.json
│   ├── to_customer.json
│   └── used_nonces.json
```

## Requirements
- Python 3.7+
- [pycryptodome](https://pypi.org/project/pycryptodome/)

## Installation
1. **Clone or download this repository.**
2. **Create a virtual environment (optional but recommended):**
   ```powershell
   python -m venv venv
   .\venv\Scripts\activate
   ```
3. **Install dependencies:**
   ```powershell
   pip install pycryptodome
   ```

## Usage
Run the main script from the project directory:
```powershell
python main.py
```

You will see a menu:
```
Secure Messaging CLI
1. Customer sends message to Bank
2. Bank reads message
3. Bank replies to Customer
4. Customer reads Bank reply
Enter option (1/2/3/4):
```

- **Option 1:** Customer composes and sends a secure message to the bank.
- **Option 2:** Bank reads and verifies the message from the customer.
- **Option 3:** Bank composes and sends a secure reply to the customer.
- **Option 4:** Customer reads and verifies the bank's reply.

All messages are securely encrypted, signed, and protected against replay attacks.

## How It Works
- **Key Generation:** On first run, RSA key pairs are generated for both parties and stored in the `keys/` directory.
- **Message Construction:**
  - A random AES key is generated for each message.
  - The message is encrypted with AES (EAX mode).
  - The AES key is encrypted with the recipient's RSA public key.
  - The ciphertext is signed with the sender's RSA private key.
  - A nonce and timestamp are included for replay protection.
- **Message Verification:**
  - The recipient decrypts the AES key with their private RSA key.
  - The message is decrypted with the AES key.
  - The signature is verified using the sender's public key.
  - The nonce and timestamp are checked to prevent replay attacks.
- **Key Revocation:**
  - Revoked keys are listed in `keys/revoked_keys.json`. If a key is revoked, messages cannot be sent or received with it.

## Security Notes
- All cryptographic operations use secure, modern algorithms (RSA 2048, AES-128 EAX, PKCS1_OAEP, SHA256).
- Nonces and timestamps are used to prevent replay attacks.
- Digital signatures ensure authenticity and integrity.
- Key revocation is supported for compromised keys.

## Customization
- You can adjust the `NONCE_EXPIRY` value in `main.py` to change the allowed message window (default: 60 seconds).
- To revoke a key, add its filename (e.g., `bank_public.pem`) to the `revoked` list in `keys/revoked_keys.json`.

## License
This project is for educational purposes. Use at your own risk.
