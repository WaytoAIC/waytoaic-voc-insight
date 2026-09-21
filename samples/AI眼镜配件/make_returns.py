#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生成「示例数据 · 退货」。全部是编的，不对应任何真实订单、真实客户。

形状（比例和坑）照一份真实退货数据来：
  · 大部分人只选了原因码、没写字
  · 原话是三段拼出来的：下拉选项|客户写的|是否愿意被联系
  · 有几条只有下拉选项、客户一个字没写
  · "与描述不符""不兼容"两个大筐里装着好几种不同的事
  · 表里混着换货记录，用的是另一套数字原因码
  · 时间是 2026/8/8 14:03 这种一位数月日的写法
  · 有一条德语原话在导出时被弄坏了（变音字母变成问号）
句子全部重写成 AI 眼镜防滑鼻托的说法。固定随机种子，重跑结果一样。
"""
import csv, random, datetime as dt, os

random.seed(20260922)
HERE = os.path.dirname(os.path.abspath(__file__))
PRODUCT = "A款-防滑鼻托套装(2对装)"
NAME = "智能眼镜 硅胶防滑鼻托 背胶款 2对装"
SPECS = ["标准款-1.8mm", "标准款-2.5mm", "大号款-1.8mm", "大号款-2.5mm"]
SPEC_W = [0.30, 0.34, 0.16, 0.20]

# (原因码, 规格, 站点, 原话三段)  —— 手写，逐条不同
V = [
 # —— 整体高度：嫌高 ——
 ("NOT_AS_DESCRIBED","标准款-2.5mm","US","Not as Expected|Pads are too thick, glasses sit way too high on my face|No"),
 ("NOT_AS_DESCRIBED","标准款-2.5mm","US","Not as Expected|Listing said low nose bridge should pick 2.5mm. I did. Way too tall, frames float above my eyebrows|No"),
 ("DEFECTIVE","标准款-2.5mm","US","Defective|lifts the frame so much the camera now points at the ceiling|No"),
 ("ORDERED_WRONG_ITEM","标准款-2.5mm","US","Wrong Item|My bad, should have gotten the 1.8. Already reordered the thinner ones and they are fine|No"),
 ("NOT_AS_DESCRIBED","大号款-2.5mm","US","Not as Expected|followed the size recommendation on the page, 2.5 is too high for me|Yes"),
 ("NOT_AS_DESCRIBED","大号款-2.5mm","US","Not as Expected|Too thick. Went by the chart for low bridge. Glasses look like they are hovering|No"),
 ("QUALITY_UNACCEPTABLE","标准款-2.5mm","US","Poor Quality|too tall, pushes lenses away from my eyes|No"),
 ("NOT_AS_DESCRIBED","标准款-1.8mm","US","Not as Expected|even the thin one raises the glasses too much for me|No"),
 ("MISORDERED","大号款-2.5mm","US","Wrong Item|ordered 2.5 by mistake, will replace with 1.8|No"),
 ("NOT_AS_DESCRIBED","标准款-2.5mm","US","Not as Expected|page says pick 2.5 if glasses slide. They did stop sliding but now sit too high and the photos are all tilted up|No"),
 ("NOT_AS_DESCRIBED","大号款-2.5mm","US","Not as Expected|too high on nose, as recommended size|No"),
 ("DEFECTIVE","标准款-2.5mm","US","Defective|Sits too high. Took them off after an hour|No"),
 # —— 整体高度：嫌矮 ——
 ("DEFECTIVE","标准款-1.8mm","US","Defective|still slides down, not thick enough|No"),
 ("NOT_AS_DESCRIBED","标准款-1.8mm","US","Not as Expected|1.8mm barely makes a difference, glasses still rest on my cheeks|No"),
 ("ORDERED_WRONG_ITEM","标准款-1.8mm","US","Wrong Item|need thicker. Will order the 2.5|No"),
 ("DEFECTIVE","大号款-1.8mm","US","Defective|too thin to help, frame still touches my cheeks when I smile|No"),
 ("NOT_AS_DESCRIBED","大号款-1.8mm","US","Not as Expected|not tall enough for a flat nose bridge|No"),
 ("QUALITY_UNACCEPTABLE","标准款-1.8mm","US","Poor Quality|too low, no real lift|No"),
 ("ORDERED_WRONG_ITEM","大号款-1.8mm","US","Wrong Item|I picked the thin one, my fault, exchanging for the thicker set|No"),
 ("DEFECTIVE","标准款-1.8mm","US","Defective|Does not raise the glasses enough. Still sliding by lunch|No"),
 ("NOT_AS_DESCRIBED","标准款-2.5mm","US","Not as Expected|even 2.5 is not enough height for me|No"),
 ("NOT_AS_DESCRIBED","标准款-1.8mm","US","Not as Expected|too short|No"),
 ("DEFECTIVE","大号款-1.8mm","US","Defective|needs to be thicker, glasses slip when I look down|No"),
 # —— 宽度与覆盖：全说太宽 ——
 ("NOT_AS_DESCRIBED","标准款-1.8mm","US","Not as Expected|pad is wider than the original nose piece, edges stick out and look ugly|No"),
 ("NOT_AS_DESCRIBED","标准款-2.5mm","US","Not as Expected|overhangs the nose pad on both sides, you can see it from the front|No"),
 ("QUALITY_UNACCEPTABLE","大号款-1.8mm","US","Poor Quality|too wide for the nose area, sticks out past the frame|No"),
 ("NOT_AS_DESCRIBED","大号款-2.5mm","US","Not as Expected|Wider than the built in pad. Looks like I taped something to my glasses|No"),
 ("DEFECTIVE","标准款-2.5mm","US","Defective|the pads are too wide, they catch dust on the exposed sticky edge|No"),
 ("NOT_AS_DESCRIBED","标准款-1.8mm","US","Not as Expected|width is off, hangs over the edge|No"),
 ("QUALITY_UNACCEPTABLE","标准款-2.5mm","US","Poor Quality|Too wide. Had to trim with scissors which defeats the purpose|No"),
 ("NOT_AS_DESCRIBED","大号款-1.8mm","US","Not as Expected|pads bigger than the nose rest so the glue edge shows|No"),
 ("NOT_AS_DESCRIBED","大号款-2.5mm","US","Not as Expected|too wide, visible from the front, embarrassing in meetings|No"),
 # —— 防滑与固定：量小但严重 ——
 ("DEFECTIVE","标准款-2.5mm","US","Defective|Fell off on day one and my glasses hit the pavement. Lens is scratched. Ridiculous!|Yes"),
 ("DEFECTIVE","标准款-1.8mm","US","Defective|adhesive gave out the first time I wore them, one pad is gone|No"),
 ("DEFECTIVE","大号款-2.5mm","US","Defective|pad came off inside the charging case and now it is stuck in there|Yes"),
 ("NOT_AS_DESCRIBED","标准款-2.5mm","US","Not as Described|Listing says sweat proof adhesive. Came off after one gym session|No"),
 ("DEFECTIVE","标准款-1.8mm","US","Defective|glue fails when I sweat, pads slide around on the frame|No"),
 ("NOT_AS_DESCRIBED","大号款-1.8mm","US","Not as Described|says stays on for months, mine lasted two days|No"),
 ("DEFECTIVE","标准款-2.5mm","US","Defective|They don't work for me. Glasses still slide when I run|No"),
 ("DEFECTIVE","大号款-2.5mm","US","Defective|still slips down my nose in hot weather|No"),
 ("QUALITY_UNACCEPTABLE","标准款-1.8mm","US","Poor Quality|left sticky residue on my 300 dollar glasses when I peeled it off. Not happy|Yes"),
 ("DEFECTIVE","标准款-2.5mm","US","Defective|slides|No"),
 # —— 兼容与收纳：说法五花八门 ——
 ("NOT_COMPATIBLE","标准款-2.5mm","US","Not Compatible|with pads on, glasses won't seat in the charging case|No"),
 ("NOT_COMPATIBLE","大号款-2.5mm","US","Not Compatible|case will not close with these installed|No"),
 ("NOT_COMPATIBLE","标准款-2.5mm","US","Not Compatible|fits in the case but does not charge, the contacts don't touch|No"),
 ("NOT_AS_DESCRIBED","标准款-2.5mm","US","Not as Described|only the 1.8 fits the case. The 2.5 doesn't. Nowhere on the page does it say that|No"),
 ("NOT_COMPATIBLE","标准款-1.8mm","US","Not Compatible|Great idea and really comfortable, but the glasses stopped charging in the case|No"),
 ("NOT_COMPATIBLE","大号款-1.8mm","US","Not Compatible|have to press the glasses down hard to get the charge light on|No"),
 ("NOT_AS_DESCRIBED","大号款-2.5mm","US","Not as Described|photo shows glasses in the case with pads on. Mine do not fit in the case at all|Yes"),
 ("NOT_COMPATIBLE","标准款-2.5mm","US","Not Compatible|case|No"),
 ("NOT_COMPATIBLE","标准款-1.8mm","US","Not Compatible|does not fit the Headliner frame, nose area is a different shape|No"),
 ("NOT_COMPATIBLE","标准款-1.8mm","US","Not Compatible|I have the large frame and bought standard. My mistake, reordering the large version|No"),
 ("NOT_COMPATIBLE","大号款-1.8mm","US","Not Compatible|not for Skyler model even though title says fits all|No"),
 ("NOT_COMPATIBLE","大号款-2.5mm","US","Not Compatible|wrong model for my glasses, ordered the other one|No"),
 ("NOT_COMPATIBLE","标准款-2.5mm","US","Not Compatible|changes the camera angle, every video is aimed too high|No"),
 # —— 材质与做工 ——
 ("QUALITY_UNACCEPTABLE","标准款-1.8mm","US","Poor Quality|silicone is hard, leaves red marks on my nose after an hour|No"),
 ("QUALITY_UNACCEPTABLE","大号款-2.5mm","US","Poor Quality|much stiffer than I expected, not soft at all|No"),
 ("QUALITY_UNACCEPTABLE","标准款-2.5mm","US","Poor Quality|too squishy, compresses flat so no lift left|No"),
 ("QUALITY_UNACCEPTABLE","标准款-1.8mm","US","Poor Quality|turned yellow within two weeks|No"),
 ("NOT_AS_DESCRIBED","标准款-2.5mm","US","Not as Described|pictured crystal clear, arrived cloudy white. Very visible on black frames|No"),
 ("NOT_AS_DESCRIBED","大号款-1.8mm","US","Not as Described|color is not what the picture shows|No"),
 ("QUALITY_UNACCEPTABLE","大号款-1.8mm","US","Poor Quality|rough edge on one pad, scratches my skin|No"),
 # —— 少发错发：藏在别的码下面 ——
 ("NOT_AS_DESCRIBED","标准款-1.8mm","US","Not as Described|listing says 2 pairs, only 1 pair in the bag|No"),
 ("NOT_AS_DESCRIBED","标准款-2.5mm","US","Not as Described|Says 2 pairs. Got 3 single pads, not even 2 full pairs|Yes"),
 ("NOT_COMPATIBLE","大号款-2.5mm","US","Not Compatible|ordered the large frame version, package label says standard|No"),
 ("NOT_COMPATIBLE","大号款-1.8mm","US","Not Compatible|received 2.5 but I ordered 1.8, bag was mislabeled|No"),
 ("NOT_AS_DESCRIBED","标准款-2.5mm","US","Not as Described|missing the alcohol wipe and the placement guide shown in the photos|No"),
 # —— 不该买这款 ——
 ("NOT_AS_DESCRIBED","标准款-1.8mm","US","Not as Expected|thought these were screw in replacement nose pads. These are just stickers|No"),
 ("NOT_AS_DESCRIBED","标准款-2.5mm","US","Not as Expected|I wanted something to stop the arms slipping behind my ears. This only does the nose|No"),
 ("NOT_AS_DESCRIBED","大号款-2.5mm","US","Not as Expected|expected a full nose bridge replacement, not stick on pads|No"),
 ("NOT_AS_DESCRIBED","标准款-1.8mm","US","Not as Expected|very nice idea but I don't want anything glued to my glasses|No"),
 # —— 只有一条的线索 ——
 ("QUALITY_UNACCEPTABLE","标准款-2.5mm","US","Poor Quality|second order from the same listing. These pads are noticeably harder than my first set|No"),
 # —— 替别人买 ——
 ("NOT_AS_DESCRIBED","标准款-2.5mm","US","Not as Expected|bought for my dad, he says it feels weird and refuses to wear them|No"),
 ("ORDERED_WRONG_ITEM","标准款-1.8mm","US","Wrong Item|gift for my husband, he has the large frames so these don't fit. Getting the right ones|No"),
 # —— 泛泛的 / 残句 ——
 ("QUALITY_UNACCEPTABLE","标准款-1.8mm","US","Poor Quality|cheap|No"),
 ("QUALITY_UNACCEPTABLE","大号款-2.5mm","US","Poor Quality|not worth the price for four bits of silicone|No"),
 ("NOT_AS_DESCRIBED","标准款-2.5mm","US","Not as Expected|not what I expected|No"),
 ("NOT_AS_DESCRIBED","标准款-1.8mm","US","Not as Expected|didn't fit|No"),
 ("NOT_AS_DESCRIBED","大号款-1.8mm","US","Not as Expected|fit|No"),
 ("DEFECTIVE","标准款-2.5mm","US","Defective|not good|No"),
 ("NOT_COMPATIBLE","标准款-2.5mm","US","Not Compatible|doesn't fit|No"),
 ("NOT_AS_DESCRIBED","大号款-2.5mm","US","Not as Expected|thickness|No"),
 ("MISORDERED","标准款-1.8mm","US","Wrong Item|ordered twice by accident|No"),
 ("QUALITY_UNACCEPTABLE","标准款-2.5mm","US","Poor Quality|looked like the bag had been opened before, pads had lint on them|No"),
 # —— 补：高度类再加 8 条，让两头合计过 30 条 ——
 ("NOT_AS_DESCRIBED","标准款-2.5mm","US","Not as Expected|too thick for my nose, glasses ride up high|No"),
 ("DEFECTIVE","大号款-2.5mm","US","Defective|sits too tall, bottom of the lens is above my eye line|No"),
 ("NOT_AS_DESCRIBED","标准款-2.5mm","US","Not as Expected|The page told me to go 2.5 for a low bridge. Too much lift|No"),
 ("ORDERED_WRONG_ITEM","大号款-2.5mm","US","Wrong Item|2.5 was too much, swapping for the 1.8|No"),
 ("DEFECTIVE","标准款-1.8mm","US","Defective|not enough lift, lashes still hit the lens|No"),
 ("NOT_AS_DESCRIBED","大号款-1.8mm","US","Not as Expected|thinner than I hoped, no change in how the glasses sit|No"),
 ("QUALITY_UNACCEPTABLE","标准款-1.8mm","US","Poor Quality|too thin|No"),
 ("ORDERED_WRONG_ITEM","标准款-1.8mm","US","Wrong Item|should have ordered the thicker ones, that is on me. Reordered|No"),
 # —— 德国站：一条好的，一条导出时被弄坏的 ——
 ("DEFECTIVE","标准款-2.5mm","DE","Defective|Hält nicht, der Kleber löst sich nach zwei Tagen|No"),
 ("NOT_COMPATIBLE","标准款-2.5mm","DE","Not Compatible|Passt nicht ins Ladeetui, zu gro?? f??r das Etui|No"),
 # —— 只有下拉选项、客户一个字没写（会被清洗掉）——
 ("DEFECTIVE","标准款-1.8mm","US","Defective|N/A"),
 ("NOT_AS_DESCRIBED","标准款-2.5mm","US","Not as Described|No"),
 ("NOT_COMPATIBLE","大号款-2.5mm","US","Not Compatible||No"),
 ("QUALITY_UNACCEPTABLE","标准款-1.8mm","US","Poor Quality|none|No"),
 ("NOT_AS_DESCRIBED","大号款-1.8mm","US","Not as Expected|n/a|No"),
 ("DEFECTIVE","大号款-2.5mm","US","Defective|-|No"),
 ("NOT_COMPATIBLE","标准款-2.5mm","US","Not Compatible|No"),
]

KEEP_W = {"NOT_AS_DESCRIBED":.30,"DEFECTIVE":.22,"NOT_COMPATIBLE":.26,
          "QUALITY_UNACCEPTABLE":.10,"ORDERED_WRONG_ITEM":.08,"MISORDERED":.04}
DROP_W = {"UNWANTED_ITEM":.40,"NO_REASON_GIVEN":.22,"FOUND_BETTER_PRICE":.08,"DAMAGED_BY_FC":.07,
          "MISSED_ESTIMATED_DELIVERY":.06,"UNAUTHORIZED_PURCHASE":.05,"MISSING_PARTS":.04,
          "SWITCHEROO":.03,"UNDELIVERABLE_UNKNOWN":.03,"DAMAGED_BY_CARRIER":.02}

def pick(w): return random.choices(list(w), weights=list(w.values()))[0]
def when():
    d = dt.datetime(2026,1,3) + dt.timedelta(days=random.randint(0,232), minutes=random.randint(0,1439))
    return f"{d.year}/{d.month}/{d.day} {d.hour}:{d.minute:02d}"   # 故意写成一位数月日

rows=[]
for code,spec,site,voice in V:
    rows.append(["fba_return",code,voice,spec,site])
for _ in range(182):                       # 留下的码，但客户没写字
    rows.append(["fba_return",pick(KEEP_W),"",random.choices(SPECS,SPEC_W)[0],"US"])
for _ in range(74):                        # 跟产品无关的码
    rows.append(["fba_return",pick(DROP_W),"",random.choices(SPECS,SPEC_W)[0],"US"])
for _ in range(14):                        # 换货：另一套数字码
    rows.append(["replacement",random.choice(["0","2","4","5","10"]),"",random.choices(SPECS,SPEC_W)[0],"US"])
random.shuffle(rows)

out=os.path.join(HERE,"退货原始导出-示例.csv")
with open(out,"w",newline="",encoding="utf-8-sig") as f:
    w=csv.writer(f)
    w.writerow(["事件ID","订单号","事件类型","退货原因代码","退货原因明细","产品","品名","规格","站点","发生时间","订单原因首件"])
    for i,(ev,code,voice,spec,site) in enumerate(rows,1):
        w.writerow([f"SAMPLE-EV-{i:04d}",f"SAMPLE-ORDER-{random.randint(1,9999):04d}",ev,code,voice,
                    PRODUCT,NAME,spec,site,when(),"1" if random.random()<0.93 else "0"])
print("写出",out,"共",len(rows),"行；手写原话",len(V),"条")
