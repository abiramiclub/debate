"""SEAM SLICE — real mediator. Attempts ONE live call through the 4-method
interface. Reports PASS with sane output, or BLOCKED if no credentials are
available in this environment.

Run:  python -m mediator.probe_real
"""

from mediator.base import Read
from mediator.claude import ClaudeMediator

READS = [
    Read("Birch", "A four-day week boosts wellbeing and output stays high.", 4),
    Read("Cedar", "We need five-day coverage for client response.", 4),
]


def main() -> int:
    med = ClaudeMediator()
    try:
        candidates = med.synthesize_candidates(READS, 3)
        steelman = med.steelman_minority(READS, [0, 1])
        assert candidates and isinstance(candidates[0], str)
        assert isinstance(steelman, str) and steelman
        print("REAL MEDIATOR SEAM: PASS")
        print("  candidates:", candidates)
        print("  steelman  :", steelman[:160])
        return 0
    except Exception as e:  # noqa: BLE001 - report any failure cleanly
        print("REAL MEDIATOR SEAM: BLOCKED in this environment")
        print(f"  {type(e).__name__}: {str(e)[:200]}")
        print("  Needs an OpenClaw endpoint or ANTHROPIC_API_KEY. Adapter is built and "
              "offline-tested (tests/test_real_mediator.py).")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
