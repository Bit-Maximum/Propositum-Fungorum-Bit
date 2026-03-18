import logging


logging.basicConfig(
    level=logging.INFO,
    datefmt="%Y-%m-%d %H:%M:%S",
    format="%(levelname)s:[%(asctime)s]/%(name)s/ %(funcName)s %(module)s:%(lineno)d - %(message)s"
)

logger = logging.getLogger('rec-trimmer')
