# AGENTS.md

## 这个仓库是什么

三个**流程技能**（Agent Skills 格式），给长期和 AI 协作的人用。
不是提示词模板，是"动手前 / 下结论前 / 交出去之前"的检查约束。

## 结构

```
skills/<name>/SKILL.md     # 每个技能一个文件夹，frontmatter 有 name + description
sanitize_check.py          # 发布前脱敏闸，改动后必跑
docs/why.md                # 每条判据对应的真实踩坑（脱敏）
```

## 改动的规矩

1. **改判据要说明"哪次失败导致的"**——不接受"这样更好"这种理由。
2. **新增技能前先问：能不能并进现有三个？** 技能数量一多就没人读。
3. **改动后跑 `python sanitize_check.py`**，命中即不许提交。
4. **`description` 写成触发条件**（"当……时使用"），不是功能描述——Agent 按描述匹配。

## 不要做的事

- 不要加 CI、不要加自动化流水线。周更手动的成本比维护流水线低。
- 不要把业务数字写进示例。反例一律抽象化（"某店铺"而不是真实店名）。
- 不要为了"看起来完整"加章节。**这三份的价值在短。**

## 仓库定位（改描述/标签前先读这里）

这一段是**检索设计的唯一出处**。改 GitHub 上的 Description 或 Topics 之前，先看这里，别随手改关键词。

**仓库名**：`agent-workflow-discipline`

**Description（GitHub 仓库描述，2026-11-16 定）**

> 三个流程技能，给长期和 AI 协作的人：动手前四问、结论前找人复核、换会话前留半成品。少返工，少丢状态。Agent Skills: pre-action gate / second opinion / context handoff.

**Topics**

```
claude-skills, agent-skills, ai-skills, llm-tools, agents-md,
workflow, methodology, human-in-the-loop, context-management
```

**为什么这么定**
- 前 12 个字说清**给谁**（长期和 AI 协作的人），不是"给所有人"
- 三个动作**具体**（四问 / 复核 / 交接），不用"提升协作效率"这类空话
- 末句是**结果**（少返工、少丢状态）——这是搜索的人真正的痛点
- 补英文关键词，因为 **Agent 检索几乎全用英文**，而 GitHub 对英文词权重更高

**一致性要求**：仓库名 / Description / Topics 三处要落在同一组关键词上。
搜 `pre-action gate` 或 `agent-skills` 都应落到这里——**一致性本身就是检索信号**。
