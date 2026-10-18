import tkinter as tk
from tkinter import ttk
import customtkinter as ctk

def _build_connect_tab(self, parent, devices):
    ctk.set_appearance_mode("dark")

    # Main layout frame with cyberpunk border
    main_frame = ctk.CTkFrame(
        parent, 
        fg_color="#0e1117",         
        corner_radius=4,            
        border_width=1,
        border_color="#00f0ff"      
    )
    main_frame.pack(fill="both", expand=True, padx=15, pady=15)

    # Terminal-style title header
    title = ctk.CTkLabel(
        main_frame, 
        text="[ CONNECTED_DEVICES // TELEMETRY ]", 
        font=("Consolas", 14, "bold"),
        text_color="#00f0ff"
    )
    title.pack(anchor="w", padx=10, pady=(15, 10))

    # Treeview Custom Style
    style = ttk.Style()
    style.theme_use("clam")
    
    style.configure(
        "Cyber.Treeview",
        background="#131722",
        foreground="#e0e0e0",
        fieldbackground="#131722",
        borderwidth=0,
        rowheight=28,
        font=("Consolas", 10)
    )
    style.configure(
        "Cyber.Treeview.Heading",
        background="#1f2430",
        foreground="#00f0ff",
        relief="flat",
        font=("Consolas", 11, "bold")
    )
    style.map(
        "Cyber.Treeview",
        background=[('selected', '#00f0ff')],
        foreground=[('selected', '#0e1117')]
    )

    # Treeview Container Frame
    tree_frame = ctk.CTkFrame(
        main_frame, 
        fg_color="#131722", 
        corner_radius=4,
        border_width=1,
        border_color="#1f2430"
    )
    tree_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))

    # Treeview Setup
    columns = ("Port", "Type", "Status", "Meta")
    self.tree = ttk.Treeview(
        tree_frame, 
        columns=columns, 
        show="headings", 
        style="Cyber.Treeview",
        selectmode="browse"
    )

    # Custom Scrollbar for Treeview
    scrollbar = ctk.CTkScrollbar(
        tree_frame, 
        orientation="vertical", 
        command=self.tree.yview,
        fg_color="#131722",
        button_color="#1f2430",
        button_hover_color="#00f0ff"
    )
    self.tree.configure(yscrollcommand=scrollbar.set)

    # tag onfig
    self.tree.tag_configure("disabled", foreground="#555555")
    self.tree.tag_configure("connected", background="#003b22", foreground="#00ff66")  # Matrix green tint
    self.tree.tag_configure("errored", background="#4a1515", foreground="#ff4d4d")    # Cyber red tint

    for col in columns:
        self.tree.heading(col, text=col, anchor="w")
        self.tree.column(col, width=130, anchor="w")

    # Filter out phantom/dead ports manually
    visible_devices = [d for d in devices if not d.is_unidentified()]

    # Populate the tree
    for _device in visible_devices:
        device = _device.to_dict()

        tags = []
        if device["status"].upper() == "IDENTIFYING...":
            tags.append("disabled")
        if _device.is_online():
            tags.append("connected")
        if getattr(_device, 'has_errored', False):
            tags.append("errored")

        new_item = self.tree.insert(
            "", "end",
            values=(device["port"], device["name"], device["status"], device["meta"]),
            tags=tuple(tags)
        )

        # Preserve selection across UI refreshes
        if hasattr(self, 'selected_device') and _device.get_port() == self.selected_device:
            self.tree.selection_add(new_item)

    self.tree.bind("<<TreeviewSelect>>", self.on_select)
    
    # Pack Treeview & Scrollbar inside container frame
    self.tree.pack(side="left", fill="both", expand=True, padx=5, pady=5)
    scrollbar.pack(side="right", fill="y", pady=5, padx=(0, 5))

    # stats
    stats_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
    stats_frame.pack(fill="x", padx=10, pady=(0, 10))

    online_count = sum(1 for d in visible_devices if d.is_online())

    self.total_label = ctk.CTkLabel(
        stats_frame, 
        text=f"> TOTAL_DEVICES: [ {len(visible_devices)} ]", 
        font=("Consolas", 11),
        text_color="#e0e0e0"
    )
    self.total_label.pack(side="left", padx=(0, 20))

    self.online_label = ctk.CTkLabel(
        stats_frame, 
        text=f"> ONLINE: [ {online_count} ]", 
        font=("Consolas", 11),
        text_color="#00ff66"
    )
    self.online_label.pack(side="left")

    # device status label
    self.device_label = ctk.CTkLabel(
        main_frame, 
        text="> STATUS: AWAITING_SELECTION...", 
        font=("Consolas", 11, "italic"),
        text_color="#00f0ff"
    )
    self.device_label.pack(anchor="w", padx=10, pady=(0, 15))