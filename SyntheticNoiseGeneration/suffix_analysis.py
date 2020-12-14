import argparse
import codecs
import re
from collections import Counter
from difflib import SequenceMatcher
from pathlib import Path

TOP_N_MISTAKES = 25

def suffix_analysis(workdir, **kwargs):
    with open(workdir / 'diff_source_and_asr', 'r', encoding='utf-8') as diff_source_and_asr, \
            open(workdir / 'suffix_pair_count', 'w', encoding='utf-8') as count_result:

        text = diff_source_and_asr.readlines()

        count_error = 0
        count_split = 0
        count_merge = 0
        count_special_split = 0
        count_special_merge = 0

        list_clean = []
        list_asr = []

        print("Starting suffix analysis")

        i = 0
        while i < len(text):
            token = text[i].split(" ")
            nb_tokens = len(text[i].split(" "))
            j = 0
            while j < nb_tokens:
                count_plus = 0
                count_minus = 0
                count_char = 0
                count_space = 0
                if re.search(r'[a-z]*', token[j]):
                    for char in token[j]:
                        if char == '+':
                            count_plus += 1
                        if char == '-':
                            count_minus += 1
                        if char != '-' and char != '+':
                            count_char += 1
                        if char == 'S':
                            count_space += 1
                if re.search(r"^\+$", token[j]):
                    count_split += 1
                if re.search(r"^-$", token[j]):
                    count_merge += 1
                if count_plus != 0 or count_minus != 0:
                    if count_char > count_plus and count_char > count_minus and count_space == 0:
                        a = re.search(r"\+", token[j])
                        b = re.search(r"-", token[j])
                        count_error += 1
                        suf_clean = ''
                        suf_asr = ''
                        for k in range(len(token[j]) - 1):
                            if a and b:
                                x = token[j][k]
                                if token[j][k] != '-' \
                                        and token[j][k] != '+' \
                                        and token[j][k - 1] != '-' \
                                        and token[j][k - 1] != '+':
                                    suf_asr = suf_asr + token[j][k]
                                    suf_clean = suf_clean + token[j][k]
                                if token[j][k] == '-':
                                    suf_clean = suf_clean + token[j][k + 1]
                                if token[j][k] == '+':
                                    suf_asr = suf_asr + token[j][k + 1]
                        list_clean.append(suf_clean)
                        list_asr.append(suf_asr)
                if re.search(r"[a-z]\+S[a-z]", token[j]) and count_space == count_plus and count_minus == 0:
                    count_special_split += 1
                if re.search(r"[a-z]\-S[a-z]", token[j]) and count_space == count_minus and count_plus == 0:
                    count_special_merge += 1
                j += 1
            i += 1

        for i in range(len(list_clean)):
            if re.search("\n", list_clean[i]):
                list_clean[i] = re.sub("\n", "", list_clean[i])

        for i in range(len(list_asr)):
            if re.search("\n", list_asr[i]):
                list_asr[i] = re.sub("\n", "", list_asr[i])

        count_error_suffixes_in_list = 0
        words = 0

        def get_root(a, b):
            min_range = min(len(a), len(b))
            if min_range < 1:
                return ""

            for i in range(min_range):
                if a[i] != b[i]:
                    return a[:i]

            return ""

        result1_list = []
        for i in range(len(list_clean)):
            count_suff_clean = 0
            count_suff_asr = 0
            roots_clean = []
            roots_asr = []

            count_suff_clean += 1
            root = get_root(list_clean[i], list_asr[i])
            if root != "":
                roots_clean.append(root)
                count_suff_asr += 1
                roots_asr.append(root)

            if count_suff_clean != 0 and count_suff_asr != 0:
                root_clean = min(roots_clean, key=len)
                root_asr = min(roots_asr, key=len)

                if root_clean == root_asr:
                    # result.write(list_clean[i] + "\t"
                    #              + list_asr[i] + "\t"
                    #              + root_clean + "\t"
                    #              + re.sub(root_clean, "", list_clean[i]) + "\t"
                    #              + re.sub(root_asr, "", list_asr[i]) + "\n")

                    result1_list.append(
                        re.sub(root_clean, "", list_clean[i]) + " " + re.sub(root_asr, "", list_asr[i]) + '\n')
                    count_error_suffixes_in_list += 1

        # result1.writelines(result1_list)
        print(f"Suffix errors: {count_error_suffixes_in_list}")
        print(count_error)
        print(count_split)
        print(count_merge)
        print(count_special_split)
        print(count_special_merge)

        a = Counter(map(lambda x: x.strip(), result1_list))
        a = Counter(dict(a.most_common()[:TOP_N_MISTAKES]))

        # Write result
        total = sum(a.values())
        total_perc = 0
        for k, v in a.most_common():
            total_perc += (v/total) * 100
            count_result.write("{} {} {:.2f}%\n".format(k, v, (v / total) * 100))

        print(f"total perc {total_perc}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--workdir", required=True)

    args = parser.parse_args()
    suffix_analysis(Path(args.workdir))


if __name__ == "__main__":
    main()
