# Databricks notebook source
import time

import mlflow
import numpy as np
import torch
from config import (
    EXPERIMENT_NAME_SUFIX,
    MODEL_NAME,
    MODEL_PATH,
    NUM_TRAIN_EPOCHS,
    PREPROCESSED_TRAINING_DATA_TABLE,
    PREPROCESSED_VALIDATION_DATA_TABLE,
    REGISTERED_MODEL_NAME,
    SEED,
    TEST_BATCH_SIZE,
    TEST_SIZE,
    TRAINING_BATCH_SIZE,
    VALIDATION_BATCH_SIZE,
)
from data_utils import (
    CustomDataCollatorWithPadding,
    batch_inference,
    cast_cat_col,
    tokenize,
)
from datasets import Dataset
from intent_classifier import (
    AutoModelForIntentClassification,
)
from metrics_utils import evaluate_classification, plot_metrics
from mlflow.models import ModelSignature
from mlflow.types.schema import ColSpec, Schema
from optim_utils import epoch_time, evaluate_model, train_model
from torch.optim import AdamW
from torch.utils.data import DataLoader
from transformers import AutoModelForSequenceClassification, AutoTokenizer, get_scheduler

# COMMAND ----------

# Set seed for reproducibility
np.random.seed(SEED)
torch.manual_seed(SEED)
torch.backends.cudnn.deterministic = True

device = torch.device("cuda") if torch.cuda.is_available() else torch.device("cpu")

USER_NAME = dbutils.notebook.entry_point.getDbutils().notebook().getContext().tags().apply("user")
experiment_name = f"/Users/{USER_NAME}/{EXPERIMENT_NAME_SUFIX}"

# COMMAND ----------

tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
data_collator = CustomDataCollatorWithPadding(tokenizer=tokenizer)

# COMMAND ----------

# The BERT model and their variants cannot process texts which are longer than 512 tokens (tokenizer.model_max_length).
# Calculate the max_length of training/sentence_text under 99 percentile
ds_train = Dataset.from_pandas(spark.table(PREPROCESSED_TRAINING_DATA_TABLE).toPandas())
sentence_text_tokenized = ds_train.map(
    lambda example: tokenizer(example["sentence_text"], truncation=False), batched=True
)["input_ids"]
sentence_text_tokenized_len = [len(sentence_tokenized) for sentence_tokenized in sentence_text_tokenized]
max_length = int(np.percentile(sentence_text_tokenized_len, 99))
max_length = tokenizer.model_max_length if max_length > tokenizer.model_max_length else max_length

# COMMAND ----------

ds_val = Dataset.from_pandas(spark.table(PREPROCESSED_VALIDATION_DATA_TABLE).toPandas())

col_to_tokenize = "sentence_text"
tokenizer_kwargs = {"truncation": True, "max_length": max_length}
ds_train = tokenize(
    ds_train,
    tokenizer,
    col_to_tokenize=col_to_tokenize,
    tokenizer_kwargs=tokenizer_kwargs,
)
ds_val = tokenize(
    ds_val,
    tokenizer,
    col_to_tokenize=col_to_tokenize,
    tokenizer_kwargs=tokenizer_kwargs,
)

INTENT_CLASS_LABELS = [
    "statement",
    "request",
    "action-request",
    "information-request",
    "yes-no-question",
]

ds_train = cast_cat_col(ds_train, "label", labels=INTENT_CLASS_LABELS)
ds_val = cast_cat_col(ds_val, "label", labels=INTENT_CLASS_LABELS)

# map the expected ids from unique_intent_type to their labels, we will need them for the model
id2label = dict(enumerate(INTENT_CLASS_LABELS))
label2id = {v: k for k, v in id2label.items()}

# COMMAND ----------

ds = ds_train.train_test_split(
    test_size=TEST_SIZE,
    shuffle=True,
    stratify_by_column="label",
    seed=SEED,
)

ds_train = ds["train"]
ds_test = ds["test"]

ds_train.set_format(type="torch", output_all_columns=True)
ds_test.set_format(type="torch", output_all_columns=True)
ds_val.set_format(type="torch", output_all_columns=True)

train_dataloader = DataLoader(
    ds_train,
    shuffle=True,
    collate_fn=data_collator,
    batch_size=TRAINING_BATCH_SIZE,
)
test_dataloader = DataLoader(ds_test, collate_fn=data_collator, batch_size=TEST_BATCH_SIZE)
validation_dataloader = DataLoader(ds_val, collate_fn=data_collator, batch_size=VALIDATION_BATCH_SIZE, shuffle=True)

del ds

# COMMAND ----------

intent_classifier = AutoModelForSequenceClassification.from_pretrained(
    MODEL_NAME, num_labels=len(id2label), id2label=id2label, label2id=label2id, seq_classif_dropout=0.35
).to(device)
optimizer = AdamW(intent_classifier.parameters(), lr=2e-5)

num_update_steps_per_epoch = len(train_dataloader)
num_training_steps = NUM_TRAIN_EPOCHS * num_update_steps_per_epoch

lr_scheduler = get_scheduler(
    "linear",
    optimizer=optimizer,
    num_warmup_steps=0,
    num_training_steps=num_training_steps,
)

signature = ModelSignature(
    inputs=Schema([ColSpec("string", "sentence_text")]),
    outputs=Schema([ColSpec("string", "intent_type"), ColSpec("float", "intent_score")]),
)

# COMMAND ----------

best_test_accuracy = 0.0

metrics = {
    "epoch": [],
    "train_loss": [],
    "test_loss": [],
    "train_accuracy": [],
    "test_accuracy": [],
}
mlflow.set_experiment(experiment_name)
with mlflow.start_run() as run:
    for epoch in range(NUM_TRAIN_EPOCHS):
        start_time = time.time()

        # Training
        train_loss, train_accuracy = train_model(intent_classifier, train_dataloader, optimizer, lr_scheduler, device)
        # Evaluation
        test_loss, test_accuracy = evaluate_model(intent_classifier, test_dataloader, device)

        end_time = time.time()
        epoch_mins, epoch_secs = epoch_time(start_time, end_time)

        if test_accuracy > best_test_accuracy:
            intent_classifier.save_pretrained(MODEL_PATH)  # We only save the best model
            tokenizer.save_pretrained(MODEL_PATH)
            model_info = mlflow.pyfunc.log_model(
                artifact_path=f"{MODEL_PATH.split('/')[-1]}/epoch_{epoch+1}",
                python_model=AutoModelForIntentClassification(),
                artifacts={"model_path": MODEL_PATH},
                signature=signature,
            )
            best_test_accuracy = test_accuracy

        metrics["epoch"].append(epoch)
        metrics["train_loss"].append(train_loss)
        metrics["test_loss"].append(test_loss)
        metrics["train_accuracy"].append(train_accuracy)
        metrics["test_accuracy"].append(test_accuracy)

        print(f"Epoch: {epoch+1:02} | Epoch Time: {epoch_mins}m {epoch_secs}s")
        print(f"\tTrain Loss: {train_loss:.3f}")
        print(f"\tTest Loss: {test_loss:.3f}")
        print(f"\tTrain Accuracy: {train_accuracy:.3f}")
        print(f"\tTest Accuracy: {test_accuracy:.3f}")
    mlflow.register_model(
        model_uri=model_info.model_uri,
        name=REGISTERED_MODEL_NAME,
    )

# COMMAND ----------

# A quick test to check how the model performs once trained
ds_val_sample = ds_val[700:705]
sample_test = {
    "id": ds_val_sample["id"],
    "intent_type": ds_val_sample["intent_type"],
    "sentence_text": ds_val_sample["sentence_text"],
    "labels": ds_val_sample["label"],
    "input_ids": ds_val_sample["input_ids"],
    "attention_mask": ds_val_sample["attention_mask"],
}
predictions, labels = batch_inference(
    intent_classifier,
    DataLoader(
        Dataset.from_dict(sample_test),
        collate_fn=data_collator,
        batch_size=len(sample_test["labels"]),
    ),
    device,
)
print(f"intent_type : {sample_test['intent_type']}")
print(f"sentence_text : {sample_test['sentence_text']}")
print(f"labels : {sample_test['labels']}")
print(f"predictions : {predictions}")
print(f"labels mapped : {[id2label[label] for label in labels]}")
print(f"predictions mapped : {[id2label[pred] for pred in predictions]}")

# COMMAND ----------

# metrics
predictions, labels = batch_inference(intent_classifier, validation_dataloader, device)

predictions_mapped = [id2label[pred] for pred in predictions]
labels_mapped = [id2label[label] for label in labels]

metrics = evaluate_classification(labels=labels_mapped, predictions=predictions_mapped)

# COMMAND ----------

class_report_dict = metrics["classification_report"]

plot_metrics("precision", class_report_dict)
plot_metrics("recall", class_report_dict)
plot_metrics("f1-score", class_report_dict)
