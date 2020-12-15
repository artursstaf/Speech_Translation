### First step: Identify size difference in terms of sentences between clean and asr 
### and remove punctuations
import argparse
import string
import sys
from pathlib import Path
import re

punct_translation = str.maketrans('', '', string.punctuation)


def remove_punctuation(line):
    line = line.lower().translate(punct_translation)
    return re.sub(' +', ' ', line).strip() + '\n'


def first_cleaning(source, source_asr, result_source, result_source_asr, **kwargs):
    with open(source, 'r', encoding='utf-8') as source, \
            open(source_asr, 'r', encoding='utf-8') as source_asr, \
            open(result_source, 'w', encoding='utf-8') as result_source, \
            open(result_source_asr, 'w', encoding='utf-8') as result_source_asr:

        source = source.readlines()
        source_asr = source_asr.readlines()

        # Size comparison to check if files contain the same number of sentences
        print("Size of source " + str(len(source)) + " sentences")
        print("Size of source asr: " + str(len(source_asr)) + " sentences")

        # Delta: difference of size between files, it should be 0 (sentences aligned)
        delta_sent = len(source) - len(source_asr)
        print("Number of sentences deleted in ASR file: " + str(delta_sent) + " sentences")

        # Punctuation removal: using string.punctuation list
        clean_wo_punct = []
        for element in source:
            clean_wo_punct.append(remove_punctuation(element))

        clean_asr_wo_punct = []
        for element in source_asr:
            clean_asr_wo_punct.append(remove_punctuation(re.sub(re.escape(r'<unk>'), '', element)))

        for src, src_asr in zip(clean_wo_punct, clean_asr_wo_punct):
            result_source.write(src)
            result_source_asr.write(src_asr)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", required=True)
    parser.add_argument("--source_asr", required=True)
    parser.add_argument("--result_source", required=True)
    parser.add_argument("--result_source_asr", required=True)
    parser.add_argument("--result_target", required=True)

    args = parser.parse_args()
    first_cleaning(Path(args.source), Path(args.source_asr), Path(args.result_source), Path(args.result_source_asr))


if __name__ == "__main__":
    main()
