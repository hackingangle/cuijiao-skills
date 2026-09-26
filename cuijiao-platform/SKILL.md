---
name: cuijiao-platform
description: >
  萃角儿项目与素材的 API 使用约定。
  当用户要求查询项目、把文本来源入库、修改或删除文本素材时使用。
---

# 萃角儿平台能力

平台项目和素材由账号隔离。访问时只使用用户已提供的 API 地址与凭证；不要猜测项目 ID，也不要输出完整 Token。若独立 API Token 尚未签发或接口返回 401/404，停止写入并说明阻塞项。

运行安装器且服务端依赖就绪后，可在终端执行 `source ~/.cuijiao/env`，然后使用 `$CUIJIAO_API_BASE` 与 `$CUIJIAO_API_TOKEN`。所有请求带 `Authorization: Bearer $CUIJIAO_API_TOKEN`。当前后端只有登录会话 Token；独立、可吊销的 API Token 尚待实现，因此不要把会话 Token 伪装为长期 API Token。

## 已有的项目与纯文本素材接口

以下路径来自 cc-b 工作区草稿，部署前仍需核对当前服务版本：

| 操作 | 路径 |
|---|---|
| 列出、创建项目 | `GET/POST /api/projects` |
| 查看、改名、删除项目 | `GET/PATCH/DELETE /api/projects/{id}` |
| 列出、创建项目素材 | `GET/POST /api/projects/{id}/materials` |
| 查看、修改、删除素材 | `GET/PATCH/DELETE /api/materials/{id}` |

创建项目使用 `title`。创建纯文本素材使用 `title`、非空 `content`，来源可用 `source_ref`。素材列表只包含摘要，读取全文需请求素材详情。创建或更新前先确定目标项目，按项目素材列表查重，并保留用户给出的来源与原文；没有确定项目时请用户指定。

文件上传、PDF 抽取、ASR、服务端代理运行尚未接入这组接口。不得调用旧 Heimdall 的文件、抽取或 `agent_id` 路由来代替。写稿、收集等策略由平台智能体人设承担，本技能只记录平台连接和数据约定。
