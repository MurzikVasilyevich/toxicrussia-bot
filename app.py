import logging.config
import sys
import time

import settings as s
from chunk import Chunk
from publish_helper import PublishManager
import generator

logging.config.fileConfig('logging.conf')
logger = logging.getLogger('app.py')


def main():
    logging.info("Starting main")
    generator.Generator()

    for i in range(1, s.POST.BATCH_SIZE + 1):
        if s.LOCAL.CLEAR_EACH_RUN:
            generator.Generator()
        logging.info(f"Starting batch {i}")
        chunk = Chunk(s.POST.GENERATE_RECORDS)
        logging.info("Starting Generation is done")
        if s.POST.CREATE_AUDIO and not s.POST.GENERATE_RECORDS:
            PublishManager(chunk)
        logging.info(f"Finished batch {i}")
        logging.info(f"Sleeping for {s.POST.SLEEP_TIME} seconds")
        time.sleep(s.POST.SLEEP_TIME)

    logging.info("Finished main")
    sys.exit(0)


if __name__ == '__main__':
    sys.exit(main())
