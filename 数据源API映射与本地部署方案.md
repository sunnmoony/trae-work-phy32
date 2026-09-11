# 数据源 API 映射与本地部署方案（P0 交付）

- 版本：v1.0｜日期：2026-09-11｜状态：待验证试跑
- 目标：把 9 个技能中所有"灰豚/蝉妈妈"文字引用落为 **API 级**（工具 + API 名 + 参数 + 示例），并梳理本地部署的前置依赖与三层架构落地细节
- 依据：灰豚 `ht-api` Skill references（common/product/author/video 等 7 文件）、蝉妈妈 `apis.md` 与 MCP 工具定义、`抖音小店经营与开放平台API复盘.md`

---

## 1. 两个数据源的调用方式（本地部署视角）

### 1.1 灰豚 ht-api —— 纯 HTTP GET

| 项 | 值 |
|---|---|
| 服务地址 | `https://dyapi.huitun.com` |
| 鉴权 | Header `api-key: <Data_Query_KEY>`（TRAE `ht-api` Connector 授权后映射为环境变量；本地部署自行注入） |
| 调用方式 | 任意 HTTP 客户端（curl / Node fetch / Python requests）；参数全部为 GET query |
| 路径白名单 | 插件 `scripts/call-node.js` 内置 100+ 白名单路径，未收录路径不可调 |
| 典型约束 | 榜单日期格式随 `periodType` 变化；普通周期近 3 年、跨度 ≤365 天；返回"次数不足，请联系客服"必须立即终止 |

示例（找"菊花"相关的养生茶商品，近 30 天销量排序）：

```
GET https://dyapi.huitun.com/search/v2/goods?keyword=菊花&sortField=sales30&searchType=2&from=1
Header: api-key: <Data_Query_KEY>
```

### 1.2 蝉妈妈 —— MCP 工具

| 工具 | 用途 | 必填参数 |
|---|---|---|
| `execute_cmm_api` | 数据类 API 统一入口 | `api`（API 英文名）、`query`（参数对象） |
| `copywriting_creation` | 文案创作（短视频/直播/小红书等） | `workflow_type`、`content`（可带 `author`/`product` 引用） |
| `video_understanding` | 视频深度理解（形式/剪辑/分镜/卖点） | `video_urls`（HTTP(S) 数组，单文件 ≤50MB） |

通用约束：时间范围近 90 天、结束不晚于昨天；销量/销售额为区间值，禁止精确计算；默认只取第 1 页；单次深挖少量代表项。

---

## 2. 技能引用 → API 映射（核心交付）

> 约定：灰豚 = 工具名（ht-api 无 MCP 工具，即 HTTP GET）；蝉妈妈 = `execute_cmm_api` 的 `api` 名，或独立 MCP 工具名。

### 2.1 daily-hot-intel（S1 情报选品）

| 技能原文引用 | 数据源 | 具体调用 |
|---|---|---|
| 主源：灰豚商品热销榜（按核心词） | 灰豚 | 链路①（类目榜）：`product_category_search`(keyword=核心词) → 取类目 ID → `product_top_selling_product_rank_period`(sort=sales, periodType=day, rdate=当日, cat0=类目ID, from=1)。链路②（关键词直搜）：`product_library_custom_search_product`(keyword=核心词, sortField=sales30, searchType=2, from=1) |
| 副源：蝉妈妈同款查询 | 蝉妈妈 | `product_library_custom_search_product`：`{keyword, day_type:1, sort:"duration_volume", page:1}` |
| G2 三源一致性 ≥2 源确认 | 灰豚+蝉妈妈+搜索 | 同一商品在灰豚榜单、蝉妈妈同款、WebSearch 舆情中出现 ≥2 次才标"确认趋势" |
| 灰豚不可用降级 | 蝉妈妈+搜索 | 只用蝉妈妈 `product_top_selling_product_rank_period`(day_type=day, day=当日) + WebSearch |

### 2.2 competitor-teardown（S1 竞品拆解）

| 技能原文引用 | 数据源 | 具体调用 |
|---|---|---|
| 商品链接/模糊名称 → 灰豚搜索精确定位 | 灰豚 | `product_library_custom_search_product`(keyword=商品名, from=1) 选 `pid`。**注意**：灰豚无"链接转 ID"接口，商品名定位失败（<2 条）即拒绝并换词 |
| （备选）抖音商品链接转 ID | 蝉妈妈 | `product_search`：`{keyword: "<商品链接>"}` → `promotion_id` |
| 相关性：类目/客单 | 灰豚 | `product_basic_info`(pid) 取类目与价格 |
| 销量体量：月销（灰豚+蝉妈妈交叉，偏差>20% 取低值） | 灰豚+蝉妈妈 | 灰豚 `product_library_custom_search_product`(keyword, sortField=sales30, searchType=2)；蝉妈妈 `product_library_custom_search_product`(keyword, day_type=30, sort="duration_volume") |
| 可模仿性：粉丝量（灰豚达人画像） | 灰豚 | `author_basic_info`(uid) 取粉丝数；**画像性别/年龄无独立接口** → 用 `author_search`(maxGender/maxAge/maxCg 筛选参数) 近似，缺口记"数据缺失=0 分" |
| 起量时长（视频发布时间倒推） | 灰豚 | `author_related_video_list_video`(uid, sortField=createTime, queryTimeStart/End=近3个月, from=1) 看最早放量视频 |
| 六维拆解（商品/达人/视频双源） | 灰豚+蝉妈妈 | 商品：灰豚 `product_basic_info`(pid) 交叉 蝉妈妈 `product_basic_info`(promotion_id)；关联达人：灰豚 `product_related_commerce_author_list`(pid, type=video, keyword="", startTime/endTime, sort=gmv) 交叉 蝉妈妈 `product_related_commerce_author_list`；关联视频：灰豚 `product_related_commerce_video_list`(pid, time=30, tag=1) 交叉 蝉妈妈 `product_related_commerce_video_list` |
| 视频拆解（钩子/脚本） | 蝉妈妈 | `video_understanding`(video_urls=[爆款视频链接]) 或 `extract_video_copywriting`(video_url)/`video_storyboard`(video_id) |

### 2.3 compliant-listing-builder（S2 建品上架）

| 技能原文引用 | 数据源 | 具体调用 |
|---|---|---|
| 灰豚/巨量算数验证候选词热度，0 热度剔除 | 灰豚 | `product_library_custom_search_product`(keyword=候选词, from=1)：返回 0 条或销量极低 → 判"0 热度"剔除；无热度词专用接口，此为近似验证 |
| 同款头部价格带（灰豚/搜索） | 灰豚+蝉妈妈 | 灰豚 `product_library_custom_search_product`(keyword=品类词, sortField=gmv30, searchType=2) 取 TOP 价格带；蝉妈妈 `product_library_custom_search_product`(keyword, day_type=30, sort="duration_amount") 交叉。定价规则：本定价不高于头部 +30% |
| 灰豚不可用降级 | 搜索 | WebSearch 抽样头部价格带 |

### 2.4 store-launch-sop（S3 货架运营）

| 技能原文引用 | 数据源 | 具体调用 |
|---|---|---|
| 标题诊断：核心搜索词热度（巨量算数/灰豚） | 灰豚 | 热度验证同上：`product_library_custom_search_product`(keyword=候选核心词, from=1)，0 热度词剔除；爆款标题参考用 `video_commerce_library`(keyword=品类词, hours=168, sortField=video_sales, from=1)（补充能力，仅作参考） |

### 2.5 content-ops-analysis（S4 内容营销）

| 技能原文引用 | 数据源 | 具体调用 |
|---|---|---|
| 灰豚达人视频榜/蝉妈妈视频拆解：对标账号近 7 天新发布播放靠前 3 条 | 灰豚+蝉妈妈 | 灰豚 `author_related_video_list_video`(uid=对标达人, sortField=digg, queryTimeStart=7天前, queryTimeEnd=今日, from=1) 取 Top3；蝉妈妈 `video_detail_info`(aweme_id) 看单视频数据、`video_understanding`(video_urls) 拆内容 |
| 按关键词找对标爆款视频 | 灰豚 | `video_commerce_library`(keyword=品类词, hours=168, sortField=video_gmv, from=1)（补充能力） |
| 灰豚/蝉妈妈不可用降级 | 搜索 | WebSearch 关键词搜当日爆款视频 |

### 2.6 douyin-influencer-collab（S5 达人推广）

| 技能原文引用 | 数据源 | 具体调用 |
|---|---|---|
| 品类相关度：带货历史类目分布 | 灰豚 | `author_commerce_category_list`(uid, startTime/endTime, tag=live|video, categoryType=cat0, sort=gmv) 看是否含食品/养生/滋补 ≥3 条 |
| 受众匹配：粉丝画像女性占比 + 年龄分布（灰豚达人画像） | 灰豚 | **无独立粉丝画像接口** → `author_search`(maxGender=2, maxAge=指定段, keyword=达人名, from=1) 预筛；或 `author_basic_info`(uid) 取粉丝数；缺口记"数据缺失=0 分"，不编造 |
| 带货能力：近 30 天场均 GMV / 视频带货单量 | 灰豚 | `author_related_video_list_video_2`(uid, sortField=gmv, queryTimeStart/End=近30天) 汇总视频带货；`author_live_video_sales_data_daily_detail`(4 请求组合) 取近 30 天日均。门禁：场均 GMV ≥3000 或单量 ≥100 |
| 合规记录：历史视频功效宣称扫描 | 蝉妈妈 | 抽样 `extract_video_copywriting`(video_url) 取口播文案 → compliance-check 扫功效词；食品类一票否决 |
| 达人发布后采集：曝光/互动/单量/GMV | 灰豚 | `author_related_video_list_video`(uid, sortField=gmv|digg, queryTimeStart/End, type=with_fusion_goods) |
| 灰豚达人数据不可用降级 | 蝉妈妈 | 蝉妈妈无达人榜/达人详情 API → 降级为商品维度 `product_related_commerce_author_list`(promotion_id=主推款, start_date/end_date, sort=volume) 看谁在带 + WebSearch 账号表现 |

---

## 3. 关键场景调用示例（可直接试跑验证）

### 场景 A：每日拉养生茶类目热销榜（S1 每日 5 分钟版）

```bash
# ① 类目名 → ID
GET /common/v2/dyCid/AI?keyword=养生茶
# ② 当日热销榜（销量降序，取前 20）
GET /rank/v2/dyGoods?sort=sales&periodType=day&rdate=2026-09-11&cat0=<类目ID>&from=1
# ③ 蝉妈妈交叉（同款查询）
{"api":"product_library_custom_search_product","query":{"keyword":"养生茶","day_type":1,"sort":"duration_volume","page":1}}
```

### 场景 B：关键词找爆款 + 双源交叉（S1 60 分钟版）

```bash
# 灰豚：近 30 天销售额 TOP
GET /search/v2/goods?keyword=菊花枸杞&sortField=gmv30&searchType=2&from=1
# 蝉妈妈：近 30 天销售额 TOP
{"api":"product_library_custom_search_product","query":{"keyword":"菊花枸杞","day_type":30,"sort":"duration_amount","page":1}}
```

### 场景 C：竞品六维拆解（S1 深挖）

```bash
# 商品基础信息（灰豚，pid 由上一步定位）
GET /goods/v2/info?pid=<pid>
# 关联达人（近 30 天）
GET /goods/userList?type=video&keyword=&pid=<pid>&startTime=2026-08-12&endTime=2026-09-11&sort=gmv&from=1
# 关联视频（近 30 天，带货场景）
GET /goods/v2/awemeTab?pid=<pid>&time=30&tag=1&sort=video_gmv&from=1
# 视频内容拆解（蝉妈妈 MCP）
video_understanding: {"video_urls":["<爆款视频链接>"]}
```

### 场景 D：达人四维筛选（S5）

```bash
# 达人搜索：食品类 + 女性粉丝为主 + 粉丝区间（万）
GET /search/user?keyword=养生&userType=video&sortField=live_gmv30&followerRange=1-50&maxGender=2&from=1
# 选中后取基础信息（uid → 粉丝数/认证）
GET /user/v3/detail?uid=<uid>
# 带货品类分布
GET /user/categoryAnalyze?uid=<uid>&startTime=2026-08-12&endTime=2026-09-11&tag=video&categoryType=cat0&mod=desc&sort=gmv
# 视频带货表现（近 30 天）
GET /user/sell/awemeList?uid=<uid>&sortField=gmv&queryTimeStart=2026-08-12&queryTimeEnd=2026-09-11&from=1
```

### 场景 E：文案创作（S4 模板化产出，原来完全没用上的能力）

```json
copywriting_creation: {
  "workflow_type": "sale_video",
  "content": "为菊花枸杞决明子茶（独立小袋装，秋冬季暖身）生成一段 30 秒带货口播文案，突出真实原料与冲泡演示",
  "product": "[@{\"type\":\"product\",\"id\":\"<promotion_id>\",\"name\":\"菊花枸杞决明子茶\"}]"
}
```

---

## 4. 本地部署前置依赖清单

| # | 依赖 | 具体内容 | 完成标志 | 优先级 |
|---|---|---|---|---|
| D1 | 灰豚 API Key | TRAE `ht-api` Connector 授权 → 环境变量 `Data_Query_KEY`；确认套餐次数/日限额（出现"次数不足"即停） | 本机 curl 打通场景 A ①② | 必装 |
| D2 | 蝉妈妈 MCP 授权 | 连接 `chanmama` 插件（execute_cmm_api 受次数/积分限制）；确认每次调用积分成本 | 试跑 execute_cmm_api 1 次成功 | 必装 |
| D3 | 抖店开放平台（可选，S0 自动取数的前提） | 企业认证（约 10 工作日）→ 软著 + 系统功能说明书（1~3 工作日）→ 创建应用拿 app_key/app_secret → 店铺授权 → access_token（7 天刷新）→ 配置 IP 白名单 | 沙箱测试 `/order/searchList` 成功 | 分期：先人工取数，单量稳定后再接 |
| D4 | 本地运行时 | Node ≥18（灰豚脚本原生）/ Python 3.10+（蝉妈妈、抖店 SDK）；SQLite3；cron（家用机常开）或云函数（免运维） | 环境自检通过 | 必装 |
| D5 | 密钥与安全 | `Data_Query_KEY`/`app_secret`/`access_token` 只存环境变量或密钥管理，不落库、不打印、不进 git；抖店密文链路合规 | 密钥规范落地 | 必装 |

**部署路径（四步，每步有验收）：**

1. **Step 1 数据源打通**：D1/D2 就绪 → 用第 3 节场景 A/C 试跑灰豚+蝉妈妈，产出第一份热销榜落库（`经营档案/每日情报日报.md`）。验收：场景 A 三个调用全部返回真实数据。
2. **Step 2 S0 自动取数**（可选）：接入抖店开放平台，S0 五数（曝光/点击率/转化率/GMV/体验分）由人工录入改自动；验收：仪表盘数据无需人工抄录。
3. **Step 3 定时任务编排**：cron 每日定时跑场景 A（S1）+ 数据落库；验收：连续 7 天无人值守产出日报。
4. **Step 4 决策层配置化**：阈值表/门禁 → JSON 规则库，S6 复盘只改配置；验收：改一条阈值无需改任何技能文件。

---

## 5. 三层架构本地化细节

```
┌─ 决策层：规则配置化
│    经营手册 M1-M8 → 阈值表/门禁/触发映射 → config/rules.json
│    S6 复盘只改配置（改 JSON + 手册版本 +1），不改流程
├─ 执行层：技能落地
│    .trae/skills 9 技能（输入契约/分级执行/输出契约/数据回流）
│    本地知识库（经营手册.md / 经营档案/）← Obsidian/语雀 可选托管
│    AI 工作流编排 60 分钟主循环：15 盯盘(S0) + 30 内容(S4) + 15 轮转(S1/S3/S5)
├─ 数据层：自动取数
│    灰豚(HTTP GET + api-key) + 蝉妈妈(MCP execute_cmm_api) + 抖店开放平台(S0)
│    → cron 定时任务 → SQLite/CSV（本地落库，只存摘要不存敏感信息）
└─ 调用链：cron → 取数脚本 → SQLite → 技能查询 → 决策层规则 → 动作清单
```

| 层 | 组件 | 本地化说明 | 失败降级 |
|---|---|---|---|
| 数据层 | 灰豚/蝉妈妈取数脚本（Python/Node）+ 定时任务 + SQLite | 每日拉榜 1-2 次即够，防次数耗尽；榜单/摘要落库，区间值原样存（不做精确计算） | 灰豚挂 → 蝉妈妈 + WebSearch；蝉妈妈挂 → 灰豚单源 + 标注"待验证" |
| 执行层 | 9 技能 + 经营档案 + AI 工作流 | 技能文件是契约，执行在 TRAE（有数据源授权）；知识库单文件 `经营手册.md`，Obsidian 仅作可视化 | 无数据源 → 技能输出"待补数据"清单，不编造 |
| 决策层 | 规则库（阈值表 JSON）+ S6 复盘 | 阈值表初版在技能/手册中，Step 4 收敛为 JSON 规则库；S6 产出"规则修订表"直接改配置 | 无数据 → 保留上次规则并标注 |

---

## 6. 未覆盖缺口（诚实标注，P1 再补）

| 缺口 | 影响 | 现状对策 |
|---|---|---|
| 达人粉丝画像（性别/年龄分布）无独立接口 | S5 受众匹配维度只能近似 | 用 `author_search` 的 maxGender/maxAge/maxCg 预筛；仍缺记 0 分（技能已有规则），不编造 |
| 搜索词热度无直接接口 | S2/S3 标题热度验证为近似 | 用商品搜索返回量近似 + WebSearch 兜底；巨量算数人工核验 |
| 蝉妈妈无达人榜/达人详情 API | S5 灰豚挂时的降级路径偏弱 | 降级为商品关联达人列表（真实带货名单）而非达人榜 |
| 灰豚无"商品链接/视频链接转 ID" | S1 输入链接时需换路 | 链接走蝉妈妈 `product_search`/`video_search`；灰豚只支持名称/类目 |
| 抖店开放平台资质门槛高（软著+企业认证） | S0 自动取数无法即刻上线 | 分阶段：先人工取数（现有技能即支持），单量稳定后走 Step 2 |

---

## 7. 下一步（P0 剩余）

- [ ] 试跑第 3 节 5 个场景，核对返回结构与技能字段对齐（需 D1/D2 就绪）
- [ ] 把本映射回写 6 个技能：替换"灰豚商品榜/蝉妈妈视频拆解"等文字引用为具体 API 名 + 参数
- [ ] 用真实返回校准《经营手册》M3/M6 阈值（如榜单销量区间口径）
