# from databases import Database
from database import Database
import os
import json
# import asyncio

# from databases import Database
# database = Database('sqlite+aiosqlite:///repositories.db')
# asyncio.run(database.connect())

db = Database("repositories.db")

# Directory containing JSON files
json_dir = os.path.join(os.path.dirname(__file__), "github_data")

# Iterate over each JSON file in the directory
for file_name in os.listdir(json_dir):
    if file_name.endswith(".json"):
        file_path = os.path.join(json_dir, file_name)
        with open(file_path, "r") as json_file:
            json_data = json.load(json_file)

            # Check if the record already exists
            # result = asyncio.run(db.fetch_repo(json_data["repo_name"])) 
            result = db.fetch_repo(json_data["repo_name"])

            if result == 0:
                # asyncio.run(db.insert_repositories_table(json_file)) 
                # ret = db.insert_repositories_table(json_data)
                # print(ret)
                db.insert_repositories_table(json_data)
            else:
                print("Repo already exists in the database.")

