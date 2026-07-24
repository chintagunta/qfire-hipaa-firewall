# Contributing

```{include} ../CONTRIBUTING.md
:start-line: 2
```

## Building these docs

```bash
uv sync --group docs
uv run sphinx-build -b html docs docs/_build/html
```

Open `docs/_build/html/index.html`. On Windows, `docs\make.bat html`; elsewhere,
`make -C docs html`.
