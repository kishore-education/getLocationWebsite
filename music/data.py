import csv
import os

csv_file = 'songs_metadata.csv'
temp_file = 'songs_metadata_temp.csv'

with open(csv_file, 'r', encoding='utf-8', newline='') as infile, open(temp_file, 'w', encoding='utf-8', newline='') as outfile:
    reader = csv.DictReader(infile)
    fieldnames = reader.fieldnames
    writer = csv.DictWriter(outfile, fieldnames=fieldnames)
    writer.writeheader()
    for row in reader:
        if row.get('quality') != '160kbps':
            writer.writerow(row)

# Replace the original file with the filtered one
os.replace(temp_file, csv_file)
print("Removed all 160kbps quality rows from songs_metadata.csv.")
