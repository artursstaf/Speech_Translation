import argparse
import re
from collections import Counter
from pathlib import Path

TOP_N_MISTAKES = 25


def suffix_analysis(source_pos, result_model, workdir, **kwargs):
    with open(source_pos, 'r', encoding='utf-8') as source_pos, \
            open(workdir / 'diff_source_and_asr', 'r', encoding='utf-8') as diff_source_and_asr, \
            open(result_model, 'w', encoding='utf-8') as result_file:

        text = diff_source_and_asr.readlines()
        source_pos = source_pos.readlines()

        count_error = 0
        count_split = 0
        count_merge = 0
        count_special_split = 0
        count_special_merge = 0

        list_src = []
        list_src_pos = []
        list_asr = []

        i = 0
        while i < len(text):
            tokens = text[i].split(" ")
            sentence_pos = source_pos[i].split(" ")
            nb_tokens = len(tokens)
            j = 0
            while j < nb_tokens:
                count_plus = 0
                count_minus = 0
                count_char = 0
                count_space = 0

                if re.search(r'[a-z]*', tokens[j]):
                    for char in tokens[j]:
                        if char == '+':
                            count_plus += 1
                        if char == '-':
                            count_minus += 1
                        if char != '-' and char != '+':
                            count_char += 1
                        if char == 'S':
                            count_space += 1
                if re.search(r"^\+$", tokens[j]):
                    count_split += 1
                if re.search(r"^-$", tokens[j]):
                    count_merge += 1

                if count_plus != 0 or count_minus != 0:
                    if count_char > count_plus and count_char > count_minus and count_space == 0:
                        a = re.search(r"\+", tokens[j])
                        b = re.search(r"-", tokens[j])
                        count_error += 1
                        word_src = ''
                        word_asr = ''
                        for k in range(len(tokens[j]) - 1):
                            if a and b:
                                if tokens[j][k] != '-' \
                                        and tokens[j][k] != '+' \
                                        and tokens[j][k - 1] != '-' \
                                        and tokens[j][k - 1] != '+':
                                    word_asr = word_asr + tokens[j][k]
                                    word_src = word_src + tokens[j][k]
                                if tokens[j][k] == '-':
                                    word_src = word_src + tokens[j][k + 1]
                                if tokens[j][k] == '+':
                                    word_asr = word_asr + tokens[j][k + 1]

                        word_pos = ''
                        for word in sentence_pos:
                            word = word.split("|")
                            if word_src in word[0]:
                                word_pos = word[2].strip("\n")
                                break
                        if word_src != '' and word_asr != '' and word_pos != '':
                            list_src_pos.append(word_pos)
                            list_src.append(word_src)
                            list_asr.append(word_asr)
                if re.search(r"[a-z]\+S[a-z]", tokens[j]) and count_space == count_plus and count_minus == 0:
                    count_special_split += 1
                if re.search(r"[a-z]\-S[a-z]", tokens[j]) and count_space == count_minus and count_plus == 0:
                    count_special_merge += 1
                j += 1
            i += 1

        for i in range(len(list_src)):
            if re.search("\n", list_src[i]):
                list_src[i] = re.sub("\n", "", list_src[i])

        for i in range(len(list_src_pos)):
            if re.search("\n", list_src_pos[i]):
                list_src_pos[i] = re.sub("\n", "", list_src_pos[i])

        for i in range(len(list_asr)):
            if re.search("\n", list_asr[i]):
                list_asr[i] = re.sub("\n", "", list_asr[i])

        count_error_suffixes_in_list = 0

        def get_root(a, b):
            min_range = min(len(a), len(b))
            if min_range < 1:
                return ""

            for i in range(min_range):
                if a[i] != b[i]:
                    return a[:i]

            return ""

        result1_list = []
        for i in range(len(list_src)):
            count_suff_src = 0
            count_suff_asr = 0
            roots_src = []
            roots_asr = []

            count_suff_src += 1
            root = get_root(list_src[i], list_asr[i])
            if root != "":
                roots_src.append(root)
                count_suff_asr += 1
                roots_asr.append(root)

            if count_suff_src != 0 and count_suff_asr != 0:
                root_src = min(roots_src, key=len)
                root_asr = min(roots_asr, key=len)

                if root_src == root_asr:
                    result1_list.append(
                        re.sub(root_src, "", list_src[i])
                        + " "
                        + re.sub(root_asr, "", list_asr[i])
                        + " "
                        + list_src_pos[i]
                        + '\n')
                    count_error_suffixes_in_list += 1

        print(f"Suffix errors: {count_error_suffixes_in_list}")
        print(f"Total erros: {count_error}")
        print(f"Splits: {count_split}")
        print(f"Merges: {count_merge}")

        a = Counter(map(lambda x: x.strip(), result1_list))
        # Take top n results
        a = Counter(dict(a.most_common()[:TOP_N_MISTAKES]))

        # Write result
        total = sum(a.values())
        total_perc = 0
        for k, v in a.most_common():
            total_perc += (v / total) * 100
            result_file.write("{} {} {:.2f}%\n".format(k, v, (v / total) * 100))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--workdir", required=True)
    parser.add_argument("--source_pos", required=True)
    parser.add_argument("--result_model", required=True)

    args = parser.parse_args()
    suffix_analysis(Path(args.source_pos), Path(args.result_model), Path(args.workdir), )


if __name__ == "__main__":
    main()
