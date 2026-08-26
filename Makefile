MAKEFLAGS += --warn-undefined-variables
SHELL := bash
.SHELLFLAGS := -eu -o pipefail -c
.DEFAULT_GOAL := responses.db
# We don't want this:
# .DELETE_ON_ERROR:
.SUFFIXES:

.PHONY: test test_survey test_vary llm analyze

data:
	ln -s default_data data


analyze:
	mkdir -p Results/2026-07-20/analysis
	python3 src/interact.py analyze --trace variations \
		Results/2026-07-20/variations.csv Results/2026-07-20/analysis

test/output:
	mkdir -p $@

test_data: | data

# Sanity test that black-boxes the calls to ollama:
test: cleantest test_data test_vary test_survey

test_vary: | test/output
	python3 src/interact.py vary $|/variations.csv \
		--models trivial --sleep 0 --random-seed 0 --logfile test/output/vary.log
	diff --strip-trailing-cr -q test/expected/variations.csv $|/variations.csv
	sqlite3 test/output/variations.db -cmd '.mode csv' \
		-cmd '.import test/output/variations.csv variations' ''

test_survey: | test/output
	python3 src/interact.py conduct-survey $|/responses.csv \
		--sleep 0 --mediator-type trivial --participant-model trivial --random-seed 0 \
		--logfile test/output/survey.log
	diff --strip-trailing-cr -q test/expected/responses.csv $|/responses.csv
	sqlite3 test/output/responses.db -cmd '.mode csv' \
		-cmd '.import test/output/responses.csv responses' ''

variations.db: variations.csv
	rm -f variations.db
	sqlite3 variations.db -cmd '.mode csv' -cmd '.import variations.csv variations' ''

variations.csv:
	test -f $@ && mv -f $@ $@.$$(date +%s) || true
	python3 src/interact.py vary --trace --sleep 300 $< $@

responses.db: responses.csv
	rm -f responses.db
	sqlite3 responses.db -cmd '.mode csv' -cmd '.import responses.csv responses' ''

responses.csv:
	python3 src/interact.py conduct-survey --trace $< $@

llm:
	docker pull ollama/ollama:0.12.1-rc0

cleantest:
	rm -Rf test/output

clean: cleantest
	rm -f responses.db responses.csv variations.db variations.csv vary.log survey.log
