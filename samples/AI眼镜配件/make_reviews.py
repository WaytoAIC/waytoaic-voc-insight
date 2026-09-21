#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生成「示例数据 · 评论」。全部是编的，不对应任何真实买家。

形状照真实评论数据来：
  · 好评居多，差评是尾巴；一条里又夸又骂的很常见
  · 有 5 星配差评正文的
  · 有几条送测评论（Vine），写得又长又满
  · 有一小撮同一天、同一规格、5 星、写得特别长的，疑似刷的
  · 时间是一位数月日的写法
  · 5 月以后关于背胶的抱怨变多（对应退货那边「同款两批不一样」的那条线索）
"""
import csv, os
HERE = os.path.dirname(os.path.abspath(__file__))
PRODUCT, NAME = "A款-防滑鼻托套装(2对装)", "智能眼镜 硅胶防滑鼻托 背胶款 2对装"
S18, S25, L18, L25 = "标准款-1.8mm", "标准款-2.5mm", "大号款-1.8mm", "大号款-2.5mm"

# (日期, 星级, 规格, 站点, 是否送测, 评论全文)
R = [
 # ---------- 1 月 ----------
 ("2026/1/4",5,S18,"US",0,"My glasses used to slide down every time I looked at my phone. With these on they stay put all day. Super comfortable too, I forget they are there."),
 ("2026/1/6",5,S25,"US",0,"Low nose bridge here. The 2.5 lifts the frames off my cheeks finally. Easy to put on, took two minutes."),
 ("2026/1/7",4,S18,"US",0,"Works well for stopping the slide. Only complaint is they are a bit wider than the original pads so you can see the edge if you look closely."),
 ("2026/1/9",5,L18,"US",0,"Perfect. No more pushing my glasses up every five minutes. Still fits in the charging case with the 1.8."),
 ("2026/1/11",5,S18,"US",0,"I was using folded tissue under the nose pads before, this is so much better. Soft and comfy."),
 ("2026/1/12",3,S25,"US",0,"Comfortable and they do stop the slipping, but with the 2.5 my glasses no longer fit in the charging case. Wish the listing had said so."),
 ("2026/1/15",5,L18,"US",0,"Bought these for my husband, he wears his glasses all day and says they are way more comfortable now. He stopped complaining about them sliding."),
 ("2026/1/17",4,S25,"US",0,"Good grip, stays on even at the gym. A little tall for my taste but I got used to it."),
 ("2026/1/19",5,S18,"US",0,"Tried another brand before and those fell off in a week. These have been on for a month, still solid."),
 ("2026/1/21",2,S25,"US",0,"They stop the sliding but the camera now points up, all my videos are aimed at the sky. Also does not fit the case."),
 ("2026/1/23",5,L25,"US",0,"Game changer for a flat nose. Glasses sit where they should. Install was simple with the little guide."),
 ("2026/1/25",5,S18,"US",0,"So comfortable. No red marks on my nose anymore."),
 ("2026/1/27",4,S18,"US",0,"Does the job. Pricey for four bits of silicone but it fixed my problem."),
 ("2026/1/30",5,L18,"US",0,"Second set I have bought, one for each pair of glasses. They just work."),
 # 送测评论
 ("2026/1/8",5,S18,"US",1,"I received this product to test and I have to say the quality is outstanding. The silicone is soft, the adhesive is strong, the fit is perfect and the packaging is premium. Highly recommended to anyone with smart glasses."),
 ("2026/1/14",5,S25,"US",1,"As a reviewer I test many accessories and this one stands out. Thoughtful design, excellent materials, flawless performance in every situation I tried. Five stars without hesitation."),
 ("2026/1/22",5,L18,"US",1,"Received for review. Beautiful packaging, clear instructions, pads feel luxurious and do exactly what the listing promises. I cannot find a single fault with this product."),
 ("2026/2/3",5,S18,"US",1,"Provided to me for an honest review. Honestly it is perfect: comfortable, invisible, strong adhesive, fits every frame. Everyone with smart glasses should own a set."),
 ("2026/2/9",4,L25,"US",1,"Got these through the review program. Well made and easy to install. Did everything I expected. Would recommend to friends and family."),
 # ---------- 2 月 ----------
 ("2026/2/2",5,S25,"US",0,"Finally my glasses do not rest on my cheeks. The 2.5 is the right call for low bridges."),
 ("2026/2/4",5,S18,"US",0,"Invisible once on. Nobody noticed. Glasses stay up when I look down."),
 ("2026/2/6",4,S18,"US",0,"Great comfort, holds well. They are slightly wider than the stock pads, which bugs me a little."),
 ("2026/2/8",1,S25,"US",0,"Way too thick. The listing told me to choose 2.5 for a low bridge and now my glasses float above my eyebrows. Returned."),
 ("2026/2/10",5,L18,"US",0,"Fits my large frames perfectly and still charges in the case. Very happy."),
 ("2026/2/12",5,S25,"US",0,"Comfortable but the glasses will not close in the charging case with these on. I take them off every night which defeats the purpose."),
 ("2026/2/16",5,S18,"US",0,"Was using a band aid on the bridge before, embarrassing. These look clean and work."),
 ("2026/2/18",5,S18,"US",0,"No slipping during my runs. Adhesive held through sweat so far."),
 ("2026/2/20",4,L25,"US",0,"Good product. Height is perfect for me. Wish they were a touch narrower."),
 ("2026/2/22",5,S18,"US",0,"Easy install, comfortable, glasses stay put. What else do you need."),
 ("2026/2/24",2,S18,"US",0,"Not enough lift for me, glasses still slide. Probably should have gone thicker."),
 ("2026/2/26",5,S25,"US",0,"My dad loves them. He kept pushing his glasses up, now he doesn't."),
 ("2026/2/27",4,S18,"US",0,"Works. A bit expensive."),
 # 同一天、同一规格、5 星、特别长 —— 疑似刷的
 ("2026/2/14",5,S18,"US",0,"These nose pads are absolutely amazing and I cannot recommend them enough to everyone who owns smart glasses. The material feels premium and soft, the adhesive is incredibly strong, the height is just perfect for every nose shape, and they look completely invisible. Best purchase I have made this year without any doubt whatsoever."),
 ("2026/2/14",5,S18,"US",0,"Wonderful product from a wonderful seller, I am so impressed with everything about it from the packaging to the performance. My glasses never slide anymore, the comfort is unbelievable, the quality is top notch and the price is very fair for what you get. I will be buying more sets for my whole family very soon."),
 ("2026/2/14",5,S18,"US",0,"I have tried many different nose pads for my smart glasses and nothing comes close to this set, it is simply the best on the market today. Perfect fit, perfect comfort, perfect adhesive, perfect look, there is honestly nothing I would change about it. Do yourself a favor and order these right now, you will thank me later."),
 ("2026/2/14",5,S18,"US",0,"Outstanding quality and outstanding value, this product exceeded every expectation I had and then some. Installation was effortless, the pads are soft and durable, they stay on through everything and they make my glasses feel like they were custom made for my face. Ten out of ten, a must have accessory for all smart glasses owners."),
 # ---------- 3 月 ----------
 ("2026/3/1",5,S18,"US",0,"Stay put all day at work. I wear a headset too and they do not shift."),
 ("2026/3/3",4,S25,"US",0,"Height is great, comfort is great. They stick out past the nose pad a bit, visible from the front in bright light."),
 ("2026/3/5",5,L18,"US",0,"Comfortable and they fit my large frames. Charging case closes fine."),
 ("2026/3/8",2,S25,"US",0,"Does not fit in the charging case. Had to choose between charging my glasses and wearing the pads."),
 ("2026/3/10",5,S18,"US",0,"Simple fix for a real problem. No more sliding when I cook or look down."),
 ("2026/3/12",3,L25,"US",0,"Stops the slide. But the pads are wider than the frame pad and it looks like I stuck tape on my glasses. Function over form I guess."),
 ("2026/3/15",5,S18,"US",0,"Soft, clear, and comfy. Took them off once to reposition and they came off clean, no residue."),
 ("2026/3/18",5,S25,"US",0,"I have a very flat bridge and these are the first thing that worked. Love them."),
 ("2026/3/20",1,S25,"US",0,"5 stars for the idea, 1 star for reality. With pads on the glasses do not charge in the case. Nowhere does the page warn you."),
 ("2026/3/23",4,S18,"US",0,"Good. Would be five stars if they matched the width of the original pads."),
 ("2026/3/26",5,S18,"US",0,"Put them on in a minute. Comfortable right away."),
 ("2026/3/29",5,L18,"US",0,"Glasses no longer slip when I sweat. Still going strong after six weeks."),
 # ---------- 4 月 ----------
 ("2026/4/2",5,S18,"US",0,"Exactly what I needed. Comfortable and the glasses stay in place."),
 ("2026/4/4",3,S25,"US",0,"They work for slipping. Too tall for me though, and they change the camera angle. Going to try the 1.8."),
 ("2026/4/7",5,S25,"US",0,"Flat nose problem solved. Worth every penny."),
 ("2026/4/9",4,S18,"US",0,"Comfy and secure. Slight yellow tint after a couple of months but still fine."),
 ("2026/4/12",2,L25,"US",0,"Glasses won't fit the case with the 2.5 pads. The photos show them in the case so I assumed it would work."),
 ("2026/4/15",5,S18,"US",0,"My wife bought these for me. I did not think I needed them. I was wrong, big difference in comfort."),
 ("2026/4/18",5,L18,"US",0,"Works with the large frame and case. No issues."),
 ("2026/4/20",4,S18,"US",0,"Stops slipping. Can see the edges of the pad from the side, they are wider than they need to be."),
 ("2026/4/23",1,S18,"US",0,"One pad fell off after three days and I lost it. Not what I expected for the price."),
 ("2026/4/26",5,S18,"US",0,"Great little upgrade. Easy to apply and totally comfortable."),
 ("2026/4/29",5,S25,"US",0,"Perfect height for me and they have stayed on through daily wear for two months."),
 # ---------- 5 月 ----------
 ("2026/5/2",5,S18,"US",0,"No more sliding. Comfortable all day."),
 ("2026/5/5",2,S18,"US",0,"First set I bought in February was great. This new set feels harder and the glue gave up in a week."),
 ("2026/5/8",3,S25,"US",0,"Comfortable, but one pad came loose after a sweaty bike ride. Pressed it back on, we will see."),
 ("2026/5/10",4,L18,"US",0,"Good fit and they work with the case. A bit wide."),
 ("2026/5/13",1,S25,"US",0,"Pad fell off on the second day while I was walking, glasses dropped and the lens got scratched. Furious."),
 ("2026/5/16",5,S18,"US",0,"Love these. Look invisible and feel great."),
 ("2026/5/19",2,S25,"US",0,"Adhesive does not survive sweat. Listing says sweat proof. It is not."),
 ("2026/5/22",4,S18,"US",0,"They do help a lot with slipping. Not cheap for what it is."),
 ("2026/5/25",3,S25,"US",0,"Nice and soft but the 2.5 will not go in the charging case. 1.8 does according to other reviews, wish I knew before."),
 ("2026/5/28",5,L25,"US",0,"Great for my low bridge. Husband noticed I stopped fiddling with my glasses."),
 ("2026/5/30",2,S18,"US",0,"Came off after a week. Left some sticky stuff on the frame too."),
 # ---------- 6 月 ----------
 ("2026/6/2",4,S18,"US",0,"Comfortable and they hold my glasses up. Edges are visible because the pad is wider than the original."),
 ("2026/6/5",1,S18,"US",0,"Lasted four days. The glue is weak, pad slid off in the heat."),
 ("2026/6/8",5,S25,"US",0,"Still the best fix for a flat nose bridge. On my second set."),
 ("2026/6/11",2,S25,"US",0,"Does not fit the case and the adhesive is already peeling at one corner after a week."),
 ("2026/6/14",5,L18,"US",0,"Comfortable, invisible, stays put. Happy."),
 ("2026/6/17",3,S18,"US",0,"It helps with sliding, comfort is good. But mine turned yellowish within a month which looks bad on black frames."),
 ("2026/6/20",1,S25,"US",0,"Fell off inside the charging case and jammed it. Had to fish it out with tweezers."),
 ("2026/6/23",4,S18,"US",0,"Works as described. Wider than needed."),
 ("2026/6/26",5,S18,"US",0,"Comfy and secure for my daily commute."),
 ("2026/6/29",2,L25,"US",0,"Not impressed. Peeled off when I cleaned my glasses. Will not reorder."),
 # ---------- 7 月 ----------
 ("2026/7/2",5,S18,"US",0,"Great comfort, no slipping at my desk all day."),
 ("2026/7/6",1,S25,"US",0,"Sweat proof? No. Gone after one workout. Do not believe the listing."),
 ("2026/7/9",4,L18,"US",0,"Fits large frames, fits the case. Could be narrower."),
 ("2026/7/13",2,S18,"US",0,"The pads are fine when they stay on. Mine lasted about a week each. Out of spares already."),
 ("2026/7/16",5,S25,"US",0,"Perfect lift for my nose, glasses finally sit level."),
 ("2026/7/19",3,S18,"US",0,"Comfortable. Adhesive is hit or miss, one side is solid and the other keeps lifting."),
 ("2026/7/23",1,S25,"US",0,"Too tall, does not fit case, and fell off in a week. Three strikes."),
 ("2026/7/27",2,S18,"US",0,"Used to love these, this is my third order. The latest ones are stiffer and do not stick like before."),
 ("2026/7/30",4,S18,"US",0,"Good product overall. Slightly visible from the front."),
 # ---------- 8 月 ----------
 ("2026/8/2",1,S18,"US",0,"Fell off day one. Waste of money."),
 ("2026/8/5",5,L18,"US",0,"Works great with my large frames and the case. Very comfortable."),
 ("2026/8/8",2,S25,"US",0,"Comfortable while it lasted. Came off in the heat after five days and the 2.5 never fit the case anyway."),
 ("2026/8/11",3,S18,"US",0,"They help. The glue could be stronger and the pad could be narrower."),
 ("2026/8/14",4,S25,"US",0,"Height is right for me. Holding so far after two weeks."),
 ("2026/8/18",1,L25,"US",0,"Peeled off within days, twice. Something changed, my set from last winter lasted months."),
 ("2026/8/22",5,S18,"US",0,"Comfortable and they keep my glasses from sliding during yoga."),
 ("2026/8/26",2,S18,"US",0,"Adhesive failed in a week. Disappointed."),
]

out = os.path.join(HERE, "评论原始导出-示例.csv")
with open(out, "w", newline="", encoding="utf-8-sig") as f:
    w = csv.writer(f)
    w.writerow(["评论ID", "Vine", "评论全文", "星级", "站点", "产品", "品名", "规格", "发生时间"])
    for i, (date, star, spec, site, vine, text) in enumerate(R, 1):
        w.writerow([f"SAMPLE-RV-{i:04d}", "TRUE" if vine else "FALSE", text, star, site, PRODUCT, NAME, spec,
                    f"{date} {8 + i % 12}:{(i * 7) % 60:02d}"])
assert len({r[5] for r in R}) == len(R), "评论全文有重复"
print("写出", out, "共", len(R), "条；其中送测", sum(r[4] for r in R))
