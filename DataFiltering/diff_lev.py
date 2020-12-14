# Comparison of sentences in clean and asr after first cleaning in terms of Levenshtein distance
import argparse
from collections import Counter
from difflib import SequenceMatcher
import sys
from pathlib import Path

import tqdm

from similarity.normalized_levenshtein import NormalizedLevenshtein


# Definition of function to calculate Levenshtein between 2 sentences
def similar(a, b):
    return SequenceMatcher(None, a, b).ratio()


def diff_lev(source, source_asr, target, source_pos, result_source, result_source_asr, result_target, result_source_pos, workdir, **kwargs):
    with open(source, 'r', encoding='utf-8') as source, \
            open(source_asr, 'r', encoding='utf-8') as source_asr, \
            open(source_pos, 'r', encoding='utf-8') as source_pos, \
            open(target, 'r', encoding='utf-8') as target, \
            open(result_source, 'w', encoding='utf-8') as result_source, \
            open(result_source_asr, 'w', encoding='utf-8') as result_source_asr, \
            open(result_source_pos, 'w', encoding='utf-8') as result_source_pos, \
            open(result_target, 'w', encoding='utf-8') as result_target, \
            open(workdir / 'distances.txt', 'w', encoding='utf-8') as distances:

        source = source.readlines()
        source_asr = source_asr.readlines()
        target = target.readlines()
        source_pos = source_pos.readlines()

        # different types to classify the sentences
        counter = Counter()

        normalized_levenshtein = NormalizedLevenshtein()
        norm_dist = []

        # Loop to analyze each pair of sentences and count the number of occurrences of each type
        for source_sent, source_asr_sent in tqdm.tqdm(zip(source, source_asr)):
            ratio = normalized_levenshtein.similarity(source_sent, source_asr_sent)
            norm_dist.append(ratio)
            if ratio == 1:
                counter["equal"] += 1
            if ratio > 0.9:
                counter["close"] += 1
            if 0.9 >= ratio > 0.7:
                counter["medium"] += 1
            if 0.7 >= ratio > 0.5:
                counter["low"] += 1
            if 0.5 >= ratio:
                counter["different"] += 1

        # Write the results of the comparisons in output file
        for dist in norm_dist:
            distances.write(f"{dist}\n")

        # print Statistics
        print(f"Equal count:{counter['equal']}, ratio: {counter['equal'] / len(source)}", file=sys.stderr)
        print(f"{counter['close']} {counter['close'] / len(source)}", file=sys.stderr)
        print(f"{counter['medium']} {counter['medium'] / len(source)}", file=sys.stderr)
        print(f"{counter['low']} {counter['low'] / len(source)}", file=sys.stderr)
        print(f"{counter['different']} {counter['different'] / len(source)}", file=sys.stderr)

        # Loop to identify similar sentences and write in output files
        # Counting sentences with same number of tokens comparing clean and asr
        for ratio, source_sent, source_asr_sent, target_sent, source_pos_sent in tqdm.tqdm(zip(norm_dist, source, source_asr, target, source_pos)):
            if float(ratio) >= 0.9:
                result_source.write(source_sent)
                result_source_asr.write(source_asr_sent)
                result_target.write(target_sent)
                result_source_pos.write(source_pos_sent)
                counter["after_filter"] += 1
                if len(source_sent.split(" ")) == len(source_asr_sent.split(" ")):
                    counter["equal_nb_tokens"] += 1

        print(f"Sentences after cleaning {counter['after_filter']}", file=sys.stderr)
        print(f"Sentences with equal number of tokens: {counter['equal_nb_tokens']}", file=sys.stderr)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", required=True)
    parser.add_argument("--source_asr", required=True)
    parser.add_argument("--target", required=True)
    parser.add_argument("--source_pos", required=True)
    parser.add_argument("--result_source", required=True)
    parser.add_argument("--result_source_asr", required=True)
    parser.add_argument("--result_target", required=True)
    parser.add_argument("--result_source_pos", required=True)
    parser.add_argument("--workdir", required=True)

    args = parser.parse_args()
    diff_lev(Path(args.source), Path(args.source_asr), Path(args.target), Path(args.source_pos), Path(args.result_source),
             Path(args.result_source_asr), Path(args.result_target), Path(args.result_source_pos), Path(args.workdir))


if __name__ == "__main__":
    main()
