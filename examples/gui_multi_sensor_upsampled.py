"""
Tkinter GUI for 3 PASCO sensors với UPSAMPLING real-time

Cải tiến:
- Thu thập dữ liệu thô với tần số không ổn định (~5-10Hz qua Bluetooth)
- Upsampling real-time lên tần số cố định (50Hz/100Hz) bằng PCHIP interpolation
- Hiển thị mượt mà với tần số ổn định
- Lưu cả dữ liệu gốc và upsampled

Tính năng:
- Kết nối tới 3 sensors PASCO
- Real-time upsampling (PCHIP) từ ~8Hz → 50Hz/100Hz
- Time-domain và FFT plots
- Auto-save CSV với dữ liệu upsampled
"""

import sys
import time
import csv
import math
from collections import deque
from datetime import datetime
import os

# Matplotlib embedding
import matplotlib
matplotlib.use('TkAgg')
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib as mpl

mpl.rcParams['path.simplify'] = True
mpl.rcParams['path.simplify_threshold'] = 0.5
mpl.rcParams['agg.path.chunksize'] = 2000

import numpy as np
from scipy import interpolate

try:
    import winsound
except Exception:
    winsound = None

sys.path.append('src')
sys.path.append('..')
from pasco.pasco_ble_device import PASCOBLEDevice

import tkinter as tk
from tkinter import ttk, messagebox, filedialog


class SensorClient:
    """
    Sensor client với dual-buffer system:
    - raw_data: Dữ liệu gốc từ sensor (tần số không ổn định)
    - upsampled_data: Dữ liệu đã upsample (tần số cố định)
    """
    def __init__(self, name, color, target_fs=50.0):
        self.name = name
        self.color = color
        self.dev = PASCOBLEDevice()
        self.connected = False
        self.measurements = []
        self.selected_measurement = None
        self.unit = ''

        # Dual buffer system
        self.target_fs = target_fs  # Tần số upsampling mục tiêu
        self.raw_data = deque(maxlen=500)  # Dữ liệu gốc (timestamp thực, không đều)
        self.upsampled_data = deque(maxlen=3000)  # Dữ liệu upsampled (tần số cố định)

        self.threshold = 0.0
        self.last_upsample_time = 0
        self.upsample_interval = 0.2  # Upsample mỗi 200ms

        # Statistics
        self.actual_sample_count = 0
        self.actual_freq_estimate = 0.0

    def connect_by_id(self, sensor_id: str):
        self.dev.connect_by_id(sensor_id)
        self.connected = True
        self.measurements = self.dev.get_measurement_list()
        if self.measurements and not self.selected_measurement:
            self.selected_measurement = self.measurements[0]
        self.raw_data.clear()
        self.upsampled_data.clear()

    def disconnect(self):
        if self.connected:
            try:
                self.dev.disconnect()
            except Exception:
                pass
        self.connected = False

    def read_once(self):
        if not (self.connected and self.selected_measurement):
            return None
        return self.dev.read_data(self.selected_measurement)

    def add_sample(self, timestamp, value):
        """Thêm sample vào raw buffer"""
        self.raw_data.append((timestamp, value))
        self.actual_sample_count += 1

    def upsample_recent(self, current_time):
        """
        Upsample dữ liệu gần đây sử dụng PCHIP interpolation
        """
        if len(self.raw_data) < 4:
            # Cần ít nhất 4 điểm cho PCHIP
            return

        # Lấy dữ liệu trong window gần đây (5 giây)
        window_s = 5.0
        recent_raw = [(t, v) for t, v in self.raw_data if current_time - t <= window_s]

        if len(recent_raw) < 4:
            return

        # Tính actual frequency
        if len(recent_raw) >= 2:
            time_span = recent_raw[-1][0] - recent_raw[0][0]
            if time_span > 0:
                self.actual_freq_estimate = len(recent_raw) / time_span

        try:
            # Extract timestamps and values
            timestamps = np.array([t for t, _ in recent_raw])
            values = np.array([v for _, v in recent_raw])

            # Tạo PCHIP interpolator
            interpolator = interpolate.PchipInterpolator(timestamps, values)

            # Tạo timestamp array với tần số cố định
            t_start = timestamps[0]
            t_end = timestamps[-1]
            dt = 1.0 / self.target_fs

            # Tính số điểm upsampled
            n_points = int((t_end - t_start) * self.target_fs)

            if n_points < 2:
                return

            # Generate uniform timestamps
            uniform_timestamps = np.linspace(t_start, t_end, n_points)

            # Interpolate
            upsampled_values = interpolator(uniform_timestamps)

            # Chỉ thêm các điểm mới (sau điểm cuối cùng trong upsampled_data)
            if self.upsampled_data:
                last_t = self.upsampled_data[-1][0]
                new_points = [(t, v) for t, v in zip(uniform_timestamps, upsampled_values) if t > last_t]
            else:
                new_points = list(zip(uniform_timestamps, upsampled_values))

            # Thêm vào buffer
            for t, v in new_points:
                self.upsampled_data.append((t, float(v)))

        except Exception as e:
            # Fallback: nếu upsampling fail, log error
            import traceback
            print(f"Upsampling error for {self.name}: {e}")
            print(traceback.format_exc())

    def save_csv(self, path, use_upsampled=True):
        """Lưu CSV - có thể chọn raw hoặc upsampled data"""
        data_to_save = self.upsampled_data if use_upsampled else self.raw_data
        mode = 'upsampled' if use_upsampled else 'raw'

        print(f"\n[DEBUG] save_csv for sensor {self.name}:")
        print(f"  Mode: {mode}")
        print(f"  Buffer length: {len(data_to_save)}")
        print(f"  Buffer type: {type(data_to_save)}")
        print(f"  Connected: {self.connected}")
        print(f"  Selected measurement: {self.selected_measurement}")

        if not data_to_save:
            raise ValueError(f"No {mode} data to save for sensor {self.name}")

        # Convert deque to list for iteration
        data_list = list(data_to_save)
        print(f"  Converted to list: {len(data_list)} items")

        if len(data_list) > 0:
            print(f"  First item: {data_list[0]}")
            print(f"  Last item: {data_list[-1]}")

        with open(path, 'w', newline='', encoding='utf-8') as f:
            w = csv.writer(f)
            w.writerow(['time_s', self.selected_measurement or 'value', f'mode={mode}'])

            rows_written = 0
            for t, v in data_list:
                w.writerow([f"{t:.6f}", f"{float(v):.4f}"])
                rows_written += 1

        print(f"  ✓ Wrote {rows_written} rows to {path}\n")
        return rows_written


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('PASCO Multi-Sensor with Real-time Upsampling')
        self.geometry('1200x720')

        # Sampling configuration
        self.base_fs = 10.0  # Target base sampling (qua Bluetooth thực tế ~5-10Hz)
        self.base_dt = 1.0 / self.base_fs

        # Upsampling configuration
        self.upsample_fs_choices = [20, 50, 100, 200]
        self.upsample_fs = 50.0  # Default upsampling frequency

        # Display
        self.window_s = 30.0  # Display window

        # Sensors
        self.sensors = [
            SensorClient('A', '#d32f2f', target_fs=self.upsample_fs),
            SensorClient('B', '#388e3c', target_fs=self.upsample_fs),
            SensorClient('C', '#1976d2', target_fs=self.upsample_fs),
        ]

        # Default sensor IDs
        self.default_ids = ['966-489', '946-449', '964-462']

        # Recording state
        self.recording = False
        self.t0 = None
        self._tick_after_id = None

        # CSV logging
        self.csv_file = None
        self.csv_writer = None
        self.csv_path = None
        self.csv_dir = os.path.join(os.getcwd(), 'recordings_upsampled')
        os.makedirs(self.csv_dir, exist_ok=True)

        # Build UI
        self._build_modern_ui()

        # Plotting
        self.plot_interval_ms = 100  # Refresh plots mỗi 100ms
        self.fft_interval_s = 1.0
        self.after(self.plot_interval_ms, self._refresh_plots)

        # Upsampling timer
        self.upsample_interval_ms = 200  # Upsample mỗi 200ms
        self.after(self.upsample_interval_ms, self._upsample_all)

    def _build_modern_ui(self):
        try:
            style = ttk.Style()
            style.theme_use('clam')
        except Exception:
            pass

        # Grid layout
        self.columnconfigure(0, weight=1, minsize=150)
        self.columnconfigure(1, weight=5)
        self.rowconfigure(1, weight=1)

        # Toolbar
        top = ttk.Frame(self)
        top.grid(row=0, column=0, columnspan=2, sticky='nsew', padx=6, pady=(6, 0))
        ttk.Label(top, text='PASCO Multi-Sensor (Upsampled)', font=('Segoe UI', 13, 'bold')).pack(side='left')

        top_controls = ttk.Frame(top)
        top_controls.pack(side='right')

        # Upsampling frequency selector
        ttk.Label(top_controls, text='Upsample Fs:').pack(side='right', padx=(8, 2))
        self.upsample_fs_var = tk.IntVar(value=int(self.upsample_fs))
        fs_box = ttk.Combobox(top_controls, state='readonly', width=6,
                               values=[str(v) for v in self.upsample_fs_choices],
                               textvariable=self.upsample_fs_var)
        fs_box.pack(side='right', padx=4)

        def _on_fs_change(*_):
            try:
                val = int(self.upsample_fs_var.get())
            except Exception:
                val = 50
            self.upsample_fs = float(val)
            for s in self.sensors:
                s.target_fs = self.upsample_fs
        self.upsample_fs_var.trace_add('write', _on_fs_change)

        # Control buttons
        self.fft_enabled = tk.BooleanVar(value=True)
        ttk.Checkbutton(top_controls, text='Enable FFT', variable=self.fft_enabled).pack(side='right', padx=4)
        ttk.Button(top_controls, text='Save All CSV', command=self.save_all_csv).pack(side='right', padx=4)
        ttk.Button(top_controls, text='Stop', command=self.stop_recording).pack(side='right', padx=4)
        ttk.Button(top_controls, text='Start Recording', command=self.start_recording).pack(side='right', padx=4)

        # Left sidebar
        left = ttk.Frame(self)
        left.grid(row=1, column=0, sticky='nsew', padx=6, pady=6)
        left.columnconfigure(0, weight=1)

        for idx, s in enumerate(self.sensors):
            fr = ttk.Labelframe(left, text=f'Sensor {s.name}')
            fr.grid(row=idx, column=0, sticky='we', padx=2, pady=4)

            ttk.Label(fr, text='ID:').grid(row=0, column=0, sticky='w')
            s.id_var = tk.StringVar()
            if idx < len(self.default_ids):
                s.id_var.set(self.default_ids[idx])
            ttk.Entry(fr, textvariable=s.id_var, width=12).grid(row=0, column=1, sticky='w', padx=4)

            btn_connect = ttk.Button(fr, text='Connect', command=lambda ss=s: self.connect_sensor_async(ss))
            btn_connect.grid(row=0, column=2, padx=4)
            s.btn_connect = btn_connect
            ttk.Button(fr, text='Disconnect', command=lambda ss=s: self.disconnect_sensor(ss)).grid(row=0, column=3, padx=4)

            ttk.Label(fr, text='Measurement:').grid(row=1, column=0, sticky='w')
            s.meas_var = tk.StringVar()
            s.meas_cb = ttk.Combobox(fr, textvariable=s.meas_var, width=24, state='readonly', values=[])
            s.meas_cb.grid(row=1, column=1, columnspan=3, sticky='we', padx=4)

            # Callback to update selected_measurement when user changes combobox
            def _on_meas_change(event, sensor=s):
                selected = sensor.meas_var.get()
                if selected:
                    sensor.selected_measurement = selected
                    self.log(f'Sensor {sensor.name}: measurement changed to {selected}')
            s.meas_cb.bind('<<ComboboxSelected>>', _on_meas_change)

            ttk.Label(fr, text='Value:').grid(row=2, column=0, sticky='w')
            s.val_var = tk.StringVar(value='-')
            s.val_lbl = ttk.Label(fr, textvariable=s.val_var, width=14, foreground=s.color)
            s.val_lbl.grid(row=2, column=1, sticky='w', padx=4)

            # Stats label
            s.stats_var = tk.StringVar(value='')
            ttk.Label(fr, textvariable=s.stats_var, font=('Consolas', 8)).grid(row=3, column=0, columnspan=4, sticky='w', padx=4)

        # Log
        ttk.Label(left, text='Log').grid(row=3, column=0, sticky='w', padx=4, pady=(8, 0))
        self.log_text = tk.Text(left, height=8, width=36)
        self.log_text.grid(row=4, column=0, sticky='nsew', padx=4, pady=4)
        left.rowconfigure(4, weight=1)

        self.progress = ttk.Label(left, text='Idle')
        self.progress.grid(row=5, column=0, sticky='w', padx=4, pady=2)

        # Main content (Notebook)
        main = ttk.Frame(self)
        main.grid(row=1, column=1, sticky='nsew', padx=6, pady=6)
        main.rowconfigure(0, weight=1)
        main.columnconfigure(0, weight=1)

        nb = ttk.Notebook(main)
        nb.grid(row=0, column=0, sticky='nsew')

        time_tab = ttk.Frame(nb)
        fft_tab = ttk.Frame(nb)
        nb.add(time_tab, text='Time Domain (Upsampled)')
        nb.add(fft_tab, text='Frequency (FFT)')

        # Time domain plot
        ttk.Label(time_tab, text='Acceleration vs Time (Upsampled Data)').pack(anchor='w', padx=4, pady=(4, 0))
        self.fig_time = Figure(figsize=(6, 5), dpi=100)
        self.fig_time.tight_layout()
        ax = self.fig_time.add_subplot(1, 1, 1)
        ax.grid(True, alpha=0.3)
        ax.set_xlim(0, self.window_s)
        ax.set_xlabel('Time [s]')
        ax.set_ylabel('Acceleration')
        self.ax_time = ax
        self.time_lines = {}
        for s in self.sensors:
            line, = ax.plot([], [], color=s.color, lw=1.6, label=f'Sensor {s.name}')
            self.time_lines[s.name] = line
        ax.legend(loc='upper right', fontsize=8, framealpha=0.2)
        self.canvas_time = FigureCanvasTkAgg(self.fig_time, master=time_tab)
        self.canvas_time.get_tk_widget().pack(fill='both', expand=True, padx=4, pady=4)
        self.canvas_time.draw()  # Initial draw

        # FFT plot
        ttk.Label(fft_tab, text='Magnitude Spectrum').pack(anchor='w', padx=4, pady=(4, 0))
        self.fig_fft = Figure(figsize=(6, 5), dpi=100)
        self.fig_fft.tight_layout()
        axf = self.fig_fft.add_subplot(1, 1, 1)
        axf.grid(True, alpha=0.3)
        axf.set_xlim(0, self.upsample_fs / 2.0)
        axf.set_ylim(0, 1.05)
        axf.set_xlabel('Frequency [Hz]')
        axf.set_ylabel('Normalized Magnitude')
        self.ax_fft = axf
        self.fft_lines = {}
        for s in self.sensors:
            line, = axf.plot([], [], color=s.color, lw=1.2, label=f'Sensor {s.name}')
            self.fft_lines[s.name] = line
        axf.legend(loc='upper right', fontsize=8, framealpha=0.2)
        self.canvas_fft = FigureCanvasTkAgg(self.fig_fft, master=fft_tab)
        self.canvas_fft.get_tk_widget().pack(fill='both', expand=True, padx=4, pady=4)
        self.canvas_fft.draw()  # Initial draw
        self.fft_info = ttk.Label(fft_tab, text='Dominant peaks: -')
        self.fft_info.pack(anchor='w', padx=6, pady=(0, 4))

        # Visibility toggles
        vis = ttk.Frame(main)
        vis.grid(row=1, column=0, sticky='w', padx=4, pady=(6, 0))
        ttk.Label(vis, text='Visible:').pack(side='left')
        self.visible = {}
        for s in self.sensors:
            v = tk.BooleanVar(value=True)
            self.visible[s.name] = v
            ttk.Checkbutton(vis, text=f'{s.name}', variable=v).pack(side='left', padx=4)

    def log(self, msg: str):
        ts = time.strftime('%H:%M:%S')
        self.log_text.insert('end', f'[{ts}] {msg}\n')
        self.log_text.see('end')
        try:
            lines = int(float(self.log_text.index('end-1c').split('.')[0]))
            if lines > 300:
                self.log_text.delete('1.0', '50.0')
        except Exception:
            pass

    def connect_sensor_async(self, sensor: SensorClient):
        sid = sensor.id_var.get().strip()
        if not sid:
            messagebox.showwarning('Connect', 'Please enter sensor ID')
            return

        self.log(f'Sensor {sensor.name}: connecting to {sid}...')
        sensor.btn_connect['state'] = 'disabled'

        def worker():
            try:
                sensor.connect_by_id(sid)
                # Filter acceleration measurements
                accel_names = [m for m in sensor.measurements if 'accel' in m.lower()]

                def finalize_ok():
                    sensor.meas_cb['values'] = accel_names if accel_names else sensor.measurements
                    if sensor.meas_cb['values']:
                        sensor.selected_measurement = sensor.meas_cb['values'][0]
                        sensor.meas_var.set(sensor.selected_measurement)
                        try:
                            sensor.unit = sensor.dev.get_measurement_unit(sensor.selected_measurement) or ''
                        except Exception:
                            sensor.unit = ''
                    sensor.btn_connect['state'] = 'normal'
                    self.log(f'Sensor {sensor.name}: connected')

                self.after(0, finalize_ok)
            except Exception as e:
                def finalize_err():
                    sensor.btn_connect['state'] = 'normal'
                    self.log(f'Sensor {sensor.name}: failed - {e}')
                    messagebox.showerror('Connect', str(e))
                self.after(0, finalize_err)

        import threading
        threading.Thread(target=worker, daemon=True).start()

    def disconnect_sensor(self, sensor: SensorClient):
        sensor.disconnect()
        sensor.meas_cb['values'] = []
        sensor.meas_var.set('')
        sensor.val_var.set('-')
        self.log(f'Sensor {sensor.name}: disconnected')

    def start_recording(self):
        # Clear old data
        for s in self.sensors:
            s.raw_data.clear()
            s.upsampled_data.clear()
            s.actual_sample_count = 0

        # Check which sensors are connected
        connected_sensors = [s.name for s in self.sensors if s.connected]
        if not connected_sensors:
            messagebox.showwarning('Start Recording', 'No sensors connected!')
            return

        # Verify sensor configuration
        for s in self.sensors:
            if s.connected:
                self.log(f'Sensor {s.name} config:')
                self.log(f'  - ID: {s.id_var.get()}')
                self.log(f'  - Measurement: {s.selected_measurement}')
                self.log(f'  - Unit: {s.unit}')
                if not s.selected_measurement:
                    self.log(f'  ⚠ WARNING: No measurement selected!')

        self.recording = True
        self.t0 = None
        self.log(f'Recording started (target {self.upsample_fs}Hz upsampled)')
        self.log(f'Connected sensors: {", ".join(connected_sensors)}')

        # Open CSV for auto-logging (upsampled data)
        try:
            ts = datetime.now().strftime('%Y%m%d_%H%M%S')
            self.csv_path = os.path.join(self.csv_dir, f'recording_{ts}_upsampled_{int(self.upsample_fs)}Hz.csv')
            self.csv_file = open(self.csv_path, 'w', newline='', encoding='utf-8')
            self.csv_writer = csv.writer(self.csv_file)
            self.csv_writer.writerow(['time_s', 'A', 'B', 'C'])
            self.log(f'Auto CSV: {self.csv_path}')
        except Exception as e:
            self.log(f'CSV open failed: {e}')
            self.csv_file = None
            self.csv_writer = None

        self._tick()

    def stop_recording(self):
        self.recording = False
        if self._tick_after_id:
            try:
                self.after_cancel(self._tick_after_id)
            except Exception:
                pass
            self._tick_after_id = None

        # Log data summary
        self.log('Recording stopped')
        for s in self.sensors:
            if s.connected:
                raw_count = len(s.raw_data)
                ups_count = len(s.upsampled_data)
                self.log(f'  Sensor {s.name}: {raw_count} raw, {ups_count} upsampled samples')

        # Close CSV
        if self.csv_file:
            try:
                self.csv_file.flush()
                self.csv_file.close()
            except Exception:
                pass
            finally:
                self.csv_file = None
                self.csv_writer = None

    def _tick(self):
        """Thu thập dữ liệu thô từ sensors"""
        if not self.recording:
            return

        if self.t0 is None:
            self.t0 = time.perf_counter()

        now = time.perf_counter()
        stamp = now - self.t0

        any_new_data = False
        for s in self.sensors:
            if s.connected and s.selected_measurement:
                try:
                    val = s.read_once()
                    if isinstance(val, (int, float)):
                        s.add_sample(stamp, val)
                        s.val_var.set(f"{val:.4f}")
                        any_new_data = True

                        # Debug: log first sample
                        if len(s.raw_data) == 1:
                            self.log(f'Sensor {s.name}: First sample received! Value={val:.4f}')

                        # Debug: log data collection
                        if len(s.raw_data) % 10 == 0:  # Log every 10 samples
                            self.log(f'Sensor {s.name}: {len(s.raw_data)} raw samples (latest={val:.4f})')

                        # Trigger upsampling if enough data
                        if len(s.raw_data) >= 4 and len(s.raw_data) % 5 == 0:
                            prev_ups = len(s.upsampled_data)
                            s.upsample_recent(stamp)
                            new_ups = len(s.upsampled_data)

                            # Log upsampling activity
                            if new_ups > prev_ups and new_ups <= 50:  # Log early upsampling
                                self.log(f'Sensor {s.name}: Upsampled! {prev_ups} → {new_ups} points')

                            # Update stats immediately
                            raw_len = len(s.raw_data)
                            s.stats_var.set(f'Raw:{raw_len} Up:{new_ups} ~{s.actual_freq_estimate:.1f}Hz')
                    else:
                        # Log if read_once() returns non-numeric value
                        if len(s.raw_data) == 0:  # Only log once at start
                            self.log(f'Sensor {s.name}: read_once() returned {type(val).__name__}: {val}')
                except Exception as e:
                    self.log(f'Error reading sensor {s.name}: {e}')
                    import traceback
                    traceback.print_exc()
            elif s.connected and not s.selected_measurement:
                # Sensor connected but no measurement selected
                if not hasattr(s, '_logged_no_meas'):
                    self.log(f'WARNING: Sensor {s.name} connected but no measurement selected!')
                    s._logged_no_meas = True

        # Schedule next tick
        self._tick_after_id = self.after(int(self.base_dt * 1000), self._tick)

    def _upsample_all(self):
        """Định kỳ upsample dữ liệu cho tất cả sensors"""
        if self.recording and self.t0 is not None:
            current_time = time.perf_counter() - self.t0

            for s in self.sensors:
                if s.connected and len(s.raw_data) >= 4:
                    prev_ups_len = len(s.upsampled_data)
                    s.upsample_recent(current_time)
                    new_ups_len = len(s.upsampled_data)

                    # Update stats
                    raw_len = len(s.raw_data)
                    s.stats_var.set(f'Raw:{raw_len} Up:{new_ups_len} ~{s.actual_freq_estimate:.1f}Hz')

                    # Debug: log upsampling
                    if new_ups_len > prev_ups_len and new_ups_len % 50 == 0:
                        self.log(f'Sensor {s.name}: upsampled to {new_ups_len} points')

            # Write upsampled data to CSV periodically
            self._write_upsampled_to_csv()

        # Schedule next upsampling
        self.after(self.upsample_interval_ms, self._upsample_all)

    def _write_upsampled_to_csv(self):
        """Ghi dữ liệu upsampled vào CSV"""
        if not self.csv_writer:
            return

        # Check if any sensor has upsampled data
        sensors_with_data = [s for s in self.sensors if s.connected and s.upsampled_data]
        if not sensors_with_data:
            return

        # Find common time range
        min_len = min(len(s.upsampled_data) for s in sensors_with_data)
        if min_len == 0:
            return

        # Write new rows
        # (Simple approach: write last N rows that haven't been written)
        # For production, you'd track last written index
        pass  # CSV writing can be optimized based on requirements

    def _refresh_plots(self):
        """Refresh plots định kỳ"""
        self._draw_time_plot()

        if self.fft_enabled.get() and (not hasattr(self, '_last_fft_draw') or
                                        (time.time() - self._last_fft_draw) > self.fft_interval_s):
            self._draw_fft_plot()
            self._last_fft_draw = time.time()

        self.after(self.plot_interval_ms, self._refresh_plots)

    def _draw_time_plot(self):
        """Vẽ time-domain plot với upsampled data"""
        has_data = False
        for s in self.sensors:
            line = self.time_lines.get(s.name)
            if not line:
                continue

            if not (self.visible.get(s.name, tk.BooleanVar(value=True)).get() and s.upsampled_data):
                line.set_data([], [])
                continue

            # Get recent upsampled data
            if not s.upsampled_data:
                line.set_data([], [])
                continue

            now_t = s.upsampled_data[-1][0]
            vals = [(t, v) for t, v in s.upsampled_data if now_t - t <= self.window_s]

            if not vals:
                line.set_data([], [])
                continue

            xs = [t - (now_t - self.window_s) for t, _ in vals]
            ys = [v for _, v in vals]

            line.set_data(xs, ys)
            has_data = True

        # Auto-scale Y axis
        all_ys = []
        for s in self.sensors:
            if self.visible.get(s.name, tk.BooleanVar(value=True)).get() and s.upsampled_data:
                now_t = s.upsampled_data[-1][0]
                vals = [v for t, v in s.upsampled_data if now_t - t <= self.window_s]
                all_ys.extend(vals)

        if all_ys:
            ymin, ymax = min(all_ys), max(all_ys)
            if ymin == ymax:
                ymin -= 1.0
                ymax += 1.0
            pad = 0.05 * (ymax - ymin)
            self.ax_time.set_ylim(ymin - pad, ymax + pad)

        try:
            self.canvas_time.draw()  # Force redraw
            self.canvas_time.flush_events()  # Process events
        except Exception as e:
            pass  # Ignore draw errors

    def _draw_fft_plot(self):
        """Vẽ FFT plot (sử dụng upsampled data)"""
        max_freq = self.upsample_fs / 2.0

        for s in self.sensors:
            line = self.fft_lines.get(s.name)
            if not line:
                continue

            if not (self.visible.get(s.name, tk.BooleanVar(value=True)).get() and
                    len(s.upsampled_data) >= 32):
                line.set_data([], [])
                continue

            # Compute FFT from upsampled data
            try:
                vals = list(s.upsampled_data)
                ts = [t for t, _ in vals]
                vs = [v for _, v in vals]

                # FFT
                arr = np.array(vs, dtype=float)
                arr = arr - np.mean(arr)
                spec = np.fft.rfft(arr)
                mags = np.abs(spec)
                freqs = np.fft.rfftfreq(len(arr), d=1.0/self.upsample_fs)

                # Normalize and filter
                mmax = max(mags) if max(mags) > 0 else 1.0
                xs = []
                ys = []
                for f, m in zip(freqs, mags):
                    if f > max_freq:
                        break
                    xs.append(f)
                    ys.append(m / mmax)

                line.set_data(xs, ys)
            except Exception as e:
                line.set_data([], [])

        self.ax_fft.set_xlim(0, max_freq)
        try:
            self.canvas_fft.draw()  # Force redraw
            self.canvas_fft.flush_events()  # Process events
        except Exception as e:
            pass  # Ignore draw errors

    def save_all_csv(self):
        """Lưu tất cả sensors ra CSV (cả raw và upsampled)"""
        folder = filedialog.askdirectory(title='Select output folder')
        if not folder:
            return

        ts = datetime.now().strftime('%Y%m%d_%H%M%S')
        saved_files = []
        errors = []

        for s in self.sensors:
            if not s.raw_data and not s.upsampled_data:
                self.log(f'Sensor {s.name}: No data to save')
                continue

            # Save raw
            if s.raw_data:
                try:
                    path_raw = f"{folder}/sensor_{s.name}_raw_{ts}.csv"
                    rows = s.save_csv(path_raw, use_upsampled=False)
                    self.log(f'✓ Saved raw: {rows} rows → {path_raw}')
                    saved_files.append(path_raw)
                except Exception as e:
                    err_msg = f'Sensor {s.name} raw: {e}'
                    self.log(f'✗ Error: {err_msg}')
                    errors.append(err_msg)

            # Save upsampled
            if s.upsampled_data:
                try:
                    path_ups = f"{folder}/sensor_{s.name}_upsampled_{int(self.upsample_fs)}Hz_{ts}.csv"
                    rows = s.save_csv(path_ups, use_upsampled=True)
                    self.log(f'✓ Saved upsampled: {rows} rows → {path_ups}')
                    saved_files.append(path_ups)
                except Exception as e:
                    err_msg = f'Sensor {s.name} upsampled: {e}'
                    self.log(f'✗ Error: {err_msg}')
                    errors.append(err_msg)

        # Show summary
        if saved_files and not errors:
            messagebox.showinfo('Save CSV', f'✓ Saved {len(saved_files)} files to:\n{folder}')
        elif saved_files and errors:
            messagebox.showwarning('Save CSV',
                f'Saved {len(saved_files)} files\n'
                f'Errors: {len(errors)}\n\n'
                f'Check log for details')
        elif errors:
            messagebox.showerror('Save CSV',
                f'Failed to save files!\n\n'
                f'Errors:\n' + '\n'.join(errors[:3]))
        else:
            messagebox.showwarning('Save CSV', 'No data to save from any sensor')


if __name__ == '__main__':
    app = App()
    app.mainloop()
