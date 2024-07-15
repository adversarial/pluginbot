# Text modifier backend
# Copyright (C) 2024 adversarial

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

import random
import queue
import re
import string

IGNORE_NSFW_MODE = True

FORBIDDEN_WORD_FILTER = [ 'https://', 'http://', '.com', '.net', '.org' ]
###############################################################################
# text transformers
###############################################################################

# replaces words with variable length while attempting to match case
def replace_casefixed(old, b, text):
    def case_fixer(match: re.Match):
        result = ''
        lowercount = 0
        uppercount = 0
        for i, c in enumerate(match.group(), start = match.start()):
            ri = i - match.start()
            if(ri > len(b)):
                break
            if c.islower():
                lowercount += 1
                result += b[ri].lower()
            if c.isupper(): 
                uppercount += 1
                result += b[ri].upper()
        if i - match.start() < len(b):
            result += b[i - match.start() + 1:].lower() if lowercount > uppercount else b[i - match.start() + 1:].upper()
        return result
    return re.sub(old, case_fixer, text, flags = re.IGNORECASE)

# removes punctuation surrounding a word and returns 3 values in order, ie: '*shouts*' -> '*', 'shouts', '*'
def strip_surrounding_punctuation(word):
    word = word.strip()
    reversed_punc = ''
    for l in reversed(word):
        if l not in string.ascii_letters + string.digits:
            reversed_punc += l
            word = word.removesuffix(l)
        else:
            break
    punc = ''
    for l in reversed(reversed_punc):
        punc += l
    prepunc = ''
    for l in word:
        if l not in string.ascii_letters + string.digits:
            prepunc += l
            word = word.removeprefix(l)
        else:
            break
    return prepunc, word, punc

NSFW_WORD_FILTER = { 'fuck' : 'frick',
                     'bitch' : 'b-word',
                     'ass' : 'butt',
                     'hell' : 'heck',
                     'penis' : 'peepee',
                     'vagina' : 'girl peepee' }


def filter_nsfw(word, nsfw_flag):
    if not nsfw_flag:
        for old, new in NSFW_WORD_FILTER.items():
            return replace_casefixed(old, new, word)
    else:
        return word
        
###############################################################################
# super
###############################################################################
class ifier:
    def __init__(self, 
                 substring_replacements, 
                 replacements, 
                 additions, 
                 actions):
        self.substring_replacements = substring_replacements
        self.replacements = replacements
        self.additions = additions
        self.actions = actions

    def ify_text(self,
                 text, 
                 replace_weight: int,
                 addition_weight: int,
                 action_weight: int,
                 nsfw_flag: bool = True):
        
        if IGNORE_NSFW_MODE:
            nsfw_flag = True
        
        # transform tokens
        transformed_string = queue.Queue()
        tokens = text.split()
        # ignore urls and whitespace, fuzzy and whole word replace, additions, add actions after punctuation, nsfw filter
        for t in tokens:
            if any(forbidden in t.lower() for forbidden in FORBIDDEN_WORD_FILTER):
                 continue
            
            prepunc, t_punctless, punc = strip_surrounding_punctuation(t)

            if self.substring_replacements:
                for old, new in self.substring_replacements.items():
                     t_punctless = replace_casefixed(old, new, t_punctless)
            
            if t_punctless in self.replacements:
                t_punctless = self.replacements[t_punctless] if replace_weight > random.randint(1, 100) else t_punctless

            sanitized = filter_nsfw(t_punctless, False if isinstance(self, sfwifier) else nsfw_flag)
            transformed_string.put(prepunc + sanitized + punc)

            if punc or (t is tokens[-1]):
                if action_weight > random.randint(1, 100) and self.actions:
                    transformed_string.put(filter_nsfw(random.choice(self.actions), nsfw_flag))
            elif addition_weight > random.randint(1, 100) and self.additions:
                transformed_string.put(filter_nsfw(random.choice(self.additions), nsfw_flag))

        return ' '.join(transformed_string.queue)

###############################################################################
# owoifier - makes cute w-wittwe owos
###############################################################################
class owoifier(ifier):
    TRIGGER_EMOJIS = [ ]
    REPLACE_WEIGHT = 100
    ADDITION_WEIGHT = 20
    ACTION_WEIGHT = 85
    SUBSTRING_REPLACEMENTS = { 'r' : 'w', 
                               'l' : 'w',
                               ' c' : ' c-c',
                               ' w' : ' w-w' }
    REPLACEMENTS = { ':)': 'oWo',
                     ':(': 'uwu' }
    ADDITIONS = [ 'rawr', 'OwO', 'owo', 'UwU', 'uwu', 'qwq', 'o.O', '-.-', '>w<', '^w^', 'òωó', 'ꈍᴗꈍ',
                  '(U ᵕ U❁)', '^•ω•^', '😳', '^^', '^^;', ';_;', 'x3', ':3', 'xD', 'cx', 'Cx', 'c:',
                  'nyah', 'bleh' 'mya', 'hehe', '(◡ ω ◡)', '(˘ε˘)', '(„ᵕᴗᵕ„)', '(ᵕᴗ ᵕ⁎)', '(｡ᴜ‿‿ᴜ｡)',
                  '( U ω U )', 'ღ(U꒳Uღ)', ':･ﾟ✧(ꈍᴗꈍ)✧･ﾟ:','(ㅅꈍ ˘ ꈍ)', 'owO' ]
    ACTIONS = [ '*snuggles*', '*bites you*', '*glomps you*', '*pounces on you*', '*blushes*',
                '*runs away*', '*hugs you*', '*nuzzles you*', '*screams*', 'EEEEEK', '*sweats*',
                '*licks lips*', '*glomp*', '*walks away*', '*cries*', '*twerks*', '*sees bulge*', '*notices bulge*']
    def __init__(self):
        super().__init__(substring_replacements = self.SUBSTRING_REPLACEMENTS,
                         replacements = self.REPLACEMENTS, 
                         additions = self.ADDITIONS, 
                         actions = self.ACTIONS)
    def ify_text(self, text, nsfw_flag = True):
        return super().ify_text(text,
                                replace_weight = self.REPLACE_WEIGHT, 
                                addition_weight = self.ADDITION_WEIGHT, 
                                action_weight = self.ACTION_WEIGHT, 
                                nsfw_flag = nsfw_flag)

###############################################################################
# vallify - like literally makes your text umm casual
###############################################################################
class vallifier(ifier):
    TRIGGER_EMOJIS = [ ]
    REPLACE_WEIGHT = 80
    ADDITION_WEIGHT = 20
    ACTION_WEIGHT = 40
    SUBSTRING_REPLACEMENTS = { }
    REPLACEMENTS = { 'I': 'like I',
                     'you': 'like you',
                     'they': 'they like',
                     'can\'t': 'can\'t even',
                     'cannot': 'literally cannot',
                     'that' : 'literally that',
                     'and' : 'and like' }
    ADDITIONS = ['literally', 'like', 'anyways', 'like even', 'so', 'umm' ]
    ACTIONS = [ '*gags you with a spoon*', 'and that\'s the tea sis', 'and so', 'and well...',
                'and then', 'and like', 'and totally', 'the audacity', ]
    def __init__(self):
        super().__init__(substring_replacements = self.SUBSTRING_REPLACEMENTS,
                         replacements = self.REPLACEMENTS, 
                         additions = self.ADDITIONS, 
                         actions = self.ACTIONS)
    def ify_text(self, text, nsfw_flag = True):
        return super().ify_text(text, 
                                replace_weight = self.REPLACE_WEIGHT, 
                                addition_weight = self.ADDITION_WEIGHT, 
                                action_weight = self.ACTION_WEIGHT, 
                                nsfw_flag = nsfw_flag)

###############################################################################
# sfwifier - makes your text less of a fricking blasphemy
###############################################################################
class sfwifier(ifier):
    TRIGGER_EMOJIS = [ ]
    REPLACE_WEIGHT = 100
    ADDITION_WEIGHT = 0
    ACTION_WEIGHT = 0
    SUBSTRING_REPLACEMENTS = { }
    REPLACEMENTS = { }
    ADDITIONS = [ ]
    ACTIONS = [ ]

    def __init__(self):
        super().__init__(substring_replacements = self.SUBSTRING_REPLACEMENTS,
                         replacements = self.REPLACEMENTS, 
                         additions = self.ADDITIONS, 
                         actions = self.ACTIONS)

    def ify_text(self, text, nsfw_flag = False):
        return super().ify_text(text,
                                replace_weight = self.REPLACE_WEIGHT, 
                                addition_weight = self.ADDITION_WEIGHT, 
                                action_weight = self.ACTION_WEIGHT, 
                                nsfw_flag = False)
        
ifier_list = [ owoifier(), vallifier(), sfwifier() ]

