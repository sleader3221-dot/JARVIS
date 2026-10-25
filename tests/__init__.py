import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

try:
    import anthropic  # noqa: F401
except ImportError:  # let the non-network tests run before dependencies are installed
    from tests import _anthropic_stub

    sys.modules["anthropic"] = _anthropic_stub
