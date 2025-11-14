import pandas as pd
from sklearn.preprocessing import LabelEncoder
import pickle

# Load training dataset
df = pd.read_csv("Training.csv")

# Encode target labels
le = LabelEncoder()
df['prognosis'] = le.fit_transform(df['prognosis'])

# Save the label encoder
with open("label_encoder.pkl", "wb") as f:
    pickle.dump(le, f)

print("✅ label_encoder.pkl created successfully.")
