NLP_INGESTION_TABLE_NAME = "applied_machine_learning.droptopicanalysis_dev.nlp_input"


# These rules are taken from the PragmaticContentFormatter
# (source: https://github.com/JohnSnowLabs/spark-nlp/blob/master/examples/python/annotation/text/english/sentence-detection/SentenceDetector_advanced_examples.ipynb).

lists = [
    "(\\()[a-z]+\\)|^[a-z]+\\)",
    "\\s\\d{1,2}\\.\\s|^\\d{1,2}\\.\\s|\\s\\d{1,2}\\.\\)|^\\d{1,2}\\.\\)|\\s\\-\\d{1,2}\\.\\s|^\\-\\d{1,2}\\.\\s|s\\-\\d{1,2}\\.\\)|^\\-\\d{1,2}(.\\))",
]
numbers = [
    "(?<=\\d)\\.(?=\\d)",
    "\\.(?=\\d)",
    "(?<=\\d)\\.(?=\\S)",
]
special_abbreviations = [
    "\\b[a-zA-Z](?:\\.[a-zA-Z])+(?:\\.(?!\\s[A-Z]))*",
    "(?i)p\\.m\\.*",
    "(?i)a\\.m\\.*",
]
abbreviations = [
    "\\.(?='s\\s)|\\.(?='s\\$)|\\.(?='s\\z)",
    "(?<=Co)\\.(?=\\sKG)",
    "(?<=^[A-Z])\\.(?=\\s)",
    "(?<=\\s[A-Z])\\.(?=\\s)",
]
punctuations = ["(?<=\\S)[!\\?]+(?=\\s|\\z|\\$)"]
# -> exclude multiple_periods = ["(?<=\\w)\\.(?=\\w)"]
geo_locations = ["(?<=[a-zA-z]°)\\.(?=\\s*\\d+)"]
ellipsis = ["\\.\\.\\.(?=\\s+[A-Z])", "(?<=\\S)\\.{3}(?=\\.\\s[A-Z])"]
in_between_punctuation = [
    "(?<=\\s|^)'[\\w\\s?!\\.,|'\\w]+'(?:\\W)",
    '"[\\w\\s?!\\.,]+"',
    "\\[[\\w\\s?!\\.,]+\\]",
    "\\([\\w\\s?!\\.,]+\\)",
]
quotation_marks = ["\\?(?=(\\'|\\\"))"]
exclamation_points = [
    "\\!(?=(\\'|\\\"))",
    "\\!(?=\\,\\s[a-z])",
    "\\!(?=\\s[a-z])",
]
basic_breakers = ["\\."]  # exclude ";" as a default rule

BOUNDS = [
    *lists,
    *numbers,
    *abbreviations,
    *special_abbreviations,
    *punctuations,
    *geo_locations,
    *ellipsis,
    *in_between_punctuation,
    *quotation_marks,
    *exclamation_points,
    *basic_breakers,
]
