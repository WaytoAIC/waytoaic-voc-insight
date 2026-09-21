## 🚀 Way to AIC | 通往 AI 电商之路
---
### 🌐 官网 Website
- https://waytoaic.com
- https://www.waytoaic.com
---

### 👥 社群招募 Community
`Way to AIC 社群招募 | WaytoAIC.com`

<p align="center">
  <img src="https://github.com/user-attachments/assets/d9f8bbf4-2056-4780-975d-86c885b52bab" width="70%">
</p>

---

### 📣 公众号 WeChat Official Account
`维正 WaytoAIC`

<p align="center">
  <img src="https://github.com/user-attachments/assets/71c71a5c-e68a-4f30-9afb-f2b056619991" width="300">
</p>

---

### 🧠 知识星球 Xiaozhixing
`AI电商之路 WaytoAIC`

<p align="center">
  <img src="https://github.com/user-attachments/assets/9eccef07-0e84-45a7-a415-affcb18c928d" width="200">
  <img src="https://github.com/user-attachments/assets/4e99fbc3-1981-4fee-b113-c9821141102d" width="400">
</p>

---

### 🧩 About Way to AIC

**AIC = AI Commerce**

在 AI 重塑商业的时代，我们希望和每一个拥抱 AI 的卖家：

- 找到场景
- 定义问题
- 积累能力
- 设计系统

共同通往 AI 电商之路。

> Way to AIC 不是教学，不是工具，
> 而是一条所有电商人共同走的进化之路。

### WaytoAIC 理念 | Principles

| 中文 | English |
|---|---|
| 场景先于方法 | Context before method |
| AI 的价值来自真实业务场景，而不是技术本身。 | AI creates value through real business contexts, not through technology alone. |
| 问题先于答案 | Problem before answer |
| 定义问题，比拥有工具更重要。 | Defining the problem matters more than collecting tools. |
| 系统胜过技巧 | System over tricks |
| 技巧是术，系统才是道，决定卖家的上限。 | Tricks are tactical; systems define long-term leverage and ceiling. |
| 共创优于独行 | Co-creation over solo progress |
| 我们相信，真正的进化发生在共同探索的过程中。 | Real evolution happens through shared exploration. |

---

# voc-insight · 把客户的声音读成"该谁改、怎么改、改完怎么验"

一个品类无关的 VOC（客户声音）分析 Skill。换品类只换一份配置，不改脚本。

- **基础版**：亚马逊退货原因 + 商品评论
- **进阶版**：再加 Reddit 讨论（先分流，再各用各的方法）

先采集，再分析；不同来源用不同的分析方式；分析完必须变成行动；行动到期要复盘；每一环留下点东西，攒起来才是资产。
**AI 不是全程都上**：只有"一条一条读原话贴标签"和"写洞察"交给 AI；清洗、算数、画图全是脚本；判断和动作全是人。脚本不编故事，AI 不算数字。

## 快速安装

```bash
curl -fsSL https://raw.githubusercontent.com/WaytoAIC/waytoaic-voc-insight/main/install.sh | bash            # Claude Code
curl -fsSL https://raw.githubusercontent.com/WaytoAIC/waytoaic-voc-insight/main/install.sh | bash -s -- --target codex
```

装完 `pip install -r requirements.txt`（pandas / openpyxl / numpy），重开会话。

## 它产出什么

| 产物 | 说明 |
|---|---|
| 网页报告 | 退货：漏斗、两头是否对称、平台原因对真实原因的连线图、该谁改、严重档构成、原话查阅。评论：散点图、好评差评双色条、按月走势、因果链、行动卡 |
| Excel | 统计全部用公式连着明细，业务自己改一个标签，数字跟着变 |
| 两张表 | 「原话+打标」「行动」，可直接导入飞书多维表格；每条行动都挂着它依据的原话 |

每条行动按五样写全：看哪个数 · 现在多少 · 要到多少 · 哪天看 · **要是没变说明什么**。复盘不是回忆，是到日子回来读这个数。

## 目录

- `skill/` Skill 本体：`SKILL.md`、`references/01–09`、`scripts/`、`assets/`、`品类配置/`
- `samples/AI眼镜配件/` 示例数据与三条线跑出来的成品。**示例全部是编的**，不对应任何真实订单、买家、群组

第一次用，照 `samples/AI眼镜配件/README.md` 把示例从头跑一遍；换成自己的品类，看 `skill/references/01` 和 `03`（怎么从零做出自己的标签表）。

## 合规

Reddit 的讨论只能人手动、低频、只读地拿；不存库、不设定时任务、不拿去训练模型；作者名不留。详见 `skill/references/09`。

---

# voc-insight · Turn customer voice into "who fixes it, how, and how to verify"

A category-agnostic VOC analysis Skill for e-commerce sellers. Switch category by swapping one config file — no code changes.

- **Basic**: Amazon return reasons + product reviews
- **Advanced**: plus Reddit discussions (triage first: where the person is in the journey × whose product they are talking about)

**AI is not used end to end.** Only two jobs go to the model: reading each verbatim to tag it, and writing the insight narrative. Cleaning, maths and charts are deterministic scripts; judgement and action stay with people. *Scripts do not tell stories; the model does not do arithmetic.*

Outputs: an HTML report (funnel, two-sided symmetry check, platform-reason vs real-reason flow chart, scatter plot, monthly trend, causal chains, action cards, verbatim browser), an Excel workbook whose statistics are live formulas over the tagged rows, and two import-ready tables (*verbatim + tags*, *actions*) where every action links back to the verbatims it rests on.

Every action carries five things: which number to watch · where it is now · where it should get to · when to look · **what it means if it does not move**.

All sample data is fictional. Docs and tag names are in Chinese.

## License

MIT
