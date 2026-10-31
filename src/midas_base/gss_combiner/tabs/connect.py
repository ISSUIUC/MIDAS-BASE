import tkinter as tk
from tkinter import ttk
import customtkinter as ctk

def _build_connect_tab(self, parent, devices):

    # Main layout
    main_frame = ttk.Frame(parent)
    main_frame.pack(fill="both", expand=True, padx=10, pady=10)

    # Left side: device list
    list_frame = ttk.Frame(main_frame)
    list_frame.pack(side="left", fill="both", expand=True)

    title = ttk.Label(list_frame, text="COM List", font=("Helvetica", 14))
    title.pack(pady=5)

    columns = ("Device Port", "Type", "Status", "Streaming to", "Meta")
    self.tree = ttk.Treeview(list_frame, columns=columns, show="headings")
    self.tree.tag_configure("disabled", foreground="gray")
    
    for col in columns:
        self.tree.heading(col, text=col)
        self.tree.column(col, width=120)

    for _device in devices:
        device = _device.to_dict()

        tags = ("disabled",) if device["status"].upper() == "NONE" or device["status"].upper() == "IDENTIFYING..." else ()
        self.tree.insert("", "end", values=(device["port"], device["name"], device["status"], device["server"], device["meta"]), tags=tags)

    self.tree.bind("<<TreeviewSelect>>", self.on_select)
    self.tree.pack(fill="both", expand=True)

    self.tree.tag_configure("connected", background="#d2ffd2")
    self.tree.tag_configure("errored", background="#ffd2d2")

    # Right side: control panel
    control_frame = ttk.Frame(main_frame)
    control_frame.pack(side="right", fill="y", padx=10, pady=5)

    control_title = ttk.Label(control_frame, text="Input", font=("Helvetica", 14))
    control_title.pack(pady=5)

    self.device_label = ttk.Label(control_frame, text="Select a device")
    self.device_label.pack(pady=5)

    self.stage_sel = tk.StringVar(value="sustainer")  # Default selected value

    radio_label = ttk.Label(control_frame, text="Stage Select:")
    radio_label.pack(pady=5)

    self.radio1 = ttk.Radiobutton(control_frame, text="Sustainer", variable=self.stage_sel, value="sustainer")
    self.radio1.pack()

    self.radio2 = ttk.Radiobutton(control_frame, text="Booster", variable=self.stage_sel, value="booster")
    self.radio2.pack()

    self.radio3 = ttk.Radiobutton(control_frame, text="Duo", variable=self.stage_sel, value="duo")
    self.radio3.pack()

    self.do_log = tk.BooleanVar(value=True)

    self.do_log_checkbox = ttk.Checkbutton(control_frame, text="Generate Log File", variable=self.do_log)
    self.do_log_checkbox.pack(pady=(0, 5))


    self.radio1.config(state="disabled")
    self.radio2.config(state="disabled")
    self.radio3.config(state="disabled")
    self.do_log_checkbox.config(state="disabled")
    # Separator
    ttk.Separator(control_frame, orient="horizontal").pack(fill="x", pady=15)

    stats_title = ttk.Label(control_frame, text="Network", font=("Helvetica", 12, "underline"))
    stats_title.pack(pady=(0, 5))

    label = ttk.Label(control_frame, text="GSS IP:")
    label.pack(pady=5)

    self.ip_entry = tk.Entry(control_frame)
    self.ip_entry.pack(pady=5)

    self.connect_btn = ttk.Button(control_frame, text="Connect", command=self.perform_action, state="normal")
    self.connect_btn.pack(pady=2)

    self.inspect_btn = ttk.Button(control_frame, text="Console", command=self.inspect_window, state="disabled")
    self.inspect_btn.pack(pady=2)


    stats_title = ttk.Label(control_frame, text="System", font=("Helvetica", 12, "underline"))
    stats_title.pack(pady=(20, 5))

    self.total_label = ttk.Label(control_frame, text=f"Total Devices: {len(devices)}")
    self.total_label.pack(anchor="w")

    online_count = sum(1 for d in devices if d.to_dict()["status"].lower() == "online")
    self.online_label = ttk.Label(control_frame, text=f"Online: {online_count}")
    self.online_label.pack(anchor="w")


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
    # ctk.set_appearance_mode("dark")

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