import socket
import subprocess
import re
from concurrent.futures import ThreadPoolExecutor
import platform

class Scanner:
    def __init__(self, logger:object, mac_table:dict, sendMessage) -> None:
        self.logger = logger 
        self.mac_table = mac_table
        self.sendMessage = sendMessage

    def getlocalIP(self) -> str or None:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
            s.close()
            return local_ip
        except Exception as err:
            self.logger.logger.critical(f"No local IP: {err}\n")
            return None
    
    def getMacFromArp(self, ip:str) -> str:
        try:
            if platform.system() == "Windows": command = ["arp", "-a", ip]
            else: command = ["arp", "-n", ip]
            result = subprocess.run(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            match = re.search(r"([0-9a-f]{2}[:-]){5}[0-9a-f]{2}", result.stdout, re.IGNORECASE)
            if match:
                mac = match.group(0).replace("-", ":").replace(".", ":")
                return mac
        except Exception as err:
            self.logger.logger.critical(f"No MAC {ip}: {err}")
        return "Undef"
    
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
            self.logger.logger.critical(f"Ping Error {ip}: {err}\n")
        return None
    
    def pingSweep(self, ip_prefix:str) -> list:
        active_ips = []
        ip_range = [f"{ip_prefix}.{i}" for i in range(1, 255)]
        def pingWithErrors(ip):
            try:
                return self.ping(ip)
            except Exception as err:
                self.logger.logger.critical(f"Error while checking IP {ip}: {err}\n")
                return None
        with ThreadPoolExecutor(max_workers=1000) as executor: results = executor.map(pingWithErrors, ip_range)
        active_ips = [ip for ip in results if ip is not None]
        return active_ips
    
    def getHostname(self, ip:str) -> str:
        try:
            hostname, _, _ = socket.gethostbyaddr(ip)
            return hostname
        except socket.herror:
            return "Undef"
        except Exception as err:
            self.logger.logger.critical(f"Error while getting hostname {ip}: {err}\n")
            return "Undef"

    def getDevices(self) -> list or None:
        local_ip = self.getlocalIP()
        if not local_ip:
            self.logger.logger.critical("No local IP address\n")
            return None
        ip_prefix = ".".join(local_ip.split(".")[:-1])
        def getIP(ip_prefix) -> list:
            active_ips = self.pingSweep(ip_prefix)
            devices = []
            for ip in active_ips:
                mac = self.getMacFromArp(ip)
                hostname = self.getHostname(ip)
                devices.append({"mac": mac, "hostname": hostname, "ip": ip})
            return devices
        devices = getIP(ip_prefix)
        devices += getIP(ip_prefix)
        return devices
    
    def findElementFromtable(self, key:str, value:str) -> dict:
        for item in self.mac_table:
            if item[key] == value: return item
    
    def checkMacTable(self, devices:list) -> list:
        result = []
        auth_mac_list = [item["mac"] for item in self.mac_table]
        auth_hostname_list = [item["hostname"] for item in self.mac_table]
        ip_devices = []
        for device in devices:
            if (device["mac"] in auth_mac_list) and not(device["ip"] in ip_devices): 
                result.append({
                    "ip": device["ip"], 
                    "mac": device["mac"], 
                    "hostname": device["hostname"], 
                    "auth_name": self.findElementFromtable(key="mac", value=device["mac"])["id_name"],
                    "is_in_table": True
                })
                ip_devices.append(device["ip"])
                continue
            if (device["hostname"] in auth_hostname_list) and not(device["ip"] in ip_devices): 
                result.append({
                    "ip": device["ip"], 
                    "mac": device["mac"], 
                    "hostname": device["hostname"], 
                    "auth_name": self.findElementFromtable(key="hostname", value=device["hostname"])["id_name"],
                    "is_in_table": True
                })
                ip_devices.append(device["ip"])
                continue
            if not(device["ip"] in ip_devices):
                result.append({
                    "ip": device["ip"], 
                    "mac": device["mac"], 
                    "hostname": device["hostname"], 
                    "auth_name": "Undef",
                    "is_in_table": False
                })
                ip_devices.append(device["ip"])
        return result

    def scanNetwork(self) -> None:
        devices = self.getDevices()
        checked_devices = self.checkMacTable(devices=devices)
        self.sendMessage(checked_devices, False)
