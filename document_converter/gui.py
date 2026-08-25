"""GUI for document converter using Tkinter."""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path
from document_converter.converter import DocumentConverter
import sys
import subprocess


class ConverterApp:
    """Main application window for the document converter."""

    def __upported_formats(self):
        """Return supported formats grouped by category."""
        return {
            "Text": ["txt", "md", "markdown"],
            "Documents": ["docx", "pdf"],
            "Spreadsheets": ["xlsx"],
            "Presentations": ["pptx"],
            "Web": ["html"],
        }

    def __init__(self, root):
        self.root = root
        self.root.title("Universal Document Converter")
        self.root.geometry("600x400")

        self.converter = DocumentConverter()

        # Check for optional dependencies and offer to install them
        try:
            self._check_optional_dependencies()
        except Exception:
            # don't block the UI on check failures
            pass

        self._create_widgets()
        self._setup_layout()

    def _create_widgets(self):
        """Create all UI widgets."""
        # Input file section
        self.input_frame = ttk.LabelFrame(self.root, text="Input File")
        self.input_path_var = tk.StringVar()
        self.input_entry = ttk.Entry(self.input_frame, textvariable=self.input_path_var, width=50)
        self.input_button = ttk.Button(self.input_frame, text="Browse", command=self._browse_input)

        # Output format section
        self.output_frame = ttk.LabelFrame(self.root, text="Output Format")
        self.output_format_var = tk.StringVar()
        self.output_combo = ttk.Combobox(self.output_frame, textvariable=self.output_format_var, state="readonly")
        self.convert_button = ttk.Button(self.output_frame, text="Convert", command=self._convert)

        # Status section
        self.status_var = tk.StringVar(value="Ready")
        self.status_label = ttk.Label(self.root, textvariable=self.status_var, foreground="blue")

    def _setup_layout(self):
        """Arrange widgets using grid geometry manager."""
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)

        # Input frame
        self.input_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=10)
        self.input_frame.columnconfigure(0, weight=1)
        self.input_entry.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
        self.input_button.grid(row=0, column=1, padx=5, pady=5)

        # Output frame
        self.output_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=5)
        self.output_frame.columnconfigure(0, weight=1)
        self.output_combo.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
        self.convert_button.grid(row=0, column=1, padx=5, pady=5)

        # Status label
        self.status_label.grid(row=2, column=0, pady=10)

        # Initialize format options on startup
        self._update_output_formats()

    def _browse_input(self):
        """Open file dialog to select input file."""
        filetypes = [
            ("All supported", "*.txt *.docx *.xlsx *.pptx *.pdf *.html *.md *.markdown"),
            ("Text files", "*.txt"),
            ("Word documents", "*.docx"),
            ("Excel sheets", "*.xlsx"),
            ("PowerPoint", "*.pptx"),
            ("PDF", "*.pdf"),
            ("HTML", "*.html"),
            ("Markdown", "*.md *.markdown"),
            ("All files", "*.*"),
        ]
        filepath = filedialog.askopenfilename(filetypes=filetypes)
        if filepath:
            self.input_path_var.set(filepath)
            self._update_output_formats()

    def _update_output_formats(self):
        """Update the output format combo based on input file."""
        input_path = self.input_path_var.get()
        if not input_path:
            self.output_combo["values"] = []
            self.output_format_var.set("")
            return

        input_ext = Path(input_path).suffix.lstrip(".")
        # Map extension to format name
        format_name = self.converter.EXTENSION_MAP.get(input_ext, input_ext)

        # Get available conversions for this format
        conversions = self.converter.CONVERSIONS.get(format_name, [])
        # Also add the format itself if reading
        all_targets = list(set(conversions))
        # If there are no direct conversions, check if an external converter is available
        if not all_targets:
            # If the converter can use external tools, offer common target formats and inform the user
            if self.converter.can_use_external():
                common_targets = ["docx", "pdf", "html", "txt", "markdown"]
                self.output_combo["values"] = common_targets
                self.output_format_var.set(common_targets[0])
                messagebox.showinfo(
                    "Using external converter",
                    f"Files with extension '.{input_ext}' will be converted using an external tool (LibreOffice or pypandoc).\nAvailable output formats: {', '.join(common_targets)}"
                )
                return

            supported_inputs = sorted(set(self.converter.EXTENSION_MAP.keys()))
            messagebox.showwarning(
                "Unsupported format",
                f"Files with extension '.{input_ext}' are not supported.\nSupported input extensions: {', '.join(supported_inputs)}"
            )
            self.output_combo["values"] = []
            self.output_format_var.set("")
            return

        self.output_combo["values"] = all_targets
        if all_targets:
            self.output_format_var.set(all_targets[0])

    def _convert(self):
        """Perform the document conversion."""
        input_path = self.input_path_var.get()
        output_format = self.output_format_var.get()

        if not input_path:
            messagebox.showerror("Error", "Please select an input file first.")
            return

        if not output_format:
            messagebox.showerror("Error", "Please select an output format.")
            return

        # Generate output path
        input_file = Path(input_path)
        output_path = input_file.parent / (input_file.stem + "." + output_format)

        try:
            self.status_var.set("Converting...")
            self.root.update()
            self.converter.convert(str(input_path), str(output_path), output_format)
            self.status_var.set(f"Success: {output_path.name}")
            messagebox.showinfo("Success", f"Converted successfully!\nSaved to:\n{output_path}")
        except Exception as e:
            self.status_var.set("Error occurred")
            messagebox.showerror("Error", f"Conversion failed:\n{e}")

    def _check_optional_dependencies(self):
        """Check for optional conversion dependencies and offer to install them."""
        optional_packages = {
            "pypdf": "PDF support",
            "openpyxl": "Excel (.xlsx) support",
            "pptx": "PowerPoint (.pptx) support (python-pptx)",
            "pypandoc": "pandoc-based conversions (pypandoc)",
        }

        missing = []
        for pkg in optional_packages.keys():
            try:
                __import__(pkg)
            except Exception:
                missing.append(pkg)

        if not missing:
            return

        names = [optional_packages.get(p, p) for p in missing]
        msg = (
            "Optional packages are missing which enable additional conversions:\n\n"
            + "\n".join(f"- {pkg}: {optional_packages.get(pkg)}" for pkg in missing)
            + "\n\nInstall them now? (This runs pip in your active Python interpreter)")

        install = messagebox.askyesno("Missing optional packages", msg)
        if not install:
            return

        # Run pip install for the missing packages using the current interpreter
        try:
            cmd = [sys.executable, "-m", "pip", "install"] + missing
            proc = subprocess.run(cmd, check=False)
            if proc.returncode == 0:
                messagebox.showinfo("Install complete", "Optional packages installed. Restart the app if needed.")
            else:
                messagebox.showwarning("Install failed", "Installing packages failed. See terminal for details.")
        except Exception as ex:
            messagebox.showerror("Install error", f"Failed to run installer: {ex}")


def main():
    """Run the GUI application."""
    root = tk.Tk()
    app = ConverterApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()


def main():
    """Run the GUI application."""
    root = tk.Tk()
    app = ConverterApp(root)
    root.mainloop()