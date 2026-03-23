#!/usr/bin/env python3
"""
端到端测试脚本 - 适配实际 API 路由
测试完整的视频生成流程
"""

import requests
import time
import os

BASE_URL = "http://localhost:8081/api/v1"

# 测试素材
TEST_VIDEO = "/home/admin/sora-video-generator/assets/test_video.mp4"
TEST_AUDIO = "/home/admin/sora-video-generator/assets/test_audio.mp3"
TEST_IMAGE = "/home/admin/sora-video-generator/assets/test_image.png"

def print_step(step: str, status: str = "⏳"):
    print(f"{status} {step}")

def test_file_upload():
    """测试文件上传"""
    print_step("【文件管理模块测试】")
    
    # 1. 上传视频
    print_step("  1. 上传测试视频...")
    if os.path.exists(TEST_VIDEO):
        with open(TEST_VIDEO, 'rb') as f:
            files = {'file': f}
            data = {'type': 'video'}
            resp = requests.post(f"{BASE_URL}/files/upload", files=files, data=data)
            if resp.status_code == 200:
                video_id = resp.json()['data']['fileId']
                print_step(f"    ✅ 视频上传成功：{video_id}", "✅")
            else:
                print_step(f"    ❌ 视频上传失败：{resp.text}", "❌")
                return None
    else:
        print_step(f"    ⚠️  测试视频不存在：{TEST_VIDEO}", "⚠️")
        return None
    
    # 2. 上传音频
    print_step("  2. 上传测试音频...")
    if os.path.exists(TEST_AUDIO):
        with open(TEST_AUDIO, 'rb') as f:
            files = {'file': f}
            data = {'type': 'audio'}
            resp = requests.post(f"{BASE_URL}/files/upload", files=files, data=data)
            if resp.status_code == 200:
                audio_id = resp.json()['data']['fileId']
                print_step(f"    ✅ 音频上传成功：{audio_id}", "✅")
            else:
                print_step(f"    ❌ 音频上传失败：{resp.text}", "❌")
                audio_id = None
    else:
        print_step(f"    ⚠️  测试音频不存在：{TEST_AUDIO}", "⚠️")
        audio_id = None
    
    # 3. 上传图片
    print_step("  3. 上传测试图片...")
    if os.path.exists(TEST_IMAGE):
        with open(TEST_IMAGE, 'rb') as f:
            files = {'file': f}
            data = {'type': 'image'}
            resp = requests.post(f"{BASE_URL}/files/upload", files=files, data=data)
            if resp.status_code == 200:
                image_id = resp.json()['data']['fileId']
                print_step(f"    ✅ 图片上传成功：{image_id}", "✅")
            else:
                print_step(f"    ❌ 图片上传失败：{resp.text}", "❌")
                image_id = None
    else:
        print_step(f"    ⚠️  测试图片不存在：{TEST_IMAGE}", "⚠️")
        image_id = None
    
    # 4. 查询文件列表
    print_step("  4. 查询文件列表...")
    resp = requests.get(f"{BASE_URL}/files")
    if resp.status_code == 200:
        data = resp.json()
        files = data.get('files', [])
        print_step(f"    ✅ 文件列表查询成功，共 {len(files)} 个文件", "✅")
    else:
        print_step(f"    ❌ 文件列表查询失败：{resp.text}", "❌")
    
    # 5. 查询文件详情
    if 'video_id' in locals():
        print_step("  5. 查询文件详情...")
        resp = requests.get(f"{BASE_URL}/files/{video_id}")
        if resp.status_code == 200:
            file_info = resp.json()
            print_step(f"    ✅ 文件详情查询成功：{file_info.get('fileName')}", "✅")
        else:
            print_step(f"    ❌ 文件详情查询失败：{resp.text}", "❌")
    
    return {
        'video_id': video_id if 'video_id' in locals() else None,
        'audio_id': audio_id if 'audio_id' in locals() else None,
        'image_id': image_id if 'image_id' in locals() else None
    }

def test_audio_processing(files: dict):
    """测试音频处理"""
    print_step("\n【音频处理模块测试】")
    
    # 1. 配音生成
    print_step("  1. 文本配音生成...")
    voiceover_data = {
        "text": "欢迎观看我的视频，记得点赞关注哦！",
        "voice": "zh-CN-XiaoxiaoNeural",
        "speed": 1.0
    }
    resp = requests.post(f"{BASE_URL}/audio/voiceover", json=voiceover_data)
    if resp.status_code == 200:
        result = resp.json()
        task_id = result.get('taskId')
        print_step(f"    ✅ 配音任务创建成功：{task_id}", "✅")
        
        # 等待任务完成
        print_step("  2. 等待配音生成完成...")
        for i in range(10):
            time.sleep(1)
            resp = requests.get(f"{BASE_URL}/asr/{task_id}")
            if resp.status_code == 200:
                task = resp.json()
                status = task.get('status')
                if status == 'completed':
                    audio_id = task.get('result', {}).get('audioId')
                    print_step(f"    ✅ 配音生成完成：{audio_id}", "✅")
                    return {'voiceover_task_id': task_id, 'voiceover_audio_id': audio_id}
                elif status == 'failed':
                    print_step(f"    ❌ 配音生成失败：{task.get('error')}", "❌")
                    break
        print_step(f"    ⏳ 配音生成超时", "⏳")
    else:
        print_step(f"    ❌ 配音任务创建失败：{resp.text}", "❌")
    
    return {}

def test_video_processing(files: dict, audio: dict):
    """测试视频处理"""
    print_step("\n【视频处理模块测试】")
    
    if not files.get('video_id'):
        print_step("  ⚠️  跳过视频处理测试（无视频文件）", "⚠️")
        return
    
    # 1. 文字叠加
    print_step("  1. 文字叠加...")
    text_data = {
        "videoId": files['video_id'],
        "text": "测试文字",
        "fontSize": 24,
        "fontColor": "#FFFFFF",
        "position": "center",
        "duration": 3
    }
    resp = requests.post(f"{BASE_URL}/video/text-overlay", json=text_data)
    if resp.status_code == 200:
        result = resp.json()
        task_id = result.get('taskId')
        print_step(f"    ✅ 文字叠加任务创建成功：{task_id}", "✅")
    else:
        print_step(f"    ❌ 文字叠加失败：{resp.text}", "❌")
    
    # 2. 图片叠加
    if files.get('image_id'):
        print_step("  2. 图片叠加...")
        image_data = {
            "videoId": files['video_id'],
            "imageId": files['image_id'],
            "position": "top-right",
            "width": 200,
            "duration": 3
        }
        resp = requests.post(f"{BASE_URL}/video/image-overlay", json=image_data)
        if resp.status_code == 200:
            result = resp.json()
            task_id = result.get('taskId')
            print_step(f"    ✅ 图片叠加任务创建成功：{task_id}", "✅")
        else:
            print_step(f"    ❌ 图片叠加失败：{resp.text}", "❌")
    
    # 3. 添加背景音乐
    if files.get('audio_id'):
        print_step("  3. 添加背景音乐...")
        music_data = {
            "videoId": files['video_id'],
            "audioId": files['audio_id'],
            "volume": 0.5,
            "loop": True
        }
        resp = requests.post(f"{BASE_URL}/video/add-music", json=music_data)
        if resp.status_code == 200:
            result = resp.json()
            task_id = result.get('taskId')
            print_step(f"    ✅ 背景音乐任务创建成功：{task_id}", "✅")
        else:
            print_step(f"    ❌ 背景音乐添加失败：{resp.text}", "❌")
    
    # 4. 添加字幕
    print_step("  4. 添加字幕...")
    subtitle_data = {
        "videoId": files['video_id'],
        "subtitles": [
            {"start": 0, "end": 3, "text": "欢迎观看"},
            {"start": 3, "end": 6, "text": "点赞关注"}
        ],
        "fontSize": 24,
        "fontColor": "#FFFFFF"
    }
    resp = requests.post(f"{BASE_URL}/video/add-subtitles", json=subtitle_data)
    if resp.status_code == 200:
        result = resp.json()
        task_id = result.get('taskId')
        print_step(f"    ✅ 字幕添加任务创建成功：{task_id}", "✅")
    else:
        print_step(f"    ❌ 字幕添加失败：{resp.text}", "❌")

def test_task_management():
    """测试任务管理"""
    print_step("\n【任务管理模块测试】")
    
    # 1. 查询任务列表
    print_step("  1. 查询任务列表...")
    resp = requests.get(f"{BASE_URL}/tasks")
    if resp.status_code == 200:
        tasks = resp.json()
        print_step(f"    ✅ 任务列表查询成功，共 {len(tasks)} 个任务", "✅")
    else:
        print_step(f"    ❌ 任务列表查询失败：{resp.text}", "❌")

def main():
    print("=" * 60)
    print("🎬 Sora Video Generator - 端到端测试")
    print("=" * 60)
    
    # 1. 文件管理测试
    files = test_file_upload()
    
    # 2. 音频处理测试
    audio = test_audio_processing(files)
    
    # 3. 视频处理测试
    test_video_processing(files, audio)
    
    # 4. 任务管理测试
    test_task_management()
    
    print("\n" + "=" * 60)
    print("✅ 端到端测试完成！")
    print("=" * 60)

if __name__ == "__main__":
    main()
