#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
把一轮分析的结果整理成两张表，给飞书多维表格导入用。只有两张：

  表一 · 原话+打标   每行一条客户原话，带上打的标，以及它被哪条行动用作依据
  表二 · 行动        每行一条行动。前 7 格 AI 填，后 4 格（责任人 / 验证日期 / 状态 / 复盘结论）留空给人

两张表靠「依据的原话」「用在哪条行动上」连起来：点开一条行动，能看到它是凭哪几条原话提的。
三条线（退货 / 评论 / Reddit）同表存、不混算：表一有「来源」这一格。
飞书里只放人要看的；脚本算数用的全量明细留在本地。

用法:
  python export_tables.py tagged.csv insights.json --source 退货 --outdir outputs/两张表
"""
import argparse, json, os, sys
from voc_common import pd, SEP


def five(t):
    """「怎么才算做完」按五样写全。"""
    if t.get("metric"):
        parts = [f"看哪个数：{t['metric']}", f"现在：{t.get('now','—')}", f"要到：{t.get('target','—')}",
                 f"哪天看：{t.get('when','—')}"]
        if t.get("if_not"):
            parts.append(f"要是没变：{t['if_not']}")
        return "\n".join(parts)
    return t.get("kpi", "")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("tagged")
    ap.add_argument("insights")
    ap.add_argument("--source", required=True, choices=["退货", "评论", "Reddit"])
    ap.add_argument("--outdir", default="outputs/两张表")
    a = ap.parse_args()

    d = pd.read_csv(a.tagged, dtype=str).fillna("")
    ins = json.load(open(a.insights, encoding="utf-8"))
    todo = ins.get("todo", [])
    prefix = {"退货": "退", "评论": "评", "Reddit": "R"}[a.source]

    used = {}
    for t in todo:
        for r in t.get("refs", []):
            used.setdefault(str(r), []).append(t.get("id", ""))

    good_bad = d["整体好坏"] if "整体好坏" in d.columns else ("差评" if a.source == "退货" else "")
    if "谁在说" in d.columns:
        who = d["谁在说"]
    else:                                              # Reddit：这人到哪一步了、说的是谁的货
        who = d.apply(lambda r: SEP.join(x for x in (r.get("到哪一步", ""),
                      ("说的是" + r["说谁的货"]) if r.get("说谁的货") else "") if x), axis=1)
    if "哪件事_细项" in d.columns:                      # 退货线：说到的事都是抱怨
        what = d["哪件事_细项"]
    else:                                              # 评论 / Reddit：好的和差的分开记，合到一格里时标清楚
        what = d.apply(lambda r: SEP.join(
            [f"好·{t.strip()}" for t in str(r.get("好评的事", "")).split(";") if t.strip()] +
            [f"差·{t.strip()}" for t in str(r.get("差评的事", "")).split(";") if t.strip()]), axis=1)
    col = lambda name: d[name] if name in d.columns else ""
    t1 = pd.DataFrame({
        "编号": d["序号"].map(lambda x: f"{prefix}-{int(x):03d}"),
        "来源": a.source,
        "产品": d["产品"] if "产品" in d.columns else ins.get("product", ""),
        "原话": d["原话"],
        "中文意思": d["中文意思"] if "中文意思" in d.columns else "",
        "谁在说": who,
        "什么情况下": d["什么情况下"] if "什么情况下" in d.columns else col("帖子类型"),
        "说的哪件事": what,
        "好还是不好": good_bad,
        "该谁改": col("该谁改"),
        "多严重": col("多严重"),
        "能不能挽回": col("能否挽回"),
        "用在哪条行动上": d["序号"].map(lambda x: SEP.join(used.get(str(x), []))),
    })
    t2 = pd.DataFrame([{
        "行动编号": t.get("id", ""),
        "产品": ins.get("product", ""),
        "问题": t.get("problem", ""),
        "动作": t.get("body", ""),
        "哪个部门": t.get("owner", ""),
        "用在哪": t.get("use", t.get("attr", "")),
        "哪一档": t.get("tier", ""),
        "怎么才算做完": five(t),
        "依据的原话": SEP.join(f"{prefix}-{int(r):03d}" for r in t.get("refs", [])),
        "依据条数": len(t.get("refs", [])) or t.get("n", ""),
        "责任人": "", "验证日期": "", "状态": "没开始", "复盘结论": "",
    } for t in todo])

    os.makedirs(a.outdir, exist_ok=True)
    p1 = os.path.join(a.outdir, f"表一-原话和打标-{a.source}.csv")
    p2 = os.path.join(a.outdir, f"表二-行动-{a.source}.csv")
    t1.to_csv(p1, index=False, encoding="utf-8-sig")
    t2.to_csv(p2, index=False, encoding="utf-8-sig")
    print(json.dumps({"表一": os.path.abspath(p1), "表一行数": len(t1),
                      "表二": os.path.abspath(p2), "表二行数": len(t2),
                      "被行动引用到的原话": int((t1["用在哪条行动上"] != "").sum())},
                     ensure_ascii=False, indent=2))
    print("\n提醒：「验证日期」在飞书里要建成日期格，不要建成文字格——文字格发不出到期提醒。")


if __name__ == "__main__":
    main()
