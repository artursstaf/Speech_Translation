import argparse
import random
import re
from collections import Counter
from pathlib import Path
import math
import json

from DataFiltering.first_cleaning import remove_punctuation


def add_noise(source, source_pos, target, result_source, result_target, noise_model, **kwargs):
    with open(source_pos, 'r', encoding='utf-8') as POS_clean, \
            open(source, 'r', encoding='utf-8') as clean, \
            open(target, 'r', encoding='utf-8') as target, \
            open(noise_model, 'r', encoding='utf-8') as noise_model, \
            open(result_target, 'w', encoding='utf-8') as result_target, \
            open(result_source, 'w', encoding='utf-8') as result_source:

        POS_clean = POS_clean.readlines()
        clean = clean.readlines()
        target = target.readlines()
        noise_model = json.loads(noise_model.read())
        print("Input files read")

        print("Building Dictionary")
        vocab_dic = Counter(word.strip() for line in clean for word in line.split())

        result = clean[:]
        # keep track of noised sentences
        is_noised = [False] * len(result)

        noised_sentences_for_suffix = []

        # Apply noise starting by least common
        for key, (percentage, suffix_pos) in list(noise_model.items())[::-1]:
            source_suffix, asr_suffix = key.split("_")
            target_noise_count = math.floor(len(clean) * (float(percentage.replace("%", "")) / 100))
            noised_sentences = get_noised_sentences(source_suffix, asr_suffix, clean, POS_clean, vocab_dic, suffix_pos)
            random.shuffle(noised_sentences)

            noised_sentences_for_suffix.append([target_noise_count, noised_sentences, (source_suffix, asr_suffix)])

        statistics_noised = Counter()

        # Try to insert sentences 1 by 1 for each noise type, stop when required count reached
        while True:
            no_more_sentences_left = True
            # Iterate suffix pair sets
            for i, (count, sentences, suffix_pair) in enumerate(noised_sentences_for_suffix):
                if count < 1:
                    continue

                if len(sentences) == 0:
                    continue

                no_more_sentences_left = False
                corpus_index, sentence = sentences.pop()

                if not is_noised[corpus_index]:
                    is_noised[corpus_index] = True
                    result[corpus_index] = sentence
                    noised_sentences_for_suffix[i][0] = count - 1
                    statistics_noised[suffix_pair] += 1

            if no_more_sentences_left:
                break

        print(f"Statistics:")
        total = sum(statistics_noised.values())
        for pair, count in statistics_noised.most_common():
            print(f"{pair}, count: {count}, proportion: {(count / total) * 100}")

        print(
            f"Total clean: {sum(int(not i) for i in is_noised)}, Total noised: {sum(int(i) for i in is_noised)}, Total: {len(result)}")

        only_noised_sentences_src = [remove_punctuation(src_line) for src_line, noised in zip(result, is_noised) if noised]
        only_noised_sentences_trg = [remove_punctuation(trg_line) for trg_line, noised in zip(target, is_noised) if noised]

        result_source.writelines(only_noised_sentences_src)
        result_target.writelines(only_noised_sentences_trg)


def get_noised_sentences(orig_suffix, asr_suffix, clean, POS_clean, vocabulary, suffix_pos):
    print(f"Generating noised sentences for {orig_suffix}_{asr_suffix}")
    POS_clean_tok = []
    for sentence in POS_clean:
        sentence = sentence.split()
        POS_clean_tok.append(sentence)

    sentence_clean_tok = []
    for sentence in clean:
        sentence = sentence.split()
        sentence_clean_tok.append(sentence)

    list_POS = [line.strip() for line in suffix_pos]

    list_POS = set(list_POS)
    noise_sentences = []
    nb_changes_each_sentence = []

    count_changes = 0
    count_tot = 0

    z = 0
    while z < len(clean):
        nb_changes_each_sentence.append(0)
        z += 1

    i = 0
    while i < len(clean):
        for index_tok_clean, token in enumerate(sentence_clean_tok[i]):
            if token.endswith(orig_suffix):
                if len(POS_clean_tok[i]) == len(sentence_clean_tok[i]):
                    if POS_clean_tok[i][index_tok_clean].split("|")[2] in list_POS:
                        nb_changes_each_sentence[i] = nb_changes_each_sentence[i] + 1
                else:
                    raise Exception(f"pos token count doesnt match in  {i} sentence")
        i += 1
    count_in_dic = 0
    count_out_dic = 0

    i = 0
    while i < len(clean):
        change = False
        for index_tok_clean, token in enumerate(sentence_clean_tok[i]):
            if token.endswith(orig_suffix):
                if POS_clean_tok[i][index_tok_clean].split("|")[2] in list_POS:
                    noise_tok = re.sub(f"{re.escape(orig_suffix)}$", asr_suffix, token)
                    count_tot += 1
                    rand = random.uniform(0, 1)
                    if noise_tok in vocabulary:
                        # On average 1 occurrence of  noise in sentence (can be more or less)
                        if rand <= 1 / nb_changes_each_sentence[i]:
                            count_in_dic += 1
                            noise_sentence = re.sub(re.escape(token), noise_tok, clean[i])
                            change = True
                            count_changes = count_changes + 1
                    else:
                        count_out_dic += 1
        if change:
            noise_sentences.append((i, noise_sentence))
        i += 1

    print(f"{len(noise_sentences)} noised_sentences retrieved for {orig_suffix}_{asr_suffix}")
    return noise_sentences


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", required=True)
    parser.add_argument("--source_pos", required=True)
    parser.add_argument("--target", required=True)
    parser.add_argument("--result_source", required=True)
    parser.add_argument("--result_target", required=True)
    parser.add_argument("--noise_model", required=True)

    args = parser.parse_args()
    add_noise(Path(args.source), Path(args.source_pos), Path(args.target), Path(args.result_source),
              Path(args.result_target), Path(args.noise_model))


if __name__ == "__main__":
    main()
