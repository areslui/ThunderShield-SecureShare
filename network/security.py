import os
import struct

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import x25519
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.hkdf import HKDF


_PUBKEY_SIZE = 32
_NONCE_SIZE = 12


def _recv_exact(sock, size):
    data = b""
    while len(data) < size:
        chunk = sock.recv(size - len(data))
        if not chunk:
            raise ConnectionError("Connection closed unexpectedly")
        data += chunk
    return data


def _derive_session_key(shared_secret):
    hkdf = HKDF(
        algorithm=hashes.SHA256(),
        length=32,
        salt=None,
        info=b"thundershield-secureshare-session",
    )
    return hkdf.derive(shared_secret)


def perform_client_key_exchange(sock):
    private_key = x25519.X25519PrivateKey.generate()
    public_key_bytes = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )
    sock.sendall(public_key_bytes)
    peer_public_key_bytes = _recv_exact(sock, _PUBKEY_SIZE)
    shared_secret = private_key.exchange(
        x25519.X25519PublicKey.from_public_bytes(peer_public_key_bytes)
    )
    return AESGCM(_derive_session_key(shared_secret))


def perform_server_key_exchange(sock):
    peer_public_key_bytes = _recv_exact(sock, _PUBKEY_SIZE)
    private_key = x25519.X25519PrivateKey.generate()
    public_key_bytes = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )
    sock.sendall(public_key_bytes)
    shared_secret = private_key.exchange(
        x25519.X25519PublicKey.from_public_bytes(peer_public_key_bytes)
    )
    return AESGCM(_derive_session_key(shared_secret))


def send_encrypted_message(sock, aesgcm, plaintext):
    nonce = os.urandom(_NONCE_SIZE)
    ciphertext = aesgcm.encrypt(nonce, plaintext, None)
    sock.sendall(struct.pack("!I", len(ciphertext)))
    sock.sendall(nonce)
    sock.sendall(ciphertext)


def recv_encrypted_message(sock, aesgcm):
    ciphertext_size = struct.unpack("!I", _recv_exact(sock, 4))[0]
    nonce = _recv_exact(sock, _NONCE_SIZE)
    ciphertext = _recv_exact(sock, ciphertext_size)
    return aesgcm.decrypt(nonce, ciphertext, None)
