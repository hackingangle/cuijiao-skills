---
name: cuijiao-platform
description: >
  萃角儿项目与素材的 API 使用约定。
  当用户要求查询项目、把文本来源入库、修改或删除文本素材时使用。
---

# 萃角儿平台能力

平台项目和素材由账号隔离。访问时只使用用户已提供的 API 地址与独立 API Token；不要猜测项目 ID，也不要输出完整 Token。若 Token 尚未签发或请求返回 401，停止写入并说明阻塞项。目标记录返回 404 时不要猜测其他 ID。

运行安装器且服务端依赖就绪后，可在终端执行 `source ~/.cuijiao/env`，然后使用 `$CUIJIAO_API_BASE` 与 `$CUIJIAO_API_TOKEN`。所有请求带 `Authorization: Bearer $CUIJIAO_API_TOKEN`。独立 API Token 以 `hd_` 开头，可由登录会话通过 `POST /api/tokens` 签发、`DELETE /api/tokens/{id}` 撤销；这些 Token 管理接口只接受登录会话。

## 已有的项目与纯文本素材接口

以下路径已在 cc-b 整合代码中实现；使用前仍需确认目标服务部署了对应版本：

| 操作 | 路径 |
|---|---|
| 列出、创建项目 | `GET/POST /api/projects` |
| 查看、改名、删除项目 | `GET/PATCH/DELETE /api/projects/{id}` |
| 列出、创建项目素材 | `GET/POST /api/projects/{id}/materials` |
| 查看、修改、删除素材 | `GET/PATCH/DELETE /api/materials/{id}` |

创建项目使用 `title`。创建纯文本素材只接受 `title`、非空 `content`；接口会拒绝 `source_ref`。需要记录来源时在 `content` 中注明，并保留原文。素材列表分页返回 `{items,total,page,page_size}`，`items` 只包含摘要；读取全文需请求素材详情。创建或更新前先确定目标项目，逐页查询项目素材以查重；没有确定项目时请用户指定。

文件上传、PDF 抽取、ASR、服务端代理运行尚未接入这组接口。不得调用旧 Heimdall 的文件、抽取或 `agent_id` 路由来代替。写稿、收集等策略由平台智能体人设承担，本技能只记录平台连接和数据约定。
