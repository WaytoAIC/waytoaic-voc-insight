#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
跨款汇总表：把这一轮的结果压成一行，接到汇总表后面。

单份报告只回答"这一款怎么了"；跑过四五款之后，汇总表回答的是
"这是这一款的问题，还是整条产品线的通病"。

退货、评论、Reddit 三条线都写进同一张表，用「来源」一栏区分——同表存，不混算：
比的时候只拿同一个来源的行互相比。

用法:
  python fingerprint.py work/tagged.csv --source 退货 --config 品类配置/xx.json \
      --prep work/prep.json --master work/跨款汇总表.csv
"""
import argparse, os, sys
from voc_common import pd, load_config, split_cell, base_tag, dump


def l1_of(cfg):
    m = {}
    for l1, subs in cfg["哪件事"]["细项"].items():
        for t in subs:
            m[t if isinstance(t, str) else t["名称"]] = l1
    return m


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("tagged")
    ap.add_argument("--source", required=True, choices=["退货", "评论", "Reddit"])
    ap.add_argument("--config", required=True)
    ap.add_argument("--prep", default=None)
    ap.add_argument("--master", default="跨款汇总表.csv")
    a = ap.parse_args()

    cfg = load_config(a.config)
    d = pd.read_csv(a.tagged, dtype=str).fillna("")
    import json
    p = json.load(open(a.prep, encoding="utf-8")) if a.prep else {}
    n = len(d)
    if n < 30:
        sys.exit(f"[样本不够] 只有 {n} 条（不到 30）。小样本的比例没法跟别的款比，写进去会把汇总表搞脏，这一轮不写。")

    neg_col = "哪件事_细项" if "哪件事_细项" in d.columns else "差评的事"
    judged = d[d[neg_col].str.strip() != ""] if neg_col == "差评的事" else d
    nj = max(1, len(judged))
    attrs = [x["名称"] for x in cfg["该谁改"]]
    l1map, l1s = l1_of(cfg), cfg["哪件事"]["大类顺序"]
    hit_l1 = {l1: int(judged[neg_col].map(
        lambda v, l1=l1: any(l1map.get(base_tag(t)) == l1 for t in split_cell(v))).sum()) for l1 in l1s}
    scope = p.get("本次范围", {})
    top_sev = cfg["多严重"][0]
    row = {
        "产品": scope.get("产品", ""), "来源": a.source, "站点": scope.get("站点", ""),
        "期间": " ~ ".join(p.get("时间跨度") or []), "有效条数": n, "其中有抱怨的": len(judged),
        "写了原因的占比": (p.get("原话") or {}).get("覆盖率", ""),
        # 只在填了「整体好坏」的人里算（Reddit 上还没买的人不填这一格，不能算进分母）
        "整体好评占比": round(float((d.loc[d["整体好坏"] != "", "整体好坏"] == cfg.get("整体好坏", ["好评"])[0]).mean()), 3)
                        if "整体好坏" in d.columns and (d["整体好坏"] != "").any() else "",
        "好评占比的分母": int((d["整体好坏"] != "").sum()) if "整体好坏" in d.columns else "",
        **{f"该谁改·{x}": round(int((judged["该谁改"] == x).sum()) / nj, 3) for x in attrs},
        **{f"抱怨·{l1}": round(hit_l1[l1] / nj, 3) for l1 in l1s},
        "严重占比": round(int((judged["多严重"] == top_sev).sum()) / nj, 3),
        "能挽回占比": round(int((d["能否挽回"] == "是").sum()) / n, 3) if "能否挽回" in d.columns else "",
        "标签表版本": cfg.get("版本", ""),
        "生成时间": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M"),
    }
    new = pd.DataFrame([row])
    if os.path.exists(a.master):
        old = pd.read_csv(a.master, dtype=str)
        key = (old["产品"] == str(row["产品"])) & (old["来源"] == a.source) & (old["期间"] == row["期间"])
        old = old[~key]                                   # 同一款同一来源同一期间重跑，覆盖旧的那一行
        new = pd.concat([old, new.astype(str)], ignore_index=True)
    new.to_csv(a.master, index=False, encoding="utf-8-sig")
    print(dump(row))
    print(f"\n已写入 {os.path.abspath(a.master)}（现在共 {len(new)} 行）")
    if len(new) >= 2:
        print("\n提醒：比之前先对齐四件事——口径一样吗、站点一样吗、标签表是同一版吗、来源一样吗。"
              "受材料直接决定的那几项，不同材料的款之间不比。")


if __name__ == "__main__":
    main()
