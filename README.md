# 人力资源政策雷达（上海）

一个只给自己用的政策信息站：每天扫一眼上海人社局新出的政策，按主题筛、按关键词搜、点开原文；另有一个本地资料柜，用来登记常用的政策原文、解读、公司制度和个人笔记。

前端是一个单文件网页（`index.html`），数据由本地脚本从官网抓取后写进页面，不需要服务器、不需要数据库、不需要账号。

## 项目结构

```
hr-policy/
├─ index.html          页面本体，含样式、交互和抓取到的数据（DATA 区由脚本写入）
├─ fetch_policies.py   抓取脚本：抓官网 → 按关键词筛选 → 写回 index.html
├─ requirements.txt    脚本依赖
├─ sources.md          数据来源清单与抓取规则
├─ 一键更新.bat        Windows 双击运行
├─ 一键更新.sh         macOS / Linux 运行
├─ LICENSE             MIT 开源协议
└─ README.md           本文件
```

## 快速开始

需要 Python 3.8 以上（Windows 装 Python 时勾选 "Add Python to PATH"）。

**Windows**：双击 `一键更新.bat`。

**macOS / Linux**：

```bash
cd hr-policy
python3 -m pip install -r requirements.txt
python3 fetch_policies.py
```

跑完打开 `index.html` 就能看到最新抓取的内容。

## 日常怎么用

1. 每周（或每天）跑一次脚本，它会抓官网两个栏目的前 8 页，按关键词筛选后追加新条目，已抓过的不会重复。
2. 打开 `index.html` 自己先看一眼，确认排版没坏。
3. 把 `index.html` 重新上传到 GitHub，网站一分钟左右自动更新。

脚本参数：

| 参数 | 作用 | 示例 |
|---|---|---|
| `--pages N` | 每个栏目只抓前 N 页，调试用 | `python fetch_policies.py --pages 2` |
| `--no-summary` | 不进详情页抓摘要，速度最快 | `python fetch_policies.py --no-summary` |
| `--max-summary N` | 本次最多补多少条摘要，默认 40 | `python fetch_policies.py --max-summary 10` |

## 想改点什么

| 想改 | 改哪里 |
|---|---|
| 抓哪些栏目、抓几页 | `fetch_policies.py` 里的 `SOURCES` |
| 关键词保留 / 排除 | `fetch_policies.py` 里的 `INCLUDE`、`EXCLUDE` |
| 分类规则（社保 / 劳动合同 / 补贴…） | `fetch_policies.py` 里的 `CATEGORY_RULES`，以及 `index.html` 里的 `CATS` |
| 配色、字号、圆角、宽度 | `index.html` 开头的「① 设计令牌」 |
| 顶部公告位、底部追加模块 | `index.html` 里的「预留位 A / B」，去掉 `hidden` 即可 |

## 部署到 GitHub Pages

1. 新建一个 **Public** 仓库，名字例如 `hr-policy`。
2. 把 `index.html` 上传到仓库根目录（其他文件可选）。
3. 仓库 `Settings` → `Pages` → Source 选 `Deploy from a branch`，分支 `main`，目录 `/ (root)`，保存。
4. 等 1–2 分钟，得到 `https://你的用户名.github.io/hr-policy/`，手机电脑都能打开。

`index.html` 必须是仓库根目录下的这个名字，GitHub Pages 只认它当首页。

## 已知限制

- **纯静态**：网页本身不能抓取官网（浏览器有跨域限制），所以更新靠本地脚本跑完再上传，不是打开页面就自动刷新。
- **资料库存在浏览器里**：登记信息保存在 `localStorage`，换设备或清缓存会丢，需要「导出备份」迁移；文件本体（PDF / Word）传不上去，要等后端阶段。
- **摘要不全**：目前靠规则从公文目的段截取，约一成条目能抽到；没抽到就不显示，不硬凑。要全覆盖需要接模型生成（第二阶段）。
- **公众号还没接**：官网结构稳定优先做，公众号有反爬限制、页面结构会变，放在后面。
- **官网改版会让脚本失效**：站点结构一变，`parse_list` 就需要跟着调整，这是这类抓取脚本的固有成本。

## 数据与免责

政策内容版权归原发布单位，本仓库只做索引与链接，不替代原文。涉及具体处置（解除劳动合同、工伤、社保申报等），以官网原文和主管部门答复为准。

## 许可

MIT，见 `LICENSE`。
