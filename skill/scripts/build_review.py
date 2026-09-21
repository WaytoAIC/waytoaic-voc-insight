#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
评论线 · 第 3 步 算数，出报告

进来:
  tagged.csv     逐条打标后的表（列名见 references/02-打标表的格子.md）
  insights.json  叙述部分，由 AI 写
  --prep / --config / --sku  同退货线
出去:
  <产品>_评论分析.xlsx     统计全部用公式连着明细
  <产品>_评论洞察报告.html  可以直接打印成 PDF

分工：脚本不编故事，AI 不算数字。
"""
import argparse, html as H, json, os, statistics as st, sys
from voc_common import (pd, load_config, multi, split_cell, base_tag, tag_dir, all_tags, dir_defs,
                        DIR_SEP, dump)
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
from openpyxl.utils import get_column_letter as GL

NEED = ["序号", "星级", "月份", "原话", "谁在说", "什么情况下", "好评的事", "差评的事", "落差指向",
        "过程感受", "再问一层", "该谁改", "多严重", "整体好坏"]
HIDE_IN_HTML = ["记录编号", "订单号"]
F = lambda **k: Font(name="Arial", **k)
HDR = PatternFill("solid", fgColor="1F3864")
SUB = PatternFill("solid", fgColor="D9E2F3")
WARN = PatternFill("solid", fgColor="FCE4D6")
_t = Side(style="thin", color="BFBFBF")
BD = Border(left=_t, right=_t, top=_t, bottom=_t)
E = lambda s: H.escape(str(s if s is not None else ""))


# ------------------------------------------------------------ 校验
def validate(d, cfg, sku):
    err = []
    miss = [c for c in NEED if c not in d.columns]
    if miss:
        sys.exit(f"[打标表缺格子] {miss}\n格子的标准叫法见 references/02-打标表的格子.md")
    attrs = [a["名称"] for a in cfg["该谁改"]]
    good = cfg.get("整体好坏", ["好评", "中性", "差评"])
    bad = sorted(set(d["整体好坏"]) - set(good))
    if bad:
        err.append(f"「整体好坏」只能填 {good}，出现了 {bad}")
    has_neg = d["差评的事"].str.strip() != ""
    bad = sorted(set(d.loc[has_neg, "该谁改"]) - set(attrs))
    if bad:
        err.append(f"有差评的事的那些行，「该谁改」只能填 {attrs}，出现了 {bad}（空着也不行）")
    bad = sorted(set(d.loc[has_neg, "多严重"]) - set(cfg["多严重"]))
    if bad:
        err.append(f"有差评的事的那些行，「多严重」只能填 {cfg['多严重']}，出现了 {bad}")
    if ((~has_neg) & ((d["该谁改"] != "") | (d["多严重"] != ""))).any():
        err.append("没有差评的事的行，「该谁改」「多严重」要留空")

    ok, dirs = all_tags(cfg, (sku or {}).get("这一款特有的标签")), dir_defs(cfg)
    unknown, bad_dir = set(), set()
    for colname in ("好评的事", "差评的事", "落差指向"):
        for v in d[colname]:
            for t in split_cell(v):
                if colname == "落差指向" and t == "没指明":
                    continue
                b, dr = base_tag(t), tag_dir(t)
                if b not in ok:
                    unknown.add(b)
                elif dr and (colname == "好评的事" or b not in dirs or dr not in dirs[b]):
                    bad_dir.add(f"{colname}:{t}")
    if unknown:
        err.append("这些细项不在标签表里（标签表定了就不改；确实是新东西，先记成下一版的提案）：\n    "
                   + "、".join(sorted(unknown)))
    if bad_dir:
        err.append("方向写法不对（方向只写在差评的事里，且只有标签表里声明了两头的细项才能带）：\n    "
                   + "、".join(sorted(bad_dir)))
    drill = cfg["哪件事"].get("再问一层", {})
    for v in d["再问一层"]:
        for item in split_cell(v):
            try:
                tag, rest = item.split(">", 1)
                dim, ans = rest.split("=", 1)
            except ValueError:
                err.append(f"「再问一层」写法不对：{item}（应为  细项>问什么=答案）")
                continue
            if tag not in drill or dim not in drill.get(tag, {}) or ans not in drill[tag][dim]:
                err.append(f"「再问一层」里有标签表没定义的：{item}")
    if err:
        sys.exit("[打标表没过校验]\n- " + "\n- ".join(dict.fromkeys(err)))


# ------------------------------------------------------------ 算数
def base_counts(series):
    s = multi(series)
    return s.groupby(s.index.map(base_tag)).sum() if len(s) else s


def has_base(cell, tag):
    return tag in [base_tag(x) for x in split_cell(cell)]


def compute(d, prep, cfg):
    n = len(d)
    good_label = cfg.get("整体好坏", ["好评", "中性", "差评"])[0]
    bad_label = cfg.get("整体好坏", ["好评", "中性", "差评"])[-1]
    pos, neg = base_counts(d["好评的事"]), base_counts(d["差评的事"])
    tags = sorted(set(pos.index) | set(neg.index), key=lambda t: -(pos.get(t, 0) + neg.get(t, 0)))
    rows = [(t, int(pos.get(t, 0) + neg.get(t, 0)), int(pos.get(t, 0)), int(neg.get(t, 0))) for t in tags]
    # 分界线按全部标签算；门槛只管进不进「该先动的」那一块，不参与分界线本身——
    # 否则门槛会把低频标签剔掉、抬高中位数，反过来把真正的短板挤出去。
    floor = max(3, round(n * 0.05))
    x_cut = st.median([r[1] for r in rows]) if rows else 0
    tot = sum(r[1] for r in rows)
    y_cut = (sum(r[2] for r in rows) / tot) if tot else 0
    elig = [r for r in rows if r[1] >= floor]
    opp = [r[0] for r in elig if r[1] >= x_cut and (r[2] / r[1]) < y_cut]
    won = [r[0] for r in elig if r[1] >= x_cut and (r[2] / r[1]) >= y_cut]

    # 差评最多的事 + 哪个部门（逐条判的「该谁改」里最多的那个；没有就用配置里的兜底）
    dept_of = {a["名称"]: a["部门"] for a in cfg["该谁改"]}
    fallback = {k: v for k, v in cfg.get("毛病归哪个部门", {}).items() if k != "说明"}
    pain = []
    for t, c in neg.sort_values(ascending=False).items():
        who = d.loc[d["差评的事"].map(lambda v: has_base(v, t)), "该谁改"].value_counts()
        top = who.index[0] if len(who) else ""
        pain.append({"tag": t, "n": int(c), "attr": top,
                     "dept": fallback.get(t) or dept_of.get(top, "待定"), "attr_dist": who.to_dict()})

    months = sorted(m for m in d["月份"].unique() if m and m != "NaT")
    trend = [{"m": mo, "n": int((d["月份"] == mo).sum()),
              "pr": float(((d["月份"] == mo) & (d["整体好坏"] == good_label)).sum() / max(1, (d["月份"] == mo).sum()))}
             for mo in months]
    # 某一件事按月的好评 / 差评次数（看走势是被哪件事拖下去的）
    tag_month = {}
    for t, total, p_, n_ in elig:
        tag_month[t] = [{"m": mo,
                         "好": int(d.loc[d["月份"] == mo, "好评的事"].map(lambda v: has_base(v, t)).sum()),
                         "差": int(d.loc[d["月份"] == mo, "差评的事"].map(lambda v: has_base(v, t)).sum())}
                        for mo in months]

    # 逐项看两头（只看差评的事里带方向的）
    item_min = int(cfg.get("逐项最少条数", 8))
    sym_items = []
    for nm, (a, b) in dir_defs(cfg).items():
        ca = int(d["差评的事"].map(lambda v: f"{nm}{DIR_SEP}{a}" in split_cell(v)).sum())
        cb = int(d["差评的事"].map(lambda v: f"{nm}{DIR_SEP}{b}" in split_cell(v)).sum())
        tot_ = ca + cb
        if not tot_:
            continue
        pa = ca / tot_ * 100
        verdict = ("样本少" if tot_ < item_min else "一边倒" if max(pa, 100 - pa) >= 90
                   else "两头都有" if abs(2 * pa - 100) <= 30 else "往一头偏")
        sym_items.append({"细项": nm, "一头": a, "另一头": b, "一头条数": ca, "另一头条数": cb, "合计": tot_,
                          "一头占比": round(pa, 1), "另一头占比": round(100 - pa, 1), "判定": verdict})
    sym_items.sort(key=lambda x: -x["合计"])

    # 再问一层
    drill = {}
    for v in d["再问一层"]:
        for item in split_cell(v):
            tag, rest = item.split(">", 1)
            dim, ans = rest.split("=", 1)
            drill.setdefault(tag, {}).setdefault(dim, {})
            drill[tag][dim][ans] = drill[tag][dim].get(ans, 0) + 1

    # 交叉：按规格属性 / 站点 / 是否疑似
    cross_cols = [r["列名"] for r in cfg.get("规格解析", []) if r["列名"] in d.columns]
    cross_cols += [c for c in ("规格", "站点", "疑似不可信") if c in d.columns]
    cross = {}
    for c in cross_cols:
        vals = [v for v in d[c].astype(str).unique() if v.strip()]
        if len(vals) < 2:
            continue
        cross[c] = [{"组": v, "条数": int((d[c] == v).sum()),
                     "好评": int(((d[c] == v) & (d["整体好坏"] == good_label)).sum()),
                     "差评": int(((d[c] == v) & (d["整体好坏"] == bad_label)).sum())}
                    for v in sorted(vals, key=lambda v: -int((d[c] == v).sum()))]
    # 一个规格还是整条线：差评的事 × 规格属性
    neg_by_attr = {}
    for t, total, p_, n_ in elig:
        if not n_:
            continue
        hit = d[d["差评的事"].map(lambda v: has_base(v, t))]
        neg_by_attr[t] = {c: hit[c].value_counts().to_dict() for c in cross_cols if c != "疑似不可信"}

    real = d[d["疑似不可信"] != "是"] if "疑似不可信" in d.columns else d
    star = pd.to_numeric(d["星级"], errors="coerce")
    star_text_gap = int(((star >= 4) & (d["整体好坏"] == bad_label)).sum())
    top_sev = cfg["多严重"][0]
    return {
        "n": n, "floor": floor, "x_cut": x_cut, "y_cut": y_cut,
        "scatter": rows, "eligible": elig, "opportunity": opp, "won": won,
        "pain": pain, "trend": trend, "tag_month": tag_month,
        "sym_items": sym_items, "drill": drill, "cross": cross, "neg_by_attr": neg_by_attr,
        "overall": d["整体好坏"].value_counts().to_dict(),
        "pos_share": float((d["整体好坏"] == good_label).mean()) if n else 0,
        "pos_share_no_suspect": float((real["整体好坏"] == good_label).mean()) if len(real) else 0,
        "suspect_n": int((d.get("疑似不可信", "") == "是").sum()) if "疑似不可信" in d.columns else 0,
        "star_mean": round(float(star.mean()), 2) if n else None,
        "star_low_share": float((star <= 2).mean()) if n else 0,
        "star_text_gap": star_text_gap,
        "attr": d.loc[d["差评的事"] != "", "该谁改"].value_counts().to_dict(),
        "sev": d.loc[d["差评的事"] != "", "多严重"].value_counts().to_dict(),
        "sev_top_by_tag": {p_["tag"]: int((d["差评的事"].map(lambda v, t=p_["tag"]: has_base(v, t))
                                          & (d["多严重"] == top_sev)).sum()) for p_ in pain},
        "gap": multi(d["落差指向"]).to_dict(),
        "user": multi(d["谁在说"]).to_dict(), "scene": multi(d["什么情况下"]).to_dict(),
        "exp": multi(d["过程感受"]).to_dict(),
        "prep": prep or {},
    }


# ------------------------------------------------------------ Excel
def sheet_head(ws, row, hs):
    for i, h in enumerate(hs, 1):
        c = ws.cell(row, i, h)
        c.font = F(bold=True, size=10, color="FFFFFF")
        c.fill = HDR
        c.alignment = Alignment(horizontal="center", wrap_text=True)


def borders(ws, r1, r2, c2, wrap=False):
    for r in ws.iter_rows(min_row=r1, max_row=r2, max_col=c2):
        for c in r:
            c.font = F(size=10)
            c.border = BD
            c.alignment = Alignment(vertical="top", wrap_text=wrap)


def xl(s):
    return str(s).replace('"', '""').replace("~", "~~").replace("?", "~?").replace("*", "~*")


def build_xlsx(d, m, path, product, ins, cfg):
    cols = [c for c in d.columns]
    CL = {n_: GL(i + 1) for i, n_ in enumerate(cols)}
    n = len(d)
    good, bad = cfg.get("整体好坏", ["好评", "中性", "差评"])[0], cfg.get("整体好坏", ["好评", "中性", "差评"])[-1]
    wb = Workbook()
    ws = wb.active
    ws.title = "打标明细"
    ws.append(cols)
    sheet_head(ws, 1, cols)
    for _, r in d.iterrows():
        ws.append(["" if pd.isna(v) else v for v in r.values])
    borders(ws, 2, n + 1, len(cols), wrap=True)
    for i, cn in enumerate(cols, 1):
        ws.column_dimensions[GL(i)].width = {"序号": 6, "星级": 6, "站点": 7, "原话": 60, "好评的事": 28,
                                             "差评的事": 28, "再问一层": 34}.get(cn, 14)
    ws.freeze_panes = "C2"
    ws.auto_filter.ref = f"A1:{GL(len(cols))}{n+1}"
    if "疑似不可信" in CL:
        j = cols.index("疑似不可信") + 1
        for r in range(2, n + 2):
            if ws.cell(r, j).value == "是":
                for c in range(1, len(cols) + 1):
                    ws.cell(r, c).fill = WARN
    FP, FN, SEN = CL["好评的事"], CL["差评的事"], CL["整体好坏"]
    D = "打标明细"

    s = wb.create_sheet("哪件事提得多满不满意")
    s["A1"] = "横着是提到多少次，竖着是好评占比"
    s["A1"].font = F(bold=True, size=13, color="1F3864")
    s["A2"] = (f"门槛跟着数据量走：进排名 ≥{m['floor']} 次；横向分界 {m['x_cut']:.0f} 次（全部标签提及的中位数）；"
               f"纵向分界 {m['y_cut']*100:.1f}%（加权平均好评占比）")
    s["A2"].font = F(size=9, italic=True, color="808080")
    sheet_head(s, 4, ["细项", "提到次数", "好评次数", "差评次数", "好评占比", "落在哪一块"])
    for i, (t, tot, p, ng) in enumerate(m["scatter"], start=5):
        s.cell(i, 1, t)
        s.cell(i, 3, f'=COUNTIF({D}!{FP}:{FP},"*{xl(t)}*")')
        s.cell(i, 4, f'=COUNTIF({D}!{FN}:{FN},"*{xl(t)}*")')
        s.cell(i, 2, f"=C{i}+D{i}")
        s.cell(i, 5, f'=IFERROR(C{i}/B{i},"")')
        s.cell(i, 5).number_format = "0.0%"
        s.cell(i, 6, f'=IF(B{i}<{m["floor"]},"没进排名（提得太少）",'
                     f'IF(B{i}>={m["x_cut"]:.0f},IF(E{i}<{m["y_cut"]:.4f},"★ 提得多又不满意 · 该先动","提得多也满意 · 已经赢了"),'
                     f'IF(E{i}<{m["y_cut"]:.4f},"提得少不满意 · 盯着","提得少但满意")))')
    borders(s, 5, 4 + len(m["scatter"]), 6)
    for c, w in zip("ABCDEF", [26, 11, 11, 11, 13, 34]):
        s.column_dimensions[c].width = w

    p = wb.create_sheet("差评最多的事")
    p["A1"] = "差评最多的事（直接对应行动）"
    p["A1"].font = F(bold=True, size=13, color="1F3864")
    sheet_head(p, 3, ["细项", "差评次数", "占全部评论", "其中严重", "哪个部门"])
    SEV = CL["多严重"]
    for i, it in enumerate(m["pain"], start=4):
        p.cell(i, 1, it["tag"])
        p.cell(i, 2, f'=COUNTIF({D}!{FN}:{FN},"*{xl(it["tag"])}*")')
        p.cell(i, 3, f'=IFERROR(B{i}/(COUNTA({D}!A:A)-1),"")')
        p.cell(i, 3).number_format = "0.0%"
        p.cell(i, 4, f'=COUNTIFS({D}!{FN}:{FN},"*{xl(it["tag"])}*",{D}!{SEV}:{SEV},"{xl(cfg["多严重"][0])}")')
        p.cell(i, 5, it["dept"])
    borders(p, 4, 3 + len(m["pain"]), 5)
    for c, w in zip("ABCDE", [28, 11, 13, 11, 30]):
        p.column_dimensions[c].width = w

    x = wb.create_sheet("交叉分析")
    x["A1"] = "分组看好评占比（好评占比 = 这一组里整体是好评的条数 ÷ 这一组的条数）｜分组小的只看方向"
    x["A1"].font = F(bold=True, size=13, color="1F3864")
    row = 3
    for colname, groups in m["cross"].items():
        c = x.cell(row, 1, f"按{colname}")
        c.font = F(bold=True, size=11, color="1F3864")
        c.fill = SUB
        row += 1
        sheet_head(x, row, ["分组", "条数", "好评", "差评", "好评占比"])
        row += 1
        start, L = row, CL[colname]
        for g in groups:
            x.cell(row, 1, g["组"])
            x.cell(row, 2, f"=COUNTIF({D}!{L}:{L},A{row})")
            x.cell(row, 3, f'=COUNTIFS({D}!{L}:{L},A{row},{D}!{SEN}:{SEN},"{good}")')
            x.cell(row, 4, f'=COUNTIFS({D}!{L}:{L},A{row},{D}!{SEN}:{SEN},"{bad}")')
            x.cell(row, 5, f'=IFERROR(C{row}/B{row},"")')
            x.cell(row, 5).number_format = "0.0%"
            row += 1
        borders(x, start, row - 1, 5)
        row += 1
    for c, w in zip("ABCDE", [28, 11, 9, 9, 13]):
        x.column_dimensions[c].width = w

    t = wb.create_sheet("按月走势")
    t["A1"] = f"按月走势（共 {n} 条，条数少的月份只看方向）"
    t["A1"].font = F(bold=True, size=13, color="1F3864")
    sheet_head(t, 3, ["月份", "条数", "其中疑似刷的", "好评", "差评", "好评占比", "平均星级"])
    MO, SUS, STAR = CL["月份"], CL.get("疑似不可信"), CL["星级"]
    r = 4
    for it in m["trend"]:
        t.cell(r, 1, it["m"])
        t.cell(r, 2, f"=COUNTIF({D}!{MO}:{MO},A{r})")
        t.cell(r, 3, f'=COUNTIFS({D}!{MO}:{MO},A{r},{D}!{SUS}:{SUS},"是")' if SUS else 0)
        t.cell(r, 4, f'=COUNTIFS({D}!{MO}:{MO},A{r},{D}!{SEN}:{SEN},"{good}")')
        t.cell(r, 5, f'=COUNTIFS({D}!{MO}:{MO},A{r},{D}!{SEN}:{SEN},"{bad}")')
        t.cell(r, 6, f'=IFERROR(D{r}/B{r},"")')
        t.cell(r, 6).number_format = "0.0%"
        t.cell(r, 7, f'=IFERROR(AVERAGEIFS({D}!{STAR}:{STAR},{D}!{MO}:{MO},A{r}),"")')
        t.cell(r, 7).number_format = "0.00"
        r += 1
    borders(t, 4, r - 1, 7)
    for c, w in zip("ABCDEFG", [11, 9, 14, 9, 9, 12, 10]):
        t.column_dimensions[c].width = w

    k = wb.create_sheet("再问一层")
    k["A1"] = "往下再问一层（要问什么，打标的时候就留好了位置）｜「没说」的占比本身就是结论"
    k["A1"].font = F(bold=True, size=13, color="1F3864")
    row = 3
    for tag, dims in m["drill"].items():
        for dim, ans in dims.items():
            c = k.cell(row, 1, f"{tag} · {dim}")
            c.font = F(bold=True, size=11, color="1F3864")
            c.fill = SUB
            row += 1
            sheet_head(k, row, ["答案", "条数", "占这一问"])
            row += 1
            start, tot = row, sum(ans.values())
            for a_, cnt in sorted(ans.items(), key=lambda kv: -kv[1]):
                k.cell(row, 1, a_)
                k.cell(row, 2, int(cnt))
                k.cell(row, 3, f"=IFERROR(B{row}/{tot},\"\")")
                k.cell(row, 3).number_format = "0.0%"
                row += 1
            borders(k, start, row - 1, 3)
            row += 1
    for c, w in zip("ABC", [36, 10, 14]):
        k.column_dimensions[c].width = w

    q = wb.create_sheet("结论对原话")
    q["A1"] = "每个结论对应哪几条原话（序号对应「打标明细」）"
    q["A1"].font = F(bold=True, size=13, color="1F3864")
    sheet_head(q, 3, ["结论", "原话（节选）", "序号", "星级"])
    r = 4
    for it in ins.get("quotes", []):
        for i, key in enumerate(["conclusion", "text", "idx", "star"], 1):
            q.cell(r, i, it.get(key, ""))
        r += 1
    borders(q, 4, max(4, r - 1), 4, wrap=True)
    for c, w in zip("ABCD", [34, 70, 8, 8]):
        q.column_dimensions[c].width = w

    nz = wb.create_sheet("说明与口径")
    notes = [("数据处理记录", "")]
    for kk, v in (m["prep"] or {}).items():
        if isinstance(v, (str, int, float)):
            notes.append((kk, str(v)))
    notes += [("", ""),
              ("门槛与分界", f"进排名 ≥{m['floor']} 次 · 横向 {m['x_cut']:.0f} 次 · 纵向 {m['y_cut']*100:.1f}%"),
              ("去掉疑似刷的之后", f"整体好评占比 {m['pos_share']*100:.1f}% → {m['pos_share_no_suspect']*100:.1f}%"),
              ("该先动的", " · ".join(m["opportunity"]) or "无"),
              ("已经赢了的", " · ".join(m["won"]) or "无"),
              ("", ""), ("这批数据答不了什么", "")]
    notes += [("", c) for c in ins.get("caveats", [])]
    nz["A1"] = f"{product}｜评论分析 · 说明与口径"
    nz["A1"].font = F(bold=True, size=14, color="1F3864")
    for i, (a_, b_) in enumerate(notes, start=3):
        nz.cell(i, 1, a_).font = F(bold=(b_ == ""), size=10, color="1F3864" if b_ == "" else "000000")
        nz.cell(i, 2, b_).font = F(size=10)
        nz.cell(i, 2).alignment = Alignment(wrap_text=True, vertical="top")
    nz.column_dimensions["A"].width = 24
    nz.column_dimensions["B"].width = 95
    wb.save(path)


# ------------------------------------------------------------ 网页
def svg_scatter(m):
    W, Hh, PL, PRr, PT, PB = 940, 500, 64, 150, 52, 58
    rows = m["eligible"] or m["scatter"]
    mx = max([r[1] for r in rows] + [1])
    ub = int(mx * 1.12) + 1
    X = lambda v: PL + v / ub * (W - PL - PRr)
    Y = lambda p: PT + (1 - p) * (Hh - PT - PB)
    grid = "".join(
        f'<line class="grid" x1="{PL}" y1="{Y(v/100):.1f}" x2="{W-PRr}" y2="{Y(v/100):.1f}"/>'
        f'<text class="axt" x="{PL-12}" y="{Y(v/100)+4:.1f}" text-anchor="end">{v}%</text>'
        for v in (0, 20, 40, 60, 80, 100))
    step = max(1, round(ub / 6))
    grid += "".join(
        f'<line class="grid" x1="{X(v):.1f}" y1="{PT}" x2="{X(v):.1f}" y2="{Hh-PB}"/>'
        f'<text class="axt" x="{X(v):.1f}" y="{Hh-PB+22}" text-anchor="middle">{v}</text>'
        for v in range(0, ub + 1, step))
    zone = (f'<rect class="zone" x="{X(m["x_cut"]):.1f}" y="{Y(m["y_cut"]):.1f}" '
            f'width="{X(ub)-X(m["x_cut"]):.1f}" height="{Hh-PB-Y(m["y_cut"]):.1f}"/>')
    pts, seen, placed = [], {}, []
    for i, (t, tot, p, ng) in enumerate(sorted(rows, key=lambda r: -r[1])):
        cx, cy = X(tot), Y(p / tot)
        key = (round(cx), round(cy))
        cy += 7 * seen.get(key, 0)
        seen[key] = seen.get(key, 0) + 1
        opp = t in m["opportunity"]
        side = "start" if cx < W * 0.55 else "end"
        dx = 12 if side == "start" else -12
        r = 6 + tot ** 0.5 * 1.5
        w = len(t) * 12.5
        lx, ly = cx + dx, cy + 4
        for _ in range(4):
            x0 = lx if side == "start" else lx - w
            if not any(abs(ly - by) < 13 and x0 < bx1 and x0 + w > bx0 for bx0, bx1, by in placed):
                break
            ly += 15
        placed.append((lx if side == "start" else lx - w, lx + w if side == "start" else lx, ly))
        pts.append(f'<g class="pt {"opp" if opp else ""}" style="--d:{i*45}ms">'
                   f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r:.1f}"/>'
                   f'<text x="{lx:.1f}" y="{ly:.1f}" text-anchor="{side}">{E(t)}</text></g>')
    return f'''<svg viewBox="0 0 {W} {Hh}" role="img" aria-label="哪件事提得多、满不满意的散点图">
{zone}{grid}
<line class="axis" x1="{PL}" y1="{Hh-PB}" x2="{W-PRr}" y2="{Hh-PB}"/>
<line class="axis" x1="{PL}" y1="{PT}" x2="{PL}" y2="{Hh-PB}"/>
<text class="zlab" x="{X(ub):.1f}" y="{Hh-PB-10}" text-anchor="end">该先动的 · 提得多又不满意</text>
<text class="axl" x="{W-PRr}" y="{Hh-14}" text-anchor="end">提到次数 →</text>
<text class="axl" x="{PL-14}" y="{PT-30}" text-anchor="start">↑ 好评占比</text>
{"".join(pts)}</svg>'''


def svg_trend(tr):
    W, Hh = 940, 190
    n = max(1, len(tr) - 1)
    X = lambda i: 60 + i * (W - 100) / n
    Y = lambda p: 18 + (1 - p) * (Hh - 58)
    line = "M " + " L ".join(f"{X(i):.1f} {Y(r['pr']):.1f}" for i, r in enumerate(tr))
    dots = "".join(
        f'<circle class="tp" cx="{X(i):.1f}" cy="{Y(r["pr"]):.1f}" r="4.5"/>'
        f'<text class="tl" x="{X(i):.1f}" y="{Hh-24}" text-anchor="middle">{r["m"][-2:]}月</text>'
        f'<text class="tn" x="{X(i):.1f}" y="{Hh-8}" text-anchor="middle">{r["n"]} 条</text>'
        for i, r in enumerate(tr))
    return f'''<svg viewBox="0 0 {W} {Hh}" role="img" aria-label="按月的好评占比走势">
<line class="grid" x1="60" y1="{Y(.5):.1f}" x2="{W-40}" y2="{Y(.5):.1f}"/>
<text class="axt" x="52" y="{Y(.5)+4:.1f}" text-anchor="end">50%</text>
<text class="axt" x="52" y="{Y(1)+4:.1f}" text-anchor="end">100%</text>
<text class="axt" x="52" y="{Y(0)+4:.1f}" text-anchor="end">0%</text>
<path d="{line}" fill="none" stroke="var(--wet)" stroke-width="2"/>{dots}</svg>'''


def kpi5(t):
    if t.get("metric"):
        return (f'<b>看哪个数</b> {E(t["metric"])}<br><b>现在</b> {E(t.get("now","—"))} → <b>要到</b> {E(t.get("target","—"))}'
                f'<br><b>哪天看</b> {E(t.get("when","—"))}'
                + (f'<span class="ifnot"><b>要是没变</b> {E(t["if_not"])}</span>' if t.get("if_not") else ""))
    return E(t.get("kpi", ""))


CSS_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets", "review_report.css")


def build_html(d, m, ins, path, product, cfg, is_sample):
    css = open(CSS_PATH, encoding="utf-8").read()
    n, prep = m["n"], m["prep"]
    tx = cfg.get("图上文字", {})
    meta = [("原始条数", prep.get("原始条数", n), 0), ("剔掉送测评论", f"−{prep.get('剔掉送测', 0)}", 0),
            ("进入分析", n, 0), ("差评占比（1–2 星）", f"{m['star_low_share']*100:.1f}%", 1),
            ("平均星级", f"{m['star_mean']:.2f}", 1), ("整体好评占比", f"{m['pos_share']*100:.1f}%", 0)]
    meta_h = "".join(f'<div class="{"neg" if b else ""}"><b>{v}</b><span>{k}</span></div>' for k, v, b in meta)
    bars = "".join(
        f'<div class="bar-row"><div class="bl">{E(t)}</div><div class="bt">'
        f'<span class="dry" style="--w:{p/tot*100:.1f}%"></span><span class="wet" style="--w:{ng/tot*100:.1f}%"></span></div>'
        f'<div class="bn"><b>{tot}</b><i>{p/tot*100:.0f}%</i></div></div>'
        for t, tot, p, ng in m["scatter"] if tot >= m["floor"])
    pmax = max([x["n"] for x in m["pain"]] + [1])
    pain = "".join(
        f'<tr><td class="pn">{E(x["tag"])}</td><td class="pc"><span style="--w:{x["n"]/pmax*100:.0f}%"></span>'
        f'<b>{x["n"]}</b></td><td class="po">{E(x["dept"])}</td></tr>' for x in m["pain"])
    won = "".join(f"<span>{E(t)}</span>" for t in m["won"])
    dual = "".join(
        f'<div class="dual"><div>{E(o["细项"])}</div><div class="bar">'
        + (f'<i class="a" style="width:{o["一头占比"]}%">{E(o["一头"])} {o["一头条数"]}</i>' if o["一头条数"] else "")
        + (f'<i class="b" style="width:{o["另一头占比"]}%">{E(o["另一头"])} {o["另一头条数"]}</i>' if o["另一头条数"] else "")
        + f'</div><div class="verdict {"hot" if o["判定"] in ("一边倒","往一头偏") else ""}">{E(o["判定"])} · 共 {o["合计"]} 条</div></div>'
        for o in m["sym_items"])
    drill_cards = ""
    for tag, dims in m["drill"].items():
        for dim, ans in dims.items():
            tot = sum(ans.values())
            rows_ = "".join(f'<div class="drill-row {"unk" if a_=="没说" else ""}"><span>{E(a_)}</span><b>{c} · {c/tot*100:.0f}%</b></div>'
                            for a_, c in sorted(ans.items(), key=lambda kv: -kv[1]))
            drill_cards += f'<div class="drill-card"><h4>{E(tag)} · {E(dim)}</h4>{rows_}</div>'
    chains = "".join(f'<div class="chain"><div class="tag">{E(c.get("tag",""))}</div><h4>{c["title"]}</h4><p>{c["body"]}</p></div>'
                     for c in ins.get("chains", []))
    lay = ins.get("layers", [])
    layers = "".join(f'<div class="layer {"last" if i==len(lay)-1 else ""}"><div class="q">{E(l.get("level",""))} · {E(l.get("q",""))}</div>'
                     f'<h4>{l["title"]}</h4><p>{l["body"]}</p></div>' for i, l in enumerate(lay))
    opps = "".join(f'<h3>{o["title"]}</h3><p>{o["body"]}</p>' +
                   "".join(f'<blockquote><p>{E(q["text"])}</p><cite>{E(q.get("cite",""))}</cite></blockquote>' for q in o.get("quotes", []))
                   for o in ins.get("opportunities", []))
    tiers = cfg.get("行动四档", ["马上止血", "根治问题", "防止再犯", "要老板定"])
    tier_when = ins.get("tier_when", {})
    todo = ""
    for ti, tier in enumerate(tiers, 1):
        items = [t for t in ins.get("todo", []) if t.get("tier") == tier]
        if not items:
            continue
        cards = "".join(
            f'<article class="todo"><header><span class="own">{E(i.get("owner",""))} · 该谁改：{E(i.get("attr",""))}'
            f'{" · 依据 "+str(i["n"])+" 条" if i.get("n") else ""}</span>'
            f'<h4>{i.get("problem") or i.get("title","")}</h4></header><p>{i["body"]}</p>'
            f'<div class="kpi"><span>怎么才算做完</span>{kpi5(i)}</div></article>' for i in items)
        todo += (f'<div class="tier"><div class="tier-h"><span class="pill t{ti}">{E(tier)}</span>'
                 f'<span class="when">{E(tier_when.get(tier,""))}</span></div><div class="todo-grid">{cards}</div></div>')
    caveats = "".join(f"<li>{c}</li>" for c in ins.get("caveats", []))
    thesis = "<br>".join(ins.get("thesis", []))
    dr = ins.get("drill")
    drill_sec = ""
    if dr or drill_cards:
        drill_sec = ("<section><div class='slab'>回到原话里验证 · 往下再问一层</div><h2>" + (dr or {}).get("title", "往下再问一层") + "</h2><p>"
                     + (dr or {}).get("body", "") + "</p>" + (f'<div class="drill-grid">{drill_cards}</div>' if drill_cards else "")
                     + "".join(f"<blockquote><p>{E(q['text'])}</p><cite>{E(q.get('cite',''))}</cite></blockquote>" for q in (dr or {}).get("quotes", []))
                     + "</section>")
    recs = d.drop(columns=[c for c in HIDE_IN_HTML if c in d.columns]).fillna("").to_dict("records")
    payload = json.dumps(recs, ensure_ascii=False, default=str).replace("</", "<\\/")
    tr = m["trend"]
    title = ins.get("title") or f'{product} · {tx.get("评论报告名","评论洞察报告")}'
    page = f'''<!DOCTYPE html><html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{E(title)}</title>
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Noto+Sans+SC:wght@300;400;500;700&family=Noto+Serif+SC:wght@500;700;900&family=IBM+Plex+Mono:wght@400;500;600&display=swap" rel="stylesheet">
<style>{css}</style></head><body><div class="wrap">
<header class="top"><div class="eyebrow">{E(tx.get("评论报告名","评论洞察报告"))}{' <span class="sample-flag">示例数据</span>' if is_sample else ''}</div>
<h1>{ins.get("headline","")}</h1>
<p class="sub">{ins.get("subtitle","")}</p>
<div class="meta">{meta_h}</div></header>

<section><div class="slab">结论先行</div>
<div class="thesis"><p>{thesis}</p></div>
<p class="lead" style="margin-top:26px">{ins.get("lead","")}</p>
{('<p style="margin-top:22px;font-size:14px;color:var(--mut)">已经赢了的（提得多、也满意，这些不用动）：</p><div class="won">'+won+'</div>') if won else ''}</section>

<section><div class="slab">算出来的</div><h2>哪件事提得多，满不满意</h2>
<p>横着是提到多少次（客户心里有多看重），竖着是好评占比。分界线跟着这批数据走：进排名至少 {m['floor']} 次，横向分界 {m['x_cut']:.0f} 次（全部标签提及的中位数），纵向分界 {m['y_cut']*100:.1f}%（加权平均好评占比）。右下阴影里的，是该先动的。</p>
<figure>{svg_scatter(m)}<figcaption>
<span class="key"><i style="background:var(--wet)"></i>该先动的</span>
<span class="key"><i style="background:var(--dry)"></i>其余</span>
<span>圆点大小 = 提到次数</span></figcaption></figure>
<div class="bars">{bars}</div>
<p style="margin-top:16px;font-size:13.5px;color:var(--mut)">深色是好评，砖红是差评。右边是总次数和好评占比。只显示进了排名的。</p>
<h3>按月走势</h3><p>{ins.get("trend_note","")}</p>
<figure>{svg_trend(tr)}<figcaption>每个月整体是好评的评论占多少。条数少的月份只看方向。</figcaption></figure>
{("<h3>分组看</h3><p>"+ins["cross_note"]+"</p>") if ins.get("cross_note") else ""}
{('<h3>同一把尺子，逐项量一遍</h3><p>'+ins.get("sym_note","两头都有人说＝个人差异；几乎全在一头＝这一项做偏了。")+'</p><div class="bars" style="border-top:1px solid var(--line)">'+dual+'</div>') if dual else ''}</section>

<section><div class="slab">算出来的</div><h2>差评最多的事</h2>
<p>{ins.get("pain_note","")}</p>
<table><thead><tr><th class="pn">哪件事</th><th>差评次数</th><th class="po">哪个部门</th></tr></thead>
<tbody>{pain}</tbody></table></section>

{drill_sec}

<section><div class="slab">为什么</div><h2>几条因果链</h2>
<div class="chains">{chains}</div></section>

<section><div class="slab">三层洞察</div><h2>发生了什么 · 为什么 · 不改会怎样</h2>
<div class="layers">{layers}</div></section>

{("<section><div class='slab'>机会</div><h2>机会</h2>"+opps+"</section>") if opps else ""}

<section><div class="slab">行动清单</div><h2>下一步做什么</h2>
<p>{ins.get("todo_note","先止血、再根治、再防再犯，最后是要老板定的。每条都写了怎么才算做完；到日子回来读那个数，就是复盘。")}</p>
{todo}</section>

<section><div class="slab">原话查阅</div><h2>{n} 条评论，随时点回去看</h2>
<p>每个结论都能点回具体的某一条。发现必须有客户的原话撑着，否则不成立。</p>
<div class="filters" id="filters"></div><div class="vlist" id="vlist"></div></section>

<div class="caveat"><h3>这批数据答不了什么</h3><ul>{caveats}</ul></div>
<footer><span>{E(ins.get("sig") or tx.get("落款",""))}</span><span>{n} 条 · {tr[0]["m"] if tr else ""} → {tr[-1]["m"] if tr else ""}</span></footer>
</div>
<script>
const RECS={payload};
const esc=s=>String(s==null?'':s).replace(/[<>&]/g,c=>({{'<':'&lt;','>':'&gt;','&':'&amp;'}}[c]));
const fb=document.getElementById('filters'),list=document.getElementById('vlist');
const opts=['全部','好评','中性','差评','疑似刷的'];let active='全部';
const pick=a=>a==='全部'?RECS:a==='疑似刷的'?RECS.filter(r=>r['疑似不可信']==='是'):RECS.filter(r=>r['整体好坏']===a);
opts.forEach(a=>{{const b=document.createElement('button');b.className='chip';b.type='button';
  b.textContent=`${{a}} ${{pick(a).length}}`;b.setAttribute('aria-pressed',a===active);
  b.onclick=()=>{{active=a;fb.querySelectorAll('.chip').forEach(c=>c.setAttribute('aria-pressed','false'));b.setAttribute('aria-pressed','true');render();}};
  fb.appendChild(b);}});
function render(){{list.innerHTML=pick(active).map(r=>`<div class="vcard"><span class="idx">#${{r['序号']}} · ${{esc(r['星级'])}} 星 · ${{esc(r['规格']||'')}} · ${{esc(r['月份']||'')}}${{r['疑似不可信']==='是'?' · 疑似刷的':''}}</span>
  ${{esc(r['原话'])}}<div class="tags">${{r['好评的事']?`<span class="g">好：${{esc(r['好评的事'])}}</span><br>`:''}}${{r['差评的事']?`<span class="b">差：${{esc(r['差评的事'])}}</span> · ${{esc(r['该谁改'])}} · ${{esc(r['多严重'])}}`:''}}</div></div>`).join('');}}
render();
</script>
</body></html>'''
    open(path, "w", encoding="utf-8").write(page)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("tagged")
    ap.add_argument("insights")
    ap.add_argument("--config", required=True)
    ap.add_argument("--prep", default=None)
    ap.add_argument("--sku", default=None)
    ap.add_argument("--outdir", default=None)
    ap.add_argument("--sample", action="store_true")
    a = ap.parse_args()

    cfg = load_config(a.config)
    d = pd.read_csv(a.tagged, dtype=str).fillna("")
    sku = json.load(open(a.sku, encoding="utf-8")) if a.sku else None
    if not sku:
        print("[提醒] 没给「这一款的特点」。卖点同时也是漏点这类结论，没有它看不出来。", file=sys.stderr)
    validate(d, cfg, sku)
    prep = json.load(open(a.prep, encoding="utf-8")) if a.prep else {}
    ins = json.load(open(a.insights, encoding="utf-8"))
    product = ins.get("product") or (prep.get("本次范围", {}) or {}).get("产品") or "未命名"
    outdir = a.outdir or ("/mnt/user-data/outputs" if os.path.isdir("/mnt/user-data/outputs") else "outputs")
    os.makedirs(outdir, exist_ok=True)

    seqs = set(d["序号"].astype(str))
    for t in ins.get("todo", []):
        if t.get("refs"):
            bad = [r for r in t["refs"] if str(r) not in seqs]
            if bad:
                sys.exit(f"[行动清单] 「{t.get('problem') or t.get('id')}」依据的原话编号不存在：{bad}")
            t["n"] = len(t["refs"])

    m = compute(d, prep, cfg)
    if m["n"] < 30:
        print("[警告] 有效评论不到 30 条。只通读，不要在报告里出任何比例。", file=sys.stderr)
    safe = product.replace("/", "-")
    xlsx = os.path.join(outdir, f"{safe}_评论分析.xlsx")
    html_ = os.path.join(outdir, f"{safe}_评论洞察报告.html")
    build_xlsx(d, m, xlsx, product, ins, cfg)
    build_html(d, m, ins, html_, product, cfg, a.sample)
    dump({k: v for k, v in m.items() if k != "prep"}, os.path.join(outdir, "stats.json"))
    print(dump({"xlsx": os.path.abspath(xlsx), "html": os.path.abspath(html_), "进入分析": m["n"],
                "门槛与分界": {"进排名": m["floor"], "横向": m["x_cut"], "纵向": round(m["y_cut"], 4)},
                "该先动的": m["opportunity"], "已经赢了的": m["won"],
                "好评占比": round(m["pos_share"], 3), "去掉疑似刷的之后": round(m["pos_share_no_suspect"], 3),
                "星级和文字对不上的": m["star_text_gap"],
                "逐项两头": [(s["细项"], s["判定"], f"{s['一头条数']}:{s['另一头条数']}") for s in m["sym_items"]]}))
    print("\n下一步：python recalc.py " + os.path.abspath(xlsx))


if __name__ == "__main__":
    main()
