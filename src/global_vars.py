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

import json

# Possible models. Make sure these are all present in the output of the `ollama list` command.
# To get just the model names run `ollama list|awk '{print $1}'|grep -v "NAME"`.
# To get just the model ids run `ollama list|awk '{print $2}'|grep -v "ID"`.
SUPPORTED_MODELS = [
    "trivial",
    "llama3.1",
    "mistral",
    "pshohel/gemini-3-pro-preview",
    "openchat",
    "gemma3:1b",
    "llama3.2",
    "deepseek-r1",
    "gemma",
    "stable-beluga",
    "orca-mini",
    "samantha-mistral",
    "phi4-mini",
    "zephyr",
]

# The maximum number of lines to keep in the conversation memory:
MAX_MEMORY = 250000

# The possible temperature settings for participants and mediators:
VALID_TEMPERATURES = [
    0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0,
    1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7, 1.8, 1.9, 2.0,
]

# ---
# Defaults that can be overriden by command line arguments:
# ---

# Default number of participants to survey:
DEFAULT_NUM_PARTICIPANTS = 100

# The value of the mean of the normal distribution used to determine each participant's
# temperature:
DEFAULT_MEAN = 0.6

# The value of the standard deviation (or 'width') of the normal distribution used to determine
# each participant's temperature:
DEFAULT_STD_DEV = 0.2

DEFAULT_MEDIATOR_LLM_MODEL = "llama3.1"
DEFAULT_MEDIATOR_LLM_MODEL_ALT = "mistral"

# See https://markaicode.com/ollama-temperature-parameter-tuning-guide/
DEFAULT_MEDIATOR_LLM_TEMPERATURE = 0.0
DEFAULT_VARIER_LLM_TEMPERATURE = 0.6

# The default proportion of sentences that should be rephrased by the mediator before being
# submitted to a participant:
DEFAULT_REPHRASE_RATIO = 0.9

# Default number of seconds to sleep after surveying a participant:
DEFAULT_SLEEP = 60

# Maximum number of seconds to wait for a response from an LLM:
LLM_RESPONSE_TIMEOUT = 60 * 60 * 4

# The default logfile name will be one of these prefixes followed by the extension 'log':
DEFAULT_SURVEY_LOGFILE_PREFIX = "survey"
DEFAULT_VARIATIONS_LOGFILE_PREFIX = "vary"
DEFAULT_INTERACT_LOGFILE_PREFIX = "interact"
DEFAULT_CUSTOM_LOGFILE_PREFIX = "custom"
DEFAULT_ANALYZE_VARIATIONS_LOGFILE_PREFIX = "analyze_variations"
DEFAULT_ANALYZE_SURVEY_LOGFILE_PREFIX = "analyze_survey"

# TODO: Make this a configuration file rather than a module.

with open("data/theses.json") as fp:
    contents = fp.read()
    THESES = json.loads(contents)
