#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
示例数据 · 评论线的打标结果。

这不是规则引擎。下面每一行是 AI 把那条评论读完之后逐条写下的判断，按评论全文对应回去。
真跑的时候这一步由 agent 直接产出 tagged.csv，不需要这个文件。

每条十格：
  谁在说 | 什么情况下 | 好评的事 | 差评的事 | 落差指向 | 过程感受 | 再问一层 | 该谁改 | 多严重 | 整体好坏
规矩：一条里又夸又骂的，两边都记；好坏以文字为准，不跟星级走；
      「该谁改」「多严重」只在有差评的事时才填；没内容的格子留空。
"""
import sys
import pandas as pd

P, L, U, Q = "产品的事", "页面的事", "客户自己选错", "说不清"
G, M, B = "好评", "中性", "差评"
W = "宽度与覆盖:偏宽"
def glue(when="没说", where="没说"):
    return f"背胶牢固度>多久出的问题={when}; 背胶牢固度>什么场合={where}"
CASE_NO = "充电盒收纳>怎么个不行=放不进去或合不上盖"
def slip(where): return f"防滑效果(泛指)>什么场合={where}"

T = {
 "My glasses used to slide down every time I looked at my phone. With these on they stay put all day. Super comfortable too, I forget they are there.": ("","全天佩戴","防滑效果(泛指); 佩戴舒适","","","",slip("低头"),"","",G),
 "Low nose bridge here. The 2.5 lifts the frames off my cheeks finally. Easy to put on, took two minutes.": ("","","整体高度; 安装难易","","","","","","",G),
 "Works well for stopping the slide. Only complaint is they are a bit wider than the original pads so you can see the edge if you look closely.": ("原装鼻托","","防滑效果(泛指)",W+"; 外观隐形","","","",P,"轻度",G),
 "Perfect. No more pushing my glasses up every five minutes. Still fits in the charging case with the 1.8.": ("","放回充电盒时","防滑效果(泛指); 充电盒收纳","","","","","","",G),
 "I was using folded tissue under the nose pads before, this is so much better. Soft and comfy.": ("自己垫东西","","佩戴舒适; 硅胶软硬","","","","","","",G),
 "Comfortable and they do stop the slipping, but with the 2.5 my glasses no longer fit in the charging case. Wish the listing had said so.": ("","放回充电盒时","佩戴舒适; 防滑效果(泛指)","充电盒收纳","充电盒收纳","",CASE_NO,L,"中度",M),
 "Bought these for my husband, he wears his glasses all day and says they are way more comfortable now. He stopped complaining about them sliding.": ("代买(伴侣)","全天佩戴","佩戴舒适; 防滑效果(泛指)","","","","","","",G),
 "Good grip, stays on even at the gym. A little tall for my taste but I got used to it.": ("","运动出汗","防滑效果(泛指); 出汗时防滑","整体高度:偏高","","",slip("运动"),Q,"轻度",G),
 "Tried another brand before and those fell off in a week. These have been on for a month, still solid.": ("其他品牌鼻托","","背胶牢固度","","","安心感(夸)","","","",G),
 "They stop the sliding but the camera now points up, all my videos are aimed at the sky. Also does not fit the case.": ("","","防滑效果(泛指)","摄像头视角; 充电盒收纳","","",CASE_NO,P,"中度",B),
 "Game changer for a flat nose. Glasses sit where they should. Install was simple with the little guide.": ("","","整体高度; 安装难易","","","","","","",G),
 "So comfortable. No red marks on my nose anymore.": ("","","佩戴舒适","","","","","","",G),
 "Does the job. Pricey for four bits of silicone but it fixed my problem.": ("","","质量(泛指)","值不值","","","",Q,"轻度",G),
 "Second set I have bought, one for each pair of glasses. They just work.": ("复购","","质量(泛指)","","","","","","",G),
 "Finally my glasses do not rest on my cheeks. The 2.5 is the right call for low bridges.": ("","","整体高度","","","","","","",G),
 "Invisible once on. Nobody noticed. Glasses stay up when I look down.": ("","","外观隐形; 防滑效果(泛指)","","","外观体面度(夸)",slip("低头"),"","",G),
 "Great comfort, holds well. They are slightly wider than the stock pads, which bugs me a little.": ("原装鼻托","","佩戴舒适; 防滑效果(泛指)",W,"","","",P,"轻度",G),
 "Way too thick. The listing told me to choose 2.5 for a low bridge and now my glasses float above my eyebrows. Returned.": ("照页面指引选的","","","整体高度:偏高; 选档指引","选档指引","外观体面度","",L,"中度",B),
 "Fits my large frames perfectly and still charges in the case. Very happy.": ("","放回充电盒时","机型适配; 装上后充电; 充电盒收纳","","","","","","",G),
 "Comfortable but the glasses will not close in the charging case with these on. I take them off every night which defeats the purpose.": ("","放回充电盒时","佩戴舒适","充电盒收纳","","",CASE_NO,P,"中度",B),
 "Was using a band aid on the bridge before, embarrassing. These look clean and work.": ("自己垫东西","","外观隐形; 防滑效果(泛指)","","","外观体面度(夸)","","","",G),
 "No slipping during my runs. Adhesive held through sweat so far.": ("","运动出汗","出汗时防滑; 背胶牢固度","","","",slip("运动"),"","",G),
 "Good product. Height is perfect for me. Wish they were a touch narrower.": ("","","整体高度",W,"","","",P,"轻度",G),
 "Easy install, comfortable, glasses stay put. What else do you need.": ("","","安装难易; 佩戴舒适; 防滑效果(泛指)","","","","","","",G),
 "Not enough lift for me, glasses still slide. Probably should have gone thicker.": ("","","","整体高度:偏矮; 防滑效果(泛指)","","",slip("没说"),U,"轻度",B),
 "My dad loves them. He kept pushing his glasses up, now he doesn't.": ("代买(父母)","","防滑效果(泛指)","","","","","","",G),
 "Works. A bit expensive.": ("","","质量(泛指)","值不值","","","",Q,"轻度",M),
 "These nose pads are absolutely amazing and I cannot recommend them enough to everyone who owns smart glasses. The material feels premium and soft, the adhesive is incredibly strong, the height is just perfect for every nose shape, and they look completely invisible. Best purchase I have made this year without any doubt whatsoever.": ("","","硅胶软硬; 背胶牢固度; 整体高度; 外观隐形","","","","","","",G),
 "Wonderful product from a wonderful seller, I am so impressed with everything about it from the packaging to the performance. My glasses never slide anymore, the comfort is unbelievable, the quality is top notch and the price is very fair for what you get. I will be buying more sets for my whole family very soon.": ("","","防滑效果(泛指); 佩戴舒适; 质量(泛指); 值不值","","","收货第一印象(夸)","","","",G),
 "I have tried many different nose pads for my smart glasses and nothing comes close to this set, it is simply the best on the market today. Perfect fit, perfect comfort, perfect adhesive, perfect look, there is honestly nothing I would change about it. Do yourself a favor and order these right now, you will thank me later.": ("其他品牌鼻托","","佩戴舒适; 背胶牢固度; 外观隐形; 质量(泛指)","","","","","","",G),
 "Outstanding quality and outstanding value, this product exceeded every expectation I had and then some. Installation was effortless, the pads are soft and durable, they stay on through everything and they make my glasses feel like they were custom made for my face. Ten out of ten, a must have accessory for all smart glasses owners.": ("","","安装难易; 硅胶软硬; 背胶牢固度; 值不值","","","","","","",G),
 "Stay put all day at work. I wear a headset too and they do not shift.": ("","全天佩戴","防滑效果(泛指)","","","","","","",G),
 "Height is great, comfort is great. They stick out past the nose pad a bit, visible from the front in bright light.": ("","","整体高度; 佩戴舒适",W+"; 外观隐形","","","",P,"轻度",G),
 "Comfortable and they fit my large frames. Charging case closes fine.": ("","放回充电盒时","佩戴舒适; 机型适配; 充电盒收纳","","","","","","",G),
 "Does not fit in the charging case. Had to choose between charging my glasses and wearing the pads.": ("","放回充电盒时","","充电盒收纳","","",CASE_NO,P,"中度",B),
 "Simple fix for a real problem. No more sliding when I cook or look down.": ("","","防滑效果(泛指)","","","",slip("低头"),"","",G),
 "Stops the slide. But the pads are wider than the frame pad and it looks like I stuck tape on my glasses. Function over form I guess.": ("","","防滑效果(泛指)",W+"; 外观隐形","","外观体面度","",P,"中度",M),
 "Soft, clear, and comfy. Took them off once to reposition and they came off clean, no residue.": ("","","硅胶软硬; 佩戴舒适; 撕下后留胶","","","","","","",G),
 "I have a very flat bridge and these are the first thing that worked. Love them.": ("","","整体高度","","","","","","",G),
 "5 stars for the idea, 1 star for reality. With pads on the glasses do not charge in the case. Nowhere does the page warn you.": ("","放回充电盒时","","装上后充电","装上后充电","","",L,"中度",B),
 "Good. Would be five stars if they matched the width of the original pads.": ("原装鼻托","","质量(泛指)",W,"","","",P,"轻度",G),
 "Put them on in a minute. Comfortable right away.": ("","","安装难易; 佩戴舒适","","","","","","",G),
 "Glasses no longer slip when I sweat. Still going strong after six weeks.": ("","运动出汗","出汗时防滑; 背胶牢固度","","","","","","",G),
 "Exactly what I needed. Comfortable and the glasses stay in place.": ("","","佩戴舒适; 防滑效果(泛指)","","","","","","",G),
 "They work for slipping. Too tall for me though, and they change the camera angle. Going to try the 1.8.": ("计划换档","","防滑效果(泛指)","整体高度:偏高; 摄像头视角","","","",Q,"中度",M),
 "Flat nose problem solved. Worth every penny.": ("","","整体高度; 值不值","","","","","","",G),
 "Comfy and secure. Slight yellow tint after a couple of months but still fine.": ("","","佩戴舒适; 防滑效果(泛指)","耐黄变","","","",P,"轻度",G),
 "Glasses won't fit the case with the 2.5 pads. The photos show them in the case so I assumed it would work.": ("","放回充电盒时","","充电盒收纳","充电盒收纳","",CASE_NO,L,"中度",B),
 "My wife bought these for me. I did not think I needed them. I was wrong, big difference in comfort.": ("送礼","","佩戴舒适","","","","","","",G),
 "Works with the large frame and case. No issues.": ("","放回充电盒时","机型适配; 充电盒收纳","","","","","","",G),
 "Stops slipping. Can see the edges of the pad from the side, they are wider than they need to be.": ("","","防滑效果(泛指)",W+"; 外观隐形","","","",P,"轻度",G),
 "One pad fell off after three days and I lost it. Not what I expected for the price.": ("","","","背胶牢固度; 值不值","","",glue("一周内"),P,"严重",B),
 "Great little upgrade. Easy to apply and totally comfortable.": ("","","安装难易; 佩戴舒适","","","","","","",G),
 "Perfect height for me and they have stayed on through daily wear for two months.": ("","全天佩戴","整体高度; 背胶牢固度","","","","","","",G),
 "No more sliding. Comfortable all day.": ("","全天佩戴","防滑效果(泛指); 佩戴舒适","","","","","","",G),
 "First set I bought in February was great. This new set feels harder and the glue gave up in a week.": ("复购","","","同款批次一致性; 硅胶软硬:偏硬; 背胶牢固度","","",glue("一周内"),P,"严重",B),
 "Comfortable, but one pad came loose after a sweaty bike ride. Pressed it back on, we will see.": ("","运动出汗","佩戴舒适","背胶牢固度","","",glue("没说","出汗"),P,"中度",M),
 "Good fit and they work with the case. A bit wide.": ("","放回充电盒时","充电盒收纳",W,"","","",P,"轻度",G),
 "Pad fell off on the second day while I was walking, glasses dropped and the lens got scratched. Furious.": ("","","","背胶牢固度","","",glue("一周内","日常佩戴"),P,"严重",B),
 "Love these. Look invisible and feel great.": ("","","外观隐形; 佩戴舒适","","","","","","",G),
 "Adhesive does not survive sweat. Listing says sweat proof. It is not.": ("","运动出汗","","背胶牢固度; 防滑宣称兑现度","背胶牢固度","",glue("没说","出汗"),L,"严重",B),
 "They do help a lot with slipping. Not cheap for what it is.": ("","","防滑效果(泛指)","值不值","","","",Q,"轻度",G),
 "Nice and soft but the 2.5 will not go in the charging case. 1.8 does according to other reviews, wish I knew before.": ("","放回充电盒时","硅胶软硬","充电盒收纳","充电盒收纳","",CASE_NO,L,"中度",M),
 "Great for my low bridge. Husband noticed I stopped fiddling with my glasses.": ("","","整体高度; 防滑效果(泛指)","","","","","","",G),
 "Came off after a week. Left some sticky stuff on the frame too.": ("","","","背胶牢固度; 撕下后留胶","","",glue("一周内"),P,"严重",B),
 "Comfortable and they hold my glasses up. Edges are visible because the pad is wider than the original.": ("原装鼻托","","佩戴舒适; 防滑效果(泛指)",W+"; 外观隐形","","","",P,"轻度",G),
 "Lasted four days. The glue is weak, pad slid off in the heat.": ("","","","背胶牢固度","","",glue("一周内","出汗"),P,"严重",B),
 "Still the best fix for a flat nose bridge. On my second set.": ("复购","","整体高度","","","","","","",G),
 "Does not fit the case and the adhesive is already peeling at one corner after a week.": ("","放回充电盒时","","充电盒收纳; 背胶牢固度","","",CASE_NO+"; "+glue("一周内"),P,"中度",B),
 "Comfortable, invisible, stays put. Happy.": ("","","佩戴舒适; 外观隐形; 防滑效果(泛指)","","","","","","",G),
 "It helps with sliding, comfort is good. But mine turned yellowish within a month which looks bad on black frames.": ("","","防滑效果(泛指); 佩戴舒适","耐黄变; 外观隐形","","外观体面度","",P,"中度",M),
 "Fell off inside the charging case and jammed it. Had to fish it out with tweezers.": ("","放回充电盒时","","背胶牢固度","","",glue("没说","放充电盒时"),P,"严重",B),
 "Works as described. Wider than needed.": ("","","质量(泛指)",W,"","","",P,"轻度",G),
 "Comfy and secure for my daily commute.": ("","全天佩戴","佩戴舒适; 防滑效果(泛指)","","","","","","",G),
 "Not impressed. Peeled off when I cleaned my glasses. Will not reorder.": ("彻底放弃","","","背胶牢固度","","",glue("没说","日常佩戴"),P,"严重",B),
 "Great comfort, no slipping at my desk all day.": ("","全天佩戴","佩戴舒适; 防滑效果(泛指)","","","","","","",G),
 "Sweat proof? No. Gone after one workout. Do not believe the listing.": ("","运动出汗","","背胶牢固度; 防滑宣称兑现度","背胶牢固度","",glue("没说","出汗"),L,"严重",B),
 "Fits large frames, fits the case. Could be narrower.": ("","放回充电盒时","机型适配; 充电盒收纳",W,"","","",P,"轻度",G),
 "The pads are fine when they stay on. Mine lasted about a week each. Out of spares already.": ("","","","背胶牢固度","","",glue("一周内"),P,"严重",B),
 "Perfect lift for my nose, glasses finally sit level.": ("","","整体高度","","","","","","",G),
 "Comfortable. Adhesive is hit or miss, one side is solid and the other keeps lifting.": ("","","佩戴舒适","背胶牢固度","","",glue(),P,"中度",M),
 "Too tall, does not fit case, and fell off in a week. Three strikes.": ("","","","整体高度:偏高; 充电盒收纳; 背胶牢固度","","",CASE_NO+"; "+glue("一周内"),P,"严重",B),
 "Used to love these, this is my third order. The latest ones are stiffer and do not stick like before.": ("复购","","","同款批次一致性; 硅胶软硬:偏硬; 背胶牢固度","","",glue(),P,"中度",B),
 "Good product overall. Slightly visible from the front.": ("","","质量(泛指)","外观隐形","","","",P,"轻度",G),
 "Fell off day one. Waste of money.": ("","第一次用就出问题","","背胶牢固度; 值不值","","",glue("第一天"),P,"严重",B),
 "Works great with my large frames and the case. Very comfortable.": ("","放回充电盒时","机型适配; 充电盒收纳; 佩戴舒适","","","","","","",G),
 "Comfortable while it lasted. Came off in the heat after five days and the 2.5 never fit the case anyway.": ("","","佩戴舒适","背胶牢固度; 充电盒收纳","","",glue("一周内","出汗")+"; "+CASE_NO,P,"严重",B),
 "They help. The glue could be stronger and the pad could be narrower.": ("","","防滑效果(泛指)","背胶牢固度; "+W,"","",glue(),P,"中度",M),
 "Height is right for me. Holding so far after two weeks.": ("","","整体高度; 背胶牢固度","","","","","","",G),
 "Peeled off within days, twice. Something changed, my set from last winter lasted months.": ("复购","","","背胶牢固度; 同款批次一致性","","",glue("一周内"),P,"严重",B),
 "Comfortable and they keep my glasses from sliding during yoga.": ("","运动出汗","佩戴舒适; 防滑效果(泛指)","","","",slip("运动"),"","",G),
 "Adhesive failed in a week. Disappointed.": ("","","","背胶牢固度","","",glue("一周内"),P,"严重",B),
}
COLS = ["谁在说", "什么情况下", "好评的事", "差评的事", "落差指向", "过程感受", "再问一层", "该谁改", "多严重", "整体好坏"]

def main():
    src, out = sys.argv[1], sys.argv[2]
    d = pd.read_csv(src, dtype=str).fillna("")
    miss = [v for v in d["原话"] if v not in T]
    if miss:
        sys.exit("这些评论还没读过、没有打标：\n" + "\n".join(miss))
    for i, c in enumerate(COLS):
        d[c] = d["原话"].map(lambda v: T[v][i])
    d.to_csv(out, index=False, encoding="utf-8-sig")
    print(f"写出 {out} · {len(d)} 条")

if __name__ == "__main__":
    main()
