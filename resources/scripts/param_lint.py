#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
param_lint.py — 参数来源与数值一致性检查器（method-writer Skill 的执行内核）

解决的问题：方法与实验章节里最难保证的是"每个数值都有来源、正文与配置/日志一致、
没有为了段落顺畅补出来的数字"。本脚本把这件事做成可复核的机械检查：

  1. 从配置文件（json / yaml / toml / ini / env）抽取 key 与取值
  2. 从实验日志与代码中抽取超参与常量赋值
  3. 从章节草稿（markdown）中抽取"参数名 + 数值 + 单位"
  4. 三方比对，分出四类结果：
       matched   正文数值有来源且一致
       conflict  正文数值与来源不一致（高优先级，必须修）
       orphan    正文出现但材料里查不到（疑似新增事实，必须确认或删）
       missing   材料里有但正文未写（覆盖不全，建议补）

子命令：
  scan   扫描材料目录 → materials.json（key/value 台账，带文件与行号锚点）
  check  比对草稿 → lint_report.json + lint_report.md
  init   生成草稿模板骨架（六段 + 参数表，供第 4 步填写）

用法：
  python3 param_lint.py scan  --materials /app/work/materials --out /app/work/materials.json
  python3 param_lint.py check --materials-json /app/work/materials.json \
                              --draft /app/output/method_experiment_draft.md \
                              --out /app/work
  python3 param_lint.py init  --out /app/output/method_experiment_draft.md

设计原则：
  * 只读材料，不修改；所有结论都带 文件:行号 锚点，便于人工回查。
  * 不做语义猜测：orphan 只是"没找到来源"，由作者确认，不自动删除。
  * 零第三方依赖，标准库即可运行。
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path


def _as_outfile(p, default_name):
    """--out 兼容层：传目录则写入目录下 default_name，传文件名则直接写该文件。"""
    path = Path(p)
    if path.is_dir() or not path.suffix:
        path = path / default_name
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def _as_outdir(p):
    """--out 兼容层：传的是文件名时取其父目录，避免把文件路径当目录用而崩溃。"""
    path = Path(p)
    if path.suffix.lower() in (".json", ".md", ".txt", ".yaml", ".yml", ".csv", ".tex", ".bib"):
        path = path.parent if str(path.parent) not in ("", ".") else Path(".")
    path.mkdir(parents=True, exist_ok=True)
    return path

TEXT_EXT = {".json", ".yaml", ".yml", ".toml", ".ini", ".cfg", ".conf", ".env",
            ".log", ".txt", ".out", ".csv", ".md", ".py", ".sh", ".yaml5"}
CONFIG_EXT = {".json", ".yaml", ".yml", ".toml", ".ini", ".cfg", ".conf", ".env"}
LOG_EXT = {".log", ".txt", ".out"}
CODE_EXT = {".py", ".sh"}

NUM_RE = re.compile(r"^[+-]?(?:\d+\.?\d*|\.\d+)(?:[eE][+-]?\d+)?%?$")
KV_LINE = re.compile(r"^[\s\-\*\|\"']*([A-Za-z_][\w\.\-]{1,60})[\"']?\s*[:=]\s*[\"']?([^\"'\n,#]{1,80})")
LOG_KV = re.compile(r"\b([A-Za-z_][\w\.\-]{2,40})\s*[:=]\s*([+-]?(?:\d+\.?\d*|\.\d+)(?:[eE][+-]?\d+)?%?)(?=$|[\s,;\)\]])")
UNIT_HINT = re.compile(r"(ms|s|sec|min|h|hr|gb|mb|kb|tb|fps|epochs?|steps?|layers?|heads?|dims?|tokens?|images?|samples?|batch(?:es)?|%)", re.I)

# 常见同义写法归一，减少 orphan 误报
ALIASES = {
    "lr": "learning_rate", "learningrate": "learning_rate", "learning-rate": "learning_rate",
    "bs": "batch_size", "batchsize": "batch_size", "batch-size": "batch_size",
    "bsz": "batch_size", "train_batch_size": "batch_size",
    "epoch": "epochs", "num_epochs": "epochs", "n_epochs": "epochs", "max_epochs": "epochs",
    "seed": "random_seed", "randomseed": "random_seed", "random-seed": "random_seed",
    "weight_decay": "weight_decay", "wd": "weight_decay",
    "opt": "optimizer", "optim": "optimizer",
    "n_layers": "num_layers", "numlayer": "num_layers", "layers": "num_layers",
    "n_heads": "num_heads", "heads": "num_heads",
    "hidden": "hidden_size", "hidden_dim": "hidden_size", "d_model": "hidden_size",
    "drop": "dropout", "dropout_rate": "dropout", "p_drop": "dropout",
    "gpu": "device", "device_type": "device",
    "val_split": "val_ratio", "validation_split": "val_ratio", "test_split": "test_ratio",
}


def norm_key(k):
    k = k.strip().strip("\"'`").lower()
    k = re.sub(r"[\s\-]+", "_", k)
    k = re.sub(r"_+", "_", k)
    return ALIASES.get(k, k)


def clean_val(v):
    v = str(v)
    v = v.replace("\\n", " ").replace("\\t", " ").replace("\\r", " ")
    v = v.strip().strip("\"'`").rstrip(",;").strip()
    v = re.sub(r"\s+", " ", v)
    return v[:200]


def is_number(v):
    return bool(NUM_RE.match(str(v).strip()))


def num_equal(a, b, unit_a="", tol=1e-9):
    sa, sb = str(a).strip(), str(b).strip()
    pa, pb = sa.endswith("%"), sb.endswith("%")
    try:
        x, y = float(sa.rstrip("%")), float(sb.rstrip("%"))
    except Exception:
        return sa.lower() == sb.lower()
    # 一边用百分比、一边用小数（80% 与 0.8）是同一取值，不能判为冲突
    if pa and not pb:
        x = x / 100.0
    elif unit_a.strip() == "%" and not pb and 0 < y < 1:
        x = x / 100.0   # 正文写 80%，配置写 0.8，属同一取值
    elif pb and not pa:
        y = y / 100.0
    if x == y:
        return True
    return abs(x - y) <= tol * max(1.0, abs(x), abs(y))


# ---------------------------------------------------------------- 配置解析

def flatten_json(obj, prefix=""):
    out = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            key = f"{prefix}.{k}" if prefix else str(k)
            out.extend(flatten_json(v, key))
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            out.extend(flatten_json(v, f"{prefix}[{i}]"))
    else:
        out.append((prefix, obj))
    return out


def parse_config(path):
    """返回 [(key, value, lineno)]"""
    res = []
    ext = path.suffix.lower()
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return res
    if ext == ".json":
        try:
            data = json.loads(text)
            for k, v in flatten_json(data):
                res.append((k, v, 0))
            return res
        except Exception:
            pass
    section = ""
    for i, raw in enumerate(text.splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith(("#", "//", ";")):
            continue
        if ext in (".ini", ".cfg", ".conf") and re.match(r"^\[.+\]$", line):
            section = line.strip("[]")
            continue
        m = re.match(r"^\s*([A-Za-z_][\w\.\-]{0,60})\s*[:=]\s*(.+?)\s*$", raw)
        if not m:
            continue
        k, v = m.group(1), m.group(2)
        if ext in (".toml",) and v.startswith("["):
            continue
        key = f"{section}.{k}" if section else k
        res.append((key, clean_val(v), i))
    return res


def parse_log(path):
    """日志里的超参打印行：key=value / key: value，只保留数值型"""
    res = []
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    except Exception:
        return res
    for i, line in enumerate(lines, 1):
        if len(line) > 2000:
            continue
        for m in LOG_KV.finditer(line):
            k, v = m.group(1), m.group(2)
            if k.lower() in ("line", "time", "elapsed", "duration", "size", "total"):
                continue
            res.append((k, v, i))
    return res


def parse_code(path):
    """代码常量与 CLI 默认值"""
    res = []
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    except Exception:
        return res
    for i, line in enumerate(lines, 1):
        m = re.match(r"^\s*([A-Z][A-Z0-9_]{2,40})\s*=\s*(.+?)\s*(?:#.*)?$", line)
        if m and is_number(clean_val(m.group(2))):
            res.append((m.group(1), clean_val(m.group(2)), i))
        m2 = re.search(r"add_argument\(\s*[\"']--([\w\-]{2,40})[\"'][^)]*default\s*=\s*([-\d\.eE]+)", line)
        if m2:
            res.append((m2.group(1), m2.group(2), i))
        m3 = re.match(r"^\s*([a-z_][\w]{2,40})\s*:\s*(?:int|float)\s*=\s*([-\d\.eE]+)", line)
        if m3:
            res.append((m3.group(1), m3.group(2), i))
    return res


def cmd_scan(args):
    root = Path(args.materials)
    inv = {}
    files_scanned, skipped = [], []
    if not root.exists():
        print(json.dumps({"ok": False, "error": f"材料目录不存在: {root}"}, ensure_ascii=False))
        return 1
    targets = [root] if root.is_file() else sorted(p for p in root.rglob("*") if p.is_file())
    for p in targets:
        if p.stat().st_size > 5 * 1024 * 1024:
            skipped.append({"file": str(p), "reason": ">5MB"})
            continue
        ext = p.suffix.lower()
        if ext not in TEXT_EXT:
            skipped.append({"file": str(p), "reason": "非文本类型"})
            continue
        if ext in CONFIG_EXT:
            pairs, src = parse_config(p), "config"
        elif ext in LOG_EXT:
            pairs, src = parse_log(p), "log"
        elif ext in CODE_EXT:
            pairs, src = parse_code(p), "code"
        else:
            skipped.append({"file": str(p), "reason": "非参数来源类型"})
            continue
        files_scanned.append(str(p))
        for k, v, ln in pairs:
            nk = norm_key(k)
            entry = inv.setdefault(nk, {"key": nk, "raw_keys": set(), "values": [], "sources": []})
            entry["raw_keys"].add(k)
            entry["values"].append({"value": clean_val(v), "source": src, "file": str(p), "line": ln})
            entry["sources"].append(f"{src}:{Path(p).name}:{ln}")
    for v in inv.values():
        v["raw_keys"] = sorted(v["raw_keys"])
        # 取值去重但保留来源
        seen, uniq = set(), []
        for it in v["values"]:
            sig = (str(it["value"]), it["file"], it["line"])
            if sig not in seen:
                seen.add(sig)
                uniq.append(it)
        v["values"] = uniq
        v["distinct_values"] = sorted({str(it["value"]) for it in uniq})
    out = {"ok": True, "materials_root": str(root), "files_scanned": files_scanned,
           "skipped": skipped, "param_count": len(inv), "inventory": inv}
    _p = _as_outfile(args.out, "materials.json")
    _p.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"ok": True, "out": args.out, "param_count": len(inv),
                      "files_scanned": len(files_scanned), "skipped": len(skipped)},
                     ensure_ascii=False))
    return 0


# ---------------------------------------------------------------- 草稿解析

DRAFT_PATTERNS = [
    # key = 1e-4 / key: 1e-4 / key 为 1e-4
    re.compile(r"([A-Za-z_][\w\.\-]{1,60})\s*(?:=|:|为|是|取)\s*([+-]?(?:\d+\.?\d*|\.\d+)(?:[eE][+-]?\d+)?%?)\s*([A-Za-z%]{0,12})"),
    # | key | 1e-4 |  (markdown 表格)
    re.compile(r"\|\s*([A-Za-z_][\w\.\- ]{1,60})\s*\|\s*([+-]?(?:\d+\.?\d*|\.\d+)(?:[eE][+-]?\d+)?%?)\s*\|"),
    # 反引号 key` 与数值在同段
    re.compile(r"`([A-Za-z_][\w\.\-]{1,60})`[^\n\d]{0,20}([+-]?(?:\d+\.?\d*|\.\d+)(?:[eE][+-]?\d+)?%?)"),
]

# 数值在前、单位/量名在后：30 epochs / 64 batch / 8 layers
VALUE_FIRST = re.compile(
    r"([+-]?(?:\d+\.?\d*|\.\d+)(?:[eE][+-]?\d+)?)\s+"
    r"(epochs?|steps?|iterations?|layers?|heads?|batch(?:es)?|seeds?|repeats?|trials?)\b", re.I)


PROSE_NUM = re.compile(
    r"(?<![\w.])([+-]?(?:\d+(?:\.\d+)?|\.\d+)(?:[eE][+-]?\d+)?)\s*(%|[A-Za-zμ°][A-Za-z°/·μ]{0,12})?")
# 数值与参数名之间的连接成分（"a batch size **of** 128" / "seed **was fixed at** 42"）
CONNECT = re.compile(
    r"^[\s_,]*(?:(?:was|were|is|are|has been|had been|of|set to|fixed at|fixed to|"
    r"initialized to|initialised to|chosen as|taken as|used|reaches|reached|=|:|为|是|取|设为|设置为|达到)"
    r"[\s_,]*)*$", re.I)
# 行文中常见的口语化写法（不在代码别名里，但论文正文经常这么写）
PROSE_ALIASES = {
    "hidden dimension": "hidden_size", "hidden dimensions": "hidden_size",
    "hidden layer size": "hidden_size", "hidden units": "hidden_size",
    "batch size": "batch_size", "batch sizes": "batch_size", "mini-batch size": "batch_size",
    "learning rate": "learning_rate", "initial learning rate": "learning_rate",
    "random seed": "random_seed", "random seeds": "random_seed", "seed value": "random_seed",
    "number of layers": "num_layers", "layer count": "num_layers", "depth": "num_layers",
    "number of epochs": "epochs", "training epochs": "epochs",
    "training set": "train_ratio", "validation set": "val_ratio", "test set": "test_ratio",
    "peak memory": "peak_memory", "gpu memory": "peak_memory",
}
# 比值类参数在行文里常写成 "80% training / 10% validation"
RATIO_WORDS = {"training": "train_ratio", "train": "train_ratio",
               "validation": "val_ratio", "valid": "val_ratio", "dev": "val_ratio",
               "test": "test_ratio", "testing": "test_ratio"}


def key_variants(inv_keys):
    """把材料里的 canonical key 展开成行文中可能出现的写法，长的优先。"""
    vs = {}
    for k in inv_keys:
        vs[k.replace("_", " ")] = k
        vs[k] = k
        for a, c in ALIASES.items():
            if c == k:
                vs[a.replace("_", " ")] = k
                vs[a] = k
        for a, c in PROSE_ALIASES.items():
            if c == k:
                vs[a] = k
                vs[a.replace(" ", "_")] = k
        for pre in ("train_", "training_", "model_", "opt_", "optimizer_"):
            if k.startswith(pre) and len(k) > len(pre) + 2:
                vs[k[len(pre):].replace("_", " ")] = k
    return sorted(((p, c) for p, c in vs.items() if len(p) >= 3), key=lambda x: -len(x[0]))


def prose_mentions(line, variants):
    """从行文句子里抽取「参数名 + 取值」，解决只在散文里写参数时的漏检。"""
    out, low = [], line.lower()
    for m in PROSE_NUM.finditer(low):
        val, unit = m.group(1), (m.group(2) or "").strip()
        head = low[max(0, m.start() - 60):m.start()]
        best = None
        for phrase, canon in variants:
            idx = head.rfind(phrase)
            if idx < 0 or not CONNECT.match(head[idx + len(phrase):]):
                continue
            if best is None or len(phrase) > best[0]:
                best = (len(phrase), canon, head[idx:])
        if best:
            out.append({"raw_key": best[2].strip()[-40:], "key": best[1], "value": val,
                        "unit": unit, "line": None, "snippet": line.strip()[:180]})
            continue
        tail = low[m.end():m.end() + 24]
        w = re.match(r"^[\s%]*(?:of\s+(?:the\s+)?)?([a-z]{4,12})", tail)
        if w and w.group(1) in RATIO_WORDS:
            out.append({"raw_key": w.group(1), "key": RATIO_WORDS[w.group(1)], "value": val,
                        "unit": unit, "line": None, "snippet": line.strip()[:180]})
    return out


def parse_draft(path, inv_keys=()):
    res = []
    try:
        lines = Path(path).read_text(encoding="utf-8", errors="replace").splitlines()
    except Exception as e:
        return res, f"读取草稿失败: {e}"
    variants = key_variants(inv_keys) if inv_keys else []
    for i, line in enumerate(lines, 1):
        if len(line) > 3000:
            continue
        for pat in DRAFT_PATTERNS:
            for m in pat.finditer(line):
                k, v = m.group(1), m.group(2)
                unit = m.group(3) if m.lastindex and m.lastindex >= 3 else ""
                res.append({"raw_key": k.strip(), "key": norm_key(k), "value": clean_val(v),
                            "unit": (unit or "").strip(), "line": i, "snippet": line.strip()[:180]})
        for m in VALUE_FIRST.finditer(line):
            res.append({"raw_key": m.group(2), "key": norm_key(m.group(2)),
                        "value": clean_val(m.group(1)), "unit": m.group(2),
                        "line": i, "snippet": line.strip()[:180]})
        if variants and not line.lstrip().startswith(("#", "|")):
            for it in prose_mentions(line, variants):
                it["line"] = i
                res.append(it)
    # 同一行同一 key 去重
    seen, uniq = set(), []
    for r in res:
        sig = (r["key"], r["value"], r["line"])
        if sig in seen:
            continue
        seen.add(sig)
        uniq.append(r)
    return uniq, None


def cmd_check(args):
    mat = json.loads(Path(args.materials_json).read_text(encoding="utf-8"))
    inv = mat.get("inventory", {})
    draft, err = parse_draft(args.draft, list(inv.keys()))
    if err:
        print(json.dumps({"ok": False, "error": err}, ensure_ascii=False))
        return 1

    matched, conflicts, orphans = [], [], []
    for d in draft:
        ent = inv.get(d["key"])
        if not ent:
            orphans.append({
                "key": d["key"], "raw_key": d["raw_key"], "value": d["value"], "unit": d["unit"],
                "anchor": f"draft:L{d['line']}", "snippet": d["snippet"],
                "action": "确认来源：在配置/日志/代码中找到出处并补 anchor，或删去该数值",
            })
            continue
        vals = [str(x) for x in ent.get("distinct_values", [])]
        if any(num_equal(d["value"], v, d.get("unit", "")) for v in vals):
            matched.append({"key": d["key"], "value": d["value"], "source_anchor": ent["sources"][:3],
                            "anchor": f"draft:L{d['line']}"})
        else:
            conflicts.append({
                "key": d["key"], "draft_value": d["value"], "material_values": vals,
                "material_anchor": ent["sources"][:5], "anchor": f"draft:L{d['line']}",
                "snippet": d["snippet"],
                "action": "以材料原值为准修正正文，或在 uncertainties 并列两值请作者确认",
            })

    # 材料有但正文未提：只统计"数值型"参数，避免噪音
    draft_keys = {d["key"] for d in draft}
    missing = []
    for k, ent in inv.items():
        if k in draft_keys:
            continue
        numeric = [v for v in ent.get("distinct_values", []) if is_number(v)]
        if not numeric:
            continue
        missing.append({"key": k, "raw_keys": ent["raw_keys"][:3],
                        "values": numeric[:5], "anchor": ent["sources"][:2]})

    coverage = (len(matched) + len(conflicts)) / max(1, len(draft)) if draft else 0.0
    report = {
        "ok": True,
        "draft": str(args.draft),
        "materials": str(args.materials_json),
        "inventory_size": len(inv),
        "draft_numeric_mentions": len(draft),
        "matched_count": len(matched),
        "conflict_count": len(conflicts),
        "orphan_count": len(orphans),
        "missing_count": len(missing),
        "source_coverage": round(coverage, 4),
        "conflicts": conflicts,
        "orphans": orphans,
        "missing": missing[:80],
        "matched": matched[:120],
        "verification_hint": {
            "source_traceability": f"有来源参数 {len(matched) + len(conflicts)} / 正文数值提及 {len(draft)}",
            "value_consistency": f"一致 {len(matched)} / 可比对 {len(matched) + len(conflicts)}",
            "no_new_facts": f"无来源数值 {len(orphans)} 条（必须为 0 或逐条说明）",
            "element_coverage": f"材料数值型参数 {len(inv)} 个，正文未提 {len(missing)} 个",
        },
    }
    outdir = _as_outdir(args.out)
    outdir.mkdir(parents=True, exist_ok=True)
    (outdir / "lint_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    # 人读版
    md = [f"# 参数一致性报告", "",
          f"- 材料参数总数：{len(inv)}",
          f"- 正文数值提及：{len(draft)}",
          f"- 一致：{len(matched)}｜冲突：{len(conflicts)}｜无来源：{len(orphans)}｜未覆盖：{len(missing)}", ""]
    if conflicts:
        md += ["## 冲突（必须修）", ""]
        for c in conflicts:
            md.append(f"- `{c['key']}` 正文={c['draft_value']} vs 材料={c['material_values']} "
                      f"（{c['anchor']}；材料 {', '.join(c['material_anchor'][:3])}）")
        md.append("")
    if orphans:
        md += ["## 无来源数值（必须确认或删）", ""]
        for o in orphans:
            md.append(f"- `{o['raw_key']}` = {o['value']}（{o['anchor']}）— {o['snippet']}")
        md.append("")
    if missing[:40]:
        md += ["## 材料有、正文未提（建议补）", ""]
        for m in missing[:40]:
            md.append(f"- `{m['key']}` 取值候选 {m['values']}（{', '.join(m['anchor'][:2])}）")
        md.append("")
    md += ["## 自检口径建议", ""]
    for k, v in report["verification_hint"].items():
        md.append(f"- `{k}`：{v}")
    (outdir / "lint_report.md").write_text("\n".join(md), encoding="utf-8")
    print(json.dumps({k: report[k] for k in ["ok", "inventory_size", "draft_numeric_mentions",
                                            "matched_count", "conflict_count", "orphan_count",
                                            "missing_count", "source_coverage"]}, ensure_ascii=False))
    return 0


# ---------------------------------------------------------------- 模板

DRAFT_TEMPLATE = """# 方法与实验章节草稿（六段骨架，缺处标 [材料未述]）

> 由 param_lint.py init 生成。填充时每个数值后加锚点，如 `learning_rate = 1e-4`（config:train.yaml:L12）。

## 1. 方法步骤
1. 输入：<材料未述> ｜ 操作：<...> ｜ 输出：<...> ｜ 判断条件：<...>

## 2. 实验设置
### 训练
- 硬件：<材料未述> ｜ 软件与版本：<材料未述> ｜ 随机种子：<材料未述> ｜ 重复次数：<材料未述>
### 验证
- <材料未述>
### 测试
- <材料未述>

## 3. 参数与来源
| 参数 | 取值 | 单位 | 作用对象 | 来源 |
|---|---|---|---|---|
| learning_rate | <材料未述> | - | 优化器 | <config/log/code> |

## 4. 数据集与划分
| 数据集 | 版本 | 规模 | 预处理 | 划分比例 | 随机方式 | 用途 |
|---|---|---|---|---|---|---|
| <材料未述> | | | | | | |

## 5. 对照实验
| 基线 | 版本 | 同预算 | 指标 | 统计方式 | 证据 |
|---|---|---|---|---|---|
| <材料未述> | | | | | |

## 6. 可复现与限制
- 复现清单：代码版本 <材料未述>；环境 <材料未述>；数据获取 <材料未述>；命令 <材料未述>
- 限制：在 <具体失效场景> 下不适用，边界为 <...>
"""


def cmd_init(args):
    out = _as_outfile(args.out, "method_experiment_draft.md")
    out.write_text(DRAFT_TEMPLATE, encoding="utf-8")
    print(json.dumps({"ok": True, "out": str(out)}, ensure_ascii=False))
    return 0


def main():
    ap = argparse.ArgumentParser(description="参数来源与数值一致性检查器")
    sub = ap.add_subparsers(dest="cmd", required=True)
    s1 = sub.add_parser("scan"); s1.add_argument("--materials", required=True); s1.add_argument("--out", required=True)
    s2 = sub.add_parser("check"); s2.add_argument("--materials-json", required=True)
    s2.add_argument("--draft", required=True); s2.add_argument("--out", required=True)
    s3 = sub.add_parser("init"); s3.add_argument("--out", required=True)
    a = ap.parse_args()
    return {"scan": cmd_scan, "check": cmd_check, "init": cmd_init}[a.cmd](a) or 0


if __name__ == "__main__":
    sys.exit(main())
