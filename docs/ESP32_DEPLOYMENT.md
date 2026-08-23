# SkyGuard AI: Edge Microcontroller Deployment Guide (ESP32 / Arduino / MicroPython)

SkyGuard AI includes ultra-lightweight, zero-dynamic-memory edge libraries for microcontrollers (ESP32, ARM Cortex-M, STM32, Arduino, Raspberry Pi Pico).

---

## 1. Edge Specifications

- **Language**: Pure C/C++ (`edge/skyguard_edge.h`) & MicroPython (`edge/skyguard_edge.py`)
- **Memory Footprint**: `< 3.2 KB RAM` total
- **Dynamic Allocation**: `0 bytes` (Zero malloc / stack allocated)
- **Execution Time**: `< 0.05 ms` per single-reading inference
- **Dependencies**: Standard `math.h` only

---

## 2. Arduino / ESP32 C++ Integration

### Step 1: Copy Header File
Copy `edge/skyguard_edge.h` into your Arduino sketch or PlatformIO project folder:
```bash
cp edge/skyguard_edge.h path/to/your/arduino_sketch/
```

### Step 2: Example Arduino Sketch (`skyguard_esp32_demo.ino`)
```cpp
#include "skyguard_edge.h"

EdgeGuardState edge_state;

void setup() {
    Serial.begin(115200);
    skyguard_edge_init(&edge_state);
    Serial.println("🌦️ SkyGuard AI Edge Guard Initialized on ESP32.");
}

void loop() {
    // Read your physical sensors (e.g. BME280, SHT31, BMP280)
    float temperature = 26.4f; // Read from sensor
    float pressure = 1012.3f;   // Read from sensor
    float humidity = 62.0f;     // Read from sensor

    EdgeTelemetryInput input = {
        .temperature_c = temperature,
        .pressure_hpa = pressure,
        .humidity_pct = humidity,
        .dt_seconds = 1.0f
    };

    EdgeDetectionResult result;
    skyguard_edge_process(&edge_state, &input, &result);

    if (result.is_anomaly) {
        Serial.printf("⚠️ ANOMALY DETECTED! Type: %d, Confidence: %.2f, DewPoint: %.1f C\n",
                      result.fault_type, result.anomaly_confidence, result.dew_point_c);
    } else {
        Serial.printf("✅ CLEAN READING: T=%.1f C, P=%.1f hPa, RH=%.1f %%, Td=%.1f C\n",
                      temperature, pressure, humidity, result.dew_point_c);
    }

    delay(1000);
}
```

---

## 3. MicroPython Deployment (ESP32 / Pico)

### Step 1: Flash `skyguard_edge.py`
Upload `edge/skyguard_edge.py` to the flash memory of your ESP32 or Raspberry Pi Pico using `ampy` or `mpremote`:
```bash
mpremote cp edge/skyguard_edge.py :skyguard_edge.py
```

### Step 2: Run MicroPython Script
```python
import time
from skyguard_edge import MicroEdgeGuard

guard = MicroEdgeGuard()

while True:
    # Read sensor values
    t, p, rh = 25.4, 1013.2, 58.0
    res = guard.process(temp_c=t, pressure_hpa=p, humidity_pct=rh, dt_sec=1.0)
    
    if res["is_anomaly"]:
        print(f"⚠️ Anomaly: {res['type']} (Confidence: {res['confidence']})")
    else:
        print(f"✅ Clean: T={t}°C, Td={res['td']:.1f}°C")
        
    time.sleep(1)
```
