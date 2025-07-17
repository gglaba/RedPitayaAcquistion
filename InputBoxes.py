import customtkinter as ctk
from tkinter import StringVar, simpledialog, messagebox
from typing import Any, Dict
from DecimationManager import DecimationManager

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
                key = rev_dec.get(str(params[lbl]),
                                  list(self.decimation_options.keys())[0])
                widget.set(key)
            else:
                self._set_var(lbl, str(params[lbl]))

    def recalculate(self) -> None:
        try:
            p = self.get()
            sr = _sampling_rate(self.vars["Decimation"].get(),
                                self.decimation_options)

            if self.calculation_mode.get() == "Time":
                loops = loops_from_time(p["Time"], p["Buffer size"],
                                        sr, p["Delay"])
                self._set_var("Loops", str(loops))
                msg = "Loops recalculated from Time"
            else:
                t = time_from_loops(p["Loops"], p["Buffer size"],
                                    sr, p["Delay"])
                self._set_var("Time", f"{t:.6f}")
                msg = "Time recalculated from Loops"

            if self.status_line:
                self.status_line.update_status(msg)

        except Exception as exc:
            if self.status_line:
                self.status_line.update_status(f"Recalc error: {exc}")
            else:
                raise