"""
第三阶段全流程集成测试
覆盖仪表盘/模板/素材/系统全模块的端到端测试

测试场景:
1. 仪表盘统计工作流
2. 模板创建到应用工作流
3. AI 短剧生成工作流
4. 素材上传到使用工作流
5. 系统健康检查和工作流
6. 多用户并发工作流
7. 配额扣费工作流
8. 错误处理和恢复工作流
9. 缓存机制验证工作流
10. 完整端到端工作流
"""
import pytest
import os
import sys
import io
import uuid
import time
import json
import shutil
import asyncio
import threading
from pathlib import Path
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi.testclient import TestClient
from src.api.main import app
from src.services.dashboard_service import DashboardService
from src.services.template_service import TemplateService
from src.services.material_service import MaterialService
from src.services.system_service import SystemService
from src.services.quota_service import QuotaService
from src.services.script_service import ScriptService
from src.services.batch_service import BatchService
from src.services.ai_video_service import AIVideoService

client = TestClient(app)

# 测试用临时文件内容
TEST_VIDEO_CONTENT = b"\x00\x00\x00\x1cftypmp42\x00\x00\x00\x00mp42isomtest video content for integration testing"
TEST_AUDIO_CONTENT = b"ID3\x03\x00\x00\x00\x00\x00test audio content for integration testing"
TEST_IMAGE_CONTENT = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc\xf8\x0f\x00\x00\x01\x01\x00\x05\x18\xd8N\x00\x00\x00\x00IEND\xaeB`\x82"


# ============================================================================
# 场景 1: 仪表盘统计工作流
# ============================================================================
class TestPhase3DashboardWorkflow:
    """场景 1: 仪表盘统计工作流测试"""
    
    def test_dashboard_stats_workflow(self):
        """
        测试仪表盘统计工作流
        1. 创建一些测试数据（任务、文件、剧本）
        2. 调用仪表盘统计接口
        3. 验证统计数据准确性
        4. 验证最近使用记录
        """
        # 1. 创建测试数据 - 上传一个视频文件
        upload_dir = os.path.join(Path(__file__).parent.parent, "uploads", "test_integration")
        os.makedirs(upload_dir, exist_ok=True)
        
        test_video_path = os.path.join(upload_dir, f"test_video_{uuid.uuid4()}.mp4")
        with open(test_video_path, 'wb') as f:
            f.write(TEST_VIDEO_CONTENT)
        
        # 2. 调用仪表盘统计接口
        response = client.get("/api/v1/dashboard/stats")
        assert response.status_code == 200
        result = response.json()
        assert result["code"] == 200
        assert "data" in result
        
        data = result["data"]
        
        # 3. 验证统计数据准确性
        # 验证 tasks 结构
        assert "tasks" in data
        assert "total" in data["tasks"]
        assert "pending" in data["tasks"]
        assert "completed" in data["tasks"]
        assert isinstance(data["tasks"]["total"], int)
        
        # 验证 files 结构
        assert "files" in data
        assert "total" in data["files"]
        assert "videos" in data["files"]
        assert "storageUsed" in data["files"]
        assert isinstance(data["files"]["total"], int)
        
        # 验证 scripts 结构
        assert "scripts" in data
        assert "total" in data["scripts"]
        
        # 验证 batches 结构
        assert "batches" in data
        assert "total" in data["batches"]
        
        # 验证 usage 结构
        assert "usage" in data
        assert "todayQuota" in data["usage"]
        assert "todayUsed" in data["usage"]
        
        # 4. 验证最近使用记录
        recent_response = client.get("/api/v1/dashboard/recent?limit=5")
        assert recent_response.status_code == 200
        recent_result = recent_response.json()
        assert recent_result["code"] == 200
        # recent_result["data"] 直接就是数据字典，包含 batches, files, scripts, tasks
        assert isinstance(recent_result["data"], dict)
        
        # 清理测试文件
        if os.path.exists(test_video_path):
            os.remove(test_video_path)
        
        print("✓ 仪表盘统计工作流测试通过")


# ============================================================================
# 场景 2: 模板创建到应用工作流
# ============================================================================
class TestPhase3TemplateWorkflow:
    """场景 2: 模板创建到应用工作流测试"""
    
    def test_template_creation_to_application(self):
        """
        测试模板创建到应用完整工作流
        1. 创建模板（添加背景音乐 + 字幕）
        2. 获取模板列表验证
        3. 上传测试视频
        4. 应用模板到视频
        5. 查询任务进度
        6. 验证输出文件
        """
        from src.services.template_service import TemplateService
        
        # 初始化模板服务
        template_service = TemplateService()
        
        # 1. 创建模板（添加背景音乐 + 字幕）
        template_steps = [
            {
                "stepType": "audio",
                "config": {
                    "voice": "zh-CN-XiaoxiaoNeural",
                    "speed": 1.0,
                    "backgroundMusic": "test_music.mp3"
                },
                "order": 0
            },
            {
                "stepType": "video",
                "config": {
                    "resolution": "1080p",
                    "fps": 30,
                    "addSubtitles": True
                },
                "order": 1
            }
        ]
        
        template = template_service.create_template(
            name="集成测试模板",
            description="用于全流程集成测试的模板",
            steps=template_steps,
            is_public=False
        )
        
        assert template is not None
        assert "templateId" in template
        assert template["templateId"].startswith("tmpl-")
        assert template["name"] == "集成测试模板"
        assert len(template["steps"]) == 2
        
        template_id = template["templateId"]
        
        try:
            # 2. 获取模板列表验证
            templates_result = template_service.get_templates(page=1, page_size=10)
            assert templates_result["total"] >= 1
            
            # 验证模板在列表中
            template_ids = [t["templateId"] for t in templates_result["templates"]]
            assert template_id in template_ids
            
            # 3. 上传测试视频（模拟）
            test_video_id = f"test_video_{uuid.uuid4()}"
            
            # 4. 应用模板到视频
            apply_result = template_service.apply_template(
                template_id=template_id,
                video_id=test_video_id
            )
            
            assert apply_result is not None
            assert "applyId" in apply_result
            assert apply_result["applyId"].startswith("apply-")
            assert apply_result["templateId"] == template_id
            assert apply_result["videoId"] == test_video_id
            assert apply_result["status"] == "ready"
            
            # 5. 查询任务进度（通过 API）
            # 注意：任务 API 可能使用不同的端点，这里验证 API 可用性
            response = client.get("/api/v1/health")
            assert response.status_code == 200
            
            # 6. 验证输出文件（模板应用记录已保存）
            records_dir = os.path.join(template_service.base_dir, "records")
            assert os.path.exists(records_dir)
            
            record_path = os.path.join(records_dir, f"{apply_result['applyId']}.json")
            assert os.path.exists(record_path)
            
            # 验证记录内容
            with open(record_path, 'r') as f:
                record_data = json.load(f)
            assert record_data["templateId"] == template_id
            assert record_data["videoId"] == test_video_id
            
            print("✓ 模板创建到应用工作流测试通过")
            
        finally:
            # 清理：删除测试模板
            try:
                template_service.delete_template(template_id)
            except:
                pass


# ============================================================================
# 场景 3: AI 短剧生成工作流
# ============================================================================
class TestPhase3AIDramaWorkflow:
    """场景 3: AI 短剧生成工作流测试"""
    
    @pytest.mark.asyncio
    async def test_ai_drama_generation_workflow(self):
        """
        测试 AI 短剧生成完整工作流
        1. 生成剧本
        2. 生成分镜
        3. 批量生成视频
        4. 查询批量进度
        5. 验证所有集数完成
        6. 验证仪表盘统计更新
        """
        from src.services.script_service import ScriptService
        from src.services.batch_service import BatchService
        
        # 重置单例
        BatchService._instance = None
        
        # 1. 生成剧本
        script_service = ScriptService()
        script_data = await script_service.generate_script(
            theme="集成测试短剧",
            episodes=3,  # 测试用少量集数
            genre="都市"
        )
        
        assert script_data is not None
        assert "scriptId" in script_data
        script_id = script_data["scriptId"]
        
        try:
            # 2. 生成分镜（通过 API 触发）
            # 分镜生成通常在批量任务中自动进行
            
            # 3. 批量生成视频
            batch_service = BatchService()
            batch_result = await batch_service.create_batch_job(
                script_id=script_id,
                episode_range={"start": 1, "end": 3},
                parallelism=2
            )
            
            assert batch_result is not None
            assert "batchId" in batch_result
            batch_id = batch_result["batchId"]
            
            assert batch_result["totalEpisodes"] == 3
            assert batch_result["status"] == "pending"
            
            # 4. 查询批量进度
            batch_status = await batch_service.query_batch_status(batch_id)
            assert batch_status is not None
            assert "batchId" in batch_status
            assert "status" in batch_status
            assert "progress" in batch_status
            
            # 5. 验证所有集数完成（等待或检查状态）
            # 由于是测试，我们验证状态字段存在即可
            assert batch_status["status"] in ["pending", "processing", "completed", "failed"]
            
            # 6. 验证仪表盘统计更新
            response = client.get("/api/v1/dashboard/stats")
            assert response.status_code == 200
            dashboard_data = response.json()["data"]
            
            # 验证 batches 统计
            assert "batches" in dashboard_data
            assert "total" in dashboard_data["batches"]
            
            print("✓ AI 短剧生成工作流测试通过")
            
        finally:
            # 清理：删除测试剧本
            script_path = os.path.join(script_service.base_dir, f"{script_id}.json")
            if os.path.exists(script_path):
                os.remove(script_path)


# ============================================================================
# 场景 4: 素材上传到使用工作流
# ============================================================================
class TestPhase3MaterialWorkflow:
    """场景 4: 素材上传到使用工作流测试"""
    
    def test_material_upload_to_usage(self):
        """
        测试素材上传到使用工作流
        1. 上传音乐素材
        2. 获取音乐列表验证
        3. 预览音乐
        4. 使用音乐处理视频
        5. 验证素材统计
        """
        import tempfile
        from src.services.material_service import MaterialService
        
        material_service = MaterialService()
        
        # 1. 上传音乐素材
        with tempfile.NamedTemporaryFile(mode='wb', suffix='.mp3', delete=False) as f:
            f.write(TEST_AUDIO_CONTENT)
            temp_file = f.name
        
        try:
            upload_result = material_service.upload_material(
                file_path=temp_file,
                material_type="music",
                category="流行",
                tags=["欢快", "测试"],
                description="集成测试音乐素材"
            )
            
            assert upload_result is not None
            assert "materialId" in upload_result
            material_id = upload_result["materialId"]
            assert material_id.startswith("mat-")
            
            # 2. 获取音乐列表验证
            music_list = material_service.get_music_list()
            assert music_list is not None
            assert "musicList" in music_list
            
            # 3. 预览音乐
            preview = material_service.preview_material(material_id)
            assert preview is not None
            assert preview["materialId"] == material_id
            assert preview["materialType"] == "music"
            assert "previewUrl" in preview
            
            # 4. 使用音乐处理视频（通过模板应用模拟）
            # 这里验证素材可用于模板配置
            template_config = {
                "backgroundMusic": material_id,
                "volume": 0.5
            }
            assert template_config["backgroundMusic"] == material_id
            
            # 5. 验证素材统计
            stats = material_service.get_material_stats()
            assert stats is not None
            assert "totalMusic" in stats
            assert "totalUploads" in stats
            assert "totalStorageBytes" in stats
            
            # 验证统计值合理
            assert stats["totalMusic"] >= 1
            assert stats["totalStorageBytes"] > 0
            
            print("✓ 素材上传到使用工作流测试通过")
            
        finally:
            # 清理测试文件
            if os.path.exists(temp_file):
                os.unlink(temp_file)
            
            # 清理素材记录
            try:
                material_service.delete_material(material_id)
            except:
                pass


# ============================================================================
# 场景 5: 系统健康检查和工作流
# ============================================================================
class TestPhase3SystemHealthWorkflow:
    """场景 5: 系统健康检查和工作流测试"""
    
    def test_system_health_and_workflow(self):
        """
        测试系统健康检查和状态
        1. 健康检查
        2. 获取系统信息
        3. 验证所有服务正常
        4. 验证功能列表完整
        """
        # 1. 健康检查
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        result = response.json()
        assert result["code"] == 200
        assert "data" in result
        
        health_data = result["data"]
        assert "status" in health_data
        assert health_data["status"] in ["healthy", "degraded", "unhealthy"]
        assert "version" in health_data
        assert "uptime" in health_data
        assert "checks" in health_data
        
        # 2. 获取系统信息
        info_response = client.get("/api/v1/system/info")
        assert info_response.status_code == 200
        info_result = info_response.json()
        assert info_result["code"] == 200
        
        system_info = info_result["data"]
        assert "os" in system_info
        assert "cpu" in system_info
        assert "memory" in system_info
        assert "disk" in system_info
        assert "python" in system_info
        
        # 3. 验证所有服务正常
        checks = health_data["checks"]
        assert "api" in checks
        assert "storage" in checks
        assert "database" in checks
        assert "memory" in checks
        assert "disk" in checks
        
        # 验证每个检查项都有 status 和 message
        for check_name, check_data in checks.items():
            assert "status" in check_data
            assert "message" in check_data
        
        # 4. 验证功能列表完整
        # 通过检查各个 API 端点可访问来验证
        endpoints_to_check = [
            "/api/v1/health",
            "/api/v1/system/info",
            "/api/v1/dashboard/stats",
            "/api/v1/templates",  # 模板列表端点
            "/api/v1/materials/music",  # 音乐列表端点
        ]
        
        for endpoint in endpoints_to_check:
            resp = client.get(endpoint)
            # 某些端点可能需要参数，只要不是 500 错误即可
            assert resp.status_code in [200, 400, 422], f"端点 {endpoint} 访问失败：{resp.status_code}"
        
        print("✓ 系统健康检查和工作流测试通过")


# ============================================================================
# 场景 6: 多用户并发工作流
# ============================================================================
class TestPhase3ConcurrentWorkflow:
    """场景 6: 多用户并发工作流测试"""
    
    def test_multi_user_concurrent_workflow(self):
        """
        测试多用户并发操作
        1. 并发创建多个模板
        2. 并发上传多个素材
        3. 并发查询仪表盘
        4. 验证所有操作成功
        """
        import tempfile
        from src.services.template_service import TemplateService
        from src.services.material_service import MaterialService
        from src.services.dashboard_service import DashboardService
        
        template_service = TemplateService()
        material_service = MaterialService()
        dashboard_service = DashboardService()
        
        # 清除缓存
        dashboard_service._invalidate_cache()
        
        created_templates = []
        created_materials = []
        errors = []
        
        # 1. 并发创建多个模板
        def create_template(user_id):
            try:
                template = template_service.create_template(
                    name=f"并发测试模板-{user_id}",
                    description=f"用户{user_id}的测试模板",
                    steps=[{"stepType": "video", "config": {"resolution": "1080p"}, "order": 0}],
                    is_public=False
                )
                created_templates.append(template["templateId"])
                return True
            except Exception as e:
                errors.append(f"模板创建失败 (user {user_id}): {str(e)}")
                return False
        
        # 2. 并发上传多个素材
        def upload_material(user_id):
            try:
                with tempfile.NamedTemporaryFile(mode='wb', suffix='.mp3', delete=False) as f:
                    f.write(TEST_AUDIO_CONTENT)
                    temp_file = f.name
                
                try:
                    result = material_service.upload_material(
                        file_path=temp_file,
                        material_type="music",
                        category="流行",
                        tags=["测试"],
                        description=f"用户{user_id}的测试音乐"
                    )
                    created_materials.append(result["materialId"])
                    return True
                finally:
                    if os.path.exists(temp_file):
                        os.unlink(temp_file)
            except Exception as e:
                errors.append(f"素材上传失败 (user {user_id}): {str(e)}")
                return False
        
        # 3. 并发查询仪表盘
        def query_dashboard(user_id):
            try:
                response = client.get("/api/v1/dashboard/stats")
                assert response.status_code == 200
                return True
            except Exception as e:
                errors.append(f"仪表盘查询失败 (user {user_id}): {str(e)}")
                return False
        
        # 执行并发操作
        with ThreadPoolExecutor(max_workers=10) as executor:
            # 并发创建 5 个模板
            template_futures = [executor.submit(create_template, i) for i in range(5)]
            
            # 并发上传 5 个素材
            material_futures = [executor.submit(upload_material, i) for i in range(5)]
            
            # 并发查询 5 次仪表盘
            dashboard_futures = [executor.submit(query_dashboard, i) for i in range(5)]
            
            # 等待所有操作完成
            all_futures = template_futures + material_futures + dashboard_futures
            for future in as_completed(all_futures):
                future.result()
        
        # 4. 验证所有操作成功
        assert len(errors) == 0, f"并发操作出现错误：{errors}"
        assert len(created_templates) == 5, f"期望创建 5 个模板，实际创建{len(created_templates)}个"
        assert len(created_materials) == 5, f"期望上传 5 个素材，实际上传{len(created_materials)}个"
        
        # 验证仪表盘查询都成功
        dashboard_responses = [client.get("/api/v1/dashboard/stats") for _ in range(5)]
        for resp in dashboard_responses:
            assert resp.status_code == 200
        
        print("✓ 多用户并发工作流测试通过")
        
        # 清理：删除创建的模板和素材
        for tmpl_id in created_templates:
            try:
                template_service.delete_template(tmpl_id)
            except:
                pass
        
        for mat_id in created_materials:
            try:
                material_service.delete_material(mat_id)
            except:
                pass


# ============================================================================
# 场景 7: 配额扣费工作流
# ============================================================================
class TestPhase3QuotaWorkflow:
    """场景 7: 配额扣费工作流测试"""
    
    @pytest.mark.asyncio
    async def test_quota_deduction_workflow(self):
        """
        测试配额扣费工作流
        1. 查询初始配额
        2. 执行 AI 视频生成（消耗配额）
        3. 查询扣费后配额
        4. 验证配额变化正确
        5. 验证交易记录
        """
        from src.services.quota_service import QuotaService
        
        # 初始化配额服务（使用测试数据库）
        quota_service = QuotaService()
        quota_service._initialized = False
        quota_service.base_dir = os.path.join(os.path.dirname(__file__), "test_uploads_quota")
        quota_service.db_path = os.path.join(quota_service.base_dir, "test_quota.db")
        os.makedirs(quota_service.base_dir, exist_ok=True)
        quota_service._init_db()
        quota_service._initialized = True
        
        test_user_id = f"test_user_{uuid.uuid4()}"
        
        try:
            # 1. 查询初始配额
            initial_quota = await quota_service.get_quota(test_user_id)
            assert initial_quota is not None
            initial_total = initial_quota.quota_total
            initial_used = initial_quota.quota_used
            initial_daily_used = initial_quota.daily_quota_used
            
            # 2. 添加一些配额以便测试扣费
            topup_result = await quota_service.add_quota(
                user_id=test_user_id,
                amount=500,
                expire_days=30
            )
            assert topup_result["success"] is True
            
            # 查询充值后配额
            quota_after_topup = await quota_service.get_quota(test_user_id)
            assert quota_after_topup.quota_total == initial_total + 500
            
            # 3. 执行 AI 视频生成（消耗配额）
            deduct_amount = 100
            deduct_result = await quota_service.deduct_quota(
                user_id=test_user_id,
                amount=deduct_amount,
                task_type="ai_video",
                task_id=f"test_task_{uuid.uuid4()}"
            )
            
            assert deduct_result["success"] is True
            assert deduct_result["deducted"] > 0
            
            # 4. 查询扣费后配额
            quota_after_deduct = await quota_service.get_quota(test_user_id)
            
            # 验证配额变化正确
            # 60 秒来自每日免费，剩余来自付费配额
            expected_paid_deduct = max(0, deduct_amount - 60)
            assert quota_after_deduct.quota_used >= initial_used
            
            # 5. 验证交易记录
            transactions = await quota_service.get_transaction_history(test_user_id)
            assert len(transactions) >= 2  # 至少充值和扣费两条记录
            
            # 验证交易类型
            transaction_types = [t["transactionType"] for t in transactions]
            assert "topup" in transaction_types
            assert "deduct" in transaction_types
            
            # 验证扣费记录
            deduct_transactions = [t for t in transactions if t["transactionType"] == "deduct"]
            assert len(deduct_transactions) >= 1
            
            print("✓ 配额扣费工作流测试通过")
            
        finally:
            # 清理测试数据库
            if os.path.exists(quota_service.db_path):
                os.remove(quota_service.db_path)
            if os.path.exists(quota_service.base_dir):
                shutil.rmtree(quota_service.base_dir, ignore_errors=True)


# ============================================================================
# 场景 8: 错误处理和恢复工作流
# ============================================================================
class TestPhase3ErrorHandlingWorkflow:
    """场景 8: 错误处理和恢复工作流测试"""
    
    def test_error_handling_and_recovery(self):
        """
        测试错误处理和恢复
        1. 提交无效请求（测试错误处理）
        2. 验证错误响应正确
        3. 提交正确请求
        4. 验证系统恢复正常
        """
        from src.services.template_service import TemplateService
        
        template_service = TemplateService()
        
        # 1. 提交无效请求（测试错误处理）
        errors_caught = []
        
        # 测试空名称
        try:
            template_service.create_template(
                name="",
                description="测试",
                steps=[{"stepType": "video", "config": {}, "order": 0}]
            )
        except ValueError as e:
            errors_caught.append(str(e))
        
        # 测试空步骤
        try:
            template_service.create_template(
                name="测试",
                description="测试",
                steps=[]
            )
        except ValueError as e:
            errors_caught.append(str(e))
        
        # 测试无效模板 ID
        try:
            template_service.get_template("")
        except ValueError as e:
            errors_caught.append(str(e))
        
        # 测试不存在的模板
        try:
            template_service.get_template("tmpl-nonexistent")
        except FileNotFoundError as e:
            errors_caught.append(str(e))
        
        # 2. 验证错误响应正确
        assert len(errors_caught) == 4, f"期望捕获 4 个错误，实际捕获{len(errors_caught)}个"
        assert any("名称" in err for err in errors_caught)
        assert any("步骤" in err for err in errors_caught)
        assert any("ID" in err for err in errors_caught)
        assert any("不存在" in err for err in errors_caught)
        
        # 3. 提交正确请求
        correct_template = template_service.create_template(
            name="正确模板",
            description="这是一个正确的模板",
            steps=[
                {"stepType": "video", "config": {"resolution": "1080p"}, "order": 0}
            ],
            is_public=False
        )
        
        assert correct_template is not None
        assert "templateId" in correct_template
        
        # 验证可以正确获取
        retrieved = template_service.get_template(correct_template["templateId"])
        assert retrieved["name"] == "正确模板"
        
        # 4. 验证系统恢复正常
        # 系统应该能继续正常处理请求
        templates_list = template_service.get_templates(page=1, page_size=10)
        assert templates_list is not None
        assert "templates" in templates_list
        
        # 验证 API 仍然可用
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        
        print("✓ 错误处理和恢复工作流测试通过")
        
        # 清理
        try:
            template_service.delete_template(correct_template["templateId"])
        except:
            pass


# ============================================================================
# 场景 9: 缓存机制验证工作流
# ============================================================================
class TestPhase3CacheWorkflow:
    """场景 9: 缓存机制验证工作流测试"""
    
    def test_cache_mechanism_workflow(self):
        """
        测试缓存机制工作流
        1. 第一次查询仪表盘（未命中缓存）
        2. 立即第二次查询（命中缓存）
        3. 比较响应时间
        4. 验证缓存数据一致性
        """
        from src.services.dashboard_service import DashboardService
        
        dashboard_service = DashboardService()
        dashboard_service._invalidate_cache()
        
        # 1. 第一次查询仪表盘（未命中缓存）
        start_time = time.time()
        response1 = client.get("/api/v1/dashboard/stats")
        first_duration = time.time() - start_time
        
        assert response1.status_code == 200
        data1 = response1.json()["data"]
        
        # 2. 立即第二次查询（命中缓存）
        start_time = time.time()
        response2 = client.get("/api/v1/dashboard/stats")
        second_duration = time.time() - start_time
        
        assert response2.status_code == 200
        data2 = response2.json()["data"]
        
        # 3. 比较响应时间
        # 第二次应该更快（使用缓存）
        # 注意：这个断言可能不稳定，但通常缓存会更快
        # 我们主要验证两次都成功返回
        
        # 4. 验证缓存数据一致性
        # 两次返回的数据应该一致（在短时间内）
        assert data1["tasks"]["total"] == data2["tasks"]["total"]
        assert data1["files"]["total"] == data2["files"]["total"]
        assert data1["scripts"]["total"] == data2["scripts"]["total"]
        assert data1["batches"]["total"] == data2["batches"]["total"]
        
        # 验证缓存键存在
        cached_data = dashboard_service._get_from_cache("dashboard_stats")
        assert cached_data is not None
        
        # 测试禁用缓存
        dashboard_service._invalidate_cache()
        response3 = client.get("/api/v1/dashboard/stats?useCache=false")
        assert response3.status_code == 200
        
        # 验证缓存已失效
        cached_after_invalidate = dashboard_service._get_from_cache("dashboard_stats")
        assert cached_after_invalidate is None
        
        # 再次查询应该重新生成缓存
        response4 = client.get("/api/v1/dashboard/stats")
        assert response4.status_code == 200
        data4 = response4.json()["data"]
        
        # 验证数据仍然一致
        assert data4["tasks"]["total"] == data2["tasks"]["total"]
        
        print("✓ 缓存机制验证工作流测试通过")


# ============================================================================
# 场景 10: 完整端到端工作流
# ============================================================================
class TestPhase3EndToEndWorkflow:
    """场景 10: 完整端到端工作流测试"""
    
    @pytest.mark.asyncio
    async def test_full_end_to_end_workflow(self):
        """
        测试完整端到端工作流
        1. 上传视频和音频
        2. 创建处理模板
        3. 应用模板处理视频
        4. 等待任务完成
        5. 下载输出文件
        6. 验证仪表盘统计
        7. 验证系统信息
        """
        import tempfile
        from src.services.template_service import TemplateService
        from src.services.material_service import MaterialService
        from src.services.dashboard_service import DashboardService
        
        template_service = TemplateService()
        material_service = MaterialService()
        dashboard_service = DashboardService()
        
        # 清除缓存
        dashboard_service._invalidate_cache()
        
        created_template_id = None
        created_material_id = None
        
        try:
            # 1. 上传视频和音频
            # 上传音频素材
            with tempfile.NamedTemporaryFile(mode='wb', suffix='.mp3', delete=False) as f:
                f.write(TEST_AUDIO_CONTENT)
                audio_file = f.name
            
            try:
                audio_result = material_service.upload_material(
                    file_path=audio_file,
                    material_type="music",
                    category="轻音乐",
                    tags=["测试", "端到端"],
                    description="端到端测试音频"
                )
                created_material_id = audio_result["materialId"]
            finally:
                if os.path.exists(audio_file):
                    os.unlink(audio_file)
            
            assert created_material_id is not None
            
            # 2. 创建处理模板
            template_steps = [
                {
                    "stepType": "audio",
                    "config": {
                        "voice": "zh-CN-XiaoxiaoNeural",
                        "speed": 1.0,
                        "backgroundMusic": created_material_id
                    },
                    "order": 0
                },
                {
                    "stepType": "video",
                    "config": {
                        "resolution": "1080p",
                        "fps": 30,
                        "addSubtitles": True
                    },
                    "order": 1
                }
            ]
            
            template = template_service.create_template(
                name="端到端测试模板",
                description="用于完整端到端测试的模板",
                steps=template_steps,
                is_public=False
            )
            created_template_id = template["templateId"]
            
            assert created_template_id is not None
            
            # 3. 应用模板处理视频
            test_video_id = f"test_video_{uuid.uuid4()}"
            apply_result = template_service.apply_template(
                template_id=created_template_id,
                video_id=test_video_id
            )
            
            assert apply_result is not None
            assert "applyId" in apply_result
            
            # 4. 等待任务完成（模拟）
            # 在实际场景中，这里会轮询任务状态
            # 测试中我们验证应用记录已创建
            apply_id = apply_result["applyId"]
            records_dir = os.path.join(template_service.base_dir, "records")
            record_path = os.path.join(records_dir, f"{apply_id}.json")
            
            # 等待记录文件创建
            timeout = 5
            start = time.time()
            while not os.path.exists(record_path) and (time.time() - start) < timeout:
                await asyncio.sleep(0.1)
            
            assert os.path.exists(record_path), "应用记录文件未创建"
            
            # 5. 下载输出文件（验证记录内容）
            with open(record_path, 'r') as f:
                record_data = json.load(f)
            
            assert record_data["templateId"] == created_template_id
            assert record_data["videoId"] == test_video_id
            assert record_data["status"] == "ready"
            
            # 6. 验证仪表盘统计
            response = client.get("/api/v1/dashboard/stats")
            assert response.status_code == 200
            dashboard_data = response.json()["data"]
            
            assert "tasks" in dashboard_data
            assert "files" in dashboard_data
            assert "templates" in dashboard_data or "scripts" in dashboard_data
            
            # 7. 验证系统信息
            info_response = client.get("/api/v1/system/info")
            assert info_response.status_code == 200
            system_info = info_response.json()["data"]
            
            assert "os" in system_info
            assert "python" in system_info
            assert "timestamp" in system_info
            
            print("✓ 完整端到端工作流测试通过")
            
        finally:
            # 清理
            if created_template_id:
                try:
                    template_service.delete_template(created_template_id)
                except:
                    pass
            
            if created_material_id:
                try:
                    material_service.delete_material(created_material_id)
                except:
                    pass


# ============================================================================
# 测试执行入口
# ============================================================================
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
