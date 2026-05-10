# bundlewrap fork — agent-friendly AGENTS.md — implementation plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a non-intrusive, agent-oriented `AGENTS.md` (and `CLAUDE.md` symlink) at the repo root so agents using bundlewrap in their own config repos can land work safely without spelunking. Pure addition — no edits to existing docs or code.

**Architecture:** Single root file, ~185 lines, nine sections (TOC + eight content sections). Cheat-sheets for the parts the existing MkDocs site doesn't cover well (dep-keywords TLDR table, metadata.py pitfalls); links out to MkDocs for everything else. PR-able to upstream `bundlewrap/bundlewrap` as one commit. `CLAUDE.md` is a symlink to `AGENTS.md` for tools that look for the Claude-Code-flavored filename.

**Tech Stack:** Markdown only. No code changes. Verification uses `bw debug -c '<expr>'` against a scratch repo created with `bw repo create`.

**Source spec:** `docs/superpowers/specs/2026-05-10-bundlewrap-fork-agents-md-design.md` — read this first if you're picking up the plan cold.

---

## File structure

| File | Status | Purpose |
|---|---|---|
| `AGENTS.md` | new (~185 lines) | Agent-oriented entry point: safety envelope, after-change runbook, cheat-sheets, deep-dive links. |
| `CLAUDE.md` | new (symlink → `AGENTS.md`) | Single-source convenience for Claude-Code-flavored tooling. |

No other files touched.

---

## Authoring conventions (apply to every section)

- Markdown headers in `## Section Title` style (no numbering inside the file — the spec's `§3.x` numbering is an internal reference scheme, not part of the file).
- All paths to existing repo docs use the `docs/content/<...>` form (the actual file path), not `docs/<...>`.
- For each cheat-sheet section, end with a "Full reference: ..." footer linking to the canonical doc.
- No fork-specific framing. No mention of WIP branches, of mwiegand, or of "this is a fork."
- Tier-1 / tier-2 / tier-3 wording for `bw` commands is consistent across §3.5 and any references elsewhere in the file.
- Inline code with backticks for command names, file paths, attribute names, function names.
- Tables with the standard pipe-delimited GitHub Markdown syntax.
- Links to hosted docs use the canonical `https://docs.bundlewrap.org/<path>` URL form.

---

## Task 1: Create AGENTS.md skeleton

**Files:**
- Create: `AGENTS.md`

The skeleton establishes the file's structure. Sections are added one per task; content fills in section-by-section.

- [ ] **Step 1: Create the file with title, lead paragraph, and section headers**

Write `AGENTS.md` at the repo root with this exact content:

```markdown
# AGENTS.md

This file orients agents working with this BundleWrap repository. It is a safety envelope, an after-change runbook, and a small set of cheat-sheets for the parts of bundlewrap-the-language that bite agents. It is not a tutorial — for that, start with [`docs/content/guide/quickstart.md`](docs/content/guide/quickstart.md) or the hosted docs at <https://docs.bundlewrap.org>. If you are working on bundlewrap itself rather than using it, see `CONTRIBUTING.md`.

## Contents

<!-- TOC filled in Task 9 -->

## Mental model

<!-- Task 2 -->

## Glossary

<!-- Task 3 -->

## Safety envelope: bw commands

<!-- Task 4 -->

## After-change runbook

<!-- Task 5 -->

## Cheat-sheet: item dependency keywords

<!-- Task 6 -->

## Cheat-sheet: metadata.py pitfalls

<!-- Task 7 -->

## Where to look for depth

<!-- Task 8 -->
```

- [ ] **Step 2: Verify the file is well-formed Markdown**

Run: `python3 -c 'import sys; print(open("AGENTS.md").read())' | head -20`
Expected: prints the title and lead paragraph cleanly.

- [ ] **Step 3: Commit**

```bash
git add AGENTS.md
git commit -m "AGENTS.md: skeleton with section headers and lead paragraph"
```

---

## Task 2: Mental model section

**Files:**
- Modify: `AGENTS.md` (replace `<!-- Task 2 -->` placeholder under `## Mental model`)

- [ ] **Step 1: Replace the placeholder under `## Mental model` with this exact content**

The content uses a 3-backtick fence around the ASCII diagram. To avoid backtick-fence-nesting confusion in the plan, the section is shown below as plain text — write it into `AGENTS.md` exactly as shown, **with** triple-backtick fences around the diagram block:

> (begin section content)
>
> ```
> nodes ←─── groups ───→ bundles ───→ items
> ```
>
> A **node** is a machine bundlewrap manages. A **group** is a set of nodes (or nested groups) that share configuration. A **bundle** is a named set of items; a node gets a bundle by being in a group that includes it, or by listing it directly. An **item** is one managed resource — a file, a package, a service, a user.
>
> Metadata flows from many places into a single resolved view per node. Each node's resolved metadata is the merge of its own static metadata, its groups' static metadata, each loaded bundle's `metadata.py` defaults, and each loaded bundle's `metadata.py` reactors run to a fixpoint. Resolved metadata is then available to each bundle's `items.py` to compute item attributes.
>
> (end section content)

The blockquote (`>`) is a plan-rendering aid; do not include it in `AGENTS.md`. The triple-backtick fence around the ASCII diagram **is** part of the file content.

- [ ] **Step 2: Read the section back and verify it renders correctly**

Run: `sed -n '/^## Mental model/,/^## Glossary/p' AGENTS.md`
Expected: the fenced ASCII diagram followed by two paragraphs.

- [ ] **Step 3: Commit**

```bash
git add AGENTS.md
git commit -m "AGENTS.md: add mental model section"
```

---

## Task 3: Glossary section

**Files:**
- Modify: `AGENTS.md` (replace placeholder under `## Glossary`)

12 short entries, definition-list style. Each ≤ 2 lines.

- [ ] **Step 1: Replace the placeholder with this exact content**

```markdown
- **node** — a machine bundlewrap manages. Defined in `nodes/<name>.py` (or in `nodes.py`). **Rename pitfall:** the node's name is its identity for derivation. `repo.vault.password_for('<node>')` derives the secret from the name string; renaming the node silently returns a different secret (not an error, just different data). The same applies to anything else keyed by the name string (`bw hash` history, `ssh` known_hosts). Always search-and-replace the old name across the repo *before* renaming.
- **group** — a set of nodes (or nested groups) that share configuration. Defined in `groups/<name>.py` (or `groups.py`).
- **bundle** — a named set of items. A bundle directory under `bundles/<name>/` may contain `items.py`, `metadata.py`, `files/`, `templates/`.
- **`items.py`** — bundle file declaring items by attribute (`files = {...}`, `pkg_apt = {...}`, etc.). Evaluated per node, with access to that node's resolved metadata.
- **`metadata.py`** — bundle file declaring metadata `defaults` and `@metadata_reactor` functions. Reactors compute metadata derived from other metadata.
- **item** — one managed resource on a node, identified by `<type>:<name>` (e.g. `file:/etc/hosts`, `pkg_apt:nginx`).
- **item type** — the kind of resource (`file`, `pkg_apt`, `svc_systemd`, ...). Built-in types live under `bundlewrap/items/`; custom types under your repo's `items/`.
- **metadata reactor** — a `@metadata_reactor`-decorated function in `metadata.py` that returns a metadata dict. Reactors are re-run to a fixpoint until none returns changed data.
- **`@metadata_reactor.provides(...)`** — declaration of which top-level metadata key paths a reactor writes. Used for lazy resolution of `bw metadata <node> -k <key>`.
- **hook** — Python function in `hooks/<file>.py` whose name matches a bundlewrap hook event (e.g. `node_apply_start`, `item_apply_end`). Called at the corresponding lifecycle point. **Pitfall:** a hook module that fails at import time (syntax error, missing dependency) breaks any `bw` command that fires that hook lifecycle — and recovery requires fixing the hook or `git stash`. When adding a new hook, test the import in isolation first: `bw debug -c "import sys; sys.path.insert(0, 'hooks'); import <hookmodule>"`.
- **lib** — Python module under your repo's `libs/`, importable from `items.py` and `metadata.py` as `repo.libs.<modulename>`. Convention for sharing helper code across bundles.
- **`repo`** — the runtime object representing your bundlewrap repository. Available in `metadata.py` (and elsewhere) without import; gives access to `repo.nodes`, `repo.vault`, `repo.libs`.
```

- [ ] **Step 2: Spot-check the entry count (12)**

Run: `sed -n '/^## Glossary/,/^## Safety envelope/p' AGENTS.md | grep -cE '^- \*\*'`
Expected: `12`

- [ ] **Step 3: Commit**

```bash
git add AGENTS.md
git commit -m "AGENTS.md: add glossary"
```

---

## Task 4: Safety envelope section

**Files:**
- Modify: `AGENTS.md` (replace placeholder under `## Safety envelope: bw commands`)

Three tiers, with the "Interactive ≠ safe" callout immediately after tier 3.

- [ ] **Step 1: Replace the placeholder with this exact content**

```markdown
The `bw` CLI has commands that read state, commands that read state via the network, and commands that mutate state. Agents must default to tier 1 and never invoke tier 2 or tier 3 without explicit user request.

### Tier 1 — read-only, local

No working-tree changes, no network. Safe to invoke autonomously.

- `bw hash` — fingerprints the merged state of nodes/items/metadata. The primary "did my change have the expected effect" signal.
- `bw metadata <node>` — prints a node's resolved metadata. `-k <key>` prints one path.
- `bw items <node>` — lists items for a node. `bw items <node> <id>` prints one item's expected state; add `--attrs` for internal attributes, or `--preview` (`-f`) for the rendered content of a file item.
- `bw nodes` — lists nodes (with selectors).
- `bw groups` — lists groups.
- `bw debug` — interactive REPL with `repo` pre-bound; non-interactive form `bw debug -c '<expr>'`. Common probes: `repo.get_node('<name>').metadata.get('<key>', None)` (resolved metadata for one node), `repo.libs.<name>` (inspect a shared helper), `repo.path` (absolute repo path).
- `bw test` — repo-level sanity (compiles every node, checks for collisions, etc.).
- `bw plot` — emits a Graphviz dot file of dependencies.
- `bw pw` — derive/encrypt/decrypt secrets to **stdout**. Tier 1 only when `-f` is not used.

### Tier 2 — read-only, networked

No mutation, but reaches out to nodes via SSH or other network calls.

- `bw verify <node>` — SSHes into the node and compares actual state to declared state. Reports differences without changing anything.

### Tier 3 — mutating, requires explicit user request

Changes the working tree, the network, or remote node state. Never invoke without a direct user instruction for that specific command on that specific target.

- `bw apply <node>` — applies declared state to the node. Mutates the node.
- `bw run <target> "<cmd>"` — runs a shell command on the target. Mutates the node.
- `bw lock add <node>` / `bw lock remove <node>` — soft-locks items on a node.
- `bw ipmi <node> "<cmd>"` — runs `ipmitool` against the node's BMC. Can power-cycle hardware.
- `bw pw -f` — same crypto operations as tier-1 `bw pw`, but writes the result to a file under `data/`.
- `bw repo create`, `bw repo bundle create <name>` — scaffold new files into the working tree.

**Interactive mode (`bw apply -i`) is still tier 3.** The `-i` flag prompts a human before each item; the prompt is for the human, not a safety belt for an agent. Do not invoke `bw apply -i` autonomously any more than plain `bw apply`.
```

- [ ] **Step 2: Verify each command name in the section actually exists in the parser**

Run:
```bash
for cmd in hash metadata items nodes groups debug test plot pw verify apply run lock ipmi repo; do
    grep -q "\"$cmd\"" bundlewrap/cmdline/parser.py && echo "OK: bw $cmd" || echo "MISSING: bw $cmd"
done
```
Expected: all `OK:` lines, no `MISSING:`.

- [ ] **Step 3: Commit**

```bash
git add AGENTS.md
git commit -m "AGENTS.md: add bw command safety envelope (tiered)"
```

---

## Task 5: After-change runbook section

**Files:**
- Modify: `AGENTS.md` (replace placeholder under `## After-change runbook`)

Table keyed by what the agent edited, plus a hash-diff workflow snippet.

- [ ] **Step 1: Replace the placeholder with this exact content**

````markdown
After making any change to a bundlewrap config repo, run the first check from the row that matches what you edited. If the first check shows a diff or change, drill in with the second column. **`bw hash` accepts only literal node or group names** — selectors like `bundle:<x>` and `group:<name>` work for `bw apply`, `bw run`, `bw nodes`, etc., but NOT for `bw hash`. To scope to a bundle, enumerate nodes first (`bw nodes bundle:<x>`) and hash each.

| You changed | First check | Drill-in |
|---|---|---|
| `bundles/<x>/items.py` | `bw hash` (whole repo) and diff; or `bw hash <node>` for a node returned by `bw nodes bundle:<x>` | `bw items <node> <id>` (expected state) |
| `bundles/<x>/metadata.py` | `bw hash` (whole repo) and diff — reactors can ripple into other bundles' namespaces, so re-check every node carrying `<x>` (`bw nodes bundle:<x>`) | `bw metadata <node>`, `bw metadata <node> -k <key>` |
| `bundles/<x>/files/<file>` (template or static) | `bw hash <node>` for an affected node | `bw items <node> <path> --preview` (rendered content) |
| `groups/*.py` (or `groups.py`) | `bw hash <groupname>` (bare group name) | `bw nodes <node> -a groups`, `bw metadata <node>` |
| `libs/*.py` | `bw hash` (no target — all nodes; biggest blast radius) | `bw debug` to inspect helper outputs |
| `nodes/<x>.py` (or `nodes.py`) | `bw hash <node>` | `bw metadata <node>` |
| `hooks/*.py` | re-run the `bw` command whose lifecycle the hook hooks | — |
| Anything | `bw test` — cheapest repo-level sanity | — |

The canonical pre/post comparison is a hash diff:

```bash
bw hash > before.txt
# ... make the change ...
bw hash > after.txt
diff before.txt after.txt
```

If the diff is empty, the change had no effect on any node's resolved state. If the diff is non-empty, every changed line tells you which node was affected.

`bw hash -d` (`--dict`) drills down through three granularity levels:

- `bw hash -d` — per-node summary hash (one line per node).
- `bw hash -d <node>` — per-item hashes for that node (one line per item, e.g. `<hash>  file:/etc/hosts`).
- `bw hash -d <node> <item-id>` — per-attribute breakdown for that item (`content_hash`, `mode`, `owner`, `type`, …).

Use the deepest level that diffs to localize the change.
````

- [ ] **Step 2: Spot-check that the table renders (8 data rows)**

Run: `sed -n '/^| You changed/,/^The canonical/p' AGENTS.md | grep -cE '^\| '`
Expected: `10` (header + separator + 8 data rows)

- [ ] **Step 3: Commit**

```bash
git add AGENTS.md
git commit -m "AGENTS.md: add after-change runbook with selector usage"
```

---

## Task 6: Cheat-sheet — item dependency keywords

**Files:**
- Modify: `AGENTS.md` (replace placeholder under `## Cheat-sheet: item dependency keywords`)

Compact reference table for the 15 dep keywords from `BUILTIN_ITEM_ATTRIBUTES`, plus a 4-line code block illustrating the `triggers`/`triggered` pair, plus the footer link.

- [ ] **Step 1: Replace the placeholder with this exact content**

````markdown
The full set of item attributes that govern dependencies, ordering, and skipping. This is a quick-reference cheat-sheet, not a spec — for full semantics, see [`docs/content/repo/items.py.md`](docs/content/repo/items.py.md) or <https://docs.bundlewrap.org/repo/items.py>.

Many dependencies are **inferred automatically** by bundlewrap (a `file`'s owning user, a service's package, etc.). Use these keywords for dependencies bundlewrap can't infer — don't redeclare what is already implicit.

Verified against `BUILTIN_ITEM_ATTRIBUTES` in `bundlewrap/items/__init__.py`.

| Keyword | What it does |
|---|---|
| `needs` | Item depends on the listed items; if any dep is skipped or fails, this item is skipped (cascaded). Example: `'needs': ['pkg_apt:nginx']`. |
| `needed_by` | Reverse `needs` — declare from the dep's side. Use only when you cannot edit the depending item. |
| `before` | Order constraint without skip cascade. Item runs before the listed items, regardless of their success. |
| `after` | Reverse `before`. Item runs after the listed items, regardless of their success. |
| `triggers` | When **this item is fixed**, the listed items are run/checked. Targets must have `triggered: True`. |
| `triggered` | This item only runs when something else triggers it. Default: never runs on its own. |
| `triggered_by` | Reverse `triggers`. Declare from the triggered item's side. |
| `preceded_by` | Like `triggers`, but the triggered item runs **before** this one, only when this one would change. |
| `precedes` | Reverse `preceded_by`. |
| `tags` | Free-form labels. Other items can depend on a tag (e.g. `'needs': ['tag:foo']`). |
| `unless` | Shell command; if it returns 0, the item is skipped. Example: `'unless': 'test -x /opt/thing.bin'`. |
| `skip` | If `True`, item is always skipped. Useful for temporary disable. |
| `when_creating` | Dict of attribute overrides applied **only on first creation** of the item, then ignored. |
| `comment` | String shown in interactive mode (`bw apply -i`) before changing this item — for warning the human. |
| `cascade_skip` | Deprecated — use `before` / `after` instead. Was: control whether skipping this item also skips its dependents. |

The `triggers` / `triggered` pair only makes sense as a relationship between two items:

```python
files = {
    '/etc/daemon.conf': {
        'triggers': ['action:restart_daemon'],
    },
}
actions = {
    'restart_daemon': {
        'command': 'systemctl restart daemon',
        'triggered': True,
    },
}
```

`action:restart_daemon` only runs when `/etc/daemon.conf` is fixed (i.e. its content changed and bundlewrap rewrote it).

Full reference: [`docs/content/repo/items.py.md`](docs/content/repo/items.py.md).
````

- [ ] **Step 2: Verify the keyword count (15)**

Run:
```bash
grep -cE '^\| `(needs|needed_by|before|after|triggers|triggered|triggered_by|preceded_by|precedes|tags|unless|skip|when_creating|comment|cascade_skip)`' AGENTS.md
```
Expected: `15`

- [ ] **Step 3: Verify each keyword exists in `BUILTIN_ITEM_ATTRIBUTES`**

Run:
```bash
for kw in needs needed_by before after triggers triggered triggered_by preceded_by precedes tags unless skip when_creating comment cascade_skip; do
    grep -q "'$kw'" bundlewrap/items/__init__.py && echo "OK: $kw" || echo "MISSING: $kw"
done
```
Expected: all `OK:` — no `MISSING:`.

- [ ] **Step 4: Commit**

```bash
git add AGENTS.md
git commit -m "AGENTS.md: add dep-keywords cheat-sheet (15 attrs, verified vs source)"
```

---

## Task 7: Cheat-sheet — metadata.py pitfalls

**Files:**
- Modify: `AGENTS.md` (replace placeholder under `## Cheat-sheet: metadata.py pitfalls`)

Six pitfalls with one-paragraph rules. The first five are reactor-mechanism gotchas; the sixth is the deep-merge-with-collision-detection trap.

- [ ] **Step 1: Replace the placeholder with this exact content**

````markdown
The existing [`docs/content/repo/metadata.py.md`](docs/content/repo/metadata.py.md) covers the basics of `defaults`, reactors, and `@metadata_reactor.provides`. These are the gotchas it doesn't surface clearly.

1. **Reactors run to fixpoint.** Bundlewrap re-runs every reactor until none returns changed metadata. There is a hard cap (`MAX_METADATA_ITERATIONS` in `bundlewrap/metagen.py`); exceed it and `bw metadata` fails with "infinite loop between flip-flopping metadata reactors" and reports the top changers. Make sure your reactor's return is **stable** given the same input — no incrementing counters, no random values, no time-dependent computation.

2. **If you use `@metadata_reactor.provides(...)`, the declaration is a contract.** The bare `@metadata_reactor` decorator is always valid — every reactor runs on every metadata resolution by default. `.provides(...)` is a performance optimization: bundlewrap uses the declared paths (strings split on `/`, or tuples for keys that contain `/`) for lazy resolution, so `bw metadata <node> -k <key>` runs only the reactors that declare that key path. **If you opt into `.provides`, declare every top-level key path your reactor writes.** Declare too narrowly and lazy queries return stale data; declare too broadly and you lose the optimization. Mix-and-match (some reactors with `.provides`, some without) is fine in 5.0.3; the un-annotated ones simply always run.

3. **Reactors can write into ANY namespace.** A `nextcloud` reactor writing to `apt.packages` is normal and useful — it's how a bundle declares "to work, my node also needs these packages on it." Implication: changing one bundle's `metadata.py` can ripple into other bundles' inputs. This is why the [after-change runbook](#after-change-runbook) says to re-hash every node carrying `<x>` when `bundles/<x>/metadata.py` changes — not just nodes "in `<x>`'s namespace."

4. **The `metadata` parameter is opaque.** Use `metadata.get('a/b/c', default)`. Slashes split levels. For keys that actually contain a slash, pass a tuple: `metadata.get(('quz', 'literal/slash'), default)`. You cannot subscript or mutate the parameter; reading a missing key without a default raises `MetadataUnavailable`.

5. **Raise `DoNotRunAgain`** when your reactor's contribution is conditional and stable: "if this node has bundle X, set Y; otherwise contribute nothing." Bundlewrap then skips your reactor in subsequent iterations of the fixpoint loop, saving work. Available without import in `metadata.py`.

6. **Returns are deep-merged, not assigned.** Reactor returns and `defaults` dicts are merged into the layered metastack (`bundlewrap/utils/metastack.py`); sets and dicts merge recursively. You **cannot unset a key by returning `{}`** from a reactor — the empty dict simply contributes nothing to the merge. Conflicting atomic values from two reactors at the same path raise a collision error at `bw test -M` time (see `tests/integration/bw_test.py::test_reactor_metadata_collision_nested`). To remove or override existing data, structure the merge or override at the consumer (`items.py`, template), not at the reactor.

7. **Iterating `repo.nodes` in a reactor triggers metadata resolution for every other node.** Cross-node patterns like `for n in repo.nodes: n.metadata.get('foo')` are documented as a feature, but each `n.metadata.get(...)` recursively asks bundlewrap to generate metadata for `n` — including running its reactors. A single such reactor can dominate `bw hash` and `bw metadata` runtime in a large repo. Use sparingly; cache results when possible; consider whether the same data could live higher up (in group metadata or `defaults`) so it's read once instead of derived per-node.

Full reference: [`docs/content/repo/metadata.py.md`](docs/content/repo/metadata.py.md).
````

- [ ] **Step 2: Verify the pitfall count (7)**

Run: `sed -n '/^## Cheat-sheet: metadata.py pitfalls/,/^## Where to look/p' AGENTS.md | grep -cE '^[0-9]+\.'`
Expected: `7`

- [ ] **Step 3: Verify the source-citations exist**

Run:
```bash
grep -q 'MAX_METADATA_ITERATIONS' bundlewrap/metagen.py && echo "OK: MAX_METADATA_ITERATIONS"
grep -q 'class Metastack' bundlewrap/utils/metastack.py && echo "OK: Metastack"
grep -q 'test_reactor_metadata_collision_nested' tests/integration/bw_test.py && echo "OK: collision test"
```
Expected: three `OK:` lines.

- [ ] **Step 4: Commit**

```bash
git add AGENTS.md
git commit -m "AGENTS.md: add metadata.py pitfalls cheat-sheet (6 items)"
```

---

## Task 8: Where to look for depth section

**Files:**
- Modify: `AGENTS.md` (replace placeholder under `## Where to look for depth`)

Compact link list, one line per pointer.

- [ ] **Step 1: Replace the placeholder with this exact content**

```markdown
- [`docs/content/guide/quickstart.md`](docs/content/guide/quickstart.md) — first-time orientation.
- [`docs/content/repo/layout.md`](docs/content/repo/layout.md) — basic repo file layout.
- [`docs/content/repo/items.py.md`](docs/content/repo/items.py.md) — full item attribute reference.
- [`docs/content/repo/metadata.py.md`](docs/content/repo/metadata.py.md) — full metadata semantics.
- [`docs/content/guide/cli.md`](docs/content/guide/cli.md) — `bw` command reference.
- [`docs/content/guide/secrets.md`](docs/content/guide/secrets.md) — `repo.vault`, faults, secret handling.
- [`docs/content/guide/dev_item.md`](docs/content/guide/dev_item.md) — write a custom item type.
- [`docs/content/guide/api.md`](docs/content/guide/api.md) — Python API for advanced uses.
- [`docs/content/repo/libs.md`](docs/content/repo/libs.md) — `repo.libs` shared-helper convention.
- [`docs/content/repo/hooks.md`](docs/content/repo/hooks.md) — full hook event list and lifecycle.
- [`docs/content/items/`](docs/content/items/) — per-item-type details (`file`, `pkg_apt`, `svc_systemd`, ...).
- <https://docs.bundlewrap.org> — same content, hosted.
```

- [ ] **Step 2: Verify each linked path exists**

Run:
```bash
for p in docs/content/guide/quickstart.md docs/content/repo/layout.md docs/content/repo/items.py.md docs/content/repo/metadata.py.md docs/content/guide/cli.md docs/content/guide/secrets.md docs/content/guide/dev_item.md docs/content/guide/api.md docs/content/repo/libs.md docs/content/repo/hooks.md docs/content/items; do
    [ -e "$p" ] && echo "OK: $p" || echo "MISSING: $p"
done
```
Expected: all `OK:` lines.

- [ ] **Step 3: Commit**

```bash
git add AGENTS.md
git commit -m "AGENTS.md: add 'where to look for depth' link list"
```

---

## Task 9: Fill in the Table of Contents

**Files:**
- Modify: `AGENTS.md` (replace `<!-- TOC filled in Task 9 -->` under `## Contents`)

Now that all sections are written, generate the TOC with anchors. GitHub renders a heading like `## After-change runbook` as anchor `#after-change-runbook` (lowercased, spaces → hyphens, punctuation stripped).

- [ ] **Step 1: Replace the TOC placeholder with this exact content**

```markdown
1. [Mental model](#mental-model)
2. [Glossary](#glossary)
3. [Safety envelope: bw commands](#safety-envelope-bw-commands)
4. [After-change runbook](#after-change-runbook)
5. [Cheat-sheet: item dependency keywords](#cheat-sheet-item-dependency-keywords)
6. [Cheat-sheet: metadata.py pitfalls](#cheat-sheet-metadatapy-pitfalls)
7. [Where to look for depth](#where-to-look-for-depth)
```

(Note: GitHub strips the `.` from `metadata.py` when generating the anchor; the entry above accounts for that. If a different Markdown engine is in play, anchors may differ — for the in-tree root file, GitHub's rendering is the relevant target since this is what reviewers will see on GitHub.)

- [ ] **Step 2: Verify each anchor target exists in the file**

Run:
```bash
for a in "Mental model" "Glossary" "Safety envelope: bw commands" "After-change runbook" "Cheat-sheet: item dependency keywords" "Cheat-sheet: metadata.py pitfalls" "Where to look for depth"; do
    grep -q "^## $a\$" AGENTS.md && echo "OK: $a" || echo "MISSING: $a"
done
```
Expected: 7 `OK:` lines.

- [ ] **Step 3: Commit**

```bash
git add AGENTS.md
git commit -m "AGENTS.md: fill in table of contents"
```

---

## Task 10: Smoke-test cheat-sheet examples

This task verifies the metadata.py and item examples in the cheat-sheets actually work against bundlewrap 5.0.3, before the file ships. Catches drift cheaply.

**Tier-3 authorization for this task only.** The smoke-test uses `bw repo create`, which is a tier-3 (mutating) command per the safety envelope written into `AGENTS.md`. For this scratch-dir verification, **`bw repo create` against the temp directory is pre-authorized** as part of plan execution — the command runs only inside `$SCRATCH` (a `mktemp -d`), it does not touch this repository's working tree, and the entire scratch dir is removed at Step 6. Do not extend this authorization to any other tier-3 command in this task or elsewhere.

**Files:**
- (No file changes unless the smoke-test surfaces a problem.)

- [ ] **Step 1: Create a scratch repo in a temp dir**

```bash
SCRATCH=$(mktemp -d)
cd "$SCRATCH"
bw repo create
mkdir -p bundles/test
touch bundles/test/items.py
```

- [ ] **Step 2: Verify the `metadata.get('a/b/c', default)` shape works**

Write `bundles/test/metadata.py`:

```python
defaults = {
    'a': {'b': {'c': 'hello'}},
}

@metadata_reactor
def reads(metadata):
    return {'echo': metadata.get('a/b/c', 'default')}
```

Add a node:

```bash
cat > nodes.py <<'EOF'
nodes = {'n1': {'bundles': ['test']}}
EOF
```

Run: `bw metadata n1 -k echo`
Expected: prints `"hello"`.

- [ ] **Step 3: Verify `@metadata_reactor.provides('foo/bar')` is accepted and respected**

Append to `bundles/test/metadata.py`:

```python
@metadata_reactor.provides('foo/bar')
def declares(metadata):
    return {'foo': {'bar': 'declared'}}
```

Run: `bw metadata n1 -k foo/bar`
Expected: prints `"declared"`. No errors about undeclared paths.

- [ ] **Step 4: Verify `DoNotRunAgain` short-circuits the reactor**

Append:

```python
@metadata_reactor
def conditional(metadata):
    if not metadata.get('a/b/c', None):
        raise DoNotRunAgain
    return {'optional_key': True}
```

Run: `bw metadata n1 -k optional_key`
Expected: prints `true`. Verify with `bw debug -c "import bundlewrap; print('ok')"` that the runtime is responsive.

- [ ] **Step 5: Verify the triggers/triggered example shape**

Write `bundles/test/items.py`:

```python
files = {
    '/tmp/agents-md-smoketest.conf': {
        'content': 'hi',
        'triggers': ['action:noop_action'],
    },
}
actions = {
    'noop_action': {
        'command': 'true',
        'triggered': True,
    },
}
```

Run: `bw items n1`
Expected: lists `file:/tmp/agents-md-smoketest.conf` and `action:noop_action`. No bundle-load errors.

- [ ] **Step 6: Clean up the scratch repo**

```bash
cd /Users/mwiegand/Projekte/bundlewrap-fork
rm -rf "$SCRATCH"
```

- [ ] **Step 7: If any smoke-test failed, fix the cheat-sheet content and re-commit**

If a smoke-test surfaced an issue, edit `AGENTS.md` to correct the example, then:
```bash
git add AGENTS.md
git commit -m "AGENTS.md: correct cheat-sheet example for <thing>"
```

If all smoke-tests passed, this task produces no commit — proceed to Task 11.

---

## Task 11: Add CLAUDE.md symlink

**Files:**
- Create: `CLAUDE.md` (symlink → `AGENTS.md`)

- [ ] **Step 1: Create the symlink**

```bash
ln -s AGENTS.md CLAUDE.md
```

- [ ] **Step 2: Verify the symlink resolves**

Run: `readlink CLAUDE.md && head -1 CLAUDE.md`
Expected: prints `AGENTS.md` then the file's first line (`# AGENTS.md`).

- [ ] **Step 3: Commit**

```bash
git add CLAUDE.md
git commit -m "CLAUDE.md: symlink to AGENTS.md for Claude-Code-flavored tooling"
```

---

## Task 12: Final read-through and reference spot-check

**Files:**
- Modify: `AGENTS.md` only if read-through surfaces issues.

- [ ] **Step 1: Read the file top-to-bottom as if landing cold**

Run: `cat AGENTS.md | wc -l` to confirm length is roughly in budget (~185 lines, ±20).

Read the whole file. Ask: "If I were an agent landing in a different bundlewrap config repo, would this give me what I need to land work safely?" Look for:
- Internal contradictions (e.g. tier-1 list mentions a command that's also in tier 3).
- Dangling references ("see `docs/content/foo.md`" where the path doesn't exist).
- Cheat-sheet inaccuracies (e.g. a dep-keyword described differently from `docs/content/repo/items.py.md`).

- [ ] **Step 2: Spot-check every linked path**

Run:
```bash
grep -oE '`docs/content/[^`]+`' AGENTS.md | sed 's/`//g' | sort -u | while read p; do
    [ -e "$p" ] && echo "OK: $p" || echo "MISSING: $p"
done
```
Expected: all `OK:`.

- [ ] **Step 3: Spot-check that the dep-keywords table doesn't contradict `docs/content/repo/items.py.md`**

Read each row of the dep-keywords table and find the matching section in `docs/content/repo/items.py.md`. The cheat-sheet's one-liner must be consistent with the upstream doc — tighter wording is fine; contradiction is not.

For any inconsistency, prefer the upstream doc's wording (since it's the canonical reference) — update the cheat-sheet.

- [ ] **Step 4: Commit any fix-ups**

If Step 1, 2, or 3 surfaced fixes:

```bash
git add AGENTS.md
git commit -m "AGENTS.md: address review fix-ups"
```

If nothing changed, no commit — the implementation is done.

---

## Final verification

After all tasks: `git log --oneline -15` should show roughly 11–13 commits with `AGENTS.md:` and `CLAUDE.md:` prefixes (one each for Tasks 1–9 and Task 11; conditional commits for Tasks 10 and 12 if those steps surfaced fixes), ending with the latest. `git diff master..HEAD --stat` should show two changed files: `AGENTS.md` (created) and `CLAUDE.md` (created as symlink).

## Squash before push (rollout shape)

The spec calls for **a single commit** at rollout (§6: "Single commit. Two files added: `AGENTS.md`, `CLAUDE.md`-as-symlink. Self-contained, easy to revert, PR-able as one unit"). The per-task commits in this plan exist for clean local bisect during execution; before pushing for review or upstream PR, squash them into one.

If your local branch holds only these implementation commits (i.e. no other unrelated work on the branch), the simplest squash is an interactive rebase against the brainstorming commit:

```bash
# Find the pre-implementation HEAD (the spec commit, 0e8e8d85, or master if you branched from there)
git log --oneline | head -20
# Squash everything since that point into one commit
git rebase -i <pre-implementation-sha>
# In the editor, change all but the first 'pick' to 'squash' (or 'fixup'); save.
# Then write a single commit message like:
#   AGENTS.md: add agent-oriented orientation layer
#
#   Adds AGENTS.md (and a CLAUDE.md symlink) at the repo root with a
#   safety envelope for `bw` commands, an after-change runbook,
#   cheat-sheets for dep keywords and metadata.py pitfalls, and links
#   into the existing MkDocs site for depth. Pure addition; no edits to
#   existing docs or code.
```

Do **not** force-push to `master` or any shared branch as part of this — the squash should happen on a feature branch dedicated to this work, before the first push.

The file is ready for review. The user (mwiegand) can now decide whether to push the branch, open a PR upstream, or fold further fork-specific content (e.g. the WIP-branch index — out-of-scope per the spec) into a follow-up.
