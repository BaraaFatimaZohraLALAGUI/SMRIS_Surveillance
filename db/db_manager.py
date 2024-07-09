from db.db_config import db 

def insert_record(record_path, frames_num, timestamp):
    record = {
        "Path": record_path,
        "Number of Frames": frames_num,
        "Timestamp": timestamp,
    }
    res = db.records.insert_one(record)

    print(f"record inserted with id --- {res.inserted_id}")

    return res.inserted_id


