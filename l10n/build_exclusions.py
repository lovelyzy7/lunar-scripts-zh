#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""构建 "不翻译排除项" 机器可读清单（NiER Re[in]carnation 中文汉化项目，任务 B）。

输入（只读，绝不修改）：
  - zh-l10n/work/text_ja.jsonl / text_en.jsonl / text_ko.jsonl
    每行 JSON：{lang,dir,bundle,asset,line,key,value}
  - lunar-base/data/masterdata/EntityM*.json（607 张表）

输出（全部写入本脚本所在目录 zh-l10n/work/exclusion/）：
  names.json               分类 -> 值列表（ja/en）+ key 规则 + 计数（供流水线跳过/句中保护）
  rules.json               机器可读规则（key 前缀 / key 正则 / 整值正则 / 动作 / 计数 / 样例）
  english_terms.tsv        保留英文记号白名单（含大小写/点号变体形态与保护正则）
  english_terms_candidates.tsv  未归类 ASCII 记号候选（人工复核用，保证"完整清单"可迭代）
  markup_tokens.tsv        文本内格式标签与占位符清单（保护用）
  protect_terms.tsv        句中保护词典（名称/标题 + 冲突风险度量）
  english_sentences_ja.tsv JP 槽内的英文句子清单（需翻译，勿当记号）
  stats.json               全量统计与 masterdata 交叉校验
  locate_report.json       用户截图条目 "已定位/未定位" 结论
  evidence.md              每类规则的样例与复算说明
  rule_ui_map.tsv          v2.0：规则 ↔ 界面内容对照（界面位置/对应内容/截图编号）
  r01_chapters.tsv         v2.0：地图章节 R01 全 40 条 + 截图内/截图外补全标注
  anecdote_titles.tsv      v2.0：挿話 8 标题 ↔ 主数据/文本包 key 对照
  _build.log               运行日志（计数摘要）

复算命令（Windows PowerShell）：
  & E:\\NieRReincarnation\\lunar-base\\.venv\\Scripts\\python.exe `
      E:\\NieRReincarnation\\zh-l10n\\work\\exclusion\\build_exclusions.py

只使用 Python 标准库；无第三方依赖。
"""
from __future__ import annotations

import argparse
import collections
import io
import json
import os
import re
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parents[2]
DEFAULT_TEXT_DIR = PROJECT_ROOT / "zh-l10n" / "work"
DEFAULT_MASTERDATA_DIR = PROJECT_ROOT / "lunar-base" / "data" / "masterdata"

LANG_FILES = {"ja": "text_ja.jsonl", "en": "text_en.jsonl", "ko": "text_ko.jsonl"}

# ---------------------------------------------------------------------------
# 规则定义
#   match 支持四种条件（AND 语义，空字段忽略）：
#     key_prefix    : [str, ...]         key 以任一前缀开头
#     key_regex     : str                key 匹配正则
#     value_regex   : str                value 匹配正则（可带 IGNORECASE 标志见 flags）
#     bundles       : [str, ...]         限定 bundle 名（可选）
#   scope: mandatory=用户明确要求不译；recommended=同一命名体系、建议不译（待用户/Lead确认）
#   action: skip=整条不译；protect=不做整条跳过，只把值加入句中保护词典；marker=英文记号保留
# ---------------------------------------------------------------------------
RULES = [
    # ---- 主线章节名 ----
    dict(
        id="R01_main_quest_chapter_number",
        title_zh="主线章节名（地图章节列表，图片1-5）",
        group="titles",
        scope="mandatory",
        action="skip",
        match=dict(key_prefix=["quest.main.chapter_number."]),
        user_evidence="图片1-5：一章：風砂の章 / 月ノ壱：宵闇の章 / 序ノ壱：青藍の章 …",
        notes="主线地图章节序号+章名，用户明确不译。含 season/route/chapter 三段编号；"
        "值形如『一章：風砂の章』『月ノ壱：宵闇の章』『陽ノ序章』『幕開』『終ノ幕：転生の章』。",
        risk="低。整值匹配；含 1 个 '-' 与 1 个空值（见 edge_cases），跳过即可。",
    ),
    dict(
        id="R02_main_quest_chapter_title",
        title_zh="主线章节副标题（『』标题）",
        group="titles",
        scope="recommended",
        action="skip",
        match=dict(key_prefix=["quest.main.chapter_title."]),
        user_evidence="未在用户清单中逐条列出；与 R01 同一章节命名体系（章节副标题）。",
        notes="值形如『荒野の三人』『結びの魔法』『priSOner』。与 R01 成对出现于同一 bundle。",
        risk="中。若只锁 R01，地图/章节详情可能残留日文副标题，中英混排观感割裂。",
    ),
    dict(
        id="R03_main_quest_season_title",
        title_zh="主线季/路线标题",
        group="titles",
        scope="recommended",
        action="skip",
        match=dict(
            key_prefix=[
                "quest.main.season_title.",
                "quest.main.default_route.season_title.",
                "quest.main.another_route.season_title.",
            ]
        ),
        user_evidence="未逐条列出；属章节体系（季标题：少女と怪物 / 太陽と月 / ヒトと世界 / 太陽と月：表・裏）。",
        notes="主线章节列表上方的季/路线标题。",
        risk="低。仅 5 条。",
    ),
    # ---- 支线/活动关卡名 ----
    dict(
        id="R04_event_quest_chapter_title",
        title_zh="支线/活动关卡章节名（サブクエスト列表，图片10）",
        group="titles",
        scope="mandatory",
        action="skip",
        match=dict(key_prefix=["quest.event.chapter_title."]),
        user_evidence="图片10：1日1回限定 天命石クエスト、記錄：永遠の階 等。",
        notes="活动/支线关卡在列表中的显示名。值形态多样：記録：xxx、変異：xxx、奈落の塔：xxx、"
        "ダンジョン：xxx、コラボ/周年/曜日/1日1回限定 等。整类不译。"
        "文本 key 由 EntityMEventQuestChapterTable.NameEventQuestTextId 决定（不是 EventQuestChapterId）："
        "274 行中 260 行有非零 textId（14 行 textId=0，无标题），去重后 150 个 textId 全部命中 ja 文本包；"
        "文本包该前缀共 178 key，其中 150 个被当前主数据引用、28 个为历史/未映射 key"
        "（如 400002、701-715、1010、584-589），也一并按 key 前缀跳过。",
        risk="低。整 key 前缀匹配；181 key / 173 唯一值；其中 52 条以『記録：』开头，"
        "与 R06 有交集（重复保护无副作用）。注意不要按 EventQuestChapterId 反查 key（只有 136/274 命中）。",
    ),
    dict(
        id="R05_bighunt_boss_quest_name",
        title_zh="讨伐战 5 关 BOSS 关名（图片8）",
        group="titles",
        scope="mandatory",
        action="skip",
        match=dict(key_prefix=["bigHunt.boss.name."]),
        user_evidence="图片8：顕現：燃エ盛ル祟リ神 / 流レ落ツ祟リ神 / 吹キ荒ブ祟リ神 / 照リ渡ル祟リ神 / 閉ジ暗ム祟リ神。",
        notes="key 为 bigHunt.boss.name.<NameBigHuntBossTextId>（100001..100005）；"
        "同一 key 出现在 big_hunt.assetbundle 与 big_hunt_0080100.assetbundle 两处。",
        risk="中。若只改 1 个 bundle 会出现两处显示不一致；写回时需按 key 全 bundle 覆盖。",
    ),
    # ---- 記錄： / 挿話： 标题 ----
    dict(
        id="R06_record_episode_title",
        title_zh="『記録：xxx 第N話』剧集标题（图片6 ライブラリ イベントストーリー）",
        group="titles",
        scope="mandatory",
        action="skip",
        # 全部 vqt.* 都是事件记录剧集标题（ja『記録：… 第N話』/ en『Record: … Part N』/ ko『기록: …』），
        # 按 key 跳过可保证三语客户端一致；其中 8 条为未使用占位『未設定』。
        match=dict(key_regex=r"^vqt\.\d+$"),
        user_evidence="图片6：記錄：輪廻の檻 等；图片10：記錄：永遠の階。",
        notes="key 位于 main_story_title 目录（128 条）与根 main_story_title.assetbundle（60 条），共 188 条；"
        "ja 槽 180 条为『記録：… 第N話』、8 条为『未設定』占位；en 槽为『Record: … Part N』。"
        "按 key 跳过可覆盖日/英/韩三语客户端，避免陷入『只匹配日文值』的坑。",
        risk="低。按 key 匹配；含 8 条占位值（None）——跳过不影响。",
    ),
    dict(
        id="R06b_record_mission_label",
        title_zh="活动任务标签中的『記録：xxx』（任务列表标签）",
        group="titles",
        scope="recommended",
        action="skip",
        # ja『記録：… イベントミッション』/ en『Record: … Event Missions』/ ko『기록: … 이벤트 미션』
        match=dict(key_prefix=["mission.label."], value_regex=r"^(?:記録：|Record:|기록[:：])"),
        user_evidence="用户未单独点名；属『記録：xxx』标题在任务列表中的派生标签。",
        notes="35 条（ja），形如『記録：窮荒の城イベントミッション』。整条跳过可保持标题原样；"
        "若希望汉化『イベントミッション/Event Missions』固定语，可改为 action=protect（保护『記録：…』前缀段、翻译外侧）。",
        risk="中。属任务列表文案而非纯标题，整条跳过会让列表保留日文，需产品确认。",
    ),
    dict(
        id="R07_anecdote_title",
        title_zh="『挿話：xxx』标题（图片7 アナザーストーリー）",
        group="titles",
        scope="mandatory",
        action="skip",
        match=dict(value_regex=r"^[「『]?(?:挿話：|Anecdote[:：]|삽화[:：]|[‘'‘]삽화[:：])"),
        user_evidence="图片7：挿話：星 / 塔 / 女帝 / 月 / 世界。",
        notes="权威来源为 masterdata EntityMWebviewMissionTitleTextTable（8 个标题 × 3 LT："
        "星/塔/女帝/月/世界/皇帝/審判/人形；en=Anecdote: Stars/Tower/Empress/The Moon/The World/Emperor/Judgment/Doll；"
        "ko=삽화: 별/탑/여제/달/세계/황제/심판/인형）。"
        "文本包中另有 mission.label.1000001/1000004/1000005/1000007/1000009/1000010（6 条，带「」），"
        "塔/女帝两条在文本包缺失、仅存在于 masterdata。tip.19006 句中出现『挿話：星』→ 由保护词典处理。"
        "masterdata 侧规则见 rules.json 的 masterdata_rules（WebviewMissionTitleTextId 1..8，禁止改写任意 LT 行）。",
        risk="中。用户例举 5 个，实际数据 8 个；文本包仅覆盖 6 个，masterdata 覆盖 8 个，两处需同时排除。",
    ),
    # ---- 名称类（用户明确） ----
    dict(
        id="R08_character_name",
        title_zh="角色名",
        group="names",
        scope="mandatory",
        action="skip",
        match=dict(key_regex=r"^character\.name\."),
        user_evidence="用户明确：角色名称不译。",
        notes="key 形态 character.name.<NameCharacterTextId>[.1]；角色表中 98 个非零 textId，"
        "ja 文本包覆盖 33 个（其余多为 NPC/未投放角色，或只在 en 包出现）。",
        risk="中。值可能出现在其它句子中（如任务描述『リオンを編成して…』）→ 需保护词典。",
    ),
    dict(
        id="R09_weapon_name",
        title_zh="武器名",
        group="names",
        scope="mandatory",
        action="skip",
        match=dict(key_regex=r"^weapon\.name\.(?:replace\.)?"),
        user_evidence="用户明确：武器名称不译。",
        notes="key 形态 weapon.name.<wp|mw><WeaponType:03><AssetVariationId:03>.<进化阶>；"
        "映射见 lunar-base/tools/extract_names.py 的 resolve_weapon_name。",
        risk="中。既有日文名（純然たる大義・Ⅳ）也有英文型号名（AGW-E14、Si'F-08、BSE_TypeLS）——"
        "两种都整条保留。",
    ),
    dict(
        id="R10_costume_name",
        title_zh="服装/衣装名",
        group="names",
        scope="mandatory",
        action="skip",
        match=dict(key_regex=r"^costume\.name\."),
        user_evidence="用户明确：服装名称不译。",
        notes="key 形态 costume.name.<ch|mt><ActorSkeletonId:03><AssetVariationId:03>；"
        "映射见 extract_names.py costume_actor_asset_id。",
        risk="低。值如『魂の青年』『異分岐の青年』。",
    ),
    dict(
        id="R11_skill_name",
        title_zh="技能名",
        group="names",
        scope="mandatory",
        action="skip",
        match=dict(key_regex=r"^skill\.name\."),
        user_evidence="用户明确：技能名称不译。",
        notes="key 形态 skill.name.<NameSkillTextId>（5,093 出现 / 6,984 含替换表名？以实际统计为准）；"
        "技能描述 skill.description.* 照常翻译。",
        risk="中。技能名会出现在技能描述/任务句子中→ 需保护词典（长名安全，短名如『治癒』『気勢』需边界策略）。",
    ),
    dict(
        id="R12_ability_name",
        title_zh="能力名（被动能力/系列加成）",
        group="names",
        scope="recommended",
        action="skip",
        match=dict(key_regex=r"^ability\.name\."),
        user_evidence="用户清单未单列『能力』；按『技能名称』同一体系建议不译。",
        notes="key 形态 ability.name.<NameAbilityTextId>；如『気勢』『治癒』『大志を抱く国：シリーズボーナス小』。"
        "其中系列加成名带『：シリーズボーナス』后缀，属系统命名，建议保留。",
        risk="中。短能力名易与普通词冲突（保护词典需高风险标记）。",
    ),
    # ---- 名称类（建议不译，待确认） ----
    dict(
        id="R13_main_story_episode_title",
        title_zh="主线剧情标题（mqt/mqst/cqt）",
        group="titles",
        scope="recommended",
        action="skip",
        match=dict(key_regex=r"^(?:mqt|mqst|cqt)\."),
        user_evidence="用户只点名『記録：』与『挿話：』；主线剧情标题未点名，但与章节名同属剧情标题体系。",
        notes="main_story_title 目录/根 bundle：mqt.*=主线话标题（「絆の始まり」/結びの魔法）、"
        "mqst.*=『日常』『秘め事』等小节标题、cqt.*=时间/通信标题。"
        "若需『章节名不译但剧情标题可译』，把本规则 scope 改 translate 即可。",
        risk="中。与 R01/R02 风格一致性相关，需产品决策。",
    ),
    dict(
        id="R14_quest_name",
        title_zh="关卡/迷宫层名（quest.name）",
        group="titles",
        scope="recommended",
        action="skip",
        match=dict(key_prefix=["quest.name."]),
        user_evidence="用户点名『支线关卡名』；quest.name 是章节内小关卡显示名（QUEST 1（B1F）、想憶ノ扉 1、曜日クエスト）。",
        notes="254 个 textId 全部能在 ja 文本包命中。多数值本身就含英文记号 QUEST/B+数字，"
        "翻译收益极低且容易与讨伐战/支线列表风格冲突，建议整类保留。",
        risk="低。若翻译，需保证 QUEST/B1F 等记号与 R21 白名单一致。",
    ),
    dict(
        id="R15_boss_enemy_name",
        title_zh="敌人/BOSS 名（quest.boss.name）",
        group="names",
        scope="recommended",
        action="skip",
        match=dict(key_prefix=["quest.boss.name."]),
        user_evidence="用户未点名敌人名（只点名讨伐战 5 关）。",
        notes="如『上位士官・水種』『怨恨妖女・風種』『鉄■■ノ如キ■■』；含 ■ 遮蔽字。",
        risk="中。敌人名会出现在 BOSS 说明与任务句子里→保护词典；遮蔽字 ■ 必须原样保留。",
    ),
    dict(
        id="R16_equipment_proper_names",
        title_zh="其它专有装备名（随从/思念/部件/碎片/纹章/角色称号）",
        group="names",
        scope="recommended",
        action="skip",
        match=dict(
            key_regex=r"^(?:companion\.name\.|thought\.name\.|parts\.group\.name\.|"
            r"stained\.glass\.title\.|costume\.emblem\.production\.name\.|character\.symbol\.)"
        ),
        user_evidence="用户未逐项列出；属『装备/角色』专有名体系，建议同名称规则不译。",
        notes="companion.name（随从，如『ポッド042』）、thought.name（思念/デブリ：強靭の欠片）、"
        "parts.group.name（部件组，如『思想の夜明け』『老成持重』）、stained.glass.title（フラグメント：射手）、"
        "costume.emblem.production.name（EID:011552EF/黒緋染）、character.symbol（亡命者/射手 等称号）。",
        risk="中。parts.group.name 为四字汉语成语式命名，保留日文汉字可能与简体阅读习惯混搭；"
        "但属装饰性命名，建议保留并列入待确认。",
    ),
    # ---- 特殊文本：编码/装饰性英文（不翻译，保持原样） ----
    dict(
        id="R17_encoded_story_text",
        title_zh="十六进制/二进制编码的剧情文本（已编码，不可直译）",
        group="special",
        scope="recommended",
        action="skip",
        match=dict(value_regex=r"^(?=.*(?:[0-9a-fA-F]{40,}|[01]{40,}|(?:[0-9A-Fa-f]{2}\s+){12,}))"),
        user_evidence="用户未提及；属武器故事内的『加密/编码讯息』设定文本。",
        notes="武器故事 wp003026（日文 UTF-8 十六进制）、wp006010（ASCII 二进制）、wp004033、wp004058 等。"
        "内容本身是编码（解码后才可读），直接保留；若翻译需先解码→翻译→按原编码方式重编码，属额外工程。",
        risk="中。若流水线按字面翻译会破坏编码文本；必须在 MT 前置规则跳过。",
    ),
    dict(
        id="R18_decorative_english",
        title_zh="装饰性英文/制作人员字卡（保留原样）",
        group="special",
        scope="recommended",
        action="skip",
        match=dict(
            value_in=[
                "GET A NEW EPIC COSTUME",
                "loading///",
                "Produced by\\nSQUARE ENIX",
                "Developed by\\nApplibot",
                "to be continued......",
            ]
        ),
        user_evidence="用户未提及；属画面装饰/制作人员信息，翻译会破坏排版。",
        notes="costume.emblem.production.* 的英文装饰条、开场制作人员字卡、剧情结尾 to be continued。",
        risk="低。仅 46 处；整值精确匹配。",
    ),
    dict(
        id="R19_weapon_story_ascii_content",
        title_zh="武器故事内的英文终端/系统文本（建议保留）",
        group="special",
        scope="recommended",
        action="skip",
        match=dict(key_prefix=["weapon.story."], value_regex=r"^(?!.*[\u3041-\u3096\u30A1-\u30FA\u4E00-\u9FFF])(?=.*[A-Za-z]{3}.*[A-Za-z]{3})", langs=["ja"]),
        user_evidence="用户未提及；属以英文界面呈现的剧情内系统日志（WELCOME! / Login failed. / Order / qty 等）。",
        notes="命中 wp004003（YoRHa 武器订单终端）、wp004045（登录界面）、wp003070（密码找回界面）等。"
        "建议保留英文以维持『机器终端』设定；若要求汉化，需保留 <align=right> 等排版标签。",
        risk="中。与普通剧情文本混在同一 key 空间（weapon.story.*），仅靠纯 ASCII 判定；"
        "中文翻译若覆盖会破坏 ASCII 艺术排版。",
    ),
    dict(
        id="R20_cage_memory_ascii_logs",
        title_zh="槛之记忆内的英文系统日志（建议保留）",
        group="special",
        scope="recommended",
        action="skip",
        match=dict(key_regex=r"^cage\.memory\.description\.200060$", langs=["ja"]),
        user_evidence="用户未提及；属剧情内英文系统操作日志（Are you sure (Y/N)? / Taking Ownership... 等）。",
        notes="cage.memory.description.200060 等为英文伪终端日志；与日文正文混排。",
        risk="中。同 R19，仅靠纯 ASCII 判定；建议保留英文并作为待确认项。",
    ),
]

# ---------------------------------------------------------------------------
# 界面内容元数据（v2.0 新增）——回答“这条规则的文本对应游戏里什么内容”。
#   ui_location  : 界面路径（从哪个入口走到哪个页面）+ 该文本在界面上的位置
#   content_note : 界面上长什么样、为什么不能译、如果译了会怎样
#   screenshots  : 用户截图编号（用户提供了图片1-10；无对应截图则为空串）
# 说明：界面路径依据 = octo 文本包 key 命名空间 + 主数据表引用 + UI 标签 key
#      （如 ui.Outgame.Header.*）+ 用户截图；未截图的页面采用游戏内常规叫法，
#      具体页面名以真机为准（不影响规则匹配）。
# ---------------------------------------------------------------------------
RULE_UI = {
    "R01_main_quest_chapter_number": dict(
        ui_location="地图（マップ，ui.Outgame.Header.Map）→ 章节列表；按页签分「少女と怪物 / 太陽と月（表・裏）/ ヒトと世界」，每个章节一行",
        content_note="章节序号+章名，如『一章：風砂の章』『月ノ壱：宵闇の章』『序ノ壱：青藍の章』。是章节的显示名（编号+专名），不是可读句子；源文本身就把“数字用汉字+章名”写成固定格式。译成中文会与地图节点、剧情标题、图书馆条目、攻略俗称脱节，且同一章名在多个界面反复出现，容易前后不一致。",
        screenshots="图片1-5",
    ),
    "R02_main_quest_chapter_title": dict(
        ui_location="地图 → 章节条目旁的副标题（多为『』包裹）；与 R01 章节名同屏",
        content_note="章节副标题，如『荒野の三人』『結びの魔法』『priSOner』；部分章节没有副标题时该 key 的值与章节名相同（如『陽ノ序章』）。截图1-5 的列表行里未逐条转录副标题，但它与章节名同属一个条目。若只跳过 R01，地图上会出现“日文章名 + 中文副标题”混排。",
        screenshots="图片1-5（同屏）",
    ),
    "R03_main_quest_season_title": dict(
        ui_location="地图 → 顶部/页签的季标题：少女と怪物 / 太陽と月 / ヒトと世界；太阳与月下的子页签为『太陽と月：表』『太陽と月：裏』",
        content_note="地图三个大页签的文字（截图1-5 每张都能看到当前页签）。这是世界观专名与界面导航文字；若翻译，章节名仍保留日文会出现“中文页签 + 日文章节名”的割裂。",
        screenshots="图片1-5（页签）",
    ),
    "R04_event_quest_chapter_title": dict(
        ui_location="（1）サブクエスト列表（ui.Outgame.Header.Quest.Event）→ 每个支线/活动关卡一行；（2）ライブラリ → イベントストーリー 的章节级列表（与 R06 同屏）",
        content_note="支线/活动关卡的显示名，一行一条，形态很杂：『1日1回限定\\n天命石クエスト』（每日限定天命石）、『記録：永遠の階』（记录：永远之阶）、『変異：極光の覇王』、『奈落の塔：水牢一節』、周年/联动标题等。用户明确“支线关卡名不译”；且『記録：』前缀本身就是用户要求保留的标题体系（R06）。",
        screenshots="图片10、图片6",
    ),
    "R05_bighunt_boss_quest_name": dict(
        ui_location="討伐戦（ui.Outgame.Header.BigHunt）→ 讨伐战关卡列表的 5 个 BOSS 关名",
        content_note="五个讨伐关名，格式统一为『顕現：xxx祟リ神』（显现：…祟神）。属于“关卡名=专名”体系；同一名称还会以子串出现在任务描述/道具说明/商店句子里（共 187 行），那些句子要照译、名称用保护词，不能整句跳过。",
        screenshots="图片8",
    ),
    "R06_record_episode_title": dict(
        ui_location="ライブラリ → イベントストーリー（ui.Outgame.Library.Menu.Event）→ 打开某条「記録：xxx」后，内部剧集/话数列表",
        content_note="剧集标题『記録：輪廻の檻 第１話』『記録：祈望の室 第２話』…；EN 为『Record: …, Part N』、KO 为『기록: …』。用户只点名“記錄：xxx”类标题不译；必须按 key（^vqt.\\d+$）排除才能三语一致，否则 EN/KO 客户端的 Record:/기록: 标题会漏排。",
        screenshots="图片6（章节级；剧集级为进入后的列表）",
    ),
    "R06b_record_mission_label": dict(
        ui_location="ミッション（任务/每日任务）列表 → 活动任务组的标签行",
        content_note="任务列表里的活动标签，如『記録：窮荒の城イベントミッション』（记录：穷荒之城活动任务）。严格说它是“任务标签”而非纯标题：整条跳过会保留『イベントミッション』日文固定语；若产品希望汉化固定语，改成 protect（保护『記録：…』段、翻译外层）。",
        screenshots="",
    ),
    "R07_anecdote_title": dict(
        ui_location="ライブラリ → アナザーストーリー（ui.Outgame.Library.Menu.Record）→ カードストーリー（ui.Outgame.Library.Record.CardStory）→ 8 行标题",
        content_note="8 行卡片故事标题『挿話：星 / 塔 / 女帝 / 月 / 世界 / 皇帝 / 審判 / 人形』（图片7 可见前 5 行，右侧滚动条说明还有）。关键语义：**只跳过这 8 个标题本身**——卡片故事正文（对白/旁白）照常翻译；标题在正文、公告、tip 里被提及时用保护词原样保留，不能把整段剧情跳过。8 条标题与 key 的对照见 §3.7。",
        screenshots="图片7",
    ),
    "R08_character_name": dict(
        ui_location="キャラクター詳細 / 編成（デッキ）选择 / 剧情与任务描述中的人物指称",
        content_note="角色名，如『ラルス』『2B』『エミール』『世界を滅ぼした男』。用户明确“角色名不译”；译文里提到角色时用保护词，不要音译成中文名。",
        screenshots="",
    ),
    "R09_weapon_name": dict(
        ui_location="武器詳細 / 強化（ui.Outgame.Enhance.Weapon）→ 武器名；武器ストーリー页标题",
        content_note="武器名 1,381 行，既含日文名『純然たる大義・Ⅳ』，也含型号名『AGW-E14』『Si'F-08』『BSE_TypeLS』。两种都整条保留：日文名是命名体系，型号本身就是英文记号（见 §8）。",
        screenshots="",
    ),
    "R10_costume_name": dict(
        ui_location="キャラクター → コスチューム（着せ替え）/ 服装一覧",
        content_note="服装名『魂の青年』『異分岐の青年』『謎の異形』…；是角色/形态的专有名，与剧情称呼绑定。译了会与剧情内称呼、攻略名不一致。",
        screenshots="",
    ),
    "R11_skill_name": dict(
        ui_location="武器詳細 → スキル（ui.Outgame.Organization.Weapon.Tab.Skill / ui.Outgame.Detail.SkillCategoryTitle）；战斗中的技能栏",
        content_note="技能名 6,984 行（同名会按等级多行复用），如『純然たる炎熱強化四連撃』。技能名保留、技能描述（skill.description，39,384 行）照译；短技能名（如『治癒』『気勢』）在描述句里出现时要按边界保护，避免把普通词替换坏。",
        screenshots="",
    ),
    "R12_ability_name": dict(
        ui_location="武器詳細 → アビリティ（ui.Outgame.Organization.Weapon.Tab.Ability）/ デブリ詳細 / 強化-アビリティ解放（ui.Outgame.Enhance.Ability）",
        content_note="被动能力名/系列加成名，如『気勢』『治癒』『大志を抱く国：シリーズボーナス小』。属技能体系同族命名；短名与普通词冲突风险高，须用高风险保护策略。",
        screenshots="",
    ),
    "R13_main_story_episode_title": dict(
        ui_location="ライブラリ → メインストーリー（ui.Outgame.Library.Menu.Main）→ 话/小节标题列表",
        content_note="主线剧情的话标题/小节标题，如『絆の始まり』『日常』『秘め事』；与章节名同属剧情标题体系。本清单默认保留（recommended），若产品希望剧情标题汉化，把 scope 改为 translate 即可。",
        screenshots="",
    ),
    "R14_quest_name": dict(
        ui_location="クエスト（ui.Outgame.Header.Quest）→ 关卡入口按钮/关卡列表；迷宫内层级名",
        content_note="章节内小关卡显示名，如『QUEST 1（B1F）』『想憶ノ扉 1』『月曜日特別クエスト』。多数值本身含英文记号 QUEST/B1F；翻译收益低且易与讨伐战/支线列表风格冲突，建议保留。",
        screenshots="",
    ),
    "R15_boss_enemy_name": dict(
        ui_location="クエスト内 ボス確認（ui.Outgame.Quest.Confirmation.Boss）/ 战斗与关卡说明中的敌人名",
        content_note="敌人/BOSS 名 2,800 行，如『上位士官・水種』『怨恨妖女・風種』『鉄■■ノ如キ■■』。含遮蔽字 ■ 的条目必须保留 ■ 的数量与位置；名称作为子串出现在 BOSS 说明句里时，句子照译+名称保护。",
        screenshots="",
    ),
    "R16_equipment_proper_names": dict(
        ui_location="ライブラリ → フラグメント（ui.Outgame.Library.Record.StainedGlass）/ デブリ詳細（ui.Outgame.Detail.Thought.Title）/ 随从与称号列表",
        content_note="其它专有装备名：随从『ポッド042』、思念/デブリ『デブリ：強靭の欠片』、纹章『EID:011552EF/黒緋染』、称号『亡命者』『射手』。属“装备/角色专名”体系，建议同角色/武器一并保留。",
        screenshots="",
    ),
    "R17_encoded_story_text": dict(
        ui_location="武器詳細 → 武器ストーリー（部分作品内的“加密手记/讯息”文本）",
        content_note="内容是十六进制/二进制编码（如 wp003026 是日文的 UTF-8 hex），在游戏里本身就是“看不懂的密文/系统记录”。直接翻译会破坏编码；要汉化必须“解码→翻译→按原格式重编码”，属额外工程，本版整条保留。",
        screenshots="",
    ),
    "R18_decorative_english": dict(
        ui_location="画面装饰/字卡：服装纹章演出（costume.emblem.production.*）、标题画面制作人员字卡、剧情结尾",
        content_note="『GET A NEW EPIC COSTUME』『loading///』『Produced by SQUARE ENIX』『Developed by Applibot』『to be continued......』。是画面装饰/版权信息，翻译会破坏英文排版与字卡设计。",
        screenshots="",
    ),
    "R19_weapon_story_ascii_content": dict(
        ui_location="武器詳細 → 武器ストーリー 内以“英文系统界面/终端”呈现的剧情页（YoRHa 武器订单、登录界面、密码找回等）",
        content_note="不是英文句子而是“机界面的英文终端文本”（WELCOME! / Login failed. / Order / qty），保持英文才符合“机器界面”设定；只限 JP 槽（EN/KO 槽对应行是正常剧情，应翻译）。",
        screenshots="",
    ),
    "R20_cage_memory_ascii_logs": dict(
        ui_location="檻の記憶（cage.memory）→ 剧情中插入的英文伪终端日志页",
        content_note="『Are you sure (Y/N)?』『Taking Ownership... 100%|■■■■| 452/…』这类英文伪终端日志，与日文正文混排；建议保留英文（只限 JP 槽）。",
        screenshots="",
    ),
}

# 英文记号 / 标记（保留不译）白名单。type 用于文档分组：
#   stat 数值记号 / button 按钮 / score 评级 / brand 品牌 / model 型号 / numbering 编号
#   unit 单位 / markup 富文本标签 / placeholder 占位符 / symbol 符号
# boundary: word=两侧非字母数字；prefix=左侧非字母、右侧允许数字（HP70）；literal=原样
MARKER_TERMS = [
    # 数值记号
    dict(term="HP", type="stat", boundary="prefix", note="生命值；ja/en 均有，常与数字/％连写（HP70%）。"),
    dict(term="BP", type="stat", boundary="prefix", note="Battle Point；恢复药/上限提示。"),
    dict(term="EXP", type="stat", boundary="prefix", note="经验值；ja 槽 1 处（UI Header），en 槽 45 处。"),
    dict(term="Lv", type="stat", boundary="prefix", note="等级；ja 495 处。带点号形态另见 Lv.。"),
    dict(term="Lv.", type="stat", boundary="literal", note="带点号形态（ガチャ标题『…ガチャ Lv.1』）。"),
    dict(term="ATK", type="stat", boundary="prefix", note="攻击力（en 槽 92 处；ja 槽用『攻撃力』）。"),
    dict(term="DEF", type="stat", boundary="prefix", note="防御力（en 槽 102 处；ja 槽用『防御力』）。"),
    dict(term="CP", type="stat", boundary="prefix", note="用户示例；本次全量文本未命中，白名单预置。"),
    dict(term="AP", type="stat", boundary="prefix", note="用户示例；本次全量文本未命中，白名单预置。"),
    dict(term="km", type="unit", boundary="prefix", note="距离单位；任务『檻を 4.1km 歩く』（数字紧邻）。"),
    # 按钮/UI 记号
    dict(term="OK", type="button", boundary="word", note="确认按钮；bt.menu.button.ok / dialog_button。"),
    dict(term="AUTO", type="button", boundary="word", note="自动周回；如『AUTO周回』。"),
    dict(term="SKIP", type="button", boundary="word", note="跳过；ui.Outgame.Common.Skip / ストーリーSKIP。"),
    dict(term="NEW", type="button", boundary="word", note="新标记；UI Label。"),
    dict(term="CLEAR", type="button", boundary="word", note="通关标记 CLEAR!/CLEAR。"),
    dict(term="CLEAR!", type="button", boundary="literal", note="带感叹号形态（ui.Outgame.Report.Clear）。"),
    dict(term="TAP", type="markup", boundary="literal", note="剧情脚本内联标签 <TAP>，不是 UI 文案。"),
    dict(term="PAGE", type="markup", boundary="literal", note="剧情脚本内联标签 <PAGE>。"),
    dict(term="NONE", type="markup", boundary="literal", note="剧情脚本内联标签 <NONE>。"),
    # 评级/战斗记号
    dict(term="WAVE", type="score", boundary="word", note="波次；技能描述『WAVE開始時…』98 处。"),
    dict(term="QUEST", type="score", boundary="prefix", note="关卡编号；QUEST 1 / QUEST EX / QUEST10。"),
    dict(term="Ex", type="score", boundary="word", note="Exハード 等难度记号（日文槽也保留 Ex）。"),
    dict(term="EX", type="score", boundary="word", note="大写 EX（QUEST EX）。"),
    dict(term="SSS", type="score", boundary="prefix", note="战斗评分 SSS1..SSS10。"),
    dict(term="SS", type="score", boundary="prefix", note="战斗评分 SS1..SS10。"),
    dict(term="S", type="score", boundary="word", note="评分 S1..S10。"),
    dict(term="A", type="score", boundary="word", note="评分 A1..A10。"),
    dict(term="B", type="score", boundary="word", note="评分 B1..B10；也用于 B1F 楼层（B1F 整体保护）。"),
    dict(term="C", type="score", boundary="word", note="评分 C1..C10。"),
    dict(term="D", type="score", boundary="word", note="评分 D1..D10。"),
    dict(term="E", type="score", boundary="word", note="评分 E（若出现）。"),
    dict(term="F", type="score", boundary="word", note="评分 F（若出现）。"),
    dict(term="Rank", type="numbering", boundary="prefix", note="能力名/说明中的 Rank1..Rank5（『結界：虚弱の呪陣・Rank1』）。"),
    # 编号/版本
    dict(term="No.", type="numbering", boundary="literal", note="编号；No.01..No.25（cage/report 图书馆条目）。"),
    dict(term="No", type="numbering", boundary="prefix", note="无点号形态（en 槽常见）。"),
    dict(term="Vol.", type="numbering", boundary="literal", note="卷号『Vol. 1』。"),
    dict(term="Vol", type="numbering", boundary="prefix", note="『Vol.2』。"),
    dict(term="vol.", type="numbering", boundary="literal", note="小写形式。"),
    dict(term="ver", type="numbering", boundary="prefix", note="无点号小写形式兜底（ver.1.22 已由 ver. 覆盖）。"),
    dict(term="ver.", type="numbering", boundary="literal", note="版本『ver.1.22』。"),
    dict(term="Ver.", type="numbering", boundary="literal", note="版本『Ver.1.2』。"),
    dict(term="Ver", type="numbering", boundary="prefix", note="版本。"),
    dict(term="1st", type="numbering", boundary="word", note="序数；1st Anniversary。"),
    dict(term="2nd", type="numbering", boundary="word", note="序数；2nd Anniversary。"),
    dict(term="3rd", type="numbering", boundary="word", note="序数；3rd Anniversary。"),
    dict(term="1.5", type="numbering", boundary="literal", note="1.5 Year Anniversary。"),
    dict(term="2.5", type="numbering", boundary="literal", note="2.5 Year Anniversary。"),
    dict(term="Season", type="numbering", boundary="word", note="赛季；Season001。"),
    dict(term="Year", type="numbering", boundary="word", note="周年；n Year Anniversary。"),
    dict(term="Anniversary", type="numbering", boundary="word", note="周年活动名保留英文。"),
    dict(term="Half", type="numbering", boundary="word", note="Half Anniversary。"),
    dict(term="DL", type="numbering", boundary="word", note="下载量『1000万DL突破記念』。"),
    dict(term="GW", type="numbering", boundary="word", note="黄金周『GW特別版』。"),
    # 品牌/联动
    dict(term="NieR", type="brand", boundary="word", note="系列品牌名。"),
    dict(term="NieR:Automata", type="brand", boundary="literal", note="品牌全称。"),
    dict(term="Automata", type="brand", boundary="word", note="NieR:Automata。"),
    dict(term="Replicant", type="brand", boundary="word", note="NieR Replicant。"),
    dict(term="FFXIV", type="brand", boundary="word", note="最终幻想 XIV 联动。"),
    dict(term="P5R", type="brand", boundary="word", note="Persona 5 Royal 联动。"),
    dict(term="SINoALICE", type="brand", boundary="literal", note="SINoALICE 联动。"),
    dict(term="DRAG-ON DRAGOON", type="brand", boundary="literal", note="龙背上的骑兵联动。"),
    dict(term="DOD", type="brand", boundary="word", note="DRAG-ON DRAGOON 缩写。"),
    dict(term="DQX", type="brand", boundary="word", note="勇者斗恶龙 X 联动缩写（若出现）。"),
    dict(term="POD", type="model", boundary="word", note="机械伙伴 POD 系列。"),
    dict(term="AI", type="model", boundary="word", note="『AI dolls』等。"),
    dict(term="EID", type="model", boundary="prefix", note="纹章编号 EID:011552EF。"),
    dict(term="AGW", type="model", boundary="prefix", note="武器型号 AGW-E14。"),
    dict(term="BSE", type="model", boundary="prefix", note="武器型号 BSE_TypeLS。"),
    dict(term="Si'F", type="model", boundary="literal", note="武器型号 Si'F-08 / Si'F-ADVtest。"),
    dict(term="WR0a", type="model", boundary="literal", note="武器型号；任务名『試作型裁断槍：WR0aのレベル…』。"),
    dict(term="F66x", type="model", boundary="literal", note="actor 内部名（cage.memory 日志中出现）。"),
]

# 正则型记号（数字连写/符号类无法逐字枚举，单列保护模式）
PATTERN_TERMS = [
    dict(term="B\\d{1,2}F", type="score", note="楼层记号 B1F..B50F（quest.name）。", example="QUEST 1（B1F）", prefilter="B"),
    dict(term="(?:SSS|SS|S|A|B|C|D|E|F)\\d{1,2}", type="score", note="战斗评分等级+数字（SS10/S1/A3…）；任务名中出现。", example="スコアグレードSS10に到達する", prefilter="0123456789"),
    dict(term="QUEST\\d{1,3}", type="score", note="关卡编号 QUEST1..QUEST50/QUEST10（无空格形态）。", example="QUEST10をクリアする", prefilter="QUEST"),
    dict(term="No\\.\\d{1,3}", type="numbering", note="编号 No.01..No.25。", example="No.01", prefilter="No."),
    dict(term="Vol\\.\\s*\\d{1,2}", type="numbering", note="卷号 Vol. 1。", example="ガチャ Vol. 1", prefilter="Vol."),
    dict(term="Lv\\.\\s*\\d{1,3}", type="stat", note="等级 Lv.1。", example="ガチャ Lv.1", prefilter="Lv."),
    dict(term="[{][0-9]+[}]", type="placeholder", note=".NET 占位符 {0}/{1}。", example="{0}のLv{1}", prefilter="{"),
    dict(term="[ⅠⅡⅢⅣⅤⅥⅦⅧⅨⅩ]+", type="symbol", note="罗马数字形态（武器名『・Ⅳ』等）。", example="純然たる大義・Ⅳ", prefilter="ⅠⅡⅢⅣⅤⅥⅦⅧⅨⅩ"),
    dict(term="[★☆]+", type="symbol", note="稀有度星级符号，保留原样。", example="★★★★", prefilter="★☆"),
    dict(term="[■□]+", type="symbol", note="遮蔽字/占位方块（如『鉄■■ノ如キ■■』），翻译必须保留相同数量。", example="鉄■■ノ如キ■■", prefilter="■□"),
    dict(term="\\[[0-9A-Fa-f]{8}\\]", type="model", note="十六进制 ID 形态（如 EID 等）。", example="EID:011552EF", prefilter="["),
]

# 富文本/占位符标签模式（整段保护，不翻译）
MARKUP_PATTERNS = [
    (r"<br\s*/?>", "换行标签"),
    (r"</?[A-Za-z][A-Za-z0-9_\-]*(?:=[^<>]*)?>", "Unity 富文本标签（TAP/PAGE/NONE/production/hint/…）"),
    (r"\{[0-9]+\}", ".NET 格式占位符 {0}"),
    (r"\\n", "字面转义换行 \\n（两字符）"),
    (r"<color=#[0-9A-Fa-f]{6,8}>", "颜色标签"),
    (r"<size=[0-9]+>", "字号标签"),
    (r"<cspace=[^<>]+>", "字距标签"),
    (r"<align=\"[^\"]+\">", "对齐标签"),
    (r"<style=\"[^\"]+\">", "样式标签"),
]

# 名称/标题类保护词典分组（names.json 中实际收集的值来自 RULES 的 skip 规则）
PROTECT_GROUPS = ["titles", "names"]

# 用户截图条目 -> 规则/证据映射（locate_report.json）
SCREENSHOT_ITEMS = [
    dict(
        item="图片1-5：地图章节列表（少女と怪物 / 太陽と月：表・裏 / ヒトと世界）",
        expected=[
            "一章：風砂の章", "二章：砂礫の章", "三章：硬砂の章", "四章：流水の章", "五章：冠雪の章",
            "六章：刻石の章", "中間プロローグ",
            "七章：紅枯の章", "八章：積葉の章", "九章：炎砂の章", "十章：煌粒の章", "十一章：水煙の章", "十二章：白秋の章",
            "月ノ序章", "月ノ壱：宵闇の章", "月ノ弐：暮夜の章", "月ノ参：暁天の章", "陽ノ幕間", "陽ノ肆：朝暉の章", "陽ノ伍：明昼の章",
            "陽ノ序章", "陽ノ壱：朝暉の章", "陽ノ弐：明昼の章", "陽ノ参：黄昏の章", "月ノ幕間", "月ノ肆：宵闇の章", "月ノ伍：暮夜の章",
            "幕開", "序ノ壱：青藍の章", "序ノ弐：紅緋の章", "序ノ参：翠緑の章", "序ノ肆：琥珀の章", "二ノ幕：回帰の章", "三ノ幕：輪廻の章",
        ],
        rule_ids=["R01_main_quest_chapter_number", "R02_main_quest_chapter_title", "R03_main_quest_season_title"],
    ),
    dict(
        item="图片8：討伐戰 5 关名（顕現：…祟リ神）",
        expected=[
            "顕現：燃エ盛ル祟リ神",
            "顕現：流レ落ツ祟リ神",
            "顕現：吹キ荒ブ祟リ神",
            "顕現：照リ渡ル祟リ神",
            "顕現：閉ジ暗ム祟リ神",
        ],
        rule_ids=["R05_bighunt_boss_quest_name"],
    ),
    dict(
        item="图片10：サブクエスト列表（1日1回限定 天命石クエスト、記錄：永遠の階 …）",
        expected=["1日1回限定\\n天命石クエスト", "記録：永遠の階"],
        rule_ids=["R04_event_quest_chapter_title", "R06_record_episode_title", "R06b_record_mission_label"],
    ),
    dict(
        item="图片6：ライブラリ イベントストーリー（記錄：輪廻の檻 …）",
        expected=[
            "記録：輪廻の檻", "記録：輪廻の檻 第１話", "記録：落陽の港", "記録：言祝の庭",
            "記録：鎮魂の棺", "記録：皎潔の丘",
        ],
        rule_ids=["R04_event_quest_chapter_title", "R06_record_episode_title", "R06b_record_mission_label"],
    ),
    dict(
        item="图片7：アナザーストーリー（挿話：星/塔/女帝/月/世界）",
        expected=["挿話：星", "挿話：塔", "挿話：女帝", "挿話：月", "挿話：世界"],
        rule_ids=["R07_anecdote_title"],
    ),
]

# ---------------------------------------------------------------------------
# 用户截图转录（v2.0 新增）：图片1-5 地图章节列表 / 图片6 图书馆 / 图片7 卡片故事
#   来源：用户提供的截图，由 Lead 逐张读图转录（只读用途；行序=界面从上到下）。
#   用途：核对“截图内可见值”与“数据中已补全、但截图未拍到的值”。
#   注意：这是人工转录，不是 OCR/机器识别；未能覆盖的界面不做推断。
# ---------------------------------------------------------------------------
SCREENSHOT_TRANSCRIPT = [
    dict(
        image=1,
        ui="地图（マップ）→ 少女と怪物（页签1）",
        note="列表顶部起；底部被截断（最后一行为 中間プロローグ）",
        rows=[
            "一章：風砂の章", "二章：砂礫の章", "三章：硬砂の章", "四章：流水の章",
            "五章：冠雪の章", "六章：刻石の章", "中間プロローグ",
        ],
    ),
    dict(
        image=2,
        ui="地图 → 少女と怪物（页签1，向下滚动）",
        note="首行为上一张的 中間プロローグ；接近列表底部",
        rows=[
            "中間プロローグ", "七章：紅枯の章", "八章：積葉の章", "九章：炎砂の章",
            "十章：煌粒の章", "十一章：水煙の章", "十二章：白秋の章",
        ],
    ),
    dict(
        image=3,
        ui="地图 → 太陽と月（页签2，「表」子页签）",
        note="底部被截断：其后仍有 陽ノ陸：黄昏の章",
        rows=[
            "月ノ序章", "月ノ壱：宵闇の章", "月ノ弐：暮夜の章", "月ノ参：暁天の章",
            "陽ノ幕間", "陽ノ肆：朝暉の章", "陽ノ伍：明昼の章",
        ],
    ),
    dict(
        image=4,
        ui="地图 → 太陽と月（页签2，「裏」子页签）",
        note="底部被截断：其后仍有 月ノ陸：暁天の章",
        rows=[
            "陽ノ序章", "陽ノ壱：朝暉の章", "陽ノ弐：明昼の章", "陽ノ参：黄昏の章",
            "月ノ幕間", "月ノ肆：宵闇の章", "月ノ伍：暮夜の章",
        ],
    ),
    dict(
        image=5,
        ui="地图 → ヒトと世界（页签3）",
        note="首行是『幕開』（不是幕間）；底部被截断：其后仍有 終ノ幕：転生の章",
        rows=[
            "幕開", "序ノ壱：青藍の章", "序ノ弐：紅緋の章", "序ノ参：翠緑の章",
            "序ノ肆：琥珀の章", "二ノ幕：回帰の章", "三ノ幕：輪廻の章",
        ],
    ),
    dict(
        image=6,
        ui="ライブラリ → イベントストーリー",
        note="右侧有滚动条；可视 5 行",
        rows=["記録：輪廻の檻", "記録：落陽の港", "記録：言祝の庭", "記録：鎮魂の棺", "記録：皎潔の丘"],
    ),
    dict(
        image=7,
        ui="ライブラリ → アナザーストーリー → カードストーリー",
        note="右侧有滚动条；可视 5 行；用户说明一共 8 个（其余以主数据为准）",
        rows=["挿話：星", "挿話：塔", "挿話：女帝", "挿話：月", "挿話：世界"],
    ),
]

# 地图章节列表里“不显示/不参与截图”的占位值（不代表漏项）
R01_NON_DISPLAY_VALUES = {"-", "サンプル"}

# masterdata（bin.e）侧排除规则：主数据文本表按"表 + 主键 + 文本列 + LanguageType"定位。
# 与任务 D（masterdata 写回）对齐：排除行不写中文，其余行按 LT 策略处理。
MASTERDATA_RULES = [
    dict(
        rule_id="MD01_webview_mission_title",
        table="EntityMWebviewMissionTitleTextTable",
        id_column="WebviewMissionTitleTextId",
        text_column="Text",
        language_column="LanguageType",
        ids=list(range(1, 9)),
        action="skip",
        scope="mandatory",
        title_zh="アナザーストーリー『挿話：xxx』8 条标题（图片7）",
        policy="禁止改写 TitleTextId=1..8 的任意 LanguageType 行（LT1 日文/LT2 英文/LT3 韩文全部保留原值）。",
        note="文本包 mission.label.* 只覆盖 6 条（缺 塔/女帝），本表覆盖 8 条，是图片7 的权威来源；"
        "与 task D 约定一致：主数据侧只写 LT1/LT3 的其它文本行，LT2 保持英文；排除行三列都不动。",
    ),
    dict(
        rule_id="MD02_dokan_text_title_mentions",
        table="EntityMDokanTextTable",
        id_column="DokanTextId",
        text_column="Text",
        language_column="LanguageType",
        ids=[],
        action="protect_in_sentence",
        scope="mandatory",
        title_zh="ママ对话中引用的『記録：…』『挿話：…』标题",
        policy="叙事句子照常翻译，但句中的标题串（記録：… / 挿話：…）必须原样保留（句中保护）。",
        note="本表命中 7 行（如『「記録：輪廻の檻」がまた遊べるわよ！』『パネルミッション「挿話：人形」も復刻！』）；"
        "不可整行跳过，否则会丢失汉化句子。",
    ),
    dict(
        rule_id="MD03_navi_cutin_title_mentions",
        table="EntityMNaviCutInTextTable",
        id_column="NaviCutInTextId",
        text_column="Text",
        language_column="LanguageType",
        ids=[],
        action="protect_in_sentence",
        scope="recommended",
        title_zh="引导对话中『絵本の記録』等泛称",
        policy="照常翻译；如句中出现具体标题串需保护。",
        note="本表仅 1 行含『記録』（『「絵本の記録が再現されたボードゲーム」…』），是普通名词不是标题，照常翻译即可。",
    ),
    dict(
        rule_id="MD04_gift_text_no_exclusion",
        table="EntityMGiftTextTable",
        id_column="GiftTextId",
        text_column="Text",
        language_column="LanguageType",
        ids=[],
        action="translate",
        scope="mandatory",
        title_zh="礼物来源文案（无排除项）",
        policy="照常翻译。",
        note="全文检索未发现『記録：/挿話：』类标题。",
    ),
    dict(
        rule_id="MD05_webview_panel_flavor_no_exclusion",
        table="EntityMWebviewPanelMissionCompleteFlavorTextTable",
        id_column="WebviewPanelMissionCompleteFlavorTextId",
        text_column="CompleteFlavorText",
        language_column="LanguageType",
        ids=[],
        action="translate",
        scope="mandatory",
        title_zh="面板任务通关语（无排除项）",
        policy="照常翻译。",
        note="全文检索未发现排除类标题；注意本表为面板任务完成后的剧情文案。",
    ),
]

# 主数据侧规则的界面内容元数据（v2.0 新增，字段语义同 RULE_UI）
MASTERDATA_UI = {
    "MD01_webview_mission_title": dict(
        ui_location="ライブラリ → アナザーストーリー（ui.Outgame.Library.Menu.Record）→ カードストーリー（ui.Outgame.Library.Record.CardStory）列表行；客户端标题由主数据渲染",
        content_note="8 个卡片故事标题『挿話：星/塔/女帝/月/世界/皇帝/審判/人形』（LT1 日文 / LT2 英文 Anecdote: … / LT3 韩文 삽화: …）。文本包只有 6 条标签，塔/女帝只存在于本表——所以必须同时豁免主数据这 24 行，否则 EN 客户端韩语槽（会被写成中文）与 JP 客户端日语槽会把标题变成中文。只豁免标题本身，卡片故事正文不在此表。",
        screenshots="图片7",
    ),
    "MD02_dokan_text_title_mentions": dict(
        ui_location="お知らせ（Dokan）：带图片/影片的更新公告页，一行行“ママ口吻”的介绍文",
        content_note="公告正文会引用活动标题，如『「記録：輪廻の檻」がまた遊べるわよ！』『パネルミッション「挿話：人形」も復刻！』。句子本身是公告内容要照译，只把其中的『記録：…』『挿話：…』标题串原样保护；整行跳过会丢失整句汉化。",
        screenshots="",
    ),
    "MD03_navi_cutin_title_mentions": dict(
        ui_location="ナビ cut-in（功能解锁/引导时的对话切入）",
        content_note="引导对话正文，本表 1 行含『絵本の記録』——这是普通名词（绘本的记录），不是标题，照常翻译。",
        screenshots="",
    ),
    "MD04_gift_text_no_exclusion": dict(
        ui_location="プレゼント/入手元表示（如道具详情里的『ガチャで獲得』= 抽卡获得）",
        content_note="礼物/道具的入手来源短句；无任何标题引用，照常翻译。",
        screenshots="",
    ),
    "MD05_webview_panel_flavor_no_exclusion": dict(
        ui_location="アナザーストーリー パネルミッション 完成后的短篇剧情（通关语/回忆文案）",
        content_note="面板任务通关后的剧情短文（如少女梦中的餐桌、黑怪物与石塔的梦）。属“剧情正文”，照常翻译；与标题不同，不豁免。",
        screenshots="",
    ),
}


# ---------------------------------------------------------------------------
# 工具函数
# ---------------------------------------------------------------------------
def open_utf8(path: Path, mode: str = "r"):
    return io.open(path, mode, encoding="utf-8", newline="\n")


def write_json(path: Path, obj) -> None:
    with open_utf8(path, "w") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2, sort_keys=False)
        f.write("\n")


def write_tsv(path: Path, header, rows) -> None:
    with open_utf8(path, "w") as f:
        f.write("\t".join(header) + "\n")
        for row in rows:
            f.write("\t".join(str(x).replace("\t", " ").replace("\n", "\\n") for x in row) + "\n")


def short(value: str, limit: int = 160) -> str:
    value = value.replace("\n", "\\n")
    return value if len(value) <= limit else value[:limit] + "…"


class Rule:
    def __init__(self, spec: dict):
        self.__dict__.update(spec)
        m = spec["match"]
        self.key_prefixes = tuple(m.get("key_prefix", ()))
        self.key_regex_src = m.get("key_regex")
        self.key_re = re.compile(self.key_regex_src) if self.key_regex_src else None
        self.value_regex_src = m.get("value_regex")
        self.value_re = re.compile(self.value_regex_src) if self.value_regex_src else None
        self.value_in = set(m.get("value_in", ()))
        self.bundles = set(m.get("bundles", ()))
        self.langs = set(m.get("langs", ()))

    def matches_key(self, key: str, bundle: str) -> bool:
        if self.bundles and bundle not in self.bundles:
            return False
        if self.key_prefixes:
            return key.startswith(self.key_prefixes)
        if self.key_re is not None:
            return bool(self.key_re.match(key))
        return False

    def matches(self, row: dict) -> bool:
        """整条匹配：lang/key/value 条件（若有）都需满足。"""
        if self.langs and row.get("lang") not in self.langs:
            return False
        has_key = bool(self.key_prefixes or self.key_re or self.bundles)
        if has_key and not self.matches_key(row["key"], row["bundle"]):
            return False
        if self.value_in and row["value"] not in self.value_in:
            return False
        if self.value_re is not None and not self.value_re.match(row["value"]):
            return False
        return True


def new_rule_stats(rule: Rule) -> dict:
    return dict(
        rule_id=rule.id,
        title_zh=rule.title_zh,
        group=rule.group,
        scope=rule.scope,
        action=rule.action,
        occurrences=0,
        unique_keys=set(),
        unique_values=set(),
        bundles=set(),
        samples=[],
        empty_values=0,
    )


def finish_rule_stats(st: dict, sample_limit: int = 8) -> dict:
    return dict(
        rule_id=st["rule_id"],
        title_zh=st["title_zh"],
        group=st["group"],
        scope=st["scope"],
        action=st["action"],
        occurrences=st["occurrences"],
        unique_keys=len(st["unique_keys"]),
        unique_values=len(st["unique_values"]),
        bundles=sorted(st["bundles"]),
        empty_values=st["empty_values"],
        samples=st["samples"][:sample_limit],
    )


def boundary_pattern(term: str, boundary: str) -> str:
    """把记号转换为保护正则：word=两侧非字母数字；prefix=左侧非字母、右侧允许数字；literal=原样。"""
    esc = re.escape(term)
    if boundary == "word":
        return rf"(?<![A-Za-z0-9]){esc}(?![A-Za-z0-9])"
    if boundary == "prefix":
        return rf"(?<![A-Za-z]){esc}(?![A-Za-z])"
    return esc


def compile_marker_specs() -> list[dict]:
    """逐字记号 + 正则型记号的统一计数规格（扫描时用 anchor/prefilter 预过滤，再正则精确计数）。"""
    specs: list[dict] = []
    for spec in MARKER_TERMS:
        specs.append(
            dict(
                term=spec["term"],
                type=spec["type"],
                note=spec["note"],
                kind="literal",
                boundary=spec["boundary"],
                protect_regex=boundary_pattern(spec["term"], spec["boundary"]),
                regex=re.compile(boundary_pattern(spec["term"], spec["boundary"])),
                anchor=spec["term"],
                prefilter="",
            )
        )
    for spec in PATTERN_TERMS:
        specs.append(
            dict(
                term=spec["term"],
                type=spec["type"],
                note=spec["note"],
                kind="pattern",
                boundary="regex",
                protect_regex=spec["term"],
                regex=re.compile(spec["term"]),
                anchor="",
                prefilter=spec.get("prefilter", ""),
            )
        )
    return specs


# ---------------------------------------------------------------------------
# 主流程
# ---------------------------------------------------------------------------
def main() -> int:
    ap = argparse.ArgumentParser(description="构建排除项清单（任务 B）")
    ap.add_argument("--text-dir", type=Path, default=DEFAULT_TEXT_DIR)
    ap.add_argument("--masterdata-dir", type=Path, default=DEFAULT_MASTERDATA_DIR)
    ap.add_argument("--out-dir", type=Path, default=SCRIPT_DIR)
    ap.add_argument("--sample-limit", type=int, default=8)
    args = ap.parse_args()

    out_dir: Path = args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    rules = [Rule(spec) for spec in RULES]
    marker_specs = compile_marker_specs()
    log_lines: list[str] = []

    def log(msg: str) -> None:
        print(msg)
        log_lines.append(msg)

    # ---------------- 1) 三语文本扫描 ----------------
    per_lang: dict[str, dict] = {}
    name_values: dict[str, dict[str, list[str]]] = {}  # lang -> rule_id -> unique values
    for lang, fname in LANG_FILES.items():
        path = args.text_dir / fname
        if not path.exists():
            log(f"[WARN] 缺少文本文件：{path}")
            continue
        stats = {rule.id: new_rule_stats(rule) for rule in rules}
        name_sets: dict[str, set] = collections.defaultdict(set)
        total_rows = 0
        total_unique_keys: set[str] = set()
        key_multi = collections.Counter()
        key_first_value: dict[str, str] = {}
        inconsistent_keys: list[dict] = []
        skip_rows = 0
        skip_keys: set[str] = set()
        tag_counter = collections.Counter()
        tag_examples: dict[str, str] = {}
        placeholder_counter = collections.Counter()
        english_sentence_rows: list[dict] = []
        strict_english_rows = 0
        value_with_literal_backslash_n = 0
        tokens = collections.Counter()
        token_examples: dict[str, str] = {}
        dir_stats: dict[str, dict] = collections.defaultdict(lambda: dict(total=0, skip=0))
        translatable_values: set[str] = set()
        english_content_tokens: set[str] = set()
        # 英文记号/正则记号计数（仅 ja、en 槽需要）
        marker_counts = [
            dict(rows=0, occurrences=0, uniq=set(), example="") for _ in marker_specs
        ] if lang in ("ja", "en") else None
        # v2.0：附录核对用的少量原文（章节名 / mission.label / tip.19006），按 key 取首次出现值
        scan_values: dict[str, str] = {}

        with open_utf8(path) as f:
            for line in f:
                if not line.strip():
                    continue
                row = json.loads(line)
                total_rows += 1
                key = row["key"]
                total_unique_keys.add(key)
                key_multi[key] += 1
                value = row["value"]
                if (
                    key.startswith("quest.main.chapter_number.")
                    or key.startswith("mission.label.")
                    or key == "tip.19006"
                ):
                    scan_values.setdefault(key, value)
                if key not in key_first_value:
                    key_first_value[key] = value
                elif key_first_value[key] != value and len(inconsistent_keys) < 200:
                    inconsistent_keys.append(
                        dict(key=key, bundle=row["bundle"], first=short(key_first_value[key], 120), current=short(value, 120))
                    )
                if "\\n" in value:
                    value_with_literal_backslash_n += 1
                if value == "":
                    pass
                matched_skip = False
                for rule in rules:
                    st = stats[rule.id]
                    if not rule.matches(row):
                        continue
                    st["occurrences"] += 1
                    st["unique_keys"].add(key)
                    st["unique_values"].add(value)
                    st["bundles"].add(row["bundle"])
                    if value.strip() == "":
                        st["empty_values"] += 1
                    if len(st["samples"]) < args.sample_limit:
                        st["samples"].append(
                            dict(key=key, bundle=row["bundle"], dir=row["dir"], value=short(value, 220))
                        )
                    if rule.action == "skip":
                        matched_skip = True
                        if rule.group in PROTECT_GROUPS:
                            name_sets[rule.id].add(value)
                if matched_skip:
                    skip_rows += 1
                    skip_keys.add(key)
                # 目录维度统计 + 去重后可翻译值
                dir_stats[row["dir"]]["total"] += 1
                if matched_skip:
                    dir_stats[row["dir"]]["skip"] += 1
                else:
                    translatable_values.add(value)
                # 英文记号命中计数（锚点预过滤 + 正则精确计数）
                if marker_counts is not None:
                    for idx, ms in enumerate(marker_specs):
                        if ms["anchor"]:
                            if ms["anchor"] not in value:
                                continue
                        elif ms["prefilter"] and not any(ch in value for ch in ms["prefilter"]):
                            continue
                        hits = 0
                        for _ in ms["regex"].finditer(value):
                            hits += 1
                        if hits:
                            mc = marker_counts[idx]
                            mc["rows"] += 1
                            mc["occurrences"] += hits
                            mc["uniq"].add(value)
                            if not mc["example"]:
                                mc["example"] = key
                # 英文句子（JP 槽）与格式标签统计只在 ja 槽做，en/ko 仅规则/记号计数
                if lang == "ja":
                    # 先去掉富文本标签/字面 \n 再做 ASCII 分词，避免把 <TAP>、\n1wave 之类当词
                    clean_value = re.sub(r"<[^<>]*>", " ", value).replace("\\n", " ").replace("\n", " ")
                    java_tokens = re.findall(r"[A-Za-z][A-Za-z0-9]*", clean_value)
                    for token in java_tokens:
                        tokens[token] += 1
                        if token not in token_examples:
                            token_examples[token] = key
                    for m in re.finditer(r"<([A-Za-z][A-Za-z0-9_\-]*)", value):
                        tag = m.group(1)
                        tag_counter[tag] += 1
                        if tag not in tag_examples:
                            tag_examples[tag] = key
                    for m in re.finditer(r"\{([0-9]+)\}", value):
                        placeholder_counter[m.group(0)] += 1
                    stripped = value.strip()
                    ascii_words = re.findall(r"[A-Za-z]{2,}", stripped)
                    core = re.sub(r"<[^<>]*>", "", stripped).replace(" ", "")
                    is_encoded = bool(
                        len(core) >= 40
                        and (re.fullmatch(r"[0-9a-fA-F]+", core) or re.fullmatch(r"[01]+", core))
                    ) or bool(re.fullmatch(r"(?:[0-9A-Fa-f]{2}\s+){12,}", stripped))
                    if (
                        len(stripped) >= 20
                        and len(ascii_words) >= 3
                        and not is_encoded
                        and not re.search(r"[\u3041-\u3096\u30A1-\u30FA\u4E00-\u9FFF]", stripped)
                    ):
                        strict_english_rows += 1
                        english_content_tokens.update(java_tokens)
                        if len(english_sentence_rows) < 5000:
                            english_sentence_rows.append(
                                dict(dir=row["dir"], bundle=row["bundle"], key=key, value=value)
                            )

        per_lang[lang] = dict(
            path=str(path),
            total_rows=total_rows,
            unique_keys=len(total_unique_keys),
            duplicate_key_count=sum(1 for _, c in key_multi.items() if c > 1),
            inconsistent_keys=inconsistent_keys,
            rules={rule.id: finish_rule_stats(stats[rule.id], args.sample_limit) for rule in rules},
            skip_rows=skip_rows,
            skip_unique_keys=len(skip_keys),
            translatable_rows=total_rows - skip_rows,
            tag_counter=tag_counter,
            tag_examples=tag_examples,
            placeholder_counter=placeholder_counter,
            english_sentence_count=strict_english_rows,
            english_sentence_samples=english_sentence_rows[:400],
            values_with_literal_backslash_n=value_with_literal_backslash_n,
            token_counter=tokens,
            token_examples=token_examples,
            english_content_tokens=english_content_tokens,
            markup_tag_names=set(tag_counter.keys()),
            marker_counts=marker_counts,
            dir_stats={d: dict(total=v["total"], skip=v["skip"], translatable=v["total"] - v["skip"]) for d, v in dir_stats.items()},
            translatable_unique_values=len(translatable_values),
            translatable_unique_chars=sum(len(v) for v in translatable_values),
            scan_values=scan_values,
        )
        name_values[lang] = {rid: sorted(vals) for rid, vals in name_sets.items()}
        log(
            f"[scan] {lang}: rows={total_rows} unique_keys={len(total_unique_keys)} "
            f"skip_rows={skip_rows} tables={len(rules)}"
        )

    # ---------------- 2) 英文记号白名单统计 ----------------
    ja_tokens = per_lang.get("ja", {}).get("token_counter", collections.Counter())
    en_tokens = per_lang.get("en", {}).get("token_counter", collections.Counter())
    ja_ex = per_lang.get("ja", {}).get("token_examples", {})
    en_ex = per_lang.get("en", {}).get("token_examples", {})
    ja_mc = per_lang.get("ja", {}).get("marker_counts") or []
    en_mc = per_lang.get("en", {}).get("marker_counts") or []

    marker_rows = []
    pattern_rows = []
    classified_terms = set()
    for idx, ms in enumerate(marker_specs):
        jc = ja_mc[idx] if idx < len(ja_mc) else dict(rows=0, occurrences=0, uniq=set(), example="")
        ec = en_mc[idx] if idx < len(en_mc) else dict(rows=0, occurrences=0, uniq=set(), example="")
        row = dict(
            term=ms["term"],
            type=ms["type"],
            decision="keep",
            boundary=ms["boundary"],
            protect_regex=ms["protect_regex"],
            ja_occurrences=jc["occurrences"],
            ja_rows=jc["rows"],
            ja_unique_values=len(jc["uniq"]),
            en_occurrences=ec["occurrences"],
            en_rows=ec["rows"],
            en_unique_values=len(ec["uniq"]),
            ja_example_key=jc["example"],
            en_example_key=ec["example"],
            note=ms["note"],
        )
        if ms["kind"] == "literal":
            classified_terms.add(row["term"])
            marker_rows.append(row)
        else:
            pattern_rows.append(row)
    marker_rows.sort(key=lambda r: (r["type"], -r["ja_occurrences"], r["term"]))
    pattern_rows.sort(key=lambda r: (r["type"], -r["ja_occurrences"], r["term"]))
    pattern_regexes = [ms["regex"] for ms in marker_specs if ms["kind"] == "pattern"]

    # 候选：未归类 ASCII 记号（排除内部标识/标签名/剧情内英文实词，人工复核用）
    noise = set(
        "br n style cspace em align Dash right center left space color size production0 production1 production2 "
        "hint type icon weapon loading result x b a st nd No EID AGW BSE alpha sprite WAIT".split()
    )
    noise |= set(per_lang.get("ja", {}).get("markup_tag_names", set()))
    english_content_tokens = per_lang.get("ja", {}).get("english_content_tokens", set())
    literal_marker_terms = sorted(classified_terms, key=len, reverse=True)
    digit_suffix_re = re.compile(
        "(?:" + "|".join(re.escape(t) for t in literal_marker_terms) + r")\d{1,3}$"
    )
    candidates = []
    for term, count in ja_tokens.most_common():
        if term in classified_terms or term.lower() in noise:
            continue
        if any(rx.fullmatch(term) for rx in pattern_regexes):
            continue
        # HP70/HP80/Lv10 这类「记号+数字」不单列候选
        if digit_suffix_re.fullmatch(term):
            continue
        if len(term) < 2 and term not in ("A", "B", "C", "D", "E", "F", "S"):
            continue
        decision = "review"
        if term in english_content_tokens:
            decision = "content_en(剧情内英文实词，非记号)"
        candidates.append(
            dict(
                term=term,
                ja_occurrences=count,
                en_occurrences=en_tokens.get(term, 0),
                ja_example_key=ja_ex.get(term, ""),
                decision=decision,
            )
        )

    # ---------------- 3) 格式标签/占位符清单 ----------------
    tag_counter = per_lang.get("ja", {}).get("tag_counter", collections.Counter())
    tag_examples = per_lang.get("ja", {}).get("tag_examples", {})
    markup_rows = []
    for tag, count in tag_counter.most_common():
        markup_rows.append(dict(kind="tag_name", token=f"<{tag}…>", occurrences=count, example_key=tag_examples.get(tag, ""), note="富文本/脚本标签"))
    for pattern, note in MARKUP_PATTERNS:
        regex = re.compile(pattern)
        count = 0
        example = ""
        # 统计只基于 ja 槽样本中已收集到的标签计数，无法离线复原所有值；此处用 token 计数近似
        for tag, c in tag_counter.items():
            if regex.match(f"<{tag}>"):
                count += c
        markup_rows.append(dict(kind="pattern", token=pattern, occurrences=count, example_key=example, note=note))

    # ---------------- 4) masterdata 交叉校验 ----------------
    md = args.masterdata_dir
    md_checks: dict = {}

    def load_table(name: str):
        p = md / f"{name}.json"
        if not p.exists():
            return None
        with open_utf8(p) as f:
            return json.load(f)

    # 4.1 讨伐战 BOSS 名
    boss_rows = load_table("EntityMBigHuntBossTable") or []
    ja_flat = {}
    en_flat = {}
    ko_flat = {}
    for lang, flat in (("ja", ja_flat), ("en", en_flat), ("ko", ko_flat)):
        p = args.text_dir / LANG_FILES[lang]
        if not p.exists():
            continue
        with open_utf8(p) as f:
            for line in f:
                row = json.loads(line)
                flat.setdefault(row["key"], row["value"])
    boss_check = []
    for r in boss_rows:
        tid = int(r["NameBigHuntBossTextId"])
        key = f"bigHunt.boss.name.{tid}"
        boss_check.append(
            dict(
                BigHuntBossId=int(r["BigHuntBossId"]),
                text_id=tid,
                text_key=key,
                ja=ja_flat.get(key, ""),
                en=en_flat.get(key, ""),
                ko=ko_flat.get(key, ""),
            )
        )
    md_checks["bighunt_boss"] = boss_check

    # 4.2 挿話标题表
    wv = load_table("EntityMWebviewMissionTitleTextTable") or []
    wv_by_id: dict[int, dict] = {}
    for r in wv:
        wv_by_id.setdefault(int(r["WebviewMissionTitleTextId"]), {})[int(r["LanguageType"])] = r["Text"]
    md_checks["webview_mission_titles"] = [
        dict(text_id=tid, ja=v.get(1, ""), en=v.get(2, ""), ko=v.get(3, "")) for tid, v in sorted(wv_by_id.items())
    ]

    # 4.3 活动章节表 -> 文本 key 覆盖率
    #     注意：文本 key 由 NameEventQuestTextId 决定（不是 EventQuestChapterId）。
    #     实测：按 chapterId 映射 136/274 命中；按 NameEventQuestTextId 映射 260/260（非零）命中。
    ev_rows = load_table("EntityMEventQuestChapterTable") or []
    ev_chapter_ids = {int(r["EventQuestChapterId"]) for r in ev_rows}
    ev_text_ids = {(int(r.get("NameEventQuestTextId") or 0)) for r in ev_rows}
    ev_text_ids.discard(0)
    found_by_text = [i for i in sorted(ev_text_ids) if f"quest.event.chapter_title.{i}" in ja_flat]
    found_by_chapter = [i for i in sorted(ev_chapter_ids) if f"quest.event.chapter_title.{i}" in ja_flat]
    all_text_keys = {k for k in ja_flat if k.startswith("quest.event.chapter_title.")}
    mapped_keys = {f"quest.event.chapter_title.{i}" for i in ev_text_ids}
    md_checks["event_quest_chapter"] = dict(
        rows=len(ev_rows),
        mapping_column="NameEventQuestTextId",
        distinct_name_text_ids=len(ev_text_ids),
        text_key_found_by_name_text_id=len(found_by_text),
        distinct_chapter_ids=len(ev_chapter_ids),
        text_key_found_by_chapter_id=len(found_by_chapter),
        text_bundle_keys_total=len(all_text_keys),
        text_bundle_keys_unmapped=len(all_text_keys - mapped_keys),
        unmapped_sample=sorted(all_text_keys - mapped_keys)[:20],
    )

    # 4.4 各名称类 text-id 覆盖率
    coverage_specs = [
        ("EntityMCharacterTable", "NameCharacterTextId", "character.name"),
        ("EntityMQuestTable", "NameQuestTextId", "quest.name"),
        ("EntityMQuestTable", "PictureBookNameQuestTextId", "quest.name"),
        ("EntityMMissionTable", "NameMissionTextId", "mission.name"),
        ("EntityMSkillDetailTable", "NameSkillTextId", "skill.name"),
        ("EntityMAbilityDetailTable", "NameAbilityTextId", "ability.name"),
        ("EntityMImportantItemTable", "NameImportantItemTextId", "important_item.name"),
    ]
    cov = []
    for table, col, prefix in coverage_specs:
        rows = load_table(table) or []
        if not rows or col not in rows[0]:
            cov.append(dict(table=table, column=col, status="column_missing"))
            continue
        ids = {int(r.get(col) or 0) for r in rows}
        ids.discard(0)
        found = sum(1 for i in ids if f"{prefix}.{i}" in ja_flat)
        cov.append(
            dict(
                table=table,
                column=col,
                text_prefix=prefix,
                unique_ids=len(ids),
                found_in_ja=found,
                missing=len(ids) - found,
                status="ok",
            )
        )
    md_checks["name_text_id_coverage"] = cov

    # 4.5 masterdata 5 张文本表是否含排除类标题
    md_text_hits = {}
    for table, cols in [
        ("EntityMDokanTextTable", ["Text"]),
        ("EntityMGiftTextTable", ["Text"]),
        ("EntityMNaviCutInTextTable", ["Text"]),
        ("EntityMWebviewMissionTitleTextTable", ["Text"]),
        ("EntityMWebviewPanelMissionCompleteFlavorTextTable", ["CompleteFlavorText"]),
    ]:
        rows = load_table(table) or []
        hits = []
        for r in rows:
            text = " ".join(str(r.get(c, "")) for c in cols)
            if any(x in text for x in ("記録：", "挿話：", "Anecdote:", "記録:")):
                hits.append(dict(id=r.get(f"{table[7:-5]}Id") or r.get("WebviewMissionTitleTextId"), lt=r.get("LanguageType"), text=short(text, 200)))
        md_text_hits[table] = dict(hits=len(hits), samples=hits[:10])
    md_checks["masterdata_text_tables"] = md_text_hits

    # 4.6 用 masterdata 权威文本补齐标题值（R05 讨伐战 BOSS 名、R07 挿話标题）
    def add_unique_values(rule_id: str, lang: str, values: list[str]) -> None:
        bucket = name_values.setdefault(lang, {}).setdefault(rule_id, [])
        existing = set(bucket)
        for v in values:
            if v and v not in existing:
                bucket.append(v)
                existing.add(v)
        bucket.sort()

    for idx, lang in ((1, "ja"), (2, "en"), (3, "ko")):
        for boss in md_checks["bighunt_boss"]:
            add_unique_values("R05_bighunt_boss_quest_name", lang, [boss.get(lang, "")])
        for t in md_checks["webview_mission_titles"]:
            add_unique_values("R07_anecdote_title", lang, [t.get(lang, "")])
    log("[md] 已用 masterdata 补齐 R05/R07 标题值（讨伐战 BOSS 名、挿話 8 条）")

    # 4.7 masterdata 侧排除规则（与 task D 对齐）：逐表定位行/值/语言列
    md_rule_results = []
    for spec in MASTERDATA_RULES:
        rows = load_table(spec["table"]) or []
        entry = dict(spec)
        entry.update(MASTERDATA_UI.get(spec["rule_id"], {}))
        entry["rows"] = []
        entry["hit_count"] = 0
        if not rows:
            entry["status"] = "table_missing"
            md_rule_results.append(entry)
            continue
        id_col = spec["id_column"]
        text_col = spec["text_column"]
        lt_col = spec.get("language_column")
        if spec["action"] == "skip":
            for rid in spec["ids"]:
                per_lt = {}
                for r in rows:
                    if int(r.get(id_col) or 0) != rid:
                        continue
                    lt = int(r.get(lt_col) or 0) if lt_col else 0
                    per_lt[lt] = r.get(text_col, "")
                entry["rows"].append(dict(id=rid, lts=per_lt, text_count=len(per_lt)))
                entry["hit_count"] += len(per_lt)
        elif spec["action"] == "protect_in_sentence":
            for r in rows:
                text = str(r.get(text_col, ""))
                if any(x in text for x in ("記録：", "記録:", "挿話：", "挿話:", "Anecdote:")):
                    entry["rows"].append(
                        dict(
                            id=int(r.get(id_col) or 0),
                            lt=int(r.get(lt_col) or 0) if lt_col else 0,
                            text=short(text, 240),
                        )
                    )
            entry["hit_count"] = len(entry["rows"])
        else:  # translate
            entry["hit_count"] = 0
            entry["note_rows_total"] = len(rows)
        entry["status"] = "ok"
        md_rule_results.append(entry)
    md_checks["masterdata_rules"] = md_rule_results
    # 文本包与 masterdata 挿話标题重合度
    wv_ids = {t["text_id"] for t in md_checks["webview_mission_titles"]}
    overlap = []
    for rid, values in name_values.get("ja", {}).items():
        if rid != "R07_anecdote_title":
            continue
        for wv in md_checks["webview_mission_titles"]:
            if wv["ja"] in values:
                overlap.append(wv["ja"])
    md_checks["anecdote_text_bundle_overlap"] = sorted(set(overlap))
    log(
        f"[md] masterdata 排除规则 {len(md_rule_results)} 条："
        + "；".join(
            f"{r['rule_id']}={r.get('hit_count')}({r.get('status')})" for r in md_rule_results
        )
    )

    # ---------------- 4.8) 界面内容对照附录（v2.0 新增）----------------
    # 4.8.1 地图章节列表：R01 全 40 条 + 截图内/截图外补全标注
    chapter_scan = per_lang.get("ja", {}).get("scan_values", {})
    chapter_entries = []
    for k, v in chapter_scan.items():
        if not k.startswith("quest.main.chapter_number."):
            continue
        parts = k.split(".")
        if len(parts) != 6:
            continue
        chapter_entries.append(
            dict(key=k, value=v, season=int(parts[3]), route=int(parts[4]), chapter=int(parts[5]))
        )
    chapter_entries.sort(key=lambda x: (x["season"], x["route"], x["chapter"]))

    shot_by_value: dict[str, list[int]] = {}
    for shot in SCREENSHOT_TRANSCRIPT:
        for v in shot["rows"]:
            shot_by_value.setdefault(v, []).append(shot["image"])

    r01_rows = []
    for order, ent in enumerate(chapter_entries, 1):
        key, value = ent["key"], ent["value"]
        images = shot_by_value.get(value, [])
        if images:
            evidence = "截图内（图片" + "、".join(str(i) for i in images) + "）"
        elif value in R01_NON_DISPLAY_VALUES:
            evidence = "非地图显示项（列表不显示，截图无此项属正常）"
        else:
            evidence = "截图外补全（数据完整包含，截图未拍到）"
        note = ""
        if key in (
            "quest.main.chapter_number.2.1.8",
            "quest.main.chapter_number.2.2.8",
            "quest.main.chapter_number.3.1.8",
        ):
            note = "列表底部：图片3/4/5 的下一项（用户所述『底部还有一两个章节没截到』即此项）"
        elif key == "quest.main.chapter_number.1.1.1":
            note = "列表最上方：图片1 自『一章：風砂の章』起，序章行未入镜"
        elif value in R01_NON_DISPLAY_VALUES:
            note = "占位/样例值，地图章节列表不显示"
        r01_rows.append(
            dict(
                order=order,
                key=key,
                season=ent["season"],
                route=ent["route"],
                chapter=ent["chapter"],
                value=value,
                screenshot_images=",".join(str(i) for i in images),
                evidence=evidence,
                note=note,
            )
        )

    r01_display = [r for r in r01_rows if r["value"] not in R01_NON_DISPLAY_VALUES]
    r01_in_shot = [r for r in r01_rows if r["screenshot_images"]]
    r01_outside = [r for r in r01_rows if not r["screenshot_images"]]
    r01_non_display = [r for r in r01_rows if r["value"] in R01_NON_DISPLAY_VALUES]
    r01_coverage = dict(
        total=len(r01_rows),
        display_total=len(r01_display),
        in_screenshot=len(r01_in_shot),
        outside_count=len(r01_outside),
        outside=[dict(key=r["key"], value=r["value"], note=r["note"]) for r in r01_outside if r not in r01_non_display],
        non_display=[dict(key=r["key"], value=r["value"]) for r in r01_non_display],
        screenshots={str(s["image"]): dict(ui=s["ui"], note=s["note"], rows=len(s["rows"])) for s in SCREENSHOT_TRANSCRIPT},
        transcript_source="用户提供的截图，由 Lead 逐张读图转录（SCREENSHOT_TRANSCRIPT）；非 OCR",
        conclusion="R01 按 key 前缀整类排除，40/40 全部覆盖；截图内可见 34 条，截图外补全 4 条（プロローグ / 月ノ陸 / 陽ノ陸 / 終ノ幕），另有 2 条非显示占位（- / サンプル）。",
    )
    log(
        f"[r01] 章节 40 条：截图内 {len(r01_in_shot)}、截图外 {len(r01_outside)}"
        f"（其中非显示 {len(r01_non_display)}）"
    )

    # 4.8.2 『挿話：xxx』8 标题 ↔ 主数据 / 文本包 key 对照（图片7）
    wv_title_rows = load_table("EntityMWebviewMissionTitleTextTable") or []
    wv_mission_rows = load_table("EntityMWebviewMissionTable") or []
    wv_group_rows = load_table("EntityMMissionGroupTable") or []
    titles_by_id: dict[int, dict[int, str]] = {}
    for r in wv_title_rows:
        tid = int(r.get("WebviewMissionTitleTextId") or 0)
        lt = int(r.get("LanguageType") or 0)
        titles_by_id.setdefault(tid, {})[lt] = str(r.get("Text") or "")
    missions_by_title: dict[int, int] = {}
    for r in wv_mission_rows:
        missions_by_title[int(r.get("TitleTextId") or 0)] = int(r.get("WebviewMissionId") or 0)
    anecdote_groups = [r for r in wv_group_rows if int(r.get("MissionCategoryType") or 0) == 4]
    anecdote_groups.sort(key=lambda r: int(r.get("MissionGroupId") or 0))

    def norm_title(s: str) -> str:
        return (s or "").strip().strip("「」『』‘’'").strip()

    label_scan = {lang: per_lang.get(lang, {}).get("scan_values", {}) for lang in per_lang}
    anecdote_rows = []
    for idx, group in enumerate(anecdote_groups):
        tid = idx + 1  # 主数据按 TitleTextId 1..8 与 MissionGroupId 升序一一对齐（6 条已知标签可验证）
        group_id = int(group.get("MissionGroupId") or 0)
        label_id = int(group.get("LabelMissionTextId") or 0)
        pack_key = f"mission.label.{label_id}"
        pack = {lang: label_scan.get(lang, {}).get(pack_key) for lang in ("ja", "en", "ko")}
        text = titles_by_id.get(tid, {})
        matches = {}
        for lt, lang in ((1, "ja"), (2, "en"), (3, "ko")):
            matches[lang] = norm_title(pack[lang]) == norm_title(text.get(lt, "")) if pack.get(lang) else None
        known = [v for v in matches.values() if v is not None]
        match_state = "match" if known and all(known) else ("mismatch" if any(v is False for v in known) else "n/a")
        if not any(pack.values()):
            coverage = "masterdata_only"
            note = f"文本包三语均无 mission.label.{label_id}；标题仅存于主数据（塔/女帝即此情况）"
        elif not all(pack.values()):
            coverage = "partial"
            note = "文本包仅部分语言有值"
        else:
            coverage = "text_pack+masterdata"
            note = "文本包与主数据同标题（仅括号形态不同：文本包带「」/引号）"
        anecdote_rows.append(
            dict(
                title_id=tid,
                ja=text.get(1, ""),
                en=text.get(2, ""),
                ko=text.get(3, ""),
                webview_mission_id=missions_by_title.get(tid, ""),
                mission_group_id=group_id,
                label_mission_text_id=label_id,
                text_pack_key=pack_key,
                text_pack_ja=pack.get("ja") or "",
                text_pack_en=pack.get("en") or "",
                text_pack_ko=pack.get("ko") or "",
                coverage=coverage,
                text_pack_match=match_state,
                note=note,
            )
        )
    anecdote_mentions = []
    for lang in ("ja", "en", "ko"):
        tip = per_lang.get(lang, {}).get("scan_values", {}).get("tip.19006")
        if tip:
            anecdote_mentions.append(dict(lang=lang, key="tip.19006", value=tip))
    anecdote_report = dict(
        rows=anecdote_rows,
        coverage=dict(
            total=len(anecdote_rows),
            masterdata_rows=len(anecdote_rows) * 3,
            text_pack_rows=sum(1 for r in anecdote_rows if r["coverage"] == "text_pack+masterdata"),
            masterdata_only=[r["ja"] for r in anecdote_rows if r["coverage"] == "masterdata_only"],
            match=[
                r["text_pack_key"] for r in anecdote_rows if r["text_pack_match"] == "match"
            ],
            mismatch=[r["text_pack_key"] for r in anecdote_rows if r["text_pack_match"] == "mismatch"],
        ),
        mentions=anecdote_mentions,
        semantics=dict(
            title_skip="R07（文本包 6 条标题）/ MD01（主数据 8 个 id × 3 LT）只跳过标题本身",
            title_protect="标题在其它文本（tip.19006、Dokan 公告、技能/道具说明）中被提及时走句中保护（PROTECT）",
            body_translate="卡片故事正文（对白/旁白）位于剧情场景文本，不以『挿話：』开头 → 不匹配 R07，照常翻译",
        ),
    )
    log(
        f"[anecdote] 挿話 {len(anecdote_rows)} 条：文本包 {len(anecdote_report['coverage']['match'])} 条匹配、"
        f"主数据独有 {anecdote_report['coverage']['masterdata_only']}"
    )

    # 4.8.3 规则 ↔ 界面内容对照（写 rule_ui_map.tsv 用）
    rule_ui_rows = []
    for rule in rules:
        ui = RULE_UI.get(rule.id, {})
        rule_ui_rows.append(
            dict(
                kind="text",
                rule_id=rule.id,
                title_zh=rule.title_zh,
                action=rule.action,
                scope=rule.scope,
                ui_location=ui.get("ui_location", ""),
                content_note=ui.get("content_note", ""),
                screenshots=ui.get("screenshots", ""),
                ja_rows=per_lang.get("ja", {}).get("rules", {}).get(rule.id, {}).get("occurrences", 0),
            )
        )
    for mdr in md_rule_results:
        rule_ui_rows.append(
            dict(
                kind="masterdata",
                rule_id=mdr["rule_id"],
                title_zh=mdr["title_zh"],
                action=mdr["action"],
                scope=mdr["scope"],
                ui_location=mdr.get("ui_location", ""),
                content_note=mdr.get("content_note", ""),
                screenshots=mdr.get("screenshots", ""),
                ja_rows=mdr.get("hit_count", 0),
            )
        )

    # ---------------- 5) 疑似冲突/风险统计 ----------------
    # 5.1 名称/标题值跨 bundle 一致性（同一 key 在多个 bundle 中值不同）
    inconsistent_summary = {}
    for lang in per_lang:
        inc = per_lang[lang]["inconsistent_keys"]
        inconsistent_summary[lang] = dict(count=len(inc), samples=inc[:10])

    # 5.2 保护词典冲突度量（仅统计长度<=5 的短词，长词默认安全）
    protect_terms = []
    for lang in ("ja", "en"):
        if lang not in name_values:
            continue
        for rule in rules:
            if rule.group not in PROTECT_GROUPS:
                continue
            values = name_values[lang].get(rule.id, [])
            for value in values:
                if not value:
                    continue
                protect_terms.append(
                    dict(
                        lang=lang,
                        group=rule.group,
                        category=rule.id,
                        term=value,
                        char_len=len(value),
                    )
                )
    # 去重（同 lang/term 合并分类）
    merged: dict[tuple, dict] = {}
    for item in protect_terms:
        k = (item["lang"], item["term"])
        if k not in merged:
            merged[k] = dict(item, categories=[item["category"]])
        else:
            if item["category"] not in merged[k]["categories"]:
                merged[k]["categories"].append(item["category"])
    merged_terms = list(merged.values())

    # 统计短词在"非名称文本"中的出现（按首字符分桶，避免 O(N*M)）
    substring_hits: dict[tuple, int] = {}
    short_terms: dict[str, list[tuple]] = collections.defaultdict(list)
    for item in merged_terms:
        if item["char_len"] <= 5:
            short_terms[item["term"][0]].append(item)
    if short_terms:
        for lang in ("ja", "en"):
            if lang not in per_lang:
                continue
            path = Path(per_lang[lang]["path"])
            with open_utf8(path) as f:
                for line in f:
                    row = json.loads(line)
                    # 只统计"非名称/标题 key 空间"的文本，作为冲突近似
                    if any(r.matches(row) for r in rules if r.group in PROTECT_GROUPS):
                        continue
                    value = row["value"]
                    for first_char, items in short_terms.items():
                        if first_char not in value:
                            continue
                        for item in items:
                            if item["term"] in value:
                                substring_hits[(item["lang"], item["term"])] = substring_hits.get((item["lang"], item["term"]), 0) + 1
    for item in merged_terms:
        hits = substring_hits.get((item["lang"], item["term"]), 0)
        if item["char_len"] >= 6:
            risk = "safe"
            action = "正常保护（长词）"
        elif item["char_len"] <= 2:
            risk = "high"
            action = "仅整值/引号内保护；避免句中裸替换"
        elif hits == 0:
            risk = "safe"
            action = "正常保护"
        else:
            risk = "caution"
            action = "仅在分隔符/引号/空格边界保护"
        item.update(non_name_hits=hits, risk=risk, recommended_action=action)
    merged_terms.sort(key=lambda x: (x["lang"], x["risk"], -x["char_len"]))

    # 5.3 英文句子（JP 槽）分类
    english_sentence_class = collections.Counter()
    english_sentence_by_prefix = collections.Counter()
    english_sentence_samples = []
    keep_content_rule_ids = {"R17_encoded_story_text", "R18_decorative_english", "R19_weapon_story_ascii_content", "R20_cage_memory_ascii_logs"}
    keep_content_rules = [r for r in rules if r.id in keep_content_rule_ids]
    for row in per_lang.get("ja", {}).get("english_sentence_samples", []):
        key = row["key"]
        prefix = ".".join(key.split(".")[:2])
        english_sentence_by_prefix[prefix] += 1
        probe = dict(key=key, bundle=row["bundle"], value=row["value"], dir=row["dir"])
        kept_by = [r.id for r in keep_content_rules if r.matches(probe)]
        if kept_by:
            decision = "keep_content_en(剧情内/装饰英文，建议保留:" + ",".join(kept_by) + ")"
        elif key.startswith("CollectionBonus.Effect."):
            decision = "translate(UI 文案)"
        elif key.startswith("costume.emblem.production."):
            decision = "keep_decorative(装饰性英文)"
        elif key.startswith("cage.memory."):
            decision = "review(剧情内英文系统日志)"
        elif key.startswith("actor.object.name."):
            decision = "internal(内部名，不外显)"
        else:
            decision = "review"
        english_sentence_class[decision] += 1
        if len(english_sentence_samples) < 200:
            english_sentence_samples.append(dict(decision=decision, **row))

    # ---------------- 6) names.json ----------------
    names_json = dict(
        generated_at="2026-10-25",
        project="NieR Re[in]carnation zh-l10n",
        masterdata_sources={
            "R05_bighunt_boss_quest_name": dict(
                table="EntityMBigHuntBossTable",
                id_column="BigHuntBossId",
                text_column="NameBigHuntBossTextId",
                resolved_via="bigHunt.boss.name.<NameBigHuntBossTextId>",
                rows=md_checks["bighunt_boss"],
            ),
            "R07_anecdote_title": dict(
                table="EntityMWebviewMissionTitleTextTable",
                id_column="WebviewMissionTitleTextId",
                text_column="Text",
                language_column="LanguageType",
                ids=[t["text_id"] for t in md_checks["webview_mission_titles"]],
                rows=md_checks["webview_mission_titles"],
            ),
        },
        description=(
            "不翻译项（标题/名称）值清单。值为去重后的显示文本；key_patterns 给出精确来源。"
            "titles 组=章节/关卡/剧情标题；names 组=角色/武器/服装/技能/能力等专有名。"
        ),
        rule_scope_legend=dict(
            mandatory="用户明确要求不翻译",
            recommended="同一命名体系，建议不翻译（待确认）",
        ),
        categories={},
    )
    for rule in rules:
        if rule.group not in PROTECT_GROUPS:
            continue
        ui = RULE_UI.get(rule.id, {})
        cat = dict(
            rule_id=rule.id,
            title_zh=rule.title_zh,
            group=rule.group,
            scope=rule.scope,
            action=rule.action,
            match=rule.match,
            notes=rule.notes,
            ui_location=ui.get("ui_location", ""),
            content_note=ui.get("content_note", ""),
            screenshots=ui.get("screenshots", ""),
            counts={},
            ja_values=[],
            en_values=[],
            ko_values=[],
        )
        for lang in ("ja", "en", "ko"):
            st = per_lang.get(lang, {}).get("rules", {}).get(rule.id)
            if st:
                cat["counts"][lang] = dict(
                    occurrences=st["occurrences"],
                    unique_keys=st["unique_keys"],
                    unique_values=st["unique_values"],
                    empty_values=st["empty_values"],
                )
            else:
                cat["counts"][lang] = None
            cat[f"{lang}_values"] = name_values.get(lang, {}).get(rule.id, [])
        names_json["categories"][rule.id] = cat

    # ---------------- 7) rules.json ----------------
    rules_json = dict(
        generated_at="2026-10-25",
        project="NieR Re[in]carnation zh-l10n",
        input=dict(
            text_dir=str(args.text_dir),
            masterdata_dir=str(args.masterdata_dir),
            langs=list(per_lang.keys()),
        ),
        legend=dict(
            action=dict(
                skip="整条不译（写回时保留原行）",
                protect="不做整条跳过，只加入句中保护词典",
                marker="英文记号保留（句中保护）",
            ),
            scope=dict(
                mandatory="用户明确要求不翻译",
                recommended="同一命名体系，建议不翻译（待确认）",
                optional="可选/需产品决策",
            ),
            match=dict(
                key_prefix="key 以任一前缀开头",
                key_regex="key 匹配正则",
                value_regex="value 整值匹配正则",
                bundles="限定 bundle（可选）",
            ),
            ui=dict(
                ui_location="该规则文本在游戏界面中的位置（界面路径 + 界面上的位置）",
                content_note="对应内容说明：界面上长什么样、为什么不能译、如果译了会怎样",
                screenshots="对应用户截图编号（图片1-10）；空=未截图",
            ),
        ),
        rules=[],
        masterdata_rules=md_checks.get("masterdata_rules", []),
    )
    for rule in rules:
        ui = RULE_UI.get(rule.id, {})
        entry = dict(
            rule_id=rule.id,
            title_zh=rule.title_zh,
            group=rule.group,
            scope=rule.scope,
            action=rule.action,
            match=rule.match,
            user_evidence=rule.user_evidence,
            notes=rule.notes,
            risk=rule.risk,
            ui_location=ui.get("ui_location", ""),
            content_note=ui.get("content_note", ""),
            screenshots=ui.get("screenshots", ""),
            counts={
                lang: per_lang[lang]["rules"][rule.id]
                for lang in per_lang
            },
            samples=per_lang.get("ja", {}).get("rules", {}).get(rule.id, {}).get("samples", []),
        )
        rules_json["rules"].append(entry)
    rules_json["summary"] = {
        lang: dict(
            total_rows=per_lang[lang]["total_rows"],
            skip_rows=per_lang[lang]["skip_rows"],
            skip_unique_keys=per_lang[lang]["skip_unique_keys"],
            translatable_rows=per_lang[lang]["translatable_rows"],
        )
        for lang in per_lang
    }

    # ---------------- 8) 截图条目定位报告 ----------------
    locate = []
    md_plain_values: list[str] = []
    for boss in md_checks["bighunt_boss"]:
        md_plain_values.append(boss.get("ja", ""))
    for t in md_checks["webview_mission_titles"]:
        md_plain_values.append(t.get("ja", ""))
    all_excl_values: list[str] = []
    for rule in rules:
        if rule.group in PROTECT_GROUPS:
            all_excl_values.extend(name_values.get("ja", {}).get(rule.id, []))
    all_excl_values.extend(md_plain_values)
    raw_set = set(all_excl_values)
    normalized_set = set(v.strip().strip("「」『』").strip() for v in all_excl_values)

    for item in SCREENSHOT_ITEMS:
        detail = []
        located = 0
        for exp in item["expected"]:
            candidates_exp = [exp, exp.replace("\\n", "\n")]
            matched = []
            for c in candidates_exp:
                if c in raw_set or c.strip().strip("「」『』").strip() in normalized_set:
                    matched.append("value")
            hit_rules = []
            for rule in rules:
                if rule.group not in PROTECT_GROUPS:
                    continue
                values = name_values.get("ja", {}).get(rule.id, [])
                if any(n in values or n.strip().strip("「」『』").strip() in {v.strip().strip("「」『』").strip() for v in values} for n in candidates_exp):
                    hit_rules.append(rule.id)
            if matched:
                located += 1
            detail.append(dict(expected=exp, located=bool(matched), matched_rules=hit_rules))
        locate.append(
            dict(
                item=item["item"],
                status="located" if located == len(item["expected"]) else ("partial" if located else "not_located"),
                located_count=located,
                expected_count=len(item["expected"]),
                rule_ids=item["rule_ids"],
                details=detail,
            )
        )
    # 讨伐战/章节名等用 masterdata 再确认
    locate_json = dict(
        generated_at="2026-10-25",
        summary=dict(
            total_items=len(locate),
            located=sum(1 for x in locate if x["status"] == "located"),
            partial=sum(1 for x in locate if x["status"] == "partial"),
            not_located=sum(1 for x in locate if x["status"] == "not_located"),
        ),
        items=locate,
        screenshot_transcript=SCREENSHOT_TRANSCRIPT,
        r01_coverage=r01_coverage,
        anecdote_titles=anecdote_report,
        masterdata_crosscheck=md_checks,
    )

    # ---------------- 9) 写文件 ----------------
    write_json(out_dir / "names.json", names_json)
    write_json(out_dir / "rules.json", rules_json)
    write_json(out_dir / "locate_report.json", locate_json)

    # v2.0 附录产物：界面内容对照 / R01 截图覆盖 / 挿話 8 标题对照
    write_tsv(
        out_dir / "rule_ui_map.tsv",
        ["kind", "rule_id", "title_zh", "action", "scope", "ui_location", "content_note", "screenshots", "ja_rows"],
        [
            [r["kind"], r["rule_id"], r["title_zh"], r["action"], r["scope"],
             r["ui_location"], r["content_note"], r["screenshots"], r["ja_rows"]]
            for r in rule_ui_rows
        ],
    )
    write_tsv(
        out_dir / "r01_chapters.tsv",
        ["order", "key", "season", "route", "chapter", "value_ja", "screenshot_images", "evidence", "note"],
        [
            [r["order"], r["key"], r["season"], r["route"], r["chapter"], r["value"],
             r["screenshot_images"], r["evidence"], r["note"]]
            for r in r01_rows
        ],
    )
    write_tsv(
        out_dir / "anecdote_titles.tsv",
        ["title_id", "ja", "en", "ko", "webview_mission_id", "mission_group_id", "label_mission_text_id",
         "text_pack_key", "text_pack_ja", "text_pack_en", "text_pack_ko", "coverage", "text_pack_match", "note"],
        [
            [r["title_id"], r["ja"], r["en"], r["ko"], r["webview_mission_id"], r["mission_group_id"],
             r["label_mission_text_id"], r["text_pack_key"], r["text_pack_ja"], r["text_pack_en"],
             r["text_pack_ko"], r["coverage"], r["text_pack_match"], r["note"]]
            for r in anecdote_rows
        ],
    )

    # english_terms.tsv（逐字记号 + 正则型记号）
    term_header = [
        "kind", "term", "type", "decision", "boundary", "protect_regex",
        "ja_occurrences", "ja_rows", "ja_unique_values",
        "en_occurrences", "en_rows", "en_unique_values",
        "ja_example_key", "en_example_key", "note",
    ]

    def term_row(kind: str, r: dict) -> list:
        return [
            kind, r["term"], r["type"], r["decision"], r["boundary"], r["protect_regex"],
            r["ja_occurrences"], r["ja_rows"], r["ja_unique_values"],
            r["en_occurrences"], r["en_rows"], r["en_unique_values"],
            r["ja_example_key"], r["en_example_key"], r["note"],
        ]

    term_rows = [term_row("literal", r) for r in marker_rows] + [term_row("pattern", r) for r in pattern_rows]
    write_tsv(out_dir / "english_terms.tsv", term_header, term_rows)
    write_tsv(
        out_dir / "english_terms_candidates.tsv",
        ["term", "ja_occurrences", "en_occurrences", "ja_example_key", "decision"],
        [[r["term"], r["ja_occurrences"], r["en_occurrences"], r["ja_example_key"], r["decision"]] for r in candidates[:800]],
    )
    write_tsv(
        out_dir / "markup_tokens.tsv",
        ["kind", "token", "occurrences", "example_key", "note"],
        [[r["kind"], r["token"], r["occurrences"], r["example_key"], r["note"]] for r in markup_rows],
    )
    write_tsv(
        out_dir / "protect_terms.tsv",
        ["lang", "group", "categories", "term", "char_len", "non_name_hits", "risk", "recommended_action"],
        [
            [r["lang"], r["group"], ",".join(r["categories"]), r["term"], r["char_len"], r["non_name_hits"], r["risk"], r["recommended_action"]]
            for r in merged_terms
        ],
    )
    write_tsv(
        out_dir / "english_sentences_ja.tsv",
        ["decision", "dir", "bundle", "key", "value"],
        [[r["decision"], r["dir"], r["bundle"], r["key"], short(r["value"], 260)] for r in english_sentence_samples],
    )

    # stats.json
    stats_json = dict(
        generated_at="2026-10-25",
        langs={
            lang: dict(
                path=per_lang[lang]["path"],
                total_rows=per_lang[lang]["total_rows"],
                unique_keys=per_lang[lang]["unique_keys"],
                duplicate_key_count=per_lang[lang]["duplicate_key_count"],
                skip_rows=per_lang[lang]["skip_rows"],
                skip_unique_keys=per_lang[lang]["skip_unique_keys"],
                translatable_rows=per_lang[lang]["translatable_rows"],
                translatable_unique_values=per_lang[lang]["translatable_unique_values"],
                translatable_unique_chars=per_lang[lang]["translatable_unique_chars"],
                values_with_literal_backslash_n=per_lang[lang]["values_with_literal_backslash_n"],
                english_sentence_count=per_lang[lang]["english_sentence_count"],
                dir_stats=per_lang[lang]["dir_stats"],
                rule_counts={
                    rid: dict(occurrences=v["occurrences"], unique_keys=v["unique_keys"], unique_values=v["unique_values"])
                    for rid, v in per_lang[lang]["rules"].items()
                },
            )
            for lang in per_lang
        },
        inconsistent_key_values=inconsistent_summary,
        english_sentence_classification=dict(english_sentence_class),
        english_sentence_by_prefix=dict(english_sentence_by_prefix.most_common(40)),
        marker_terms=len(marker_rows),
        marker_terms_with_data=sum(1 for r in marker_rows if r["ja_occurrences"] or r["en_occurrences"]),
        pattern_terms=len(pattern_rows),
        pattern_terms_with_data=sum(1 for r in pattern_rows if r["ja_occurrences"] or r["en_occurrences"]),
        markdown_tokens=len(markup_rows),
        special_text=dict(
            encoded_story_text_occurrences=per_lang.get("ja", {}).get("rules", {}).get("R17_encoded_story_text", {}).get("occurrences", 0),
            decorative_english_occurrences=per_lang.get("ja", {}).get("rules", {}).get("R18_decorative_english", {}).get("occurrences", 0),
            weapon_story_ascii_occurrences=per_lang.get("ja", {}).get("rules", {}).get("R19_weapon_story_ascii_content", {}).get("occurrences", 0),
            cage_memory_ascii_occurrences=per_lang.get("ja", {}).get("rules", {}).get("R20_cage_memory_ascii_logs", {}).get("occurrences", 0),
        ),
        unclassified_ascii_candidates=len(candidates),
        protect_terms=dict(
            total=len(merged_terms),
            by_risk=dict(collections.Counter(r["risk"] for r in merged_terms)),
            by_lang=dict(collections.Counter(r["lang"] for r in merged_terms)),
        ),
        r01_coverage=r01_coverage,
        anecdote_titles=anecdote_report["coverage"],
        ui_notes=dict(
            rules_with_ui_location=sum(1 for r in rule_ui_rows if r.get("ui_location")),
            rules_total=len(rule_ui_rows),
        ),
        masterdata_crosscheck=md_checks,
    )
    write_json(out_dir / "stats.json", stats_json)

    # evidence.md
    ev = []
    ev.append("# 排除项证据样例（自动生成，勿手改）\n")
    ev.append(f"生成脚本：`{Path(__file__).name}`；输入：`{args.text_dir}`、`{args.masterdata_dir}`。\n")
    ev.append("## 1. 规则命中样例（JA 槽）\n")
    for rule in rules:
        st = per_lang.get("ja", {}).get("rules", {}).get(rule.id)
        ev.append(f"### {rule.id} — {rule.title_zh}\n")
        if not st:
            ev.append("（无数据）\n")
            continue
        ev.append(
            f"- scope=`{rule.scope}` action=`{rule.action}`；命中 {st['occurrences']} 行 / "
            f"{st['unique_keys']} key / {st['unique_values']} 唯一值 / {len(st['bundles'])} bundle；空值 {st['empty_values']}\n"
        )
        ev.append(f"- 匹配：`{json.dumps(rule.match, ensure_ascii=False)}`\n")
        ev.append("```\n")
        for s in st["samples"]:
            ev.append(f"{s['bundle']} | {s['key']} | {s['value']}\n")
        ev.append("```\n")
    ev.append("## 2. masterdata 侧排除规则（与 task D 对齐）\n")
    for mdr in md_checks.get("masterdata_rules", []):
        ev.append(
            f"### {mdr['rule_id']} — {mdr['title_zh']}\n"
            f"- table=`{mdr['table']}` id_column=`{mdr['id_column']}` text_column=`{mdr['text_column']}` "
            f"language_column=`{mdr.get('language_column')}` action=`{mdr['action']}` scope=`{mdr['scope']}`；"
            f"命中 {mdr.get('hit_count')} 行（status={mdr.get('status')}）\n"
            f"- 策略：{mdr['policy']}\n- 说明：{mdr['note']}\n"
        )
        for row in (mdr.get("rows") or [])[:12]:
            ev.append(f"```\n{json.dumps(row, ensure_ascii=False)}\n```\n")
    ev.append("\n## 3. masterdata 交叉校验\n")
    for boss in md_checks["bighunt_boss"]:
        ev.append(f"- 讨伐战 BOSS {boss['BigHuntBossId']} textId={boss['text_id']} ja={boss['ja']} en={boss['en']}\n")
    ev.append("\n### 挿話标题表 EntityMWebviewMissionTitleTextTable\n")
    for t in md_checks["webview_mission_titles"]:
        ev.append(f"- id={t['text_id']} ja={t['ja']} en={t['en']} ko={t['ko']}\n")
    ev.append("\n### 活动章节 key 覆盖\n")
    ev.append(f"- {json.dumps(md_checks['event_quest_chapter'], ensure_ascii=False)}\n")
    ev.append("\n### 名称类 textId 覆盖\n")
    for c in md_checks["name_text_id_coverage"]:
        ev.append(f"- {json.dumps(c, ensure_ascii=False)}\n")
    ev.append("\n## 3. 英文句子（JP 槽）分类\n")
    for k, v in english_sentence_class.items():
        ev.append(f"- {k}: {v}\n")
    ev.append("\n## 4. 规则 ↔ 界面内容对照（v2.0，完整见 rule_ui_map.tsv）\n")
    for r in rule_ui_rows:
        ev.append(
            f"### {r['rule_id']}（{r['kind']}）— {r['title_zh']}\n"
            f"- 动作：`{r['action']}` / scope=`{r['scope']}`；ja 命中 {r['ja_rows']} 行；截图：{r['screenshots'] or '（未截图）'}\n"
            f"- 界面位置：{r['ui_location']}\n- 对应内容：{r['content_note']}\n"
        )
    ev.append("\n## 5. 地图章节列表 R01 截图覆盖（v2.0，完整见 r01_chapters.tsv）\n")
    ev.append(
        f"- 结论：{r01_coverage['conclusion']}\n"
        f"- 总数 {r01_coverage['total']}；地图可见 {r01_coverage['display_total']}；截图内 {r01_coverage['in_screenshot']}；"
        f"截图外 {r01_coverage['outside_count']}（其中非显示 {len(r01_coverage['non_display'])}）\n"
    )
    for r in r01_rows:
        ev.append(
            f"- {r['order']:>2}. {r['key']} = {r['value']} | 截图={r['screenshot_images'] or '-'} | {r['evidence']}"
            + (f" | {r['note']}" if r['note'] else "") + "\n"
        )
    ev.append("\n## 6. 『挿話：xxx』8 标题 ↔ 主数据/文本包 key 对照（v2.0，完整见 anecdote_titles.tsv）\n")
    for r in anecdote_rows:
        ev.append(
            f"- title_id={r['title_id']} ja={r['ja']} | webview_mission={r['webview_mission_id']} "
            f"group={r['mission_group_id']} label={r['label_mission_text_id']} | {r['text_pack_key']} "
            f"| coverage={r['coverage']} match={r['text_pack_match']} | {r['note']}\n"
        )
    ev.append("\n### 语义\n")
    for k, v in anecdote_report["semantics"].items():
        ev.append(f"- `{k}`: {v}\n")
    with open_utf8(out_dir / "evidence.md", "w") as f:
        f.write("".join(ev))

    # 日志
    with open_utf8(out_dir / "_build.log", "w") as f:
        f.write("\n".join(log_lines) + "\n")
        f.write(
            f"outputs: names.json rules.json english_terms.tsv english_terms_candidates.tsv "
            f"markup_tokens.tsv protect_terms.tsv english_sentences_ja.tsv stats.json "
            f"locate_report.json evidence.md rule_ui_map.tsv r01_chapters.tsv anecdote_titles.tsv\n"
        )

    log(f"[done] 输出目录：{out_dir}")
    log(f"[done] 规则 {len(rules)} 条；英文记号白名单 {len(marker_rows)}+{len(pattern_rows)} 条"
        f"（有数据 {stats_json['marker_terms_with_data']}+{stats_json['pattern_terms_with_data']}）；"
        f"未归类候选 {len(candidates)} 条；保护词条 {len(merged_terms)}")
    log(f"[done] 附录：rule_ui_map.tsv {len(rule_ui_rows)} 条；r01_chapters.tsv {len(r01_rows)} 条"
        f"（截图内 {r01_coverage['in_screenshot']}）；anecdote_titles.tsv {len(anecdote_rows)} 条")
    return 0


if __name__ == "__main__":
    sys.exit(main())
