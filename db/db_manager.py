from db.db_config import db 
import datetime
from datetime import timezone

def insert_record(record_path, frames_num, timestamp):
    record = {
        "Path": record_path,
        "Number of Frames": frames_num,
        "Timestamp": timestamp,
    }
    res = db.records.insert_one(record)

    print(f"record inserted with id --- {res.inserted_id}")

    return res.inserted_id

def get_record_by_date(date):
    date = datetime.datetime.strptime(date, "%Y-%m-%d")
    start_date = datetime.datetime(date.year, date.month, date.day, 0, 0, 0, 000000)
    end_date = datetime.datetime(date.year, date.month, date.day, 23, 59, 59, 999999)

    return db.records.find({"Timestamp": {'$gte': start_date, '$lte': end_date}})



def get_record_by_time(start_time, end_time):
    pass