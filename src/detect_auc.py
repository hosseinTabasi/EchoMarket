"""DEV-only TF-IDF logistic AUC. Author: Hossein Tabasi."""
from __future__ import annotations

def fit_auc(real_dev, real_test, synth_dev, synth_test):
    result = {"method": "tfidf-logistic", "n_real_dev": len(real_dev),
              "n_synth_dev": len(synth_dev), "n_real_test": len(real_test),
              "n_synth_test": len(synth_test), "dev_cv_auc": "N/A",
              "test_auc": "N/A", "dev_note": "", "test_note": ""}
    try:
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.linear_model import LogisticRegression
        from sklearn.metrics import roc_auc_score
        from sklearn.model_selection import StratifiedKFold, cross_val_score
        import numpy as np
    except Exception as exc:
        result["dev_note"] = "sklearn unavailable (%s)" % exc
        result["test_note"] = result["dev_note"]
        return result
    if len(real_dev) < 8 or len(synth_dev) < 8:
        result["dev_note"] = "too few labeled reals n=%s synth n=%s" % (len(real_dev), len(synth_dev))
        return result
    rng = np.random.RandomState(20260311)
    synth_fit = synth_dev
    if len(synth_fit) > 8000:
        idx = rng.choice(len(synth_fit), size=8000, replace=False)
        synth_fit = [synth_fit[i] for i in idx]
    texts = real_dev + synth_fit
    y = np.array([0] * len(real_dev) + [1] * len(synth_fit))
    vec = TfidfVectorizer(min_df=1, ngram_range=(1, 2), max_features=4000)
    x = vec.fit_transform(texts)
    clf = LogisticRegression(max_iter=400, class_weight="balanced")
    n0 = int((y == 0).sum())
    n1 = int((y == 1).sum())
    n_splits = max(2, min(5, n0, n1))
    cv = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=20260311)
    scores = cross_val_score(clf, x, y, cv=cv, scoring="roc_auc")
    result["dev_cv_auc"] = float(scores.mean())
    result["dev_note"] = "n_real=%s n_synth_used=%s cv_splits=%s" % (len(real_dev), len(synth_fit), n_splits)
    clf.fit(x, y)
    if len(real_test) < 8 or len(synth_test) < 8:
        result["test_note"] = "too few labeled reals n=%s synth n=%s; never fit on E09/E10" % (len(real_test), len(synth_test))
        return result
    synth_te = synth_test
    if len(synth_te) > 8000:
        idx = rng.choice(len(synth_te), size=8000, replace=False)
        synth_te = [synth_te[i] for i in idx]
    xt = vec.transform(real_test + synth_te)
    yt = __import__('numpy').array([0] * len(real_test) + [1] * len(synth_te))
    pr = clf.predict_proba(xt)
    classes = list(clf.classes_)
    col = classes.index(1) if 1 in classes else -1
    from sklearn.metrics import roc_auc_score as _auc
    result["test_auc"] = float(_auc(yt, pr[:, col]))
    result["test_note"] = "n_real=%s n_synth_used=%s; model fit on DEV only" % (len(real_test), len(synth_te))
    return result
