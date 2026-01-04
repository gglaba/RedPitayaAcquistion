import customtkinter as ctk
from tkinter import StringVar, simpledialog, messagebox
from typing import Any, Dict
from DecimationManager import DecimationManager
import json
from pathlib import Path

def _sampling_rate(dec_key: str, dec_dict: Dict[str, str]) -> float:
    return 125e6 / int(dec_dict[dec_key])

def loops_from_time(t_s: float, buf: int, sr: float,
                    delay_ms: float, overhead: float = 0.01) -> int:
    loop_t = buf / sr + delay_ms / 1_000 + overhead
    return max(1, round(t_s / loop_t))

def time_from_loops(loops: int, buf: int, sr: float,
                    delay_ms: float, overhead: float = 0.01) -> float:
    loop_t = buf / sr + delay_ms / 1_000 + overhead
    return loops * loop_t

class InputBoxes(ctk.CTkFrame):

    def __init__(self,
                 master: Any,
                 *positional,                   
                 labels: list[str] | None = None,
                 status_line: Any | None = None,
                 decimation_options: Dict[str, str] | None = None,
                 **kwargs) -> None:

        self.title = "Parameters"
        if positional and isinstance(positional[0], str):
            self.title = positional[0]

        self.status_line = status_line

        frame_kwargs = {k: v for k, v in kwargs.items()
                        if k not in {"labels", "status_line"}}
        super().__init__(master, **frame_kwargs)

        self.labels = labels or ["Decimation", "Buffer size",
                                 "Delay", "Loops", "Time"]

        self.decimations = DecimationManager()
        self.ADD_NEW_OPTION = "Add new sampling rate..."
        self.DELETE_OPTION = "Delete selected sampling rate..."

        self._refresh_decimation_options()

        self._updating = False

        TRIG_OPTIONS = [
            "RP_TRIG_SRC_NOW",
            "RP_TRIG_SRC_CHA_PE",
            "RP_TRIG_SRC_CHA_NE",
            "RP_TRIG_SRC_CHB_PE",
            "RP_TRIG_SRC_CHB_NE",
        ]

        self.vars: Dict[str, StringVar] = {}
        self.inputs: Dict[str, ctk.CTkEntry | ctk.CTkComboBox] = {}

        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(self, text=self.title,
                     fg_color="gray30", corner_radius=6)\
            .grid(row=0, column=0, columnspan=4,
                  padx=10, pady=(10, 4), sticky="ew")

        default_values = {
            "Buffer size": "16384",
            "Delay":"0",
            "Loops":"64",
            "Time":"0.008",
            "Trigger Source": "RP_TRIG_SRC_NOW"
        }

        for i, lbl in enumerate(self.labels):
            ctk.CTkLabel(self, text=lbl).grid(row=i+1, column=0,
                                              padx=10, pady=5, sticky="ew")

            if lbl == "Decimation":
                var = StringVar(value=list(self.decimation_options.keys())[0])
                widget = ctk.CTkComboBox(self, variable=var,
                                         values=list(self.decimation_options.keys()))
                widget.bind("<<ComboboxSelected>>", self._on_decimation_selected)
                add_btn = ctk.CTkButton(self, text="+", width=30, command=self._prompt_new_sampling_rate)
                del_btn = ctk.CTkButton(self, text="-", width=30, command=self._delete_selected_sampling_rate)
                widget.grid(row=i+1, column=1, padx=(10,0), pady=5, sticky="e")
                add_btn.grid(row=i+1, column=2, padx=(2,0), pady=5)
                del_btn.grid(row=i+1, column=3, padx=(2,10), pady=5)
            elif lbl == "Trigger Source":
                var = StringVar(value="RP_TRIG_SRC_NOW")
                widget = ctk.CTkComboBox(self, variable=var, values=TRIG_OPTIONS)
                widget.grid(row=i+1, column=1, padx=10, pady=5, sticky="e", columnspan=3)
            else:
                var = StringVar(value=default_values.get(lbl, "0"))
                widget = ctk.CTkEntry(self, textvariable=var)
                var.trace_add("write",
                              lambda *_, l=lbl: self._on_user_edit(l))
                widget.grid(row=i+1, column=1, padx=10, pady=5, sticky="e", columnspan=3)
            self.vars[lbl] = var
            self.inputs[lbl] = widget

        self.calculation_mode = StringVar(value="Time")
        rb_frame = ctk.CTkFrame(self, fg_color="transparent")
        rb_frame.grid(row=len(self.labels)+1, column=0,
                      columnspan=4, pady=(2, 0), sticky="ew")

        ctk.CTkRadioButton(rb_frame, text="Time  ➜  Loops",
                           variable=self.calculation_mode, value="Time")\
            .pack(side="left", padx=6)
        ctk.CTkRadioButton(rb_frame, text="Loops ➜ Time",
                           variable=self.calculation_mode, value="Loops")\
            .pack(side="left", padx=6)

        ctk.CTkButton(self, text="Recalculate",
                      command=self.recalculate)\
            .grid(row=len(self.labels)+2, column=0, columnspan=4,
                  padx=10, pady=8)

    def _refresh_decimation_options(self):
        self.decimation_options = self.decimations.get_dict()

    def _on_decimation_selected(self, event=None):
        pass

    def _prompt_new_sampling_rate(self):
        parent = self.winfo_toplevel()
        rate_str = simpledialog.askstring(
            "Add Sampling Rate",
            "Enter new sampling rate (in MSa/s):",
            parent=parent
        )
        if not rate_str:
            return
        try:
            rate = float(rate_str)
            if rate <= 0 or rate > 125:
                raise ValueError
        except ValueError:
            messagebox.showerror(
                "Invalid Input",
                "Please enter a valid positive number up to 125.",
                parent=parent
            )
            return

        decimation = int(round(125 / rate))
        power2 = 1
        while power2 < decimation:
            power2 <<= 1
        decimation = power2
        actual_rate = 125 / decimation
        label = f"{actual_rate:.6g} MSa/s"
        value = str(decimation)

        if label not in self.decimation_options:
            self.decimations.save(label, value)
            self._refresh_decimation_options()
            self.inputs["Decimation"].configure(values=list(self.decimation_options.keys()))
        self.vars["Decimation"].set(label)

    def _delete_selected_sampling_rate(self):
            parent = self.winfo_toplevel()
            selected = self.vars["Decimation"].get()
            if selected not in self.decimation_options:
                messagebox.showinfo("Delete Sampling Rate", "Select a valid sampling rate to delete.", parent=parent)
                return
            confirm = messagebox.askyesno("Delete Sampling Rate", f"Delete '{selected}'?", parent=parent)
            if confirm:
                self.decimations.delete(selected)
                self._refresh_decimation_options()
                self.inputs["Decimation"].configure(values=list(self.decimation_options.keys()))
                self.vars["Decimation"].set(list(self.decimation_options.keys())[0])

    def _on_user_edit(self, lbl: str) -> None:
        if self._updating:
            return
        if lbl in ("Time", "Loops"):
            self.calculation_mode.set(lbl)


    def _set_var(self, lbl: str, value: str) -> None:
        self._updating = True
        self.vars[lbl].set(value)
        self._updating = False


    def hide_input(self, label: str) -> None:
        if label in self.inputs:
            self.inputs[label].grid_remove()


    def show_input(self, label: str) -> None:
        if label in self.inputs:
            self.inputs[label].grid()


    def get(self) -> Dict[str, float | int | str]:
        out: Dict[str, float | int | str] = {}

        for lbl, widget in self.inputs.items():
            if lbl == "Decimation":
                key = widget.get()
                out[lbl] = self.decimation_options.get(key, "1")
            elif lbl == "Trigger Source":
                out[lbl] = widget.get()
            else:
                raw = widget.get()
                out[lbl] = float(raw) if lbl == "Time" else int(raw or 0)

        return out


    def set(self, params: Dict[str, Any]) -> None:
        rev_dec = {v: k for k, v in self.decimation_options.items()}

        for lbl, widget in self.inputs.items():
            if lbl not in params:
                continue

            if lbl == "Decimation":
                key = rev_dec.get(
                    str(params[lbl]),
                    list(self.decimation_options.keys())[0]
                )
                widget.set(key)
            elif lbl == "Trigger Source":
                self._set_var(lbl, str(params[lbl]))
            else:
                self._set_var(lbl, str(params[lbl]))


    def recalculate(self) -> None:
        try:
            params = self.get()
            sample_rate = _sampling_rate(
                self.vars["Decimation"].get(),
                self.decimation_options
            )

            if self.calculation_mode.get() == "Time":
                loops = loops_from_time(
                    params["Time"],
                    params["Buffer size"],
                    sample_rate,
                    params["Delay"]
                )
                self._set_var("Loops", str(loops))
                message = "Calculated number of loops based on time input."
            else:
                duration = time_from_loops(
                    params["Loops"],
                    params["Buffer size"],
                    sample_rate,
                    params["Delay"]
                )
                self._set_var("Time", f"{duration:.6f}")
                message = "Calculated time based on loop count."

            if self.status_line:
                self.status_line.update_status(message)

        except Exception as error:
            if self.status_line:
                self.status_line.update_status(f"Error during recalculation: {error}")
            else:
                raise
    
    def create_streaming_view(self, config_path: str | Path = "streaming_mode/config.json") -> None:
        # 1) Hide ALL existing children to avoid overlapping with streaming controls
        for child in list(self.winfo_children()):
            try:
                child.grid_remove()
            except Exception:
                pass

        # 2) Clear mappings of inputs for now (keep vars dict so get()/set() stays safe)
        #    We only replace/add streaming keys inside self.inputs.
        for k in list(self.inputs.keys()):
            self.inputs.pop(k, None)

        # 3) Define editable keys, pretty labels, and option sets
        editable_keys = [
            "data_type_sd",
            "format_sd",
            "resolution",
            "channel_state_1",
            "channel_state_2",
            "channel_attenuator_1",
            "channel_attenuator_2",
            "adc_decimation",
        ]
        pretty_labels = {
            "data_type_sd": "Data type",
            "format_sd": "File format",
            "resolution": "Resolution",
            "channel_state_1": "Channel 1 state",
            "channel_state_2": "Channel 2 state",
            "channel_attenuator_1": "Channel 1 Gain",
            "channel_attenuator_2": "Channel 2 Gain",
            "adc_decimation": "ADC decimation",
        }
        # For reverse lookup if needed
        self._streaming_pretty_to_key = {v: k for k, v in pretty_labels.items()}
        self._streaming_key_to_pretty = pretty_labels.copy()

        options = {
            "data_type_sd": ["VOLT", "RAW"],
            "format_sd": ["BIN", "WAV", "TDMS"],
            "resolution": ["BIT_16", "BIT_8"],
            "channel_state_1": ["ON", "OFF"],
            "channel_state_2": ["ON", "OFF"],
            "channel_attenuator_1": ["A_1_1", "A_1_20"],
            "channel_attenuator_2": ["A_1_1", "A_1_20"],
            "adc_decimation": ["1", "2", "4", "8", "16", "32", "64", "128", "256", "512", "1024", "2048", "4096", "8192"],
        }

        pretty_option_map = {
            "channel_attenuator_1": {"A_1_1": "±1V", "A_1_20": "±20V"},
            "channel_attenuator_2": {"A_1_1": "±1V", "A_1_20": "±20V"},
            "data_type_sd": {"VOLT": "Voltage", "RAW": "Raw"},
            "format_sd": {"BIN": "Binary", "WAV": "Wave", "TDMS": "TDMS"},
            "resolution": {"BIT_16": "16-bit", "BIT_8": "8-bit"},
            "channel_state_1": {"ON": "Enabled", "OFF": "Disabled"},
            "channel_state_2": {"ON": "Enabled", "OFF": "Disabled"}
            }

        # 4) Load defaults from config.json
        defaults: dict[str, str] = {}
        cfg_path = Path(config_path)
        if cfg_path.exists():
            try:
                with cfg_path.open("r", encoding="utf-8") as f:
                    cfg = json.load(f)
                adc = cfg.get("adc_streaming", {})
                for k in editable_keys:
                    v = adc.get(k)
                    if v is not None:
                        defaults[k] = str(v)
            except Exception as e:
                if self.status_line:
                    self.status_line.update_status(f"Streaming config load failed: {e}")

        # 5) Recreate the streaming UI cleanly
        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(self, text="Streaming Parameters",
                    fg_color="gray30", corner_radius=6)\
            .grid(row=0, column=0, columnspan=4, padx=10, pady=(10, 4), sticky="ew")

        row = 1
        self._streaming_pretty_to_internal = {}  # pretty -> internal value mapping per key
        for key in editable_keys:
            pretty = pretty_labels.get(key, key.replace("_", " "))
            ctk.CTkLabel(self, text=pretty).grid(row=row, column=0, padx=10, pady=5, sticky="w")

            # Map internal values to pretty display values
            option_map = pretty_option_map.get(key, None)
            if option_map:
                pretty_options = [option_map[v] for v in options[key]]
                # Build reverse mapping for later
                self._streaming_pretty_to_internal[key] = {option_map[v]: v for v in options[key]}
                # Set default value (pretty)
                internal_default = defaults.get(key, options[key][0])
                pretty_default = option_map.get(internal_default, internal_default)
                var = StringVar(value=pretty_default)
                widget = ctk.CTkComboBox(self, variable=var, values=pretty_options)
            else:
                pretty_options = options[key]
                self._streaming_pretty_to_internal[key] = {v: v for v in options[key]}
                internal_default = defaults.get(key, options[key][0])
                var = StringVar(value=internal_default)
                widget = ctk.CTkComboBox(self, variable=var, values=pretty_options)

            widget.grid(row=row, column=1, padx=10, pady=5, sticky="ew", columnspan=3)
            self.vars[key] = var
            self.inputs[key] = widget
            row += 1

        # --- Add "Time" parameter for user only (not saved to JSON) ---
        ctk.CTkLabel(self, text="Time (s)").grid(row=row, column=0, padx=10, pady=5, sticky="w")
        time_var = StringVar(value="0")
        time_entry = ctk.CTkEntry(self, textvariable=time_var)
        time_entry.grid(row=row, column=1, padx=10, pady=5, sticky="ew", columnspan=3)
        self.vars["streaming_time"] = time_var
        self.inputs["streaming_time"] = time_entry

        if self.status_line:
            self.status_line.update_status("Streaming mode UI loaded.")

    def get_streaming_params(self) -> dict[str, str]:
        """
        Return current streaming parameter selections for the editable set.
        Excludes the 'Time' parameter (which is for UI only).
        """
        keys = [
            "data_type_sd",
            "format_sd",
            "resolution",
            "channel_state_1",
            "channel_state_2",
            "channel_attenuator_1",
            "channel_attenuator_2",
            "adc_decimation",
        ]
        out: dict[str, str] = {}
        for k in keys:
            w = self.inputs.get(k)
            if w:
                pretty_val = w.get()
                # Map pretty value back to internal value
                internal_val = self._streaming_pretty_to_internal[k].get(pretty_val, pretty_val)
                out[k] = internal_val
        return out

    def get_streaming_time(self) -> str:
        return self.vars.get("streaming_time", StringVar(value="1.0")).get()