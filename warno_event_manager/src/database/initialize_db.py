from WarnoConfig import utility

db = utility.connect_db()
cur = db.cursor()

utility.initialize_database(cur)
db.commit()
