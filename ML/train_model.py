"""
import pandas as pd
import joblib
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression

# -----------------------------
# LOAD DATA
# -----------------------------
data = pd.read_csv("ML/heart.csv")

# -----------------------------
# FIX CATEGORICAL VALUES
# -----------------------------

# sex: Male/Female → 1/0
data['sex'] = data['sex'].map({'Male': 1, 'Female': 0})

# chest pain type → numeric mapping
cp_map = {
    'Typical Angina': 0,
    'Atypical Angina': 1,
    'Non-anginal Pain': 2,
    'Asymptomatic': 3
}
data['chest_pain_type'] = data['chest_pain_type'].map(cp_map)

# exercise induced angina: Yes/No → 1/0
data['exercise_induced_angina'] = data['exercise_induced_angina'].map({
    'Yes': 1,
    'No': 0
})

# fasting blood sugar: True/False → 1/0
data['fasting_blood_sugar'] = data['fasting_blood_sugar'].map({
    'True': 1,
    'False': 0
})

# -----------------------------
# NUMERIC CONVERSION (SAFETY)
# -----------------------------
numeric_cols = [
    'age', 'Max_heart_rate', 'resting_blood_pressure',
    'oldpeak', 'vessels_colored_by_flourosopy'
]

for col in numeric_cols:
    data[col] = pd.to_numeric(data[col], errors='coerce').fillna(0)

# -----------------------------
# FEATURE ENGINEERING
# -----------------------------

# stress from oldpeak
data['stress'] = data['oldpeak'].apply(
    lambda x: 0 if x < 1 else 1 if x < 2 else 2
)

# genetics from vessels
data['genetics'] = data['vessels_colored_by_flourosopy'].apply(
    lambda x: 1 if x > 0 else 0
)

# smoking proxy
data['smoking'] = data['fasting_blood_sugar']

# -----------------------------
# FINAL 10 FEATURES
# -----------------------------
X = data[[
    'age',
    'sex',
    'chest_pain_type',
    'Max_heart_rate',
    'resting_blood_pressure',
    'smoking',
    'exercise_induced_angina',
    'fasting_blood_sugar',
    'stress',
    'genetics'
]]

y = data['target']

print("✅ Features used:", X.columns.tolist())
print("✅ Feature count:", X.shape[1])
print("✅ Data types:\n", X.dtypes)

# -----------------------------
# TRAIN TEST SPLIT
# -----------------------------
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

# -----------------------------
# SCALING
# -----------------------------
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

# -----------------------------
# TRAIN MODEL
# -----------------------------
model = LogisticRegression(max_iter=1000)
model.fit(X_train_scaled, y_train)

# -----------------------------
# SAVE MODEL
# -----------------------------
joblib.dump(model, "ML/heart_model.pkl")
joblib.dump(scaler, "ML/scaler.pkl")

print("🎉 Model trained successfully with 10 numeric features")




import pandas as pd
import joblib
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.impute import SimpleImputer

# -----------------------------
# LOAD DATA
# -----------------------------
data = pd.read_csv("ML/heart.csv")

# -----------------------------
# FIX CATEGORICAL VALUES
# -----------------------------

# sex: Male/Female → 1/0
data['sex'] = data['sex'].map({'Male': 1, 'Female': 0})

# chest pain type → numeric mapping
cp_map = {
    'Typical Angina': 0,
    'Atypical Angina': 1,
    'Non-anginal Pain': 2,
    'Asymptomatic': 3
}
data['chest_pain_type'] = data['chest_pain_type'].map(cp_map)

# exercise induced angina: Yes/No → 1/0
data['exercise_induced_angina'] = data['exercise_induced_angina'].map({
    'Yes': 1,
    'No': 0
})

# fasting blood sugar: True/False → 1/0
data['fasting_blood_sugar'] = data['fasting_blood_sugar'].map({
    'True': 1,
    'False': 0
})

# -----------------------------
# NUMERIC CONVERSION (SAFETY)
# -----------------------------
numeric_cols = [
    'age', 'Max_heart_rate', 'resting_blood_pressure',
    'oldpeak', 'vessels_colored_by_flourosopy'
]

for col in numeric_cols:
    data[col] = pd.to_numeric(data[col], errors='coerce')

# -----------------------------
# FEATURE ENGINEERING
# -----------------------------

# stress from oldpeak
data['stress'] = data['oldpeak'].apply(lambda x: 0 if x < 1 else 1 if x < 2 else 2)

# genetics from vessels
data['genetics'] = data['vessels_colored_by_flourosopy'].apply(lambda x: 1 if x > 0 else 0)

# smoking proxy from fasting_blood_sugar
data['smoking'] = data['fasting_blood_sugar']

# diet placeholder (if not in dataset, fill with 0)
if 'diet' not in data.columns:
    data['diet'] = 0

# -----------------------------
# FINAL 10 FEATURES IN DB ORDER
# -----------------------------
X = data[[
    'age',                    # age
    'sex',                    # sex
    'chest_pain_type',        # chest pain
    'Max_heart_rate',         # heart rate
    'resting_blood_pressure', # bp
    'smoking',                # smoking
    'diet',                   # diet/eating habits
    'exercise_induced_angina',# exercise
    'stress',                 # stress
    'genetics'                # genetics
]]

y = data['target']

# -----------------------------
# HANDLE MISSING VALUES
# -----------------------------
imputer = SimpleImputer(strategy='mean')
X = pd.DataFrame(imputer.fit_transform(X), columns=X.columns)

print("✅ Features used:", X.columns.tolist())
print("✅ Feature count:", X.shape[1])
print("✅ Data types:\n", X.dtypes)

# -----------------------------
# TRAIN TEST SPLIT
# -----------------------------
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

# -----------------------------
# SCALING
# -----------------------------
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

# -----------------------------
# TRAIN MODEL
# -----------------------------
model = LogisticRegression(max_iter=1000)
model.fit(X_train_scaled, y_train)

# -----------------------------
# SAVE MODEL & SCALER
# -----------------------------
joblib.dump(model, "ML/heart_model.pkl")
joblib.dump(scaler, "ML/scaler.pkl")

print("🎉 Model trained successfully with 10 numeric features")

"""
import pandas as pd
import joblib
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.impute import SimpleImputer

# -----------------------------
# LOAD DATA
# -----------------------------
data = pd.read_csv("ML/heart.csv")  # replace with your dataset path

# -----------------------------
# FIX CATEGORICAL VALUES
# -----------------------------

# sex: Male/Female → 1/0
data['sex'] = data['sex'].map({'Male': 1, 'Female': 0}).fillna(0)

# chest pain type → numeric mapping
cp_map = {
    'Typical Angina': 0,
    'Atypical Angina': 1,
    'Non-anginal Pain': 2,
    'Asymptomatic': 3
}
data['chest_pain_type'] = data['chest_pain_type'].map(cp_map).fillna(0)

# exercise induced angina: Yes/No → 1/0
data['exercise_induced_angina'] = data['exercise_induced_angina'].map({
    'Yes': 1,
    'No': 0
}).fillna(0)

# fasting blood sugar: True/False → 1/0
data['fasting_blood_sugar'] = data['fasting_blood_sugar'].map({
    'True': 1,
    'False': 0
}).fillna(0)

# -----------------------------
# NUMERIC CONVERSION (SAFETY)
# -----------------------------
numeric_cols = [
    'age', 'Max_heart_rate', 'resting_blood_pressure',
    'oldpeak', 'vessels_colored_by_flourosopy'
]

for col in numeric_cols:
    data[col] = pd.to_numeric(data[col], errors='coerce').fillna(0)

# -----------------------------
# FEATURE ENGINEERING
# -----------------------------

# stress from oldpeak
data['stress'] = data['oldpeak'].apply(lambda x: 0 if x < 1 else 1 if x < 2 else 2)

# genetics from vessels
data['genetics'] = data['vessels_colored_by_flourosopy'].apply(lambda x: 1 if x > 0 else 0)

# smoking proxy (fill missing values)
data['smoking'] = data.get('fasting_blood_sugar', 0)
data['smoking'] = data['smoking'].fillna(0)

# diet placeholder (if not present, fill with 0)
if 'diet' not in data.columns:
    data['diet'] = 0
data['diet'] = data['diet'].fillna(0)

# -----------------------------
# FINAL 10 FEATURES (ORDER MATCHES DB)
# -----------------------------
X = data[[
    'age',                      # age
    'sex',                      # sex
    'chest_pain_type',          # chest pain
    'Max_heart_rate',           # heart rate
    'resting_blood_pressure',   # bp
    'smoking',                  # smoking
    'diet',                     # diet / eating habits
    'exercise_induced_angina',  # exercise
    'stress',                   # stress
    'genetics'                  # genetics
]]

y = data['target']

# -----------------------------
# HANDLE MISSING VALUES
# -----------------------------
imputer = SimpleImputer(strategy='mean')
X = pd.DataFrame(imputer.fit_transform(X), columns=X.columns)

print("✅ Features used:", X.columns.tolist())
print("✅ Feature count:", X.shape[1])
print("✅ Data types:\n", X.dtypes)

# -----------------------------
# TRAIN TEST SPLIT
# -----------------------------
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

# -----------------------------
# SCALING
# -----------------------------
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

# -----------------------------
# TRAIN MODEL
# -----------------------------
model = LogisticRegression(max_iter=1000)
model.fit(X_train_scaled, y_train)

# -----------------------------
# SAVE MODEL & SCALER
# -----------------------------
joblib.dump(model, "ML/heart_model.pkl")
joblib.dump(scaler, "ML/scaler.pkl")

print("🎉 Model trained successfully with 10 numeric features")
































































"""
# Load dataset
data = pd.read_csv("ML/heart.csv")

# Encode categorical columns
label_encoder = LabelEncoder()

for col in data.columns:
    if data[col].dtype == 'object':
        data[col] = label_encoder.fit_transform(data[col])

# Split features & target
X = data.drop("target", axis=1)
y = data["target"]

# Scaling
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

# Train-test split
X_train, X_test, y_train, y_test = train_test_split(
    X_scaled, y, test_size=0.2, random_state=42
)

# Train model
model = LogisticRegression(max_iter=1000)
model.fit(X_train, y_train)

# Save model & scaler
joblib.dump(model, "ML/heart_model.pkl")
joblib.dump(scaler, "ML/scaler.pkl")

print("✅ Model trained successfully")
"""