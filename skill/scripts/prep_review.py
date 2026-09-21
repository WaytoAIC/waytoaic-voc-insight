#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
评论线 · 第 1 步 清洗

做五件事并打印一份数据体检：
  1. 剔掉送测评论（不是真实购买的人写的，留着好评率整体虚高）
  2. 去掉没写字的
  3. 解析日期、算月份
  4. 标出疑似刷的评论 —— 只标记，不删
  5. 从规格里读出属性（读不出就停，不许猜）

用法:
  python prep_review.py 评论导出.csv --config 品类配置/你的品类.json \
      --product "A款-防滑鼻托套装" --out work/cleaned.csv --report work/prep.json
"""
import argparse, re, sys
from voc_common import pd, load_config, read_any, parse_dates, dump

try:
    import numpy as np
except ImportError:
    sys.exit("缺少依赖。先安装：pip install -r requirements.txt")


def clean_cell(s):
    return "" if pd.isna(s) else str(s).strip().strip("[]").strip('"').strip()


def parse_attr(value, rules):
    low = str(value).lower()
    return next((name for name, pat in rules if re.search(pat, low)), "读不出")


def flag_suspect(df, rule):
    """疑似刷的：同一天 + 同一规格 + 星级够高 + 明显比别人写得长。只标记不删。"""
    n = len(df)
    no = pd.Series(["否"] * n, index=df.index)
    if n < 10:
        return no, pd.Series([""] * n, index=df.index)
    length = df["原话"].str.len()
    thr = length.mean() + float(rule.get("长度超过均值几个标准差", 1.0)) * length.std()
    key = ["日期"] + (["规格"] if "规格" in df.columns else [])
    grp = df.groupby(key)["原话"].transform("size")
    star = pd.to_numeric(df["星级"], errors="coerce")
    hi = star >= int(rule.get("星级至少", 5))
    hit = (length > thr) & (grp >= int(rule.get("同日同规格至少几条", 2))) & hi
    why = pd.Series(np.where(hit, f"同一天同一规格 + {int(rule.get('星级至少', 5))} 星 + 写得特别长", ""), index=df.index)
    # 第二条判据：高星、够长、开头几乎一样的（模板味）。取正文前 8 个词比
    k = int(rule.get("开头取几个词", 5))
    body = df["原话"].str.split(". ", n=1).str[-1]
    head = body.str.lower().str.replace(r"[^a-z\u4e00-\u9fff ]", "", regex=True).str.split().str[:k].str.join(" ")
    same = head.map(head[hi & (length > length.median())].value_counts()).fillna(0)
    hit2 = hi & (length > length.median()) & (same >= int(rule.get("开头相同至少几条", 2))) & (head.str.len() > 20)
    why = why.where(~(hit2 & ~hit), "高星 + 开头和别的评论几乎一样")
    hit = hit | hit2
    return pd.Series(np.where(hit, "是", "否"), index=df.index), why


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("src")
    ap.add_argument("--config", required=True)
    ap.add_argument("--product", default=None)
    ap.add_argument("--site", default=None)
    ap.add_argument("--out", default="cleaned.csv")
    ap.add_argument("--report", default=None)
    a = ap.parse_args()

    cfg = load_config(a.config)
    col = dict(cfg["输入列"]["评论"])
    df, enc = read_any(a.src)
    must = ["送测标记", "原话", "星级", "时间"]
    missing = [f"{k}（你的列名填的是「{col.get(k,'')}」）" for k in must
               if not col.get(k) or col[k] not in df.columns]
    if missing:
        sys.exit("[前提不满足] 表里找不到这些必需的列：\n  " + "\n  ".join(missing) +
                 f"\n表里现有的列：{list(df.columns)}\n"
                 "没有「送测标记」这一列的话，送测评论剔不掉，好评率会整体虚高——先补这一列再跑。")
    raw_n = len(df)
    if a.product and col.get("产品") in df.columns:
        df = df[df[col["产品"]].astype(str).str.strip() == a.product].copy()
        if not len(df):
            sys.exit(f"[参数不对] 产品「{a.product}」没有数据。")
    if a.site and col.get("站点") in df.columns:
        df = df[df[col["站点"]].astype(str).str.strip() == a.site].copy()
    scoped_n = len(df)

    vine = df[col["送测标记"]].astype(str).str.strip().str.upper().isin(["TRUE", "1", "YES", "Y", "是"])
    vine_n = int(vine.sum())
    d = df[~vine].copy().reset_index(drop=True)

    ren = {col["原话"]: "原话", col["星级"]: "星级", col.get("站点", ""): "站点", col.get("规格", ""): "规格",
           col.get("品名", ""): "品名", col.get("产品", ""): "产品", col.get("记录编号", ""): "记录编号"}
    d = d.rename(columns={k: v for k, v in ren.items() if k and k in d.columns and k != v})
    for c in ("站点", "规格", "品名", "产品"):
        if c in d.columns:
            d[c] = d[c].map(clean_cell)
    d["原话"] = d["原话"].fillna("").astype(str).str.strip()
    empty_n = int((d["原话"].str.len() == 0).sum())
    d = d[d["原话"].str.len() > 0].reset_index(drop=True)
    before = len(d)
    d = d.drop_duplicates(subset=["原话"]).reset_index(drop=True)      # 整段一字不差的只留一条
    dup_n = before - len(d)

    dt = parse_dates(d[col["时间"]])
    if len(d) and dt.isna().all():
        sys.exit("[前提不满足] 时间那一列解析不成日期。")
    d["日期"] = dt.dt.strftime("%Y-%m-%d")
    d["月份"] = dt.dt.to_period("M").astype(str)
    bad_dates = int(dt.isna().sum())

    d["疑似不可信"], d["疑似原因"] = flag_suspect(d, cfg.get("疑似刷评", {}))

    attr_cols, unreadable = [], {}
    for rule in cfg.get("规格解析", []):
        src = "规格" if rule["来源"] == "规格" else rule["来源"]
        if src not in d.columns:
            continue
        d[rule["列名"]] = d[src].map(lambda v: parse_attr(v, rule["规则"]))
        attr_cols.append(rule["列名"])
        bad = sorted(set(d.loc[d[rule["列名"]] == "读不出", src].astype(str)))[:5]
        if bad:
            unreadable[rule["列名"]] = bad

    d.insert(0, "序号", range(1, len(d) + 1))
    order = (["序号", "记录编号", "星级", "站点", "品名", "产品", "规格"] + attr_cols +
             ["日期", "月份", "疑似不可信", "疑似原因", "原话"])
    d[[c for c in order if c in d.columns]].to_csv(a.out, index=False, encoding="utf-8-sig")

    star = pd.to_numeric(d["星级"], errors="coerce")
    rep = {
        "品类": cfg["品类"], "配置版本": cfg.get("版本", ""), "文件编码": enc,
        "原始条数": raw_n, "本次范围": {"产品": a.product or "全部", "站点": a.site or "全部", "条数": scoped_n},
        "剔掉送测": vine_n, "剔掉没写字的": empty_n, "剔掉整段重复的": dup_n, "进入分析": len(d),
        "疑似刷的": int((d["疑似不可信"] == "是").sum()),
        "差评占比_1到2星": round(float((star <= 2).mean()), 3) if len(d) else None,
        "平均星级": round(float(star.mean()), 2) if len(d) else None,
        "星级分布": {str(int(k)): int(v) for k, v in star.value_counts().sort_index().items()},
        "时间跨度": [d["月份"].min(), d["月份"].max()] if len(d) else None,
        "站点分布": d["站点"].value_counts().to_dict() if "站点" in d.columns else {},
        "规格分布": d["规格"].value_counts().to_dict() if "规格" in d.columns else {},
        "属性分布": {k: d[k].value_counts().to_dict() for k in attr_cols},
    }
    warn = {}
    if len(d) < 30:
        warn["样本量"] = "有效评论不到 30 条：只通读，不要出任何比例。"
    elif len(d) < 50:
        warn["样本量"] = "不到 50 条：低于建议下限，比例只能看方向。"
    elif len(d) < 200:
        warn["样本量"] = "50–200 条：可以判方向；分组之后每组很薄，要注明。200 条以上才做细分对比。"
    mc = d["月份"].value_counts()
    if len(mc) >= 4 and mc.iloc[0] >= 0.4 * len(d) and mc.iloc[0] >= 3 * mc.median():
        warn["评论来得不自然"] = (f"{mc.index[0]} 一个月就有 {int(mc.iloc[0])} 条，占全部的 {mc.iloc[0]/len(d):.0%}，是平常月份的好几倍。"
                            "正常卖货的评论不会这样来。好评的水平要打折看；按月走势不要拿来下结论。")
    warn["先确认是不是全量"] = "第三方工具常常只给一部分评论。对一下商品页面上显示的评论总数；差得多的话，写进「这批数据答不了什么」。"
    if bad_dates:
        warn["日期解析"] = f"有 {bad_dates} 条的时间解析不出来，这些条不进按月统计。"
    if unreadable:
        warn["规格读不出"] = unreadable
    rep["提醒"] = warn
    print(dump(rep, a.report))
    hard = [r_["列名"] for r_ in cfg.get("规格解析", []) if r_.get("读不出", "报错") == "报错" and r_["列名"] in unreadable]
    if hard:
        sys.exit("\n[停] 有规格读不出属性。不要猜，去问负责人补规则。")


if __name__ == "__main__":
    main()
