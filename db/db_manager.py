import datetime
from db.db_config import db 

def insert_record(record_path, people_num, duration):
    record = {
        "Path": record_path,
        "Duration": duration,
        "Number of People": people_num,
        "Timestamp": datetime.datetime.now(tz=datetime.timezone.utc),
    }
    res = db.records.insert_one(record)

    print(f"record inserted with id --- {res.inserted_id}")

    return res.inserted_id


