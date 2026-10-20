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

from enum import Enum
from langchain.chat_models import init_chat_model
from langchain.messages import HumanMessage, SystemMessage

import csv
import logging
import random
import re
import signal
import sys
import time

from common import Timeout, generate_context_message
from global_vars import MAX_MEMORY, DEFAULT_SLEEP, DEFAULT_VARIER_LLM_TEMPERATURE, \
    DEFAULT_MEDIATOR_LLM_MODEL, DEFAULT_MEDIATOR_LLM_MODEL_ALT, LLM_RESPONSE_TIMEOUT
from mediator import Mediator


logger = logging.getLogger(__name__)


# TODO: Make this a command-line argument:
USE_MEDIATION = False


class VarierType(Enum):
    """
    Represents the type of an varier
    """
    Trivial = 0
    LLM = 1


class Varier:
    """Represents a varier"""
    def __init__(self, varier_model):
        if varier_model.casefold() == "trivial":
            self.varier_type = VarierType.Trivial
            self.trivial = Varier_Trivial()
        else:
            self.varier_type = VarierType.LLM
            self.llm = Varier_LLM(
                varier_model,
                DEFAULT_VARIER_LLM_TEMPERATURE
            )

    def reset(self):
        if self.varier_type == VarierType.Trivial:
            return self.trivial.reset()
        else:
            return self.llm.reset()

    def invoke(self, message):
        if self.varier_type == VarierType.Trivial:
            return self.trivial.invoke(message)
        else:
            return self.llm.invoke(message)

    def vary(self, thesis, num_variants, sleep_time=DEFAULT_SLEEP):
        if self.varier_type == VarierType.Trivial:
            return self.trivial.vary(thesis, num_variants)
        else:
            return self.llm.vary(thesis, num_variants, sleep_time)


class Varier_Trivial:
    def __init__(self):
        logger.info(
            "Initializing trivial varier ..."
        )

    def reset(self):
        pass

    def invoke(self, message):
        return "Here is a trivial response."

    def vary(self, thesis, num_variants):
        thesis = thesis["message"]
        rephrased_theses = []
        while len(rephrased_theses) < num_variants:
            ceiling = 1000 if num_variants <= 100 else num_variants * 10
            random_number = random.choice(range(0, ceiling))
            rephrased_thesis = f"{thesis.rstrip('.')} and {random_number} = {random_number}."
            if rephrased_thesis not in rephrased_theses:
                rephrased_theses.append(rephrased_thesis)

        if num_variants == 1:
            logger.info(f"The varier has rephrased the thesis to '{rephrased_thesis}'")
        else:
            logger.info(
                f"The varier claims to have finished rephrasing the thesis '{thesis}' "
                f"{num_variants} times"
            )

        return rephrased_theses


class Varier_LLM:
    def __init__(self, model, temperature):
        # Initialize the LLM varier:
        logger.info(
            f"Initializing LLM varier using model '{model}' and temperature {temperature} ..."
        )
        self.model = model
        self.llm = init_chat_model(f"ollama:{model}", temperature=temperature)
        self.memory = []

    def reset(self):
        self.memory = []

    def invoke(self, message):
        logger.info(
            f"Sending varier {self.model} the message: {message}"
        )

        # Add a timeout:
        signal.alarm(LLM_RESPONSE_TIMEOUT)

        response = ""
        try:
            response = self.llm.invoke([
                SystemMessage(generate_context_message(self.memory)),
                HumanMessage(message),
            ])
        except Timeout:
            logger.error(f"Timed out after {LLM_RESPONSE_TIMEOUT}s")
            return response

        # Cancel the timeout timer:
        signal.alarm(0)

        # Remove any enclosing quotes:
        response = response.content.strip("'").strip('"')

        # Commit the new response to memory, truncating the existing memory first if we have
        # hit the limit of MAX_MEMORY:
        self.memory = self.memory[-MAX_MEMORY + 1:]
        self.memory.append(f"*Human*: {message}\n*AI*: {response}")
        logger.info(
            f"Received a response from varier {self.model}: {response}"
        )
        if len(self.memory) >= MAX_MEMORY:
            logger.warning(
                f"Exceeded memory limit for this LLM. Forgetting what happened {MAX_MEMORY} "
                "rounds of interaction ago."
            )

        return response

    def vary(self, thesis, num_variants, sleep_time=DEFAULT_SLEEP):
        # Explain the task and ask the LLM to summarize it:
        prep_thesis = prepare_varier_thesis(num_variants, thesis["type"])
        response = self.invoke(prep_thesis)
        if response == "":
            return []

        # Give the CPU(s) a break:
        logger.info(
            f"Sleeping for {sleep_time}s before moving on."
        )
        time.sleep(sleep_time)

        # Go ahead with the task:
        thesis = thesis["message"].rstrip('.')
        thesis = (
            f"Ok. Here you go: '{thesis}'. "
            f"Please go ahead, as per my instructions."
        )
        response = self.invoke(thesis)

        # Split the response by newline and return all the lines that have word characters in them:
        return [line for line in response.split('\n') if not re.fullmatch(r"[^\w]*", line)]


def generate_variations(theses, cli_args):
    """
    Generate variations of the given theses. The number of varations to generate
    can be customized using cli_args["num_variants"], and the models
    to generate variations for may be customized using: cli_args["models"] and/or
    cli_args["exclude"]
    """
    def write_csvfile(writer, model, mediator_model, thesis_name, variants):
        for variant in variants:
            row = {
                "model": model,
                "mediator_model": mediator_model,
                "thesis": thesis_name,
                "variant": variant,
            }
            writer.writerow(row)

    csv_filename = cli_args["OUTPUT"]
    min_sleep_time = cli_args.get("sleep") if cli_args.get("sleep") is not None \
        else DEFAULT_SLEEP
    models = [model for model in cli_args["models"] if model not in cli_args["exclude"]]
    num_variants = cli_args['num_variants']
    with open(csv_filename, 'w') as csvfile:
        mediator_type = 'trivial' if cli_args['models'] == ['trivial'] else 'llm'
        mediator_model = None if mediator_type == 'trivial' else DEFAULT_MEDIATOR_LLM_MODEL
        # A model should not be a mediator for its own kind, so we initialize an alternate to
        # handle those cases:
        mediator_alt_model = 'trivial' if mediator_type == 'trivial' \
            else DEFAULT_MEDIATOR_LLM_MODEL_ALT
        mediator = Mediator({
            "mediator_type": mediator_type,
            "llm_mediator_model": mediator_model
        })
        mediator_alt = Mediator({
            "mediator_type": mediator_type,
            "llm_mediator_model": mediator_alt_model
        })
        writer = None
        for i, model in enumerate(models):
            # Initialize a mediator using this model:
            varier = Varier(model)

            # Ask the varier to vary each thesis:
            for j, (_, thesis) in enumerate(theses.items()):
                logger.info(
                    f"Asking model '{model}' to generate {num_variants} variants "
                    f"of: '{thesis['message']}'"
                )

                start = time.time()
                variants = varier.vary(thesis, num_variants, min_sleep_time)
                duration = round(time.time() - start)
                logger.info(f"Got {len(variants)} sentences from {model} after {duration}s.")
                varier.reset()

                # Initialize the CSV writer if it hasn't been initialized already:
                if not writer:
                    writer = csv.DictWriter(csvfile, fieldnames=[
                        "model",
                        "mediator_model",
                        "thesis",
                        "variant",
                    ])
                    writer.writeheader()

                # Output the variants, before pruning, to CSV:
                write_csvfile(writer, model, None, thesis["message"], variants)

                if USE_MEDIATION:
                    sleep_time = round(max(min_sleep_time, duration / 10))
                    logger.info(f"Sleeping for {sleep_time}s before waking up the mediator.")
                    time.sleep(sleep_time)

                    start = time.time()
                    # Send the set of variants to the mediator to prune. The original instructions
                    # are determined by getting the varier preparation message and removing
                    # the last line about summarizing the instructions to make sure that they
                    # are understood.
                    original_instructions = '\n'.join(
                        prepare_varier_thesis(num_variants, thesis["type"]).split('\n')[:-2]
                    )
                    # A model should not be the mediator for its own kind:
                    assigned_mediator = mediator_alt if model == mediator.get_model() else mediator
                    assigned_mediator_model = assigned_mediator.get_model()
                    pruned_variants = assigned_mediator.prune_variants(
                        thesis,
                        original_instructions,
                        variants,
                        num_variants
                    )

                    duration = round(time.time() - start)
                    logger.info(
                        f"Got {len(pruned_variants)} sentences from mediator "
                        f"{assigned_mediator_model} after {duration}s."
                    )
                    mediator.reset()

                    # Output the pruned variants to CSV:
                    write_csvfile(
                        writer, model, assigned_mediator_model, thesis["message"], pruned_variants
                    )

                # Give the CPU(s) a break (unless we are done):
                if i != len(cli_args["models"]) and j != len(theses):
                    sleep_time = round(max(min_sleep_time, duration / 10))
                    logger.info(f"Sleeping for {sleep_time}s before moving on to the next thesis.")
                    time.sleep(sleep_time)

            logger.info(f"Model '{model}' has generated variations for all theses.")
        logger.info("All models have generated variations.")


def prepare_varier_thesis(num_variants, thesis_type):
    if thesis_type.casefold() == "label":
        filename = "data/variation_preparation_prompt_label.txt"
    elif thesis_type.casefold() == "sentence":
        filename = "data/variation_preparation_prompt_sentence.txt"
    else:
        logger.error(f"Invalid thesis_type: {thesis_type}")
        sys.exit(1)

    with open(filename) as fp:
        prompt = fp.read()
        if not prompt:
            logger.error("Could not read variation preparation prompt")
            sys.exit(1)
        return prompt.format(num_variants=num_variants)
