import subprocess

import spacy

download_command = ["python3", "-m", "spacy", "download", "en_core_web_sm"]
subprocess.run(download_command, check=False)

nlp = spacy.load("en_core_web_sm")
stopwords = nlp.Defaults.stop_words


def extract_semantic_entities(sentence: str) -> list[dict[str, str]]:
    """
    Methodology to identify whether a noun within the sentence was the actor of the verb or was being acted on by the verb.
    Extract semantic roles entities, based on this doc: https://web.stanford.edu/~jurafsky/slp3/slides/22_SRL.pdf
    """
    if not sentence:
        return None

    doc = nlp(sentence)
    semantic_entites = {
        "agent": [],
        "lemma": [],
        "theme": [],
        "goal": [],
        "beneficiary": [],
        "entities_related_to_lemma": [],
    }
    for token in doc:
        if token.dep_ == "nsubj" and token.head.pos_ == "VERB":
            agent = token.text
            lemma = token.head.lemma_

            # Find direct objects of the verb
            objects = [child.text for child in token.head.children if child.dep_ == "dobj"]
            # Find indirect objects of the verb
            indirect_objects = [child.text for child in token.head.children if child.dep_ == "dative"]
            # Find other relevant entities related to the verb
            other_entities = [
                child
                for child in token.head.children
                if child.dep_ != "nsubj" and child.dep_ != "dobj" and child.dep_ != "dative" and not child.is_punct
            ]
            # Find prepositional phrases and extract relevant information

            semantic_entites["lemma"].append(lemma)
            semantic_entites["agent"].append(agent)

            prep_phrases = [child for child in token.head.children if child.dep_ == "prep"]

            for prep in prep_phrases:
                prep_text = prep.text
                prep_object = [child.text for child in prep.children if child.dep_ == "pobj"]
                if prep_object:
                    semantic_entites["goal"].extend([prep_text, *prep_object])
            if objects:
                semantic_entites["theme"].extend(objects)
            if indirect_objects:
                semantic_entites["beneficiary"].extend(indirect_objects)
            if other_entities:
                new_other_entities = []
                for other_entity in other_entities:
                    if other_entity not in stopwords:
                        if other_entity.pos_ == "VERB":
                            new_other_entities.append(other_entity.lemma_)
                        else:
                            new_other_entities.append(other_entity.text)
                semantic_entites["entities_related_to_lemma"].extend(new_other_entities)

    return [semantic_entites]
