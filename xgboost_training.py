from xgboost import XGBClassifier
from sklearn.metrics import accuracy_score, f1_score
import joblib

print("Loading data for XGBoost...")
X_train, X_val, X_test, y_train, y_val, y_test = load_raw_data()

xgb_model = XGBClassifier(
    n_estimators=300,
    max_depth=6,
    learning_rate=0.05,
    subsample=0.8,
    colsample_bytree=0.8,
    use_label_encoder=False,
    eval_metric='logloss',
    random_state=42
)

print("Training XGBoost...")
xgb_model.fit(X_train, y_train,
              eval_set=[(X_val, y_val)],
              verbose=50)

joblib.dump(xgb_model, '/kaggle/working/xgb_model.pkl')

xgb_preds = xgb_model.predict(X_test)
xgb_acc   = accuracy_score(y_test, xgb_preds)
xgb_f1    = f1_score(y_test, xgb_preds, average='weighted')

xgb_log = [
    "\n" + "="*60,
    "XGBOOST RESULTS",
    "="*60,
    f"Test Accuracy : {xgb_acc:.4f}",
    f"F1 Score      : {xgb_f1:.4f}",
]
for line in xgb_log:
    print(line)

with open(logs_dir, 'a') as f:
    f.write('\n'.join(xgb_log))
print(f"\n✅ XGBoost log appended to {logs_dir}")