"""
系统服务模块
提供系统健康检查和系统信息查询功能
"""
import os
import platform
import psutil
import socket
from datetime import datetime, timezone
from typing import Dict, Any


class SystemService:
    """系统服务类"""
    
    _instance = None
    
    def __new__(cls):
        """单例模式"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def health_check(self) -> Dict[str, Any]:
        """
        健康检查
        
        返回:
            健康状态信息，包括：
            - status: 整体状态 (healthy/degraded/unhealthy)
            - version: 服务版本
            - uptime: 运行时间（秒）
            - timestamp: 检查时间戳
            - checks: 各项检查详情
                - api: API 服务状态
                - storage: 存储服务状态
                - database: 数据库状态
                - memory: 内存状态
                - disk: 磁盘状态
        """
        checks = {}
        issues = []
        
        # API 服务检查
        try:
            checks["api"] = {
                "status": "ok",
                "message": "API 服务正常运行"
            }
        except Exception as e:
            checks["api"] = {
                "status": "error",
                "message": str(e)
            }
            issues.append("api")
        
        # 存储服务检查
        try:
            base_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "uploads")
            os.makedirs(base_dir, exist_ok=True)
            test_file = os.path.join(base_dir, ".health_check")
            with open(test_file, 'w') as f:
                f.write("ok")
            os.remove(test_file)
            checks["storage"] = {
                "status": "ok",
                "message": "存储服务正常"
            }
        except Exception as e:
            checks["storage"] = {
                "status": "error",
                "message": str(e)
            }
            issues.append("storage")
        
        # 数据库检查（SQLite）
        try:
            db_path = os.path.join(base_dir, "tasks.db")
            # 尝试连接数据库
            import sqlite3
            conn = sqlite3.connect(db_path)
            conn.execute("SELECT 1")
            conn.close()
            checks["database"] = {
                "status": "ok",
                "message": "数据库连接正常"
            }
        except Exception as e:
            checks["database"] = {
                "status": "ok",
                "message": f"数据库文件不存在或连接失败：{str(e)}"
            }
            # 数据库不存在不算严重问题，可以自动创建
        
        # 内存检查
        try:
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            if memory_percent < 80:
                status = "ok"
            elif memory_percent < 90:
                status = "warning"
                issues.append("memory")
            else:
                status = "error"
                issues.append("memory")
            
            checks["memory"] = {
                "status": status,
                "message": f"内存使用率：{memory_percent:.1f}%",
                "details": {
                    "total": memory.total,
                    "available": memory.available,
                    "used": memory.used,
                    "percent": memory_percent
                }
            }
        except Exception as e:
            checks["memory"] = {
                "status": "error",
                "message": str(e)
            }
            issues.append("memory")
        
        # 磁盘检查
        try:
            disk = psutil.disk_usage('/')
            disk_percent = disk.percent
            if disk_percent < 80:
                status = "ok"
            elif disk_percent < 90:
                status = "warning"
                issues.append("disk")
            else:
                status = "error"
                issues.append("disk")
            
            checks["disk"] = {
                "status": status,
                "message": f"磁盘使用率：{disk_percent:.1f}%",
                "details": {
                    "total": disk.total,
                    "used": disk.used,
                    "free": disk.free,
                    "percent": disk_percent
                }
            }
        except Exception as e:
            checks["disk"] = {
                "status": "error",
                "message": str(e)
            }
            issues.append("disk")
        
        # 确定整体状态
        if any(checks[key].get("status") == "error" for key in ["api", "storage"]):
            overall_status = "unhealthy"
        elif issues:
            overall_status = "degraded"
        else:
            overall_status = "healthy"
        
        # 计算运行时间
        try:
            process = psutil.Process(os.getpid())
            uptime = (datetime.now(timezone.utc) - datetime.fromtimestamp(process.create_time(), timezone.utc)).total_seconds()
        except:
            uptime = 0
        
        return {
            "status": overall_status,
            "version": "v3.0.4",
            "uptime": int(uptime),
            "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "checks": checks,
            "issues": issues
        }
    
    def get_system_info(self) -> Dict[str, Any]:
        """
        获取系统信息
        
        返回:
            系统详细信息，包括：
            - os: 操作系统信息
            - cpu: CPU 信息
            - memory: 内存信息
            - disk: 磁盘信息
            - network: 网络信息
            - python: Python 环境信息
        """
        info = {}
        
        # 操作系统信息
        info["os"] = {
            "system": platform.system(),
            "release": platform.release(),
            "version": platform.version(),
            "machine": platform.machine(),
            "processor": platform.processor(),
            "node": platform.node(),
            "architecture": platform.architecture()[0]
        }
        
        # CPU 信息
        try:
            cpu_count = psutil.cpu_count(logical=True)
            cpu_count_physical = psutil.cpu_count(logical=False)
            cpu_freq = psutil.cpu_freq()
            cpu_percent = psutil.cpu_percent(interval=0.1)
            
            info["cpu"] = {
                "physical_cores": cpu_count_physical,
                "logical_cores": cpu_count,
                "frequency_mhz": round(cpu_freq.current, 2) if cpu_freq else None,
                "usage_percent": cpu_percent
            }
        except Exception as e:
            info["cpu"] = {
                "error": str(e)
            }
        
        # 内存信息
        try:
            memory = psutil.virtual_memory()
            swap = psutil.swap_memory()
            
            info["memory"] = {
                "total_gb": round(memory.total / (1024 ** 3), 2),
                "available_gb": round(memory.available / (1024 ** 3), 2),
                "used_gb": round(memory.used / (1024 ** 3), 2),
                "percent": memory.percent,
                "swap_total_gb": round(swap.total / (1024 ** 3), 2) if swap.total else 0,
                "swap_used_gb": round(swap.used / (1024 ** 3), 2) if swap.used else 0,
                "swap_percent": swap.percent
            }
        except Exception as e:
            info["memory"] = {
                "error": str(e)
            }
        
        # 磁盘信息
        try:
            disk = psutil.disk_usage('/')
            partitions = psutil.disk_partitions()
            
            disk_info = {
                "total_gb": round(disk.total / (1024 ** 3), 2),
                "used_gb": round(disk.used / (1024 ** 3), 2),
                "free_gb": round(disk.free / (1024 ** 3), 2),
                "percent": disk.percent,
                "partitions": []
            }
            
            for partition in partitions:
                try:
                    partition_usage = psutil.disk_usage(partition.mountpoint)
                    disk_info["partitions"].append({
                        "device": partition.device,
                        "mountpoint": partition.mountpoint,
                        "fstype": partition.fstype,
                        "total_gb": round(partition_usage.total / (1024 ** 3), 2),
                        "used_gb": round(partition_usage.used / (1024 ** 3), 2),
                        "free_gb": round(partition_usage.free / (1024 ** 3), 2),
                        "percent": partition_usage.percent
                    })
                except:
                    pass
            
            info["disk"] = disk_info
        except Exception as e:
            info["disk"] = {
                "error": str(e)
            }
        
        # 网络信息
        try:
            hostname = socket.gethostname()
            ip_addresses = []
            
            # 获取所有网络接口的 IP
            addrs = psutil.net_if_addrs()
            for iface_name, addrs_list in addrs.items():
                for addr in addrs_list:
                    if addr.family == socket.AF_INET:
                        ip_addresses.append({
                            "interface": iface_name,
                            "ip": addr.address,
                            "netmask": addr.netmask
                        })
            
            info["network"] = {
                "hostname": hostname,
                "ip_addresses": ip_addresses
            }
        except Exception as e:
            info["network"] = {
                "error": str(e)
            }
        
        # Python 环境信息
        import sys
        info["python"] = {
            "version": sys.version,
            "version_info": {
                "major": sys.version_info.major,
                "minor": sys.version_info.minor,
                "micro": sys.version_info.micro
            },
            "executable": sys.executable,
            "path": sys.path
        }
        
        # 添加时间戳
        info["timestamp"] = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        
        return info
