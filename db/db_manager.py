import datetime
from db.db_config import db 

def insert_record(record_path, frames_num):
    record = {
        "Path": record_path,
        "Number of Frames": frames_num,
        "Timestamp": datetime.datetime.now(tz=datetime.timezone.utc),
    }
    res = db.records.insert_one(record)

    print(f"record inserted with id --- {res.inserted_id}")

    return res.inserted_id


