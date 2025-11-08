# secure_comm_enhanced.py
# Updated version: allows bi-directional secure communication between customer and bank

import os
import json
import base64
import time
from pathlib import Path
from Crypto.PublicKey import RSA
from Crypto.Cipher import AES, PKCS1_OAEP
from Crypto.Signature import pkcs1_15
from Crypto.Hash import SHA256
from Crypto.Random import get_random_bytes

# --- CONFIGURATION ---
KEYS_DIR = Path("keys")
MSG_DIR = Path("messages")
REVOKED_KEYS_FILE = KEYS_DIR / "revoked_keys.json"
USED_NONCES_FILE = MSG_DIR / "used_nonces.json"
NONCE_EXPIRY = 60  # seconds

# --- INITIAL SETUP ---
KEYS_DIR.mkdir(exist_ok=True)
MSG_DIR.mkdir(exist_ok=True)

# --- UTILITY FUNCTIONS ---
def b64e(data: bytes) -> str:
    return base64.b64encode(data).decode()

def b64d(data: str) -> bytes:
    return base64.b64decode(data)

def load_json(path):
    if not path.exists():
        return {}
    with open(path, 'r') as f:
        return json.load(f)

def save_json(path, data):
    with open(path, 'w') as f:
        json.dump(data, f, indent=2)

# --- KEY MANAGEMENT ---
def generate_rsa_keypair(name: str):
    key = RSA.generate(2048)
    private_key = key.export_key()
    public_key = key.publickey().export_key()
    (KEYS_DIR / f"{name}_private.pem").write_bytes(private_key)
    (KEYS_DIR / f"{name}_public.pem").write_bytes(public_key)
    return private_key, public_key

def load_key(path):
    return path.read_bytes()

def is_key_revoked(key_name: str):
    # revoked = load_json(REVOKED_KEYS_FILE).get("revoked", [])
    revoked = load_json(REVOKED_KEYS_FILE).get("revoked", ["customer_private.pem", "bank_private.pem"])
    return key_name in revoked

# --- CRYPTOGRAPHIC OPERATIONS ---
def encrypt_aes_key(pub_key_bytes, aes_key):
    pub_key = RSA.import_key(pub_key_bytes)
    cipher = PKCS1_OAEP.new(pub_key)
    return cipher.encrypt(aes_key)

def decrypt_aes_key(priv_key_bytes, enc_aes_key):
    priv_key = RSA.import_key(priv_key_bytes)
    cipher = PKCS1_OAEP.new(priv_key)
    return cipher.decrypt(enc_aes_key)

def encrypt_message(aes_key, plaintext):
    cipher = AES.new(aes_key, AES.MODE_EAX)
    ciphertext, tag = cipher.encrypt_and_digest(plaintext.encode())
    return cipher.nonce, ciphertext, tag

def decrypt_message(aes_key, nonce, ciphertext, tag):
    cipher = AES.new(aes_key, AES.MODE_EAX, nonce=nonce)
    return cipher.decrypt_and_verify(ciphertext, tag).decode()

def sign_data(private_key_bytes, message_bytes):
    key = RSA.import_key(private_key_bytes)
    h = SHA256.new(message_bytes)
    return pkcs1_15.new(key).sign(h)

def verify_signature(public_key_bytes, message_bytes, signature):
    key = RSA.import_key(public_key_bytes)
    h = SHA256.new(message_bytes)
    pkcs1_15.new(key).verify(h, signature)

# --- REPLAY PROTECTION ---
def check_and_store_nonce(nonce_str):
    store = load_json(USED_NONCES_FILE)
    now = int(time.time())
    store = {n: ts for n, ts in store.items() if now - ts <= NONCE_EXPIRY}
    if nonce_str in store:
        return False
    store[nonce_str] = now
    save_json(USED_NONCES_FILE, store)
    return True

# --- MESSAGE CONSTRUCTION ---
def construct_secure_message(sender_priv_key, recipient_pub_key, plaintext_msg):
    aes_key = get_random_bytes(16)
    enc_aes_key = encrypt_aes_key(recipient_pub_key, aes_key)
    nonce, ciphertext, tag = encrypt_message(aes_key, plaintext_msg)
    signature = sign_data(sender_priv_key, ciphertext)
    timestamp = int(time.time())

    return {
        "enc_aes_key": b64e(enc_aes_key),
        "nonce": b64e(nonce),
        "ciphertext": b64e(ciphertext),
        "tag": b64e(tag),
        "signature": b64e(signature),
        "timestamp": timestamp
    }

# --- MESSAGE VERIFICATION ---
def decrypt_and_verify_message(receiver_priv_key, sender_pub_key, message):
    enc_key = b64d(message["enc_aes_key"])
    nonce = b64d(message["nonce"])
    ciphertext = b64d(message["ciphertext"])
    tag = b64d(message["tag"])
    signature = b64d(message["signature"])
    timestamp = message["timestamp"]

    if abs(time.time() - timestamp) > NONCE_EXPIRY:
        raise Exception("Message timestamp expired.")

    if not check_and_store_nonce(b64e(nonce)):
        raise Exception("Replay attack detected (nonce reused).")

    verify_signature(sender_pub_key, ciphertext, signature)
    aes_key = decrypt_aes_key(receiver_priv_key, enc_key)
    return decrypt_message(aes_key, nonce, ciphertext, tag)

# --- MAIN CLI LOGIC ---
if __name__ == "__main__":
    import sys

    # Ensure keypairs exist
    if not (KEYS_DIR / "bank_private.pem").exists():
        generate_rsa_keypair("bank")
    if not (KEYS_DIR / "customer_private.pem").exists():
        generate_rsa_keypair("customer")

    # Load keys once
    bank_priv = load_key(KEYS_DIR / "bank_private.pem")
    bank_pub = load_key(KEYS_DIR / "bank_public.pem")
    cust_priv = load_key(KEYS_DIR / "customer_private.pem")
    cust_pub = load_key(KEYS_DIR / "customer_public.pem")

    # Main loop
    try:
        while True:
            print("\nSecure Messaging CLI")
            print("1. Customer sends message to Bank")
            print("2. Bank reads message")
            print("3. Bank replies to Customer")
            print("4. Customer reads Bank reply")
            print("5. Exit")
            choice = input("Enter option (1/2/3/4/5): ").strip()

            if choice == "1":
                if is_key_revoked("bank_private.pem"):
                    print("Bank key revoked. Cannot send message.")
                else:
                    msg = input("Enter message to send to Bank: ")
                    message_payload = construct_secure_message(cust_priv, bank_pub, msg)
                    MSG_DIR.joinpath("to_bank.json").write_text(json.dumps(message_payload, indent=2))
                    print("[Customer] Message sent to bank.")

            elif choice == "2":
                if is_key_revoked("customer_private.pem"):
                    print("Customer key revoked. Cannot receive message.")
                else:
                    msg_data = load_json(MSG_DIR / "to_bank.json")
                    if not msg_data:
                        print("[Bank] No message found for Bank to read.")
                        continue
                    try:
                        plaintext = decrypt_and_verify_message(bank_priv, cust_pub, msg_data)
                        print(f"[Bank] Received message: {plaintext}")
                    except Exception as e:
                        print(f"[Bank] Message rejected: {e}")

            elif choice == "3":
                if is_key_revoked("customer_public.pem"):
                    print("Customer key revoked. Cannot send message.")
                else:
                    msg = input("Enter message to send to Customer: ")
                    message_payload = construct_secure_message(bank_priv, cust_pub, msg)
                    MSG_DIR.joinpath("to_customer.json").write_text(json.dumps(message_payload, indent=2))
                    print("[Bank] Reply sent to customer.")

            elif choice == "4":
                if is_key_revoked("bank_public.pem"):
                    print("Bank key revoked. Cannot receive message.")
                else:
                    msg_data = load_json(MSG_DIR / "to_customer.json")
                    if not msg_data:
                        print("[Customer] No reply found from Bank.")
                        continue
                    try:
                        plaintext = decrypt_and_verify_message(cust_priv, bank_pub, msg_data)
                        print(f"[Customer] Received reply from Bank: {plaintext}")
                    except Exception as e:
                        print(f"[Customer] Message rejected: {e}")

            elif choice == "5":
                print("Exiting Secure Messaging CLI.")
                break

            else:
                print("Invalid choice. Please select 1-5.")

    except KeyboardInterrupt:
        print("\nInterrupted. Exiting.")
