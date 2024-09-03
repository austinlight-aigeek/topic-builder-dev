import pandas as pd
import torch
from datasets import Dataset
from mlflow import pyfunc
from torch.nn import functional
from torch.utils.data import DataLoader
from transformers import (
    AutoModelForSequenceClassification,
    AutoTokenizer,
    DataCollatorWithPadding,
)

INFERENCE_BATCH = 128
INTENT_CLASS_LABELS = [
    "statement",
    "request",
    "action-request",
    "information-request",
    "yes-no-question",
]


class AutoModelForIntentClassification(pyfunc.PythonModel):
    def load_context(self, context):
        self.device = torch.device("cuda") if torch.cuda.is_available() else torch.device("cpu")
        self.id2label = dict(enumerate(INTENT_CLASS_LABELS))
        self.label2id = {v: k for k, v in self.id2label.items()}

        self.tokenizer = AutoTokenizer.from_pretrained(context.artifacts["model_path"])
        self.model = AutoModelForSequenceClassification.from_pretrained(
            context.artifacts["model_path"],
            num_labels=len(self.id2label),
            id2label=self.id2label,
            label2id=self.label2id,
        ).to(self.device)

    def predict(self, context, model_input):  # noqa: ARG002
        data_loader = self.__get_data_loader(model_input[model_input.columns[0]].to_list())
        predictions_labels = []
        scores = []
        self.model.eval()
        for batch in data_loader:
            with torch.no_grad():
                logits = self.model(
                    input_ids=batch["input_ids"].to(self.device),
                    attention_mask=batch["attention_mask"].to(self.device),
                ).logits
            predictions = logits.argmax(dim=-1).detach().cpu().clone().numpy().tolist()
            predictions_labels += [self.id2label[pred] for pred in predictions]
            scores += torch.max(functional.softmax(logits, dim=-1), axis=-1)[0].detach().cpu().clone().numpy().tolist()

            torch.cuda.empty_cache()

        return pd.DataFrame({"intent_type": predictions_labels, "intent_score": scores})

    def __get_data_loader(self, sentences: list[str]):
        def tokenize(example, col_to_tokenize):
            return self.tokenizer(example[col_to_tokenize], truncation=True)

        ds = Dataset.from_dict({"sentence_text": sentences})
        ds = ds.map(
            tokenize,
            batched=True,
            fn_kwargs={"col_to_tokenize": "sentence_text"},
            remove_columns="sentence_text",
        )
        ds.set_format(type="torch", output_all_columns=True)

        return DataLoader(
            ds,
            collate_fn=DataCollatorWithPadding(tokenizer=self.tokenizer),
            batch_size=INFERENCE_BATCH,
            shuffle=False,
            pin_memory=True,
            num_workers=4,
        )
