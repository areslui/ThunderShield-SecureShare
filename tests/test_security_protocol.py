import os
import socket
import tempfile
import threading
import time
import unittest

from network.receiver import FileReceiver
from network.security import (
    perform_client_key_exchange,
    perform_server_key_exchange,
    send_encrypted_message,
    recv_encrypted_message,
)
from network.sender import FileSender


def _find_free_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


class SecurityProtocolTests(unittest.TestCase):
    def test_encrypted_message_exchange_after_key_negotiation(self):
        client_sock, server_sock = socket.socketpair()
        received = {}

        def server_worker():
            secure_session = perform_server_key_exchange(server_sock)
            received["payload"] = recv_encrypted_message(server_sock, secure_session)
            server_sock.close()

        thread = threading.Thread(target=server_worker)
        thread.start()

        secure_session = perform_client_key_exchange(client_sock)
        send_encrypted_message(client_sock, secure_session, b"thundershield")
        client_sock.close()
        thread.join(timeout=5)
        self.assertFalse(thread.is_alive(), "Server thread did not complete in time")

        self.assertEqual(received.get("payload"), b"thundershield")

    def test_sender_and_receiver_report_encrypted_verified_transfer(self):
        logs = []
        ui_events = []

        with tempfile.TemporaryDirectory() as tmp_dir:
            source_path = os.path.join(tmp_dir, "source.txt")
            with open(source_path, "wb") as source_file:
                source_file.write(b"secure transfer payload")

            receiver = FileReceiver()
            port = _find_free_port()
            receiver.start_receiving(
                port,
                tmp_dir,
                log_callback=logs.append,
                ui_callback=lambda action, state: ui_events.append((action, state)),
            )
            self.addCleanup(receiver.stop_receiving)

            sender = FileSender()
            sender.send_file(source_path, "127.0.0.1", port, "received.txt")

            for _ in range(20):
                if os.path.exists(os.path.join(tmp_dir, "received.txt")):
                    break
                time.sleep(0.1)

            self.assertTrue(os.path.exists(os.path.join(tmp_dir, "received.txt")))

            receiver.stop_receiving()

            with open(os.path.join(tmp_dir, "received.txt"), "rb") as received_file:
                self.assertEqual(received_file.read(), b"secure transfer payload")

        self.assertTrue(any("🔐 Encrypted transfer active" in log for log in logs))
        transfer_events = [event for event in ui_events if event[0] == "transfer_result"]
        self.assertTrue(transfer_events)
        self.assertTrue(transfer_events[-1][1]["encrypted"])
        self.assertTrue(transfer_events[-1][1]["integrity_verified"])


if __name__ == "__main__":
    unittest.main()
