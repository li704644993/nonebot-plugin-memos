# NoneBot Memos 同步插件

一个用于将 QQ 机器人消息同步到 [Memos](https://github.com/usememos/memos) 笔记系统的 NoneBot2 插件。

## 功能特性

- 🚀 **简单易用**：只需发送以 `note` 开头的消息即可同步到 Memos
- 📝 **文字同步**：支持纯文字内容同步
- 🖼️ **图片同步**：支持图片上传和同步
- 🔒 **权限控制**：支持用户和群组权限控制
- 🏷️ **标签支持**：自动为同步的内容添加标签
- 📱 **多媒体**：支持文字和图片混合同步

## 安装

### 使用 pip 安装依赖（如果nb运行在虚拟环境中，需要在虚拟环境中安装依赖）

```bash
pip install httpx pillow
```

### 手动安装

1. 将 `memos_sync.py` 文件放置到你的 NoneBot 插件目录中，如nonebot/plugins
2. 确保已安装所需依赖
3. 在pyproject.toml的plugins数组中，加入"plugins.memos_sync"
4. 重启nb即可

## 配置

在使用前，请修改 `memos_sync.py` 文件中的配置项：

```python
# --- 配置部分 ---
ALLOWED_GROUP_IDS = [123456789, 987654321]  # 允许使用的群组ID
SPECIAL_USER_ID = [111111111, 222222222]   # 特殊用户ID
MEMOS_URL = "https://your-memos-instance.com"  # 你的 Memos 实例地址
MEMOS_ACCESS_TOKEN = "your-memos-access-token-here"  # 你的 Memos 访问令牌
DEFAULT_TAGS = ["nonebot", "sync"]  # 默认标签（可选）
```

### 配置说明

| 配置项 | 说明 | 示例 |
|--------|------|------|
| `ALLOWED_GROUP_IDS` | 允许使用插件的 QQ 群组 ID 列表 | `[123456789, 987654321]` |
| `SPECIAL_USER_ID` | 拥有特殊权限的用户 ID 列表 | `[111111111, 222222222]` |
| `MEMOS_URL` | 你的 Memos 实例地址 | `"https://memo.example.com"` |
| `MEMOS_ACCESS_TOKEN` | Memos API 访问令牌 | 在 Memos 设置中生成 |
| `DEFAULT_TAGS` | 自动添加的默认标签 | `["nonebot", "工作"]` |

### 获取 Memos Access Token

1. 登录你的 Memos 实例
2. 前往 `设置` -> `我的账户` -> `访问令牌`
3. 创建新的访问令牌
4. 复制生成的令牌到配置中

## 使用方法

### 基本用法

发送以 `note` 开头的消息即可同步到 Memos：

```
note 今天学习了 Python 编程
note 重要的会议记录
note 突然想到的好想法
```

### 图片同步

发送 `note` 加图片：

```
note 今天的代码截图
[图片]
```

或者只发送图片：

```
note
[图片]
```

### 文字和图片混合

```
note 今天完成的项目截图
[图片]
```

### 加标签的方式

```
note #这里是标签 memo正文
note #这里是标签 [图片]
```

## 权限控制

插件支持两种权限控制方式：

1. **特殊用户**：配置在 `SPECIAL_USER_ID` 中的用户可以在任何地方使用
2. **群组权限**：在 `ALLOWED_GROUP_IDS` 中配置的群组内的所有用户都可以使用

## 示例

### 文字同步示例

**输入：**
```
note 今天完成了 NoneBot 插件开发
```

**输出：**
```
✅ 成功同步文字内容到 Memos！
Memo ID: abc123def456
```

### 图片同步示例

**输入：**
```
note 项目架构图
[图片]
```

**输出：**
```
✅ 成功同步内容和 1 张图片到 Memos！
Memo ID: xyz789uvw012
```

## 技术实现

- **框架**：基于 NoneBot2 和 OneBot v11 适配器
- **HTTP 客户端**：使用 httpx 进行异步 HTTP 请求
- **图片处理**：使用 Pillow 处理图片
- **文件管理**：自动下载、上传和清理临时文件

## 依赖项

```
nonebot2
nonebot-adapter-onebot
httpx
pillow
```

## 目录结构

```
memos-plugin/
├── memos_sync.py       # 主插件文件
├── README.md           # 说明文档
└── memos_resources/    # 临时文件目录（自动创建）
```

## 注意事项

1. **权限配置**：请确保正确配置用户和群组权限
2. **网络访问**：确保机器人服务器可以访问你的 Memos 实例
3. **令牌安全**：请妥善保管 Memos 访问令牌，不要泄露
4. **存储空间**：插件会下载图片到本地临时处理，处理完成后自动清理

## 故障排除

### 常见问题

**Q: 发送消息没有反应**
- 检查用户/群组是否有权限
- 确认消息格式是否正确（以 `note` 开头）

**Q: 图片同步失败**
- 检查网络连接
- 确认 Memos 实例可访问
- 验证访问令牌是否正确

**Q: 提示权限错误**
- 检查 `ALLOWED_GROUP_IDS` 和 `SPECIAL_USER_ID` 配置
- 确认用户 ID 和群组 ID 是否正确

## 贡献

欢迎提交 Issues 和 Pull Requests！

## 许可证

MIT License

## 更新日志

### v1.0.0
- 初始版本发布
- 支持文字和图片同步
- 支持权限控制
- 支持自定义标签
