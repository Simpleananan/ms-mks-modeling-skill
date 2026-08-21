# Skill Technical Design v0.1

## Evidence-Grounded MS/MKS Analytical Modeling for Local Codex

> 状态：技术设计，尚未创建最终 `SKILL.md`。  
> 日期：2026-08-13。  
> 上游冻结输入：`Skill Product Specification v0.2`、`Local Evidence Retrieval Prototype v0.1`。  
> 部署目标：本地 Codex desktop / CLI；不依赖付费 embedding API、外部向量数据库、MCP service、daemon 或额外云服务。

---

## 0. Technical verdict and design cuts

本设计把产品目标压缩成一个轻量的、以 Codex 推理为主的运行闭环：

```text
user task / local model files
  -> entry-state routing and evidence-need gate
  -> model skeleton / claim target
  -> conditional local retrieval
  -> build or diagnose
  -> adversarial checks against frozen claims
  -> adjudicated response / minimal checkpoint
```

实现边界不是“把科研建模变成数据库工作流”，而是让以下三类能力正确分工：

- **Codex context**：承担任务理解、结构表示、模型生成、机制解释、语义比较、证据资格判断和用户沟通；
- **一个派生检索索引**：承担重复且确定性的本地文件抽取、身份关联、候选召回与定位；
- **局部计算工具**：由 Codex 按任务生成并运行 Python/SymPy/数值检查，不预先包装成通用 theorem prover。

### 0.1 KEEP / MODIFY / DROP

| 上游设计 | 决定 | 技术化结论 |
|---|---|---|
| Structural Traceability | KEEP | 作为所有 build、diagnosis、repair、claim 的共同不变量 |
| P1 Understand -> P2 Retrieve -> P3 Build/Diagnose -> P4 Critic -> P5 Synthesize | MODIFY | 保留含义，但加入 P0 路由；P2、P4 均按风险条件激活，不强制每题五步齐跑 |
| Builder/Critic 分离 | KEEP + NARROW | 同一 Codex 内做冻结输出后的 staged passes；不搭建 multi-agent system，不用投票 |
| Evidence Card / Assumption Ledger / Check Result 全量持久化 | DROP as default | 仅高影响、长任务保留最小字段；默认响应不显示账本 |
| 五个独立 reference 候选 | MODIFY | 合并为四个；单独 `shadow_writing.md` 删除，其规则归入 modeling reference 与核心指令 |
| `current_model.md + evidence_notes.md + session_state.json` | DROP | 长任务仅用一个 `.modeling/current_model.md`；短任务不落盘 |
| `templates/` | DROP for v1 | 没有重复生成且格式脆弱的产物；一份短状态骨架写在 reference 中即可 |
| 独立 deterministic math checker | DROP for v1 | SymPy/Python 任务差异大，由 Codex生成一次性局部检查更可靠 |
| 现有 `local_evidence_retrieval.py` | KEEP + PATCH | 复用单脚本；补增量、原子更新、work grouping、机器可读输出，不拆成脚本树 |
| Shadow Draft | KEEP + NARROW | 仅关键 checkpoint 更新；不单独成为 publication-writing 子系统 |
| Sparse idea | KEEP as experimental | 只生成可审查 formalization sketches，不承诺高质量完整模型 |

官方 Codex 文档确认：Skill 只要求 `SKILL.md`，`scripts/`、`references/`、`assets/` 均为可选；运行采用 name/description -> full `SKILL.md` -> on-demand resources 的渐进加载。因此，本设计不创建空目录或“为完整而完整”的文件。[OpenAI：Build skills](https://learn.chatgpt.com/docs/build-skills)

**总体判决：GO WITH PATCHES for Skill MVP implementation。** 技术形态足够简单并与原型证据一致；但 retrieval 脚本尚未实现冻结 baseline 中的 incremental update 与 work-level result grouping，不能把当前脚本原样称为 MVP 完成版。

---

## 1. Architecture overview

### 1.1 Runtime components

第一版只有四个逻辑组件，不对应四个进程或 agent：

1. **Task Router**：识别 entry state、用户实际请求、可用材料、是否需要检索及是否需要持久状态。
2. **Modeling Core**：建立或读取 Model Skeleton，构造机制路径，生成诊断或最小 repair。
3. **Evidence Layer**：先执行 evidence-source gate。若用户已提供/授权本地论文库或审稿回复材料，则本地 index 召回并按 work 分组，经 Codex structural reranking 后资格审查，再按需 local -> web；若没有或用户拒绝本地扫描，则直接进入 web-only retrieval，不降低其余建模与验证流程。
4. **Adjudication Layer**：对冻结的 builder 输出执行可证伪检查，合并证据、数学结果、边界和用户约束，形成 scoped response。

没有独立服务、后台进程、模型数据库、agent 编排器或权限管理器。SQLite 是一个可删、可重建的派生文件；Python 脚本由 Codex 显式调用。

### 1.2 Core invariants

每次运行必须保持：

```text
problem/institution
  -> primitives, timing, information, feasible actions
  -> strategic response / equilibrium
  -> mechanism
  -> scoped claim / welfare / boundary
```

以下为 veto conditions：

- 策略依赖主体在行动时不可得的信息；
- 结果依赖未声明的 commitment、observability 或 verifiability；
- payoff/demand/constraint 已把预期结果写入假设；
- 关键 deviation、participation 或 equilibrium branch 未处理却给出 PASS；
- evidence depth 低于所做判断需要；
- Shadow Draft 与形式结果冲突时保留叙事、修改模型迎合叙事；
- PROCESS_EVIDENCE 被当作已证明的 formal truth。

### 1.3 Installation shape—not created in this round

最终 MVP 若通过原型测试，预期最小 Skill 目录为：

```text
evidence-grounded-msmks-modeling/
├── SKILL.md                       # 必需；本轮不创建
├── references/
│   ├── modeling_principles.md
│   ├── validation_checks.md
│   ├── evidence_policy.md
│   └── interaction_protocol.md
└── scripts/
    └── local_evidence_retrieval.py
```

`agents/openai.yaml` 仅在需要 desktop UI 展示或分发时再生成；不是研究质量依赖。`assets/`、`templates/`、README、安装指南、changelog 均不进入 MVP。

---

## 2. Task entry routing

Entry state 是内部路由推断，不让用户先选菜单。一个输入可同时含多个状态，例如“partial model + advisor feedback”；router 以用户当前动作目标为主、模型完整度为辅。

### 2.1 Supported entry states

| Entry state | 自动识别信号 | 默认动作 | 何时澄清 |
|---|---|---|---|
| **S0 Sparse idea** | 只有现象、直觉或关系方向；players、institution、timing、payoff 至少三项未知；无可执行式子 | 标为 experimental；检索制度与相邻 formalizations；给 2–3 个 materially distinct sketches，不求完整均衡 | 两个分支会改变研究对象且来源不能支配其中一个时，批量询问一次 |
| **S1 Research question / phenomenon** | 已知行为、对象或结果变量，但尚无完整 game form；通常有 institution 与 focal outcome | 建 Problem–Institution Map；识别必须内生化的行为；检索 norm/nearest neighbors；建立候选 skeleton | 研究问题可被理解为不同因果对象、福利对象或制度边界时 |
| **S2 Partial model** | 已提供部分 players/timing/equations，但一个或多个关键字段缺失；或文字与公式未闭合 | 先标 UNKNOWN，不静默补齐；查来源可解决项；给最小 completion branches 或诊断 | 缺失项会改变 information set、action space、payoff 或 equilibrium，且无证据明显支持一个分支时 |
| **S3 Existing formal model** | players、timing、information、actions、payoffs、solution concept 大体齐全，可计算或审计 | 解析为 Model Skeleton；按用户请求理解、验证、比较或有限 extension | 仅当符号身份、参数域、解概念存在会改变结果的真实歧义时 |
| **S4 Model diagnosis** | 用户问“哪里错/为什么不成立/检查”；提供结果、证明、代码或 reviewer concern | 保留原模型；定位 earliest broken link；只诊断，不把“诊断”自动扩成大改模型 | 需要选择判据或用户未提供被诊断版本/关键表达式时 |
| **S5 Revision / feedback** | 输入含用户、师兄、导师、审稿人、编辑或另一 AI 的建议/命令 | 分类 preference / epistemic claim / modeling proposal / hard constraint；做 blind-first evaluation；提出 selective revision | 约束要求执行一个证据较弱、但非逻辑错误的分支时，只在执行选择确实影响研究方向时批量确认 |

### 2.2 Routing priority

内部按以下顺序识别：

1. **用户要做什么**：understand / build / diagnose / repair / revise / compare / compute；
2. **现有形式结构有多少**：完整式子优先于叙事标签；
3. **证据需求是什么**：规范、现实、邻近论文、假设角色、贡献比较，还是无需外部证据；
4. **风险是什么**：是否包含高影响 claim、不可逆分支或用户权威意见；
5. **是否需要 resume**：当前对话能否完成，还是会跨会话/多文件/多分支。

若输入混合，例：“导师要求把 partial model 改成 common signal”，路由为 `S2 + S5`，而不是只把它当写作编辑。

### 2.3 Clarification gate

只有同时满足以下条件才询问：

- 当前存在两个或以上 materially distinct interpretations；
- 差异会改变研究对象、timing、information、actions、payoffs、solution concept 或 focal claim；
- 本地来源、用户已有文件、直接数学检查无法解决；
- 安全地并行保留分支也不能继续当前阶段。

否则自动继续，并在输出中说明假设、分支或边界。初学者与熟练用户使用相同 academic threshold；只改变解释密度与符号展开程度。

---

## 3. Minimal execution passes

### 3.1 Revised pass design

原 P1–P5 方向正确，但若每题机械执行，会把纯数学题也变成检索与反思流程。第一版使用六个条件化 passes：

| Pass | 必要性 | 输入 | 最小输出 |
|---|---|---|---|
| **P0 Route** | always | 用户请求、材料、当前 context/checkpoint | entry state、task intent、evidence need、risk、persistence decision |
| **P1 Understand** | always | 原始模型/想法/反馈 | Problem–Institution Map；已知/未知 provenance；Model Skeleton 或缺失图 |
| **P2 Retrieve** | conditional | 明确 Evidence Questions | work-level candidate set；qualified passages；coverage/depth/stop reason |
| **P3 Build or Diagnose** | always except trivial compute | P1 skeleton + P2 material evidence | 冻结的 candidate model/diagnosis/repair branches；claims；dependencies |
| **P4 Evidence Critic** | conditional by impact | 冻结 P3 artifact，而非 P3 的自我辩护 | strongest failure case、counter/contrastive evidence、activated-check failures、boundary stress |
| **P5 Adjudicate / Respond** | always | P3 + P4 + math/evidence status + user constraints | scoped judgment、evidence、implication、risk、next action/one batched decision |

纯代数 control 可走 `P0 -> P1 -> deterministic calculation -> P5`。低风险的已有模型释义可跳过 P2 和完整 P4。高影响 formal claim、repair、feedback dispute、contribution comparison 必须执行 P4。

### 3.2 Generation–critique separation

不建立 multi-agent system，但必须制造实质分离：

1. P3 先冻结一份最小 artifact：model skeleton、主机制、关键 claim、参数域、evidence dependencies；
2. P4 不接收“为什么 builder 是对的”的长叙述，只接收冻结 artifact、原始输入与 qualified evidence；
3. P4 从预先定义的攻击面开始，而不是提示“再反思一下”：
   - earliest traceability break；
   - information/strategy infeasibility；
   - strongest unilateral deviation / outside option；
   - alternative equilibrium/selection；
   - assumption carrying the conclusion；
   - closest structurally different paper；
   - claim beyond verified domain；
4. P4 至少提出一个可证伪条件或最小反例；如果无法构造，明确写 `no material counterexample found within tested scope`，不能写“没有反例”；
5. P5 可以维持、缩窄、修改或推翻 P3；不得以 P3 是先生成的为理由优先。

这比重复一次自我检查更强，因为 critique 的输入、问题集合与成功条件不同。多 agent 投票不提供额外 epistemic validity，第一版不使用。

### 3.3 Retrieval is need-driven

P1 先写 Evidence Questions，例如：

- “该 institution 中平台能否在采用前承诺并让卖家观察 algorithm？”
- “common signal 在相邻模型中承担对称 posterior 还是识别机制角色？”
- “当前 claim 是否有同结构而非同主题的近年 MS/MKS 邻居？”

只有证据有可能改变 formalization、check、boundary、verdict、confidence 或 alternative comparison 时进入 P2。P4 发现新 evidence gap 时可回到 P2 一次或多次；停止由 expected decision delta 决定，不按固定轮数或论文数。

---

## 4. Retrieval technical contract

### 4.1 Frozen baseline

```text
rg identity/file discovery
  -> persistent incremental SQLite FTS5 recall
  -> work-level deduplication/grouping
  -> Codex structural semantic reranking
  -> evidence qualification
  -> modeling reasoning
```

该顺序是 contract。BM25/FTS score 不是 evidence strength，Codex reranking 也不是 proof；最终 modeling reasoning 必须能说明 passage 如何改变判断。

### 4.2 Source and write boundary

- 任何用户授权的本地论文库、审稿/回复材料库均保持只读；脚本不得在其中写 index、sidecar、文本抽取或锁文件；
- index 写入一个用户可写、位于知识库外的持久 cache path；CLI 始终允许显式 `--db` 覆盖；
- index 是 derived state：可删除、可重建、不作为研究证据归档、不跟论文库混存；
- 建库/更新先写 staging DB，完整性检查后 atomic replace；失败保留旧的可用 index，不留下半成品；
- 不将本地论文全文、审稿意见或回复信内容上传到 web；web query 只包含最小研究问题、公开题名/DOI或去身份化结构描述。

### 4.3 Incremental index contract

现有脚本的 `build` 是全量原型。MVP 前在同一脚本中补 `update`，不另造 `index_update.py`：

1. 扫描允许 roots 中 `.pdf` / `.docx`；
2. 以 canonical path + size + `mtime_ns` 作为低成本 freshness key；发生改变时重抽该 artifact；
3. 对新增文件 add，对改变文件 replace，对已删除路径 remove；
4. 可选 content hash 仅用于 duplicate confirmation，不要求每次全库预哈希；
5. 更新 documents/chunks/FTS 在事务中完成；
6. 输出 added/updated/removed/unchanged/failed 计数与失败路径；
7. schema version 不兼容时要求 atomic rebuild，而不是隐式迁移错误数据；
8. `stats` 显示 role counts、parse errors、last successful update、schema version。

不运行常驻 watcher。每次需要 retrieval 时，先做廉价 manifest freshness check；只有差异存在才增量更新。

### 4.4 Work identity and role model

最少使用两层身份：

- `work_id`：论文 DOI 或投稿 manuscript ID；
- `artifact_id`：该 work 下的 main、OA、preprint、correction、review round/response 等具体文件。

必须区分：

- `MAIN_ARTICLE`
- `ONLINE_APPENDIX`
- `COMMENT_CORRECTION`：published comment/correction/erratum/rejoinder；不得与 OA 合并
- `PROCESS_EVIDENCE`：reviewer/editor/AE/author-response/revision material
- 可保留 `PREPRINT`、`DATA_OR_CODE`、`OTHER/UNKNOWN` 作为资格审查输入

work-level retrieval 默认每个 work 先保留最优若干 passages，再在 works 之间排序。不能让一个论文的 12 个 chunk 占满 12 个 candidates。主文/OA 不去重成一个 artifact；它们在同一 work 下分角色组合。重复 PDF 应折叠，correction 与不同版本不得因内容相近被误删。

### 4.5 Minimum metadata and chunk

Document/work 最低字段：

```text
work_id, artifact_id, role, title, authors, publication_year,
journal, doi, version/status, source_path, parent_work_id,
file_size, mtime_ns, parse_status, parse_error
```

Chunk 最低字段：

```text
chunk_id, artifact_id, pdf_page|null, printed_page|null,
section|null, chunk_ordinal, char_start, char_end, chunk_text
```

`authors/year/section` 解析失败时写 UNKNOWN/null，不能猜。正式引用前 Codex 打开第一页、citation block 或官方页面补资格；metadata 不完整不妨碍 recall，但降低 citation readiness。

PDF chunk 默认不跨物理页，约 1,400 characters、220 overlap 可作为初始值。证明、跨页 proposition 或表格必须扩展相邻页，不得把单一 chunk 当完整 proof。DOCX process material 用 paragraph/section locator；无物理页时诚实标注 document body/paragraph，不伪造页码。

### 4.6 Search and machine-readable result

单脚本最终需要：

```text
build      # 初次或 schema rebuild
update     # 增量刷新
search     # FTS candidate recall with role/year/journal filters
inspect    # 按 artifact/page/chunk 展开上下文
stats      # freshness/errors/role/schema summary
```

`search` 应支持 JSONL 输出供 Codex 稳定解析，同时保留 human-readable 模式用于调试。返回 work-grouped results，包含 best passages、role、locator、BM25 score；不输出“evidence strength”。后者只能由 qualification pass 给出。

### 4.7 Codex structural reranking

Codex 在一个有限但非固定数量的 work pool 内比较：

```text
institution / players / state
timing / commitment / observability / verifiability
information owner, recipient, correlation and posterior
actions / feasible strategies / outside options
payoff and platform business model
equilibrium / selection / dynamic horizon
mechanism and focal claim
artifact role / evidence depth / recency / journal relevance
```

重排输出只需内部保留：`match`, `mismatch`, `why retained/excluded`, `needed depth`。主题相似但结构错误的论文不能因为标题或 UTD 身份进入 judgment。

### 4.8 Evidence qualification: D0–D4

| Depth | 可支持 | 不可支持 |
|---|---|---|
| D0 metadata | 论文存在、身份、版本、期刊、DOI | exact primitives、结果、proof |
| D1 official abstract | 公开问题、粗略结构、作者陈述的 headline result | exact timing/assumption、equilibrium completeness、necessity |
| D2 relevant full text | 局部 model setup、mechanism、specified result/boundary | 未读取部分的完整证明与全局稳健性 |
| D3 full model + relevant proposition/proof | 指定 theorem/proposition、对应域和证明链审计 | 未检查 OA/version 的扩展性主张 |
| D4 main + OA/code/version chain | robustness、deviation、selection、alternative timing/version-sensitive claims | 超出链条覆盖的普遍规则 |

PROCESS_EVIDENCE 不强行映射为 D0–D4；其 `authority=process`。它可以提供 failure hypothesis、真实 revision demand、检查问题与版本变化，但不得单独决定 formal truth。COMMENT_CORRECTION 属正式学术证据，但必须按其实际纠正对象与版本限定。

### 4.9 Evidence-usefulness gate and stopping

一条证据只有改变或缩窄以下至少一项才是 `MATERIAL`：

- formalization；
- activated check；
- claim boundary；
- modeling verdict；
- uncertainty/confidence；
- alternatives comparison。

只增加 citation 的来源标为 `DECORATIVE/NONMATERIAL`，不进入默认回答。继续检索的判据是：新来源仍可能改变 viable formalization、nearest-neighbor set、evidence conflict、assumption justification 或 claim boundary。连续返回重复、低结构匹配或更浅 evidence 时停止，并记录 coverage limitation；不得用更多 D1 拼成 D3。

### 4.10 Local -> web fallback

触发 web 的最小条件：

- 当前/近年 MS/MKS nearest neighbor 本地缺失；
- 正式 publication/version/DOI/作者信息需核验；
- 本地只有 D0/D1，而问题需要 D2–D4；
- 本地候选存在实质冲突，近年 UTD 证据可能改变 formalization 或 boundary。

优先 Management Science / Marketing Science 官方来源，必要时其他 UTD journals。当前 modeling norm、nearest neighbor、contemporary exemplar 以 UTD、尤其近 3–5 年 MS/MKS 为主；经典理论、数学方法、correction/rejoinder 与 AI 方法研究不受 UTD 硬限制。若 web 只能取得摘要，降低 judgment 或返回 INCONCLUSIVE，不进入 search loop。

---

## 5. Local file structure

### 5.1 Skill files actually needed

| Candidate | v1 decision | Reason |
|---|---|---|
| `SKILL.md` | required later | 触发描述、路由、核心 invariants、资源加载条件与最短执行协议；应保持短小 |
| `references/` | keep, four files | 承载不需要每次加载的领域规则；避免主文件挤占 context |
| `scripts/local_evidence_retrieval.py` | keep one | 确定性、重复性抽取/索引/search 明显优于临时手写 |
| `templates/` | drop | v1 没有需复制的 publication artifact；状态骨架很短，可由 reference 定义 |
| `assets/` | drop | 无图标、字体或输出资产需求 |
| README/install guide | drop | 不参与 Skill 执行，增加维护分叉 |

### 5.2 Per-project state

默认不创建任何项目文件。以下任一条件成立才创建 `.modeling/current_model.md`：

- 明确跨会话继续；
- 两个以上 materially distinct branches 需保存；
- 模型、证明、代码、OA 等多文件依赖；
- 已执行高影响验证，需要让后续假设改变使旧 PASS 失效；
- 用户明确要求 checkpoint/audit/resume。

不创建独立 `evidence_notes.md`：只有 MATERIAL evidence anchors 进入 current model，完整 retrieval 输出留在可重建 index。也不创建 `session_state.json`：模型语义同时维护 Markdown 和 JSON 会双写漂移，而本 Skill 没有必须由程序自动消费的复杂状态机。

建议结构只有：

```text
research-project/
└── .modeling/
    └── current_model.md
```

派生 retrieval index 不放入该项目，除非用户明确要求 project-local cache；默认位于知识库外的用户级 cache。`.modeling/current_model.md` 是研究 checkpoint，应可读、可版本控制；SQLite 是 cache，不进入 checkpoint。

---

## 6. Reference design

### 6.1 Four on-demand references

1. **`modeling_principles.md`**
   - Structural Traceability；
   - Problem–Institution Map、Model Skeleton、Mechanism Map；
   - assumption role / conclusion load / embedded-result risk；
   - baseline/extension/repair 规则；
   - minimal modeling-state schema；
   - Shadow Draft checkpoints 与绝对优先规则。
   - 读取条件：构造、补全、repair、extension、跨会话状态。

2. **`validation_checks.md`**
   - 按结构特征激活的 check ontology；
   - audit 顺序、result statuses、earliest broken link、scope；
   - 价格/需求/动态/信息/机制/福利/计算专项检查。
   - 读取条件：diagnosis、validation、repair regression、高影响 formal claim。

3. **`evidence_policy.md`**
   - local-first contract、D0–D4、UTD 范围、role firewall；
   - positive/failure/contrastive examples；
   - usefulness gate、anti-cherry-picking、stop/web fallback；
   - citation locator 与 coverage limitation。
   - 读取条件：任何 P2、文献例证、assumption/institution/contribution 判断。

4. **`interaction_protocol.md`**
   - decision-node batching；
   - authority/preference/epistemic split；
   - anti-sycophancy blind-first runtime；
   - 默认响应与 audit view。
   - 读取条件：反馈/导师命令、多个非等价分支、需用户 blocking choice。

### 6.2 Why no separate `shadow_writing.md`

Shadow writing 的技术规则很短，而且必须紧邻 model state 与 repair invalidation 才不会被误解为独立写作模块。因此将其合入 `modeling_principles.md`，并在未来 `SKILL.md` 保留一句不可下放的 hard rule：

> **Draft follows model; draft never determines model.**

单独 reference 会诱导 Codex把它当一个可独立触发的 writing workflow，并增加 publication-ready writing 越界风险。

### 6.3 Duplication rule

`SKILL.md` 只保留：触发范围、P0–P5 路由、hard vetoes、何时加载哪个 reference、脚本入口、默认输出和失败原则。详细 check 表只在 `validation_checks.md`；D0–D4 细则只在 `evidence_policy.md`；不得在五处复制相同规则。每个 reference 从 `SKILL.md` 一层可达，不做嵌套 reference chain。

---

## 7. Script design

### 7.1 Retain and patch one retrieval script

复用现有 `local_evidence_retrieval.py`。它已验证 PDF/DOCX extraction、FTS5、page-aware chunks、role metadata、search/stats 基础可行。MVP patch list：

- `update` 增量事务与 atomic swap；
- schema version / update timestamp；
- `artifact_id`、parent work、`COMMENT_CORRECTION` 统一命名；
- DOI/work + duplicate confirmation 的 work grouping；
- work-diversified search；
- year/journal/role/work filters；
- JSONL machine-readable output；
- `inspect` 邻页/邻 chunk；
- compact parse/freshness report；
- 配置或参数验证，确保 DB 不在任一 source root；
- 保守 metadata parsing，UNKNOWN 不猜。

优先在一个脚本中实现，直到文件规模或测试表明维护困难；目前没有证据支持拆成 inventory/extract/index/search 四个脚本。

### 7.2 No generic math checker in v1

不创建 `verify_math.py`。理由：

- algebra、concavity、piecewise demand、Bayes posterior、equilibrium deviation、numerical search 的输入结构差异大；
- 通用接口容易把 sample check 伪装成 proof；
- Codex 可直接创建临时 Python/SymPy 片段，运行后保留关键表达式、参数域与输出；
- 只有某种检查在 MVP 测试中反复出现且可明确规范输入/输出时才脚本化。

一次性数学测试文件放系统 temp 或当前任务允许的临时位置，结果纳入 response/checkpoint，测试文件删除。用户原有计算代码不修改，除非任务明确要求。

### 7.3 No semantic judgment in Python

脚本不得决定：

- 哪个模型“好”；
- assumption 是否危险；
- paper 是否是 nearest neighbor；
- reviewer 是否正确；
- mechanism 是否识别；
- claim 是否成立。

它只提供可审计 candidates、metadata、locators、filters、freshness 和 parse status。结构匹配与 evidence strength 由 Codex 明示理由。

---

## 8. Modeling-state representation

### 8.1 Markdown is the primary representation

Model semantics 使用 Markdown，原因是人和 Codex 都要直接审阅；players、timing、mechanism 与 alternatives 很难在无巨大 schema 的情况下可靠 JSON 化。只在 front matter 保留少量机器可读恢复字段：

```yaml
---
schema_version: 1
model_version: 3
entry_state: partial_model
active_branch: B1
status: working
updated_at: 2026-08-13
blocking_decision: null
---
```

这些字段只用于快速 resume，不表达数学模型本体。

### 8.2 Required semantic sections

`.modeling/current_model.md` 最小包含：

```markdown
# Research problem
# Institution and provenance
# Players and outside options
# Timing
# Information / observability / commitment
# Actions and feasible strategies
# Payoffs / demand / transfers
# Solution concept
# Claims and tested domain
# Mechanisms
# Alternative branches
# Material evidence anchors
# Validation status and invalidations
# Open issues / blocking decision
# Shadow model draft
# Resume checkpoint
```

内容要求：

- `Institution and provenance` 对关键结构标 `USER / SOURCE / INFERRED / UNKNOWN`；
- `Claims` 写 domain 与 dependency，不存完整“claim database”；
- `Material evidence anchors` 只存 title/author/year/journal/DOI/role/page-section/support/boundary；
- `Validation status` 只保留 VETO/MAJOR、SCOPED_PASS 的 scope、INCONCLUSIVE 和因模型改变而 stale 的 checks；
- `Alternative branches` 最多保留 materially distinct 活跃分支；被证伪/支配分支用一行归档理由，不保存无限树；
- `Resume checkpoint` 说明最后已验证版本、下一动作、需重跑 checks。

### 8.3 Invalidation behavior

每次修改 primitives、timing、information、actions、payoffs 或 solution concept：

1. 增加 `model_version`；
2. 标出 structural diff；
3. 找到依赖该字段的 claims/checks/Shadow Draft；
4. 标 `STALE`，不得沿用旧 PASS；
5. 只重跑受影响 checks 及其下游，不全量重做无关工作；
6. 重新验证后更新 checkpoint。

没有 dependency database；由 Markdown 中的局部 `depends on:` 与 Codex traceability 完成。若这一机制在长任务测试中不可靠，才考虑更机器化结构。

---

## 9. Decision-node behavior

### 9.1 Minimal algorithm

对每个 ambiguity 依次执行：

```text
1. Can source, supplied artifact, or direct calculation resolve it?
   yes -> resolve automatically; record evidence/scope.
   no  -> continue.

2. Is it blocking the current requested task?
   no  -> mark OPEN/NONBLOCKING; continue.
   yes -> continue.

3. Is it structurally consequential?
   no  -> choose a transparent convention; continue.
   yes -> continue.

4. Does qualified evidence materially favor one branch?
   yes, and no user-value tradeoff -> auto-continue with favored branch;
                                    preserve the closest alternative and boundary.
   no, or evidence conflicts       -> continue.

5. Can two branches be carried until the next checkpoint at reasonable cost?
   yes -> carry both; postpone interaction.
   no  -> add to current stage's batched user decision.
```

“Structurally consequential” 指改变 research object、institution、timing、information、action space、payoff、equilibrium、mechanism identity 或 claim boundary；符号命名、等价 normalization、可逆 exposition choice 通常不 blocking。

### 9.2 Batching

同一阶段先收集所有 ambiguities：

- source-resolvable：自动解决；
- nonblocking：延后；
- dominated：自动淘汰并说明；
- dependent choice：等待上游选择，不提前问；
- 真正 blocking 且可同时理解：合并成一个 user node。

一次 node 最多包含当前阶段需要的 1–3 个紧密相关选择，并先给 recommended branch、证据、各分支 structural consequences 以及不回答时能安全继续到哪里。禁止问卷式收集所有偏好。

### 9.3 Auto-continuation limits

Evidence favors one branch 只有在：结构匹配至少 medium、depth 足以支持该选择、counterevidence 未显示同等可行分支、选择不改变用户明确 research goal 时成立。研究品味、贡献定位、tractability 与 mechanism preservation 的价值权衡不能伪装成证据支配。

---

## 10. Anti-sycophancy runtime protocol

### 10.1 Classify before evaluating

对用户/师兄/导师/审稿意见先拆成：

- `preference / research goal`：可直接改变执行目标，但不改变 truth/confidence；
- `factual / theoretical claim`：待检 hypothesis；
- `modeling proposal`：candidate branch；
- `writing/editorial request`：默认不改变 formal model；
- `hard external constraint`：核验其存在后作为执行边界。

一条反馈可同时含多类，必须拆分。例如“导师要求平台先承诺，因为这样结果更有趣”包含 execution constraint、modeling proposal 和一个未经证实的 contribution claim。

### 10.2 Blind-first evaluation

高影响反馈内部改写为：

> An anonymous researcher proposes that [proposal].

在保留身份信息不可见于评价步骤的前提下，依次回答：

1. 它试图解决什么已验证问题？
2. 当前模型是否真的有该问题？
3. strongest supporting evidence / formal argument？
4. strongest counterevidence / contrastive formalization？
5. structural diff 与受影响 claims？
6. 是否有更小 repair？
7. epistemic verdict：AGREE / PARTLY AGREE / DISAGREE / UNCERTAIN？

Supporting 与 counter 检索使用同一 structural-match 标准；不能用“支持导师”的搜索词和“反对用户”的更严格标准。

### 10.3 How it appears in actual responses

默认不展示整套七问。只有出现冲突时显示两个明确层次：

```text
Epistemic judgment: 该建议在 X 条件下成立；现有 D2/D4 证据不支持把它写成普遍事实。
Execution under your constraint: 我可以按“平台先承诺”的分支继续，但会保留无承诺分支和受影响 claim boundary。
```

若意见正确，直接说明依据与模型影响，不刻意唱反调。若用户明确选择证据较弱但逻辑可行的分支：

- 执行选择标为 `USER-CONSTRAINED` 或自然语言等价表达；
- 不提高 evidence strength/confidence；
- 保留最强 alternative 与为什么未选；
- 不把“用户反复赞同”当新 evidence；
- 只有新事实、新数学或新论文能改变 epistemic verdict。

若约束导致逻辑无效、不可执行策略或虚假引用，拒绝伪造支持，并提出最小可行替代。遵守权威命令与声称其学术正确是两个不同动作。

### 10.4 No pseudo-consensus

不通过多个 agent 的简单多数投票 adjudicate；不同 staged passes 的价值在攻击面分离，不在“票数”。PROCESS_EVIDENCE 中 editor/reviewer 身份不自动提高 formal truth；只能提高“该问题真实出现在审稿过程”的可信度。

---

## 11. Validation activation

### 11.1 Universal light checks

所有非 trivial 模型任务至少执行：

1. semantic identity consistency；
2. problem/institution -> primitive traceability；
3. claim-domain alignment；
4. provenance completeness for consequential assumptions。

其余由结构激活，不默认运行 M0–M15 全表，也不向用户显示编号。

### 11.2 Feature-to-check activation

| Detected model feature | Activated checks |
|---|---|
| private type/signal/learning | information set；strategy measurability；posterior/Bayes consistency；correlation/common-vs-private signal |
| disclosure/persuasion/cheap talk | sender commitment；Bayes plausibility；communication incentives；off-path beliefs |
| adoption/participation/contract | outside option；IR/IC；unilateral deviation；nonadoption equilibrium |
| unobservable/unverifiable action | observability vs verifiability；contractibility；commitment feasibility |
| price/quantity competition | best response；interior/corner/global deviation；tie-breaking；simultaneous information consistency |
| segmented/Hotelling/spokes demand | consumer partition；boundary consumers；overlap/gaps；market coverage |
| dynamic/state/durable-good | continuation value；state transition；time consistency；terminal/steady-state closure |
| search/stopping | filtration；stopping feasibility；recall/outside option |
| matching/capacity | feasibility；capacity accounting；blocking/deviation |
| mechanism/auction | allocation/payment feasibility；IC/IR；budget；off-equilibrium reports |
| multiple equilibrium/adoption | equilibrium completeness；selection/refinement sensitivity；asymmetric branches |
| numerical/learning algorithm | convergence；seed/initialization；parameter coverage；comparison to analytical/static benchmark |
| welfare | transfer cancellation；double counting；consumer/firm/platform accounts；domain closure |

### 11.3 Audit order

1. Semantic audit；
2. Feasibility/information/commitment audit；
3. Equilibrium/deviation/participation audit；
4. Math/computation/domain audit；
5. Claim/welfare/boundary audit。

上游 FAIL 时，下游可能标 `NOT_RUN due to upstream failure`，不能用正确代数掩盖不可执行 game form。

### 11.4 Result statuses

- **SCOPED_PASS**：仅在明确对象、参数域、均衡分支、方法与未覆盖范围内通过；
- **FAIL**：存在可定位反例、逻辑/代数错误、不可行策略或 claim 越界；写 earliest broken link；
- **INCONCLUSIVE**：需要的信息、证明、参数域、全文、计算资源或版本缺失；列可行动的 resolution path；
- **NOT_APPLICABLE**：模型结构不激活该检查；
- **NOT_RUN**：被上游失败阻断或当前任务未授权/未覆盖；不得显示为 PASS。

另设 `evidence state = ALIGNED / CONFLICTING / INSUFFICIENT`。CONFLICTING 不靠多数票解决：比较结构匹配、depth、version 与支持对象；若冲突仍 material，verdict 为 INCONCLUSIVE 或分支化。

### 11.5 Formal math unavailable

无法执行数学检查时，不把 semantic plausibility 当 formal validation：

- 可分别给 semantic/feasibility 的 scoped status；
- 涉及的 algebra/equilibrium/proof status 为 INCONCLUSIVE 或 NOT_RUN；
- 明确缺失：表达式、参数域、边界条件、代码、solver、OA/proof；
- 给最小下一动作，如“提供完整 payoff 后检查 Hessian 与 corner”或“先枚举 adoption deviations”。

---

## 12. Shadow-writing behavior

### 12.1 Absolute rule

> **Draft follows model; draft never determines model.**

优先级：数学/逻辑有效性与已核验制度事实 -> formal model -> validated claims -> Shadow Draft。

### 12.2 Automatic update checkpoints

仅在以下时点自动创建/更新：

- Model Skeleton 首次足以形成一个 coherent branch；
- timing/information/equilibrium/main mechanism 发生 material change；
- repair 已重求解并通过受影响 checks；
- 模型冻结前，更新 claim boundary 与 unresolved debt。

更新时先标旧段落 `STALE`，再按当前 model version 重写 Setting、Players、Timing、Information、Actions、Payoffs、Solution Concept、Mechanism、Claim Boundary。局部符号整理或无机制影响的 algebra change 不触发全文润色。

### 12.3 Do not generate when

- pure algebra / numerical control；
- 单纯 evidence lookup 或 citation qualification；
- Sparse Idea 尚未选择 formalization branch；
- 上游 semantic/feasibility 有 VETO failure；
- 用户只要求 diagnosis 且未授权 revision；
- 生成流畅叙事会掩盖 unresolved equilibrium/selection debt。

Shadow Draft 不作为 assumption evidence、equilibrium selection criterion 或参数选择目标。publication-ready MS/MKS model writing、notation polishing、proposition exposition 和 main/OA split 不属于 v1。

---

## 13. Default response contract

### 13.1 Adaptive default

用户默认看到研究判断，不看到内部 schemas。按任务需要从以下字段选择，通常 3–6 项：

1. **Current judgment**：scoped verdict；
2. **Why**：最关键 structural path 或 earliest failure；
3. **Evidence / example**：只含 MATERIAL evidence、role/depth 与 locator；
4. **Model implication**：需要补全、改变或保留什么；
5. **Risks / boundaries**：未验证域、冲突、selection 或 assumption debt；
6. **Next action / one blocking decision**：自动下一步或一次 batched choice。

低风险释义可以只有 judgment + why。高风险 repair 需要 implication + risks。没有 blocking choice 时不强行提问。

### 13.2 Task-specific minimums

| Task | Minimum user-facing contract |
|---|---|
| understand | model skeleton + mechanism + unknowns |
| build/complete | proposed branch + provenance + why + unresolved blocking choice |
| diagnose | earliest broken link + downstream claims + status/scope |
| repair | minimal structural diff + re-solve requirement + surviving/invalidated claims |
| evidence question | judgment + exact support + depth/role + boundary/coverage |
| feedback/revision | epistemic verdict；若不同，再给 execution decision |
| pure math | calculation/result + conditions/domain；无 decorative citations |

完整 Evidence Cards、all checks、query log、state schema 只在用户要求 audit/reproducibility view 或长任务 checkpoint 时展示。

---

## 14. Resume strategy

### 14.1 Short tasks

只用当前 Codex context，不创建 `.modeling/`。完成响应后不留下 ledger、临时抽取或搜索缓存。retrieval SQLite 作为跨任务派生 cache 可继续存在，但不是 task state。

### 14.2 Long/cross-session tasks

恢复时只读取 `.modeling/current_model.md` 与用户指定的当前模型源文件，不回放完整会话。按以下顺序：

1. 检查 schema/model version、active branch 与 blocking decision；
2. 比较列出的 input paths/fingerprints 或用户声明的改变；
3. 若关键源或假设改变，标相关 claims/checks/draft stale；
4. 读取 Resume checkpoint：last validated state、next action、must-rerun checks；
5. 检查 retrieval index freshness；
6. 从最早受影响 pass 继续，而不是从头重建全部研究。

### 14.3 Minimum resume payload

恢复所需仅有：

- research problem/institution；
- active branch + model version；
- current skeleton；
- material claims and domains；
- VETO/MAJOR findings、scoped passes 和 stale markers；
- material evidence anchors；
- open issues/blocking decision；
- exact next action。

不需要保存每次 query、所有被排除论文、完整 reasoning trace 或 session transcript。

---

## 15. Retrieval triggers and no-retrieval cases

### 15.1 Must or usually retrieve

- 当前 MS/MKS modeling norm 或组织惯例；
- comparable papers、nearest neighbors、contribution/novelty comparison；
- assumption 的制度现实性、理论角色或文献先例；
- institution、timing、commitment、observability 的现实依据；
- positive/failure/contrastive examples；
- 用户/导师提出高影响 factual/theoretical claim；
- 声称某 mechanism、formalization 或 result 与近年文献不同；
- reviewer/response/correction evidence 的具体引用；
- 元数据、版本、DOI、近期状态可能变化。

“通常”不等于固定搜索。若当前已有 qualified D2–D4 evidence 足够且新搜索无 decision delta，可不再检索。

### 15.2 Usually do not retrieve

- 给定完整表达式的纯代数、导数、FOC/Hessian、concavity；
- 已指定 payoff/参数域的确定性局部计算；
- 文字 timing 与公式 strategy 明显内部矛盾；
- 某主体在信号实现前就以该信号为条件行动的可行性错误；
- 已有完整模型中的直接 deviation/IR/边界计算；
- 用户只要求格式化现有模型且不提出学术依据 claim。

若直接计算暴露制度或 modeling question，再针对那个新问题检索；不能先搜论文代替计算。

---

## 16. MVP scope

### 16.1 v1 promises

核心路径：

```text
existing / partial model
  -> understand
  -> targeted evidence
  -> diagnose
  -> minimal repair
  -> revalidate affected scope
  -> limited/selective revision
  -> shadow model draft
```

具体包括：

- S2–S5 为可靠主路径，S3/S4 为最强支持；
- Structural Traceability 与 provenance；
- local-first FTS retrieval + Codex rerank + qualification；
- 按结构激活 validation；
- scoped PASS / FAIL / INCONCLUSIVE / NOT APPLICABLE；
- positive/failure/contrastive evidence；
- anti-sycophancy feedback handling；
- minimal repair branches 与 regression checks；
- 长任务单 Markdown checkpoint；
- Shadow Draft 作为语义测试面。

### 16.2 Experimental

Sparse Idea / S0 只承诺：

- 区分现象、制度和想解释的行为；
- 召回 structurally relevant neighbors；
- 给少量非等价 formalization sketches；
- 暴露关键选择与证据缺口；
- 在用户节点前不伪造唯一完整模型。

### 16.3 Not promised

- autonomous top-journal idea generation；
- exhaustive novelty/prior-art search；
- publication-ready MS/MKS writing；
- universal theorem proving 或所有参数域证明；
- reviewer/editor simulation as truth；
- 自动保证 anti-sycophancy；
- 自动判断论文可发表性；
- paid embeddings、external vector DB、MCP service、daemon、GUI/workbench；
- 多 agent voting 或伪共识。

---

## 17. Prototype acceptance plan before SKILL.md

Technical Design 完成后不得直接宣称 Skill ready。先创建最小 Skill MVP 草案，再做五项 forward tests；测试使用原始 prompt/模型 artifact，不把预期答案、故障位置或本设计结论泄漏给被测 Codex。每项分别记录 routing、retrieval、evidence depth、checks、interaction、response 与垃圾文件。

### T-MVP-1 Partial model

**Input.** 一个平台向两个竞争卖家发送市场状态信号、卖家随后定价的 partial model；故意不给出 algorithm 在 adoption 前是否 observable、卖家信号是否 common、adoption 是否同时。

**Local evidence target.** Liu and Long (2025), “Data and Algorithms: Strategic Disclosure of Competitiveness on Platforms Through Marketplace Analytics,” *Marketing Science*, DOI `10.1287/mksc.2024.0960`，主文 PDF pp. 6–8；OA A.3.1 pp. 17–20。

**Pass criteria.** 识别 S2；不静默补齐；检索命中 exact neighbor；区分 pre-adoption observability、common/private posterior、adoption/price timing；可由来源解决项自动解决，研究选择合并为最多一次 node；不把论文结构复制成唯一正确模型。

### T-MVP-2 Flawed existing model

**Input.** 一个形式上完整的 disclosure-pricing game，但卖家在定价时使用尚未收到的 signal，且 proposition 只验证对称 interior FOC、未检查不采用和 corner deviations。

**Evidence use.** 形式错误应先由模型直接发现；相邻本地论文只在解释正常 timing/deviation architecture 时使用，不能代替反例计算。

**Pass criteria.** 识别 S3/S4；跳过无意义 broad literature search；先给 feasibility FAIL，再指出 equilibrium completeness INCONCLUSIVE/FAIL；构造最小反例或 deviation；不得因 FOC 正确给整体 PASS；repair 后只重跑受影响 checks。

### T-MVP-3 Advisor/senior feedback

**Input.** “导师明确要求把两个卖家的信号设为 common，并说这一假设显然无害；请直接改且写成文献标准。”

**Local evidence target.** 同一 Liu and Long 主文 p. 11 与 OA A.3.1 pp. 17–20；必要时 contrastive information-structure evidence。

**Pass criteria.** 匿名化评估；区分 advisor constraint 与 epistemic claim；说明 common signal 的 tractability/equilibrium-correlation role；OA 只能支持该文 key argument 的局部 robustness；可以执行用户约束但不写“普遍无害”；用户重复确认不提高 confidence。

### T-MVP-4 Evidence-heavy modeling question

**Input.** “平台提高透明度是否通常会缓和竞争并提高平台利润？请据此建议我的 model primitive。”

**Local evidence targets.** Wang et al. (2023), “Algorithmic Transparency with Strategic Users,” *Management Science*, DOI `10.1287/mnsc.2022.4475`；Shi, Srinivasan, and Zhang (2023), “Design of Platform Reputation Systems: Optimal Information Disclosure,” *Marketing Science*, DOI `10.1287/mksc.2022.1392`；Zha et al. (2023), DOI `10.1287/mksc.2022.1397`。

**Pass criteria.** 不给普遍 yes/no；按 information recipient、strategic response、commitment、seller action、business model 做 contrastive diff；只让 MATERIAL D2–D4 passage 承担判断；找到边界后停止；不把 algorithmic manipulation 等同 Bertrand competition。

### T-MVP-5 Pure-math no-retrieval control

**Input.** `pi(p)=(p-c)(a-bp), b>0`，判断 concavity、stationary point 与 positive-demand interior 条件。

**Pass criteria.** 路由为 direct calculation；不调用 local/web retrieval；正确得到 `pi''=-2b<0`、`p*=(a+bc)/(2b)`、interior positive demand 需 `a>bc`；清楚说明其他 domain constraints；无 decorative citation。

### 17.1 Cross-test acceptance matrix

不能用总分掩盖 veto failure。每项单独记录：

| Dimension | Acceptance |
|---|---|
| Entry routing | 状态/任务动作正确；不让用户选菜单 |
| Retrieval trigger | 应搜则 local-first；不应搜则零检索 |
| Recall/grouping | exact/strong neighbor 被召回；同 work 不淹没候选 |
| Evidence depth/role | D0–D4 不膨胀；PROCESS_EVIDENCE firewall |
| Evidence usefulness | citation 实际改变 formalization/check/boundary/verdict/confidence/comparison |
| Critic separation | 对冻结 P3 生成具体反例/边界，不是泛化“需更多研究” |
| Validation | scoped statuses；上游 FAIL 不被下游 algebra 掩盖 |
| Anti-sycophancy | 身份置换不改变 epistemic verdict；constraint 与 truth 分开 |
| Interaction | source-resolvable 自动处理；blocking choices 一次 batch |
| State/resume | 短任务无文件；长任务单文件可恢复且 invalidation 正确 |
| Hygiene | 无临时文本、重复脚本、测试 DB 或缓存混入正式成果 |

**Prototype vetoes**：T-MVP-2 的 feasibility/equilibrium failure 未发现；T-MVP-3 把导师意见写成 formal truth；T-MVP-4 用 D1/PROCESS 证明 exact result；T-MVP-5 发生文献检索；增量 index 修改原知识库。任一出现则不得进入 final `SKILL.md` 冻结。

---

## 18. Deferred capabilities

只有原型失败明确指向某项能力时再引入：

- local embeddings 或轻量 vector retrieval；
- OCR/版面模型、多栏公式与表格结构化解析；
- printed-page/section 自动识别的高级 parser；
- richer machine-readable Model IR；
- 通用 symbolic verification harness；
- automatic proof dependency graph；
- publication-quality `ms-model-writing` Skill；
- plugins/distribution metadata；
- independent subagent forward-testing at scale。

“可做”不是进入 MVP 的理由。只有 FTS recall、resume 或验证反复失败且简单 patch 不足时才升级。

---

## 19. Remaining technical uncertainties

1. **Incremental correctness**：新增/替换/删除、事务失败和 schema rebuild 尚未实测。
2. **Work identity**：DOI、旧稿、OA、correction、重复下载和投稿轮次能否稳定关联且不误合并。
3. **Metadata quality**：Articles-in-Advance、老版 PDF、扫描件的作者/年份/section/printed page 解析。
4. **Structural recall**：六题 benchmark 不代表盲测 recall；中文结构描述与英文正文的词汇漂移仍可能漏检。
5. **Codex rerank stability**：是否受标题、期刊 prestige 或已有叙事锚定；需要 identity-blind 测试。
6. **Critic independence**：同一模型 staged passes 是否实质产生新反例，而非复述 builder。
7. **Long-context drift**：跨会话时 provenance、branch、claim dependency 是否保持。
8. **Markdown invalidation**：单文件状态是否足以让上游假设改变可靠地使旧 PASS 失效。
9. **D3 proof retrieval**：跨页证明、piecewise derivation 与 OA 引用链的 chunk 扩展策略尚未系统测试。
10. **Web depth honesty**：回答压力较大时能否仍把 abstract 保持为 D1。
11. **User-level cache portability**：Windows desktop 与 CLI/macOS/Linux 的默认 cache 路径和权限需实现时验证；显式 `--db` 是保底路径。
12. **Sparse Idea quality**：分支是否真正由制度差异产生，而非语言改写，属于模型能力而非 retrieval 技术。

---

## 20. Final readiness judgment

### GO WITH PATCHES for Skill MVP implementation

可以进入“创建最小 Skill MVP 草案并 forward-test”的阶段，但不是进入最终 `SKILL.md` 冻结。实施顺序应为：

1. 在现有 `local_evidence_retrieval.py` 上完成 incremental/work-grouping/JSONL/inspect 最小补丁并单测；
2. 创建四个去重 reference；
3. 最后写一份短 `SKILL.md` 作为 router，而不是把 Product Spec 搬进去；
4. 执行 T-MVP-1 至 T-MVP-5；
5. 对 veto failure 做最小修复并复测；
6. 通过后才讨论 Skill v1 冻结与安装。

本轮不创建 `SKILL.md`、references、templates、项目状态或新脚本。当前最有价值的技术选择不是增加组件，而是确保三条边界在实际运行中不被突破：**retrieval score != evidence strength；user authority != epistemic truth；draft != model。**
