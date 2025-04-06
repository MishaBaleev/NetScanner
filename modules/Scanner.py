import socket
import subprocess
import re
from concurrent.futures import ThreadPoolExecutor
import platform

class Scanner:
    def __init__(self, logger:object, mac_table:dict, sendMessage) -> None:
        self.logger = logger 
        self.mac_table = mac_table
        self.logger.logger.info(f"Scanner object created")
        self.sendMessage = sendMessage

    def getlocalIP(self) -> str or None:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
            s.close()
            return local_ip
        except Exception as err:
            self.logger.logger.critical(f"Ошибка при получении локального IP: {err}")
            return None
    
    def ping(self, ip:str) -> str or None:
        try:
            if platform.system() == "Windows": command = ["ping", "-n", "1", "-w", "1000", ip]
            else: command = ["ping", "-c", "1", "-W", "1", ip]
            response = subprocess.run(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            if response.returncode == 0:
                return ip
        except Exception as err:
            self.logger.logger.critical(f"Ошибка при ping {ip}: {err}")
        return None
    
    def pingSweep(self, ip_prefix:str) -> list:
        active_ips = []
        ip_range = [f"{ip_prefix}.{i}" for i in range(1, 255)] 
        with ThreadPoolExecutor(max_workers=100) as executor:
            results = executor.map(self.ping, ip_range)
        active_ips = [ip for ip in results if ip is not None]
        return active_ips
    
    def getArpTable(self) -> dict:
        arp_table = {}
        try:
            if platform.system() == "Windows": command = ["arp", "-a"]
            else: command = ["arp", "-n"]
            result = subprocess.run(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            lines = result.stdout.splitlines()
            for line in lines:
                match = re.search(r"(\d+\.\d+\.\d+\.\d+)\s+([0-9a-f\-:]{17})", line, re.IGNORECASE)
                if match:
                    ip = match.group(1)
                    mac = match.group(2).replace("-", ":").replace(".", ":")
                    arp_table[ip] = mac
        except Exception as err:
            self.logger.logger.critical(f"Ошибка при получении ARP-таблицы: {err}")
        return arp_table

    def getMacTable(self) -> dict:
        self.logger.logger.info(f"Start scanning...")
        local_ip = self.getlocalIP()
        if not local_ip:
            self.logger.logger.critical("No local IP-address")
            return None
        ip_prefix = ".".join(local_ip.split(".")[:-1])
        self.sendMessage(f"Сканирую сеть: {ip_prefix}.1-{ip_prefix}.254")
        active_ips = self.pingSweep(ip_prefix)
        arp_table = self.getArpTable()
        print(active_ips)
        print(arp_table)
        # message = "---Devices in the network---\n"
        # message += ("-"*30+"\n")
        result_dict = {}
        for ip in active_ips:
            mac = arp_table.get(ip, "Undefinite")
            result_dict[ip] = mac
        return result_dict
        # self.sendMessage(message)

    def scanNetwork(self) -> None:
        mac_table = self.getMacTable()
