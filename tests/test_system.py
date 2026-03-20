"""
系统模块单元测试
测试用例覆盖：
- test_health_check_success: 健康检查 - 正常流程
- test_health_check_structure: 健康检查 - 数据结构验证
- test_health_check_status: 健康检查 - 状态字段验证
- test_system_info_success: 系统信息 - 正常流程
- test_system_info_structure: 系统信息 - 数据结构验证
- test_system_info_os_info: 系统信息 - 操作系统信息验证
"""
import pytest
import os
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi.testclient import TestClient
from src.api.main import app
from src.services.system_service import SystemService

client = TestClient(app)


class TestHealthCheck:
    """健康检查接口测试"""
    
    def test_health_check_success(self):
        """test_health_check_success: 健康检查 - 正常流程"""
        response = client.get("/api/v1/health")
        
        assert response.status_code == 200
        result = response.json()
        assert result["code"] == 200
        assert "data" in result
        assert "message" in result
        assert result["message"] == "健康检查完成"
    
    def test_health_check_structure(self):
        """test_health_check_structure: 健康检查 - 数据结构验证"""
        response = client.get("/api/v1/health")
        
        assert response.status_code == 200
        result = response.json()
        data = result["data"]
        
        # 验证顶层字段
        assert "status" in data
        assert "version" in data
        assert "uptime" in data
        assert "timestamp" in data
        assert "checks" in data
        assert "issues" in data
        
        # 验证 checks 字段包含所有检查项
        checks = data["checks"]
        assert "api" in checks
        assert "storage" in checks
        assert "database" in checks
        assert "memory" in checks
        assert "disk" in checks
        
        # 验证每个检查项的结构
        for check_name, check_data in checks.items():
            assert "status" in check_data
            assert "message" in check_data
    
    def test_health_check_status(self):
        """test_health_check_status: 健康检查 - 状态字段验证"""
        response = client.get("/api/v1/health")
        
        assert response.status_code == 200
        result = response.json()
        data = result["data"]
        
        # 验证状态值在预期范围内
        assert data["status"] in ["healthy", "degraded", "unhealthy"]
        
        # 验证版本号
        assert data["version"] == "v3.0.4"
        
        # 验证运行时间是非负整数
        assert isinstance(data["uptime"], int)
        assert data["uptime"] >= 0
        
        # 验证时间戳格式
        assert isinstance(data["timestamp"], str)
        assert "T" in data["timestamp"]
        assert data["timestamp"].endswith("Z")
        
        # 验证 issues 是列表
        assert isinstance(data["issues"], list)


class TestSystemInfo:
    """系统信息接口测试"""
    
    def test_system_info_success(self):
        """test_system_info_success: 系统信息 - 正常流程"""
        response = client.get("/api/v1/system/info")
        
        assert response.status_code == 200
        result = response.json()
        assert result["code"] == 200
        assert "data" in result
        assert "message" in result
        assert result["message"] == "获取成功"
    
    def test_system_info_structure(self):
        """test_system_info_structure: 系统信息 - 数据结构验证"""
        response = client.get("/api/v1/system/info")
        
        assert response.status_code == 200
        data = response.json()["data"]
        
        # 验证顶层字段
        assert "os" in data
        assert "cpu" in data
        assert "memory" in data
        assert "disk" in data
        assert "network" in data
        assert "python" in data
        assert "timestamp" in data
    
    def test_system_info_os_info(self):
        """test_system_info_os_info: 系统信息 - 操作系统信息验证"""
        response = client.get("/api/v1/system/info")
        
        assert response.status_code == 200
        data = response.json()["data"]
        os_info = data["os"]
        
        # 验证操作系统字段
        assert "system" in os_info
        assert "release" in os_info
        assert "version" in os_info
        assert "machine" in os_info
        assert "processor" in os_info
        assert "node" in os_info
        assert "architecture" in os_info
        
        # 验证系统类型
        assert os_info["system"] in ["Linux", "Windows", "Darwin"]
        
        # 验证 CPU 信息
        cpu_info = data["cpu"]
        assert "physical_cores" in cpu_info or "error" in cpu_info
        assert "logical_cores" in cpu_info or "error" in cpu_info
        
        # 验证内存信息
        memory_info = data["memory"]
        if "error" not in memory_info:
            assert "total_gb" in memory_info
            assert "available_gb" in memory_info
            assert "used_gb" in memory_info
            assert "percent" in memory_info
        
        # 验证磁盘信息
        disk_info = data["disk"]
        if "error" not in disk_info:
            assert "total_gb" in disk_info
            assert "used_gb" in disk_info
            assert "free_gb" in disk_info
            assert "percent" in disk_info
        
        # 验证网络信息
        network_info = data["network"]
        if "error" not in network_info:
            assert "hostname" in network_info
            assert "ip_addresses" in network_info
        
        # 验证 Python 信息
        python_info = data["python"]
        assert "version" in python_info
        assert "version_info" in python_info
        assert "executable" in python_info
        assert "path" in python_info
        
        # 验证 version_info 结构
        version_info = python_info["version_info"]
        assert "major" in version_info
        assert "minor" in version_info
        assert "micro" in version_info


class TestSystemService:
    """系统服务类测试"""
    
    def test_system_service_singleton(self):
        """test_system_service_singleton: 系统服务 - 单例模式验证"""
        service1 = SystemService()
        service2 = SystemService()
        
        # 验证是同一个实例
        assert service1 is service2
    
    def test_system_service_health_check(self):
        """test_system_service_health_check: 系统服务 - 健康检查方法"""
        service = SystemService()
        result = service.health_check()
        
        # 验证返回结构
        assert isinstance(result, dict)
        assert "status" in result
        assert "version" in result
        assert "uptime" in result
        assert "timestamp" in result
        assert "checks" in result
        assert "issues" in result
        
        # 验证状态值
        assert result["status"] in ["healthy", "degraded", "unhealthy"]
    
    def test_system_service_get_system_info(self):
        """test_system_service_get_system_info: 系统服务 - 获取系统信息方法"""
        service = SystemService()
        result = service.get_system_info()
        
        # 验证返回结构
        assert isinstance(result, dict)
        assert "os" in result
        assert "cpu" in result
        assert "memory" in result
        assert "disk" in result
        assert "network" in result
        assert "python" in result
        assert "timestamp" in result
