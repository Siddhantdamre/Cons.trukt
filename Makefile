PYTHON ?= python

.PHONY: install lint typecheck test verify evaluate

install:
	$(PYTHON) -m pip install -e ".[dev]"

lint:
	$(PYTHON) -m ruff check src scripts tests

typecheck:
	$(PYTHON) -m mypy src

test:
	$(PYTHON) -m pytest -q

verify: lint typecheck test

evaluate:
	$(PYTHON) scripts/build_v2_benchmarks.py
	$(PYTHON) -m cons_trukt train-hazard-model --dataset benchmarks/hazard_v2/train.jsonl --output artifacts/hazard_nb_v2.json
	$(PYTHON) -m cons_trukt validate-hazards --dataset benchmarks/hazard_v2/test.jsonl --ood-dataset benchmarks/hazard_v2/ood_v3.jsonl --model artifacts/hazard_nb_v2.json --output results/hazard_v2/selective_evaluation_v3.json
	$(PYTHON) -m cons_trukt fit-precedent-index --corpus benchmarks/retrieval_v2/corpus.jsonl --output artifacts/precedent_tfidf_v2.json
	$(PYTHON) -m cons_trukt evaluate-retrieval --queries benchmarks/retrieval_v2/queries.jsonl --model artifacts/precedent_tfidf_v2.json --output results/retrieval_v2/evaluation.json
