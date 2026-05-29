"""
File Sender - Handles sending files over network
"""

import socket
import os
import hashlib
import json
from network.security import perform_client_key_exchange, send_encrypted_message

def calculate_sha256(file_path):
    sha256 = hashlib.sha256()
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b''):
            sha256.update(chunk)
    return sha256.hexdigest()
class FileSender:
    def __init__(self):
        pass

    def send_file(self, file_path, host, port, dest_filename, progress_callback=None, auto_discover=True):
        """
        Send a file to a remote host
        
        Args:
            file_path: Path to the file to send
            host: Target host address (or 'auto' to use discovery)
            port: Target port number
            dest_filename: Filename to save as on receiver
            progress_callback: Function to call with progress updates (0-100)
            auto_discover: If True and host is 'auto', use UDP broadcast to find server
        """

        if not os.path.isfile(file_path):
            raise FileNotFoundError(f"File '{file_path}' does not exist.")

        file_size = os.path.getsize(file_path)

        # Auto-discover host if requested
        # if auto_discover and (host == 'auto' or not host or host.strip() == ''):
        #     host = discover_file_server_ip()

        # Create socket and connect to the server
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect((host, port))

        try:
            # Mandatory encrypted session
            aesgcm = perform_client_key_exchange(client)
            checksum = calculate_sha256(file_path)
            metadata = {
                "filename": dest_filename,
                "filesize": file_size,
                "checksum": checksum,
            }
            send_encrypted_message(client, aesgcm, json.dumps(metadata).encode())

            # Send file data
            with open(file_path, 'rb') as file:
                sent = 0
                while True:
                    data = file.read(64 * 1024)
                    if not data:
                        break
                    send_encrypted_message(client, aesgcm, data)
                    sent += len(data)

                    # Update progress if callback is provided
                    if progress_callback:
                        progress = (sent / file_size) * 100
                        progress_callback(progress)
            return {"encrypted": True, "checksum": checksum}
        
        finally:
            client.close()