# Contributing

## Development setup
```bash
make setup
```

## Quality checks
```bash
make verify
```

## Adding dependencies
- Runtime: `uv add <package>`
- Dev: `uv add --dev <package>`

## Pull requests
- Keep changes small and focused.
- Add or update tests for behavior changes.
- Make sure `make verify` passes.
