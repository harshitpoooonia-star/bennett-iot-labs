import os
import numpy as np, pandas as pd
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS

# ---- 1. Simulate 10 days of two-zone soil sensor data (15-min interval) ----
np.random.seed(21)
n_days, readings_per_day = 10, 96
n = n_days * readings_per_day
timestamps = pd.date_range("2026-09-01", periods=n, freq="15min")
hours = np.array([t.hour + t.minute/60 for t in timestamps])

def make_zone(seed, start, irrigate_every_h, irrigate_amt, decay):
    rng = np.random.default_rng(seed)
    m = np.zeros(n); m[0] = start; nxt = irrigate_every_h
    for i in range(1, n):
        day_f = 1.3 if 6 <= hours[i] <= 18 else 0.6
        m[i] = m[i-1] - decay*day_f + rng.normal(0, 0.03)
        if i*0.25 >= nxt:
            m[i] += irrigate_amt + rng.uniform(-0.4, 0.4); nxt += irrigate_every_h
    m = np.clip(m, 6, 48)
    temp = 24 + 5*np.sin((hours-10)/24*2*np.pi - np.pi/2) + rng.normal(0, 0.3, n)
    batt = 3.3 - 0.025*(np.arange(n)//readings_per_day) + rng.normal(0, 0.01, n)
    return m.round(2), temp.round(2), batt.round(3)

mA, tA, bA = make_zone(1, 34, 24, 10, 0.11)      # Zone A: irrigated daily, healthy
mB, tB, bB = make_zone(2, 34, 30, 13.2, 0.115)   # Zone B: irrigated less often, dips low

# ---- 1b. Shift the timestamps so the 10-day series ENDS AT THE CURRENT TIME ----
# (values are unchanged; this makes the relative Flux ranges -15m / -24h / -7d return data)
now = pd.Timestamp.now(tz="UTC").floor("15min")
timestamps = timestamps.tz_localize("UTC") + (now - timestamps.tz_localize("UTC")[-1])

# ---- 2. Write every reading into InfluxDB as a Point ----
client = InfluxDBClient(url="http://localhost:8086", token=os.environ["INFLUX_TOKEN"], org="iot_analytics_lab")
write_api = client.write_api(write_options=SYNCHRONOUS)

points = []
for zone, m, t, b in [("zone_A", mA, tA, bA), ("zone_B", mB, tB, bB)]:
    for i in range(n):
        pt = (Point("soil_sensor")
              .tag("field", zone)
              .field("soil_moisture", float(m[i]))
              .field("soil_temperature", float(t[i]))
              .field("battery_voltage", float(b[i]))
              .time(timestamps[i]))
        points.append(pt)

write_api.write(bucket="soil_sensors", record=points)
print(f"Wrote {len(points)} points to InfluxDB.")
