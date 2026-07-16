.PHONY: baseline-check

baseline-check:
	@test -d data/ease-bi
	@test -d data/peraturan-ojk
	@test -d downloads/ease-bi
	@test -d downloads/peraturan-ojk
	@test ! -e processed
	@uv lock --check
