from flask import Flask, jsonify, request
import re
import os

app = Flask(__name__)


@app.route('/rhyme', methods=['POST'])
def show_rhymes():
    message = request.get_json(force=True)
    word = message['word']
    syllables_count = message['syllables_count']
    scoreboard = get_scoreboard(word, syllables_count=syllables_count)
    response = jsonify(scoreboard=scoreboard)
    response.headers.add('Access-Control-Allow-Origin', '*')
    return response


def load_dictionary():
    words_dict = []
    directory_path = 'dictionary'
    for filename in os.listdir(directory_path):
        if filename.endswith(".txt"):
            file_path = os.path.join(directory_path, filename)
            lines = open(file_path, 'r', encoding='utf-8').read().split('\n')
            for line in lines:
                words_dict.append(line.strip())
    return words_dict


def get_syllables_count(word):
    vowel_pattern = '[aąeęioóuy]+'
    i_pattern = 'i[aąeęioóuy]'
    diphthong_pattern = '[ae]u'
    vowel_groups = re.findall(vowel_pattern, word)
    count = 0
    for vowel_group in vowel_groups:
        count += len(vowel_group)
        if re.match(i_pattern, vowel_group):
            count -= 1
        if re.match(diphthong_pattern, vowel_group):
            count -= 1
    return count


def get_last_vowels(word):
    word = word.replace('ó', 'u')
    vowel_pattern = '[aąeęioóuy]+'
    i_pattern = 'i[aąeęioóuy]'
    vowel_groups = re.findall(vowel_pattern, word)
    if len(vowel_groups) == 0:
        return ''
    else:
        vowel_group = vowel_groups[-1]
        if re.match(i_pattern, vowel_group):
            return vowel_group[-2:]
        else:
            return vowel_group[-1:]


def get_last_consonants(word):
    consonant_pattern = '[^aąeęioóuy]+'
    consonant_groups = re.findall(consonant_pattern, word)
    if len(consonant_groups) == 0:
        return ''
    else:
        consonant_group = consonant_groups[-1]
        if consonant_group in ['ż', 'rz']:
            return 'sz'
        elif consonant_group == 'dż':
            return 'cz'
        elif consonant_group == 'b':
            return 'p'
        elif consonant_group == 'g':
            return 'k'
        elif consonant_group == 'dź':
            return 'ć'
        elif consonant_group == 'dz':
            return 'c'
        elif consonant_group == 'w':
            return 'f'
        elif consonant_group == 'd':
            return 't'
        elif consonant_group == 'z':
            return 's'
        elif consonant_group == 'ch':
            return 'h'
        else:
            return consonant_group


def get_word_ending(word):
    last_vowels = get_last_vowels(word)
    vowel_pattern = '[aąeęioóuy]'
    if re.match(vowel_pattern, word[-1]):
        return last_vowels
    else:
        return last_vowels + get_last_consonants(word)


def get_word_key(word):
    syllables_count = get_syllables_count(word)
    ending = get_word_ending(word)
    return str(syllables_count) + '_' + ending


def get_word_beginning(word):
    vowel_pattern = '[aąeęioóuy]+'
    i_pattern = 'i[aąeęioóuy]'
    vowel_matches = re.finditer(vowel_pattern, word)
    vowel_match = None
    for match in vowel_matches:
        vowel_match = match

    if not vowel_match:
        return ''
    else:
        vowel_group = vowel_match.group()
        if re.match(i_pattern, vowel_group):
            return word[:vowel_match.end() - 2]
        else:
            return word[:vowel_match.end() - 1]


def get_indexed_dictionary(dictionary):
    indexed_dict = {}
    for word in dictionary:
        key = get_word_key(word)
        if key in indexed_dict:
            indexed_dict[key].append(word)
        else:
            indexed_dict[key] = [word]
    return indexed_dict


def get_score(original_word, checked_word):
    original_word_ending = get_word_ending(original_word)
    checked_word_ending = get_word_ending(checked_word)
    if original_word_ending != checked_word_ending:
        final_score = 0
    else:
        original_word_syllables = get_syllables_count(original_word)
        checked_word_syllables = get_syllables_count(checked_word)
        if original_word_syllables == 1:
            score = 1
        else:
            vowel_pattern = '[aąeęioóuy]'
            if re.match(vowel_pattern, original_word_ending[-1]):
                score = 0.4
            else:
                score = 0.7

            original_word_beginning = get_word_beginning(original_word)
            checked_word_beginning = get_word_beginning(checked_word)
            original_word_beginning = (original_word_beginning.
                                       replace('ó', 'u').
                                       replace('ch', 'h').
                                       replace('au', 'ał').
                                       replace('eu', 'eł'))
            checked_word_beginning = (checked_word_beginning.
                                      replace('ó', 'u').
                                      replace('ch', 'h').
                                      replace('au', 'ał').
                                      replace('eu', 'eł'))

            match = re.search(vowel_pattern, original_word_beginning)
            max_letters = len(original_word_beginning[match.start():])

            same_letters = 0
            for i in range(min(max_letters, len(checked_word_beginning))):
                if original_word_beginning[-1 - i] == checked_word_beginning[-1 - i]:
                    same_letters += 1
                else:
                    break

            score = score + (1 - score) * same_letters / max_letters

        syllables_difference = abs(original_word_syllables - checked_word_syllables)
        final_score = score * (1 - 0.05 * syllables_difference)
        final_score = max(final_score, 0)
    return round(final_score, 2)


def get_rhymes_list(word, syllables_count):
    rhymes_list = []
    ending = get_word_ending(word)
    key = str(syllables_count) + '_' + ending
    rhymes = indexed_dictionary.get(key, None)
    if rhymes is not None:
        for rhyme in rhymes:
            if rhyme == word:
                continue
            rhymes_list.append(rhyme)
    return rhymes_list


def get_scoreboard(word, syllables_count):
    rhymes = get_rhymes_list(word, syllables_count)
    scoreboard = [{"word": rhyme, "score": get_score(word, rhyme)} for rhyme in rhymes]
    sorted_scoreboard = sorted(scoreboard, key=lambda x: (-x["score"], x["word"]))
    return sorted_scoreboard


words_dictionary = load_dictionary()
indexed_dictionary = get_indexed_dictionary(words_dictionary)
app.run()
