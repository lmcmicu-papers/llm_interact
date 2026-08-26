import logging
import random

from enum import Enum

from global_vars import SUPPORTED_MODELS


logger = logging.getLogger(__name__)


class ResponseCode(Enum):
    HardAgree = 0
    SoftAgree = 1
    SoftDisagree = 2
    HardDisagree = 3
    Other = 4
    Unrecognized = 5


def random_model(except_model):
    """
    Return one of the supported models, other than `except_model`, at random.
    """
    models_to_choose_from = [model for model in SUPPORTED_MODELS if model not in (
        "trivial", except_model
    )]
    model = random.choice(models_to_choose_from)
    if not model:
        raise Exception("Model not defined")

    logger.info(f"Participant model is: {model}")
    return model


def read_messages(filename):
    """
    Read messages from the given file. To allow for multi-line messages, we use ';' as a
    separator.
    """
    with open(filename, "r") as f:
        delim = ";"
        buffer = ""
        items = []
        for line in f:
            buffer += line
            while delim in buffer:
                item, buffer = buffer.split(delim, 1)
                item = item.lstrip("\n")
                items.append(item.rstrip())
        return items


def generate_context_message(conversation_so_far):
    context = '\n'.join(conversation_so_far)
    return (
        "You, a helpful AI assistant, are to treat everything after the newline as a "
        "record of a conversation that you have been having with this human up until "
        "now. You are to use it to inform your response to the human but make sure never "
        f"to explicitly mention it.\n{context}"
    )
