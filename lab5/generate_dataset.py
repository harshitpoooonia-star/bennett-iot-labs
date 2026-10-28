import numpy as np, pandas as pd

rng = np.random.default_rng(42)
n = 24 * 90                              # 90 days, one reading per hour
t = pd.date_range("2026-09-01", periods=n, freq="h")
hour = t.hour.values
air = 26 + 8*np.sin((hour - 9)/24*2*np.pi) + rng.normal(0, 1.5, n)
hum = np.clip(60 - 1.6*(air - 26) + rng.normal(0, 6, n), 20, 95)
rain = np.where(rng.random(n) < 0.03, rng.uniform(1, 8, n), 0.0)

m = np.zeros(n); m[0] = 30; irr = np.zeros(n, dtype=int)
for i in range(n - 1):
    if hour[i] in (6, 18):               # waters at 06:00 and 18:00
        irr[i] = int(rng.random() < (0.85 if m[i] < 24 else 0.05))
    evap = 0.30 + 0.05*max(air[i] - 20, 0) * (1 - hum[i]/130)
    m[i+1] = np.clip(m[i] - evap + 1.2*rain[i] + 10*irr[i]
                     + rng.normal(0, 0.25), 8, 48)

soil_t = 22 + 0.5*(air - 26) + rng.normal(0, 0.4, n)
batt = 3.9 - 0.0008*np.arange(n)/24 + rng.normal(0, 0.01, n)

df = pd.DataFrame({"timestamp": t, "hour": hour,
    "air_temp_c": air.round(2), "humidity_pct": hum.round(1),
    "rain_mm": rain.round(1), "irrigated": irr,
    "soil_temp_c": soil_t.round(2), "soil_moisture_pct": m.round(2),
    "battery_v": batt.round(3)})

# the two things we want to predict (one hour ahead)
df["moisture_next_hr"] = df["soil_moisture_pct"].shift(-1)
df = df.iloc[:-1].copy()
df["low_next_hr"] = (df["moisture_next_hr"] < 20).astype(int)

# simulate sensor dropouts (missing readings)
for col, k in (("humidity_pct", 25), ("soil_moisture_pct", 10)):
    df.loc[df.sample(k, random_state=7).index, col] = np.nan

df.to_csv("soil_ml_data.csv", index=False)
print(df.shape)
