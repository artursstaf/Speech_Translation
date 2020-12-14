# Filtering sentences to remove main id entified errors of ASR file by using Regex
# Selected sentences written in output files "stripped"

import argparse
import re
from difflib import SequenceMatcher
import sys
from pathlib import Path

import tqdm


def asr_mistakes(source, source_asr, target, source_pos, result_source, result_source_asr, result_target, result_source_pos, **kwargs):
    with open(source, 'r', encoding='utf-8') as source, \
            open(source_asr, 'r', encoding='utf-8') as source_asr, \
            open(target, 'r', encoding='utf-8') as target, \
            open(source_pos, 'r', encoding='utf-8') as source_pos, \
            open(result_source, 'w', encoding='utf-8') as result_source, \
            open(result_source_asr, 'w', encoding='utf-8') as result_source_asr, \
            open(result_target, 'w', encoding='utf-8') as result_target, \
            open(result_source_pos, 'w', encoding='utf-8') as result_source_pos:

        source = source.readlines()
        source_asr = source_asr.readlines()
        target = target.readlines()
        source_pos = source_pos.readlines()

        # For loop containing the Regex to identify sentences not to be written in output file.
        i = 0
        for j in tqdm.tqdm(range(len(source))):
            x = re.search("[0-9]", source[j])
            y = re.search("http", source[j])
            z = re.search("^[a-z]$", source[j])
            k = re.search("^\n$", source[j])
            l = re.search("www", source[j])
            m = re.search("^[mdclxvi]+$", source[j])
            n = re.search("^link$", source[j])
            o = re.search("°", source[j])
            p = re.search(" [mdclxvi]+$", source[j])

            if not x and not y and not z and not k and not l and not m and not n and not o and not p:
                result_source.write(source[j])
                result_source_asr.write(source_asr[j])
                result_target.write(target[j])
                result_source_pos.write(source_pos[j])

            if SequenceMatcher(None, source[j], source_asr[j]).quick_ratio() < 1:
                i += 1

        print(f"Num of different sentences: {i}", file=sys.stderr)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", required=True)
    parser.add_argument("--source_asr", required=True)
    parser.add_argument("--target", required=True)
    parser.add_argument("--result_source", required=True)
    parser.add_argument("--result_source_asr", required=True)
    parser.add_argument("--result_target", required=True)
    parser.add_argument("--source_pos", required=True)
    parser.add_argument("--result_source_pos", required=True)

    args = parser.parse_args()
    asr_mistakes(Path(args.source), Path(args.source_asr), Path(args.target), Path(args.source_pos),
                 Path(args.result_source), Path(args.result_source_asr), Path(args.result_target),
                 Path(args.result_source_pos))


if __name__ == "__main__":
    main()
