"""GUI application for Product Categorizer."""

import asyncio
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from loguru import logger

from src.config import ACTIVE_CONFIG, AVAILABLE_MODELS, Config, load_config, save_config
from src.core import process_csv_async


def prompt_for_config(root: tk.Tk | None = None) -> Config | None:  # noqa: PLR0915, ARG001
    """Show modal dialog to collect API key and model name.

    Args:
        root: Parent tkinter window (unused, kept for compatibility)

    Returns:
        Config object if successfully saved, None if user cancelled
    """
    # Load current config to prefill values
    current_config = load_config()

    # Create standalone window instead of Toplevel to avoid macOS withdrawn parent issues
    dialog = tk.Tk()
    dialog.title("Configuration Required")
    dialog.geometry("500x300")
    dialog.resizable(False, False)

    # Center the dialog
    dialog.update_idletasks()
    x = (dialog.winfo_screenwidth() // 2) - (dialog.winfo_width() // 2)
    y = (dialog.winfo_screenheight() // 2) - (dialog.winfo_height() // 2)
    dialog.geometry(f"+{x}+{y}")

    # Content
    content_frame = tk.Frame(dialog, padx=30, pady=20)
    content_frame.pack(fill=tk.BOTH, expand=True)

    tk.Label(
        content_frame,
        text="OpenAI API Configuration",
        font=("Helvetica", 16, "bold"),
    ).pack(pady=(0, 10))

    tk.Label(
        content_frame,
        text="Please enter your OpenAI API key and select a model:",
        font=("Helvetica", 10),
    ).pack(pady=(0, 20))

    # API Key field
    tk.Label(
        content_frame,
        text="API Key:",
        font=("Helvetica", 10, "bold"),
    ).pack(anchor=tk.W)
    api_key_entry = tk.Entry(content_frame, font=("Helvetica", 10), show="*", width=50)
    # Prefill API key if config exists
    if current_config:
        api_key_entry.insert(0, current_config.openai_api_key)
    api_key_entry.pack(fill=tk.X, pady=(5, 15))

    # Model selection
    tk.Label(
        content_frame,
        text="Model:",
        font=("Helvetica", 10, "bold"),
    ).pack(anchor=tk.W)
    # Use current model if config exists, otherwise default to first model
    default_model = current_config.model_name if current_config else AVAILABLE_MODELS[0]
    model_var = tk.StringVar(value=default_model)
    model_combo = ttk.Combobox(
        content_frame,
        textvariable=model_var,
        values=AVAILABLE_MODELS,
        state="readonly",
        font=("Helvetica", 10),
    )
    model_combo.pack(fill=tk.X, pady=(5, 20))

    result_config: Config | None = None

    def on_save() -> None:
        nonlocal result_config
        api_key = api_key_entry.get().strip()
        model = model_combo.get()  # Get directly from combobox instead of StringVar

        logger.debug(f"Selected model from combobox: '{model}'")

        if not api_key:
            messagebox.showerror("Error", "API key cannot be empty", parent=dialog)
            return

        try:
            config = Config(openai_api_key=api_key, model_name=model)
            logger.debug(f"Config object created with model: '{config.model_name}'")
            asyncio.run(save_config(config))
            result_config = config
            logger.info("Configuration saved and verified successfully")
            dialog.quit()
        except ValueError as e:
            logger.error(f"API key verification failed: {e}")
            messagebox.showerror("Error", f"API key verification failed:\n\n{e}", parent=dialog)
        except Exception as e:
            logger.error(f"Failed to save configuration: {e}")
            messagebox.showerror("Error", f"Failed to save configuration:\n\n{e}", parent=dialog)

    save_button = tk.Button(
        content_frame,
        text="Save Configuration",
        command=on_save,
        font=("Helvetica", 11, "bold"),
        padx=20,
        pady=10,
    )
    save_button.pack()

    def on_close() -> None:
        if not result_config:
            if messagebox.askyesno(
                "Warning",
                "API key is required to use this application. Exit anyway?",
                parent=dialog,
            ):
                dialog.quit()
        else:
            dialog.quit()

    dialog.protocol("WM_DELETE_WINDOW", on_close)
    dialog.mainloop()
    dialog.destroy()

    return result_config


class ProductCategorizerApp:
    """Main GUI application for Product Categorizer."""

    def __init__(self, root: tk.Tk) -> None:
        """Initialize the application window.

        Args:
            root: Tkinter root window
        """
        self.root = root
        self.root.title("Product Categorizer")
        self.root.geometry("700x500")
        self.root.resizable(False, False)

        # Application state
        self.selected_file: Path | None = None
        self.is_processing = False

        # Build UI
        self._build_ui()

    def _build_ui(self) -> None:
        """Build the main user interface."""
        # Header
        header_frame = tk.Frame(self.root, height=80)
        header_frame.pack(fill=tk.X)
        header_frame.pack_propagate(False)

        title_label = tk.Label(
            header_frame,
            text="Product Categorizer",
            font=("Helvetica", 24, "bold"),
        )
        title_label.pack(pady=20)

        # Main content area
        content_frame = tk.Frame(self.root, padx=40, pady=30)
        content_frame.pack(fill=tk.BOTH, expand=True)

        # File selection section
        file_section = tk.LabelFrame(
            content_frame,
            text="1. Select Input CSV File",
            font=("Helvetica", 12, "bold"),
            padx=20,
            pady=15,
        )
        file_section.pack(fill=tk.X, pady=(0, 20))

        self.file_label = tk.Label(
            file_section,
            text="No file selected",
            font=("Helvetica", 10),
            wraplength=550,
        )
        self.file_label.pack(pady=(0, 10))

        select_button = tk.Button(
            file_section,
            text="Browse Files...",
            command=self._on_select_file,
            font=("Helvetica", 10),
            padx=20,
            pady=8,
        )
        select_button.pack()

        # Status section
        status_section = tk.LabelFrame(
            content_frame,
            text="2. Processing Status",
            font=("Helvetica", 12, "bold"),
            padx=20,
            pady=15,
        )
        status_section.pack(fill=tk.BOTH, expand=True, pady=(0, 20))

        self.status_text = tk.Text(
            status_section,
            height=8,
            font=("Courier", 9),
            state=tk.DISABLED,
        )
        self.status_text.pack(fill=tk.BOTH, expand=True)

        self._update_status("Ready. Please select a CSV file to begin.")

        # Action buttons
        button_frame = tk.Frame(content_frame)
        button_frame.pack(fill=tk.X)

        self.run_button = tk.Button(
            button_frame,
            text="Run Categorization",
            command=self._on_run_processing,
            font=("Helvetica", 12, "bold"),
            padx=30,
            pady=12,
            state=tk.DISABLED,
        )
        self.run_button.pack(side=tk.LEFT, padx=(0, 10))

        settings_button = tk.Button(
            button_frame,
            text="Settings",
            command=self._on_settings,
            font=("Helvetica", 10),
            padx=20,
            pady=12,
        )
        settings_button.pack(side=tk.LEFT)

    def _on_settings(self) -> None:
        """Show settings dialog."""
        prompt_for_config(self.root)

    def _on_select_file(self) -> None:
        """Handle file selection."""
        file_path = filedialog.askopenfilename(
            title="Select Input CSV File",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
        )

        if file_path:
            self.selected_file = Path(file_path)
            self.file_label.config(text=str(self.selected_file))
            self.run_button.config(state=tk.NORMAL)
            self._update_status(f"File selected: {self.selected_file.name}")
            logger.info(f"File selected: {self.selected_file}")

    def _update_status(self, message: str) -> None:
        """Update status display.

        Args:
            message: Status message to display
        """
        self.status_text.config(state=tk.NORMAL)
        self.status_text.insert(tk.END, f"{message}\n")
        self.status_text.see(tk.END)
        self.status_text.config(state=tk.DISABLED)

    def _on_run_processing(self) -> None:
        """Handle Run button click."""
        if not self.selected_file:
            messagebox.showwarning("No File", "Please select a CSV file first")
            return

        if self.is_processing:
            messagebox.showinfo("Processing", "Processing is already in progress")
            return

        # Start processing in background thread
        self.is_processing = True
        self.run_button.config(state=tk.DISABLED, text="Processing...")
        self._update_status(f"\n{'=' * 50}")
        self._update_status(f"Starting categorization of {self.selected_file.name}...")
        self._update_status(f"Using model: {ACTIVE_CONFIG.model_name}")

        def run_in_thread() -> None:
            try:
                self._validate_and_process()
            except Exception as e:
                logger.error(f"Processing failed: {e}")
                self.root.after(0, self._on_processing_error, str(e))

        thread = threading.Thread(target=run_in_thread, daemon=True)
        thread.start()

    def _validate_and_process(self) -> None:
        """Validate file selection and run processing."""
        if not self.selected_file:
            msg = "No file selected"
            raise ValueError(msg)

        # Run async CSV processing
        output_path, summary = asyncio.run(process_csv_async(self.selected_file))

        # Update UI on success (schedule on main thread)
        self.root.after(0, self._on_processing_complete, output_path, summary)

    def _on_processing_complete(self, output_path: Path, summary: dict[str, int]) -> None:
        """Handle successful processing completion.

        Args:
            output_path: Path to output CSV file
            summary: Processing summary statistics
        """
        self.is_processing = False
        self.run_button.config(state=tk.NORMAL, text="Run Categorization")

        self._update_status("\n✓ Categorization complete!")
        self._update_status(f"Output file: {output_path}")
        self._update_status("\nSummary:")
        self._update_status(f"  Total rows: {summary['total']}")
        self._update_status(f"  Categorized: {summary['categorized']}")
        self._update_status(f"  Unknown: {summary['unknown']}")

        messagebox.showinfo(
            "Success",
            f"Categorization complete!\n\n"
            f"Total: {summary['total']} rows\n"
            f"Categorized: {summary['categorized']}\n"
            f"Unknown: {summary['unknown']}\n\n"
            f"Output saved to:\n{output_path}",
        )

    def _on_processing_error(self, error_message: str) -> None:
        """Handle processing error.

        Args:
            error_message: Error message to display
        """
        self.is_processing = False
        self.run_button.config(state=tk.NORMAL, text="Run Categorization")

        self._update_status(f"\n✗ Error: {error_message}")
        messagebox.showerror("Processing Error", f"An error occurred:\n\n{error_message}")
