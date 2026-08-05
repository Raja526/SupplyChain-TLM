"""Command-line interface for the human-review queue."""

from __future__ import annotations

import argparse
import json

from .extraction import PlainTextProvider
from .review import ReviewQueue
from .text_extract import extract_fields


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Manage uncertain supply-chain document reviews")
    parser.add_argument("--queue", default="review/review.jsonl")
    parser.add_argument("--json", action="store_true", dest="as_json", help="emit machine-readable JSON")
    subparsers = parser.add_subparsers(dest="command", required=True)

    enqueue = subparsers.add_parser("enqueue")
    enqueue.add_argument("path")
    resolve = subparsers.add_parser("resolve")
    resolve.add_argument("item_id")
    resolve.add_argument("reviewer")
    resolve.add_argument("decision")
    subparsers.add_parser("list")

    args = parser.parse_args(argv)
    queue = ReviewQueue(args.queue)
    if args.command == "enqueue":
        text = PlainTextProvider().extract(args.path).text
        item = queue.enqueue_extraction(args.path, extract_fields(text))
        if item is None:
            if args.as_json:
                print(json.dumps({"status": "no_review_needed"}, sort_keys=True))
                return 0
            print("no review needed")
            return 0
        if args.as_json:
            print(json.dumps({"status": "queued", "item": item.__dict__}, sort_keys=True))
            return 0
        print(f"queued: {item.item_id} reason={item.reason}")
        return 0
    if args.command == "list":
        if args.as_json:
            print(json.dumps({"items": [item.__dict__ for item in queue.open_items()]}, sort_keys=True))
            return 0
        for item in queue.open_items():
            print(f"{item.item_id} source={item.source} reason={item.reason}")
        return 0
    item = queue.resolve(args.item_id, args.reviewer, args.decision)
    if args.as_json:
        print(json.dumps({"status": "resolved", "item": item.__dict__}, sort_keys=True))
        return 0
    print(f"resolved: {item.item_id} reviewer={item.reviewer} decision={item.decision}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
