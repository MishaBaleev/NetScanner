from modules.Logger import Logger
from modules.TGBot import Bot
import ujson as json


def loadConfig(logger:object) -> dict or None:
    try:
        with open("./config.json", "r") as config: 
            logger.logger.info(f"Successfully loaded config-file")
            return json.loads(config.read())
    except Exception as err:
        logger.logger.critical(f"Error while loading config, err - {err}")
        return None


if __name__ == "__main__":
    logger_obj = Logger()
    logger_obj.start()
    config = loadConfig(logger=logger_obj)
    if config:
        bot = Bot(config=config, logger=logger_obj)
        bot.start_polling()