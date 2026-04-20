
from sklearn.metrics import classification_report, roc_auc_score, roc_curve
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
import shap
import xgboost as xgb
#importing packages
from constants import FEATURE_COLS
from data_generator import load_or_generate_data
from feature_engineering import engineer_features


def train_model():
    df = load_or_generate_data()
    df = engineer_features(df)
    cat_cols = ["sex", "region", "subscription_tier", "tenant_company"]
    le_map = {}

    for column in cat_cols:
        encoder = LabelEncoder()
        df[f"{column}_enc"] = encoder.fit_transform(df[column].astype(str))
        le_map[column] = encoder

    X = df[FEATURE_COLS].astype(float)
    y = df["high_risk"].astype(int)

    X_tr, X_te, y_tr, y_te = train_test_split(
        X,
        y,
        test_size=0.20,
        random_state=42,
        stratify=y,
    )

    model = xgb.XGBClassifier(
        n_estimators=250,
        max_depth=5,
        learning_rate=0.05,
        subsample=0.8,
        colsample_bytree=0.8,
        eval_metric="logloss",
        random_state=42,
        n_jobs=-1,
    )
    model.fit(X_tr, y_tr)

    explainer = None
    shap_error = None
    try:
        explainer = shap.TreeExplainer(model)
        shap_vals = explainer.shap_values(X_te)
    except Exception as exc:  # pragma: no cover - library compatibility fallback
        shap_error = str(exc)
        booster = model.get_booster()
        dtest = xgb.DMatrix(X_te, feature_names=list(X_te.columns))
        contribs = booster.predict(dtest, pred_contribs=True)
        shap_vals = contribs[:, :-1]
    y_prob = model.predict_proba(X_te)[:, 1]
    y_pred = (y_prob >= 0.5).astype(int)
    report = classification_report(y_te, y_pred, output_dict=True)
    rocauc = roc_auc_score(y_te, y_prob)
    fpr, tpr, _ = roc_curve(y_te, y_prob)

    return {
        "model": model,
        "explainer": explainer,
        "le_map": le_map,
        "X_te": X_te,
        "y_te": y_te,
        "y_prob": y_prob,
        "y_pred": y_pred,
        "shap_vals": shap_vals,
        "shap_error": shap_error,
        "report": report,
        "roc_auc": rocauc,
        "fpr": fpr,
        "tpr": tpr,
        "df": df,
    }
