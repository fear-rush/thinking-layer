.PHONY: check-demolition

check-demolition:
	@! rg -n -i 'answer\.composer|retrieval\.(evidence|planning|query_tools|search|topic_coverage)|indexing\.(scoring|semantic|title)|config\.(heuristic_audit|heuristics)|lexicon\.(candidates|merge)|evaluation\.golden|confidence\.score' thinking_layer
