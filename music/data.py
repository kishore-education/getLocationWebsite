
from pymongo.mongo_client import MongoClient
# from pymongo.server_api import ServerApi
import csv


# MongoDB connection
uri = "mongodb+srv://kishoresaravanan440:dlLRM1oRCAM6ERtB@cluster0.tqksj4o.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
client = MongoClient(uri)

# Send a ping to confirm a successful connection
try:
    client.admin.command('ping')
    print("Pinged your deployment. You successfully connected to MongoDB!")
except Exception as e:
    print(e)

# Use database 'music' and collection 'songs_metadata'
db = client['music']
songs_collection = db['songs_metadata']

# Read and insert data from CSV into MongoDB
with open('songs_metadata.csv', 'r', encoding='utf-8') as csvfile:
    reader = csv.DictReader(csvfile)
    docs = []
    for row in reader:
        # Convert duration to int if present
        if row.get('duration'):
            try:
                row['duration'] = int(row['duration'])
            except Exception:
                row['duration'] = None
        else:
            row['duration'] = None
        docs.append(row)
    if docs:
        result = songs_collection.insert_many(docs)
        print(f"Inserted {len(result.inserted_ids)} documents into MongoDB.")
    else:
        print("No data to insert.")
