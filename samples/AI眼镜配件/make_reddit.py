#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生成「示例数据 · Reddit」。全部是编的：群组名、帖子、作者都不对应任何真实的群组和用户。

形状照真实的讨论来：帖子和回复混着；求助、求推荐、比较、吐槽、经验分享都有；
有还没买在问的、正在几家里挑的、买了在用的、用过放弃的；说的有我的货、对手的货、整个品类、自己凑合的土办法；
有一两条广告和跑题的；有已删除的；有一个人反复发的。
真上手时，这份表由采集工具导出（讲师机用 TikHub，学员用免费的 reddit-readonly），人手动、低频、只读、不存库。
"""
import csv, os
HERE = os.path.dirname(os.path.abspath(__file__))
G1, G2, G3 = "r/示例-智能眼镜", "r/示例-戴眼镜的人", "r/示例-跑步"
P, C = "帖子", "回复"
# (群组, 类型, 标题, 正文, 点赞, 日期, 作者)
R = [
 # —— 没买，在问 ——
 (G1,P,"Glasses keep sliding down my nose, any fix?","Low nose bridge here. My smart glasses slide down every time I look at my phone and end up resting on my cheeks. Is there anything that actually works without looking ridiculous?",182,"2026/6/3","u01"),
 (G1,C,"Glasses keep sliding down my nose, any fix?","Same problem. Do the stick on nose pads still let the glasses fit in the charging case? That is the only thing stopping me from ordering.",96,"2026/6/3","u02"),
 (G1,C,"Glasses keep sliding down my nose, any fix?","Following. Mine hit my eyelashes when I blink. Would thicker pads fix that or do I need a different frame?",41,"2026/6/4","u03"),
 (G1,P,"Asian fit options for smart glasses?","There is no low bridge version of these frames. Before I return them, has anyone found an add on that raises them? Worried anything glued on will leave residue.",74,"2026/6/10","u04"),
 (G2,P,"Nose pads for plastic frames - do they fall off?","I see lots of adhesive silicone pads online. Do they actually stay on when you sweat or do they fall off in a week? Do not want to lose a pad on the street.",58,"2026/5/22","u05"),
 (G2,C,"Nose pads for plastic frames - do they fall off?","Also curious if they are visible from the front. I wear mine to client meetings.",22,"2026/5/22","u06"),
 (G3,P,"Smart glasses bounce when I run","Any runners solved the bounce? Mine slide on the downhills once I start sweating. Thinking about nose pads or an ear hook, not sure which.",67,"2026/7/2","u07"),
 (G1,P,"Will nose pads mess up the camera angle?","If I raise the frames a couple of mm, do videos end up pointing too high? Anyone tested this?",39,"2026/7/9","u08"),
 (G1,C,"Day one must haves for new owners?","What thickness do people get? I cannot tell from photos if I need 1.8 or 2.5. No way to try before buying.",35,"2026/7/15","u09"),
 (G2,P,"Glasses leave my nose sore by noon","Heavy frames, sore nose bridge by lunch. Would soft pads help or is this a weight problem?",28,"2026/6/18","u10"),
 (G1,C,"Glasses keep sliding down my nose, any fix?","How much are these things? Twelve bucks for four pieces of silicone seems like a lot.",12,"2026/6/5","u11"),
 (G1,P,"Large frame owners: do accessories fit?","Most nose pad listings do not say if they fit the large frame. Anyone with the large version confirm?",31,"2026/7/20","u12"),
 # —— 正在几家里挑 ——
 (G1,P,"Brand A vs Brand B stick on pads","Deciding between the two popular ones. A says it fits the charging case, B comes in three thicknesses. Which matters more in daily use?",88,"2026/6/12","u13"),
 (G1,C,"Brand A vs Brand B stick on pads","Go by case fit. If you have to peel them off to charge every night you will stop using them within a week.",120,"2026/6/12","u14"),
 (G1,C,"Brand A vs Brand B stick on pads","I care more about the glue. B fell off me twice. Ask which one survives sweat.",64,"2026/6/13","u15"),
 (G2,P,"Clear vs black silicone pads?","Narrowing it down. Clear ones yellow over time I heard, black ones show on light frames. What did you pick?",26,"2026/5/30","u16"),
 (G1,C,"Day one must haves for new owners?","I am between the thin and thick set. Leaning thin because I read the thick ones do not fit the case.",47,"2026/7/16","u17"),
 (G3,C,"Smart glasses bounce when I run","Comparing nose pads against an ear hook for running. Pads are invisible, hooks are more secure. Tough call.",19,"2026/7/3","u18"),
 (G1,P,"Is the pricier set worth it?","One set is double the price and says medical grade silicone. Is that marketing or does it actually feel different?",17,"2026/8/1","u19"),
 # —— 买了，在用（我的货）——
 (G1,C,"Day one must haves for new owners?","Got the A-style pads, 1.8. They fit great, no issues putting the glasses in the case and they barely add height. Just enough to bring my glasses where I want.",141,"2026/7/15","u20"),
 (G1,P,"Nose pads review after 2 months","Using the A-style 1.8 set since May. Comfortable, glasses stopped sliding. Only gripe: they are wider than the stock pad so the edge shows a little.",53,"2026/7/28","u21"),
 (G1,C,"Nose pads review after 2 months","Same set here but the 2.5. Love the lift, hate that it will not go in the case. I peel them off on travel days.",44,"2026/7/28","u22"),
 (G1,C,"Nose pads review after 2 months","My newest A-style set is not as sticky as the one I bought in winter. First one lasted months, this one a week.",38,"2026/7/29","u23"),
 (G3,C,"Smart glasses bounce when I run","A-style pads fixed the slide for me on easy runs. On hot days one pad peeled off mid run though.",25,"2026/7/4","u24"),
 (G2,C,"Glasses leave my nose sore by noon","Soft stick on pads helped me a lot. No more red marks. Been wearing the A-style ones all day at work.",33,"2026/6/19","u25"),
 # —— 买了，在用（对手的货）——
 (G1,C,"Brand A vs Brand B stick on pads","I have B. Three thicknesses is nice but the glue is weak. Lost one at the gym in the first week.",72,"2026/6/13","u26"),
 (G1,C,"Brand A vs Brand B stick on pads","B user. The medium thickness still would not fit in my charging case. Sent them back.",51,"2026/6/14","u27"),
 (G1,P,"PSA: cheap pads left residue on my frames","Bought a no name set. When I peeled them off there was sticky gunk all over the nose area. Took rubbing alcohol and a lot of patience.",109,"2026/5/18","u28"),
 (G2,C,"Clear vs black silicone pads?","My clear ones from brand C went yellow in a month. Look gross on black frames now.",30,"2026/5/31","u16"),
 (G1,C,"Large frame owners: do accessories fit?","Brand B says fits all but it does not sit right on the large frame, the curve is different.",27,"2026/7/21","u29"),
 (G2,C,"Nose pads for plastic frames - do they fall off?","I use brand C on my regular glasses. Stays on fine, been three months. Too thick for my smart glasses case though.",18,"2026/5/23","u30"),
 (G1,C,"Will nose pads mess up the camera angle?","With B's thickest pads my videos tilt up noticeably. Medium is fine.",21,"2026/7/10","u31"),
 (G3,C,"Smart glasses bounce when I run","Brand D sport pads have a grippy texture, best for sweat in my experience. They are thick though.",16,"2026/7/5","u32"),
 # —— 用过，放弃了 ——
 (G1,P,"Gave up on stick on nose pads","Tried two brands. Both fell off within two weeks and neither fit the case. Went to an optician and had small screw in pads added instead. Wish I had done that first.",95,"2026/8/5","u33"),
 (G1,C,"Gave up on stick on nose pads","Same. I ended up with an ear hook. Ugly but it works and the glasses still charge.",40,"2026/8/5","u34"),
 (G3,C,"Smart glasses bounce when I run","Stopped using pads for running, sweat kills the glue every time. A strap is the only thing that holds.",37,"2026/7/6","u07"),
 (G2,C,"Glasses leave my nose sore by noon","Pads made mine sit too high and look weird. Took them off after a day. Now I just push them up like always.",14,"2026/6/20","u35"),
 (G1,C,"PSA: cheap pads left residue on my frames","After the residue mess I am done with anything adhesive. Not risking it on 300 dollar glasses.",29,"2026/5/19","u36"),
 # —— 土办法 ——
 (G1,C,"Glasses keep sliding down my nose, any fix?","Cheap hack: a strip of moleskin on each nose pad. Looks bad up close but costs nothing.",66,"2026/6/4","u37"),
 (G2,C,"Nose pads for plastic frames - do they fall off?","I use a tiny bit of mouldable glue and shape my own pads. Lasts a year, fits the case because I keep them thin.",45,"2026/5/24","u38"),
 (G1,C,"Asian fit options for smart glasses?","I folded a band aid over the bridge for months before finding pads. It works but people do ask what is wrong with your glasses.",52,"2026/6/11","u39"),
 (G3,C,"Smart glasses bounce when I run","Heat shrink tubing on the arms. Two dollars. Does not fix the nose slide but stops the bounce.",23,"2026/7/7","u40"),
 # —— 同一个人反复发 ——
 (G1,C,"Brand A vs Brand B stick on pads","Honestly just get A. It fits the case.",9,"2026/6/14","u14"),
 (G1,C,"Day one must haves for new owners?","A-style pads, thin ones. They fit the case. That is all you need to know.",15,"2026/7/16","u14"),
 (G1,C,"Large frame owners: do accessories fit?","A has a large frame version and it fits the case. B does not.",11,"2026/7/21","u14"),
 # —— 广告、跑题、已删除、太短 ——
 (G1,P,"Best nose pads 2026 - 20% off link inside","Check out our store for the best silicone nose pads, use code SLIDE20 for a discount today only!",2,"2026/6/20","u41"),
 (G1,C,"Glasses keep sliding down my nose, any fix?","Have you tried having a smaller face lol",18,"2026/6/3","u42"),
 (G1,C,"Glasses keep sliding down my nose, any fix?","[deleted]",1,"2026/6/3","u43"),
 (G2,C,"Clear vs black silicone pads?","this",3,"2026/5/30","u44"),
]
out = os.path.join(HERE, "Reddit原始导出-示例.csv")
with open(out, "w", newline="", encoding="utf-8-sig") as f:
    w = csv.writer(f)
    w.writerow(["帖子ID", "群组", "类型", "标题", "正文", "点赞数", "发生时间", "作者", "链接"])
    for i, (g, t, title, body, up, date, au) in enumerate(R, 1):
        w.writerow([f"SAMPLE-RD-{i:04d}", g, t, title, body, up, f"{date} {9 + i % 10}:{(i * 11) % 60:02d}", f"示例用户_{au}", ""])
assert len({r[3] for r in R}) == len(R), "正文有重复"
print("写出", out, "共", len(R), "条")
