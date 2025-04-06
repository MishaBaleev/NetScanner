# ********************
# телеграмм-бот, написанный при помощи библиотеки Python3 telebot
# имя бота в телеграмме - https://t.me/AnyoneHome_bot
# ********************

import telebot
from telebot import types
from .Scanner import Scanner
from threading import Thread
import time

class Bot:
    def __init__(self, config:dict, logger:object) -> None:
        token = "7434966649:AAGEeSA9cUrXNzZZfXOWMEaXxBL8KrlqkJo"
        self.bot = telebot.TeleBot(token)
        self.chat_id = config["chat_id"]
        self.logger = logger
        self.register_handlers()
        self.scanner = Scanner(logger=self.logger, mac_table=config["mac_table"], sendMessage=self.sendMessage)
        self.scan_thread = None

    def sendMessage(self, message:str) -> None:
        self.bot.send_message(self.chat_id, message)
        self.logger.logger.info(f"Sended message to {self.chat_id}")

    def register_handlers(self) -> None:
        self.bot.message_handler(commands=['start'])(self.start)
        self.bot.message_handler(content_types=['text'])(self.send_text)

    def start(self, message) -> None:
        reply = types.ReplyKeyboardMarkup(resize_keyboard=True)
        manual = types.KeyboardButton("Anyone Home?")
        reply.add(manual)
        self.bot.send_message(self.chat_id, "Hello, push button to know who is in home", reply_markup=reply)

    def send_text(self, message) -> None:
        self.logger.logger.info(f"Recieve message with text - {message.text} from chat - {message.chat.id}")
        msg = message.text
        match msg:
            case "Anyone Home?":
                self.scanner.scanNetwork()
    
    def timeScanning(self) -> None:
        while 1:
            self.sendMessage("scanning")
            time.sleep(1)

    def start_polling(self) -> None:
        self.logger.logger.info(f"Starting bot")
        # Thread(target=self.timeScanning, daemon=True).start()
        self.bot.polling(non_stop=True)