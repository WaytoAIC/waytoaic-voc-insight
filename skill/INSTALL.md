# 安装

这个包遵循开放的 Agent Skills 约定（SKILL.md + scripts/ + references/ + assets/），支持这个约定的 agent 都能用。

| Agent | 放哪 |
|---|---|
| Claude Code | 项目级 `.claude/skills/voc-insight/`，或用户级 `~/.claude/skills/voc-insight/` |
| Claude 桌面 / 网页 | 打成 `.skill`（就是 zip）上传 |
| Codex | `.codex/skills/voc-insight/` 或 `~/.codex/skills/voc-insight/` |

放好后重开一次会话。

```bash
pip install -r requirements.txt        # pandas / openpyxl / numpy
```

`recalc.py` 可选用 LibreOffice 预先算好 Excel 里的公式。没有也能跑完，只是统计页在轻量预览器里显示为空；用 Excel、WPS、Google Sheets 打开会自动算出来。

## 第一次用，先跑一遍示例

`samples/AI眼镜配件/README.md` 里有从头到尾的命令。示例数据全是编的。

## 换成你自己的品类

1. 复制 `品类配置/示例-AI眼镜配件.json`，改成你的品类（`references/01`）
2. 标签表不要照抄示例的，照 `references/03` 的六步自己做
3. 每分析一款，先让人填一份"这一款的特点"
