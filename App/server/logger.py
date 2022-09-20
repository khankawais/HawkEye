import logging
from config import log_file

LOG_FORMAT="%(levelname)s %(asctime)s - %(message)s"
logging.basicConfig(filename=log_file,level=logging.INFO,format=LOG_FORMAT)
logging.getLogger("pika").setLevel(logging.CRITICAL)
genlog=logging.getLogger()
