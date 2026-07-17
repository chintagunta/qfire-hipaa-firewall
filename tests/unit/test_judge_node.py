import json
import urllib.error
from contextlib import contextmanager
from unittest.mock import patch

import pytest

from qfire.nodes.judge import JudgeNode


@contextmanager
def _fake_response(body: dict):
    class _Resp:
        def read(self):
            return json.dumps(body).encode("utf-8")

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

    yield _Resp()


def test_judge_allows_in_scope_request():
    node = JudgeNode(endpoint="http://fake/judge", scope="general health info only")
    with patch("urllib.request.urlopen") as mock_urlopen:
        with _fake_response({"response": "allow"}) as resp:
            mock_urlopen.return_value = resp
            result = node.run("What is hypertension?")
    assert result.verdict == "allow"


def test_judge_blocks_out_of_scope_request():
    node = JudgeNode(endpoint="http://fake/judge", scope="general health info only")
    with patch("urllib.request.urlopen") as mock_urlopen:
        with _fake_response({"response": "block - diagnosis request"}) as resp:
            mock_urlopen.return_value = resp
            result = node.run("Do I have meningitis?")
    assert result.verdict == "block"


def test_judge_unreachable_raises():
    node = JudgeNode(endpoint="http://fake/judge", scope="x", timeout=0.01)
    with patch("urllib.request.urlopen", side_effect=urllib.error.URLError("refused")):
        with pytest.raises(RuntimeError):
            node.run("anything")
