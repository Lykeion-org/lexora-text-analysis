import spacy
from en_service.maps import GENDER_MAP, NUMBER_MAP, CASE_MAP, MOOD_MAP, TENSE_MAP, ASPECT_MAP,PERSON_MAP

_NLP = spacy.load("en_core_web_sm")

OBJECT_POS = {"NOUN", "PROPN"}
ACTION_POS = {"VERB"}
MODIFIER_POS = {"ADJ", "ADV"}

def extract_word_attributes(token) -> dict:
    morph = token.morph

    word_attributes = {
        "gender": GENDER_MAP.get(morph.get("Gender")[0], 0) if morph.get("Gender") else 0,
        "number": NUMBER_MAP.get(morph.get("Number")[0], 0) if morph.get("Number") else 0,
        "case": CASE_MAP.get(morph.get("Case")[0], 0) if morph.get("Case") else 0,
        "mood": MOOD_MAP.get(morph.get("Mood")[0], 0) if morph.get("Mood") else 0,
        "tense": TENSE_MAP.get(morph.get("Tense")[0], 0) if morph.get("Tense") else 0,
        "aspect": ASPECT_MAP.get(morph.get("Aspect")[0], 0) if morph.get("Aspect") else 0,
        "person": PERSON_MAP.get(morph.get("Person")[0], 0) if morph.get("Person") else 0,
        "diminutive": False,
        "direct_object": token.dep_ == "dobj",
        "indirect_object": token.dep_ == "iobj",
        "valency": len([
            child for child in token.children if child.dep_ in ("nsubj", "obj", "iobj")
        ]),
        "reflexive": bool(morph.get("Reflex")),
        "unique": token.pos_ == "PROPN"
    }

    return word_attributes

def analyze_text(text: str) -> dict:
    doc = _NLP(text)
    
    objects = {}
    actions = {}
    modifiers = {}

    for token in doc:
        if token.pos_ in OBJECT_POS:
            bucket = objects
        elif token.pos_ in ACTION_POS:
            bucket = actions
        elif token.pos_ in MODIFIER_POS:
            bucket = modifiers
        else:
            # Determiners, pronouns, punctuation, numbers etc. are not dictionary entries.
            continue

        item = {
            # Keep capitals only for names, so "Bicycles" at the start of a sentence becomes "bicycles".
            "text": token.text if token.pos_ == "PROPN" else token.text.lower(),
            "lemma": token.lemma_,
            "pos": token.pos_,
            "attributes": extract_word_attributes(token)
        }
        # One entry per surface form, so "coffee" and "coffees" are both kept.
        bucket.setdefault((token.text.lower(), token.pos_), item)

    return {
        "objects": list(objects.values()),
        "actions": list(actions.values()),
        "modifiers": list(modifiers.values())
    }
    