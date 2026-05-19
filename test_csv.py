import pandas as pd

file_path = './inst/survey_app_data - entries.csv'

data = pd.read_csv(file_path)

print(data)