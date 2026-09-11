---
name: ht-api
description: 千里眼电商数据查询：查达人（找达人/找主播/找KOL/网红筛选/粉丝画像/带货数据/带货榜单/带货列表）、查商品（热销榜/爆款商品/这个商品卖得怎么样/带货达人/用户评论/商品分析）、查小店（店铺数据/小店销售/关联商品/动销分析）、查品牌（XX品牌市场表现/市场份额/竞品对比/品牌销售趋势）、查直播（直播间数据/场观人数/弹幕分析/直播商品/直播销售额）、查视频（爆款视频/热门视频/千川素材/视频带货数据/视频榜单）、查品类（品类趋势/市场分析/类目数据/属性特征分析）。当用户询问抖音数据、抖音电商相关数据时使用此Skill。
---

# HT API

使用此 skill 调用 ht-chat-ai 的 HT API 直连执行端点。

## 接口地址

调用 `POST {HT_API_BASE_URL}/v1/ai/api`。
默认 base URL：`https://dyapi.huitun.com`。

鉴权要求：
- 使用客户端请求头 `api-key: $Data_Query_KEY`。

常用请求体：

```json
{
  "api": "product_basic_info",
  "query": {
    "pid": "HARYVvhiGpIBuK+A2X135kLJvRT4T5YAhGkedu57gxk="
  }
}
```

## 使用流程

### 首次使用或需要检查版本等信息

1. 调用检查接口：
   ```bash
   GET {HT_API_BASE_URL}/v1/ai/api/list
   api-key: $Data_Query_KEY
   ```
   - 若Data_Query_KEY未配置，引导用户前往灰豚数据-鲸策AI获得KEY，并添加到环境变量。地址`https://dy.huitun.com/app/#/app/ai`
2. 版本检查（静默）：
   - 根据接口返回的 message 提示信息 或 对比返回的 `version` 与本地版本 `2026-09-04`
   - 如果有新版本，**提醒用户升级。**
   - 提醒用户：
     > 💡 发现新版本 数据查询Skill（{version}），是否现在更新？我可以帮您自动完成。
   - 如果用户同意，请根据 https://dy.huitun.com/agent/ht-skill-guide.md 将HT_API_Skills重新安装并刷新 skill：

### 正常调用流程
1. 如果只有实体名称（达人名/商品名/品牌名/店铺名等）而非ID，先阅读 `references/common.md` 调用搜索API转为ID。
2. 分析需求，确定主查询实体（主语是谁？查什么？），阅读对应的references文件：
   - 涉及多实体时，按主查询实体选择
   - 示例："交个朋友直播间带货的花西子商品" → 主实体是"达人"，读 `author.md`
3. 根据意图、API 摘要和查询字段选择 API。
4. 使用参考文件中记录的字段名构造 `query`。
5. 用户需要真实调用时，优先使用curl命令，运行环境无curl命令时使用 `scripts/call_ht_api.py` 执行。若提供 `HT_API_BASE_URL` 则使用该地址，否则使用默认地址。
6. 如果 `code != 0`，将 `msg` 中的错误信息和引导链接直接展示给用户；只有在鉴权、实体或日期等输入无法安全推断时再向用户追问。

## 日期参数处理

- 普通日期通常使用 `YYYY-MM-DD`，但字段名可能是 `startTime/endTime`、`queryTimeStart/queryTimeEnd`、`start/end`，或单个 `time="开始日期,结束日期"`。以所选 API 的参数表为准。
- references 明确标注时，普通周期最早支持近 3 年，且单次跨度不超过 365 天；这不是所有接口的统一规则。例如直播库的 `createTimes` 最早为近 2 年、跨度最多 90 天。
- 榜单日期格式不统一。常见格式为日榜 `yyyy-mm-dd`、周榜 `mm月dd日-mm月dd日`、月榜 `yyyy年mm月`，部分榜单还支持季度、半年和年榜。
- `periodType` 在不同 API 中可能是英文字符串、整数或数字字符串。必须同时按当前接口核对 `periodType` 和日期字段，不得套用其他榜单的值。
- 视频热销带货榜可用 `hours=24/72/168`，或使用 `periodType + time`，两种方式二选一。
- 相对日期遵循运行时系统提示词注入的当前日期口径；未提供运行时口径时，默认按北京时间使用截至昨日的完整数据。用户明确要求今天、实时或当日数据时，才在接口支持的前提下纳入今天。

## 多步查询模式

以下示例用于说明组合方式。真实调用前仍需打开对应 reference，补齐其标为必填的字段。

**模式 1：达人名称 -> 达人ID -> 详情**

```text
1. author_search(keyword="交个朋友直播间", from="1") -> 选择 达人ID
2. author_basic_info(uid=达人ID) -> 达人基础信息
```

**模式 2：达人 + 品牌 -> 达人带货商品**

```text
1. author_search(keyword="交个朋友直播间", from="1") -> 选择 达人 ID
2. brand_search(keyword="花西子", sort="gmv", from="1") -> 选择品牌 ID
3. author_commerce_product_list(
     uid=达人 ID,
     brandId=品牌 ID,
     startTime="2026-07-01",
     endTime="2026-07-20",
     from="1",
     sort="sales"
   )
```

**模式 3：商品名称 -> 商品 ID -> 画像**

```text
1. product_library_custom_search_product(keyword="洗面奶", from="1") -> 选择商品 ID
2. product_audience_profile(pId=商品 ID) -> 观众画像
   或 product_audience_profile(pId=商品 ID, tag="1") -> 成交画像
```

**模式 4：小店名称 -> 小店 ID -> 成交画像**

```text
1. shop_search(keyword="目标店铺", sort="gmv", from="1") -> 选择小店 ID
2. shop_order_profile(
     id=小店 ID,
     startTime="2026-07-01",
     endTime="2026-07-20",
     tag="shop"
   )
```

**模式 5：主播名称 -> 直播场次 -> 直播详情**

```text
1. author_search(keyword="目标主播", from="1") -> 选择 uid
2. author_related_live_list(uid=uid, from="1", time="2026-07-20") -> 选择 roomId
3. live_basic_info_product_list_audience_profile(roomId=roomId, uid=uid)
   按 reference 顺序请求基础信息、商品列表、观众画像
```

## 数据理解规范

### 区间值说明

如果API 返回的销售额、销量等核心指标均为**区间值**时，不是精确数字。常见格式如 `"10万-50万"`、`"1000-5000"`、`"100W+"` 等。

**上限规则**（区间超过此值时显示为带 `+` 的上限值）：
- 达人/小店/视频/直播/品牌/品类：
  - 销售额上限：`1000W+`（即 ≥ 1000万 时显示为 `1000W+`）
  - 销量上限：`100W+`（即 ≥ 100万件 时显示为 `100W+`）
- 单个商品对象：
  - 销售额上限：`100W+`
  - 销量上限：`10W+`

**指数说明**：
1. 销量/销售额指数是基于商品成交相关数据综合计算得出
2. 可通过销量/销售额指数比较同一区间销量/销售额的大小，不可直接用于计算同环比数据

### 禁止对区间值做数学计算

⚠️ **任何情况下，禁止对区间值进行加减乘除、求和、取平均或合计操作。** 

原因：
1. 区间值本身包含不确定性，取中位数或端点值均会引入误差
2. 多条目累加会将误差叠加放大，合计结果严重失真
3. `1000万+` 等带 `+` 的截断值根本无法参与准确计算

**正确做法**：
- 直接展示原始区间字符串，不换算为具体数值后相加
- 需要对比或排序时，仅做定性描述（如"A 销售额高于 B"），不输出精确合计
- 若用户明确要求"粗略估算"，可说明取中位数估算并标注"仅供参考，非真实数据"

### 向用户说明数据局限

- 回复中涉及销售额/销量上限时，**必须向用户解释**平台数据的区间值规范和上限，强调上限值并非实际数值，避免用户理解偏差
- 数据为单平台数据，不含私域、线下、其他平台数据
- 制定查询策略时优先在当前会员权限范围内取数；若权限限制导致明显数据缺口（如时间范围被截断、某模块不可访问），如实说明缺口并引导用户升级数据会员

## 版本与更新

当前 skill 版本：`2026-09-04`。

可通过 `GET {HT_API_BASE_URL}/v1/ai/api/list` 查询当前 API Key 可访问的API 列表、最新 skill 版本号。

请求参数与鉴权：
- `api-key: $Data_Query_KEY`

返回字段：
- `data`：可访问的 API 权限映射。
- `version`：最新 skill 版本号，取下载链接记录创建日期。

## 请求方式

### 请求头

- `api-key`: $Data_Query_KEY

### 请求体
- `api`：所选参考文件中的英文 API 名。
- `query`：包含该 API 文档字段的对象。

### 请求方式

默认直接调用 `curl`，不依赖 Python。先安全确认凭据是否存在；只输出配置状态，不得输出凭据值：

```bash
if [ -n "${Data_Query_KEY:-}" ]; then
  printf 'Data_Query_KEY is configured\n'
else
  printf 'Data_Query_KEY is not configured\n'
fi
```

POST 请求示例：

```bash
ht_api_base_url="${HT_API_BASE_URL:-https://dyapi.huitun.com}"
curl --silent --show-error \
  --connect-timeout 15 \
  --max-time 120 \
  -X POST "${ht_api_base_url}/v1/ai/api" \
  --header "api-key: ${Data_Query_KEY}" \
  --header "Content-Type: application/json" \
  --data-raw '{"api":"shop_key_metrics_live_video_author_sales_data_daily_detail","query":{"id":"F0mN9ygPH61SRcQiYjnZ9w==","startTime":"2026-08-26","endTime":"2026-08-26"}}'
```

- 保留响应 body 以及末尾的 `HTTP_STATUS`。遇到 HTTP 错误时展示服务端错误码和消息；遇到 DNS、网络或沙箱限制时，按当前运行时的审批机制重试同一请求，不要擅自更换服务地址。
- 不要使用 `set -x`，不要直接输出 `Data_Query_KEY`，不要把真实凭据写入文件或回复。

仅当 `curl` 不可用而环境提供 Python 时，使用可选兼容脚本：

```bash
ht_api_skill_dir="/absolute/path/to/ht-api"
python "$ht_api_skill_dir/scripts/call_ht_api.py" \
  --api shop_key_metrics_live_video_author_sales_data_daily_detail \
  --query '{"id":"F0mN9ygPH61SRcQiYjnZ9w==","startTime":"2026-08-26","endTime":"2026-08-26"}'
```

## 参考文件

只按下列参考文件选择能力。每个文件先查看 `API 索引`；正式能力不足时才查看其下方独立的 `其他 API 索引`，并读取同一区域对应的详情：

- **达人相关**（`references/author.md`）
  - 达人库（自定义找达人/推荐达人）
  - 达人榜单（带货达人榜/涨粉达人榜）
  - 达人基础信息、粉丝画像
  - 达人关键数据（日明细/周期合计）
  - 达人关联的直播列表、视频列表（发布视频/动销视频）
  - 达人带货的商品列表、品类列表、小店列表、品牌列表

- **商品相关**（`references/product.md`）
  - 商品库（自定义找商品）
  - 商品榜单（热销榜/热推榜/直播热销榜/视频热销榜）
  - 商品基础信息、观众画像、成交画像、评论明细
  - 商品关键数据（日明细/周期合计）
  - 商品关联的达人列表、直播列表、视频列表

- **小店相关**（`references/shop.md`）
  - 小店库（自定义找小店）
  - 小店榜单（热销小店榜/热销品牌官方小店榜）
  - 小店基础信息、观众画像、成交画像
  - 小店关键数据（日明细/周期合计）
  - 小店关联的达人列表、商品列表、直播列表、视频列表、商品卡列表、品类列表

- **品牌相关**（`references/brand.md`）
  - 品牌库（自定义找品牌）
  - 品牌榜单（热销品牌榜）
  - 品牌基础信息、观众画像、成交画像
  - 品牌关键数据（日明细/周期合计）
  - 品牌关联的达人列表、小店列表、商品列表、直播列表、视频列表、商品卡列表、品类列表

- **直播相关**（`references/live.md`）
  - 直播库（自定义找热门直播间）
  - 直播榜单（今日热销带货直播间榜）
  - 直播详情（基础信息/关键数据/商品列表/观众画像）
  - 直播过程信息（场观明细/互动弹幕/高光讲解）
  - 直播弹幕明细

- **视频相关**（`references/video.md`）
  - 视频库（自定义找热门视频）
  - 带货视频库（自定义找热销视频）
  - 视频榜单
  - 视频详情（数据指标/视频信息/视频评论）
  - 全网趋势热点

- **通用搜索**（`references/common.md`）
  - 商品类目名称搜索
  - 达人名称搜索
  - 小店名称搜索
  - 品牌名称搜索
  - 产品名称搜索
