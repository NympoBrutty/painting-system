"""Stage B — Skeleton Code Generation Package (A-PRACTICAL)

Subpackages:
    - stageB.generator: contract → *_autogen.* generation
    - stageB.modules: generated skeletons + manual pipeline entry points
    - stageB.tests: B-Gate tests

Generator principle:
    - Writes ONLY *_autogen.py / *_autogen.md (atomic rename)
    - Never overwrites manual files (pipeline.py, __manual__.py, __init__.py)
    - Output is deterministic (idempotent) for the same input contracts
    - Traceability: contract_sha256 in every autogen header + runtime constants
"""

__version__ = "1.3.0"
__author__ = "painting-system"
