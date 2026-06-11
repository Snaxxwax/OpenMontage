"""Keep pytest from importing the standalone QA scripts in this directory.

`test_04`–`test_08` are executable QA scripts (run directly, e.g.
`python tests/qa/test_05_video_compose.py`), not pytest modules. They run real
video composition at module import time and contain no `def test_*` functions,
so collecting them would trigger side effects and slow/real renders.

Only `test_09_hyperframes_compose.py` holds real pytest tests (gated behind the
`HYPERFRAMES_QA` env var), so it must stay collectable. Ignoring the scripts
individually here — rather than excluding the whole directory via
`norecursedirs` — keeps `test_09` discoverable under a plain `pytest` run.
"""

collect_ignore_glob = ["test_0[4-8]_*.py"]
