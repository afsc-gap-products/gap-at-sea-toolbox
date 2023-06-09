import pandas as pd

file_path = './inst/survey_app_data - entries.csv'

data = pd.read_csv(file_path)

print(data)

# def populate_list(self):
#         with open('data.csv', 'r', newline='') as file:
#             reader = csv.reader(file)
#             header = next(reader)  # Read the header row
#             self.model.setHorizontalHeaderLabels(header)

#             for row in reader:
#                 name = row[0]
#                 description = row[1]
#                 location = row[2]
#                 last_update = row[3]

#                 name_item = QStandardItem(name)
#                 description_item = QStandardItem(description)
#                 location_item = QStandardItem(location)
#                 last_update_item = QStandardItem(last_update)

#                 self.model.appendRow(
#                     [name_item, description_item, location_item, last_update_item])