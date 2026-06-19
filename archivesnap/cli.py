"""Command-line interface for archivesnap."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import __version__
from .differ import diff_snapshots
from .fetcher import FileFetcher, LiveFetcher
from .normalize import html_to_text
from .store import SnapshotStore
from .watcher import load_config, run_watch


def _capture(url: str, *, store_dir: str, live: bool,
             from_file: str | None) -> int:
    store = SnapshotStore(store_dir)
    if live:
        raw = LiveFetcher().fetch(url)
    elif from_file:
        raw = FileFetcher(from_file).fetch(url)
    else:
        print("error: provide --from-file PATH or use --live", file=sys.stderr)
        return 2
    text = html_to_text(raw)
    snap = store.save(url, text, meta={"live": live, "source": from_file or "live"})
    print(f"snapshot saved: {url}")
    print(f"  timestamp: {snap.timestamp}")
    print(f"  hash:      {snap.content_hash}")
    print(f"  lines:     {len(text.splitlines())}")
    print(f"  store:     {Path(store_dir).resolve()}")
    return 0


def _diff(url: str, *, store_dir: str, threshold: float) -> int:
    store = SnapshotStore(store_dir)
    latest = store.latest(url)
    prev = store.previous(url)
    if latest is None:
        print(f"error: no snapshots for {url}", file=sys.stderr)
        return 2
    if prev is None:
        print(f"only one snapshot for {url}; nothing to diff against")
        return 0
    result = diff_snapshots(prev, latest, threshold=threshold)
    print(f"diff: {url}")
    print(f"  {prev.timestamp}  ->  {latest.timestamp}")
    print(f"  {result.summary()}")
    if result.unified:
        print("---")
        print(result.unified)
    return 0


def _list(url: str, *, store_dir: str) -> int:
    store = SnapshotStore(store_dir)
    snaps = store.list(url)
    if not snaps:
        print(f"no snapshots for {url}")
        return 0
    print(f"{len(snaps)} snapshot(s) for {url}:")
    for i, s in enumerate(snaps):
        print(f"  [{i}] {s.timestamp}  {s.content_hash[:12]}  "
              f"{len(s.text.splitlines())} lines")
    return 0


def _watch(config_path: str, *, once: bool, live: bool,
           fail_on_change: bool) -> int:
    if not once:
        print("error: only --once mode is supported", file=sys.stderr)
        return 2
    config = load_config(config_path)
    base_dir = Path(config_path).resolve().parent
    fetcher = LiveFetcher() if live else None
    result = run_watch(config, base_dir=base_dir, fetcher=fetcher)

    for r in result.results:
        if r.status == "new":
            print(f"[new]       {r.url}  (baseline captured)")
        elif r.status == "unchanged":
            print(f"[unchanged] {r.url}")
        else:
            tag = "CHANGED*" if r.significant else "changed "
            print(f"[{tag}] {r.url}  {r.diff.summary()}")

    sig = result.changed_pages
    print(f"\n{len(sig)} significant change(s) of {len(result.results)} page(s).")
    if fail_on_change and result.any_significant:
        return 1
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="archivesnap",
        description="Web-page snapshot and change monitor (defensive use).",
    )
    parser.add_argument("--version", action="version",
                        version=f"archivesnap {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    p_snap = sub.add_parser("snapshot", help="capture and store a snapshot")
    p_snap.add_argument("url")
    p_snap.add_argument("--store", default="snapshots", help="store directory")
    p_snap.add_argument("--live", action="store_true",
                        help="fetch over the network via urllib")
    p_snap.add_argument("--from-file", help="read page content from a local file")

    p_diff = sub.add_parser("diff", help="diff latest vs previous snapshot")
    p_diff.add_argument("url")
    p_diff.add_argument("--store", default="snapshots", help="store directory")
    p_diff.add_argument("--threshold", type=float, default=0.05,
                        help="significance threshold (change ratio, 0..1)")

    p_list = sub.add_parser("list", help="list snapshots for a url")
    p_list.add_argument("url")
    p_list.add_argument("--store", default="snapshots", help="store directory")

    p_watch = sub.add_parser("watch", help="check a list of pages from a config")
    p_watch.add_argument("config")
    p_watch.add_argument("--once", action="store_true",
                         help="run a single pass (required)")
    p_watch.add_argument("--live", action="store_true",
                         help="fetch over the network via urllib")
    p_watch.add_argument("--fail-on-change", action="store_true",
                         help="exit 1 if any page changed significantly")

    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "snapshot":
        return _capture(args.url, store_dir=args.store, live=args.live,
                        from_file=args.from_file)
    if args.command == "diff":
        return _diff(args.url, store_dir=args.store, threshold=args.threshold)
    if args.command == "list":
        return _list(args.url, store_dir=args.store)
    if args.command == "watch":
        return _watch(args.config, once=args.once, live=args.live,
                      fail_on_change=args.fail_on_change)
    return 2  # pragma: no cover


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
