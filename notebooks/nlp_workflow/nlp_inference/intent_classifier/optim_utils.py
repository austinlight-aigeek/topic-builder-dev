import numpy as np
import torch
from torch import nn
from torch.utils.data import DataLoader

MAX_GRAD_NORM = 1


def train_model(
    model: nn.Module,
    iterator: DataLoader,
    optimizer: torch.optim,
    lr_scheduler: torch.optim.lr_scheduler,
    device: torch.device,
) -> tuple[float, float]:
    total = 0.0
    corrects = 0.0
    epoch_loss = 0.0

    model.train()
    for batch in iterator:
        outputs = model(
            input_ids=batch["input_ids"].to(device),
            attention_mask=batch["attention_mask"].to(device),
            labels=batch["labels"].to(device),
        )
        loss = outputs.loss
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), MAX_GRAD_NORM)

        optimizer.step()
        lr_scheduler.step()
        optimizer.zero_grad()

        predictions = outputs.logits.argmax(dim=-1).detach().cpu().clone().numpy()
        labels = batch["labels"].detach().cpu().clone().numpy()

        total += len(predictions)
        corrects += np.sum(labels == predictions)

        epoch_loss += loss.item()

    return epoch_loss / len(iterator), corrects / total


def evaluate_model(model: nn.Module, iterator: DataLoader, device: torch.device) -> tuple[float, float]:
    total = 0.0
    corrects = 0.0
    epoch_loss = 0.0

    model.eval()
    for batch in iterator:
        with torch.no_grad():
            outputs = model(
                input_ids=batch["input_ids"].to(device),
                attention_mask=batch["attention_mask"].to(device),
                labels=batch["labels"].to(device),
            )
            loss = outputs.loss.item()

        predictions = outputs.logits.argmax(dim=-1).detach().cpu().clone().numpy()
        labels = batch["labels"].detach().cpu().clone().numpy()

        epoch_loss += loss

        total += len(predictions)
        corrects += np.sum(labels == predictions)

    return epoch_loss / len(iterator), corrects / total


def epoch_time(start_time, end_time):
    elapsed_time = end_time - start_time
    elapsed_mins = int(elapsed_time / 60)
    elapsed_secs = int(elapsed_time - (elapsed_mins * 60))
    return elapsed_mins, elapsed_secs
