"""Enable ``python -m archivesnap`` as an alias for the console script."""

from .cli import main

if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
