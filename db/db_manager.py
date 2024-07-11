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
    # print(f"record inserted with id --- {res.inserted_id}")
    return res.inserted_id

def get_record_by_date_range(date):
    date = datetime.datetime.strptime(date, "%Y-%m-%d")
    start_date = datetime.datetime(date.year, date.month, date.day, 0, 0, 0, 000000)
    end_date = datetime.datetime(date.year, date.month, date.day, 23, 59, 59, 999999)

    return db.records.find({"Timestamp": {'$gte': start_date, '$lte': end_date}})

def get_record_by_date_range(date1, date2):
    date1 = datetime.datetime.strptime(date1, "%Y-%m-%d")
    date2 = datetime.datetime.strptime(date2, "%Y-%m-%d")

    start_date = datetime.datetime(date1.year, date1.month, date1.day, 0, 0, 0, 000000)
    end_date = datetime.datetime(date2.year, date2.month, date2.day, 23, 59, 59, 999999)

    return db.records.find({"Timestamp": {'$gte': start_date, '$lte': end_date}})

def get_record_by_time_range(start_time, end_time):
    start_time = datetime.datetime.strptime(start_time, "%Y-%m-%d %H:%M:%S")
    end_time = datetime.datetime.strptime(end_time, "%Y-%m-%d %H:%M:%S")
    start_time = datetime.datetime(start_time.year, start_time.month, start_time.day, start_time.hour, start_time.minute, start_time.second, 000000)
    end_time = datetime.datetime(end_time.year, end_time.month, end_time.day, end_time.hour, end_time.minute, end_time.second, 000000)
    
    return db.records.find({"Timestamp": {'$gte': start_time, '$lte': end_time}})
