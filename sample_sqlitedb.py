# Create a database instance, and connect to it.
from databases import Database
import asyncio

database = Database('sqlite+aiosqlite:///example.db')

asyncio.run(database.connect())
# await database.connect()

# Create a table.
query = """CREATE TABLE IF NOT EXISTS HighScores (id INTEGER PRIMARY KEY, name VARCHAR(100), score INTEGER)"""
# await database.execute(query=query)
asyncio.run(database.execute(query=query))


# Insert some data.
query = "INSERT INTO HighScores(name, score) VALUES (:name, :score)"
values = [
    {"name": "Daisy", "score": 92},
    {"name": "Neil", "score": 87},
    {"name": "Carol", "score": 43},
]
# await database.execute_many(query=query, values=values)
asyncio.run(database.execute_many(query=query, values=values))

# Run a database query.
query = "SELECT * FROM HighScores"
# rows = await database.fetch_all(query=query)
rows = asyncio.run(database.fetch_all(query=query))
print('High Scores:', rows)
