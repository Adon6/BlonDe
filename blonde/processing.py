import logging, spacy, re
from . import CATEGORIES_EN, CATEGORIES_DE, VB_TYPE, PRONOUN_TYPE_ENGLISH, PRONOUN_TYPE_GERMAN,\
    PRONOUN_MAP_ENGLISH, PRONOUN_MAP_GERMAN, DM_TYPE, DM_MAP, PRONOUN_TAGS_ENGLISH, PRONOUN_TAGS_GERMAN,\
    PRONOUN_MAP_ENGLISH_2ND_PERSON, PRONOUN_MAP_GERMAN_2ND_PERSON, PRONOUN_MAP_ENGLISH_3rd_PERSON_PLURAL
from .utils import ProcessedSent, ProcessedDoc, ProcessedCorpus
from collections import Counter
from typing import Sequence, Tuple, Dict

import en_core_web_sm, de_core_news_sm
# spacy.prefer_gpu()
nlp_en = en_core_web_sm.load()
nlp_de = de_core_news_sm.load()
# nlp = spacy.load('en_core_web_sm')

def count_vb(sent_tag):
    count_vb = Counter()
    for tag in sent_tag:
        if tag in VB_TYPE:
            count_vb[tag] += 1
    return count_vb


def count_formality(sent_tok, sent_tag, source_sent, source_tags):
    types = ['formal', 'informal']
    count_fo = Counter()
    assert len(sent_tok) == len(sent_tag)
    if source_sent is not None:  # we check if  2nd person neutral pronoun is in source sentence
        valid_example = False
        assert len(source_sent) == len(source_tags)
        for word, tag in zip(source_sent, source_tags):
            if tag in PRONOUN_TAGS_ENGLISH and word in PRONOUN_MAP_ENGLISH_2ND_PERSON:
                valid_example = True
        if valid_example:
            for word, tag in zip(source_sent, source_tags):  # if 3rd person neuter/female or 3rd person plural is in source, formal style could be mistaken for those
                if tag in PRONOUN_TAGS_ENGLISH and word in PRONOUN_MAP_ENGLISH_3rd_PERSON_PLURAL + PRONOUN_MAP_ENGLISH['neuter'] + PRONOUN_MAP_ENGLISH['feminine']:
                    types.remove('formal')
                    break
    else:
        valid_example = True
    if not valid_example:
        return Counter()  # we are only looking for 3rd person neutral pronouns here
    for word, tag in zip(sent_tok, sent_tag):
        for type in types:
            if word in PRONOUN_MAP_GERMAN_2ND_PERSON[type] and tag in PRONOUN_TAGS_GERMAN:
                count_fo[type] += 1
    # if len(count_fo) > 0:
    #     import pdb; pdb.set_trace()
    return count_fo


def count_pronoun(sent_tok, pronoun_type, pronoun_map, sent_tag, pronoun_tags, source_sent=None, source_tags=None,
                  source_lang=None):
    pronoun_type = pronoun_type.copy()
    count_pr = Counter()
    assert len(sent_tok) == len(sent_tag)
    if source_sent is not None:  # we check if  3rd person neutral pronoun is in source sentence
        valid_example = False
        assert len(source_sent) == len(source_tags)
        for word, tag in zip(source_sent, source_tags):
            if tag in PRONOUN_TAGS_ENGLISH and word in PRONOUN_MAP_ENGLISH['neuter']:
                valid_example = True
        if valid_example:
            for word, tag in zip(source_sent, source_tags):  # if 2nd person or 3rd person plural is in source, we can not reliably detect female form
                if tag in PRONOUN_TAGS_ENGLISH and word in (PRONOUN_MAP_ENGLISH_2ND_PERSON + PRONOUN_MAP_ENGLISH_3rd_PERSON_PLURAL):
                    pronoun_type.remove('feminine')
                    break
    else:
        valid_example = True
    if not valid_example:
        return Counter()  # we are only looking for 3rd person neutral pronouns here
    for word, tag in zip(sent_tok, sent_tag):
        for type in pronoun_type:
            if word in pronoun_map[type] and tag in pronoun_tags:
                count_pr[type] += 1
    # if len(count_pr) > 1:
    #     import pdb; pdb.set_trace()
    return count_pr


def count_entity(sent_ent: Tuple[str, str, int, int], tgt_lang) -> Sequence[Counter]:
    cnt_person = Counter()
    cnt_non_person = Counter()
    if tgt_lang == 'english':
        for ent in sent_ent:
            if ent[1] == 'PERSON':
                cnt_person[ent[0]] += 1
            elif ent[1] == 'NORP' or ent[1] == 'GPE' or ent[1] == 'FAC' or ent[1] == 'ORG' or ent[1] == 'WORK_OF_ART':
                cnt_non_person[ent[0]] += 1
    elif tgt_lang == 'german':
        for ent in sent_ent:
            if ent[1] == 'PER':
                cnt_person[ent[0]] += 1
            elif ent[1] == 'ORG':
                cnt_non_person[ent[0]] += 1
    return [cnt_person, cnt_non_person]


def count_dm(sent_tok: Sequence[str]) -> Counter:
    def _count_sublist(L: Sequence, s: Sequence):
        """count how many sublist s there are in the list L."""
        return len([None for i in range(len(L)) if L[i:i+len(s)] == s])
    count_dm = Counter()
    lower_tok = [tok.lower() for tok in sent_tok]
    for type in DM_TYPE:
        for dm_span in DM_MAP[type]:
            dm_span = dm_span.split(' ')
            tmp_count = _count_sublist(lower_tok, dm_span)
            count_dm[type] += tmp_count
    return count_dm


def count_plus(sent_text: str, checkpoints: Sequence[str]) -> Counter:
    """
    checkpoints is the list of annotated spans of a certain category, e.g. Ambiguity or Ellipsis
    """
    count_c = Counter() # c denotes BlonDe plus category
    for span in checkpoints:
        pattern = re.compile(r"\b{}\b".format(span), re.IGNORECASE)
        lst = re.findall(pattern, sent_text)
        count_c[span] = len(lst)
    return count_c


def post_process_ent(ent: Tuple[str, str, int, int]) -> Tuple[str, str, int, int]:
    """
    rule-based post processing after spacy's NER process: drop of 's, e.g. Qiao Lian's -> Qiao Lian
    """
    text = ent.text
    if text[-2:] == "’s":  # or other inflections
        text = text[:-2]
    return text, ent.label_, ent.start, ent.end - 1


def count_ngram(sent_tok: Sequence[str], orders: Tuple[int]) -> Sequence[Counter]:
    def _extract_word_ngrams(tokens: Sequence[str], n: int) -> Counter:
        """Extracts n-grams with order `n` from a list of tokens.

        :param tokens: A list of tokens.
        :param n: The order of n-grams.
        :return: a Counter object with n-grams counts.
        """
        return Counter([' '.join(tokens[i:i + n]) for i in range(len(tokens) - n + 1)])
    return [_extract_word_ngrams(sent_tok, n) for n in orders]


def process_corpus(corpus: Sequence[Sequence[str]], categories: Dict[str, Sequence[str]]=CATEGORIES_EN, lowercase=False,
                   language='english', source=None, source_lang=None) -> ProcessedCorpus:
    """
    :param corpus: a list of documents from a same corpus, which share the same named entities, such as a book.
                corpus = [doc1, doc2, ...], where doc1 = [sent1, sent2, ...], and `sent1` is a string.
    :param categories: a dict
    :param min_order: Minimum n-gram order.
    :param max_order: Maximum n-gram order.
    :return processed_corpus： a list of `processed_doc` (`Doc` object)
                        where `processed_doc` is a list of dicts (corresponds to a chapter),
                        where each dict `processed_sent` corresponds to a sentence.
                        The keys are:
                          "str": the plain texts of the sentence
                          "sent_tok": a list of tokens
                          "sent_tag": a list of POS tags
                          "sent_ent": (ent.text, ent.label_, ent.start, ent.end)
                          "category_count": a dict, where
                              "tense": a dict of the counts of verbs, where the keys are VB_TYPE (7 keys)
                              "pronoun": a dict of the counts of pronouns, where the keys are PRONOUN_TYPE (4 keys)
                              "entity": [cnt_person, cnt_non_person],
                                        where `cnt_person` and `cnt_non_person` are counters and the keys are entities.
                              "dm": a dict of the counts of DM categories, where the keys are DM_TYPE (5 keys)
                              "n-gram": [1-gram, i-gram, ...], where `i-gram`s are counters and the keys are i-grams.
    """
    if language == 'english':
        nlp = nlp_en
        categories = CATEGORIES_EN
        pronoun_type = PRONOUN_TYPE_ENGLISH
        pronoun_map = PRONOUN_MAP_ENGLISH
        pronoun_tags = PRONOUN_TAGS_ENGLISH
    elif language == 'german':
        nlp = nlp_de
        categories = CATEGORIES_DE
        pronoun_type = PRONOUN_TYPE_GERMAN
        pronoun_map = PRONOUN_MAP_GERMAN
        pronoun_tags = PRONOUN_TAGS_GERMAN

    if source is not None:
        if lowercase:
            source = [sent.lower() for sent in source]
        source = list(nlp_en.pipe(source, disable=["parser"]))
        source_sent = [[w.text for w in doc] for doc in source]
        source_tags = [[w.tag_ for w in doc] for doc in source]

    flat_doc_list, sent_num_per_doc = _flatten_list(corpus)
    if lowercase:
        flat_doc_list = [sent.lower() for sent in flat_doc_list]
    processed_corpus = []
    processed_doc = []
    i = 0
    for k, doc in enumerate(nlp.pipe(flat_doc_list, disable=["parser"])):
        sent_tok = [w.text for w in doc]
        sent_tag = [w.tag_ for w in doc]
        sent_ent = [post_process_ent(ent) for ent in doc.ents]
        processed_sent = {"str": doc.text,  "sent_tok": sent_tok, "sent_tag": sent_tag, "sent_ent": sent_ent,
                          "count": {}}
        if "tense" in categories.keys():
            processed_sent["count"]["tense"] = count_vb(sent_tag)
        if "pronoun" in categories.keys():
            processed_sent["count"]["pronoun"] = count_pronoun(sent_tok, pronoun_type=pronoun_type,
                                                               pronoun_map=pronoun_map, sent_tag=sent_tag,
                                                               pronoun_tags=pronoun_tags,
                                                               source_sent=source_sent[k] if source is not None else None,
                                                               source_tags=source_tags[k] if source is not None else None,
                                                               source_lang=source_lang)
        if "formality" in categories.keys():
            processed_sent["count"]["formality"] = count_formality(sent_tok, sent_tag=sent_tag,
                                                               source_sent=source_sent[k] if source is not None else None,
                                                               source_tags=source_tags[k] if source is not None else None,)
        if "entity" in categories.keys():
            processed_sent["count"]["entity"] = count_entity(sent_ent, tgt_lang=language)
        if "dm" in categories.keys():
            processed_sent["count"]["dm"] = count_dm(sent_tok)
        if "n-gram" in categories.keys():
            orders = categories["n-gram"]
            if len(orders) == 1:
                orders = range(orders)
            processed_sent["count"]["n-gram"] = count_ngram(sent_tok, orders)
        processed_doc.append(processed_sent)
        sent_num_per_doc[i] -= 1
        if sent_num_per_doc[i] == 0:
            processed_corpus.append(processed_doc)
            processed_doc = []
            i += 1
    return processed_corpus


def _flatten_list(doc_list: Sequence[Sequence[str]]) -> Tuple[Sequence[str], int]:
    """
    :param doc_list: a `corpus`, a list of lists of sentences (str), where a list of sentences is called a `document`.
    :return res: a list of strings, where a string is a long concatenation of all the tokens in a document.
    :return sent_num_per_doc: a list of the numbers of sentences per document
    """

    def flatten(lst):
        return [item for sublist in lst for item in sublist]

    res = flatten(doc_list)
    sent_num_per_doc = [len(doc) for doc in doc_list]
    return res, sent_num_per_doc


def add_blonde_plus_categories(doc: ProcessedDoc, lines_an):
    """
    Add the annotated BlonDe+ categories to `Doc` object, which is a list of dicts described in `processed_doc`,
    i.g. list_of_dict[ {"str": "xxx", "ambiguity": ["xx", "xx", "xx"], "ellipsis": ["xx", "xx", "xx"]} ]

    Error Types:
        Ambiguity: It is right to put it in a single sentence, but it is wrong in the context #1
        Ellipsis: 1) Subject/object pronouns are omitted in Chinese, but appear in reference #2
                  2) Other omissions (if any, mark the word/phrase) #3
        Cohesion: Translation error related to named entities #4
                  Tense error #5
        Sentence-level error #6
        No error: #0
    """
    # Sanity Check
    if len(lines_an) != len(doc):
        logging.error(f"The length of lines_an is not equal to reference document! "
                        f"They should contain the same amount of sentences!")

    # For each sentence, we get `amb_checkpoints` and `ell_checkpoints`, by pass them as `checkpoint_lst` and append
    def append_checkpoints(checkpoint_lst, error_type):
        # error_type: 1,indifferent, cold <pos/266,269>
        check_spans = error_type[2:].split(";")
        for check_span in check_spans:
            pair = check_span.split("<pos/")[0]
            if len(pair) < 2:
                continue
            ref_checkpoint = pair.split(",")[0]  # 'indifferent'
            checkpoint_lst.append(ref_checkpoint)

    for j, line_an in enumerate(lines_an):
        amb_checkpoints, ell_checkpoints = [], []
        error_types = line_an.split("\t")
        for error_type in error_types:
            if len(error_type) < 1 or not error_type[0].isdigit():  # the text string
                continue
            if error_type[0] == "1":  # Ambiguity
                append_checkpoints(amb_checkpoints, error_type)
            if error_type[0] == "3":  # Ellipsis
                append_checkpoints(ell_checkpoints, error_type)
        sent_text = doc[j]["str"]
        doc[j]["count"]["plus"] = []
        #print("amb_checkpoints: ", amb_checkpoints)
        #print(count_plus(sent_text, amb_checkpoints))
        doc[j]["count"]["plus"].append(count_plus(sent_text, amb_checkpoints))
        doc[j]["count"]["plus"].append(count_plus(sent_text, ell_checkpoints))


def refine_NER(doc: ProcessedDoc, lines_ner):
    """
    Add the human annotated NER (instead of the automated recognized ones) into `doc`

    The format of `ner_file`:
        PERSON: ()	NONPERSON: ()
        PERSON: (Zhang Gong: 1; )	NONPERSON: (Tianwu: 2; Libo: 1; the Dalu Kingdom : 1; the Magic Kingdom of Aixia: 1; the Xiuda Kingdom: 1; )
                (1 is the number of occurrences of the named entity)

    for each sentence in `doc`, we add a field "count_ent":
        a tuple [cnt_person, cnt_non_person],
        where `cnt_person` and `cnt_non_person` are dicts, and the keys of entities.
    """
    if len(lines_ner) != len(doc):
        logging.warning(f"length of the ner is not equal to reference document! ")
    for j, line in enumerate(lines_ner):
        new_count_ent = [Counter(), Counter()]
        entity_types = line.split("\t")
        for i, entity_type in enumerate(entity_types):
            entity_type = entity_type.split("(")[1]
            entities = entity_type.split(";")[:-1]
            for entity in entities:
                name = entity.split(":")[0].strip(' ').lower().split("'s")[0].split("’s")[0].split("'")[0]
                count = int(entity.split(":")[-1])
                new_count_ent[i][name] = count
        doc[j]["count_ent"] = new_count_ent