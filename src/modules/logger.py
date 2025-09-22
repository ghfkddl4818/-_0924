
import logging, sys
from logging.handlers import RotatingFileHandler
from pathlib import Path
from datetime import datetime

class GuiLogHandler(logging.Handler):
    def __init__(self, callback):
        super().__init__()
        self.callback = callback
    def emit(self, record):
        try:
            msg = self.format(record)
            level = record.levelname
            self.callback(level, msg)
        except Exception:
            pass

def setup_logging(config: dict):
    log_folder = Path(config["paths"]["log_folder"])
    log_folder.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d")
    logfile = log_folder / f"run_{ts}.log"

    logger = logging.getLogger("UAS")
    logger.setLevel(getattr(logging, config["logging"]["level"], logging.INFO))

    fmt = logging.Formatter(config["logging"]["format"], datefmt=config["logging"]["date_format"])

    fh = RotatingFileHandler(logfile, maxBytes=config["logging"]["max_size_mb"]*1024*1024, backupCount=config["logging"]["max_files"])
    fh.setFormatter(fmt)
    logger.addHandler(fh)

    if config["logging"]["console_output"]:
        ch = logging.StreamHandler(sys.stdout); ch.setFormatter(fmt); logger.addHandler(ch)

    # buffer for GUI (not strictly needed)
    gui_buffer = []
    return logger, gui_buffer
