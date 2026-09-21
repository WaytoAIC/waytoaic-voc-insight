#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
三条线共用的底层函数：读配置、读表格、解析日期、拆多值格、算"两头是否对称"。

所有跟品类有关的东西都在「品类配置」那个 JSON 里，这里一个字都不写死。
"""
import json, re, sys

try:
    import pandas as pd
except ImportError:
    sys.exit("缺少依赖。先安装：pip install -r requirements.txt")

SEP = "; "          # 多值格的统一分隔符：分号 + 空格（三条线一致）
DIR_SEP = ":"       # 细项可以带方向，写成  名称:方向  例如  整体高度:偏高


def load_config(path):
    try:
        cfg = json.load(open(path, encoding="utf-8"))
    except FileNotFoundError:
        sys.exit(f"[找不到品类配置] {path}\n每个品类一份配置，做法见 references/03-怎么做出自己的标签表.md")
    for k in ("品类", "原因码", "哪件事", "该谁改"):
        if k not in cfg:
            sys.exit(f"[品类配置不完整] 缺少「{k}」。对照 品类配置/示例-AI眼镜配件.json 补齐。")
    return cfg


def read_any(path):
    """导出文件的编码五花八门，逐个试。返回 (表, 用的编码)。"""
    last = None
    for enc in ("utf-8-sig", "utf-8", "gb18030", "gbk", "utf-16"):
        try:
            return pd.read_csv(path, encoding=enc, dtype=str), enc
        except (UnicodeDecodeError, UnicodeError) as e:
            last = e
    sys.exit(f"[前提不满足] 文件解不开，请确认编码。最后的报错：{last}")


def parse_dates(series):
    """把「发生时间」解析成日期。

    原包用 str[:10] 截前 10 个字符，遇到 2026/8/8 14:03 这种一位数的月日会截错，
    月份跟着错。这里改成整串交给 pandas 解析。
    """
    s = series.astype(str).str.strip()
    dt = pd.to_datetime(s, errors="coerce", format="mixed")
    return dt


def multi(series):
    """把多值格拆开数数。兼容分号、中文分号；空格子不算。"""
    s = (series.fillna("").astype(str).str.replace("；", ";")
         .str.split(";").explode().str.strip())
    return s[s != ""].value_counts()


def split_cell(v):
    return [x.strip() for x in str(v or "").replace("；", ";").split(";") if x.strip()]


def base_tag(tag):
    """去掉方向后缀： 整体高度:偏高 -> 整体高度"""
    return tag.split(DIR_SEP, 1)[0].strip()


def tag_dir(tag):
    return tag.split(DIR_SEP, 1)[1].strip() if DIR_SEP in tag else ""


def bands_of(cfg):
    b = cfg.get("对称档位")
    if not b:
        sys.exit("[品类配置不完整] 缺少「对称档位」。这几条线每个品类要自己标，不能沿用别的品类。")
    return [(float(x[0]), x[1], x[2] if len(x) > 2 else "") for x in b]


def symmetry(a_cnt, b_cnt, a_name, b_name, bands, min_n=30):
    """两头是否对称。

    凡是两头都可能错的属性（大小、高矮、软硬……），两头都有人抱怨是常态。
    要看的不是量，是两头差多少：差距 = |一头占比 − 另一头占比|。
    """
    a_cnt, b_cnt = int(a_cnt), int(b_cnt)
    tot = a_cnt + b_cnt
    if tot == 0:
        return {"可判定": False, "合计": 0}
    pa, pb = a_cnt / tot * 100, b_cnt / tot * 100
    skew = round(abs(pa - pb), 1)
    lim, name, meaning = next(b for b in bands if skew <= b[0])
    out = {"可判定": tot >= min_n, "一头": a_name, "另一头": b_name,
           "一头条数": a_cnt, "另一头条数": b_cnt, "合计": tot,
           "一头占比": round(pa, 1), "另一头占比": round(pb, 1), "差距": skew,
           "偏向": a_name if a_cnt > b_cnt else (b_name if b_cnt > a_cnt else "持平"),
           "判定": name, "含义": meaning}
    if tot < min_n:
        out["判定"] = "样本少"
        out["含义"] = f"两头合计只有 {tot} 条（不到 {min_n}），差距不稳定，只当线索不当结论"
    return out


def all_tags(cfg, extra=None):
    """标签表里全部合法的细项名（不含方向后缀）。extra = 这一款特有的标签。"""
    ok = set()
    for l1, subs in cfg["哪件事"]["细项"].items():
        for t in subs:
            ok.add(t if isinstance(t, str) else t["名称"])
    for t in (extra or []):
        ok.add(t)
    return ok


def dir_defs(cfg):
    """哪些细项可以带方向，以及它的两头叫什么。 {细项: [一头, 另一头]}"""
    out = {}
    for l1, subs in cfg["哪件事"]["细项"].items():
        for t in subs:
            if isinstance(t, dict) and t.get("两头"):
                out[t["名称"]] = list(t["两头"])
    return out


def dump(obj, path=None):
    txt = json.dumps(obj, ensure_ascii=False, indent=2, default=str)
    if path:
        open(path, "w", encoding="utf-8").write(txt)
    return txt
