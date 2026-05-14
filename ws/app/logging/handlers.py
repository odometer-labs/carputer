import logging
import time
import os

t = time.localtime()
fmt_time = time.strftime("%Y-%m-%d_%H;%M;%S", t)

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Create the folder if it does not exists
os.makedirs("./app/logging/logs", exist_ok=True)

filename = f"./app/logging/logs/{fmt_time}.log"
file_handler = logging.FileHandler(filename, mode="a", encoding="utf-8")
file_handler.setLevel(logging.DEBUG)
formatter = logging.Formatter("%(asctime)s - %(filename)s:%(lineno)d - %(levelname)s: %(message)s")
file_handler.setFormatter(formatter)

logger.addHandler(file_handler)