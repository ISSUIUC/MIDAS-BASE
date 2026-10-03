import tkinter as tk
from tkinter import ttk

class DeviceConsoleFrame(ttk.Frame):
    """A reusable terminal UI for a specific connected FeatherSubprocess."""
    def __init__(self, parent, device):
        super().__init__(parent)
        self.device = device
        self.port_name = device.get_port()

        # ── Output Area (Text Widget) ──
        self.output_text = tk.Text(
            self, state="disabled", wrap="word",
            bg="#000000", fg="#ffffff", font=("Courier", 10),
            insertbackground="lime"
        )
        self.output_text.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Configure the specific color tags requested by the lead
        self.output_text.tag_config("user_in", foreground="#00FF00") # Bright green
        self.output_text.tag_config("raw_out", foreground="light sky blue")

        # Scrollbar for output
        scrollbar = ttk.Scrollbar(self.output_text, command=self.output_text.yview)
        self.output_text.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")

        # ── Input Area ──
        input_frame = ttk.Frame(self)
        input_frame.pack(fill="x", padx=5, pady=5)

        ttk.Label(input_frame, text=">").pack(side="left")

        self.input_entry = ttk.Entry(input_frame, font=("Courier", 10))
        self.input_entry.pack(side="left", fill="x", expand=True, padx=(5, 5))
        self.input_entry.bind("<Return>", self._on_submit)

        clear_btn = ttk.Button(input_frame, text="Clear", command=self._clear_console)
        clear_btn.pack(side="right", padx=(0, 5))

        send_btn = ttk.Button(input_frame, text="Send", command=self._on_submit)
        send_btn.pack(side="right")

        self.show_data_var = tk.BooleanVar(value=False) # Defaults to showing data
        self.data_filter_btn = ttk.Checkbutton(
            input_frame, 
            text="Show MIDAS Data", 
            variable=self.show_data_var
        )
        self.data_filter_btn.pack(side="right", padx=10)

        # ── Hook into FeatherSubprocess ──
        self.device.set_terminal_output(self.output_text)

        # ── Load existing history with formatting ──
        self.output_text.configure(state="normal")
        self.output_text.insert("end", "<BEGINNING OF LOG>\n")
        
        for msg in self.device.main_stdout:
            # Apply formatting tags based on the message prefix
            if msg.startswith("[F]"):
                self.output_text.insert("end", f"{msg}\n", "raw_out")
            elif msg.startswith(">> "):
                self.output_text.insert("end", f"{msg}\n", "user_in")
            else:
                self.output_text.insert("end", f"{msg}\n")
                
        self.output_text.configure(state="disabled")
        self.output_text.see("end")
        
        # ── Start Reading Hardware Data ──
        self._poll_serial()

    def _clear_console(self):
        """Clears the visual terminal and the underlying stdout history."""
        # Unlock the text widget, delete everything from line 1 character 0 to the end
        self.output_text.configure(state="normal")
        self.output_text.delete("1.0", tk.END)
        
        # Add the beginning log header back in and lock the widget
        self.output_text.insert("end", "<BEGINNING OF LOG>\n")
        self.output_text.configure(state="disabled")
        
        # Clear the backend history list
        self.device.main_stdout.clear()

    def _on_submit(self, event=None):
        """Triggered when user presses Enter or clicks Send."""
        cmd = self.input_entry.get().strip() 
        if cmd:
            self.input_entry.delete(0, tk.END)
            
            # Echo our command to the screen visually
            self.output_text.configure(state="normal")
            self.output_text.insert("end", f">> {cmd}\n", "user_in")
            self.output_text.configure(state="disabled")
            self.output_text.see("end")
            
            # Send the shell command to the hardware WITH carriage return
            command_bytes = f"{cmd}\r\n".encode('utf-8')
            
            try:
                self.device.send_serial_msg(command_bytes)
            except Exception as e:
                self.output_text.configure(state="normal")
                self.output_text.insert("end", f"[ERROR] Failed to send: {e}\n")
                self.output_text.configure(state="disabled")

    def _poll_serial(self):
        """Continuously check the board for new messages and print them."""
        try:
            incoming_lines = self.device.read_serial_lines()
            for line in incoming_lines:
                if line:  # Ignore empty strings
                    if not self.show_data_var.get() and '{"type": "data"' in line:
                        continue
                    self.device.add_to_stdout(line)
        except Exception:
            pass # Ignore read errors
            
        # Check again in 100 milliseconds
        self.after(100, self._poll_serial)


def _build_consoles_tab(self, parent, get_devices_callback):
    """Builds the dynamic Consoles tab."""
    container = ttk.Frame(parent)
    container.pack(fill="both", expand=True, padx=10, pady=10)

    # ── Top selector ──
    selector_frame = ttk.Frame(container)
    selector_frame.pack(fill="x", pady=(0, 10))

    ttk.Label(selector_frame, text="Connected Device:", font=("Helvetica", 12)).pack(side="left")

    self.selected_device_display = tk.StringVar()
    
    device_dropdown = ttk.Combobox(
        selector_frame,
        textvariable=self.selected_device_display,
        state="readonly",
        width=35
    )
    device_dropdown.pack(side="left", padx=10)

    # ── View container (stacked frames) ──
    self.console_views = {}
    self.display_to_port = {}  # Maps "MIDAS MINI (COM3)" -> "COM3"
    
    view_container = ttk.Frame(container)
    view_container.pack(fill="both", expand=True)

    def switch_view(*args):
        selected_display = self.selected_device_display.get()
        port = self.display_to_port.get(selected_display)
        if port and port in self.console_views:
            self.console_views[port].lift()

    device_dropdown.bind("<<ComboboxSelected>>", switch_view)

    # ── Dynamic Update Loop ──
    def update_dropdown():
        current_ports = []
        valid_devices = {}
        display_names = []
        new_display_to_port = {}
        
        # 1. Fetch the absolute newest list using the callback
        source_devices = get_devices_callback()
            
        # 2. Extract ready devices
        if source_devices is not None:
            for device in source_devices:
                stat = device.stat.upper()
                port = device.get_port()
                
                if stat not in ("NONE", "IDENTIFYING..."):
                    current_ports.append(port)
                    valid_devices[port] = device
                    
                    device_name = device.to_dict().get("name", "UNKNOWN")
                    display_str = f"{device_name} ({port})"
                    
                    display_names.append(display_str)
                    new_display_to_port[display_str] = port

        self.display_to_port = new_display_to_port

        # 3. Create consoles for NEW devices
        for port in current_ports:
            if port not in self.console_views:
                frame = DeviceConsoleFrame(view_container, valid_devices[port])
                frame.place(relx=0, rely=0, relwidth=1, relheight=1)
                self.console_views[port] = frame

        # 4. Remove consoles for DISCONNECTED devices
        disconnected = [p for p in list(self.console_views.keys()) if p not in current_ports]
        for port in disconnected:
            self.console_views[port].destroy()
            del self.console_views[port]

        # 5. Update the Combobox values
        device_dropdown['values'] = display_names

        # 6. Handle selection fallback
        current_selection = self.selected_device_display.get()
        if current_selection not in display_names:
            if display_names:
                self.selected_device_display.set(display_names[0])
                switch_view()
            else:
                self.selected_device_display.set("")
                for frame in self.console_views.values():
                    frame.place_forget()

        parent.after(2000, update_dropdown)

    update_dropdown()
    return container

