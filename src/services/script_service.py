"""
AI 剧本生成服务
使用 GPT API 生成短剧剧本
"""
import os
import json
import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
import asyncio

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False


class ScriptService:
    """剧本生成服务"""
    
    def __init__(self):
        # 初始化 OpenAI 客户端（使用 DeepSeek 或通义千问）
        # 从环境变量读取 API key
        api_key = os.getenv("OPENAI_API_KEY") or os.getenv("DASHSCOPE_API_KEY")
        base_url = os.getenv("OPENAI_BASE_URL", "https://api.deepseek.com")
        
        if OPENAI_AVAILABLE and api_key:
            self.client = OpenAI(api_key=api_key, base_url=base_url)
            self.enabled = True
        else:
            self.client = None
            self.enabled = False
        
        # 剧本存储目录
        self.base_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "scripts")
        os.makedirs(self.base_dir, exist_ok=True)
        
        # 支持的题材类型
        self.supported_genres = [
            "言情", "悬疑", "喜剧", "动作", "科幻", "古装", "都市", "奇幻",
            "恐怖", "励志", "家庭", "职场", "校园", "武侠", "仙侠"
        ]
        
        # 默认题材
        self.default_genre = "言情"
        
        # 默认集数
        self.default_episodes = 80
    
    def _get_system_prompt(self) -> str:
        """获取系统提示词"""
        return """你是一个专业的短剧剧本创作专家，擅长创作各种题材的短视频剧本。
你需要按照以下 JSON 格式输出剧本：

{
  "scriptId": "script-uuid",
  "title": "剧本标题",
  "episodes": 80,
  "genre": "题材类型",
  "createdAt": "2026-03-21T10:00:00Z",
  "scenes": [
    {
      "sceneId": "S01E01-001",
      "episode": 1,
      "location": "场景地点",
      "time": "日/夜",
      "characters": ["角色 1", "角色 2"],
      "description": "场景描述",
      "dialogue": [
        {"character": "角色 1", "text": "台词内容", "emotion": "情绪"}
      ],
      "duration": 15
    }
  ]
}

要求：
1. 每个场景 duration 在 10-30 秒之间
2. 对话要符合人物性格和情绪
3. 场景描述要简洁清晰，便于拍摄
4. 剧情要有吸引力，节奏紧凑
5. 符合短视频平台的用户喜好"""

    def _get_user_prompt(self, theme: str, episodes: int, genre: str) -> str:
        """获取用户提示词"""
        return f"""请创作一个{genre}题材的短剧剧本。

主题：{theme}
集数：{episodes}集

要求：
1. 每集时长约 1-2 分钟
2. 每集包含 3-5 个场景
3. 剧情要有起伏和悬念
4. 人物性格鲜明
5. 对话生动有趣

请只输出 JSON 格式的剧本内容，不要有其他说明文字。"""

    async def generate_script(self, theme: str, episodes: int = None, genre: str = None) -> Dict[str, Any]:
        """
        根据主题生成剧本
        
        Args:
            theme: 剧本主题/梗概
            episodes: 集数，默认 80 集
            genre: 题材类型，默认"言情"
        
        Returns:
            生成的剧本 JSON 数据
        """
        # 使用默认值并验证题材
        if episodes is None:
            episodes = self.default_episodes
        if genre is None or genre not in self.supported_genres:
            genre = self.default_genre
        
        if not self.enabled:
            # API 不可用时使用模拟数据
            return self._generate_mock_script(theme, episodes, genre)
        
        # 构建提示词
        system_prompt = self._get_system_prompt()
        user_prompt = self._get_user_prompt(theme, episodes, genre)
        
        try:
            # 调用 GPT API
            response = await asyncio.to_thread(
                self.client.chat.completions.create,
                model="deepseek-chat",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.8,
                max_tokens=4000,
                response_format={"type": "json_object"}
            )
            
            # 解析响应
            script_content = response.choices[0].message.content
            script_data = json.loads(script_content)
            
            # 补充必要字段
            script_id = str(uuid.uuid4())
            script_data["scriptId"] = script_id
            script_data["createdAt"] = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
            
            # 保存剧本到文件
            script_path = os.path.join(self.base_dir, f"{script_id}.json")
            with open(script_path, 'w', encoding='utf-8') as f:
                json.dump(script_data, f, ensure_ascii=False, indent=2)
            
            return script_data
            
        except Exception as e:
            # 如果 API 调用失败，返回示例数据
            return self._generate_mock_script(theme, episodes, genre)
    
    def _generate_mock_script(self, theme: str, episodes: int, genre: str) -> Dict[str, Any]:
        """生成模拟剧本数据（当 API 不可用时）"""
        script_id = str(uuid.uuid4())
        
        # 根据题材生成示例场景
        scenes = []
        for ep in range(1, min(episodes, 3) + 1):  # 只生成前 3 集示例
            for scene_num in range(1, 4):  # 每集 3 个场景
                scene = {
                    "sceneId": f"S{ep:02d}E{ep:02d}-{scene_num:03d}",
                    "episode": ep,
                    "location": "场景地点",
                    "time": "日" if scene_num % 2 == 1 else "夜",
                    "characters": ["女主", "男主"],
                    "description": f"第{ep}集第{scene_num}场：{theme}相关场景",
                    "dialogue": [
                        {"character": "女主", "text": f"这是第{ep}集的开场白", "emotion": "期待"},
                        {"character": "男主", "text": "剧情正在发展中...", "emotion": "神秘"}
                    ],
                    "duration": 15
                }
                scenes.append(scene)
        
        script_data = {
            "scriptId": script_id,
            "title": theme,
            "episodes": episodes,
            "genre": genre,
            "createdAt": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "scenes": scenes
        }
        
        # 保存剧本到文件
        script_path = os.path.join(self.base_dir, f"{script_id}.json")
        with open(script_path, 'w', encoding='utf-8') as f:
            json.dump(script_data, f, ensure_ascii=False, indent=2)
        
        return script_data
    
    async def expand_script(self, script_id: str, target_episodes: int = None) -> Dict[str, Any]:
        """
        扩展剧本为更多集
        
        Args:
            script_id: 剧本 ID
            target_episodes: 目标集数
        
        Returns:
            扩展后的剧本数据
        """
        # 获取原剧本
        script_data = self.get_script(script_id)
        
        if not script_data:
            raise ValueError(f"剧本 {script_id} 不存在")
        
        current_episodes = script_data.get("episodes", 0)
        if target_episodes is None:
            target_episodes = current_episodes + 20  # 默认扩展 20 集
        
        if target_episodes <= current_episodes:
            raise ValueError(f"目标集数 {target_episodes} 必须大于当前集数 {current_episodes}")
        
        # 获取已有场景
        existing_scenes = script_data.get("scenes", [])
        max_episode = max([s.get("episode", 0) for s in existing_scenes], default=0)
        
        # 生成新集数的场景
        new_scenes = []
        for ep in range(max_episode + 1, target_episodes + 1):
            for scene_num in range(1, 4):  # 每集 3 个场景
                scene = {
                    "sceneId": f"S{ep:02d}E{ep:02d}-{scene_num:03d}",
                    "episode": ep,
                    "location": "新场景",
                    "time": "日",
                    "characters": ["女主", "男主"],
                    "description": f"第{ep}集第{scene_num}场：剧情继续发展",
                    "dialogue": [
                        {"character": "女主", "text": "新的剧情开始了", "emotion": "期待"},
                        {"character": "男主", "text": "精彩继续...", "emotion": "自信"}
                    ],
                    "duration": 15
                }
                new_scenes.append(scene)
        
        # 更新剧本
        script_data["episodes"] = target_episodes
        script_data["scenes"].extend(new_scenes)
        
        # 保存更新后的剧本
        script_path = os.path.join(self.base_dir, f"{script_id}.json")
        with open(script_path, 'w', encoding='utf-8') as f:
            json.dump(script_data, f, ensure_ascii=False, indent=2)
        
        return script_data
    
    def get_script(self, script_id: str) -> Optional[Dict[str, Any]]:
        """
        获取剧本详情
        
        Args:
            script_id: 剧本 ID
        
        Returns:
            剧本数据，不存在则返回 None
        """
        script_path = os.path.join(self.base_dir, f"{script_id}.json")
        
        if not os.path.exists(script_path):
            return None
        
        try:
            with open(script_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return None
    
    def list_scripts(self, limit: int = 20) -> List[Dict[str, Any]]:
        """
        获取剧本列表
        
        Args:
            limit: 返回数量限制
        
        Returns:
            剧本列表（仅基本信息）
        """
        scripts = []
        
        for filename in os.listdir(self.base_dir):
            if not filename.endswith('.json'):
                continue
            
            script_path = os.path.join(self.base_dir, filename)
            try:
                with open(script_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    scripts.append({
                        "scriptId": data.get("scriptId"),
                        "title": data.get("title"),
                        "episodes": data.get("episodes"),
                        "genre": data.get("genre"),
                        "createdAt": data.get("createdAt")
                    })
            except Exception:
                continue
            
            if len(scripts) >= limit:
                break
        
        # 按创建时间倒序
        scripts.sort(key=lambda x: x.get("createdAt", ""), reverse=True)
        return scripts
    
    def delete_script(self, script_id: str) -> bool:
        """
        删除剧本
        
        Args:
            script_id: 剧本 ID
        
        Returns:
            是否删除成功
        """
        script_path = os.path.join(self.base_dir, f"{script_id}.json")
        
        if os.path.exists(script_path):
            os.remove(script_path)
            return True
        return False


# 全局服务实例
script_service = ScriptService()
