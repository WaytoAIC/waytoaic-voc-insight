#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
退货线 · 第 1 步 清洗 + 第 1.5 步 先看大盘

做七件事并打印一份数据体检：
  1. 只留"退货"这一类记录（换货用的是另一套数字原因码，混进来规则全错）
  2. 原因码逐个对清单，出现不认识的码直接停
  3. 按留 / 剔分流
  4. 去掉没写字的
  5. 去掉平台套话（下拉选项|客户写的|是否愿意被联系 → 只留中间）
  6. 从规格里读出属性（读不出就停，不许猜）
  7. 原因码大盘：各占多少；两头属性在原因码层是否对称

用法:
  python prep_return.py 原始导出.csv --config 品类配置/你的品类.json \
      --product "A款-防滑鼻托套装" --out work/cleaned.csv --report work/prep.json
"""
import argparse, html, re, sys
from voc_common import (pd, load_config, read_any, parse_dates, bands_of, symmetry, dump)


def clean_voice(raw, head, tail):
    """去平台套话。洗完是空的就返回空串，由调用方剔除。

    像 "Defective|N/A" 这种只有下拉选项、客户一个字没写的，留着会让某类问题整体虚高。
    """
    s = html.unescape(html.unescape(str(raw))).strip().strip('"').strip()
    parts = [p.strip() for p in s.split("|")]
    if parts and parts[0].lower() in head:
        parts = parts[1:]
    parts = [p for p in parts if p.lower() not in tail]
    if not parts:
        return ""
    return re.sub(r"\s+", " ", " — ".join(parts)).strip().strip('"').strip()


def parse_attr(value, rules):
    low = str(value).lower()
    return next((name for name, pat in rules if re.search(pat, low)), "读不出")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("src")
    ap.add_argument("--config", required=True)
    ap.add_argument("--product", default=None, help="只分析某一个产品")
    ap.add_argument("--site", default=None, help="只分析某一个站点，如 US")
    ap.add_argument("--out", default="cleaned.csv")
    ap.add_argument("--report", default=None)
    a = ap.parse_args()

    cfg = load_config(a.config)
    col = dict(cfg["输入列"]["退货"])
    keep, drop = cfg["原因码"]["留"], cfg["原因码"]["剔"]
    head = {x.lower() for x in cfg["平台套话"]["开头"]}
    tail = {x.lower() for x in cfg["平台套话"]["结尾"]}

    df, enc = read_any(a.src)
    must = ["原因码", "原话", "产品", "时间"]
    missing = [f"{k}（你的列名填的是「{col.get(k,'')}」）" for k in must
               if not col.get(k) or col[k] not in df.columns]
    if missing:
        sys.exit("[前提不满足] 表里找不到这些必需的列：\n  " + "\n  ".join(missing) +
                 f"\n表里现有的列：{list(df.columns)}\n到品类配置的「输入列」里改右边的列名。")
    raw_n = len(df)

    # 1. 只留退货 —— 必须在看原因码之前
    ev, ev_val = col.get("事件类型"), col.get("退货事件取值")
    if ev and ev in df.columns and ev_val:
        r = df[df[ev].astype(str).str.strip() == ev_val].copy()
        if not len(r):
            sys.exit(f"[前提不满足] 筛不出 {ev} = {ev_val} 的行。")
    else:
        r = df.copy()
    ret_n = len(r)

    if a.product:
        r = r[r[col["产品"]].astype(str).str.strip() == a.product].copy()
        if not len(r):
            opts = sorted(df[col["产品"]].dropna().astype(str).unique())
            sys.exit(f"[参数不对] 产品「{a.product}」没有数据。可选：\n" + "\n".join(opts))
    if a.site and col.get("站点") in r.columns:
        r = r[r[col["站点"]].astype(str).str.strip() == a.site].copy()
    scoped_n = len(r)

    # 2. 原因码对清单
    r["_码"] = r[col["原因码"]].astype(str).str.strip()
    unknown = sorted(set(r["_码"]) - set(keep) - set(drop) - {"nan", ""})
    if unknown:
        sys.exit(f"[出现了清单里没有的原因码] {unknown}\n"
                 "不要自己归类。去问负责人这些码该留还是该剔，确认后加进品类配置并把版本号加一。")

    # 3. 留 / 剔
    r["_留剔"] = r["_码"].map(lambda c: "留" if c in keep else "剔")
    r["_剔的原因"] = r["_码"].map(lambda c: drop.get(c, ["", ""])[1])
    kept = r[r["_留剔"] == "留"].copy()

    # 4 + 5. 有字的 + 去套话
    voice_col = col["原话"]
    voiced_all = int(r[voice_col].notna().sum())
    d = kept[kept[voice_col].notna()].copy()
    d["原话"] = d[voice_col].map(lambda v: clean_voice(v, head, tail))
    only_template = int((d["原话"].str.len() == 0).sum())
    d = d[d["原话"].str.len() > 0].reset_index(drop=True)

    # 6. 从规格里读属性
    attr_cols, unreadable = [], {}
    for rule in cfg.get("规格解析", []):
        src = col.get(rule["来源"], rule["来源"])
        if src not in d.columns:
            continue
        d[rule["列名"]] = d[src].map(lambda v: parse_attr(v, rule["规则"]))
        attr_cols.append(rule["列名"])
        bad = sorted(set(d.loc[d[rule["列名"]] == "读不出", src].astype(str)))[:5]
        if bad:
            unreadable[rule["列名"]] = bad

    dt = parse_dates(d[col["时间"]])
    if len(d) and dt.isna().all():
        sys.exit("[前提不满足] 时间那一列解析不成日期。")
    d["日期"] = dt.dt.strftime("%Y-%m-%d")
    d["月份"] = dt.dt.to_period("M").astype(str)
    bad_dates = int(dt.isna().sum())

    d.insert(0, "序号", range(1, len(d) + 1))
    ren = {col.get("记录编号", ""): "记录编号", col.get("订单号", ""): "订单号",
           col.get("站点", ""): "站点", col.get("品名", ""): "品名",
           col["产品"]: "产品", col.get("规格", ""): "规格", col["原因码"]: "平台原因码"}
    d = d.rename(columns={k: v for k, v in ren.items() if k and k in d.columns and k != v})
    order = (["序号", "记录编号", "订单号", "站点", "品名", "产品", "规格"] + attr_cols +
             ["日期", "月份", "平台原因码", "原话"])
    d[[c for c in order if c in d.columns]].to_csv(a.out, index=False, encoding="utf-8-sig")

    # ---- 数据体检 ----
    oc = col.get("订单去重列")
    orders = int((r[oc].astype(str).str.strip() == "1").sum()) if oc and oc in r.columns else None
    broken = int(sum(str(v).count("??") for v in r[voice_col].dropna()))
    cov = round(voiced_all / scoped_n, 3) if scoped_n else 0
    reason_all = r["_码"].value_counts().to_dict()
    reason_share = {k: round(v / (scoped_n or 1), 4) for k, v in reason_all.items()}

    bands = bands_of(cfg)
    sym = []
    for att in cfg.get("两头属性", []):
        ca = sum(reason_all.get(c, 0) for c in att["一头"].get("原因码", []))
        cb = sum(reason_all.get(c, 0) for c in att["另一头"].get("原因码", []))
        has_codes = bool(att["一头"].get("原因码") or att["另一头"].get("原因码"))
        s = symmetry(ca, cb, att["一头"]["叫法"], att["另一头"]["叫法"], bands) if has_codes else \
            {"可判定": False, "合计": 0, "原因": "这个品类的平台原因码里没有方向信息，只能在原话那一层看"}
        s["属性"] = att["名称"]
        sym.append(s)

    rep = {
        "品类": cfg["品类"], "配置版本": cfg.get("版本", ""),
        "文件编码": enc, "原始行数": raw_n, "退货行数": ret_n,
        "本次范围": {"产品": a.product or "全部", "站点": a.site or "全部", "行数": scoped_n},
        "口径": {"退货明细行": scoped_n, "退货订单": orders},
        "留剔": {"留": int((r["_留剔"] == "留").sum()), "剔": int((r["_留剔"] == "剔").sum()),
                "剔的构成": r.loc[r["_留剔"] == "剔", "_剔的原因"].value_counts().to_dict(),
                "剔掉的码有几类": int(r.loc[r["_留剔"] == "剔", "_码"].nunique())},
        "原话": {"范围内写了字的": voiced_all, "覆盖率": cov, "只有平台套话被剔掉": only_template,
                "留下且有原话": len(d)},
        "原因码分布": reason_all, "原因码占比": reason_share,
        "原因码中文": {**keep, **{k: v[0] for k, v in drop.items()}},
        "留下的码": sorted(keep),
        "大筐": cfg["原因码"].get("大筐", []),
        "两头对称_原因码层": sym,
        "站点分布": d["站点"].value_counts().to_dict() if "站点" in d.columns else {},
        "规格分布": d["规格"].value_counts().to_dict() if "规格" in d.columns else {},
        "属性分布": {k: d[k].value_counts().to_dict() for k in attr_cols},
        "时间跨度": [d["月份"].min(), d["月份"].max()] if len(d) else None,
    }
    warn = {}
    if broken:
        warn["编码损坏"] = (f"原话里出现 {broken} 处字面的 '??'。非英文字符在导出时就丢了，救不回来。"
                        "要求重新导出为 UTF-8，不要拿坏掉的原话去打标。")
    if bad_dates:
        warn["日期解析"] = f"有 {bad_dates} 条的时间解析不出来，这些条不进按月统计。"
    if cov and cov < 0.05:
        warn["覆盖率"] = (f"写了原因的只占 {cov:.1%}。这么低更可能是采集漏了，不是客户不爱说。先查采集，别急着解读。")
    if len(d) < 30:
        warn["样本量"] = "有原话的不到 30 条：只通读，不要出任何比例。"
    elif len(d) < 80:
        warn["样本量"] = "30–80 条：可以判方向；分组之后每组很薄，要注明。"
    if unreadable:
        warn["规格读不出"] = unreadable
    rep["提醒"] = warn

    print(dump(rep, a.report))
    hard = [r_["列名"] for r_ in cfg.get("规格解析", []) if r_.get("读不出", "报错") == "报错" and r_["列名"] in unreadable]
    if hard:
        sys.exit("\n[停] 有规格读不出属性。不要猜，去问负责人补规则，补进品类配置的「规格解析」。")


if __name__ == "__main__":
    main()
