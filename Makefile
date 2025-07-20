.PHONY: format check type test all

# Format code with black
format:
	python -m black game/

# Check formatting without changing files
check:
	python -m black game/ --check

# Type check with mypy
type:
	python -m mypy --strict game/

# Run all checks
all: check type

# Development workflow - format then check
dev: format type
