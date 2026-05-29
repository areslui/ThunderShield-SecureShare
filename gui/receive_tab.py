"""
Receive File Tab - UI for receiving files
"""

import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog, messagebox
import os
import time
from network.receiver import FileReceiver

class ReceiveTab:
    pass
    def __init__(self, parent, root):
        self.parent = parent
        self.root = root
        self.receiver = FileReceiver()

        self.setup_ui()

    def setup_ui(self):
        # Server section
        server_section = ctk.CTkFrame(self.parent)
        server_section.pack(fill="x", padx=20, pady=20)

        ctk.CTkLabel(
            server_section,
            text="Server Settings",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(pady=(15, 10))

        # Port input for receiver
        port_frame = ctk.CTkFrame(server_section)
        port_frame.pack(fill="x", padx=20, pady=10)

        ctk.CTkLabel(port_frame, text="Listen on Port:").pack(side="left", padx=(10, 5))
        self.receive_port_entry = ctk.CTkEntry(port_frame, placeholder_text="9999", width=100)
        self.receive_port_entry.pack(side="left", padx=5)
        self.receive_port_entry.insert(0, "9999")

        # Download directory
        dir_frame = ctk.CTkFrame(server_section)
        dir_frame.pack(fill="x", padx=20, pady=10)

        ctk.CTkLabel(dir_frame, text="Save to:").pack(side="left", padx=(10, 5))
        self.save_dir_var = tk.StringVar(value=os.getcwd())
        self.save_dir_label = ctk.CTkLabel(
            dir_frame,
            textvariable=self.save_dir_var,
            wraplength=300,
        )
        self.save_dir_label.pack(side="left", padx=5, fill="x", expand=True)

        browse_dir_button = ctk.CTkButton(
            dir_frame,
            text="Browse",
            command=self.browse_directory,
            width=80
        )
        browse_dir_button.pack(side="right", padx=5)

        # Control buttons
        button_frame = ctk.CTkFrame(server_section)
        button_frame.pack(fill="x", padx=20, pady=(10, 5))

        self.start_server_button = ctk.CTkButton(
            button_frame,
            text="Start Receiving",
            command=self.start_receiving,
            height=35
        )
        self.start_server_button.pack(side="left", padx=(10, 5), fill="x", expand=True)

        self.stop_server_button = ctk.CTkButton(
            button_frame,
            text="Stop Receiving",
            command=self.stop_receiving,
            height=35,
            state="disabled"
        )
        self.stop_server_button.pack(side="right", padx=(5, 10), fill="x", expand=True)

        # Status section
        status_section = ctk.CTkFrame(self.parent)
        status_section.pack(fill="both", padx=20, pady=10, expand=True)

        ctk.CTkLabel(
            status_section,
            text="Status",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(pady=(10, 5))

        # Status text box
        self.status_textbox = ctk.CTkTextbox(status_section, height=150)
        self.status_textbox.pack(fill="both", padx=10, pady=(5, 10), expand=True)
        self.log_message("Ready to receive files...")
    
    def browse_directory(self):
        selected_dir = filedialog.askdirectory(title="Select download directory")
        if selected_dir:
            self.save_dir_var.set(selected_dir)
    
    def start_receiving(self):
        if self.receiver.is_receiving:
            return

        port = int(self.receive_port_entry.get() or "9999")
        save_dir = self.save_dir_var.get()

        try:
            # Setup callbacks
            def log_callback(message):
                self.root.after(0, lambda m=message: self.log_message(m))
            
            def ui_callback(action, state=None):
                if action == "server_started":
                    self.root.after(0, lambda: self.start_server_button.configure(state="disabled"))
                    self.root.after(0, lambda: self.stop_server_button.configure(state="normal"))

                elif action == "server_stopped":
                    self.root.after(0, lambda: self.start_server_button.configure(state="normal"))
                    self.root.after(0, lambda: self.stop_server_button.configure(state="disabled"))
                elif action == "transfer_result" and isinstance(state, dict):
                    encryption_status = "🔐 Encrypted" if state.get("encrypted") else "⚠️ Unencrypted"
                    integrity_status = "✅ Verified" if state.get("integrity_verified") else "❌ Integrity Failed"
                    filename = state.get("filename", "unknown")
                    self.root.after(0, lambda: self.log_message(
                        f"Transfer Result - {filename}: {encryption_status} | {integrity_status}"
                    ))
            
            # Start receiver
            self.receiver.start_receiving(
                port,
                save_dir,
                log_callback,
                ui_callback
            )

        except Exception as e:
            messagebox.showerror("Error", f"Failed to start receiving: {e}")
            return
    
    def stop_receiving(self):
        self.receiver.stop_receiving()

    def log_message(self, message):
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        self.status_textbox.insert("end", f"[{timestamp}] {message}\n")
        self.status_textbox.see("end")