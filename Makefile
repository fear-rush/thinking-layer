.PHONY: test-fast test-live-api test-acceptance test-ui-fixture test-ui-live

# Fast, deterministic checks. These use fixtures or temporary SQLite indexes.
test-fast:
	uv run python -m unittest discover -s tests -v

# Production QueryService and API against the current generated SQLite index.
test-live-api:
	uv run python -m unittest discover -s tests/acceptance -v

# Exact live corpus/answer acceptance. This intentionally fails on any case.
test-acceptance: test-live-api
	uv run python -m thinking_layer.evaluation.golden --tier smoke --jobs 1 --require-acceptance

test-ui-fixture:
	cd frontend && bun run test:e2e:fixture

test-ui-live:
	cd frontend && bun run test:e2e:live
