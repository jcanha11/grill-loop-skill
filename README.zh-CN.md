# Grill Loop

中文 | [English](README.md)

Grill Loop 是一个 Codex skill，用来对产品方案、策略方案、实验方案做可审计的循环式拷问与迭代。

它继承 `grill-me` 的价值：持续追问关键问题；但它要解决 `grill-me` 的运行瓶颈：人不应该为每一个小问题持续在线接球。

## 可视化说明页

可视化页应作为这个项目的公开落地页和演示页，而不是放在仓库里吃灰：

- GitHub Pages：<https://jcanha11.github.io/grill-loop-skill/grill-loop-visual/>
- 本地预览：

```bash
python3 -m http.server 8765
open http://127.0.0.1:8765/grill-loop-visual/
```

它要讲清楚的不是“多 Agent 很酷”，而是这个因果链：

```text
Grill Me 问得细
→ 每一问都等人
→ 人的注意力成为瓶颈
→ Grill Loop 自动分流简单问题、可查问题、争议问题、升级问题
→ 人只处理真正需要人的例外
```

## 为什么有 Grill Me 还需要 Grill Loop？

`grill-me` 的价值在于它会细致地、一问一答地追问方案。问题也恰恰在这里：每个问题都会等待人的反馈，包括低风险、可逆、已有明确推荐答案、或者可以从材料中查到答案的问题。

Grill Loop 改变的是运行方式：

- 简单且可逆的问题可以快速通过；
- 可从本地材料、代码、SQL、配置或用户提供资料中回答的问题先研究；
- 重要或有争议的问题交给独立 Judge 裁决；
- 只有需要业务事实、授权或风险接受的问题才升级给人。

目标不是替代人判断，而是把人的注意力留给真正需要人的判断。

## 它做什么

Grill Loop 会围绕一份方案运行一个有状态的循环：

1. Grill 角色找出当前最高影响的未决问题。
2. Controller 将问题路由为 `FAST_PASS`、`RESEARCH`、`JUDGE` 或 `ESCALATE`。
3. 必要时生成一个候选修订稿。
4. Judge 用固定量表给最终保留的方案重新评分。
5. 状态管理器记录决策，并判断循环是否继续。

它会保留：

- 原始方案；
- 不可变的草稿快照；
- `state.json` 机器状态；
- `decisions.md` 人类可读裁决日志；
- 明确的终态、未决升级项和否决项。

## 安装

### 一键安装

```bash
curl -fsSL https://raw.githubusercontent.com/jcanha11/grill-loop-skill/main/install.sh | bash
```

默认安装到：

```text
$HOME/.agents/skills/grill-loop
```

如果你的环境仍使用 legacy 的 Codex skills 目录，可以指定安装位置：

```bash
curl -fsSL https://raw.githubusercontent.com/jcanha11/grill-loop-skill/main/install.sh | \
  GRILL_LOOP_SKILLS_DIR="$HOME/.codex/skills" bash
```

### 手动安装

```bash
git clone https://github.com/jcanha11/grill-loop-skill.git
mkdir -p "$HOME/.agents/skills"
cp -R grill-loop-skill/grill-loop "$HOME/.agents/skills/grill-loop"
```

如果 skill 没有立即出现，重启 Codex 或开启一个新 session。

### 让 Codex 自然语言安装

把下面这段发给 Codex：

```text
Use $skill-installer to install the skill folder from
https://github.com/jcanha11/grill-loop-skill/tree/main/grill-loop
into my user skills directory. Then verify it by running:
python3 -m unittest grill-loop/scripts/test_grill_state.py
```

如果你的 Codex 环境不支持通过 `$skill-installer` 从仓库安装 skill，就发这个：

```text
Clone https://github.com/jcanha11/grill-loop-skill, copy the grill-loop folder
to $HOME/.agents/skills/grill-loop, and run its unit tests.
Do not publish or modify any of my other files.
```

### 让其他 Agent 安装

如果对方支持 open Agent Skills 格式：

```text
Install the Agent Skill at:
https://github.com/jcanha11/grill-loop-skill/tree/main/grill-loop

Preserve the SKILL.md file, references/, scripts/, tests/, and agents/openai.yaml.
Install it as a user-level skill named grill-loop.
After installation, run the Python unittest suite in grill-loop/scripts/test_grill_state.py.
```

如果对方不支持原生 skills，就让它 clone 仓库，并把 `grill-loop/SKILL.md` 当成工作流指令文件使用。

## 使用

### Supervised / 监督模式

适合你希望系统自动处理简单问题，但关键未知仍然问你的场景。

```text
Use $grill-loop in supervised mode to stress-test and improve this plan.
```

### Autonomous / 自动模式

适合你明确授权 subagents 连续运行，并允许系统采用保守可逆分支继续推进的场景。

```text
Use $grill-loop in autonomous mode with specialized subagents to improve this plan.
You may choose conservative reversible branches, but keep unresolved business decisions in the final escalation list.
```

自动模式不能编造缺失事实。如果没有安全的保守分支，应该停止并留下未决项，而不是假装确定。

## 仓库结构

```text
grill-loop/
  SKILL.md
  agents/openai.yaml
  references/
    role-contracts.md
    rubric.md
  scripts/
    grill_state.py
    test_grill_state.py
  tests/
    fixtures/flawed-plan.md

grill-loop-visual/
  index.html

install.sh
```

## 验证

运行确定性的状态管理测试：

```bash
python3 -m unittest grill-loop/scripts/test_grill_state.py
```

期望结果：

```text
Ran 12 tests
OK
```

## 如何评估它是否真的有用

不要用“概念是否优雅”判断它，要用工作流指标判断。

建议观察：

- 人被打断次数：每次评审需要问用户多少个问题；
- 完成率：循环是否能达到 `passed` 或 `conditional_pass`；
- 质量提升：baseline 到 final 的评分提升；
- 审计性：另一个人是否能看懂每个分支为什么接受、拒绝或升级；
- 错误自动率：自动模式是否把本该升级的问题错误地自行判断；
- 决策耗时：从输入方案到最终产物需要多久。

最小成功标准：相比 `grill-me`，用户花更少的主动注意力，同时拿到更清晰、评分更高、可复盘的方案。

## 状态

这是一个实验性 v0.1 skill，适合本地使用和方法探索。自动模式应被视为保守的方案评审助手，不代表它有权限上线、花预算、修改生产系统或做不可逆业务决策。

## License

MIT。见 [LICENSE](LICENSE)。
