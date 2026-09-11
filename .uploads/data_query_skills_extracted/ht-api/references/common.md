# 通用搜索 API 参考

本文件只包含已完整满足 `ht-api` 标准能力的正式接口。API 名和摘要使用 HT API 定义，HTTP method、path 和查询参数使用当前可执行接口定义。

## API 索引

| API                       | 摘要                                                              |
|---------------------------|-----------------------------------------------------------------|
| `product_category_search` | Search product category names and return matching category IDs. |
| `author_search`           | Search authors by name and return matching author IDs.          |
| `shop_search`             | Search shops by name and return matching shop IDs.              |
| `brand_search`            | Search brands by name and return matching brand IDs.            |
| `product_search`          | Search products by name and return matching product IDs.        |

## API 详情

### product_category_search

Search product category names and return matching category IDs.

| 参数        | 必填   | 说明                                     |
|-----------|------|----------------------------------------|
| `keyword` | 是    | 需要匹配的抖音带货类目名称关键词，例如“美妆”“女装”或“零食”。不能为空。 |

### author_search

Search authors by name and return matching author IDs.

| 参数        | 必填   | 说明     |
|-----------|------|--------| 
| `keyword` | 否    | 搜索关键词。 |


### shop_search

Search shops by name and return matching shop IDs.

| 参数        | 必填   | 说明    |
|-----------|------|-------| 
| `keyword` | 否    | 搜索关键词 |

### brand_search

Search brands by name and return matching brand IDs.

| 参数        | 必填   | 说明     |
|-----------|------|--------|
| `keyword` | 否    | 搜索关键词  |

### product_search

Search products by name and return matching product IDs.

| 参数        | 必填   | 说明     |
|-----------|------|--------|
| `keyword` | 否    | 搜索关键词  |