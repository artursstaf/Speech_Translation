# Comparison of clean and asr tokenized and true cased using difflib to generate comparison file that will be used in further analysis
import argparse
import codecs
from difflib import Differ
import re
from pathlib import Path

import tqdm


def difflib_comparison(source, source_asr, workdir, **kwargs):
    with open(source, 'r', encoding='utf-8') as source, \
            open(source_asr, 'r', encoding='utf-8') as source_asr, \
            open(workdir / 'diff_source_and_asr', 'w', encoding='utf-8') as result:
        clean = source.readlines()
        clean_asr = source_asr.readlines()

        # Define comparison function and apply it generating output data
        d = Differ()

        i = 0
        for sent_nb in tqdm.tqdm(range(len(clean))):
            diff_output = d.compare(clean[sent_nb], clean_asr[sent_nb])
            diff = "".join(diff_output).strip() + '\n'

            corr = re.sub(r'     ', 'X', diff)
            corr1 = re.sub(r'    ', 'S', corr)
            corr15 = re.sub(r'   ', 'X', corr1)
            corr2 = re.sub(r' ', '', corr15)
            corr3 = re.sub(r'X', ' ', corr2)
            corr4 = re.sub(r'--', ' - -', corr3)
            corr5 = re.sub(r'\+\+', ' + +', corr4)

            result.write(corr5)
            i += 1


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", required=True)
    parser.add_argument("--source_asr", required=True)
    parser.add_argument("--workdir", required=True)

    args = parser.parse_args()
    difflib_comparison(Path(args.source), Path(args.source_asr), Path(args.workdir))


if __name__ == "__main__":
    main()
