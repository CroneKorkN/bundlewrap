# AGENTS.md

This file orients agents working with this BundleWrap repository. It is a safety envelope, an after-change runbook, and a small set of cheat-sheets for the parts of bundlewrap-the-language that bite agents. It is not a tutorial — for that, start with [`docs/content/guide/quickstart.md`](docs/content/guide/quickstart.md) or the hosted docs at <https://docs.bundlewrap.org>. If you are working on bundlewrap itself rather than using it, see `CONTRIBUTING.md`.

## Contents

1. [Mental model](#mental-model)
2. [Glossary](#glossary)
3. [Safety envelope: bw commands](#safety-envelope-bw-commands)
4. [After-change runbook](#after-change-runbook)
5. [Cheat-sheet: item dependency keywords](#cheat-sheet-item-dependency-keywords)
6. [Cheat-sheet: metadata.py pitfalls](#cheat-sheet-metadatapy-pitfalls)
7. [Where to look for depth](#where-to-look-for-depth)

## Mental model

```
nodes ←─── groups ───→ bundles ───→ items
```

A **node** is a machine bundlewrap manages. A **group** is a set of nodes (or nested groups) that share configuration. A **bundle** is a named set of items; a node gets a bundle by being in a group that includes it, or by listing it directly. An **item** is one managed resource — a file, a package, a service, a user.

Metadata flows from many places into a single resolved view per node. Each node's resolved metadata is the merge of its own static metadata, its groups' static metadata, each loaded bundle's `metadata.py` defaults, and each loaded bundle's `metadata.py` reactors run to a fixpoint. Resolved metadata is then available to each bundle's `items.py` to compute item attributes.

## Glossary

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

## Safety envelope: bw commands

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
- `bw pw` — derive/encrypt/decrypt secrets to **stdout**. Tier 1 only when `--file`/`-f` is not used; with `-f` it writes to `data/` and is tier 3 (see below).

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

## After-change runbook

After making any change to a bundlewrap config repo, run the first check from the row that matches what you edited. If the first check shows a diff or change, drill in with the second column. **`bw hash` accepts only literal node or group names** — selectors like `bundle:<x>` and `group:<name>` work for `bw apply`, `bw run`, `bw nodes`, etc., but NOT for `bw hash`. To scope to a bundle, enumerate nodes first (`bw nodes bundle:<x>`) and hash each.

| You changed | First check | Drill-in |
| --- | --- | --- |
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

## Cheat-sheet: item dependency keywords

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

## Cheat-sheet: metadata.py pitfalls

The existing [`docs/content/repo/metadata.py.md`](docs/content/repo/metadata.py.md) covers the basics of `defaults`, reactors, and `@metadata_reactor.provides`. These are the gotchas it doesn't surface clearly.

1. **Reactors run to fixpoint.** Bundlewrap re-runs every reactor until none returns changed metadata. There is a hard cap (`MAX_METADATA_ITERATIONS` in `bundlewrap/metagen.py`); exceed it and `bw metadata` fails with "infinite loop between flip-flopping metadata reactors" and reports the top changers. Make sure your reactor's return is **stable** given the same input — no incrementing counters, no random values, no time-dependent computation.

2. **If you use `@metadata_reactor.provides(...)`, the declaration is a contract.** The bare `@metadata_reactor` decorator is always valid — every reactor runs on every metadata resolution by default. `.provides(...)` is a performance optimization: bundlewrap uses the declared paths (strings split on `/`, or tuples for keys that contain `/`) for lazy resolution, so `bw metadata <node> -k <key>` runs only the reactors that declare that key path. **If you opt into `.provides`, declare every top-level key path your reactor writes.** Declare too narrowly and lazy queries return stale data; declare too broadly and you lose the optimization. Mix-and-match (some reactors with `.provides`, some without) is fine in 5.0.3; the un-annotated ones simply always run. **Every reactor — bare `@metadata_reactor` or `.provides`-decorated — must read at least one metadata key** (it's not a `.provides` thing; the check at `bundlewrap/metagen.py:426` is unconditional). If you're providing a value with no input, use `defaults` instead. Example:
```python
@metadata_reactor.provides('foo/bar')
def computes_derived_value(metadata):
    # Read at least one key (required for reactors)
    version = metadata.get('app/version', '1.0')
    return {'foo': {'bar': f'version-{version}'}}
```

3. **Reactors can write into ANY namespace.** A `nextcloud` reactor writing to `apt.packages` is normal and useful — it's how a bundle declares "to work, my node also needs these packages on it." Implication: changing one bundle's `metadata.py` can ripple into other bundles' inputs. This is why the [after-change runbook](#after-change-runbook) says to re-hash every node carrying `<x>` when `bundles/<x>/metadata.py` changes — not just nodes "in `<x>`'s namespace."

4. **The `metadata` parameter is opaque.** Use `metadata.get('a/b/c', default)`. Slashes split levels. For keys that actually contain a slash, pass a tuple: `metadata.get(('quz', 'literal/slash'), default)`. You cannot subscript or mutate the parameter; reading a missing key without a default raises `MetadataUnavailable`.

5. **Raise `DoNotRunAgain`** when your reactor's contribution is conditional and stable (e.g. "if this node has bundle X, set Y; else contribute nothing"). Bundlewrap then skips the reactor in subsequent iterations of the fixpoint loop, saving work. Available without import in `metadata.py`.

6. **Returns are deep-merged, not assigned.** Reactor returns and `defaults` dicts are merged into the layered metastack (`bundlewrap/utils/metastack.py`); sets and dicts merge recursively. You **cannot unset a key by returning `{}`** from a reactor — the empty dict simply contributes nothing to the merge. Conflicting atomic values from two reactors at the same path raise a collision error at `bw test -M` time (`-M` = metadata-collision check; see `tests/integration/bw_test.py::test_reactor_metadata_collision_nested`). To remove or override existing data, structure the merge or override at the consumer (`items.py`, template), not at the reactor.

7. **Iterating `repo.nodes` in a reactor triggers metadata resolution for every other node.** Cross-node patterns like `for n in repo.nodes: n.metadata.get('foo')` are documented as a feature, but each `n.metadata.get(...)` recursively asks bundlewrap to generate metadata for `n` — including running its reactors. A single such reactor can dominate `bw hash` and `bw metadata` runtime in a large repo. Use sparingly; cache results when possible; consider whether the same data could live higher up (in group metadata or `defaults`) so it's read once instead of derived per-node.

Full reference: [`docs/content/repo/metadata.py.md`](docs/content/repo/metadata.py.md).

## Where to look for depth

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
