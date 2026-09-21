#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
示例数据 · 退货线的打标结果。

这不是规则引擎。下面每一行是 AI 把那条原话读完之后逐条写下的判断，
按原话全文对应回去（不按序号，免得示例数据重排后对不上）。
真跑的时候这一步由 agent 直接产出 tagged.csv，不需要这个文件。

每条八格：大类 | 细项 | 谁在说 | 什么情况下 | 过程感受 | 该谁改 | 多严重 | 能否挽回
"""
import os, sys
import pandas as pd

A, B, C, D, E, F = "高度与贴合", "防滑与固定", "兼容与收纳", "材质与做工", "综合质量", "非产品因素"
P, L, U, X, Q, O = "产品的事", "页面的事", "客户自己选错", "不该买这款", "说不清", "其他"
GUIDE = "照页面指引选的"

T = {
 "followed the size recommendation on the page, 2.5 is too high for me": (A,"整体高度:偏高; 选档指引",GUIDE,"","",L,"中度","否"),
 "very nice idea but I don't want anything glued to my glasses": (E,"贴片式形态(这一款特有); 与预期(泛指)","","","",X,"轻度","否"),
 "listing says 2 pairs, only 1 pair in the bag": (F,"发货准确","","","收货第一印象",O,"中度","否"),
 "didn't fit": (A,"合适度(没说方向)","","","",Q,"轻度","否"),
 "Listing says sweat proof adhesive. Came off after one gym session": (B,"背胶牢固度; 防滑宣称兑现度","","运动出汗","",L,"严重","否"),
 "Sits too high. Took them off after an hour": (A,"整体高度:偏高","","","佩戴舒适度",Q,"中度","否"),
 "even 2.5 is not enough height for me": (A,"整体高度:偏矮","","","",Q,"中度","否"),
 "page says pick 2.5 if glasses slide. They did stop sliding but now sit too high and the photos are all tilted up": (A,"整体高度:偏高; 选档指引; 摄像头视角",GUIDE,"","安心感(夸)",L,"中度","否"),
 "They don't work for me. Glasses still slide when I run": (B,"防滑效果(泛指)","","运动出汗","",P,"严重","否"),
 "too high on nose, as recommended size": (A,"整体高度:偏高; 选档指引",GUIDE,"","",L,"中度","否"),
 "not good": (E,"质量(泛指)","","","",Q,"中度","否"),
 "not for Skyler model even though title says fits all": (C,"机型适配; 兼容宣称兑现度","","","",L,"中度","否"),
 "second order from the same listing. These pads are noticeably harder than my first set": (E,"同款批次一致性; 硅胶软硬:偏硬","长期佩戴","","",P,"中度","否"),
 "not worth the price for four bits of silicone": (E,"值不值","","","",Q,"轻度","否"),
 "Great idea and really comfortable, but the glasses stopped charging in the case": (C,"装上后充电","","放回充电盒时","佩戴舒适度(夸)",P,"中度","否"),
 "color is not what the picture shows": (D,"颜色与图片一致","","","",L,"中度","否"),
 "fit": (A,"合适度(没说方向)","","","",Q,"轻度","否"),
 "pad is wider than the original nose piece, edges stick out and look ugly": (A,"宽度与覆盖:偏宽","原装鼻托","","外观体面度",P,"中度","否"),
 "thickness": (A,"合适度(没说方向)","","","",Q,"轻度","否"),
 "Pads are too thick, glasses sit way too high on my face": (A,"整体高度:偏高","","","",Q,"中度","否"),
 "too short": (A,"整体高度:偏矮","","","",Q,"轻度","否"),
 "too wide for the nose area, sticks out past the frame": (A,"宽度与覆盖:偏宽","","","",P,"中度","否"),
 "looked like the bag had been opened before, pads had lint on them": (E,"新旧状态","","","收货第一印象",P,"严重","否"),
 "does not fit the Headliner frame, nose area is a different shape": (C,"机型适配","","","",Q,"中度","否"),
 "Says 2 pairs. Got 3 single pads, not even 2 full pairs": (F,"发货准确","","","收货第一印象",O,"中度","否"),
 "glue fails when I sweat, pads slide around on the frame": (B,"出汗时防滑","","运动出汗","",P,"严重","否"),
 "not tall enough for a flat nose bridge": (A,"整体高度:偏矮","","","",Q,"中度","否"),
 "changes the camera angle, every video is aimed too high": (C,"摄像头视角","","","",P,"中度","否"),
 "too wide, visible from the front, embarrassing in meetings": (A,"宽度与覆盖:偏宽","","","外观体面度",P,"严重","否"),
 "need thicker. Will order the 2.5": (A,"整体高度:偏矮","计划换档","","",Q,"轻度","是"),
 "adhesive gave out the first time I wore them, one pad is gone": (B,"背胶牢固度","","第一次用就出问题","",P,"严重","否"),
 "Listing said low nose bridge should pick 2.5mm. I did. Way too tall, frames float above my eyebrows": (A,"整体高度:偏高; 选档指引",GUIDE,"","外观体面度",L,"中度","否"),
 "even the thin one raises the glasses too much for me": (A,"整体高度:偏高","","","",Q,"中度","否"),
 "thought these were screw in replacement nose pads. These are just stickers": (E,"贴片式形态(这一款特有); 与预期(泛指)","","","",X,"中度","否"),
 "I have the large frame and bought standard. My mistake, reordering the large version": (C,"机型适配","已换档复购","","",U,"轻度","是"),
 "1.8mm barely makes a difference, glasses still rest on my cheeks": (A,"整体高度:偏矮","","","",Q,"中度","否"),
 "wrong model for my glasses, ordered the other one": (C,"机型适配","已换档复购","","",Q,"轻度","是"),
 "fits in the case but does not charge, the contacts don't touch": (C,"装上后充电","","放回充电盒时","",P,"中度","否"),
 "Does not raise the glasses enough. Still sliding by lunch": (A,"整体高度:偏矮; 防滑效果(泛指)","","全天佩戴","",P,"中度","否"),
 "rough edge on one pad, scratches my skin": (D,"边缘做工","","","佩戴舒适度",P,"中度","否"),
 "Hält nicht, der Kleber löst sich nach zwei Tagen": (B,"背胶牢固度","","","",P,"中度","否"),
 "with pads on, glasses won't seat in the charging case": (C,"充电盒收纳","","放回充电盒时","",P,"中度","否"),
 "slides": (B,"防滑效果(泛指)","","","",P,"严重","否"),
 "I wanted something to stop the arms slipping behind my ears. This only does the nose": (E,"与预期(泛指)","","","",X,"中度","否"),
 "I picked the thin one, my fault, exchanging for the thicker set": (A,"整体高度:偏矮","计划换档","","",U,"轻度","是"),
 "Too wide. Had to trim with scissors which defeats the purpose": (A,"宽度与覆盖:偏宽","","","",P,"中度","否"),
 "ordered 2.5 by mistake, will replace with 1.8": (A,"合适度(没说方向)","计划换档","","",U,"轻度","是"),
 "missing the alcohol wipe and the placement guide shown in the photos": (F,"发货准确","","","收货第一印象",L,"中度","否"),
 "case will not close with these installed": (C,"充电盒收纳","","放回充电盒时","",P,"中度","否"),
 "expected a full nose bridge replacement, not stick on pads": (E,"贴片式形态(这一款特有); 与预期(泛指)","","","",X,"中度","否"),
 "ordered the large frame version, package label says standard": (F,"发货准确","","","",O,"中度","否"),
 "Passt nicht ins Ladeetui, zu gro?? f??r das Etui": (C,"充电盒收纳","","放回充电盒时","",P,"中度","否"),
 "not what I expected": (E,"与预期(泛指)","","","",Q,"轻度","否"),
 "Wider than the built in pad. Looks like I taped something to my glasses": (A,"宽度与覆盖:偏宽","原装鼻托","","外观体面度",P,"中度","否"),
 "only the 1.8 fits the case. The 2.5 doesn't. Nowhere on the page does it say that": (C,"充电盒收纳; 兼容宣称兑现度","","放回充电盒时","",L,"中度","否"),
 "too thin to help, frame still touches my cheeks when I smile": (A,"整体高度:偏矮","","","",Q,"中度","否"),
 "overhangs the nose pad on both sides, you can see it from the front": (A,"宽度与覆盖:偏宽","","","外观体面度",P,"中度","否"),
 "left sticky residue on my 300 dollar glasses when I peeled it off. Not happy": (B,"撕下后留胶","","","",P,"严重","否"),
 "Fell off on day one and my glasses hit the pavement. Lens is scratched. Ridiculous!": (B,"背胶牢固度","","第一次用就出问题","",P,"严重","否"),
 "needs to be thicker, glasses slip when I look down": (A,"整体高度:偏矮; 防滑效果(泛指)","","","",Q,"中度","否"),
 "photo shows glasses in the case with pads on. Mine do not fit in the case at all": (C,"充电盒收纳; 兼容宣称兑现度","","放回充电盒时","",L,"中度","否"),
 "the pads are too wide, they catch dust on the exposed sticky edge": (A,"宽度与覆盖:偏宽","","","",P,"中度","否"),
 "pads bigger than the nose rest so the glue edge shows": (A,"宽度与覆盖:偏宽","","","外观体面度",P,"中度","否"),
 "bought for my dad, he says it feels weird and refuses to wear them": (E,"与预期(泛指)","代买(父母)","","使用者拒绝佩戴; 佩戴舒适度",Q,"中度","否"),
 "too tall, pushes lenses away from my eyes": (A,"整体高度:偏高","","","",Q,"中度","否"),
 "My bad, should have gotten the 1.8. Already reordered the thinner ones and they are fine": (A,"整体高度:偏高","已换档复购","","",U,"轻度","是"),
 "pictured crystal clear, arrived cloudy white. Very visible on black frames": (D,"颜色与图片一致","","","外观体面度",L,"中度","否"),
 "lifts the frame so much the camera now points at the ceiling": (A,"整体高度:偏高; 摄像头视角","","","",P,"中度","否"),
 "still slips down my nose in hot weather": (B,"出汗时防滑","","","",P,"严重","否"),
 "still slides down, not thick enough": (B,"防滑效果(泛指); 整体高度:偏矮","","","",P,"中度","否"),
 "ordered twice by accident": (F,"重复下单","","重复下单","",U,"轻度","否"),
 "gift for my husband, he has the large frames so these don't fit. Getting the right ones": (C,"机型适配","代买(伴侣); 计划换档","","",U,"轻度","是"),
 "cheap": (E,"质量(泛指)","","","",Q,"中度","否"),
 "case": (C,"充电盒相关(没说清)","","","",Q,"轻度","否"),
 "silicone is hard, leaves red marks on my nose after an hour": (D,"硅胶软硬:偏硬","","","佩戴舒适度",P,"中度","否"),
 "much stiffer than I expected, not soft at all": (D,"硅胶软硬:偏硬","","","",Q,"中度","否"),
 "have to press the glasses down hard to get the charge light on": (C,"装上后充电","","放回充电盒时","",P,"中度","否"),
 "Too thick. Went by the chart for low bridge. Glasses look like they are hovering": (A,"整体高度:偏高; 选档指引",GUIDE,"","外观体面度",L,"中度","否"),
 "received 2.5 but I ordered 1.8, bag was mislabeled": (F,"发货准确","","","",O,"中度","否"),
 "pad came off inside the charging case and now it is stuck in there": (B,"背胶牢固度","","放回充电盒时","",P,"严重","否"),
 "width is off, hangs over the edge": (A,"宽度与覆盖:偏宽","","","",P,"中度","否"),
 "turned yellow within two weeks": (D,"耐黄变","","","",P,"中度","否"),
 "doesn't fit": (A,"合适度(没说方向)","","","",Q,"轻度","否"),
 "too squishy, compresses flat so no lift left": (D,"硅胶软硬:偏软; 整体高度:偏矮","","","",P,"中度","否"),
 "says stays on for months, mine lasted two days": (B,"背胶牢固度; 防滑宣称兑现度","","","",L,"严重","否"),
 "too low, no real lift": (A,"整体高度:偏矮","","","",Q,"中度","否"),
 "too thick for my nose, glasses ride up high": (A,"整体高度:偏高","","","",Q,"中度","否"),
 "sits too tall, bottom of the lens is above my eye line": (A,"整体高度:偏高","","","",Q,"中度","否"),
 "The page told me to go 2.5 for a low bridge. Too much lift": (A,"整体高度:偏高; 选档指引",GUIDE,"","",L,"中度","否"),
 "2.5 was too much, swapping for the 1.8": (A,"整体高度:偏高","计划换档","","",Q,"轻度","是"),
 "not enough lift, lashes still hit the lens": (A,"整体高度:偏矮","","","",Q,"中度","否"),
 "thinner than I hoped, no change in how the glasses sit": (A,"整体高度:偏矮","","","",Q,"中度","否"),
 "too thin": (A,"整体高度:偏矮","","","",Q,"轻度","否"),
 "should have ordered the thicker ones, that is on me. Reordered": (A,"整体高度:偏矮","已换档复购","","",U,"轻度","是"),
}

COLS = ["哪件事_大类", "哪件事_细项", "谁在说", "什么情况下", "过程感受", "该谁改", "多严重", "能否挽回"]

def main():
    src, out = sys.argv[1], sys.argv[2]
    d = pd.read_csv(src, dtype=str).fillna("")
    miss = [v for v in d["原话"] if v not in T]
    if miss:
        sys.exit("这些原话还没读过、没有打标：\n" + "\n".join(miss))
    for i, c in enumerate(COLS):
        d[c] = d["原话"].map(lambda v: T[v][i])
    d.to_csv(out, index=False, encoding="utf-8-sig")
    print(f"写出 {out} · {len(d)} 条")

if __name__ == "__main__":
    main()
