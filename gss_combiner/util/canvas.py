from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

class Canvas:
    id = 1
    def __init__(self, plt, parent, xdata, ydata, **kwargs):
        self.parent = parent
        self.xdata = xdata
        self.ydata = ydata
        self.title = kwargs.get("title") if "title" in kwargs else ""
        self.xlabel = kwargs.get("xlabel") if "xlabel" in kwargs else ""
        self.ylabel = kwargs.get("ylabel") if "ylabel" in kwargs else ""
        self.fig_id = Canvas.id
        Canvas.id += 1
        self.fig = plt.figure(self.fig_id)
    def plot(self, plt):
        plt.plot(self.xdata, self.ydata)
        plt.xlabel(self.xlabel)
        plt.ylabel(self.ylabel)
        plt.title(self.title)
        total_width = self.parent.winfo_width()
        total_height = self.parent.winfo_height()
        self_width = total_width / 4.3
        self_height = self_width * 4.8 / 6.4
        dpi = self.parent.winfo_fpixels('1i')
        self.fig.set_size_inches(self_width / dpi, self_height / dpi, forward=True)
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.parent)
        self.plot_widget = self.canvas.get_tk_widget()
        self.plot_widget.grid(row=(self.fig_id - 1) // 4, column=(self.fig_id - 1) % 4, padx=total_width*0.02325/5, pady=total_width*0.0235/5)
        self.canvas.draw()
    
    def destroy(self, plt):
        self.plot_widget.destroy()
        Canvas.count = 1
        plt.figure(self.fig_id)
        plt.close()


TELEM_DATA_KEYS = {
    "barometer_altitude": {
        "title": "Barometer Altitude",
    },
    "latitude": {
        "title": "Latitude"
    },
    "longitude": {
        "title": "Longitude"
    },
    "altitude": {
        "title": "Altitude"
    },
    "highG_ax": {
        "title": "High G X Acceleration"
    },
    "highG_ay": {
        "title": "High G Y Acceleration"
    },
    "highG_az": {
        "title": "High G Z Acceleration"
    },
    "battery_voltage": {
        "title": "Battery Voltage"
    },
    "cam_battery_voltage": {
        "title": "Cam Battery Voltage"
    },
    "FSM_State": {
        "title": "FSM State"
    },
    "tilt_angle": {
        "title": "Tilt Angle"
    },
    "frequency": {
        "title": "Frequency"
    },
    "RSSI": {
        "title": "RSSI"
    },
    "sat_count": {
        "title": "Satellite Count"
    },
    "kf_velocity": {
        "title": "Kalman Filter Velocity"
    },
    "kf_position": {
        "title": "Kalman Filter Position"
    },
    "is_sustainer": {
        "title": "Is it sustainer?"
    },
    "roll_rate": {
        "title": "Roll Rate"
    },
    "c_valid": {
        "title": "Camera Valid"
    },
    "c_on": {
        "title": "Camera On"
    },
    "c_rec": {
        "title": "Camera Recording"
    },
    "vtx_on": {
        "title": "Video Transmitting"
    },
    "vmux_stat": {
        "title": "Video MUX Status"
    },
    "cam_ack": {
        "title": "Camera Acknowledgement"
    },
    "cmd_ack": {
        "title": "Command Acknowledged"
    },
    "gps_fixtype": {
        "title": "GPS Fixed?"
    },
    "pyro_a": {
        "title": "Pyro A"
    },
    "pyro_b": {
        "title": "Pyro B"
    },
    "pyro_c": {
        "title": "Pyro C"
    },
    "pyro_d": {
        "title": "Pyro D"
    }
}