import sys
sys.path.insert(0, '/kaggle/working')

import torch
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
from model_utils import *
from sklearn.metrics import confusion_matrix, f1_score

device    = torch.device("cuda" if torch.cuda.is_available() else "cpu")
plots_dir = Path('/kaggle/working')
logs_dir  = Path('/kaggle/working/training_log.txt')
model_dir = Path('/kaggle/working/best_model.pth')

print(f"Using device: {device}")

batch_size = 128
train_iter, val_iter, test_iter = load_data_cdc_diabetes(batch_size, device)
X_sample, y_sample = next(iter(train_iter))
print("Input shape:", X_sample.size())

model = DiabetesClassifier(in_channels=21, out_channels=2)
model.apply(init_weights)
model.to(device)

loss_fn    = torch.nn.CrossEntropyLoss()
optimizer  = torch.optim.AdamW(model.parameters(), lr=0.00677174682597258, weight_decay=3.103759723739499e-05)
early_stop = EarlyStopping(wait_epoch=150, index=True)
losses, train_accs, val_accs = [], [], []

log_lines = ["=" * 60, "MLP TRAINING LOG", "=" * 60]

num_epochs = 200
for epoch in range(num_epochs):
    msg = f'\nEpoch {epoch+1}/{num_epochs}'
    print(msg)
    log_lines.append(msg)
    model.train()
    for Xb, yb in train_iter:
        out = model(Xb); l = loss_fn(out, yb)
        optimizer.zero_grad(); l.backward(); optimizer.step()
        losses.append(float(l))
    model.eval()
    with torch.no_grad():
        train_acc = evaluate_metric(model, train_iter, correct)
        val_acc   = evaluate_metric(model, val_iter,   correct)
        train_accs.append(train_acc); val_accs.append(val_acc)
        update = (f'  Loss: {float(l):.4f} | Train Acc: {train_acc:.4f} | Val Acc: {val_acc:.4f}')
        print(update); log_lines.append(update)
        early_stop(val_acc, model, epoch+1)
        if early_stop.early_stop:
            stop_msg = f"  Early stopping at epoch {epoch+1}. Best val acc: {early_stop.max_val_acc:.4f}"
            print(stop_msg); log_lines.append(stop_msg); break
    best_msg = f'  Best val acc so far: {early_stop.max_val_acc:.4f} at epoch {early_stop.prime_epoch}'
    print(best_msg); log_lines.append(best_msg)

# Test evaluation
model.load_state_dict(torch.load(model_dir, map_location=device))
model.eval()
with torch.no_grad():
    test_acc = evaluate_metric(model, test_iter, correct)

preds_labels, actual_labels = [], []
with torch.no_grad():
    for Xb, yb in test_iter:
        _, predicted = torch.max(model(Xb), 1)
        preds_labels.extend(predicted.cpu().numpy())
        actual_labels.extend(yb.cpu().numpy())

mlp_f1 = f1_score(actual_labels, preds_labels, average='weighted')
test_msg = [
    "\n" + "="*60,
    "MLP FINAL RESULTS",
    "="*60,
    f"Test Accuracy : {float(test_acc):.4f}",
    f"F1 Score      : {mlp_f1:.4f}",
    f"Best Val Acc  : {early_stop.max_val_acc:.4f} at epoch {early_stop.prime_epoch}",
]
for line in test_msg:
    print(line); log_lines.append(line)

with open(logs_dir, 'w') as f:
    f.write('\n'.join(log_lines))
print(f"\n✅ MLP log saved to {logs_dir}")