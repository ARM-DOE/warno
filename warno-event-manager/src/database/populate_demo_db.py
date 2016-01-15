import utility

db = utility.connect_db()
cur = db.cursor()

# For each entry, first entry is table name, second entry is demo data for the table
table_data = [
                   "instruments",
                   "instrument_logs",
                   "prosensing_paf",
                   "event_codes",
                   "events_with_text",
                   "events_with_value",
                   "pulse_captures",
                   "table_references",
                   "instrument_data_references"
               ]

for table in table_data:
    if utility.table_exists(table, cur):
        utility.load_data_into_table("schema/%s.data" % table, table, db)
