# Research Audit — 沃伦·巴菲特 (celebrity / budget-unfriendly)

## Verdict
- Status: PASS
- Reason: 6 轨道全部覆盖且内容互不克隆；15 个已验证 URL；一手占比 82%；无黑名单信源；6 个实质矛盾；21 个候选心智模型（≥3）；known-answer 银行 3 问；edge-case 1 问；长文主导、品味原则合规。

## Coverage Review
- Track coverage: 6/6 维度覆盖
- Missing or weak tracks: Track 2（对话）最薄——语料以书面信函为主，即兴问答缺失，已在笔记中诚实标注并给出补强方案（股东会视频转写），不影响合成
- Cross-track redundancy: 各轨道内容互不克隆（01=心智模型体系、02=压力对话、03=语言指纹、04=决策案例、05=他者视角、06=演化时间线），交叉引用而非复制

## Source Quality Assessment

### Source Mix
- Primary-source count: 16 处一手标记（81 封原信 + 芒格 2014 亲笔 + 概念/公司回溯整理）
- Secondary-source count: 3（Forbes、Business Insider ×2，均为已 curl 验证 HTTP 200 的具体文章页）
- Primary-source ratio: 82%（目标 >50%，达标）
- Grounding quality: 本地 60+ 个伯克希尔官网逐年链接 + chian.io 合伙信链接（均为信件具体页）；3 个外部 URL 为具体文章页（非首页/搜索页/话题页）

### Source Hierarchy Compliance
- Sources from weight 1-3: 14（原信/概念整理/芒格亲笔/年度索引）
- Sources from weight 4-5: 0
- Sources from weight 6-7: 3（外部权威媒体）
- Blacklisted sources used: 无（未引用知乎/公众号/百度百科/内容农场）

### Taste Principle Compliance
- Long-form vs. snippet ratio: 长文主导（81 封信件全文 + 长文代表作清单 > 金句摘录）
- Firsthand vs. secondhand ratio: 82% 一手
- Controversial/distinctive positions captured: 是（2008 vs 2020 行动差异、不碰科技股遭嘲笑、meme 股批评、"言行不一"讨论）
- Thinking evolution documented: 是（七段演化 + 6 个跨时段矛盾）

## Contradictions Inventory
- Total contradictions found: 6
- Classification:
  - Temporal (view evolution): 烟蒂→品质；账面价值→停用；分散→集中（3 条）
  - Contextual (domain differences): 2008 大买 vs 2020 观望（1 条）
  - Inherent (value tensions): "永远持有" vs 实际卖出；"现金收购"原则 vs Dexter 股票支付（2 条）
- Quality: 实质张力而非表面矛盾——每条都能追溯到具体年份与具体交易，且与"基本面叙事驱动"的解释框架自洽

## Mental Model Candidates
- Candidate count: 21（从 01_writings 提炼），提名前 6 位做三重门：
  1. **护城河/持久竞争优势**（跨维度：01 著作、04 决策、06 时间线均有证据）
  2. **安全边际/不对称下注**（01、04：1956 起点 + 历次买入案例）
  3. **能力圈**（01、04、06：1993 论述 + 科技泡沫 + 苹果重定义）
  4. **基本面叙事驱动的持有/退出**（04、06：可口可乐 vs IBM/航空/苹果减持）
  5. **复利时间机器/长期主义**（01、04：可口可乐 16 倍 + 浮存金杠杆）
  6. **错误即系统补丁**（01、04：错误清单 → 标准修订）
- Preliminary gate assessment: 全部具备跨上下文复现 + 生成力（可推演未见问题）+ 部分具排他性（护城河/能力圈/安全边际为巴菲特标签式模型）

## Known-Answer Bank
- Question: 股价大跌/市场恐慌时应该怎么办？
  Evidence anchors: 1987 市场先生（波动是机会）、2004 别人贪婪时恐惧、2008 买入美国、2020 未大买（反向锚）
- Question: 要不要分散投资？
  Evidence anchors: 1963"分散是对无知的保护"、1996 所有者手册、1988 起集中重仓
- Question: 科技公司能不能投？
  Evidence anchors: 1998-2000 不碰、2011 IBM 后认错、2016 苹果=消费品、2022 台积电短暂持有
- Strength: 三个问题均可从研究证据直接作答，方向/框架/置信度可校准

## Edge-Case Candidate
- Question: 一个以散户为主、涨跌停+T+1、政策驱动的市场（如 A 股），巴菲特会如何设计选股与仓位？
- Why this is adjacent but under-evidenced: 巴菲特从未系统论述 A 股微观结构；但其能力圈/安全边际/长期主义模型可外推
- Expected reasoning approach: 先声明能力圈局限 → 用"可预测性"过滤（政策市 vs 生意质量）→ 安全边际应对波动 → 用"生意语言"重述监管规则

## Cold Figure Assessment
- Total grounded sources: 16+（远 >10）
- Is this a cold figure: 否
- If yes: 不适用

## Backfill Tasks
- （无阻塞项）可选补强：Track 2 增加 2021-2024 股东大会问答转写；外部视角可再加 1-2 个批评性来源（如对 2008 优先股条款的争议分析）
