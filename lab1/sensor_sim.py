"""
Simulated DHT22 sensor node - stands in for the ESP32/Raspberry Pi when no
hardware is attached. Publishes on the SAME topics and in the SAME format as
the lab's ESP32 sketch (dtostrf(x,4,2) -> "27.43"), every 2 seconds.
Temperature follows a slow drift + noise and periodically heats past 35 C so
the threshold alert (Practice Task 2) can be demonstrated.
"""
import math, random, time, sys
import paho.mqtt.client as mqtt

BROKER = sys.argv[1] if len(sys.argv) > 1 else "localhost"
PORT = 1883
T_TOPIC, H_TOPIC = "iot/sensor/temperature", "iot/sensor/humidity"

client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="ESP32Client-sim")
client.connect(BROKER, PORT)
client.loop_start()
print(f"Connected to MQTT broker {BROKER}:{PORT}", flush=True)

t0 = time.time()
n = 0
while True:
    k = time.time() - t0
    # 60 s cycle: 28 C baseline, peaks ~37 C to trip the 35 C alert
    temp = 28 + 9 * max(0, math.sin(2 * math.pi * k / 60)) ** 2 + random.gauss(0, 0.3)
    hum = 60 - 0.8 * (temp - 28) + random.gauss(0, 1.0)   # humidity falls as temp rises
    ts, hs = f"{temp:.2f}", f"{hum:.2f}"
    client.publish(T_TOPIC, ts)
    client.publish(H_TOPIC, hs)
    n += 1
    print(f"[{time.strftime('%H:%M:%S')}] #{n:03d} Temperature: {ts} C  Humidity: {hs} %  -> published", flush=True)
    time.sleep(2)
