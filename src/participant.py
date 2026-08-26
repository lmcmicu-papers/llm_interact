import logging
import numpy
import time
from enum import Enum
from langchain.chat_models import init_chat_model
from langchain.messages import HumanMessage, SystemMessage

from global_vars import DEFAULT_MEAN, DEFAULT_NUM_PARTICIPANTS, DEFAULT_SLEEP, DEFAULT_STD_DEV, \
    MAX_MEMORY
from common import generate_context_message, random_model
from mediator import Mediator, ResponseCode

logger = logging.getLogger(__name__)


class ParticipantType(Enum):
    """
    Represents the type of a participant.
    """
    Trivial = 0
    LLM = 1


class Participant:
    """Represents a survey participant"""
    def __init__(self, model, temperature):
        if model.casefold() == "trivial":
            self.participant_type = ParticipantType.Trivial
            self.trivial = Participant_Trivial()
        else:
            self.participant_type = ParticipantType.LLM
            self.llm = Participant_LLM(model, temperature)

    def reset(self):
        if self.participant_type == ParticipantType.Trivial:
            return self.trivial.reset()
        else:
            return self.llm.reset()

    def invoke(self, message):
        if self.participant_type == ParticipantType.LLM:
            return self.llm.invoke(message)
        else:
            return self.trivial.invoke(message)

    def survey(self, claim):
        if self.participant_type == ParticipantType.Trivial:
            return self.trivial.survey(claim)
        else:
            return self.llm.survey(claim)


class Participant_Trivial:
    """Represents a trivial survey participant"""
    def __init__(self):
        logger.info(
            "Initializing trivial participant ..."
        )

    def reset(self):
        pass

    def invoke(self, message):
        return "Here is a trivial response."

    def survey(self, message):
        return "Here is a trivial response."


class Participant_LLM:
    """Represents a survey participant using an LLM"""
    def __init__(self, participant_model, participant_temperature):
        self.llm = init_chat_model(
            f"ollama:{participant_model}",
            temperature=participant_temperature
        )
        self.model = participant_model
        self.memory = []

    def reset(self):
        self.memory = []

    def invoke(self, message):
        logger.info(
            f"Sending participant {self.model} the message: {message}"
        )
        response = self.llm.invoke([
            SystemMessage(generate_context_message(self.memory)),
            HumanMessage(message),
        ]).content.strip("'").strip('"')
        # Commit the new response to memory, truncating the existing memory first if we have
        # hit the limit of MAX_MEMORY:
        self.memory = self.memory[-MAX_MEMORY + 1:]
        self.memory.append(f"*Human*: {message}\n*AI*: {response}")
        logger.info(
            f"Received a response from participant {self.model}: {response}"
        )
        if len(self.memory) >= MAX_MEMORY:
            logger.warning(
                f"Exceeded memory limit for this LLM. Forgetting what happened {MAX_MEMORY} "
                "rounds of interaction ago."
            )

        return response

    def survey(self, message):
        with open("data/participant_survey_message.txt") as fp:
            participant_context = fp.read()

        participant_response = self.invoke(
            f"{participant_context} Here you go: '{message}'"
        )
        return participant_response


def survey_participant(
    messages,
    participant,
    participant_model,
    participant_temperature,
    mediator,
    response_distribution,
):
    """
    Iterates over the given messages, randomly asking the mediator to rephrase them, and then
    records the participant's responses to each in the given response distribution dictionary.
    """
    # Sanity check:
    if not participant_model:
        raise Exception("Participant model not defined")

    participant_label = participant_model if participant_model.casefold() != "trivial" else \
        random_model(mediator.get_model())

    for (msg_num, message) in enumerate(messages):
        logger.info(f"Received message #{msg_num + 1}: '{message}'")

        # Ask the mediator to rephrase the message if she so chooses:
        rephrased_message = mediator.rephrase(message)

        # Create a new entry in the map for this combination of parameters if one hasn't
        # been created already:
        if not response_distribution.get(msg_num):
            response_distribution[msg_num] = {}
        if not response_distribution[msg_num].get(rephrased_message):
            response_distribution[msg_num][rephrased_message] = {}
        if not response_distribution[msg_num][rephrased_message].get(participant_label):
            response_distribution[msg_num][rephrased_message][participant_label] = {}
        if not (response_distribution[msg_num][rephrased_message][participant_label]
                .get(participant_temperature)):
            response_distribution[msg_num][rephrased_message][participant_label][
                participant_temperature
            ] = {
                "hard_agree": 0,
                "soft_agree": 0,
                "hard_disagree": 0,
                "soft_disagree": 0,
                "other": 0,
                "unrecognized": 0,
            }

        response_content = participant.survey(rephrased_message)
        participant.reset()
        logger.info(f"Got response from participant: '{response_content}'")
        response_code = mediator.interpret_response(rephrased_message, response_content)
        logger.info(f"The mediator interprets the participant response as: {response_code}")

        if response_code == ResponseCode.HardAgree:
            response_distribution[msg_num][rephrased_message][participant_label][
                participant_temperature
            ][
                "hard_agree"
            ] += 1
        elif response_code == ResponseCode.SoftAgree:
            response_distribution[msg_num][rephrased_message][participant_label][
                participant_temperature
            ][
                "soft_agree"
            ] += 1
        elif response_code == ResponseCode.SoftDisagree:
            response_distribution[msg_num][rephrased_message][participant_label][
                participant_temperature
            ][
                "soft_disagree"
            ] += 1
        elif response_code == ResponseCode.HardDisagree:
            response_distribution[msg_num][rephrased_message][participant_label][
                participant_temperature
            ][
                "hard_disagree"
            ] += 1
        elif response_code == ResponseCode.Other:
            response_distribution[msg_num][rephrased_message][participant_label][
                participant_temperature
            ][
                "other"
            ] += 1
        else:
            response_distribution[msg_num][rephrased_message][participant_label][
                participant_temperature
            ][
                "unrecognized"
            ] += 1


def conduct_survey(messages, cli_args):
    """
    Conduct a survey using the given messages and command line arguments.
    """
    # Collect the input parameters that have defaults:
    num_participants = cli_args.get("participants") \
        if cli_args.get("participants") is not None else DEFAULT_NUM_PARTICIPANTS
    sleep_time = cli_args.get("sleep") if cli_args.get("sleep") is not None \
        else DEFAULT_SLEEP
    mean = cli_args.get("mean") if cli_args.get("mean") is not None else DEFAULT_MEAN
    std_dev = cli_args.get("std_dev") if cli_args.get("std_dev") is not None \
        else DEFAULT_STD_DEV

    # Input parameters without defaults:
    required_participant_model = cli_args.get("participant_model")

    # Initialize the mediator:
    mediator = Mediator(cli_args)

    # This will record distribution of responses, indexed by message id, message_variant,
    # participant model, and participant temperature:
    response_distribution = {}
    for participant_num in range(num_participants):
        if participant_num != 0:
            # Give the CPU(s) a break:
            logger.info(
                f"Sleeping for {sleep_time}s before moving on to participant #{participant_num}."
            )
            time.sleep(sleep_time)
        participant_model = required_participant_model or random_model(mediator.get_model())
        participant_temperature = round(numpy.random.normal(mean, std_dev), 1)
        logger.info(
            f"Initializing Participant #{participant_num + 1} of {num_participants}, using "
            f"Ollama model {participant_model}, with temperature {participant_temperature} ..."
        )
        participant = Participant(participant_model, participant_temperature)
        survey_participant(
            messages, participant, participant_model, participant_temperature,
            mediator, response_distribution,
        )

    logger.info(f"Responses from all {num_participants} survey partipants have been collected.")
    return response_distribution
