from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, field_validator
from datetime import datetime
from typing import List
import mysql.connector

app = FastAPI()

# Konfigurasi database
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': '',
    'database': 'smartwaste'
}

# Model data yang diterima
class SensorData(BaseModel):
    timestamp: datetime
    jarak: float
    kapasitas: float

    @field_validator('timestamp', mode='before')
    def parse_timestamp(cls, value):
        if isinstance(value, str):
            try:
                return datetime.strptime(value, '%Y-%m-%d %H:%M:%S')
            except ValueError:
                raise ValueError('Invalid timestamp format')
        return value

# Fungsi untuk menyimpan data ke database
def save_to_database(data: SensorData):
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        query = "INSERT INTO sensor_data (timestamp, jarak, kapasitas) VALUES (%s, %s, %s)"
        values = (data.timestamp, data.jarak, data.kapasitas)
        cursor.execute(query, values)
        conn.commit()
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        print(f"Database Error: {e}")
        return False

# Endpoint untuk menerima data sensor
@app.post("/save-data")
async def save_data(data: SensorData):
    if save_to_database(data):
        return {"message": "Data saved successfully!"}
    else:
        raise HTTPException(status_code=500, detail="Failed to save data to database.")

@app.get("/sensor-data")
async def get_sensor_data(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=100)
):
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)
        
        # Get total count
        cursor.execute("SELECT COUNT(*) as total FROM sensor_data")
        total_records = cursor.fetchone()['total']
        
        # Calculate offset
        offset = (page - 1) * page_size
        
        # Get paginated data
        query = """
            SELECT timestamp, jarak, kapasitas 
            FROM sensor_data 
            ORDER BY timestamp DESC 
            LIMIT %s OFFSET %s
        """
        cursor.execute(query, (page_size, offset))
        data = cursor.fetchall()
        
        cursor.close()
        conn.close()

        return {
            "data": data,
            "page": page,
            "page_size": page_size,
            "total_records": total_records,
            "total_pages": -(-total_records // page_size)  # Ceiling division
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")