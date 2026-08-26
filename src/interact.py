import logging
import random
import csv
import numpy
import os
import sys
import traceback

from argparse import ArgumentParser
from pprint import pformat

from analyze import analyze_survey, analyze_variations
from direct import directly_interact
from vary import generate_variations
from global_vars import SUPPORTED_MODELS, \
    DEFAULT_NUM_PARTICIPANTS, DEFAULT_MEAN, DEFAULT_STD_DEV, \
    DEFAULT_MEDIATOR_LLM_MODEL, DEFAULT_MEDIATOR_LLM_TEMPERATURE, \
    DEFAULT_REPHRASE_RATIO, DEFAULT_SLEEP, \
    DEFAULT_SURVEY_LOGFILE_PREFIX, DEFAULT_VARIATIONS_LOGFILE_PREFIX, \
    DEFAULT_INTERACT_LOGFILE_PREFIX, DEFAULT_CUSTOM_LOGFILE_PREFIX, \
    DEFAULT_ANALYZE_VARIATIONS_LOGFILE_PREFIX, DEFAULT_ANALYZE_SURVEY_LOGFILE_PREFIX, \
    THESES
from participant import conduct_survey


# TODO: Update ollama libraries.

logger = logging.getLogger(__name__)


def handle_survey_args(args):
    """
    Handles the arguments of the conduct-survey subcommand.
    """
    # Do some sanity checks on some of the arguments:
    if args["participants"] < 0:
        raise Exception("Number of participants must not be negative.")

    if args["sleep"] < 0:
        raise Exception("Sleep time must not be negative.")

    if args["rephrase_ratio"] < 0 or args["rephrase_ratio"] > 1:
        raise Exception("Rephrase ratio must be a number in between zero and one.")

    if args["mediator_type"] == "llm" and args["participant_model"] == args["llm_mediator_model"]:
        raise Exception("The participant model and mediator model cannot be the same.")

    csv_filename = args["OUTPUT"]
    csv_dir = os.path.dirname(csv_filename) or "."
    if os.path.exists(csv_filename):
        raise Exception(f"The file '{csv_filename}' already exists.")
    if not os.path.isdir(csv_dir) or not os.access(csv_dir, os.W_OK):
        raise Exception(f"The file '{csv_filename}' is not writable.")

    # Get the messages:
    messages = list(THESES.keys())

    # Conduct the survey:
    logger.info(
        f"Conducting a survey with {args['participants']} participants, using "
        f"params: {pformat(args)}"
    )
    response_distribution = conduct_survey(messages, args)

    # Write the results:
    if not response_distribution:
        prefix = "Nothing to write"
        if args["participants"] == 0:
            print(f"{prefix}, which is unsurprising since you specified zero participants")
            sys.exit(0)
        else:
            raise Exception(f"{prefix}")

    logger.info(f"Writing responses to {csv_filename}")
    with open(csv_filename, 'w') as csvfile:
        writer = None
        # Flatten the response dictionary into rows that are then written to the file:
        for message_number, message_stats in response_distribution.items():
            for rephrased_message, rephrased_message_stats in message_stats.items():
                for participant_model, participant_model_stats in rephrased_message_stats.items():
                    for participant_temperature, participant_temperature_stats in \
                            participant_model_stats.items():
                        row = {
                            "message_number": message_number,
                            "rephrased_message": rephrased_message,
                            "participant_model": participant_model,
                            "participant_temperature": participant_temperature,
                            "hard_agree": participant_temperature_stats["hard_agree"],
                            "soft_agree": participant_temperature_stats["soft_agree"],
                            "hard_disagree": participant_temperature_stats["hard_disagree"],
                            "soft_disagree": participant_temperature_stats["soft_disagree"],
                            "other": participant_temperature_stats["other"],
                            "unrecognized": participant_temperature_stats["unrecognized"],
                        }
                        if not writer:
                            writer = csv.DictWriter(csvfile, fieldnames=row)
                            writer.writeheader()
                        writer.writerow(row)


def handle_vary_args(args):
    """
    Handles the arguments of the vary subcommand.
    """
    num_variants = args["num_variants"]
    if num_variants < 0:
        raise Exception("The number of variants cannot be less than zero.")

    if args["sleep"] < 0:
        raise Exception("Sleep time must not be negative.")

    csv_filename = args["OUTPUT"]
    csv_dir = os.path.dirname(csv_filename) or "."
    if os.path.exists(csv_filename):
        raise Exception(f"The file '{csv_filename}' already exists.")
    if not os.path.isdir(csv_dir) or not os.access(csv_dir, os.W_OK):
        raise Exception(f"The file '{csv_filename}' is not writable.")

    # Get the messages:
    messages = list(THESES.keys())

    logger.info(
        f"Generating {num_variants} variants per message per model, using "
        f"params: {pformat(args)}"
    )
    generate_variations(messages, args)


def handle_analyze_survey_args(args):
    """
    Handles the arguments of the 'analyze survey' subcommand.
    """
    analyze_survey(args)


def handle_analyze_variations_args(args):
    """
    Handles the arguments of the 'analyze variations' subcommand.
    """
    infilename = args["INPUT"]
    with open(infilename, 'r') as infile:
        outdir = args["OUTPUT_DIRECTORY"]
        if not os.access(outdir, os.W_OK):
            print(f"Cannot write to directory '{outdir}' or it does not exist.", file=sys.stderr)
            sys.exit(1)
        analyze_variations(infile, outdir)


def handle_interact_args(args):
    logger.info(f"Entering interactive mode with args: {args}")
    if args.get("MODEL") not in SUPPORTED_MODELS:
        raise Exception(f"Unsupported model '{args.get('MODEL')}'")

    model = args["MODEL"]
    temperature = args["TEMPERATURE"]
    transient = args["transient"]

    try:
        directly_interact(model, temperature, transient)
    except KeyboardInterrupt:
        pass


def handle_custom_args(args):
    pass


def main(args):
    parser = ArgumentParser(
        description="Interact with LLMs from the Ollama library in various ways"
    )
    subparsers = parser.add_subparsers(
        required=True,
        help="Use --help with the subcommand name to get help specific to that command."
    )

    # The subparser for the 'conduct-survey' subcommand.
    survey_parser = subparsers.add_parser(
        "conduct-survey",
        help="Conduct a survey with N participants"
    )
    survey_parser.add_argument(
        "--participants",
        default=DEFAULT_NUM_PARTICIPANTS,
        metavar='N',
        type=int,
        help=f"The number of participants to survey (default: {DEFAULT_NUM_PARTICIPANTS})",
    )
    survey_parser.add_argument(
        "--mean",
        default=DEFAULT_MEAN,
        metavar='X',
        type=float,
        help=("The value of the mean of the normal distribution used to determine "
              f"each participant's temperature (default: {DEFAULT_MEAN})."),
    )
    survey_parser.add_argument(
        "--std-dev",
        default=DEFAULT_STD_DEV,
        metavar='X',
        type=float,
        help=("The value of the standard deviation (or 'width') of the normal distribution used "
              f"to determine each participant's temperature (default: {DEFAULT_STD_DEV})."),
    )
    survey_parser.add_argument(
        "--rephrase-ratio",
        default=DEFAULT_REPHRASE_RATIO,
        metavar='R',
        type=float,
        help=("The proportion of messages (between 0 and 1) that should be rephrased by the "
              f"mediator (default: {DEFAULT_REPHRASE_RATIO})."),
    )
    survey_parser.add_argument(
        "--participant-model",
        nargs="?",
        choices=SUPPORTED_MODELS,
        help=("The model LLM to use for every participant (default: use a random non-trivial "
              " model for every participant)."),
    )
    survey_parser.add_argument(
        "--mediator-type",
        default="llm",
        choices=["llm", "trivial"],
        help="The type of mediator to use (default: llm).",
    )
    survey_parser.add_argument(
        "--llm-mediator-model",
        nargs="?",
        choices=SUPPORTED_MODELS,
        default=DEFAULT_MEDIATOR_LLM_MODEL,
        help=("The LLM model to use as a mediator (default: "
              f"{DEFAULT_MEDIATOR_LLM_MODEL}). "
              "Only applicable to mediators of type 'llm'"),
    )
    survey_parser.add_argument(
        "--llm-mediator-temperature",
        type=float,
        default=DEFAULT_MEDIATOR_LLM_TEMPERATURE,
        help=("The temperature of the mediator (default "
              f"{DEFAULT_MEDIATOR_LLM_TEMPERATURE}). "
              "Only applicable to mediators of type 'llm'"),
    )
    survey_parser.add_argument(
        "--sleep",
        default=DEFAULT_SLEEP,
        metavar='SECONDS',
        type=int,
        help=("The number of seconds to sleep after surveying each participant "
              f" (default: {DEFAULT_SLEEP})"),
    )
    survey_parser.add_argument(
        "--random-seed",
        type=int,
        metavar='SEED',
        help="Specify a SEED for the random number generator.",
    )
    survey_parser.add_argument(
        "--logfile",
        help=f"Write logging output to LOGFILE (defaults to {DEFAULT_SURVEY_LOGFILE_PREFIX}.log)."
    )
    survey_parser.add_argument(
        "--trace",
        help="Display stack trace information when exceptions are caught.",
        action='store_true',
    )
    # TODO: Possibly use more mediator and/or participant parameters
    # (see https://markaicode.com/ollama-temperature-parameter-tuning-guide/)
    survey_parser.add_argument(
        "OUTPUT",
        help=("The filename to which the CSV data will be written"),
    )

    # The parser for the 'vary' subcommand.
    vary_parser = subparsers.add_parser("vary", help="Generate label variants")
    nontrivial_models = [model for model in SUPPORTED_MODELS if model != 'trivial']
    vary_parser.add_argument(
        "--models",
        metavar="MODEL",
        choices=SUPPORTED_MODELS,
        default=nontrivial_models,
        nargs="+",
        help=("A list of the model(s) to use for generating variations "
              "(default: all non-trivial models)"),
    )
    vary_parser.add_argument(
        "--exclude",
        metavar="EXCLUDED_MODEL",
        choices=SUPPORTED_MODELS,
        default=[],
        nargs="+",
        help=("A list of models that should not be used when generating "
              "variations. In the case of a conflict between --models and --exclude, the "
              "latter takes priority. (default: no models excluded)"),
    )
    vary_parser.add_argument(
        "--num-variants",
        default=100,
        type=int,
        help="The total number of variations of the given label to generate.",
    )
    vary_parser.add_argument(
        "--sleep",
        default=DEFAULT_SLEEP,
        metavar='SECONDS',
        type=int,
        help=("The number of seconds to sleep after generating each set of variations "
              f"(default: {DEFAULT_SLEEP} seconds)"),
    )
    vary_parser.add_argument(
        "--random-seed",
        type=int,
        metavar='SEED',
        help="Specify a SEED for the random number generator (normally only for testing).",
    )
    vary_parser.add_argument(
        "--logfile",
        help=(
            "Write logging output to LOGFILE "
            f"(defaults to '{DEFAULT_VARIATIONS_LOGFILE_PREFIX}.log')"
        )
    )
    vary_parser.add_argument(
        "--trace",
        help="Display stack trace information when exceptions are caught.",
        action='store_true',
    )
    vary_parser.add_argument(
        "OUTPUT",
        help=("The filename to which the CSV data will be written"),
    )

    # The subparser for the 'analyze' subcommand and its further subparsers:
    analyze_parser = subparsers.add_parser("analyze", help="Analyze data")
    analyze_parser.add_argument(
        "--logfile",
        help=(
            "Write logging output to LOGFILE "
            f"(defaults to '{DEFAULT_ANALYZE_VARIATIONS_LOGFILE_PREFIX}.log' or "
            f"'{DEFAULT_ANALYZE_SURVEY_LOGFILE_PREFIX}.log')"
        )
    )
    analyze_parser.add_argument(
        "--trace",
        help="Display stack trace information when exceptions are caught.",
        action='store_true',
    )
    analyze_parser.add_argument(
        "--random-seed",
        type=int,
        metavar='SEED',
        help="Specify a SEED for the random number generator (normally only for testing).",
    )
    analyze_subparsers = analyze_parser.add_subparsers(
        required=True,
        help="Use --help with the subcommand name to get help specific to that command."
    )

    # The sub-subparser for the 'analyze variations' subcommand:
    analyze_variations_parser = analyze_subparsers.add_parser(
        "variations",
        help="Analyze variations"
    )
    analyze_variations_parser.add_argument(
        "INPUT",
        help=("The filename from which variations will be read"),
    )
    analyze_variations_parser.add_argument(
        "OUTPUT_DIRECTORY",
        help=("The directory to which data will be written."),
    )

    # The sub-subparser for the 'analyze survey' subcommand:
    analyze_survey_parser = analyze_subparsers.add_parser("survey", help="Analyze survey results")
    analyze_survey_parser.add_argument(
        "INPUT",
        help=("The filename from which survey results will be read"),
    )
    analyze_survey_parser.add_argument(
        "OUTPUT",
        nargs='?',
        help=("The filename to which data will be written, or STDOUT if unspecified."),
    )

    # The subparser for the 'interact' subcommand.
    interact_parser = subparsers.add_parser("interact", help="Directly interact with an LLM")
    interact_parser.add_argument(
        "--transient",
        help="Do not keep track of the conversation but begin every question with a clean slate.",
        action='store_true',
    )
    interact_parser.add_argument(
        "--random-seed",
        type=int,
        metavar='SEED',
        help="Specify a SEED for the random number generator (normally only for testing).",
    )
    interact_parser.add_argument(
        "--logfile",
        help=(
            "Write logging output to LOGFILE "
            f"(defaults to '{DEFAULT_INTERACT_LOGFILE_PREFIX}.log')"
        )
    )
    interact_parser.add_argument(
        "--trace",
        help="Display stack trace information when exceptions are caught.",
        action='store_true',
    )
    interact_parser.add_argument(
        "MODEL",
        help="The name of the model to interact with.",
    )
    interact_parser.add_argument(
        "TEMPERATURE",
        type=float,
        help="The temperature to use.",
    )

    # The parser for the custom subcommand
    custom_parser = subparsers.add_parser(
        "custom",
        help="Run a customized sequence of interactions with an LLM."
    )
    custom_parser.add_argument(
        "--sleep",
        default=DEFAULT_SLEEP,
        metavar='SECONDS',
        type=int,
        help=("The number of seconds to sleep when resting "
              f"(default: {DEFAULT_SLEEP} seconds)"),
    )
    custom_parser.add_argument(
        "--random-seed",
        type=int,
        metavar='SEED',
        help="Specify a SEED for the random number generator (normally only for testing).",
    )
    custom_parser.add_argument(
        "--logfile",
        help=(
            "Write logging output to LOGFILE "
            f"(defaults to '{DEFAULT_CUSTOM_LOGFILE_PREFIX}.log')"
        )
    )
    custom_parser.add_argument(
        "--trace",
        help="Display stack trace information when exceptions are caught.",
        action='store_true',
    )
    custom_parser.add_argument(
        "MODEL",
        help="The name of the model to run a customized sequence of interactions with.",
    )
    custom_parser.add_argument(
        "TEMPERATURE",
        type=float,
        help="The temperature to use.",
    )

    # Associate the right functions to handle the various subcommand arguments:
    survey_parser.set_defaults(subcommand=handle_survey_args)
    vary_parser.set_defaults(subcommand=handle_vary_args)
    analyze_variations_parser.set_defaults(subcommand=handle_analyze_variations_args)
    analyze_survey_parser.set_defaults(subcommand=handle_analyze_survey_args)
    interact_parser.set_defaults(subcommand=handle_interact_args)
    custom_parser.set_defaults(subcommand=handle_custom_args)

    # Parse the arguments and extract the desired subcommand:
    args = parser.parse_args()
    args = vars(args)
    subcommand = args["subcommand"]
    del args["subcommand"]

    # Configure the logger. Possible logging levels are: NOTSET, DEBUG, INFO, WARNING, ERROR,
    # and CRITICAL (see https://docs.python.org/3/library/logging.html#logging-levels).
    if subcommand == handle_survey_args:
        logfile_prefix = DEFAULT_SURVEY_LOGFILE_PREFIX
    elif subcommand == handle_vary_args:
        logfile_prefix = DEFAULT_VARIATIONS_LOGFILE_PREFIX
    elif subcommand == handle_analyze_variations_args:
        logfile_prefix = DEFAULT_ANALYZE_VARIATIONS_LOGFILE_PREFIX
    elif subcommand == handle_analyze_survey_args:
        logfile_prefix = DEFAULT_ANALYZE_SURVEY_LOGFILE_PREFIX
    elif subcommand == handle_interact_args:
        logfile_prefix = DEFAULT_INTERACT_LOGFILE_PREFIX
    else:
        logfile_prefix = DEFAULT_CUSTOM_LOGFILE_PREFIX

    logfile = args["logfile"] or f"{logfile_prefix}.log"
    # We copy the value back to args since it will be read later and logged:
    args["logfile"] = logfile
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s %(levelname)s %(message)s',
        filename=logfile,
        filemode='w'
    )
    print(f"The log is being written to '{logfile}'.")

    # If there is a --random-seed, set it here:
    if args["random_seed"] is not None:
        random.seed(args["random_seed"])
        numpy.random.seed(args["random_seed"])

    # Finally, call the subcommand:
    try:
        subcommand(args)
    except (BrokenPipeError, KeyboardInterrupt):
        logger.critical("Aborted by user.")
        sys.exit(1)
    except Exception as exc:
        logger.critical(f"{exc}")
        if args["trace"]:
            print(traceback.format_exc(), file=sys.stderr)
        else:
            print(
                f"Error: '{exc}' (to show stack trace information use the --trace option)",
                file=sys.stderr
            )

        sys.exit(1)


if __name__ == "__main__":
    main(sys.argv)
