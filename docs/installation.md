# Installation

Requires Python 3.12+.

```bash
pip install qfire-hipaa-firewall                    # core: PyYAML, regex
pip install "qfire-hipaa-firewall[classifier]"       # + onnxruntime and tokenizers, for the local ONNX classifier node
```

## From source (uv)

```bash
git clone https://github.com/chintagunta/qfire-hipaa-firewall.git
cd qfire-hipaa-firewall
uv sync                    # core: PyYAML, regex
uv sync --extra classifier # + onnxruntime (CPU) and tokenizers
```

## Verify

```bash
uv run qfire validate --rules rules/
```
