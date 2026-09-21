#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
示例数据 · Reddit 线的打标结果。不是规则引擎：每一行是 AI 把那条讨论读完之后写下的判断。

Reddit 比退货、评论多一步：**先分流**——这人到哪一步了、说的是谁的货；再各用各的方法。
每条十二格：
  帖子类型 | 到哪一步 | 说谁的货 | 想解决什么 | 买之前看重什么 | 现在怎么凑合 |
  好评的事 | 差评的事 | 客户的说法 | 该谁改 | 多严重 | 整体好坏
规矩：「该谁改」「多严重」只在说的是我的货、且有差评的事时才填；
      「整体好坏」只给买了的人填；示例里 A-style 指我的货，Brand B/C/D 和 no name 指对手的货。
"""
import sys
import pandas as pd

ASK, SHOP, USE, QUIT, UNK = "没买在问", "正在几家里挑", "买了在用", "用过放弃", "看不出来"
MINE, RIVAL, CAT, DIY, NA = "我的", "对手的", "整个品类", "土办法", "看不出来"
P, L = "产品的事", "页面的事"
W = "宽度与覆盖:偏宽"

T = {
 "Low nose bridge here. My smart glasses slide down every time I look at my phone and end up resting on my cheeks. Is there anything that actually works without looking ridiculous?":
   ("求助",ASK,CAT,"眼镜往下滑; 镜框压在脸颊上","外观隐形","忍着","","","low nose bridge; slide down; rest on my cheeks","","",""),
 "Same problem. Do the stick on nose pads still let the glasses fit in the charging case? That is the only thing stopping me from ordering.":
   ("求助",ASK,CAT,"眼镜往下滑","充电盒收纳","","","","stick on nose pads; fit in the case","","",""),
 "Following. Mine hit my eyelashes when I blink. Would thicker pads fix that or do I need a different frame?":
   ("求助",ASK,CAT,"睫毛碰到镜片","整体高度","","","","hit my eyelashes","","",""),
 "There is no low bridge version of these frames. Before I return them, has anyone found an add on that raises them? Worried anything glued on will leave residue.":
   ("求推荐",ASK,CAT,"镜框压在脸颊上","撕下后留胶; 整体高度","","","","low nose bridge; leave residue","","",""),
 "I see lots of adhesive silicone pads online. Do they actually stay on when you sweat or do they fall off in a week? Do not want to lose a pad on the street.":
   ("求助",ASK,CAT,"","背胶牢固度; 出汗时防滑","","","","stick on nose pads; fall off","","",""),
 "Also curious if they are visible from the front. I wear mine to client meetings.":
   ("求助",ASK,CAT,"","外观隐形","","","","visible from the front","","",""),
 "Any runners solved the bounce? Mine slide on the downhills once I start sweating. Thinking about nose pads or an ear hook, not sure which.":
   ("求助",ASK,CAT,"运动时眼镜乱动; 眼镜往下滑","出汗时防滑","","","","bounce; slide down","","",""),
 "If I raise the frames a couple of mm, do videos end up pointing too high? Anyone tested this?":
   ("求助",ASK,CAT,"","摄像头视角","","","","videos pointing too high","","",""),
 "What thickness do people get? I cannot tell from photos if I need 1.8 or 2.5. No way to try before buying.":
   ("求助",ASK,CAT,"","选档指引; 整体高度","","","","what thickness; no way to try before buying","","",""),
 "Heavy frames, sore nose bridge by lunch. Would soft pads help or is this a weight problem?":
   ("求助",ASK,CAT,"鼻梁压得疼","佩戴舒适","忍着","","","sore nose bridge","","",""),
 "How much are these things? Twelve bucks for four pieces of silicone seems like a lot.":
   ("求助",ASK,CAT,"","值不值","","","","four pieces of silicone","","",""),
 "Most nose pad listings do not say if they fit the large frame. Anyone with the large version confirm?":
   ("求助",ASK,CAT,"","机型适配","","","","large frame","","",""),
 "Deciding between the two popular ones. A says it fits the charging case, B comes in three thicknesses. Which matters more in daily use?":
   ("比较",SHOP,CAT,"","充电盒收纳; 整体高度","","","","fit in the case; three thicknesses","","",""),
 "Go by case fit. If you have to peel them off to charge every night you will stop using them within a week.":
   ("比较",USE,CAT,"","充电盒收纳","","","","fit in the case; peel them off to charge","","",""),
 "I care more about the glue. B fell off me twice. Ask which one survives sweat.":
   ("比较",USE,RIVAL,"","背胶牢固度; 出汗时防滑","","","背胶牢固度","survives sweat","","","差评"),
 "Narrowing it down. Clear ones yellow over time I heard, black ones show on light frames. What did you pick?":
   ("比较",SHOP,CAT,"","耐黄变; 外观隐形","","","","yellow over time","","",""),
 "I am between the thin and thick set. Leaning thin because I read the thick ones do not fit the case.":
   ("比较",SHOP,CAT,"","充电盒收纳; 整体高度","","","","thin and thick; fit in the case","","",""),
 "Comparing nose pads against an ear hook for running. Pads are invisible, hooks are more secure. Tough call.":
   ("比较",SHOP,CAT,"运动时眼镜乱动","外观隐形; 出汗时防滑","","","","invisible; more secure","","",""),
 "One set is double the price and says medical grade silicone. Is that marketing or does it actually feel different?":
   ("比较",SHOP,CAT,"","值不值; 硅胶软硬","","","","medical grade silicone","","",""),
 "Got the A-style pads, 1.8. They fit great, no issues putting the glasses in the case and they barely add height. Just enough to bring my glasses where I want.":
   ("经验分享",USE,MINE,"","","","充电盒收纳; 整体高度","","barely add height","","","好评"),
 "Using the A-style 1.8 set since May. Comfortable, glasses stopped sliding. Only gripe: they are wider than the stock pad so the edge shows a little.":
   ("经验分享",USE,MINE,"眼镜往下滑","","","佩戴舒适; 防滑效果(泛指)",W+"; 外观隐形","wider than the stock pad; edge shows",P,"轻度","好评"),
 "Same set here but the 2.5. Love the lift, hate that it will not go in the case. I peel them off on travel days.":
   ("经验分享",USE,MINE,"","","","整体高度","充电盒收纳","love the lift; fit in the case",P,"中度","中性"),
 "My newest A-style set is not as sticky as the one I bought in winter. First one lasted months, this one a week.":
   ("吐槽",USE,MINE,"","","","","背胶牢固度; 同款批次一致性","not as sticky as the one I bought in winter",P,"严重","差评"),
 "A-style pads fixed the slide for me on easy runs. On hot days one pad peeled off mid run though.":
   ("经验分享",USE,MINE,"运动时眼镜乱动","","","防滑效果(泛指)","背胶牢固度; 出汗时防滑","fall off; mid run",P,"中度","中性"),
 "Soft stick on pads helped me a lot. No more red marks. Been wearing the A-style ones all day at work.":
   ("经验分享",USE,MINE,"鼻梁压得疼","","","佩戴舒适; 硅胶软硬","","no more red marks","","","好评"),
 "I have B. Three thicknesses is nice but the glue is weak. Lost one at the gym in the first week.":
   ("经验分享",USE,RIVAL,"","","","整体高度","背胶牢固度; 出汗时防滑","glue is weak; fall off","","","差评"),
 "B user. The medium thickness still would not fit in my charging case. Sent them back.":
   ("吐槽",QUIT,RIVAL,"","","","","充电盒收纳","fit in the case","","","差评"),
 "Bought a no name set. When I peeled them off there was sticky gunk all over the nose area. Took rubbing alcohol and a lot of patience.":
   ("吐槽",QUIT,RIVAL,"","","","","撕下后留胶","leave residue; sticky gunk","","","差评"),
 "My clear ones from brand C went yellow in a month. Look gross on black frames now.":
   ("吐槽",USE,RIVAL,"","","","","耐黄变; 外观隐形","went yellow in a month","","","差评"),
 "Brand B says fits all but it does not sit right on the large frame, the curve is different.":
   ("吐槽",USE,RIVAL,"","","","","机型适配; 兼容宣称兑现度","says fits all","","","差评"),
 "I use brand C on my regular glasses. Stays on fine, been three months. Too thick for my smart glasses case though.":
   ("经验分享",USE,RIVAL,"","","","背胶牢固度","充电盒收纳","fit in the case; too thick","","","中性"),
 "With B's thickest pads my videos tilt up noticeably. Medium is fine.":
   ("经验分享",USE,RIVAL,"","","","","摄像头视角","videos tilt up","","","中性"),
 "Brand D sport pads have a grippy texture, best for sweat in my experience. They are thick though.":
   ("经验分享",USE,RIVAL,"运动时眼镜乱动","","","出汗时防滑","整体高度:偏高","grippy texture; best for sweat","","","好评"),
 "Tried two brands. Both fell off within two weeks and neither fit the case. Went to an optician and had small screw in pads added instead. Wish I had done that first.":
   ("吐槽",QUIT,RIVAL,"","","去眼镜店调鼻托","","背胶牢固度; 充电盒收纳","fall off; screw in pads","","","差评"),
 "Same. I ended up with an ear hook. Ugly but it works and the glasses still charge.":
   ("经验分享",QUIT,CAT,"","装上后充电","加耳勾或头带","","","ear hook; ugly but it works","","","差评"),
 "Stopped using pads for running, sweat kills the glue every time. A strap is the only thing that holds.":
   ("吐槽",QUIT,CAT,"运动时眼镜乱动","","加耳勾或头带","","背胶牢固度; 出汗时防滑","sweat kills the glue; fall off","","","差评"),
 "Pads made mine sit too high and look weird. Took them off after a day. Now I just push them up like always.":
   ("吐槽",QUIT,CAT,"眼镜往下滑","","忍着","","整体高度:偏高; 外观隐形","sit too high and look weird","","","差评"),
 "After the residue mess I am done with anything adhesive. Not risking it on 300 dollar glasses.":
   ("吐槽",QUIT,CAT,"","撕下后留胶","","","撕下后留胶","leave residue; done with anything adhesive","","","差评"),
 "Cheap hack: a strip of moleskin on each nose pad. Looks bad up close but costs nothing.":
   ("经验分享",USE,DIY,"眼镜往下滑","","垫纸巾或创可贴","","","cheap hack; moleskin","","",""),
 "I use a tiny bit of mouldable glue and shape my own pads. Lasts a year, fits the case because I keep them thin.":
   ("经验分享",USE,DIY,"","充电盒收纳","自己用胶泥或热缩管做","","","shape my own pads; fit in the case","","",""),
 "I folded a band aid over the bridge for months before finding pads. It works but people do ask what is wrong with your glasses.":
   ("经验分享",USE,DIY,"眼镜往下滑","外观隐形","垫纸巾或创可贴","","","band aid over the bridge","","",""),
 "Heat shrink tubing on the arms. Two dollars. Does not fix the nose slide but stops the bounce.":
   ("经验分享",USE,DIY,"运动时眼镜乱动","","自己用胶泥或热缩管做","","","heat shrink tubing","","",""),
 "Honestly just get A. It fits the case.":
   ("比较",USE,MINE,"","","","充电盒收纳","","fit in the case","","","好评"),
 "A-style pads, thin ones. They fit the case. That is all you need to know.":
   ("经验分享",USE,MINE,"","","","充电盒收纳","","fit in the case","","","好评"),
 "A has a large frame version and it fits the case. B does not.":
   ("比较",USE,MINE,"","","","机型适配; 充电盒收纳","","large frame; fit in the case","","","好评"),
 "Check out our store for the best silicone nose pads, use code SLIDE20 for a discount today only!":
   ("广告或无关",UNK,NA,"","","","","","","","",""),
 "Have you tried having a smaller face lol":
   ("广告或无关",UNK,NA,"","","","","","","","",""),
}
COLS = ["帖子类型", "到哪一步", "说谁的货", "想解决什么", "买之前看重什么", "现在怎么凑合",
        "好评的事", "差评的事", "客户的说法", "该谁改", "多严重", "整体好坏"]

def main():
    src, out = sys.argv[1], sys.argv[2]
    d = pd.read_csv(src, dtype=str).fillna("")
    miss = [v for v in d["原话"] if v not in T]
    if miss:
        sys.exit("这些还没读过、没有打标：\n" + "\n".join(miss))
    for i, c in enumerate(COLS):
        d[c] = d["原话"].map(lambda v: T[v][i])
    d.to_csv(out, index=False, encoding="utf-8-sig")
    print(f"写出 {out} · {len(d)} 条")

if __name__ == "__main__":
    main()
