import argparse
import re
from pathlib import Path
import sys
from tqdm import tqdm
import json


def analyse_noise_pair(orig_suffix, asr_suffix, diff_lines, pos_lines):
    print(f"Analyzing {orig_suffix}_{asr_suffix} pair")

    list_clean = []
    list_POS_clean = []
    list_POS_clean_complete = []
    sent_index = []

    counter = 0
    count_suf_clean = 0
    count_suf_asr = 0
    for sentence_diff, sentence_POS_clean in tqdm(zip(diff_lines, pos_lines)):
        token = sentence_diff.split(" ")
        nb_tokens = len(sentence_diff.split(" "))
        sentence_POS_clean = sentence_POS_clean.split(" ")

        j = 0
        while j < nb_tokens:
            count_plus = 0
            count_minus = 0
            count_char = 0
            count_space = 0
            if re.search('[a-z]*', token[j]):
                for char in token[j]:
                    if char == '+':
                        count_plus += 1
                    if char == '-':
                        count_minus += 1
                    if char != '-' and char != '+':
                        count_char += 1
                    if char == 'S':
                        count_space += 1
            if count_plus != 0 or count_minus != 0:
                if count_char > count_plus and count_char > count_minus and count_space == 0:
                    a = re.search("\+", token[j])
                    b = re.search("-", token[j])
                    suf_clean = ''
                    suf_asr = ''
                    for k in range(len(token[j]) - 1):
                        if a and b:
                            if (token[j][k] != '-'
                                    and token[j][k] != '+'
                                    and token[j][k - 1] != '-'
                                    and token[j][k - 1] != '+'):
                                suf_asr = suf_asr + token[j][k]
                                suf_clean = suf_clean + token[j][k]
                            if token[j][k] == '-':
                                suf_clean = suf_clean + token[j][k + 1]
                            if token[j][k] == '+':
                                suf_asr = suf_asr + token[j][k + 1]
                    if suf_clean.endswith(orig_suffix) and suf_asr.endswith(asr_suffix):
                        sent_index.append(counter)
                        suf_ver_clean = re.sub(f"{orig_suffix}$", "", suf_clean)
                        suf_ver_asr = re.sub(f"{asr_suffix}$", "", suf_asr)
                        if suf_ver_clean == suf_ver_asr:
                            count_suf_clean += 1
                            count_suf_asr += 1
                            for word in sentence_POS_clean:
                                word = word.split("|")
                                if suf_clean in word[0]:
                                    list_clean.append(suf_clean)
                                    list_POS_clean_complete.append(word[2].strip("\n"))
                                    word2 = word[2].split("-")
                                    list_POS_clean.append(word2[0])
                                    break
            j += 1
        counter += 1

    list_POS_clean_complete = set(list_POS_clean_complete)

    return list_POS_clean_complete


def pos_noise_analysis(source_pos, result_model, workdir, **kwargs):
    with open(source_pos, 'r', encoding='utf-8') as source_pos, \
            open(workdir / 'diff_source_and_asr', 'r', encoding='utf-8') as diff_file, \
            open(workdir / 'suffix_pair_count', 'r', encoding='utf-8') as suffix_pair_count, \
            open(result_model, 'w', encoding='utf-8') as result_file:
        diff_file = diff_file.readlines()
        POS_clean = source_pos.readlines()

        results = {}

        for entry in suffix_pair_count.readlines():
            entry = entry.split()
            source_suffix, asr_suffix, _, percentage = entry

            pos_analysis_result = analyse_noise_pair(source_suffix, asr_suffix, diff_file, POS_clean)
            results[f"{source_suffix}_{asr_suffix}"] = [percentage, list(pos_analysis_result)]

        result_file.write(json.dumps(results, indent=4))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source_pos", required=True)
    parser.add_argument("--workdir", required=True)
    parser.add_argument("--result_model", required=True)

    args = parser.parse_args()
    pos_noise_analysis(Path(args.source_pos), Path(args.result_model), Path(args.workdir), )


if __name__ == "__main__":
    main()
