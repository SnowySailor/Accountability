import logging
import discord
import sys

from .utils import LoggerWriter

logger = None

def init_logger():
    global logger
    logger = logging.getLogger('discord')
    logger.setLevel(logging.DEBUG)
    sys.stderr = LoggerWriter(logger.error)
    handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
    handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
    logger.addHandler(handler)

def logtofile(msg: str, level: str = 'debug'):
    getattr(logger, level)(msg)
