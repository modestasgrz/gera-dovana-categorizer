"""Main entrypoint for Product Categorizer."""

import tkinter as tk

from loguru import logger

from src.config import load_config
from src.gui import ProductCategorizerApp, prompt_for_config
from src.logging_utils import setup_logging


def main() -> None:
    """Main application entry point."""
    # Setup logging
    setup_logging()
    logger.info("Starting Product Categorizer")

    # Check if config exists
    config = load_config()
    if not config:
        logger.warning("Configuration not found, prompting user")
        config = prompt_for_config()

        if not config:
            logger.info("User cancelled configuration, exiting")
            return

    # Launch main GUI
    root = tk.Tk()
    ProductCategorizerApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
