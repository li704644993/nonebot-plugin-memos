import asyncio
import base64
import io
import json
import mimetypes
import os
import time
from pathlib import Path
from typing import Optional, Dict, Any, List, cast

import httpx
from PIL import Image
from nonebot import logger, on_command, on_message
from nonebot.adapters.onebot.v11 import (
    Bot,
    GroupMessageEvent,
    Message,
    MessageSegment,
    MessageEvent,
    ActionFailed,
)
from nonebot.matcher import Matcher
from nonebot.params import CommandArg
from nonebot.plugin import PluginMetadata

# --- 配置部分 ---
# 请根据你的实际情况修改以下配置
ALLOWED_GROUP_IDS = [123456789, 987654321]  # 允许使用的群组ID，请替换为你的群组ID
SPECIAL_USER_ID = [111111111, 222222222]  # 特殊用户ID，请替换为你的用户ID
MEMOS_URL = "https://your-memos-instance.com"  # 你的 Memos 实例地址，请替换为实际地址
MEMOS_ACCESS_TOKEN = "your-memos-access-token-here"  # 你的 Memos 访问令牌，请替换为实际令牌
DEFAULT_TAGS = []  # 默认标签，可以添加你想要的标签，如 ["nonebot", "sync"]
RESOURCE_DIR = "./memos_resources"  # 资源存储目录

# --- 权限控制 ---
def is_authorized(event: MessageEvent) -> bool:
    """检查用户是否为特殊用户，或是否在允许的群组中"""
    if event.user_id in SPECIAL_USER_ID:
        return True
    if isinstance(event, GroupMessageEvent) and event.group_id in ALLOWED_GROUP_IDS:
        return True
    return False

# --- Memos API 调用函数 ---
async def memos_post_text(content: str) -> Optional[str]:
    """发送文本内容到 Memos"""
    url = f"{MEMOS_URL}/api/v1/memos"

    # 添加默认标签
    tags_text = " ".join([f"#{tag}" for tag in DEFAULT_TAGS])
    full_content = f"{content}\n{tags_text}" if tags_text else content

    payload = {
        "content": full_content
    }

    headers = {
        'Authorization': f'Bearer {MEMOS_ACCESS_TOKEN}',
        'Content-Type': 'application/json'
    }

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()

            result = response.json()
            memo_name = result.get("name")
            if memo_name:
                memo_id = memo_name.split('/')[-1]
                logger.info(f"成功创建 Memo，ID: {memo_id}")
                return memo_id
            else:
                logger.error("Memos API 响应中未找到 name 字段")
                return None

    except Exception as e:
        logger.error(f"发送文本到 Memos 失败: {e}")
        return None

async def memos_upload_file(file_path: str, file_name: str) -> Optional[str]:
    """上传文件到 Memos，返回 attachment ID"""
    url = f"{MEMOS_URL}/api/v1/attachments"

    try:
        with open(file_path, "rb") as fh:
            file_bytes = fh.read()

        b64_content = base64.urlsafe_b64encode(file_bytes).decode()

        payload = {
            "filename": file_name,
            "content": b64_content,
            "type": mimetypes.guess_type(file_name)[0] or "application/octet-stream"
        }

        headers = {
            "Authorization": f"Bearer {MEMOS_ACCESS_TOKEN}",
            "Content-Type": "application/json"
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()

            result = response.json()
            attachment_id = result.get("name")
            if attachment_id:
                logger.info(f"成功上传文件，attachment ID: {attachment_id}")
                return attachment_id
            else:
                logger.error("文件上传响应中未找到 name 字段")
                return None

    except Exception as e:
        logger.error(f"上传文件到 Memos 失败: {e}")
        return None

async def memos_post_with_attachment(content: str, attachment_id: str) -> Optional[str]:
    """发送带附件的内容到 Memos"""
    url = f"{MEMOS_URL}/api/v1/memos"

    # 添加默认标签
    tags_text = " ".join([f"#{tag}" for tag in DEFAULT_TAGS])
    full_content = f"{content}\n{tags_text}" if content else tags_text

    payload = {
        "content": full_content,
        "visibility": "PRIVATE",
        "attachments": [{"name": attachment_id}]
    }

    headers = {
        'Authorization': f'Bearer {MEMOS_ACCESS_TOKEN}',
        'Content-Type': 'application/json'
    }

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()

            result = response.json()
            memo_name = result.get("name")
            if memo_name:
                memo_id = memo_name.split('/')[-1]
                logger.info(f"成功创建带附件的 Memo，ID: {memo_id}")
                return memo_id
            else:
                logger.error("Memos API 响应中未找到 name 字段")
                return None

    except Exception as e:
        logger.error(f"发送带附件内容到 Memos 失败: {e}")
        return None

# --- 文件处理函数 ---
async def download_image(url: str, filename: str) -> Optional[str]:
    """下载图片并保存到本地"""
    if not os.path.exists(RESOURCE_DIR):
        os.makedirs(RESOURCE_DIR)

    file_path = os.path.join(RESOURCE_DIR, filename)

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url)
            response.raise_for_status()

            with open(file_path, 'wb') as f:
                f.write(response.content)

            logger.info(f"成功下载图片: {file_path}")
            return file_path

    except Exception as e:
        logger.error(f"下载图片失败: {e}")
        return None

def cleanup_file(file_path: str):
    """清理临时文件"""
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            logger.info(f"已清理临时文件: {file_path}")
    except Exception as e:
        logger.error(f"清理文件失败: {e}")

# --- 触发规则 ---
def note_message_rule(event: MessageEvent) -> bool:
    """检查是否为note开头的消息并且用户有权限"""
    if not is_authorized(event):
        return False

    # 检查消息是否包含以"note"开头的文本段
    for segment in event.get_message():
        if segment.type == "text":
            text = str(segment.data.get("text", "")).strip()
            if text.startswith("note ") or text == "note":
                return True
    return False

# --- 命令处理器 ---
note_sync = on_message(rule=note_message_rule, priority=5, block=True)
@note_sync.handle()
async def handle_note_sync(matcher: Matcher, event: MessageEvent):
    # 提取note后面的文本内容
    text_content = ""
    for segment in event.get_message():
        if segment.type == "text":
            text = str(segment.data.get("text", "")).strip()
            if text.startswith("note "):
                text_content = text[5:].strip()  # 移除"note "前缀
                break
            elif text == "note":
                text_content = ""  # 只有"note"关键词，没有额外内容
                break

    # 检查消息中是否包含图片
    images = []
    for segment in event.get_message():
        if segment.type == "image":
            images.append(segment.data.get("url"))

    if not text_content and not images:
        await matcher.send("❌ 请提供要同步的内容，例如：note 今天的学习笔记")
        return

    await matcher.send("正在同步内容到 Memos...")

    try:
        if images:
            # 如果有图片，先上传图片
            image_ids = []
            for i, img_url in enumerate(images):
                filename = f"memo_image_{int(time.time())}_{i}.jpg"
                file_path = await download_image(img_url, filename)

                if file_path:
                    attachment_id = await memos_upload_file(file_path, filename)
                    if attachment_id:
                        image_ids.append(attachment_id)
                    cleanup_file(file_path)

            if image_ids:
                # 创建带图片的 memo
                memo_id = await memos_post_with_attachment(text_content, image_ids[0])
                if memo_id:
                    await matcher.send(f"✅ 成功同步内容和 {len(image_ids)} 张图片到 Memos！\nMemo ID: {memo_id}")
                else:
                    await matcher.send("❌ 同步失败，请检查配置或稍后重试")
            else:
                await matcher.send("❌ 图片上传失败")
        else:
            # 只有文字内容
            memo_id = await memos_post_text(text_content)
            if memo_id:
                await matcher.send(f"✅ 成功同步文字内容到 Memos！\nMemo ID: {memo_id}")
            else:
                await matcher.send("❌ 同步失败，请检查配置或稍后重试")

    except Exception as e:
        logger.error(f"同步内容失败: {e}")
        await matcher.send("❌ 同步过程中发生错误，请稍后重试")

# --- 插件元数据 ---
__plugin_meta__ = PluginMetadata(
    name="Memos同步",
    description="将消息内容同步到 Memos 笔记系统",
    usage="""
使用方法：
发送以 "note " 开头的消息即可同步到 Memos

示例：
note 今天学习了 Python
note 今天的代码截图（配合图片使用）
note 重要的会议记录
""",
    type="application",
    homepage="https://github.com/yourusername/memos-sync",
    supported_adapters={"~onebot.v11"},
)