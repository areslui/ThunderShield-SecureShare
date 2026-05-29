"""
File Receiver - Handles receiving files over network
"""

import socket
import threading
import os
import hashlib
import json
from utils.helpers import get_local_ip
from network.security import perform_server_key_exchange, recv_encrypted_message

def calculate_sha256(file_path):
    sha256 = hashlib.sha256()
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b''):
            sha256.update(chunk)
    return sha256.hexdigest()

class FileReceiver:
    def __init__(self):
        self.server_socket = None
        self.is_receiving = False
        self.log_callback = None  # Ensure attribute always exists
        self.ui_callback = None   # Ensure attribute always exists
        self.udp_discovery_thread = None
        self.udp_discovery_running = False

    def start_receiving(self, port, save_dir, log_callback=None, ui_callback=None):
        """
        Start the file receiver server
        
        Args:
            port: Port to listen on
            save_dir: Directory to save received files
            log_callback: Function to call with log messages
            ui_callback: Function to call for UI updates
        """

        if self.is_receiving:
            return

        self.save_dir = save_dir
        self.log_callback = log_callback
        self.ui_callback = ui_callback

        # Create a server socket
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind(("0.0.0.0", port))
        self.server_socket.listen()

        self.is_receiving = True

        if self.log_callback:
            self.log_callback(f"Server started on port {port}")
            self.log_callback("Waiting for incoming connections...")

        if self.ui_callback:
            self.ui_callback("server_started", f"Listening on port {port}")

        # Start a thread to accept incoming connections
        threading.Thread(target=self._receive_files_thread, daemon=True).start()

        # Start UDP discovery responder
        self.udp_discovery_running = True
        self.udp_discovery_thread = threading.Thread(target=self._udp_discovery_responder, args=(port,), daemon=True)
        self.udp_discovery_thread.start()

    def stop_receiving(self):
        """
        Stop the file receiver server
        """

        if self.server_socket:
            self.server_socket.close()
            self.server_socket = None
        
        self.is_receiving = False

        if self.log_callback:
            self.log_callback("Server stopped")

        if self.ui_callback:
            self.ui_callback("server_stopped", "No longer listening for connections")
        
        # Stop UDP discovery responder
        self.udp_discovery_running = False
        

    def _receive_files_thread(self):
        """
        Thread to handle incoming file transfers
        """

        while self.is_receiving:
            try:
                client, addr = self.server_socket.accept()
                if self.log_callback:
                    self.log_callback(f"Connection from {addr[0]}:{addr[1]}")

                # Handle client connection in a separate thread
                threading.Thread(target=self._handle_client, args=(client,), daemon=True).start()
            
            except Exception as e:
                if self.is_receiving:
                    if self.log_callback:
                        self.log_callback(f"Error accepting connection: {e}")
                break
    
    def _handle_client(self, client):
        """
        Handle file transfer from a connected client
        Args:
            client: Connected client socket
        """

        try:
            secure_session = perform_server_key_exchange(client)
            metadata = json.loads(recv_encrypted_message(client, secure_session).decode())
            filename = metadata["filename"]
            filesize = int(metadata["filesize"])
            expected_checksum = metadata["checksum"]

            if self.log_callback:
                self.log_callback(f"Receiving file '{filename}' ({filesize} bytes)")
                self.log_callback("🔐 Encrypted transfer active")

            # Create full path
            save_path = os.path.join(self.save_dir, filename)

            # Receive file data
            with open(save_path, "wb") as file:
                received = 0
                while received < filesize:
                    data = recv_encrypted_message(client, secure_session)
                    file.write(data)
                    received += len(data)

                    # Update progress if UI callback is provided
                    if self.log_callback:
                        progress = (received / filesize) * 100
                        if received == filesize or progress % 25 == 0:  # Log at 25% intervals
                            self.log_callback(f"Progress for {filename}: {progress:.1f}%")
            
            local_checksum = calculate_sha256(save_path)
            integrity_verified = expected_checksum == local_checksum
            if integrity_verified:
                if self.log_callback:
                    self.log_callback(f"✅ Verified SHA-256 for '{filename}'")
            else:
                if self.log_callback:
                    self.log_callback(f"❌ Integrity Failed for '{filename}'\nExpected: {expected_checksum}\nGot: {local_checksum}")

            if self.log_callback:
                encryption_status = "🔐 Encrypted"
                integrity_status = "✅ Verified" if integrity_verified else "❌ Integrity Failed"
                self.log_callback(f"File '{filename}' received successfully | {encryption_status} | {integrity_status}")
            if self.ui_callback:
                self.ui_callback("transfer_result", {
                    "filename": filename,
                    "encrypted": True,
                    "integrity_verified": integrity_verified,
                })
        
        except Exception as e:
            if self.log_callback:
                self.log_callback(f"Error receiving file: {str(e)}")

        finally:
            client.close()

    def _recv_line(self, sock):
        """"Receive a line of text from the socket"""

        line = b""
        while True:
            char = sock.recv(1)
            if char == b"\n" or char == b"":
                break
            line += char
        return line.decode()

    def _udp_discovery_responder(self, tcp_port, broadcast_port=9999):
        """
        Listen for UDP broadcast discovery messages and respond with the server's IP address.
        """
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            s.bind(("", broadcast_port)) # Listen on all ips and the specified broadcast port
            s.settimeout(1)
            while self.udp_discovery_running:
                try:
                    data, addr = s.recvfrom(1024)
                    if data == b"DISCOVER_FILE_SERVER" or data == b"DISCOVER_FILE_SERVERS":
                        # Respond with our IP address
                        ip = get_local_ip()
                        s.sendto(ip.encode(), addr)
                except socket.timeout:
                    continue
                except Exception:
                    break