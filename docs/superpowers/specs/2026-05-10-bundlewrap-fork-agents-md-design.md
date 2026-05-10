# Bundlewrap fork — agent-friendly AGENTS.md — design

Date: 2026-05-10

## 1. Goals & non-goals

**Goal.** Add a non-intrusive agent-orientation layer to the bundlewrap fork
so an agent landing cold can use bundlewrap in a config repo (their own, not
this one) safely and without spelunking. The MkDocs site already covers
bundlewrap-the-language well; the gap is a concise, agent-oriented entry
point that surfaces the safety envelope, the after-change runbook, and
cheat-sheets for the parts MkDocs doesn't cover well (dep-keywords TLDR
table, metadata.py pitfalls).

**Audience.** Agents using bundlewrap in a config repo (primary). Agents
working on bundlewrap itself are out of scope here — this file may
incidentally help them, but content is not tailored to that.

**In scope.**

- Add `AGENTS.md` at repo root (~185 lines, including a TOC).
- Add `CLAUDE.md` at repo root as a symlink → `AGENTS.md`.

**Out of scope (explicitly).**

- No edits to existing files. Nothing under `docs/content/`, nothing under
  `bundlewrap/`, nothing under `tests/`. No edits to `README.md`,
  `CONTRIBUTING.md`, `mkdocs.yml`. Pure addition.
- No fork-specific framing in the doc (no mention of WIP branches, no "this
  is a fork" wording). Reads as if it could land at upstream
  `bundlewrap/bundlewrap`. Future PR-to-upstream is a downstream option,
  not a goal of this spec.
- No subfolder `AGENTS.md` files (e.g. `bundlewrap/AGENTS.md`,
  `tests/AGENTS.md`). Splitting can happen later if any one section bloats;
  current content estimate fits comfortably in a single file.
- No "working on bundlewrap itself" section. Contributors land via
  `CONTRIBUTING.md` and existing docs.
- No MkDocs nav changes. The new file lives at repo root, outside the
  MkDocs site.
- No automated docs tests / lint.

## 2. File layout

```
bundlewrap-fork/
├── AGENTS.md              ← new, ~155 lines
└── CLAUDE.md              ← new, symlink → AGENTS.md
```

Two files. No other changes.

## 3. AGENTS.md content — section-by-section

Section numbering below matches the order of sections in the file.

### 3.1 Table of contents (~10 lines)

A simple anchor list at the top of the file linking to §§3.2–3.9 (the
content sections below). Reason: a 165-line file in a single Markdown
view is hard to scan — a TOC makes it agent-friendly for jump-to-section
access. (MkDocs would auto-generate this; the standalone root file
doesn't get that for free.)

### 3.2 What this is (~10 lines)

One sentence on bundlewrap (decentralized configuration management;
nodes/groups/bundles/items model). One sentence on this file's purpose
("orient + safety envelope; deep docs are at `docs/content/` and
<https://docs.bundlewrap.org>"). One-line scope note: this file is for
agents *using* bundlewrap; for working on bundlewrap itself see
`CONTRIBUTING.md` and the upstream docs.

### 3.3 Mental model (~10 lines)

Nodes ← groups → bundles → items. One paragraph + a tiny ASCII sketch.
Metadata flow paragraph: each node's resolved metadata = node static
metadata + group static metadata + each bundle's `metadata.py` defaults +
each bundle's reactors run to fixpoint. Resolved metadata is then
available to that bundle's `items.py`.

### 3.4 Glossary (~25 lines)

One paragraph (≤2 lines) per term, in this order: node, group, bundle,
`items.py`, `metadata.py`, item, item type, metadata reactor,
`@metadata_reactor.provides`, hook, lib (`repo.libs`), `repo`. Definitions
should be precise enough that an agent doesn't have to chase MkDocs for
the basics; for depth, the doc relies on §3.8 links.

### 3.5 Safety envelope: bw commands (~32 lines)

Three tiers. Rule for agents: default to tier 1; never invoke tier 2 or
tier 3 without explicit user request.

- **Tier 1 — read-only, local.** No side effects on the working tree, no
  network. `bw hash`, `bw metadata`, `bw items`, `bw nodes`, `bw groups`,
  `bw debug`, `bw test`, `bw plot`, `bw pw` (without `-f`; encrypt/decrypt
  to stdout is local-read-only, but `-f` writes a file under `data/`).
- **Tier 2 — read-only, networked.** No mutation, but SSH/network calls.
  `bw verify` (SSHes into nodes; reads state but does not change it).
- **Tier 3 — mutating, requires explicit user request.** `bw apply`,
  `bw run`, `bw lock add`, `bw lock remove`, `bw ipmi`, `bw pw -f`
  (writes the result of encrypt/decrypt into `data/`),
  `bw repo bundle create`, `bw repo create` (writes new files into the
  working tree).

Each command gets a one-line description. Source for the split: verified
against `bundlewrap/cmdline/parser.py` and `bundlewrap/cmdline/verify.py`
in the 5.0.3 source.

Explicit one-line note immediately after the tier-3 list: **"Interactive
mode (`bw apply -i`) is still tier 3."** The `-i` flag prompts a human
before each item, but the prompt is for the human, not a safety belt for
agents. An agent must not invoke `bw apply -i` autonomously any more than
plain `bw apply`.

### 3.6 After-change runbook (~25 lines)

Table keyed by what the agent edited. First check is the cheapest signal;
drill-in is the next step if the first check shows a difference.

| Changed | First check | Drill-in |
|---|---|---|
| `bundles/<x>/items.py` | `bw hash <node-with-bundle-x>` | `bw items <node> <id> -p` |
| `bundles/<x>/metadata.py` | `bw hash bundle:<x>` (hashes every node with bundle `<x>`; reactors can ripple into other bundles' namespaces) | `bw metadata <node>`, `bw metadata <node> -k <key>` |
| `bundles/<x>/files/<template>` | `bw hash <node>` | `bw items <node> <path> -p` |
| `groups/*.py` | `bw hash` every affected node (use `group:<name>` selector to scope) | `bw groups -n <node>` |
| `libs/*.py` | `bw hash` all nodes — biggest blast radius | `bw debug` |
| `nodes/<x>.py` | `bw hash <node>` | `bw metadata <node>` |
| `hooks/*.py` | re-run the bw command whose lifecycle the hook hooks | — |
| Anything | `bw test` — cheapest repo-level sanity | — |

After the table: a hash diff workflow snippet — `bw hash > before.txt`,
make the change, `bw hash > after.txt`, `diff before.txt after.txt`. This
is the canonical "did my change have the effect I expected, and only
that effect" check.

### 3.7 Cheat: dep keywords (~30 lines)

Compact reference table. One row per keyword: name, one-sentence
semantic, tiny inline example. Keywords (verified against
`BUILTIN_ITEM_ATTRIBUTES` in `bundlewrap/items/__init__.py`):

`needs`, `needed_by`, `before`, `after`, `triggers`, `triggered`,
`triggered_by`, `preceded_by`, `precedes`, `tags`, `unless`, `skip`,
`when_creating`, `comment`, `cascade_skip` (marked deprecated).

After the table, allow one 3–5-line fenced code block illustrating the
`triggers`/`triggered` pair, since that keyword pair only makes sense
as a relationship between two items and a one-line example can't
capture it. Other keywords stay as inline examples.

Footer one-liner: "Full reference: `docs/content/repo/items.py.md` or
<https://docs.bundlewrap.org/repo/items.py>."

This is a cheat-sheet, not a spec; it's marked as such inline.

### 3.8 Cheat: metadata.py pitfalls (~35 lines)

Five items the existing `docs/content/repo/metadata.py.md` doesn't
surface clearly. Each: one-paragraph rule + one-line "why it bites you".

1. **Reactors run to fixpoint.** Bundlewrap re-runs reactors until none
   return changed metadata. There's a hard cap
   (`MAX_METADATA_ITERATIONS` in `bundlewrap/metagen.py`); exceed it and
   `bw metadata` fails with "infinite loop between flip-flopping
   metadata reactors" and reports the top changers. Make returns stable.

2. **`@metadata_reactor.provides(...)` is a contract.** Every top-level
   key path your reactor writes must be declared. The decorator stores
   the provided paths (strings split on `/`, or tuples for keys that
   contain `/`) and bundlewrap uses them for lazy resolution: if you
   request `bw metadata <node> -k <key>`, only the reactors that declare
   that key path run. Declare too narrowly and lazy queries return
   stale data; declare too broadly and you lose the optimization.

3. **Reactors can write into ANY namespace.** A `nextcloud` reactor
   writing to `apt.packages` is normal and useful — it's how a bundle
   declares "to work, my node also needs these packages." Implication:
   changing one bundle's `metadata.py` can ripple into other bundles'
   inputs. This is why the runbook (§3.5) says "every node with bundle
   `<x>`" — the change can affect any node that loaded the bundle, not
   just the namespace the reactor "belongs to."

4. **The `metadata` parameter is opaque.** Use
   `metadata.get('a/b/c', default)`. Slashes split levels. For keys that
   actually contain a slash, pass a tuple. You cannot subscript or
   mutate the parameter; reading missing keys without a default raises
   `MetadataUnavailable`.

5. **Raise `DoNotRunAgain`** when your reactor's contribution is
   conditional and stable (e.g. "if this node has bundle X, set Y; else
   contribute nothing"). Bundlewrap then skips the reactor in subsequent
   iterations of the fixpoint loop.

6. **Returns are deep-merged, not assigned.** Reactor returns and
   `defaults` dicts are merged into the layered metastack
   (`bundlewrap/utils/metastack.py`); sets and dicts merge recursively.
   You cannot unset a key by returning `{}` from a reactor — the empty
   dict simply contributes nothing to the merge. Conflicting atomic
   values from two reactors at the same path raise a collision error
   at `bw test -M` time (see
   `tests/integration/bw_test.py::test_reactor_metadata_collision_nested`).
   To remove or override existing data, structure the merge or override
   at the consumer (`items.py`, template), not at the reactor.

Footer one-liner: "Full reference: `docs/content/repo/metadata.py.md`."

### 3.9 Where to look for depth (~10 lines)

Compact link list. One line per pointer:

- `docs/content/guide/quickstart.md` — first-time orientation
- `docs/content/repo/items.py.md` — full item attribute reference
- `docs/content/repo/metadata.py.md` — metadata semantics
- `docs/content/guide/cli.md` — bw command reference
- `docs/content/guide/secrets.md` — `repo.vault`, faults
- `docs/content/guide/dev_item.md` — write a custom item type
- `docs/content/guide/api.md` — Python API for advanced uses
- `docs/content/items/<type>.md` — per-item-type details
- <https://docs.bundlewrap.org> — same content, hosted

## 4. Authoring rules

- **Style.** Opinionated about safety, factually neutral about the
  codebase. Reads as if it could land at upstream `bundlewrap/bundlewrap`.
- **No fork-specific content.** No mention of WIP branches, of mwiegand,
  or of "this is a fork." Future PR-to-upstream stays an option.
- **Cheat-sheets are clearly marked as cheat-sheets,** with the canonical
  doc linked at the end of each section ("Full reference: `<path>`").
- **Don't redocument what exists.** Where MkDocs covers a topic well,
  link, don't duplicate. Cheat-sheets only fill gaps.
- **Path conventions.** Refer to existing docs as `docs/content/<...>`
  (the actual file structure), not `docs/<...>`. The site's URL paths
  on docs.bundlewrap.org drop the `content/` prefix; both forms are
  given where it helps an agent navigate either source.
- **No code blocks beyond inline tiny examples.** AGENTS.md is reference,
  not tutorial.
- **Source material reuse.** Sections 4 and 6 of
  `/Users/mwiegand/Projekte/ckn-bw/docs/superpowers/specs/2026-05-10-agent-friendliness-design.md`
  are reusable as starting drafts; strip ckn-bw-specifics (demagify,
  vault magic strings, `repo.libs.hashable`, eval()-loaded `nodes.py`)
  since those are config-repo idioms, not bundlewrap-the-language idioms.

## 5. Verification

Before committing:

- Read top-to-bottom. The doc lives or dies by usefulness; review it
  the way an agent landing cold would read it.
- Spot-check every referenced path exists
  (`docs/content/repo/items.py.md`, etc.).
- Re-confirm the read-only / mutating split against
  `bundlewrap/cmdline/parser.py` and `bundlewrap/cmdline/verify.py` in
  the 5.0.3 source. (Initial split already validated via
  `ccc search` during design.)
- Re-confirm the dep-keyword list against `BUILTIN_ITEM_ATTRIBUTES` in
  `bundlewrap/items/__init__.py` — must match exactly (excluding the
  niche `error_on_missing_fault` and `canned_actions_inherit_tags`,
  which are not dep-keywords proper).
- Re-read the dep-keywords cheat-table against
  `docs/content/repo/items.py.md` to ensure no contradictions in
  semantics or examples.
- **Smoke-test the cheat-sheet examples against a real bundlewrap
  5.0.3 install.** Use a minimal scratch repo (`bw repo create` in a
  tmp dir) and `bw debug -c '<expression>'` to evaluate each example
  in `metadata.py` shape: `metadata.get('a/b/c', default)`,
  `@metadata_reactor.provides('foo/bar')`, `DoNotRunAgain`, the
  `triggers`/`triggered` pair. Goal: catch drift between cheat-sheet
  and reality before the file ships, cheaply.

No automated tests for the doc itself. No MkDocs nav change, so no nav
check needed.

## 6. Rollout

Single commit. Two files added: `AGENTS.md`, `CLAUDE.md`-as-symlink.
Self-contained, easy to revert, PR-able as one unit.

## 7. Out-of-scope follow-ups (not this spec)

Tracked here so they don't get lost; explicitly not part of this work.

- WIP-branch index in AGENTS.md (the fork has 19 active WIP branches:
  canned_stop, docker, metadata_class, metaproc_flowcontrol,
  mocked_passwords_with_requested_length, new_zfs, print_bundle_name,
  show_errors, …). Adds fork-specific framing; defer until needed.
- Switching the `ckn-bw` venv to an editable install of this fork.
- Returning to the `ckn-bw` brainstorm (root AGENTS.md, per-area
  AGENTS.md, conventions.md, commands.md, per-bundle docs) with
  reduced scope, now that bundlewrap-the-language docs live here.
- Targeted MkDocs improvements (top-of-`items.py.md` cheat table,
  metadata.py pitfalls section, `cli.md` read-only/mutating annotation,
  `nodes.py.md`/`groups.py.md` `eval()`-pitfall callout). Out of scope
  per user direction: do not change existing docs.
- A PR to upstream `bundlewrap/bundlewrap` adding this `AGENTS.md`.

## 8. Risks

- **Drift.** As bundlewrap evolves, AGENTS.md lags. Mitigation: cheat-
  sheets are short and link to canonical references; the safety envelope
  and after-change runbook change rarely.
- **Cheat-sheet duplication of MkDocs.** Acknowledged. Mitigation:
  cheat-sheets are explicitly marked, kept short, and end with a link to
  the canonical doc. The dep-keywords table is the most exposed; if
  upstream's `items.py.md` ever grows a TLDR table, this one can shrink
  to a pointer.
- **`bw pw -f` ambiguity.** `bw pw` is a single subcommand whose
  side-effect depends on flags. The safety table classifies forms
  without `-f` as tier 1 and forms with `-f` as tier 3 (the `-f` flag
  causes encrypt/decrypt output to be written to `data/`). If agents
  misread, they could write a secret to `data/`. Mitigation: call out
  the flag distinction explicitly in the tier-1 entry.
