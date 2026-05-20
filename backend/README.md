# 后端说明

后端基于 FastAPI，负责认证、视频解析、下载任务编排、结果读取与安全控制。

## 主要职责

- 使用 `yt-dlp` 解析公开视频链接
- 做额度控制、限流与审计记录
- 执行下载、字幕提取与总结任务
- 持久化任务、字幕、摘要和导出产物
- 通过 DeepSeek Chat API 生成结构化总结

## 本地运行

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

## 运行测试

```bash
pytest
```

## 运行时依赖

- `yt-dlp`：已在 `requirements.txt` 中声明

## DeepSeek 单模型模式所需环境变量

- `OPENAI_API_KEY`
- `OPENAI_BASE_URL`
- `OPENAI_MODEL`
- `SECRET_KEY`

推荐配置：

```env
OPENAI_BASE_URL=https://api.deepseek.com
OPENAI_MODEL=deepseek-chat
SECRET_KEY=replace-with-a-long-random-secret
```

## 安全提醒

- 不要把真实 API Key 写进 `.env.example` 或任何受版本控制的文件。
- 真实密钥只应保存在本地 `.env` 或部署平台的密钥管理系统中。
- 如果真实密钥曾出现在日志、聊天记录、截图或已提交文件中，应立即轮换。

## 关于当前总结能力

当前版本采用 DeepSeek 单模型模式。  
这意味着总结能力依赖源视频本身是否提供字幕或自动字幕。

- 有可用字幕：可以生成结构化总结
- 没有可用字幕：只能下载，不能总结

如果没有检测到可用字幕，任务会明确失败并给出可读错误提示，而不是伪造转写内容。
