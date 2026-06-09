import psycopg2
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

load_dotenv()

db_config = {
    "host": "localhost",
    "database": "sensor_data",
    "user": "sensor_user",
    'password': os.environ.get('DB_PASSWORD')
}

class Database:
    def save(self, temperature, humidity):
        """Salva i dati su PostgreSQL."""
        try:
            conn = psycopg2.connect(**db_config)
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO sensor_data (time, temperature, humidity) VALUES (NOW(), %s, %s)",
                (temperature, humidity)
            )
            conn.commit()
            cursor.close()
            conn.close()
            return True
        except Exception as e:
            print(f"Errore salvataggio DB: {e}")
            return False
    def fetch_historical_data(self, hours=24):
        """Recupera e raggruppa i dati storici."""
        try:
            conn = psycopg2.connect(**db_config)
            cursor = conn.cursor()
            
            end_time = datetime.now()
            start_time = end_time - timedelta(hours=hours)
            
            cursor.execute(
                "SELECT time, temperature, humidity FROM sensor_data WHERE time BETWEEN %s AND %s ORDER BY time",
                (start_time, end_time)
            )
            raw_data = cursor.fetchall()
            cursor.close()
            conn.close()
            
            # Raggruppa per slot orari
            temp_slots = {i: [] for i in range(hours)}
            hum_slots = {i: [] for i in range(hours)}
            
            for row in raw_data:
                # Converte il timestamp in datetime naive (rimuove timezone)
                db_time = row[0].replace(tzinfo=None)
                time_diff = (db_time - start_time).total_seconds() / 3600
                slot = int(time_diff)
                if 0 <= slot < hours:
                    temp_slots[slot].append(row[1])
                    hum_slots[slot].append(row[2])
            
            # Calcola medie
            temp_averaged = []
            hum_averaged = []
            for slot in range(hours):
                temp_avg = sum(temp_slots[slot]) / len(temp_slots[slot]) if temp_slots[slot] else 0
                hum_avg = sum(hum_slots[slot]) / len(hum_slots[slot]) if hum_slots[slot] else 0
                temp_averaged.append(temp_avg)
                hum_averaged.append(hum_avg)
            
            return [
                (start_time + timedelta(hours=i), temp_averaged[i], hum_averaged[i])
                for i in range(hours)
            ]
            
        except Exception as e:
            print(f"Errore recupero dati: {e}")
            return []
