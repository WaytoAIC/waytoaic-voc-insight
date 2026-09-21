# 示例数据 · AI 眼镜配件（防滑鼻托）

**全部是编的。** 不对应任何真实订单、真实客户、真实品牌。

形状（比例和坑）照一份真实退货数据来，句子全部重写：大部分人只选了原因码没写字；原话是三段拼出来的；
有几条只有下拉选项；"与描述不符""不兼容"两个大筐里装着好几种不同的事；表里混着换货记录；
时间是一位数月日的写法；有一条德语原话在导出时被弄坏了。

| 文件 | 是什么 |
|---|---|
| `make_returns.py` | 生成 `退货原始导出-示例.csv`（固定随机种子，重跑结果一样） |
| `退货原始导出-示例.csv` | 371 行：357 笔退货 + 14 笔换货 |
| `这一款的特点.json` | 人填的那张表：这一款长什么样、给谁用、为什么这么设计、可能带来什么问题 |
| `tag_returns.py` | 94 条原话逐条读完之后的打标记录（不是规则引擎） |
| `insights-退货.json` | AI 写的叙述部分：论点、因果、三层洞察、行动清单 |
| `成品-退货/` | 跑出来的东西：打标结果、数据体检、网页报告、Excel、给飞书用的两张表 |
| `make_reviews.py` | 生成 `评论原始导出-示例.csv`：97 条评论，含 5 条送测、4 条疑似刷的、1 条 5 星配差评正文；5 月以后背胶的抱怨变多 |
| `tag_reviews.py` | 92 条评论逐条读完之后的打标记录 |
| `insights-评论.json` | 评论线的叙述部分 |
| `成品-评论/` | 评论线跑出来的东西 |
| `make_reddit.py` | 生成 `Reddit原始导出-示例.csv`：49 条讨论，3 个群组（群组名、帖子、作者全是编的）；有没买在问的、在挑的、买了的、放弃的；有一个人反复发的、有广告和跑题的 |
| `tag_reddit.py` | 47 条讨论逐条读完之后的打标记录（先分流，再各用各的方法） |
| `insights-Reddit.json` | Reddit 线的叙述部分 |
| `成品-Reddit/` | Reddit 线跑出来的东西（进阶版） |

两条线埋的是同一个故事，可以叠着看：宽度在退货里 9 比 0、在评论里 12 比 0；「同一个链接两批不一样」在退货里只有 1 条，
到评论里多了 3 位回头客和一个 5 月的拐点；被页面选档建议坑到的人，退货里 6 条，评论里只有 1 条（不满意的人多数不写评论，直接退了）。

从头重跑退货线（在 `skill/scripts/` 下；评论线把 `return` 换成 `review`、文件名换成评论那一套即可）：

```bash
python3 prep_return.py "../../samples/AI眼镜配件/退货原始导出-示例.csv" --config "../品类配置/示例-AI眼镜配件.json" \
  --product "A款-防滑鼻托套装(2对装)" --out ../../work/returns/cleaned.csv --report ../../work/returns/prep.json
python3 "../../samples/AI眼镜配件/tag_returns.py" ../../work/returns/cleaned.csv ../../work/returns/tagged.csv
python3 build_return.py ../../work/returns/tagged.csv "../../samples/AI眼镜配件/insights-退货.json" \
  --config "../品类配置/示例-AI眼镜配件.json" --prep ../../work/returns/prep.json \
  --sku "../../samples/AI眼镜配件/这一款的特点.json" --outdir ../../work/returns/out --sample
python3 export_tables.py ../../work/returns/tagged.csv "../../samples/AI眼镜配件/insights-退货.json" --source 退货 --outdir ../../work/returns/out/两张表
```
