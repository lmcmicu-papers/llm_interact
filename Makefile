##
# llm_interact - a handy tool for communicating with Ollama LLM models using Python
# Copyright (C) 2025 Michael E. Cuffaro
# 
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
##

MAKEFLAGS += --warn-undefined-variables
SHELL := bash
.SHELLFLAGS := -eu -o pipefail -c
.DEFAULT_GOAL := responses.db
.SUFFIXES:

# Build a database of variations:

variations.db: variations.csv
	rm -f variations.db
	sqlite3 variations.db -cmd '.mode csv' -cmd '.import variations.csv variations' ''

variations.csv:
	test -f $@ && mv -f $@ $@.$$(date +%s) || true
	python3 src/interact.py vary --models llama3.1 mistral llama3.2 pshohel/gemini-3-pro-preview deepseek-r1 \
		--trace $< $@

# Build a database of responses to a questionnaire:

responses.db: responses.csv
	rm -f responses.db
	sqlite3 responses.db -cmd '.mode csv' -cmd '.import responses.csv responses' ''

responses.csv:
	python3 src/interact.py conduct-survey --trace $< $@

clean: cleantest
	rm -f responses.db responses.csv variations.db variations.csv vary.log survey.log
	rm -Rf data.bak.*

# Tests

.PHONY: test prepare_test_data restore_normal_data test_vary test_survey cleantest

# Sanity test that black-boxes the calls to ollama:
test: cleantest prepare_test_data test_vary test_survey restore_normal_data

prepare_test_data:
	test ! -h data.bak || mv -f data.bak data.bak.$$(date +"%s")
	test ! -h data || mv -f data data.bak
	ln -s default_data data

restore_normal_data:
	rm -f data
	mv -f data.bak data

test_vary: | test/output
	python3 src/interact.py vary $|/variations.csv \
		--models trivial --sleep 0 --random-seed 0 --logfile test/output/vary.log --trace
	diff --strip-trailing-cr -q test/expected/variations.csv $|/variations.csv
	sqlite3 test/output/variations.db -cmd '.mode csv' \
		-cmd '.import test/output/variations.csv variations' ''

test_survey: | test/output
	python3 src/interact.py conduct-survey $|/responses.csv \
		--sleep 0 --mediator-type trivial --participant-model trivial --random-seed 0 \
		--logfile test/output/survey.log --trace
	diff --strip-trailing-cr -q test/expected/responses.csv $|/responses.csv
	sqlite3 test/output/responses.db -cmd '.mode csv' \
		-cmd '.import test/output/responses.csv responses' ''

cleantest:
	rm -Rf test/output

test/output:
	mkdir -p $@
