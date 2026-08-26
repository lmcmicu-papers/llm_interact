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

import logging
import re
import sys
import textwrap

from langchain.chat_models import init_chat_model
from langchain.messages import HumanMessage, SystemMessage
from os.path import dirname, realpath

from common import generate_context_message

print(
    textwrap.dedent("""
    llm_interact  Copyright (C) 2025 Michael E. Cuffaro
    This program comes with ABSOLUTELY NO WARRANTY.
    This is free software, and you are welcome to redistribute it
    under certain conditions. Type sys[tem]:license for details.
    """)
)


logger = logging.getLogger(__name__)


def directly_interact(model, temperature, transient):
    """
    TODO: Add description
    """
    logger.info(f"Initializing model ollama:{model} with temperature {temperature}")
    llm = init_chat_model(f"ollama:{model}", temperature=temperature)
    conversation_so_far = []
    print("[Entering interactive mode. To run system commands, use the syntax: "
          "'system:COMMAND' (or 'sys:COMMAND').]")
    print("[To see the available system commands, enter 'system:help' (or 'sys:help)'.]")
    print("[To quit, enter 'system:exit' (or 'sys:exit'), or alternately either press Ctrl-D on "
          "an empty line, or press Ctrl-C.]")

    # TODO: output current day and time when prompting.
    print("[What would you like to say now?]")
    while message := sys.stdin.readline().strip():
        # Ignore blank lines (but don't ignore lines that have nothing but whitespace):
        if not message:
            continue

        # TODO: Add system commands for more fine-grained control, like:
        # repeat the last invocation
        # delete the last n records
        # etc.

        # Handle system messages:
        if matches := re.fullmatch("(sys|system):[ ]*(.+)?", message):
            recognized_instructions = "\n\
            sys[tem]:exit\n\
            sys[tem]:quit\n\
            sys[tem]:[good]bye\n\
            sys[tem]:show[ the] conversation history\n\
            sys[tem]:clear[ the] conversation history\n\
            sys[tem]:[turn ]transient mode on\n\
            sys[tem]:[turn ]transient mode off\n\
            sys[tem]:license\n\
            sys[tem]:help"

            system_message = matches.group(2)
            if (system_message is not None and system_message.casefold() in [
                    "exit", "quit", "bye", "goodbye"
            ]):
                logger.info("Terminating as requested.")
                break
            else:
                if not system_message or system_message == "help":
                    print(f"The recognized system commands are:\n{recognized_instructions}")
                elif system_message.casefold() in ["license", "licence"]:
                    license_path = dirname(realpath(__file__))
                    with open(f"{license_path}/../LICENSE") as fp:
                        print(f"{fp.read()}")
                    print()
                    print("[What would you like to say now?]")
                elif re.fullmatch(r"show([ ]+the|[ ]+our){0,1}[ ]+conversation history",
                                  system_message.casefold()):
                    if transient:
                        print("No conversation history (running in transient mode)")
                    else:
                        if not conversation_so_far:
                            print("This conversation has just started")
                        else:
                            print("Conversation history:\n---\n{}".format(
                                '\n'.join(conversation_so_far)))
                elif re.fullmatch(r"clear([ ]+the|[ ]+our){0,1}[ ]+conversation history",
                                  system_message.casefold()):
                    if not transient:
                        conversation_so_far = []
                        output = "Conversation history cleared."
                        logger.info(output)
                        print(output)
                    else:
                        print("Already in transient mode.")
                elif re.fullmatch(r"(turn[ ]+)*transient mode on", system_message.casefold()):
                    if not transient:
                        conversation_so_far = []
                        transient = True
                        output = "Transient mode is now on"
                        logger.info(output)
                        print(output)
                    else:
                        print("Already in transient mode.")
                elif re.fullmatch(r"(turn[ ]+)*transient mode off", system_message.casefold()):
                    if transient:
                        transient = False
                        output = "Transient mode is now off"
                        logger.info(output)
                        print(output)
                    else:
                        print("Transient mode is already off.")
                else:
                    output = (
                        f"Unrecognized system command: '{system_message}'. The recognized "
                        f"system commands are:\n{recognized_instructions}"
                    )
                    logger.warning(output)
                    print(output)
                continue

        # If the message is not a system message, we send it to the LLM:
        print(f"\n[{model} is thinking about it ...]")
        logger.info(f"Sending message to {model} (the full log will be recorded later).")
        response = llm.invoke([
            SystemMessage(generate_context_message(conversation_so_far)),
            HumanMessage(message),
        ]).content.strip("'").strip('"')
        logger.info(f"Received response from {model} (the full log will be recorded later).")
        print(response)
        if not transient:
            conversation_so_far.append(f"*Human*: {message}\n*AI*: {response}")
        print("\n[What would you like to say now?]")

    conversation_log = '\n'.join(conversation_so_far)
    if conversation_log:
        logger.info(f"Conversation log:\n{conversation_log}")
    else:
        logger.info("No conversation to log.")
