import numpy as np
from sklearn.metrics import accuracy_score, f1_score

print("Running Ensemble (MLP + XGBoost)...")

# Get MLP probabilities on test set
mlp_probs = []
model.eval()
with torch.no_grad():
    for Xb, yb in test_iter:
        probs = torch.nn.functional.softmax(model(Xb), dim=1)
        mlp_probs.append(probs.cpu().numpy())
mlp_flat = np.vstack(mlp_probs)  # shape: (70912, 2)

# ✅ Fix: trim XGBoost to exactly match MLP sample count
n = mlp_flat.shape[0]               # 70912 — use this as the master size
X_test_aligned = X_test[:n]
y_test_aligned = y_test[:n]

xgb_probs = xgb_model.predict_proba(X_test_aligned)  # now also (70912, 2)

# Average the two model probabilities
ensemble_probs = (mlp_flat + xgb_probs) / 2
ensemble_preds = np.argmax(ensemble_probs, axis=1)

ens_acc = accuracy_score(y_test_aligned, ensemble_preds)
ens_f1  = f1_score(y_test_aligned, ensemble_preds, average='weighted')

ens_log = [
    "\n" + "="*60,
    "ENSEMBLE (MLP + XGBoost) RESULTS",
    "="*60,
    f"Test Accuracy : {ens_acc:.4f}",
    f"F1 Score      : {ens_f1:.4f}",
    "\n" + "="*60,
    "MODEL COMPARISON SUMMARY",
    "="*60,
    f"MLP      -> Acc: {float(test_acc):.4f} | F1: {mlp_f1:.4f}",
    f"XGBoost  -> Acc: {xgb_acc:.4f} | F1: {xgb_f1:.4f}",
    f"Ensemble -> Acc: {ens_acc:.4f} | F1: {ens_f1:.4f}",
]
for line in ens_log:
    print(line)

with open(logs_dir, 'a') as f:
    f.write('\n'.join(ens_log))
print(f"\n✅ Ensemble log appended to {logs_dir}")