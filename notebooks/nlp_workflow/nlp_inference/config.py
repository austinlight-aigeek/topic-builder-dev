import numpy as np
from pyspark.ml import Pipeline
from sentence_transformers import SentenceTransformer
from sparknlp.annotator import BertForZeroShotClassification, Tokenizer
from sparknlp.base import DocumentAssembler

NLP_INPUT_TABLE_NAME = "applied_machine_learning.droptopicanalysis_dev.nlp_input"
NLP_OUTPUT_TABLE_NAME = "applied_machine_learning.droptopicanalysis_dev.nlp_output"
NLP_BACKFILL_TABLE_NAME = "applied_machine_learning.droptopicanalysis_dev.backfill"
MODEL_NAME_FOR_ZERO_SHOT_CLASSIFICATION = "bert_base_cased_zero_shot_classifier_xnli"
MODEL_NAME_FOR_SENTENCE_EMBEDDING = "sentence-transformers/all-MiniLM-L6-v2"
CANDIDATE_LABELS_SENTIMENT = [
    "very negative",
    "very positive",
    "neutral",
    "positive",
    "negative",
]

# Multi-class Sentiment and intent Classification
document_assembler = DocumentAssembler().setInputCol("sentence_text").setOutputCol("document")

tokenizer = Tokenizer().setInputCols(["document"]).setOutputCol("token")

zero_shot_classification = (
    BertForZeroShotClassification.pretrained(MODEL_NAME_FOR_ZERO_SHOT_CLASSIFICATION, "en")
    .setInputCols(["token", "document"])
    .setOutputCol("label")
    .setCaseSensitive(True)
    .setMaxSentenceLength(511)
    .setCandidateLabels(
        CANDIDATE_LABELS_SENTIMENT,
    )
)

pipeline = Pipeline(stages=[document_assembler, tokenizer, zero_shot_classification])


sentence_transformer = SentenceTransformer(MODEL_NAME_FOR_SENTENCE_EMBEDDING)
assert (
    np.linalg.norm(sentence_transformer.encode("Embedding vectors must have a norm equal to 1.")) == 1
), "Embedding vectors must have a norm equal to 1."
