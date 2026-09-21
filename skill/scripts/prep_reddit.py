#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Reddit 线（进阶版）· 第 1 步 清洗

做五件事并打印数据体检：
  1. 去掉已删除的、太短的
  2. 去重
  3. 算一下"同一个人反复发"占多少（防止一个人刷屏被当成很多人的意见）
  4. **把作者名去掉**，换成无意义的编号（同一个人还是同一个编号，但认不出是谁）
  5. 解析日期、算月份；各群组各拿到多少条

广告帖、跑题帖脚本不判——那要读内容，留给打标那一步标成「广告或无关」。

合规提醒：Reddit 的数据只能人手动、低频、只读地拿；不存进库、不设定时任务、不拿去喂模型训练。
"""
import argparse, hashlib, sys
from voc_common import pd, load_config, read_any, parse_dates, dump

DEAD = {"[deleted]", "[removed]", ""}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("src")
    ap.add_argument("--config", required=True)
    ap.add_argument("--out", default="cleaned.csv")
    ap.add_argument("--report", default=None)
    a = ap.parse_args()

    cfg = load_config(a.config)
    if "Reddit" not in cfg:
        sys.exit("[品类配置里没有「Reddit」这一块] 进阶版才用得到，对照示例配置补上。")
    col = dict(cfg["输入列"]["Reddit"])
    rc = cfg["Reddit"]
    df, enc = read_any(a.src)
    must = ["原话", "群组", "时间"]
    missing = [f"{k}（你的列名填的是「{col.get(k,'')}」）" for k in must if not col.get(k) or col[k] not in df.columns]
    if missing:
        sys.exit("[前提不满足] 表里找不到这些必需的列：\n  " + "\n  ".join(missing))
    raw_n = len(df)

    ren = {col["原话"]: "原话", col["群组"]: "群组", col.get("类型", ""): "类型", col.get("标题", ""): "标题",
           col.get("点赞", ""): "点赞", col.get("记录编号", ""): "记录编号", col.get("作者", ""): "_作者"}
    d = df.rename(columns={k: v for k, v in ren.items() if k and k in df.columns and k != v}).copy()
    d["原话"] = d["原话"].fillna("").astype(str).str.strip()
    dead = d["原话"].isin(DEAD)
    short = (~dead) & (d["原话"].str.len() < int(rc.get("最短字数", 15)))
    d = d[~dead & ~short].copy()
    before = len(d)
    d = d.drop_duplicates(subset=["原话"]).reset_index(drop=True)
    dup_n = before - len(d)

    top_share, heavy = None, []
    if "_作者" in d.columns:
        salt = "voc-insight"
        d["发言人"] = d["_作者"].astype(str).map(lambda s: "人-" + hashlib.sha256((salt + s).encode()).hexdigest()[:6])
        vc = d["发言人"].value_counts()
        top_share = round(float(vc.iloc[0] / len(d)), 3) if len(d) else 0
        heavy = [{"发言人": k, "条数": int(v)} for k, v in vc.items() if v >= 3]
        d = d.drop(columns=["_作者"])
    for c in [x for x in d.columns if x in ("链接", "作者", col.get("作者", ""))]:
        d = d.drop(columns=[c])

    dt = parse_dates(d[col["时间"]])
    d["日期"] = dt.dt.strftime("%Y-%m-%d")
    d["月份"] = dt.dt.to_period("M").astype(str)
    if "点赞" in d.columns:
        d["点赞"] = pd.to_numeric(d["点赞"], errors="coerce").fillna(0).astype(int)
    d.insert(0, "序号", range(1, len(d) + 1))
    order = ["序号", "记录编号", "群组", "类型", "标题", "点赞", "日期", "月份", "发言人", "原话"]
    d[[c for c in order if c in d.columns]].to_csv(a.out, index=False, encoding="utf-8-sig")

    rep = {
        "品类": cfg["品类"], "配置版本": cfg.get("版本", ""), "文件编码": enc,
        "原始条数": raw_n, "剔掉已删除的": int(dead.sum()), "剔掉太短的": int(short.sum()), "剔掉重复的": dup_n,
        "进入打标": len(d),
        "各群组": d["群组"].value_counts().to_dict(),
        "帖子与回复": d["类型"].value_counts().to_dict() if "类型" in d.columns else {},
        "时间跨度": [d["月份"].min(), d["月份"].max()] if len(d) else None,
        "同一个人最多占": top_share, "发了 3 条以上的人": heavy,
        "作者名": "已去掉，换成了认不出人的编号",
    }
    warn = {}
    if len(d) < 30:
        warn["样本量"] = "不到 30 条：只通读，不要出任何比例。"
    if top_share is not None and top_share >= float(rc.get("同一作者占比提醒线", 0.15)):
        warn["同一个人刷屏"] = f"有一个人占了 {top_share:.0%}。看比例时要留意是不是他一个人的意见。"
    elif heavy:
        warn["同一个人反复发"] = f"有 {len(heavy)} 个人发了 3 条以上。引用他们的话时别当成好几个人的意见。"
    if len(d["群组"].unique()) < 3:
        warn["群组太少"] = "建议挑 3–5 个：一个聊这类产品的、一个聊这群人的、一个聊这个使用场景的。"
    rep["提醒"] = warn
    print(dump(rep, a.report))


if __name__ == "__main__":
    main()
