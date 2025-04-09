# ********************
# телеграмм-бот, написанный при помощи библиотеки Python3 telebot
# имя бота в телеграмме - https://t.me/AnyoneHome_bot
# ********************

import telebot
from telebot import types
from .Scanner import Scanner
from threading import Thread
import time
import os
import io

class Bot:
    def __init__(self, config:dict, logger:object) -> None:
        token = "7434966649:AAGEeSA9cUrXNzZZfXOWMEaXxBL8KrlqkJo"
        self.bot = telebot.TeleBot(token)
        self.chat_id = config["chat_id"]
        self.logger = logger
        self.scanner = Scanner(logger=self.logger, mac_table=config["mac_table"], sendMessage=self.sendMessage)
        self.scan_thread = None
        self.refresh_count = 0

    def keepAlive(self):
        while True:
            try:
                self.bot.get_me()
                # self.bot.polling(non_stop=True)
            except Exception as e:
                self.logger.logger.error(f"Error during keep-alive: {e}\n")
            time.sleep(60)  

    def sendMessage(self, message:list, is_auto:bool) -> None:
        self.logger.logger.info(f"---Scanning---")
        for m in message:
            line = f'ip - {m["ip"]};\nmac - {m["mac"]};\nhostname - {m["hostname"]};\nauth_name - {m["auth_name"]};\nis_registered - {m["is_in_table"]}'
            if not is_auto: self.bot.send_message(self.chat_id, line)
            self.logger.logger.info(line.replace("\n", " "))
        self.logger.logger.info("---------------\n")

    def register_handlers(self) -> None:
        self.bot.message_handler(commands=['start'])(self.start)
        self.bot.message_handler(content_types=['text'])(self.send_text)

    def start(self, message) -> None:
        reply = types.ReplyKeyboardMarkup(resize_keyboard=True)
        button_1 = types.KeyboardButton("Anyone Home?")
        button_2 = types.KeyboardButton("Get Last Log")
        reply.add(button_1, button_2)
        self.bot.send_message(self.chat_id, "Hello, push button to know who is in home", reply_markup=reply)

    def send_text(self, message) -> None:
        msg = message.text
        self.bot.send_chat_action(self.chat_id, action="typing")
        match msg:
            case "Anyone Home?":
                self.scanner.scanNetwork()
            case "Get Last Log":
                with open(os.getcwd()+"/logs/scanning_log.txt", "rb") as file: 
                    self.logger.logger.info(f"user want to get log")
                    self.bot.send_document(self.chat_id, file)
                self.logger.refresh()
    
    def timeScanning(self) -> None:
        while 1:
            scan_res = self.scanner.checkMacTable(devices=self.scanner.getDevices())
            self.sendMessage(message=scan_res, is_auto=True)
            time.sleep(600)

    def start_polling(self) -> None:
        Thread(target=self.timeScanning, daemon=True).start()
        Thread(target=self.keepAlive, daemon=True).start()
        self.register_handlers()
        self.bot.infinity_polling()