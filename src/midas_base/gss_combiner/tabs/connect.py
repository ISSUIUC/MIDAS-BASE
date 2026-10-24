import tkinter as tk
from tkinter import ttk
import customtkinter as ctk

def _build_connect_tab(self, parent, devices):
    colors = self.theme_colors
    main_frame = ttk.Frame(parent)
    main_frame.pack(fill="both", expand=True, padx=22, pady=20)

    list_frame = ttk.Frame(main_frame)
    list_frame.pack(side="left", fill="both", expand=True, padx=(0, 20))

    header = ttk.Frame(list_frame)
    header.pack(fill="x", pady=(0, 12))
    ttk.Label(header, text="DEVICE DISCOVERY", style="Title.TLabel").pack(anchor="w")
    ttk.Label(
        header,
        text="Select a detected board to configure its connection.",
        style="Muted.TLabel",
    ).pack(anchor="w", pady=(4, 0))

    columns = ("Device Port", "Type", "Status", "Streaming to", "Meta")
    self.tree = ttk.Treeview(list_frame, columns=columns, show="headings")
    
    for col in columns:
        self.tree.heading(col, text=col)
        self.tree.column(col, width=130, anchor="w")
    self.tree.column("Device Port", width=110)
    self.tree.column("Status", width=115)

    for _device in devices:
        device = _device.to_dict()

        tags = ("disabled",) if device["status"].upper() == "NONE" or device["status"].upper() == "IDENTIFYING..." else ()
        self.tree.insert("", "end", values=(device["port"], device["name"], device["status"], device["server"], device["meta"]), tags=tags)

    self.tree.bind("<<TreeviewSelect>>", self.on_select)
    self.tree.pack(fill="both", expand=True)

    # Keep these states local to the device list.
    self.tree.tag_configure("disabled", foreground=colors["muted"])
    self.tree.tag_configure("connected", background="#12352F", foreground=colors["success"])
    self.tree.tag_configure("errored", background="#3A202A", foreground=colors["error"])

    control_frame = ttk.Frame(main_frame)
    control_frame.pack(side="right", fill="y", padx=(0, 2), pady=2)
    control_frame.configure(width=310)
    control_frame.pack_propagate(False)

    ttk.Label(control_frame, text="CONNECTION CONTROL", style="Title.TLabel").pack(anchor="w", pady=(0, 14))
    selection_card = ttk.LabelFrame(control_frame, text="SELECTED DEVICE", padding=(14, 12))
    selection_card.pack(fill="x", pady=(0, 12))
    self.device_label = ttk.Label(
        selection_card,
        text="No device selected",
        style="Section.TLabel",
        wraplength=250,
    )
    self.device_label.pack(anchor="w")

    self.stage_sel = tk.StringVar(value="sustainer")  # Default selected value
    stage_card = ttk.LabelFrame(control_frame, text="FLIGHT STAGE", padding=(12, 10))
    stage_card.pack(fill="x", pady=(0, 12))
    ttk.Label(
        stage_card,
        text="Choose the stage used for this connection.",
        style="Muted.TLabel",
        wraplength=260,
    ).pack(anchor="w", pady=(0, 8))
    stage_options = ttk.Frame(stage_card)
    stage_options.pack(fill="x")

    self.radio1 = ttk.Radiobutton(stage_options, text="Sustainer", variable=self.stage_sel, value="sustainer")
    self.radio1.pack(side="left", expand=True, anchor="w")
    self.radio2 = ttk.Radiobutton(stage_options, text="Booster", variable=self.stage_sel, value="booster")
    self.radio2.pack(side="left", expand=True, anchor="w")
    self.radio3 = ttk.Radiobutton(stage_options, text="Duo", variable=self.stage_sel, value="duo")
    self.radio3.pack(side="left", expand=True, anchor="w")

    self.do_log = tk.BooleanVar(value=True)
    self.do_log_checkbox = ttk.Checkbutton(stage_card, text="Save connection log", variable=self.do_log)
    self.do_log_checkbox.pack(anchor="w", pady=(8, 0))

    self.radio1.config(state="disabled")
    self.radio2.config(state="disabled")
    self.radio3.config(state="disabled")
    self.do_log_checkbox.config(state="disabled")
    network_card = ttk.LabelFrame(control_frame, text="GROUND STATION", padding=(12, 10))
    network_card.pack(fill="x", pady=(0, 12))
    ttk.Label(network_card, text="HOST / IP ADDRESS", style="Section.TLabel").pack(anchor="w", pady=(0, 5))
    self.ip_entry = ttk.Entry(network_card)
    self.ip_entry.pack(fill="x", pady=(0, 10))

    self.connect_btn = ttk.Button(
        network_card,
        text="CONNECT TO DEVICE",
        style="Accent.TButton",
        command=self.perform_action,
        state="normal",
    )
    self.connect_btn.pack(fill="x", pady=(0, 6))
    self.inspect_btn = ttk.Button(
        network_card,
        text="OPEN DEVICE CONSOLE",
        command=self.inspect_window,
        state="disabled",
    )
    self.inspect_btn.pack(fill="x")

    system_card = ttk.LabelFrame(control_frame, text="SYSTEM STATUS", padding=(12, 10))
    system_card.pack(fill="x")
    self.total_label = ttk.Label(system_card, text=f"DETECTED  //  {len(devices)}", style="Muted.TLabel")
    self.total_label.pack(anchor="w")

    online_count = sum(1 for d in devices if d.to_dict()["status"].lower() == "online")
    self.online_label = ttk.Label(system_card, text=f"ONLINE  //  {online_count}", style="Success.TLabel")
    self.online_label.pack(anchor="w", pady=(6, 0))

    def deselect(event=None):
        self.selected_device = None
        self.tree.selection_remove(self.tree.selection())
        self.device_label.config(text="Select a device")
        self.radio1.config(state="disabled")
        self.radio2.config(state="disabled")
        self.radio3.config(state="disabled")
        self.inspect_btn.config(state="disabled")
        self.connect_btn.config(state="disabled")
        self.do_log_checkbox.config(state="disabled")
    self.bind("<Escape>", deselect)
    # # Main layout frame with cyberpunk border
    # main_frame = ctk.CTkFrame(
    #     parent, 
    #     fg_color="#0e1117",         
    #     corner_radius=4,            
    #     border_width=1,
    #     border_color="#00f0ff"      
    # )
    # main_frame.pack(fill="both", expand=True, padx=15, pady=15)

    # # Terminal-style title header
    # title = ctk.CTkLabel(
    #     main_frame, 
    #     text="[ CONNECTED_DEVICES // TELEMETRY ]", 
    #     font=("Consolas", 14, "bold"),
    #     text_color="#00f0ff"
    # )
    # title.pack(anchor="w", padx=10, pady=(15, 10))

    # self.connect_btn = ttk.Button(main_frame, text="Connect", command=self.perform_action)
    # self.connect_btn.pack(side=tk.RIGHT, anchor=tk.NE, padx=20, pady=20)
    # label = ttk.Label(main_frame, text="GSS IP:")
    # label.pack(pady=5)
    # self.ip_entry = ttk.Entry(main_frame)
    # self.ip_entry.config()
    # self.ip_entry.pack(pady=5)

    # # if _device.is_online():
    # #     dev_ip, dev_sl = _device.get_stat()
    # #     self.do_log.set(dev_sl)
    # #     self.ip_entry.delete(0, tk.END) # Clear existing content
    # #     self.ip_entry.insert(0, dev_ip)
    # #     self.stage_sel.set(_device.stage_sel)

    # # Treeview Custom Style
    # style = ttk.Style()
    # style.theme_use("clam")
    
    # style.configure(
    #     "Cyber.Treeview",
    #     background="#131722",
    #     foreground="#e0e0e0",
    #     fieldbackground="#131722",
    #     borderwidth=0,
    #     rowheight=28,
    #     font=("Consolas", 10)
    # )
    # style.configure(
    #     "Cyber.Treeview.Heading",
    #     background="#1f2430",
    #     foreground="#00f0ff",
    #     relief="flat",
    #     font=("Consolas", 11, "bold")
    # )
    # style.map(
    #     "Cyber.Treeview",
    #     background=[('selected', '#00f0ff')],
    #     foreground=[('selected', '#0e1117')]
    # )

    # # Treeview Container Frame
    # tree_frame = ctk.CTkFrame(
    #     main_frame, 
    #     fg_color="#131722", 
    #     corner_radius=4,
    #     border_width=1,
    #     border_color="#1f2430"
    # )
    # tree_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))

    # # Treeview Setup
    # columns = ("Port", "Type", "Status", "Meta")
    # self.tree = ttk.Treeview(
    #     tree_frame, 
    #     columns=columns, 
    #     show="headings", 
    #     style="Cyber.Treeview",
    #     selectmode="browse"
    # )

    # # Custom Scrollbar for Treeview
    # scrollbar = ctk.CTkScrollbar(
    #     tree_frame, 
    #     orientation="vertical", 
    #     command=self.tree.yview,
    #     fg_color="#131722",
    #     button_color="#1f2430",
    #     button_hover_color="#00f0ff"
    # )
    # self.tree.configure(yscrollcommand=scrollbar.set)

    # # tag onfig
    # self.tree.tag_configure("disabled", foreground="#555555")
    # self.tree.tag_configure("connected", background="#003b22", foreground="#00ff66")  # Matrix green tint
    # self.tree.tag_configure("errored", background="#4a1515", foreground="#ff4d4d")    # Cyber red tint

    # for col in columns:
    #     self.tree.heading(col, text=col, anchor="w")
    #     self.tree.column(col, width=130, anchor="w")

    # # Filter out phantom/dead ports manually
    # visible_devices = [d for d in devices if not d.is_unidentified()]

    # # Populate the tree
    # for _device in visible_devices:
    #     device = _device.to_dict()

    #     tags = []
    #     if device["status"].upper() == "IDENTIFYING...":
    #         tags.append("disabled")
    #     if _device.is_online():
    #         tags.append("connected")
    #     if getattr(_device, 'has_errored', False):
    #         tags.append("errored")

    #     new_item = self.tree.insert(
    #         "", "end",
    #         values=(device["port"], device["name"], device["status"], device["meta"]),
    #         tags=tuple(tags)
    #     )

    #     # Preserve selection across UI refreshes
    #     if hasattr(self, 'selected_device') and _device.get_port() == self.selected_device:
    #         self.tree.selection_add(new_item)

    # self.tree.bind("<<TreeviewSelect>>", self.on_select)
    
    # # Pack Treeview & Scrollbar inside container frame
    # self.tree.pack(side="left", fill="both", expand=True, padx=5, pady=5)
    # scrollbar.pack(side="right", fill="y", pady=5, padx=(0, 5))

    # # stats
    # stats_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
    # stats_frame.pack(fill="x", padx=10, pady=(0, 10))

    # online_count = sum(1 for d in visible_devices if d.is_online())

    # self.total_label = ctk.CTkLabel(
    #     stats_frame, 
    #     text=f"> TOTAL_DEVICES: [ {len(visible_devices)} ]", 
    #     font=("Consolas", 11),
    #     text_color="#e0e0e0"
    # )
    # self.total_label.pack(side="left", padx=(0, 20))

    # self.online_label = ctk.CTkLabel(
    #     stats_frame, 
    #     text=f"> ONLINE: [ {online_count} ]", 
    #     font=("Consolas", 11),
    #     text_color="#00ff66"
    # )
    # self.online_label.pack(side="left")

    # # device status label
    # self.device_label = ctk.CTkLabel(
    #     main_frame, 
    #     text="> STATUS: AWAITING_SELECTION...", 
    #     font=("Consolas", 11, "italic"),
    #     text_color="#00f0ff"
    # )
    # self.device_label.pack(anchor="w", padx=10, pady=(0, 15))