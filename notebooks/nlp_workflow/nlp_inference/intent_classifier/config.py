RAW_DATA_TABLE = "applied_machine_learning.droptopicanalysis_dev.inf_halosight_halo_fact_topic"
PREPROCESSED_TRAINING_DATA_TABLE = "applied_machine_learning.droptopicanalysis_dev.preprocessed_intent_train_data"
PREPROCESSED_VALIDATION_DATA_TABLE = (
    "applied_machine_learning.droptopicanalysis_dev.preprocessed_intent_validation_data"
)

MODEL_NAME = "distilbert/distilbert-base-uncased"
MODEL_PATH = "/dbfs/FileStore/shared_uploads/nlp_topic_builder/intent_classifier/model_weights"
REGISTERED_MODEL_NAME = "intent_classifier"

EXPERIMENT_NAME_SUFIX = "train_val_intent_classifier"

TRAIN_SIZE = 0.8
TEST_SIZE = 0.1

TRAINING_BATCH_SIZE = 128
TEST_BATCH_SIZE = 128
VALIDATION_BATCH_SIZE = 512

NUM_TRAIN_EPOCHS = 5

SEED = 42
