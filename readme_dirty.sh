#!/usr/bin/env bash

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

cat <<EOF > saved_usage.$$
$ python3 src/interact.py --help
usage: interact.py [-h] {conduct-survey,vary,analyze,interact,custom} ...

Interact with LLMs from the Ollama library in various ways

positional arguments:
  {conduct-survey,vary,analyze,interact,custom}
                        Use --help with the subcommand name to get help
                        specific to that command.
    conduct-survey      Conduct a survey with N participants
    vary                Generate label variants
    analyze             Analyze data
    interact            Directly interact with an LLM
    custom              Run a customized sequence of interactions with an LLM.

options:
  -h, --help            show this help message and exit

$ python3 src/interact.py conduct-survey --help
usage: interact.py conduct-survey [-h] [--participants N] [--mean X]
                                  [--std-dev X] [--rephrase-ratio R]
                                  [--participant-model [{trivial,llama3.1,mistral,pshohel/gemini-3-pro-preview,openchat,gemma3:1b,llama3.2,deepseek-r1,gemma,stable-beluga,orca-mini,samantha-mistral,phi4-mini,zephyr}]]
                                  [--mediator-type {llm,trivial}]
                                  [--llm-mediator-model [{trivial,llama3.1,mistral,pshohel/gemini-3-pro-preview,openchat,gemma3:1b,llama3.2,deepseek-r1,gemma,stable-beluga,orca-mini,samantha-mistral,phi4-mini,zephyr}]]
                                  [--llm-mediator-temperature LLM_MEDIATOR_TEMPERATURE]
                                  [--sleep SECONDS] [--random-seed SEED]
                                  [--logfile LOGFILE] [--trace]
                                  OUTPUT

positional arguments:
  OUTPUT                The filename to which the CSV data will be written

options:
  -h, --help            show this help message and exit
  --participants N      The number of participants to survey (default: 100)
  --mean X              The value of the mean of the normal distribution used
                        to determine each participant's temperature (default:
                        0.6).
  --std-dev X           The value of the standard deviation (or 'width') of
                        the normal distribution used to determine each
                        participant's temperature (default: 0.2).
  --rephrase-ratio R    The proportion of messages (between 0 and 1) that
                        should be rephrased by the mediator (default: 0.9).
  --participant-model [{trivial,llama3.1,mistral,pshohel/gemini-3-pro-preview,openchat,gemma3:1b,llama3.2,deepseek-r1,gemma,stable-beluga,orca-mini,samantha-mistral,phi4-mini,zephyr}]
                        The model LLM to use for every participant (default:
                        use a random non-trivial model for every participant).
  --mediator-type {llm,trivial}
                        The type of mediator to use (default: llm).
  --llm-mediator-model [{trivial,llama3.1,mistral,pshohel/gemini-3-pro-preview,openchat,gemma3:1b,llama3.2,deepseek-r1,gemma,stable-beluga,orca-mini,samantha-mistral,phi4-mini,zephyr}]
                        The LLM model to use as a mediator (default: llama3.1,
                        alternate: mistral). Only applicable to mediators of
                        type 'llm'
  --llm-mediator-temperature LLM_MEDIATOR_TEMPERATURE
                        The temperature of the mediator (default 0.0). Only
                        applicable to mediators of type 'llm'
  --sleep SECONDS       The number of seconds to sleep after surveying each
                        participant (default: 60)
  --random-seed SEED    Specify a SEED for the random number generator.
  --logfile LOGFILE     Write logging output to LOGFILE (defaults to
                        survey.log).
  --trace               Display stack trace information when exceptions are
                        caught.

$ python3 src/interact.py vary --help
usage: interact.py vary [-h] [--models MODEL [MODEL ...]]
                        [--exclude EXCLUDED_MODEL [EXCLUDED_MODEL ...]]
                        [--num-variants NUM_VARIANTS] [--sleep SECONDS]
                        [--random-seed SEED] [--logfile LOGFILE] [--trace]
                        OUTPUT

positional arguments:
  OUTPUT                The filename to which the CSV data will be written

options:
  -h, --help            show this help message and exit
  --models MODEL [MODEL ...]
                        A list of the model(s) to use for generating
                        variations (default: all non-trivial models)
  --exclude EXCLUDED_MODEL [EXCLUDED_MODEL ...]
                        A list of models that should not be used when
                        generating variations. In the case of a conflict
                        between --models and --exclude, the latter takes
                        priority. (default: no models excluded)
  --num-variants NUM_VARIANTS
                        The total number of variations of the given label to
                        generate.
  --sleep SECONDS       The number of seconds to sleep after generating each
                        set of variations (default: 60 seconds)
  --random-seed SEED    Specify a SEED for the random number generator
                        (normally only for testing).
  --logfile LOGFILE     Write logging output to LOGFILE (defaults to
                        'vary.log')
  --trace               Display stack trace information when exceptions are
                        caught.

$ python3 src/interact.py interact --help
usage: interact.py interact [-h] [--transient] [--random-seed SEED]
                            [--logfile LOGFILE] [--trace]
                            MODEL TEMPERATURE

positional arguments:
  MODEL               The name of the model to interact with.
  TEMPERATURE         The temperature to use.

options:
  -h, --help          show this help message and exit
  --transient         Do not keep track of the conversation but begin every
                      question with a clean slate.
  --random-seed SEED  Specify a SEED for the random number generator (normally
                      only for testing).
  --logfile LOGFILE   Write logging output to LOGFILE (defaults to
                      'interact.log')
  --trace             Display stack trace information when exceptions are
                      caught.
EOF

echo "$ python3 src/interact.py --help" > current_usage.$$
python3 src/interact.py --help >> current_usage.$$
echo >> current_usage.$$
echo "$ python3 src/interact.py conduct-survey --help" >> current_usage.$$
python3 src/interact.py conduct-survey --help >> current_usage.$$
echo >> current_usage.$$
echo "$ python3 src/interact.py vary --help" >> current_usage.$$
python3 src/interact.py vary --help >> current_usage.$$
echo >> current_usage.$$
echo "$ python3 src/interact.py interact --help" >> current_usage.$$
python3 src/interact.py interact --help >> current_usage.$$
diff --strip-trailing-cr -q saved_usage.$$ current_usage.$$ > /dev/null
if [[ $? -eq 0 ]]
then
    echo "The saved usage is up to date"
    rm -f *.$$
else
    echo "The saved usage is not up to date."
    echo "Here are the differences:"
    echo "-----"
    diff --strip-trailing-cr saved_usage.$$ current_usage.$$ | tail -n +2
    echo
    echo "Here is the current usage:"
    echo "-----"
    cat current_usage.$$
    rm -f *.$$
    exit 1
fi
