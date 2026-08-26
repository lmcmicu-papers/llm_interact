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

import csv
import logging
import numpy
import re

from collections import OrderedDict
from global_vars import THESES


logger = logging.getLogger(__name__)

is_numbered_re = re.compile(r"^\d+[\.:]? ")
to_hyphen_re = re.compile(r"(—|–)")
to_single_space_re = re.compile(r"\s\s+")
get_words_re = re.compile(r"\b[\w\.-_]+\b")

stopword_list = [
    "a",
    "all",
    "an",
    "and",
    "any",
    "are",
    "as",
    "at",
    "be",
    "because",
    "but",
    "by",
    "for",
    "from",
    "in",
    "into",
    "is",
    "it",
    "more",
    "not",
    "of",
    "on",
    "one",
    "only",
    "or",
    "over",
    "rather",
    "since",
    "some",
    "such",
    "than",
    "that",
    "the",
    "these",
    "this",
    "those",
    "to",
    "under",
    "while",
    "with",
    "without",
]


def get_ngrams(sentence):
    """
    TODO: Add docstring.
    """
    def words_to_ngrams(words, n, sep=" "):
        return [sep.join(words[i:i + n]) for i in range(len(words) - n + 1)]

    all_words = [word.casefold() for word in get_words_re.findall(sentence)]

    unigrams = [word for word in all_words if word not in stopword_list]
    bigrams = words_to_ngrams(unigrams, 2)
    trigrams = words_to_ngrams(unigrams, 3)

    ngrams = unigrams + bigrams + trigrams
    return set(ngrams)


def generate_benchmarks():
    benchmark_content = {}
    for thesis, variations in THESES.items():
        benchmark_content[thesis] = {"best": variations["best"]}
        for model in ["claude", "gpt", "gemini"]:
            text = variations[model]
            ngrams = get_ngrams(text)
            benchmark_content[thesis][model] = ngrams
    return benchmark_content


def normalize(token):
    """
    TODO: Add docstring.
    """
    token = token.strip().casefold()
    token = to_hyphen_re.sub('-', token)
    token = to_single_space_re.sub(' ', token)
    return token


def valid(variant, label):
    """
    Variants that do not pass this test are not candidates to receive a score. They are simply
    ignored.
    """

    # TODO: Add some checks here.

    # If we make it to here then everything is ok.
    return True


def has_drift(variant_ngrams, label_ngrams):
    # TODO: Calculate something here.
    return False


def score_variant(variant, label, benchmarks):
    score = 0
    label_ngrams = get_ngrams(label)

    # Remove any of the variant's ngrams that also appear in the label's:
    variant_ngrams = [ngram for ngram in get_ngrams(variant) if ngram not in label_ngrams]

    # Record drift:
    drift = has_drift(variant_ngrams, label_ngrams)

    # The score is calculated based on the Jaccard index of the variant with respect to the
    # set of benchmark variations, using the highest of these as the variant's score.
    max_jacard_index = {}
    for benchmark_model in ["claude", "gpt", "gemini"]:
        # Calculate the Jaccard index of the variant with respect to this benchmark model's
        # variation of the label.
        benchmark_ngrams = benchmarks[label][benchmark_model]
        intersect_cardinality = len(benchmark_ngrams.intersection(variant_ngrams))
        union_cardinality = len(benchmark_ngrams.union(variant_ngrams))
        jaccard_index = intersect_cardinality / union_cardinality

        # We want the maximum Jaccard index across all benchmark models:
        if "index" not in max_jacard_index:
            max_jacard_index["benchmark_model"] = benchmark_model
            max_jacard_index["index"] = jaccard_index
        elif jaccard_index > max_jacard_index["index"]:
            max_jacard_index["benchmark_model"] = benchmark_model
            max_jacard_index["index"] = jaccard_index

    # We then apply a penalty if the variant manifests drift:
    score = max_jacard_index["index"] if not drift else (max_jacard_index["index"] / 2)
    return score


def compute_scores(infile):
    csv_reader = csv.DictReader(infile)
    benchmarks = generate_benchmarks()
    scores = {}
    invalid_rows = {}
    for row in csv_reader:
        model = row["model"].casefold()
        label = row["label"].casefold()
        variant = row["variant"].casefold()
        logger.debug(f"Got model: {model}, label: {label}, variant: {variant}")

        # Make sure we have the required entries in the dictionary:
        if model not in scores:
            scores[model] = {}
        if label not in scores[model]:
            scores[model][label] = {}
            scores[model][label]["total"] = 1
            scores[model][label]["total_invalid"] = 0
            scores[model][label]["total_nonumber"] = 0
        else:
            scores[model][label]["total"] += 1

        variant = normalize(variant)
        if not valid(variant, label):
            logger.info(
                f"Skipping row. Got invalid variant for model {model} and {label}: '{variant}'."
            )
            scores[model][label]["total_invalid"] += 1
            if model not in invalid_rows:
                invalid_rows[model] = {}
            if label not in invalid_rows[model]:
                invalid_rows[model][label] = set()
            invalid_rows[model][label].add(variant)
            continue

        # Remove the number from the start of the variant and extract all of the ngrams except
        # those that appear in the stopword list.
        variant_short = is_numbered_re.sub("", variant)
        if variant_short == variant:
            scores[model][label]["total_nonumber"] += 1
            logger.info(f"Got a valid variant without a number: {variant}")
        variant = variant_short

        score = score_variant(variant, label, benchmarks)
        logger.info(
            f"Model {model} got score: {score} for its variant '{variant}' of label '{label}'"
        )
        scores[model][label][variant] = score
    return scores, invalid_rows


def decorate(scores):
    variant_data = []
    summary_data = {}
    for model, model_scores in scores.items():
        for label, label_scores in model_scores.items():
            # Record the summary data:
            if model not in summary_data:
                summary_data[model] = {}
            if label not in summary_data[model]:
                summary_data[model][label] = {}

            # Record the meta label data and then remove it since it would interfere with
            # the sorting step.
            summary_data[model][label]["total"] = label_scores["total"]
            summary_data[model][label]["total_invalid"] = label_scores["total_invalid"]
            summary_data[model][label]["total_nonumber"] = label_scores["total_nonumber"]
            del label_scores["total"]
            del label_scores["total_invalid"]
            del label_scores["total_nonumber"]

            # To get the best variant and model, sort the data in descending order of score,
            # then take the first row.
            label_score_items = list(label_scores.items())
            label_score_items.sort(key=lambda kv_pair: kv_pair[1], reverse=True)
            try:
                best_variant, best_score = next(iter(label_score_items))
            except StopIteration:
                best_variant = ""
                best_score = 0

            # Calculate the mean:
            if len(label_score_items) == 0:
                logger.warning(f"Model {model} produced no valid variants of label '{label}'")
                mean_score = 0
            else:
                mean_score = numpy.mean([v for (k, v) in label_score_items])

            # Record the summary data:
            summary_data[model][label]["mean_score"] = mean_score
            summary_data[model][label]["best_score"] = best_score
            summary_data[model][label]["best_variant"] = best_variant

            # Record the detailed data:
            label_scores = OrderedDict(label_score_items)
            for variant in label_scores:
                score = label_scores[variant]
                variant_data.append([model, label, variant, score])
    return {
        "summary_data": summary_data,
        "variant_data": variant_data,
    }


def write_results(scores, invalid_rows, outdir):
    # First add some summary information to the data:
    scores = decorate(scores)

    # Then write everything to the CSV, beginning with the summary information:
    prefix = "analyze_variations"
    with open(f"{outdir}/{prefix}_summary.csv", "w") as outfile:
        csv_writer = csv.writer(outfile)
        csv_writer.writerow(
            ["model", "label", "total", "invalid", "nonumber", "best_variant", "best_score",
             "mean_score"]
        )
        for model, model_data in scores["summary_data"].items():
            for label, label_data in model_data.items():
                csv_writer.writerow([
                    model,
                    label,
                    label_data["total"],
                    label_data["total_invalid"],
                    label_data["total_nonumber"],
                    label_data["best_variant"],
                    label_data["best_score"],
                    label_data["mean_score"],
                ])

    # Next write the detailed data:
    with open(f"{outdir}/{prefix}_detailed.csv", "w") as outfile:
        csv_writer = csv.writer(outfile)
        csv_writer.writerow(["model", "label", "variant", "score"])
        for row in scores["variant_data"]:
            csv_writer.writerow(row)

    # Finally write out the invalid rows:
    with open(f"{outdir}/{prefix}_invalid.csv", "w") as outfile:
        csv_writer = csv.writer(outfile)
        csv_writer.writerow(["model", "label", "invalid_variant"])
        for (model, label_data) in invalid_rows.items():
            for (label, variant_data) in label_data.items():
                for variant in variant_data:
                    csv_writer.writerow([model, label, variant])


def analyze_variations(infile, outdir):
    """
    TODO: Add docstring.
    """
    scores, invalid_rows = compute_scores(infile)
    write_results(scores, invalid_rows, outdir)


def analyze_survey(args):
    """
    TODO: Add docstring.
    """
    print(f"SURVEY ARGS: {args}")
