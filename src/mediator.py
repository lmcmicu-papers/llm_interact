import logging
import random
import re
import sys

from textwrap import indent
from enum import Enum
from langchain.chat_models import init_chat_model
from langchain.messages import HumanMessage, SystemMessage

from common import ResponseCode, generate_context_message
from global_vars import DEFAULT_MEDIATOR_LLM_TEMPERATURE, DEFAULT_MEDIATOR_LLM_MODEL, \
    DEFAULT_REPHRASE_RATIO, MAX_MEMORY

logger = logging.getLogger(__name__)


class MediatorType(Enum):
    """
    Represents the type of a mediator.
    """
    Trivial = 0
    LLM = 1


class Mediator:
    """
    Abstract representation of a mediator.
    """
    def __init__(self, args):
        mediator_type = args.get("mediator_type", "")
        if mediator_type.casefold() == "llm":
            self.mediator_type = MediatorType.LLM
            self.llm = Mediator_LLM(
                args.get("llm_mediator_model"),
                args.get("llm_mediator_temperature"),
                args.get("rephrase_ratio")
            )
        elif mediator_type.casefold() == "trivial":
            self.mediator_type = MediatorType.Trivial
            self.trivial = Mediator_Trivial()
        else:
            logger.error(f"Unsupported mediator type: {mediator_type}")
            return None

    def reset(self):
        if self.mediator_type == MediatorType.Trivial:
            return self.trivial.reset()
        else:
            return self.llm.reset()

    def get_model(self):
        if self.mediator_type == MediatorType.LLM:
            return self.llm.get_model()

    def prune_variants(self, label, instructions, variants, num_variants):
        if self.mediator_type == MediatorType.LLM:
            return self.llm.prune_variants(label, instructions, variants, num_variants)
        elif self.mediator_type == MediatorType.Trivial:
            return self.trivial.prune_variants(variants)
        else:
            logger.error(f"Unsupported mediator type: {self.mediator_type}")

    def invoke(self, message):
        if self.mediator_type == MediatorType.LLM:
            return self.llm.invoke(message)
        elif self.mediator_type == MediatorType.Trivial:
            return self.trivial.invoke(message)
        else:
            logger.error(f"Unsupported mediator type: {self.mediator_type}")

    def rephrase(self, message):
        if self.mediator_type == MediatorType.LLM:
            return self.llm.rephrase(message)
        elif self.mediator_type == MediatorType.Trivial:
            return self.trivial.rephrase(message)
        else:
            logger.error(f"Unsupported mediator type: {self.mediator_type}")

    def interpret_response(self, claim, response):
        if self.mediator_type == MediatorType.LLM:
            return self.llm.interpret_response(claim, response)
        elif self.mediator_type == MediatorType.Trivial:
            return self.trivial.interpret_response(claim, response)
        else:
            logger.error(f"Unsupported mediator type: {self.mediator_type}")


class Mediator_Trivial:
    """Implements a mediator trivially"""
    def __init__(self):
        logger.info(
            "Initializing trivial mediator ..."
        )

    def reset(self):
        pass

    def invoke(self, message):
        return message

    def prune_variants(self, variants):
        return variants

    def rephrase(self, message):
        random_number = random.choice(range(0, 1000))
        rephrased_message = f"{message.rstrip('.')} and {random_number} = {random_number}."
        logger.info(f"The mediator has rephrased the message to '{rephrased_message}'")
        return rephrased_message

    def interpret_response(self, message, response):
        return random.choice([choice for choice in ResponseCode.__iter__()])


class Mediator_LLM:
    """
    Implements a mediator using an LLM.
    """
    def __init__(self, model, temperature, rephrase_ratio):
        # Initialize the LLM mediator:
        logger.info(
            f"Initializing LLM mediator using model '{model}' and temperature {temperature} ..."
        )
        self.model = model or DEFAULT_MEDIATOR_LLM_MODEL
        self.temperature = temperature or DEFAULT_MEDIATOR_LLM_TEMPERATURE
        self.llm = init_chat_model(f"ollama:{model}", temperature=temperature)
        self.rephrase_ratio = rephrase_ratio or DEFAULT_REPHRASE_RATIO
        self.memory = []

    def get_model(self):
        return self.model

    def get_temperature(self):
        return self.temperature

    def reset(self):
        self.memory = []

    def invoke(self, message):
        response = self.llm.invoke([
            SystemMessage(generate_context_message(self.memory)),
            HumanMessage(message),
        ]).content.strip("'").strip('"')
        # Commit the new response to memory, truncating the existing memory first if we have
        # hit the limit of MAX_MEMORY:
        self.memory = self.memory[-MAX_MEMORY + 1:]
        self.memory.append(f"*Human*: {message}\n*AI*: {response}")
        if len(self.memory) >= MAX_MEMORY:
            logger.warning(
                f"Exceeded memory limit for this LLM. Forgetting what happened {MAX_MEMORY} "
                "rounds of interaction ago."
            )

        return response

    def prune_variants(self, label, instructions, variants, num_variants):
        with open("data/mediator_prune_message.txt") as fp:
            mediator_message = fp.read()
            if not mediator_message:
                logger.error("Could not read variation pruning prompt")
                sys.exit(1)

            instructions = indent(instructions, "            > ")
            variants = indent("{}".format("\n".join(variants)), "            > ")
            mediator_message = mediator_message.format(
                label=label,
                num_variants=num_variants,
                instructions=instructions,
                variants=variants,
            )

            logger.info(f"Sending mediator the message: {mediator_message}")
            response = self.invoke(mediator_message)
            logger.info(f"Received a reponse from the mediator:\n{response}")
            # Split the response by newline and return all the lines that have word
            # characters in them:
            return [
                line for line in response.split('\n') if not re.fullmatch(r"[^\w]*", line)
            ]

    def rephrase(self, sentence):
        with open("data/mediator_rephrase_message.txt") as fp:
            mediator_variation_context = fp.read()
            if (random.choice(range(1, 11)) / 10) <= self.rephrase_ratio:
                logger.info("The mediator has decided to rephrase.")
                rephrased_sentence = self.invoke(
                    f"{mediator_variation_context} The sentence is: '{sentence}'"
                )
                logger.info(f"The mediator has rephrased the sentence to '{rephrased_sentence}'")
            else:
                logger.info("The mediator has decided not to rephrase.")
                rephrased_sentence = sentence
            return [rephrased_sentence]

    def interpret_response(self, claim, response):
        with open("data/mediator_interpret_response_message.txt") as fp:
            mediator_response_context = fp.read()
            logger.info("Asking the mediator to interpret the response.")
            mediator_response = self.invoke(
                f"{mediator_response_context} The claim, X, is '{claim}'. "
                f"The response is '{response}'"
            )
            logger.info(f"Full mediator response: {mediator_response}")
            mediator_response_lc = mediator_response.casefold().lstrip()
            if mediator_response_lc.startswith("strong agree"):
                return ResponseCode.HardAgree
            elif mediator_response_lc.startswith("weak agree"):
                return ResponseCode.SoftAgree
            elif mediator_response_lc.startswith("weak disagree"):
                return ResponseCode.SoftDisagree
            elif mediator_response_lc.startswith("strong disagree"):
                return ResponseCode.HardDisagree
            elif mediator_response_lc.startswith("other"):
                return ResponseCode.Other
            else:
                return ResponseCode.Unrecognized
