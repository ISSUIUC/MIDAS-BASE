# function _build_consoles_tab(parent, get_devices):

#     # Outer container
#     make a frame inside parent that fills and expands, with padding

#     # Three stacked sections inside it
#     make selector_frame at the top (horizontal stretch only, small bottom pad)
#     make output_frame in the middle (fill both, expand)
#     make input_frame at the bottom (horizontal stretch only, small top pad)


#     # --- selector_frame ---
#     put a "Device:" label on the left

#     make a StringVar, remember it as console_port_var

#     make a dropdown (Combobox) bound to console_port_var,
#         readonly, width about 20, remember it as console_dropdown
#     put it on the left

#     make an empty label, remember it as console_type_label
#     put it on the left with a little padding


#     # --- output_frame ---
#     make a vertical scrollbar, put it on the right, fill vertical

#     make a Text widget:
#         wrap by word
#         black background, white text, lime cursor
#         disabled by default
#         remember it as console_output
#     put it in the middle, fill both, expand

#     on the Text widget, add two color tags:
#         "user_in"  -> bright green
#         "raw_out"  -> light sky blue

#     wire the scrollbar and the Text widget to each other, both directions


#     # --- input_frame ---
#     make a StringVar, remember it as console_input_var

#     make an Entry bound to console_input_var
#     put it on the left, fill horizontally, expand
#     keep a reference to it so we can bind Return later

#     (Send button comes later, after send_command exists)


#     # --- bookkeeping ---
#     remember on self: which port we're currently following, initially nothing


#     # --- helper ---
#     define function port_to_device(port):
#         if port is empty, return nothing
#         for each device in get_devices():
#             if device's port equals port, return that device
#         return nothing


#     # --- load_device ---
#     define function load_device(port):

#         # 1. detach from whatever we were following
#         look up the old device using the stored active port
#         if there was an old device:
#             tell it to stop sending output to our Text widget

#         # 2. clear the terminal
#         enable the Text widget
#         delete everything in it

#         # 3. nothing to show?
#         look up the new device from port
#         if no device:
#             write "<no device selected>"
#             disable the Text widget
#             clear the type label
#             forget the active port
#             return

#         # 4. show history and start following
#         write "<BEGINNING OF LOG>"
#         for each line in the device's stored log:
#             if line starts with "[F]", write it with the raw_out tag
#             else if line starts with ">> ", write it with the user_in tag
#             else write it plain

#         disable the Text widget
#         scroll to the bottom

#         tell the device to start sending output to our Text widget
#         remember this port as the active one
#         set the type label to "Type: <device name>"


#     # --- dropdown handler ---
#     define function when_dropdown_changes:
#         call load_device with whatever's currently selected

#     hook that function up to the dropdown's selection event


#     # --- keep dropdown in sync ---
#     define function refresh_devices:

#         # figure out what the dropdown should show
#         gather every device that is ready for console use
#         pull out their port names
#         set the dropdown's choices to that list

#         read whatever's currently selected

#         # case: selection is gone
#         if selection is not in the new list:
#             if there are ports:
#                 select the first one and load it
#             else:
#                 clear the selection and load nothing

#         # case: selection is valid but not loaded yet
#         else if selection is not the active port:
#             load it


#     # --- send command ---
#     define function send_command:

#         read the entry box, strip whitespace
#         if empty, return

#         look up the device for the currently selected port
#         if no device, return

#         echo ">> " + command into the log
#             (so the user sees what they typed, in green)

#         try to send the command plus a newline to the device
#         if that fails, write an error line into the log

#         clear the entry box


#     # --- wire everything up ---
#     bind Return on the entry to send_command
#     make a "Send" button on the right of input_frame, calling send_command

#     store refresh_devices on self so the main app can call it
#     call refresh_devices once right now so the tab isn't empty