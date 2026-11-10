# -*- coding: utf-8 -*-
"""
上海人社局官网政策抓取脚本
=================================================
作用：把 rsj.sh.gov.cn 上"规范性文件""其他文件"两个栏目里的政策，
     按关键词筛选后写成 data.js，供 index.html 读取。

用法（在 hr-policy 文件夹里打开命令行/终端）：
    python fetch_policies.py                # 抓全部页面
    python fetch_policies.py --pages 3      # 每个栏目只抓前 3 页，调试用
    python fetch_policies.py --no-summary   # 不抓详情页，速度最快

第一次运行前先装依赖：
    pip install requests beautifulsoup4

注意：脚本会保留 data.js 里已有的旧条目（按原文链接去重），
     所以它不会把历史数据冲掉，只会追加新条目。
"""

import argparse
import json
import os
import re
import time
from datetime import datetime

import requests
from bs4 import BeautifulSoup

BASE = "https://rsj.sh.gov.cn"
HERE = os.path.dirname(os.path.abspath(__file__))
OUT_FILE = os.path.join(HERE, "index.html")   # 数据直接写回页面里的 DATA 区

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/120.0 Safari/537.36"
}

# ==========================================================
# 1. 数据源：以后加别的官网，在这里照抄一行即可
#    column   = 栏目第一页地址
#    pattern  = 后续页地址模板，{n} 从 1 开始（第 2 页 = index_1.html）
#    pages    = 抓多少页
# ==========================================================
SOURCES = [
    {"name": "上海市人社局·规范性文件",
     "column": "/tgwgfx_17726/index.html",
     "pattern": "/tgwgfx_17726/index_{n}.html",
     "pages": 8},
    {"name": "上海市人社局·其他文件",
     "column": "/tgwqt_17736/index.html",
     "pattern": "/tgwqt_17736/index_{n}.html",
     "pages": 8},
]

# ==========================================================
# 2. 关键词规则：改这里就能控制"拉什么、不拉什么"
#    标题命中任一 INCLUDE、且不命中任何 EXCLUDE，才会保留
# ==========================================================
INCLUDE = [
    "保险", "社保", "公积金", "劳动", "工资", "薪", "工伤", "失业",
    "养老", "医疗", "生育", "个税", "税收", "补贴", "补助", "津贴",
    "人才", "职称", "技能", "培训", "派遣", "用工", "就业", "退休",
    "病假", "工时", "休假", "女职工", "未成年工", "集体合同", "年金",
    "档案", "招聘", "裁减", "辞退", "解除",
]

EXCLUDE = [
    "拟聘", "拟录用", "公示名单", "考试成绩", "准考证", "摇号",
    "招标", "采购", "中标", "搬迁公告", "关闭公告", "值班",
]

# 标题关键词 → 主题，从具体到宽泛依次匹配，命中第一个就停
CATEGORY_RULES = [
    ("公积金", "公积金"),
    ("个税", "个税"),
    ("税收", "个税"),
    ("补贴", "补贴"),
    ("补助", "补贴"),
    ("津贴", "补贴"),
    ("派遣", "劳动合同"),
    ("劳动合同", "劳动合同"),
    ("劳动", "劳动合同"),
    ("裁减", "劳动合同"),
    ("解除", "劳动合同"),
    ("工资", "劳动合同"),
    ("工时", "劳动合同"),
    ("休假", "劳动合同"),
    ("病假", "劳动合同"),
    ("社保", "社保"),
    ("社会保险", "社保"),
    ("保险", "社保"),
    ("养老", "社保"),
    ("工伤", "社保"),
    ("失业", "社保"),
    ("医疗", "社保"),
    ("生育", "社保"),
    ("退休", "社保"),
    ("年金", "社保"),
    ("职称", "人才与技能"),
    ("技能", "人才与技能"),
    ("培训", "人才与技能"),
    ("人才", "人才与技能"),
    ("就业", "人才与技能"),
    ("评审", "人才与技能"),
    ("招聘", "人才与技能"),
    ("高技能", "人才与技能"),
]


def guess_category(title):
    for kw, cat in CATEGORY_RULES:
        if kw in title:
            return cat
    return "其他"


def keep(title):
    if any(k in title for k in EXCLUDE):
        return False
    return any(k in title for k in INCLUDE)


# ==========================================================
# 3. 抓取
# ==========================================================
def get(url, tries=3):
    for i in range(tries):
        try:
            r = requests.get(BASE + url, headers=HEADERS, timeout=20)
            r.raise_for_status()
            r.encoding = r.apparent_encoding or "utf-8"
            return r.text
        except Exception as e:
            if i == tries - 1:
                print("  ! 抓取失败 %s：%s" % (url, e))
                return ""
            time.sleep(1.5)
    return ""


def parse_list(html):
    """从栏目页表格里取出：标题、文号、生成日期、链接"""
    soup = BeautifulSoup(html, "html.parser")
    rows = []
    for tr in soup.find_all("tr"):
        tds = tr.find_all("td")
        if len(tds) < 3:
            continue
        a = tds[0].find("a")
        if not a or not a.get("href"):
            continue
        title = a.get_text(" ", strip=True)
        if not title:
            continue
        doc_no = tds[1].get_text(strip=True)
        date = tds[2].get_text(strip=True)
        if not re.match(r"20\d\d-\d\d-\d\d", date):
            continue
        rows.append({
            "t": title,
            "no": doc_no,
            "d": date,
            "u": BASE + a["href"] if a["href"].startswith("/") else a["href"],
        })
    return rows


def _strip_refs(text):
    """去掉《文件名》（文号）这类引用，只留主干"""
    text = re.sub(r"《[^》]*》\s*(（[^）]*）|〔[^〕]*〕)?", "", text)
    text = re.sub(r"（[^）]*）", "", text)
    text = re.sub(r"[，、]{2,}", "，", text)
    return text.strip("，、 ")


def fetch_summary(url):
    """
    截一句"这份文件管什么"的摘要。
    公文的目的段通常以"为……"或"根据……"开头，比第一段
    "××局、各有关单位："有用得多；抽不出来就返回空字符串，
    页面直接不显示摘要那一行，不硬凑。
    """
    html = get(url.replace(BASE, ""))
    if not html:
        return ""
    soup = BeautifulSoup(html, "html.parser")

    paras = []
    for p in soup.find_all("p"):
        text = re.sub(r"\s+", "", p.get_text(" ", strip=True))
        if len(text) > 25:
            paras.append(text)

    for text in paras:
        if not text.startswith(("为", "根据", "按照")):
            continue
        core = _strip_refs(text)
        for cut in ("现通知如下", "现印发", "现公布", "现将", "现予"):
            core = core.split(cut)[0]
        core = re.sub(r"现就.{0,24}如下[：:]?$", "", core)
        core = core.strip("，、 ")
        # 引用被删干净后只剩"为贯彻，的规定"这类空壳，跳过
        if re.search(r"为(贯彻|落实|深入|加强)[，、。]", core):
            continue
        if len(core) < 28 or "我们制定了" in core or "我们研究" in core:
            continue
        parts = [x for x in core.split("，") if x]
        # "根据规定""按照要求"这类空壳分句直接丢掉
        parts = [x for x in parts if not re.match(r"^(根据|按照|依据|参照|遵照).{0,10}$", x)]
        if not parts:
            continue
        out = parts[0]
        for x in parts[1:]:
            if len(out) + len(x) > 66:
                break
            out += "，" + x
        out = re.sub(r"。(。)+", "。", out.strip("，。") + "。")
        if len(out) >= 26:
            return out[:76] + ("…" if len(out) > 76 else "")

    # 目的段抽不出来时，退一步用"一、……"这类正文首条（往往是调整/标准/范围）
    for text in paras:
        if not re.match(r"^(一、|（一）|1\.)", text):
            continue
        body = re.sub(r"^(一、|（一）|1\.)", "", text).strip()
        if len(body) < 30:
            continue
        parts = [x for x in body.split("，") if x]
        out = parts[0]
        for x in parts[1:]:
            if len(out) + len(x) > 66:
                break
            out += "，" + x
        out = out.strip("，、 ")
        # 以"；"结尾的多是告知承诺书里的表格栏目，不是正文，丢掉
        if out.endswith(("；", ";", "：", ":")) or "下列" in out or len(out) < 26:
            continue
        return out[:76] + ("。" if len(out) <= 76 else "…")
    return ""


# ==========================================================
# 4. 读写 data.js
# ==========================================================
def load_existing():
    if not os.path.exists(OUT_FILE):
        return [], {}
    if not os.path.exists(OUT_FILE):
        return [], {}
    raw = open(OUT_FILE, encoding="utf-8").read()
    items, meta = [], {}
    m = re.search(r"window\.POLICY_DATA\s*=\s*(\[[\s\S]*?\]);", raw)
    if m:
        try:
            items = json.loads(m.group(1))
        except Exception as e:
            print("  ! 旧 data.js 解析失败，将重新生成：%s" % e)
    m = re.search(r"window\.POLICY_META\s*=\s*([\s\S]*?);\s*(?:\n|$)", raw)
    if m:
        try:
            meta = json.loads(m.group(1))
        except Exception:
            meta = {}
    return items, meta


def save(items, meta):
    """把数据写回 index.html 里 DATA:START 与 DATA:END 之间的区间（用字符串定位，不用正则）"""
    items.sort(key=lambda i: (i.get("d", ""), i.get("t", "")), reverse=True)
    payload = json.dumps(items, ensure_ascii=False, separators=(",", ":"))
    block = (
        "/* ===== DATA:START 数据区，由 fetch_policies.py 自动写入 ===== */\n"
        "window.POLICY_DATA = " + payload + ";\n"
        "window.POLICY_META = " + json.dumps(meta, ensure_ascii=False, separators=(",", ":")) + ";\n"
        "/* ===== DATA:END 数据区结束 ===== */"
    )
    raw = open(OUT_FILE, encoding="utf-8").read()
    start = raw.find("/* ===== DATA:START")
    end = raw.find("/* ===== DATA:END")
    if start == -1 or end == -1 or end < start:
        raise SystemExit("！index.html 里找不到 DATA 标记，请确认标记行没被删掉")
    end_of_line = raw.find("\n", end)
    new_raw = raw[:start] + block + raw[end_of_line:]
    tmp = OUT_FILE + ".tmp"
    open(tmp, "w", encoding="utf-8").write(new_raw)
    os.replace(tmp, OUT_FILE)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pages", type=int, default=0, help="每个栏目抓多少页，0=用配置里的值")
    ap.add_argument("--no-summary", action="store_true", help="跳过详情页，不抓摘要")
    ap.add_argument("--max-summary", type=int, default=40, help="本次最多抓多少条摘要")
    args = ap.parse_args()

    existing, old_meta = load_existing()
    known_urls = {i.get("u") for i in existing}
    new_items = []

    for src in SOURCES:
        pages = args.pages or src["pages"]
        print("== %s（%d 页）" % (src["name"], pages))
        for p in range(1, pages + 1):
            # 站点约定：第 1 页是 index.html，第 N 页是 index_N.html
            url = src["column"] if p == 1 else src["pattern"].format(n=p)
            html = get(url)
            if not html:
                continue
            rows = parse_list(html)
            kept = 0
            for row in rows:
                if not keep(row["t"]):
                    continue
                if row["u"] in known_urls:
                    continue
                row["s"] = src["name"].split("·")[0]
                row["c"] = guess_category(row["t"])
                row["x"] = ""
                new_items.append(row)
                known_urls.add(row["u"])
                kept += 1
            print("  第 %d 页：%d 条，命中关键词 %d 条" % (p, len(rows), kept))
            time.sleep(0.8)

    # 摘要：新条目 + 之前没抓到的旧条目，按日期从新到旧补，控制数量
    all_items = existing + new_items
    if not args.no_summary:
        need = sorted([i for i in all_items if not i.get("x")],
                      key=lambda i: i.get("d", ""), reverse=True)
        todo = need[:args.max_summary]
        if todo:
            print("== 抓取摘要（%d 条，待补 %d 条）" % (len(todo), len(need)))
            for i, item in enumerate(todo, 1):
                item["x"] = fetch_summary(item["u"])
                print("  [%d/%d] %s" % (i, len(todo), item["t"][:26]))
                time.sleep(0.6)

    all_items = existing + new_items
    meta = dict(old_meta)
    meta["fetchedAt"] = datetime.now().strftime("%Y-%m-%d %H:%M")
    meta["sources"] = [s["column"] for s in SOURCES]
    meta["total"] = len(all_items)

    save(all_items, meta)
    print("\n完成：新增 %d 条，累计 %d 条 → %s" % (len(new_items), len(all_items), OUT_FILE))
    if new_items:
        print("下一步：把 data.js 和 index.html 一起重新上传到 GitHub，网站会在 1 分钟后更新。")


if __name__ == "__main__":
    main()
#（注：内容由AI生成）
