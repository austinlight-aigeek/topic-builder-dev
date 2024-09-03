from typing import Any

import torch
from datasets import Dataset
from datasets.features import ClassLabel
from torch import nn
from torch.utils.data import DataLoader
from transformers import AutoTokenizer, DataCollatorWithPadding


def tokenize(
    dataset: Dataset,
    tokenizer: AutoTokenizer,
    col_to_tokenize: str,
    tokenizer_kwargs: dict[str, str | bool | int] | None = None,
) -> Dataset:
    def tokenize_function(example, col_to_tokenize):
        if tokenizer_kwargs:
            return tokenizer(example[col_to_tokenize], **tokenizer_kwargs)
        return tokenizer(example[col_to_tokenize])

    return dataset.map(
        tokenize_function,
        batched=True,
        fn_kwargs={"col_to_tokenize": col_to_tokenize},
    )


def cast_cat_col(dataset: Dataset, cat_col: str, labels: list[str]):
    class_labels = ClassLabel(num_classes=len(labels), names=labels)
    return dataset.cast_column(cat_col, class_labels)


def batch_inference(model: nn.Module, iterator: DataLoader, device: torch.device) -> tuple[list[int], list[int]]:
    predictions = []
    labels = []

    model.eval()
    for batch in iterator:
        with torch.no_grad():
            outputs = model(
                input_ids=batch["input_ids"].to(device),
                attention_mask=batch["attention_mask"].to(device),
                labels=batch["labels"].to(device),
            )

        predictions += outputs.logits.argmax(dim=-1).detach().cpu().clone().numpy().tolist()
        labels += batch["labels"].detach().cpu().clone().numpy().tolist()

    return predictions, labels


class CustomDataCollatorWithPadding(DataCollatorWithPadding):
    def __call__(self, features: list[dict[str, Any]]) -> dict[str, Any]:
        features_without_padding = {"id": [], "intent_type": [], "sentence_text": []}
        for feature in features:
            features_without_padding["id"].append(feature.pop("id"))
            features_without_padding["intent_type"].append(feature.pop("intent_type"))
            features_without_padding["sentence_text"].append(feature.pop("sentence_text"))

        batch = super().__call__(features)
        batch["id"] = features_without_padding["id"]
        batch["intent_type"] = features_without_padding["intent_type"]
        batch["sentence_text"] = features_without_padding["sentence_text"]

        return batch
