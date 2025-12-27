#!/usr/bin/env python3
"""run_stageB.py — Stage B runner.

Generates *_autogen.* files from Stage A contracts and runs B-Gate tests.

Usage:
    python run_stageB.py           # generate + test
    python run_stageB.py -v        # verbose
    python run_stageB.py --gen     # generate only (skip tests)
    python run_stageB.py --test    # run tests only (skip generation)
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path
from typing import List, Optional

REPO_ROOT = Path(__file__).resolve().parent


def run_command(cmd: List[str], description: str, verbose: bool = False) -> bool:
    """Run a command and return success status."""
    print(f"\n{'=' * 72}")
    print(f"▶ {description}")
    print("=" * 72)

    if verbose:
        print(f"Command: {' '.join(cmd)}")

    result = subprocess.run(
        cmd,
        cwd=str(REPO_ROOT),
        text=True,
        capture_output=not verbose,
    )

    if result.returncode == 0:
        if verbose and result.stdout:
            print(result.stdout)
        print(f"✅ {description} — PASSED")
        return True

    # Show output on failure
    if not verbose:
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(result.stderr, file=sys.stderr)
    print(f"❌ {description} — FAILED")
    return False


def main(argv: Optional[List[str]] = None) -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Stage B: generate skeletons + run B-Gate tests"
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Verbose output"
    )
    parser.add_argument(
        "--gen", "--generate",
        action="store_true",
        dest="generate_only",
        help="Generate only (skip tests)"
    )
    parser.add_argument(
        "--test",
        action="store_true",
        dest="test_only",
        help="Run tests only (skip generation)"
    )
    args = parser.parse_args(argv)

    results: List[bool] = []

    # Generate skeletons
    if not args.test_only:
        results.append(
            run_command(
                [sys.executable, "-m", "stageB.generator.generate_module", "--all"],
                "Generating *_autogen.* from contracts",
                verbose=args.verbose,
            )
        )

    # Run tests
    if not args.generate_only:
        verbosity = "-v" if args.verbose else "-q"
        results.append(
            run_command(
                [
                    sys.executable,
                    "-m", "unittest",
                    "discover",
                    "-s", "stageB/tests",
                    "-p", "test_*.py",
                    verbosity,
                ],
                "Running B-Gate tests",
                verbose=args.verbose,
            )
        )

    print()
    if all(results):
        print("✅ STAGE B COMPLETE")
        return 0

    print("❌ STAGE B FAILED")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
