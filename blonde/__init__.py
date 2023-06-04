#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__version__ = '0.1.4'


VB_TYPE = ('VBD', 'VBN', 'VBP', 'VBZ', 'VBG', 'VB', 'MD')
# VB_MAP = dict(zip(VB_TYPE, VB_TYPE))

PRONOUN_TYPE_ENGLISH = ['masculine', 'feminine', 'neuter', 'epicene']
PRONOUN_TYPE_GERMAN = ['masculine', 'feminine', 'neuter', ]
PRONOUN_MAP_ENGLISH = {"masculine": ["he", "his", "him", "He", "His", "Him", "himself", "Himself"],
                       "feminine": ["she", "her", "hers", "She", "Her", "Hers", "herself", "Herself"],
                       "neuter": ["it", "its", "It", "Its", "itself", "Itself"],
                       "epicene": ["they", "their", "them", "They", "Their", "Them", "themselves", "Themselves"]
                       }
# from here https://www.ef.com/wwen/english-resources/english-grammar/pronouns/
PRONOUN_MAP_ENGLISH_2ND_PERSON = ['You', 'you', 'Your', 'your', 'Yours', 'yours', 'Yourself', 'yourself']
PRONOUN_MAP_ENGLISH_3rd_PERSON_PLURAL = ['They', 'they', 'Them', 'them', 'Their', 'their', 'Theirs', 'theirs',
                                         'Themselves', 'themselves']

PRONOUN_MAP_GERMAN_2ND_PERSON = {
    'formal': ['Sie', 'sie', 'Ihr', 'ihr', 'Ihrer', 'ihrer', 'Ihnen', 'ihnen', 'Ihre', 'ihre', 'Ihres', 'ihres'],
    'informal': ['Du', 'du', 'Deiner', 'deiner', 'Dir', 'dir', 'Dich', 'dich', 'Deine', 'deine', 'Dein', 'dein',
                 'Deines', 'deines', 'Deinem', 'deinem', 'Deinen', 'deinen',],
}
# from here: https://www.frustfrei-lernen.de/deutsch/pronomen-deutsch.html
PRONOUN_MAP_GERMAN = {
                      # "masculine": ["Er", "er", "Seiner", "seiner", "Ihm", "ihm", "Ihn", "ihn", "Sein", "sein", "Seine",
                      #               "seine", "Seines", "seines", "Seinem", "seinem"],
    "masculine": ["Er", "er", "Ihm", "ihm", "Ihn", "ihn"],
                      "feminine": ["Sie", "sie", "Ihrer", "ihrer", "Ihr", "ihr", "Ihre", "ihre", "Ihres", "ihres",
                                   "Ihrem", "ihrem"],
                      "neuter": ["Es", "es", ],
                      }
# PRONOUN_TYPE = list(PRONOUN_MAP.keys())
PRONOUN_TAGS_ENGLISH = ['PRP', 'PRP$', 'WP', 'WP$']
PRONOUN_TAGS_GERMAN = ['PDAT', 'PDS', 'PIAT', 'PIS', 'PPER', 'PPOSAT', 'PPOSS', 'PRELAT', 'PRELS', 'PRF', 'PWAT', 'PWAV', 'PWS']


"""
DM_MAP is based on the PDTB hierarchy
The top hierarchy are: 'comparison', 'contingency', 'expansion', 'temporal'
    - Comparison: combine "concession" and "contrast"
    - Contingency: only consider "cause"
    - Expansion: only consider "conjunction"
    - Temporal: "synchronous" and "asynchronous"
"""
DM_TYPE = ('comparison', 'cause', 'conjunction', 'asynchronous', 'synchronous')
DM_MAP = {
    # Comparison:
    'comparison': ["but", "while", "however", "although", "though", "still", "yet", "whereas",
                   "on the other hand", "in contrast", "by contrast", "by comparison", "conversely"],
    # Contingency:
    'cause': ["if", "because", "so", "since", "thus", "hence", "as a result", "therefore", "thereby",
              "accordingly", "consequently", "in consequence", "for this reason"], #"because of that", "because of this"
    # "condition": ["if", "as long as" , "provided that", "assuming that", "given that"],
    # Expansion:
    'conjunction': ["also", "in addition", "moreover", "additionally", "besides", "else,", "plus"],
    # "instantiation": ["for example", "for instance"],
    # "alternative": ["instead", "or", "unless", "separately" ],
    # "restatement": ["indeed", "in fact", "clearly", "in other words", "specifically"]
    # Temporal:
    'asynchronous': ["when", "after", "then", "before",
                     "until", "later", "once", "afterward", "next"],
    'synchronous': ["meantime", "meanwhile", "simultaneously"]
}
# DM_TYPE = list(DM_MAP.keys())

# ('tense', 'pronoun', 'entity', 'dm', 'n-gram')
CATEGORIES_EN = {
    "tense": VB_TYPE,
    "pronoun": PRONOUN_TYPE_ENGLISH,
    "entity": ["PERSON", "NON-PERSON"],
    "dm": DM_TYPE,
    "n-gram": [1, 2, 3, 4]
}

CATEGORIES_DE = {
    "tense": VB_TYPE,
    "pronoun": PRONOUN_TYPE_GERMAN,
    "entity": ["PERSON", "NON-PERSON"],
    "dm": DM_TYPE,
    "n-gram": [1, 2, 3, 4],
    "formality": ["formal", "informal"]
}

WEIGHTS_EN = {
        "tense": (1/7, 1/7, 1/7, 1/7, 1/7, 1/7, 1/7),
        "pronoun": (0.5, 0.5, 0, 0),
        "entity": (1, 0),
        "dm": (0.2, 0.2, 0.2, 0.2, 0.2),
        "n-gram": (0.25, 0.25, 0.25, 0.25)
}

WEIGHTS_DE = {
        "tense": (1/7, 1/7, 1/7, 1/7, 1/7, 1/7, 1/7),
        "pronoun": (0.5, 0.5, 0),
        "entity": (1, 0),
        "dm": (0.2, 0.2, 0.2, 0.2, 0.2),
        "n-gram": (0.25, 0.25, 0.25, 0.25),
        "formality": (0.5, 0.5)
}

from .BlonDe import BLONDE, BLONDEScore, BLONDESignature