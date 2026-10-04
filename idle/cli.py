"""命令行入口：跑挂机踢出样例。"""

import argparse

from .core import IdleGuard


def build_parser():
    parser = argparse.ArgumentParser(prog="anti-idle-kick", description="挂机踢出判定")
    parser.add_argument("--sample", default="whitelist", help="whitelist / exact / grace / scan")
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    if args.sample == "whitelist":
        guard = IdleGuard(1000, 500)
        guard.allow("p")
        guard.touch("e1", "p", 0)
        print("result=%s" % guard.check("p", 5000))
    elif args.sample == "exact":
        guard = IdleGuard(1000, 500)
        guard.touch("e1", "p", 0)
        print("result=%s" % guard.check("p", 1000))
    elif args.sample == "grace":
        guard = IdleGuard(1000, 500)
        guard.touch("e1", "p", 0)
        print("result=%s" % guard.check("p", 1500))
    elif args.sample == "scan":
        guard = IdleGuard(1000, 500)
        for index in range(3000):
            guard.touch("e-%d" % index, "p-%d" % index, 0)
        for _ in range(3000):
            guard.check("p-0", 0)
        print("scanned=%d" % guard.scanned_count())
    else:
        raise SystemExit("需要 --sample whitelist|exact|grace|scan")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
