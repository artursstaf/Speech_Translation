import argparse
from pathlib import Path
import random

from tqdm import tqdm

from DataFiltering.first_cleaning import remove_punctuation

LEXICON_FREQ_THRESHOLD = 50


class Node:

    def __init__(self, value):
        self.__children = dict()
        self.is_terminating = False
        self.value = value
        self.frequency = 1

    def add_child(self, value):
        self.__children[value] = Node(value)

    def contains(self, value):
        return value in self.__children.keys()

    def get_child(self, value):
        return self.__children[value]

    def __repr__(self):
        child_values = []
        for node in self.__children:
            child_values.append(node.value)
        return f"{self.value}: {child_values}"


def generate_split_merge(source, target, result_source, result_target, dict_source=None, **kwargs):
    with open(source, 'r', encoding='utf-8') as source, \
            open(target, 'r', encoding='utf-8') as target, \
            open(result_source, 'w', encoding='utf-8') as result_source, \
            open(result_target, 'w', encoding='utf-8') as result_target:

        if dict_source is not None:
            with open(dict_source, 'r', encoding='utf-8') as dict_source:
                dict_source = dict_source.readlines()
        else:
            dict_source = source.readlines()

        source = source.readlines()
        target = target.readlines()

        tree = build_lexicon_tree(dict_source)
        splits = generate_splits(source, tree)
        merges = generate_merges(source, tree)

        random.shuffle(splits)
        random.shuffle(merges)

        noised_src = source[:]
        is_noised = [False] * len(noised_src)

        def try_apply_noise(noise):
            i, src = noise
            if not is_noised[i]:
                is_noised[i] = True
                noised_src[i] = src

        for noise in merges:
            try_apply_noise(noise)

        for noise in splits:
            try_apply_noise(noise)

        print(f"Total clean: {sum(int(not i) for i in is_noised)}, " +
              f"Total noised: {sum(int(i) for i in is_noised)}, Total: {len(noised_src)}")

        only_noised_sentences_src = [remove_punctuation(src_line) for src_line, noised in zip(noised_src, is_noised) if noised]
        only_noised_sentences_trg = [remove_punctuation(trg_line) for trg_line, noised in zip(target, is_noised) if noised]

        result_source.writelines(only_noised_sentences_src)
        result_target.writelines(only_noised_sentences_trg)


def build_lexicon_tree(sentences):
    root = Node('root')

    print("Building tree: ")
    for sentence in tqdm(sentences):
        for word in sentence.strip().split():
            current_node = root
            for char in word.strip():
                if not current_node.contains(char):
                    current_node.add_child(char)
                current_node = current_node.get_child(char)
            if len(word) > 1:
                current_node.is_terminating = True
                current_node.frequency += 1
    return root


def generate_splits(source, lexicon_tree):
    result = []

    count_per_sentence = []
    print("Generating splits: ")
    for sent_ind, sentence in enumerate(tqdm(source)):
        sentence = sentence.strip().split()
        count_splits = 0
        word_split_points = []

        for word_ind, word in enumerate(sentence):
            current_node = lexicon_tree
            # Find possible split points
            split_points = []
            for char_ind, char in enumerate(word):
                if not current_node.contains(char):
                    break
                current_node = current_node.get_child(char)

                if current_node.is_terminating \
                        and len(word) > char_ind + 1 \
                        and word_in_lexicon(lexicon_tree, word[char_ind + 1:]):
                    split_points.append(char_ind)

            if len(split_points) > 0:
                word_split_points.append((word_ind, word, split_points))

        # Choose split point and insert splits
        for word_ind, word, split_points in word_split_points:
            if random.random() <= 1 / len(word_split_points):
                split_index = random.choice(split_points)
                part1, part2 = (word[:split_index + 1], word[split_index + 1:])

                sentence[word_ind] = f"{part1} {part2}"
                result.append((sent_ind, " ".join(sentence) + '\n'))
                count_splits += 1

        count_per_sentence.append(count_splits)
    print(f"Splits: {len(result)}")
    print(f"Avg splits per sentence {sum(count_per_sentence) / len(count_per_sentence)}")
    return result


def generate_merges(source, lexicon_tree):
    print("Generating merges: ")
    result = []
    sentence_merges_count = []
    for sent_ind, sentence in enumerate(tqdm(source)):
        count_merges = 0
        sentence = sentence.strip().split()
        if len(sentence) > 1:
            possible_merges = []
            for word_ind, (word1, word2) in enumerate(zip(sentence, sentence[1:])):
                if word_in_lexicon(lexicon_tree, word1 + word2):
                    possible_merges.append((word_ind, word1 + word2))

            for word_ind, merged_word in possible_merges:
                if random.random() <= 1 / len(possible_merges):
                    sentence[word_ind] = merged_word
                    sentence[word_ind + 1] = ''
                    result.append((sent_ind, ' '.join(sentence) + '\n'))
                    count_merges += 1

        sentence_merges_count.append(count_merges)
    print(f"Merges: {len(result)}")
    print(f"Avg merges per sentences {sum(sentence_merges_count) / len(sentence_merges_count)}")
    return result


def word_in_lexicon(lexicon_tree, word):
    current_node = lexicon_tree
    for char in word:
        if not current_node.contains(char):
            return False
        current_node = current_node.get_child(char)

    if current_node.is_terminating and current_node.frequency >= LEXICON_FREQ_THRESHOLD:
        return True
    else:
        return False


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", required=True)
    parser.add_argument("--target", required=True)
    parser.add_argument("--dict_source")
    parser.add_argument("--result_source", required=True)
    parser.add_argument("--result_target", required=True)

    args = parser.parse_args()
    if not args.dict_source:
        dict_source = args.source
    else:
        dict_source = args.dict_source
    generate_split_merge(Path(args.source), Path(args.target), Path(args.result_source), Path(args.result_target), Path(dict_source))


if __name__ == "__main__":
    main()
