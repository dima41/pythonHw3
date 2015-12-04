import os
from os import listdir
from os.path import join
import re
from collections import Counter
import random
import pickle


class NgramCounter:

    def get_texts(self):
        self._sents = []
        directories = [join(self._corpus_path, f)
                       for f in listdir(self._corpus_path)]
        files = [join(d, f) for d in directories for f in listdir(d)]
        for f in files:
            with open(f) as input_file:
                text = input_file.read()
                for sent in re.split("[.!?]*", text):
                    self._sents.append(re.split("[^a-zA-Z0-9'-]*",
                                                sent.strip()) + ["."])

    def set_ngrams_count(self):
        for n in range(4):
            for sent in self._sents:
                if len(sent) < n:
                    continue
                for i in range(len(sent) - n + 1):
                    ngram_count = sent[i: i + n]
                    self._ngrams_count[n][tuple(ngram_count)] += 1
        self._ngrams_count[0][()] -= len(self._sents)

    def set_upper_words(self):
        self._upper_words = []
        for word in self._words:
            if word[:1].isupper():
                self._upper_words.append(word)

    def set_index_of_words(self):
        self._index_of_words = dict()
        for i, word in enumerate(self._words):
            self._index_of_words[word] = i

    def __init__(self, corpus_path='corpus'):
        self._corpus_path = corpus_path
        self._ngrams_count = {i: Counter() for i in range(4)}
        self.get_texts()
        self.set_ngrams_count()
        self._words = []
        for word in self._ngrams_count[1].keys():
            self._words.append(word[0])
        self.set_upper_words()
        self.set_index_of_words()


class NgramDistribution:

    def set_onegram_distribution(self, ngramCounter):
        self._onegram_distribution = dict()
        for pair in ngramCounter._ngrams_count[2]:
            self._onegram_distribution[pair[0]] = list()
        for pair in ngramCounter._ngrams_count[2]:
            first_word = pair[0]
            segment = 0
            if len(self._onegram_distribution[first_word]) > 0:
                segment = self._onegram_distribution[first_word][-1][1]
            index = ngramCounter._index_of_words[pair[1]]
            segment += ngramCounter._ngrams_count[2][pair]
            self._onegram_distribution[first_word].append((index, segment))

    def set_twogram_distribution(self, ngramCounter):
        self._twogram_distribution = dict()
        for three in ngramCounter._ngrams_count[3]:
            self._twogram_distribution[three[:2]] = list()
        for three in ngramCounter._ngrams_count[3]:
            context = three[:2]
            segment = 0
            if len(self._twogram_distribution[context]) > 0:
                segment = self._twogram_distribution[context][-1][1]
            index = ngramCounter._index_of_words[three[2]]
            segment += ngramCounter._ngrams_count[3][three]
            self._twogram_distribution[context].append((index, segment))

    def __init__(self, ngramCounter):
        self.set_onegram_distribution(ngramCounter)
        self.set_twogram_distribution(ngramCounter)


class Generator:

    def find_index(self, x, distribution):
        if x < distribution[0][1]:
            return distribution[0][0]
        left = 1
        right = len(distribution)
        while (right - left) > 1:
            mid = (right - left)/2 + left
            if distribution[mid-1][1] <= x:
                left = mid
            else:
                right = mid
        return distribution[left][0]

    def generate_upper_word(self):
        i = random.randint(0, len(self._ngramCounter._upper_words) - 1)
        return self._ngramCounter._upper_words[i]

    def generate_second_word(self, word):
        segment = self._ngramDistribution._onegram_distribution[word][-1][1]
        x = random.randint(0, segment - 1)
        temp = self._ngramDistribution._onegram_distribution[word]
        index = self.find_index(x, temp)
        return self._ngramCounter._words[index]

    def generate_word(self, context):
        segment = self._ngramDistribution._twogram_distribution[context][-1][1]
        x = random.randint(0, segment - 1)
        temp = self._ngramDistribution._twogram_distribution[context]
        index = self.find_index(x, temp)
        return self._ngramCounter._words[index]

    def generate_sent(self, max_sent_len):
        sent = []
        first_word = self.generate_upper_word()
        sent.append(first_word)
        second_word = self.generate_second_word(first_word)
        sent.append(second_word)
        n = max_sent_len - 2
        while n > 0 and second_word != '.':
            temp_word = second_word
            second_word = self.generate_word((first_word, second_word))
            first_word = temp_word
            sent.append(second_word)
            n -= 1
        return sent

    def generate_text(self, max_text_len):
        text = ""
        n = max_text_len
        while n > 0:
            sent = self.generate_sent(n)
            text += " ".join(sent[:-1]) + '.\n'
            n -= len(sent)
        return text

    def __init__(self, ngramCounter, ngramDistribution):
        self._ngramCounter = ngramCounter
        self._ngramDistribution = ngramDistribution


ngramCounter = NgramCounter()
with open('ngramCounter.pickle', 'wb') as f:
    pickle.dump(ngramCounter, f)

ngramDistribution = NgramDistribution(ngramCounter)
with open('ngramDistribution.pickle', 'wb') as f:
    pickle.dump(ngramDistribution, f)

ngramCounter = None
ngramDistribution = None

with open('ngramCounter.pickle', 'rb') as f:
    ngramCounter = pickle.load(f)
with open('ngramDistribution.pickle', 'rb') as f:
    ngramDistribution = pickle.load(f)

generator = Generator(ngramCounter, ngramDistribution)

text = generator.generate_text(10000)
print text

with open("out.txt", 'w') as output_file:
    output_file.write(text)
output_file.close()
