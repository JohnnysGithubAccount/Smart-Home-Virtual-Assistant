import logging
import os


def setup_logger(name: str, log_file: str, log_dir: str, level=logging.INFO):
    """Setup individual logger that writes to a specific file inside log_dir"""
    os.makedirs(log_dir, exist_ok=True)  # make sure folder exists
    log_path = os.path.join(log_dir, log_file)

    logger = logging.getLogger(name)
    logger.setLevel(level)

    if not logger.handlers:  # prevent duplicate handlers
        fh = logging.FileHandler(log_path)
        fh.setLevel(level)

        formatter = logging.Formatter(
            "%(asctime)s - %(levelname)s - %(message)s", "%Y-%m-%d %H:%M:%S"
        )
        fh.setFormatter(formatter)

        logger.addHandler(fh)

    return logger


def init_loggers(log_dir: str):
    """Initialize all loggers with the same base folder"""
    plan_logger = setup_logger("PlanLogger", "plans.log", log_dir, logging.INFO)
    function_logger = setup_logger("FunctionLogger", "functions.log", log_dir, logging.INFO)
    error_logger = setup_logger("ErrorLogger", "errors.log", log_dir, logging.ERROR)
    return plan_logger, function_logger, error_logger
