from app.shared.runtime.logger import logger

logger.debug("This is a debug message")
logger.info("This is an info message")
logger.warning("This is a warning message")
logger.error("This is an error message")

name = "andy"
age = 18

logger.info(f"My name is {name} and I am {age} years old")

try:
    a = 1/0
except Exception as e:
    logger.exception(f"This is a critical message {e}")
