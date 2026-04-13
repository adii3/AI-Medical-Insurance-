import pandas as pd


def engineer_features(df):
    data = df.copy()
    data["Age_x_BMI"] = data["age"] * data["bmi"]
    data["Smoker_x_Hosp"] = data["smoker_status"].astype(int) * data["recent_hospitalizations"]
    data["BMI_Category"] = pd.cut(
        data["bmi"],
        [0, 18.5, 25, 30, 55],
        labels=[0, 1, 2, 3],
    ).astype(float)
    data["Age_Group"] = pd.cut(
        data["age"],
        [0, 30, 45, 60, 100],
        labels=[0, 1, 2, 3],
    ).astype(float)
    return data


def engineer_single_row(row: dict) -> dict:
    profile = row.copy()
    profile["Age_x_BMI"] = profile["age"] * profile["bmi"]
    profile["Smoker_x_Hosp"] = int(profile["smoker_status"]) * profile["recent_hospitalizations"]
    profile["BMI_Category"] = (
        0 if profile["bmi"] < 18.5 else
        1 if profile["bmi"] < 25 else
        2 if profile["bmi"] < 30 else 3
    )
    profile["Age_Group"] = (
        0 if profile["age"] < 30 else
        1 if profile["age"] < 45 else
        2 if profile["age"] < 60 else 3
    )
    return profile
