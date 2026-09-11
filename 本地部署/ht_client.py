#!/usr/bin/env python3
"""灰豚 ht-api 本地调用客户端（对标插件 call-node.js，供本地部署/定时任务使用）

用法：
    python3 ht_client.py --path /search/v2/goods --query '{"keyword":"菊花","sortField":"sales30","searchType":2,"from":1}'

依赖环境变量：
    Data_Query_KEY   （必填，灰豚 API Key，经 ht-api Connector 授权注入）
    HT_API_BASE_URL  （可选，默认 https://dyapi.huitun.com）

安全约束（与插件脚本一致）：
    - 只允许调用 ALLOWED_PATHS 白名单内的路径，防止越权/探测
    - 密钥只从环境变量读取，不落盘、不打印
"""
import json
import os
import sys
import urllib.parse
import urllib.request

DEFAULT_BASE_URL = "https://dyapi.huitun.com"
TIMEOUT_S = 120

ALLOWED_PATHS = {
    "/aweme/aiRank", "/aweme/awemeTopic", "/aweme/goodsList", "/aweme/grassList",
    "/aweme/music", "/aweme/rankVideoList", "/brand/brandAwemeCategory",
    "/brand/brandAwemeCurve", "/brand/brandGrassAwemeList", "/brand/brandInfo",
    "/brand/brandLiveCategory", "/brand/brandLiveCurve", "/brand/brandPriceRange",
    "/brand/brandShop", "/brand/brandShopCate", "/brand/brandUser", "/brand/brandWithGoods",
    "/brand/brandCurveCat", "/brand/curve", "/brand/live", "/brand/prop/cate",
    "/brand/prop/condition", "/brand/prop/list", "/brand/v2/brandAwemeList",
    "/brand/v2/withGoods/other", "/brand/word/cate", "/brand/wordList",
    "/common/rankConditions", "/common/v2/dyCid/AI", "/goods/awemeChart",
    "/goods/infoCurve", "/goods/relateLive", "/goods/relateLiveTrend", "/goods/userList",
    "/goods/v2/awemeTab", "/goods/v2/awemeTab/cid", "/goods/v2/fans", "/goods/v2/info",
    "/goods/v3/infoChart", "/live/brandFans", "/live/detail/fans", "/live/roomInfo",
    "/live/roomInfo/barrage", "/live/roomInfo/brandCategory", "/live/roomInfo/djAweme",
    "/live/roomInfo/goods", "/live/scList", "/live/sell/record", "/live/sell/recordData",
    "/live/shopFans", "/live/tradeFans", "/live/v2/goods", "/live/v2/record",
    "/rank/area/shop", "/rank/dailyLive", "/rank/goodsAwemeStat", "/rank/goodsCard",
    "/rank/live/fansInc", "/rank/live/hourTakeGoodsUser", "/rank/live/takeGoodsUser",
    "/rank/liveGoods", "/rank/liveStream", "/rank/userScoreRank", "/rank/v2/brand",
    "/rank/v2/dyGoods", "/rank/v2/shop", "/rank/videoImageTxt", "/rank/videoUser",
    "/rank/windmill", "/search/room", "/search/user", "/search/v2/brand",
    "/search/v2/goods", "/search/v2/shop", "/shop/awemeBrandAnalyze",
    "/shop/awemeBrandCate", "/shop/awemeCategoryAnalyze", "/shop/awemeCurve",
    "/shop/live/curve", "/shop/liveBrandAnalyze", "/shop/liveBrandCate",
    "/shop/liveCategoryAnalyze", "/shop/priceRangeAnalyze", "/shop/prop/cate",
    "/shop/prop/condition", "/shop/prop/list", "/shop/relateLive", "/shop/shopCurve",
    "/shop/shopCurveCat", "/shop/shopUser", "/shop/shopWithGoods", "/shop/v2/awemeList",
    "/shop/v2/info", "/shop/v2/withGoods/other", "/shop/word/cate", "/shop/wordList",
    "/user/ad/awemeList", "/user/allGoods", "/user/aweme/sell/workCurve",
    "/user/aweme/workCurve", "/user/awemeList", "/user/categoryAnalyze",
    "/user/commonCount", "/user/curve", "/user/liveAnalyze/curve", "/user/productCurve",
    "/user/sell/awemeList", "/user/v3/detail", "/user/videoGoods", "/user/withGoods",
    "/user/withGoods/cate",
}


def fatal(msg: str):
    print(json.dumps({"error": msg}, ensure_ascii=False))
    sys.exit(1)


def main():
    api_key = os.environ.get("Data_Query_KEY")
    if not api_key:
        fatal("Data_Query_KEY is not configured. Please connect the ht-api connector first.")

    args = sys.argv[1:]
    path = None
    query_raw = None
    for i, a in enumerate(args):
        if a == "--path" and i + 1 < len(args):
            path = args[i + 1]
        elif a == "--query" and i + 1 < len(args):
            query_raw = args[i + 1]

    if not path or not path.startswith("/") or path.startswith("//") or ".." in path or "?" in path:
        fatal("--path must be a valid absolute path beginning with /")
    if path not in ALLOWED_PATHS:
        fatal("path is not listed in the bundled HT API references")

    query = {}
    if query_raw:
        try:
            query = json.loads(query_raw)
            if not isinstance(query, dict):
                raise ValueError
        except ValueError:
            fatal("--query must be a JSON object")

    base = os.environ.get("HT_API_BASE_URL", DEFAULT_BASE_URL).rstrip("/")
    qs = urllib.parse.urlencode(
        {k: (json.dumps(v, ensure_ascii=False) if isinstance(v, (dict, list)) else str(v))
         for k, v in query.items() if v is not None}
    )
    url = f"{base}{path}" + (f"?{qs}" if qs else "")

    req = urllib.request.Request(url, headers={"api-key": api_key, "Accept": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT_S) as resp:
            body = resp.read().decode("utf-8", errors="replace")
            print(json.dumps({"status": resp.status, "data": body}, ensure_ascii=False, indent=2))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        print(json.dumps({"status": e.code, "error": e.reason, "data": body}, ensure_ascii=False))
        sys.exit(1)
    except Exception as e:
        fatal(f"HT API request failed: {e}")


if __name__ == "__main__":
    main()
