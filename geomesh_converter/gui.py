"""tkinter GUI for GeoMesh Converter."""

from __future__ import annotations

import os
import threading
import traceback
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, scrolledtext, ttk

from converter import landxml_to_obj, obj_to_landxml


class GeoMeshConverterApp(tk.Tk):
    """Simple desktop GUI for LandXML/OBJ conversion."""

    def __init__(self) -> None:
        super().__init__()
        self.title("GeoMesh Converter v1.0")
        self.geometry("640x460")
        self.resizable(True, True)

        self.direction = tk.StringVar(value="landxml_to_obj")
        self.input_path = tk.StringVar()
        self.output_path = tk.StringVar()

        self._build_widgets()

    def _build_widgets(self) -> None:
        container = ttk.Frame(self, padding=16)
        container.pack(fill=tk.BOTH, expand=True)

        direction_frame = ttk.LabelFrame(container, text="変換方向", padding=10)
        direction_frame.pack(fill=tk.X, pady=(0, 12))
        ttk.Radiobutton(
            direction_frame,
            text="LandXML → OBJ（Blenderへ）",
            variable=self.direction,
            value="landxml_to_obj",
            command=self._on_direction_changed,
        ).pack(anchor=tk.W)
        ttk.Radiobutton(
            direction_frame,
            text="OBJ → LandXML（Blenderから戻す）",
            variable=self.direction,
            value="obj_to_landxml",
            command=self._on_direction_changed,
        ).pack(anchor=tk.W)

        form = ttk.Frame(container)
        form.pack(fill=tk.X, pady=(0, 12))
        ttk.Label(form, text="入力ファイル:").grid(row=0, column=0, sticky=tk.W, padx=(0, 8), pady=4)
        ttk.Entry(form, textvariable=self.input_path).grid(row=0, column=1, sticky=tk.EW, pady=4)
        ttk.Button(form, text="参照", command=self._browse_input).grid(row=0, column=2, padx=(8, 0), pady=4)
        ttk.Label(form, text="出力先:").grid(row=1, column=0, sticky=tk.W, padx=(0, 8), pady=4)
        ttk.Entry(form, textvariable=self.output_path).grid(row=1, column=1, sticky=tk.EW, pady=4)
        ttk.Button(form, text="参照", command=self._browse_output).grid(row=1, column=2, padx=(8, 0), pady=4)
        form.columnconfigure(1, weight=1)

        self.convert_button = ttk.Button(container, text="変換実行", command=self._start_conversion)
        self.convert_button.pack(fill=tk.X, pady=(0, 12))

        self.log = scrolledtext.ScrolledText(container, height=12, state=tk.DISABLED)
        self.log.pack(fill=tk.BOTH, expand=True)
        self.log.tag_configure("error", foreground="red")
        self.log.tag_configure("warning", foreground="darkorange")

    def _on_direction_changed(self) -> None:
        if self.input_path.get():
            self._set_default_output(self.input_path.get())

    def _browse_input(self) -> None:
        if self.direction.get() == "landxml_to_obj":
            filetypes = [("LandXML/XML", "*.xml"), ("All files", "*.*")]
        else:
            filetypes = [("OBJ", "*.obj"), ("All files", "*.*")]
        selected = filedialog.askopenfilename(title="入力ファイルを選択", filetypes=filetypes)
        if selected:
            self.input_path.set(selected)
            self._set_default_output(selected)

    def _browse_output(self) -> None:
        extension = ".obj" if self.direction.get() == "landxml_to_obj" else ".xml"
        filetypes = [(extension.upper().lstrip("."), f"*{extension}"), ("All files", "*.*")]
        initial = self.output_path.get() or self._default_output_path(self.input_path.get())
        selected = filedialog.asksaveasfilename(
            title="出力先を選択",
            defaultextension=extension,
            initialfile=Path(initial).name if initial else None,
            initialdir=str(Path(initial).parent) if initial else None,
            filetypes=filetypes,
        )
        if selected:
            self.output_path.set(selected)

    def _default_output_path(self, input_path: str) -> str:
        if not input_path:
            return ""
        extension = ".obj" if self.direction.get() == "landxml_to_obj" else ".xml"
        return str(Path(input_path).with_suffix(extension))

    def _set_default_output(self, input_path: str) -> None:
        self.output_path.set(self._default_output_path(input_path))

    def _append_log(self, message: str, tag: str | None = None) -> None:
        self.log.configure(state=tk.NORMAL)
        self.log.insert(tk.END, message + "\n", tag)
        self.log.see(tk.END)
        self.log.configure(state=tk.DISABLED)

    def _start_conversion(self) -> None:
        input_path = self.input_path.get().strip()
        output_path = self.output_path.get().strip()
        if not input_path:
            messagebox.showwarning("入力エラー", "入力ファイルを選択してください")
            return
        if not output_path:
            messagebox.showwarning("入力エラー", "出力先を選択してください")
            return

        self.convert_button.configure(state=tk.DISABLED, text="変換中...")
        self._append_log("変換を開始しました")
        thread = threading.Thread(target=self._run_conversion, args=(input_path, output_path), daemon=True)
        thread.start()

    def _run_conversion(self, input_path: str, output_path: str) -> None:
        try:
            converter = landxml_to_obj.convert if self.direction.get() == "landxml_to_obj" else obj_to_landxml.convert
            result = converter(input_path, output_path)
            self.after(0, self._handle_success, result, output_path)
        except Exception as exc:  # noqa: BLE001 - GUI needs a catch-all to report failures.
            details = "".join(traceback.format_exception_only(type(exc), exc)).strip()
            self.after(0, self._handle_error, details)

    def _handle_success(self, result: dict, output_path: str) -> None:
        for surface in result.get("surfaces", []):
            self._append_log(
                f"Surface: {surface['name']} / 頂点数: {surface['vertices']} / フェイス数: {surface['faces']}"
            )
        for warning in result.get("warnings", []):
            self._append_log("警告: " + warning, "warning")
        self._append_log(f"出力: {os.path.abspath(output_path)}")
        self._append_log("変換が完了しました")
        self.convert_button.configure(state=tk.NORMAL, text="変換実行")
        messagebox.showinfo("完了", "変換が完了しました")

    def _handle_error(self, message: str) -> None:
        self._append_log("エラー: " + message, "error")
        self.convert_button.configure(state=tk.NORMAL, text="変換実行")
        messagebox.showerror("エラー", message)
