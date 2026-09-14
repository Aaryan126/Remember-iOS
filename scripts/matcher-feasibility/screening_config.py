"""Decisions fixed before outcomes; Stage 2 execution requires new authorization."""


def folds():
    # Interleaving makes each outer fold cover the whole training-library range.
    all_ids = [f"mf{i:02}" for i in range(1, 19)]
    output = []
    for index in range(3):
        evaluation = all_ids[index::3]
        remaining = [v for v in all_ids if v not in evaluation]
        calibration = [remaining[i] for i in (index, index+4, index+8)]
        fitting = [v for v in remaining if v not in calibration]
        output.append({"id": f"fold-{index+1}", "fit": fitting, "calibration": calibration,
                       "evaluation": evaluation,
                       "hybridInnerValidation": [fitting[i::3] for i in range(3)]})
    return {"schemaVersion": 1, "folds": output, "testAccess": False,
            "threshold": {"minimumPrecision": .95, "minimumAcceptedKnownPairs": 30,
                          "objective": "macro-library recall", "ties": ["higher precision", "higher threshold"],
                          "nonqualifying": "abstain; diagnostic PR curve separately"}}


def trials():
    configurations = [
        {"id": "A1", "family": "simple", "model": "logistic", "C": 1, "features": "six"},
        {"id": "A2", "family": "simple", "model": "logistic", "C": 1, "features": "six+identifiers"},
        {"id": "A3", "family": "simple", "model": "gradient_boosting", "estimators": 100, "depth": 2, "learningRate": .05, "features": "six+identifiers"},
        {"id": "B1", "family": "embedding_head", "model": "logistic", "C": .1, "features": "vector_comparisons+six+identifiers"},
        {"id": "B2", "family": "embedding_head", "model": "mlp", "hiddenUnits": 32},
        {"id": "B3", "family": "embedding_head", "model": "mlp", "hiddenUnits": 64},
        {"id": "C1", "family": "minilm", "trainable": "head", "backboneLearningRate": 0},
        {"id": "C2", "family": "minilm", "trainable": "head+last_two_layers", "backboneLearningRate": 1e-5},
        {"id": "C3", "family": "minilm", "trainable": "all", "backboneLearningRate": 5e-6},
    ]
    configurations += [{"id": f"D{i}", "family": "hybrid", "base": f"C{i}", "model": "logistic", "C": 1,
                        "features": "six+identifiers+cross_fitted_base_same_logit"} for i in range(1,4)]
    return {"schemaVersion": 1, "authorizedToExecute": False, "configurations": configurations,
        "control": {"model": "multinomial_logistic", "C": 10, "classWeight": "balanced", "features": "six"},
        "defaults": {"seed": 17, "confirmationSeeds": [17,29,41], "binaryPositive": "same",
            "binaryNegative": ["related","unrelated"], "uncertain": "excluded from loss; reported separately",
            "classWeight": None, "logisticSolver": "lbfgs", "maxIterations": 2000,
            "mlp": {"features": "vector_comparisons+six+identifiers", "activation": "relu", "dropout": .2,
                    "optimizer": "AdamW", "learningRate": .001, "weightDecay": .01, "epochs": 20},
            "minilm": {"epochs": 3, "headLearningRate": .001, "weightDecay": .01,
                       "warmupFraction": .1, "schedule": "linear decay", "maxLength": 512,
                       "optimizer": "AdamW", "effectiveBatch": 16, "microbatch": 8},
            "vectorComparisons": "abs(a-b), a*b for contextual and sentence vectors, kept in distinct spaces",
            "pairDirections": "average probability vectors for text models; symmetric features otherwise",
            "fitOnlyPreprocessing": True, "textFeatures": "reuse frozen six-feature definitions; refit TF-IDF/scaler per fit fold"},
        "identifierFeatures": {"tokens": "case-sensitive code tokens containing a letter and a digit or an internal hyphen; exclude standalone dates/times; no source record IDs",
            "measurements": ["token-set Jaccard", "both-have-codes-and-disjoint", "either-missing-code", "both-missing-code"],
            "policy": "clues only; never a hard join prohibition"},
        "hybrid": "inner three-fold base predictions within nine fit libraries; combiner fit on OOF scores; base refit on all nine; calibrate on separate three; evaluate on six",
        "ranking": ["number of qualifying outer folds", "pooled macro-library recall", "pooled precision", "lower deployment complexity A then B then C then D", "trial ID"],
        "diagnosticFallback": "same-class average precision; research lead only, never qualification",
        "confirmation": "at most two families, best trial each; fit on 18 training libraries; calibrate/report on six development libraries; stochastic seeds17/29/41; no final test",
        "finalQualification": {"minimumPrecision": .95, "minimumAcceptedKnownPairs": 30,
                               "macroRecallGain": .05, "maximumPrecisionDrop": .01},
        "stage2BlockedUntil": "Stage1 checkpoint review and explicit user continuation; new manifest binds Stage2 implementation"}
