from .intent_classifier import (  # noqa: TID252 F401. Need to be imported for get_intents udf function, it serializes AutoModelForIntentClassification.
    AutoModelForIntentClassification,
)
