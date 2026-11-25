.PHONY: install test lint run app demo docker clean

install:            ## install TruthLayer and the dev tools
	pip install -e ".[dev]"

test:               ## pytest + ruff + mypy (no AI calls)
	pytest -q
	ruff check .
	mypy

lint:
	ruff check .

run:                ## whole pipeline on the Blue Button case, MOCK mode unless you add --live
	truthlayer run --auto-approve-high

app:                ## web dashboard on http://localhost:8501
	truthlayer app

demo:               ## run on the SYNTHETIC fixtures
	truthlayer demo

docker:
	docker build -t truthlayer .

clean:
	rm -rf demo-output .pytest_cache .mypy_cache .ruff_cache
