import random
import time
import json
from datetime import datetime

# ─────────────────────────────────────────────
#  ZONES in the factory (we have 4 zones)
# ─────────────────────────────────────────────
ZONES = ["Zone 1 - Coke Oven", "Zone 2 - Gas Pipeline", "Zone 3 - Boiler Room", "Zone 4 - Maintenance Bay"]

# ─────────────────────────────────────────────
#  This holds the current state of the factory
# ─────────────────────────────────────────────
factory_state = {
    "Zone 1 - Coke Oven":      {"gas_level": 20, "temperature": 35, "permit_active": False, "worker_count": 2},
    "Zone 2 - Gas Pipeline":   {"gas_level": 15, "temperature": 30, "permit_active": False, "worker_count": 1},
    "Zone 3 - Boiler Room":    {"gas_level": 10, "temperature": 45, "permit_active": False, "worker_count": 3},
    "Zone 4 - Maintenance Bay":{"gas_level": 5,  "temperature": 28, "permit_active": False, "worker_count": 0},
}

# ─────────────────────────────────────────────
#  RISK CALCULATOR — the core logic
#  This is the KEY part of your project:
#  One bad reading alone = just a warning
#  Two bad readings together = CRITICAL alert
# ─────────────────────────────────────────────
def calculate_risk(zone_data):
    gas    = zone_data["gas_level"]
    temp   = zone_data["temperature"]
    permit = zone_data["permit_active"]

    # Safe — everything normal
    if gas < 40 and temp < 60:
        return "SAFE", "green"

    # Single sensor high — warning but not critical
    if gas >= 40 and not permit:
        return "WARNING", "yellow"

    if temp >= 60 and not permit:
        return "WARNING", "yellow"

    # COMPOUND RISK — this is your unique selling point
    # Gas is high AND someone has a work permit active = CRITICAL
    # This is exactly what happened in Vizag
    if gas >= 40 and permit:
        return "CRITICAL", "red"

    if temp >= 60 and permit:
        return "CRITICAL", "red"

    return "SAFE", "green"

# ─────────────────────────────────────────────
#  UPDATE FUNCTION — runs every few seconds
#  Randomly changes sensor values to simulate
#  a real factory environment
# ─────────────────────────────────────────────
def update_factory_state(scenario=None):

    # SCENARIO MODE — for your live demo
    # You can trigger a specific dangerous situation
    # by calling update_factory_state("vizag")
    if scenario == "vizag":
        # Simulate what happened in Vizag:
        # Gas slowly rises, permit gets activated, = disaster
        factory_state["Zone 1 - Coke Oven"]["gas_level"]     = random.randint(65, 90)
        factory_state["Zone 1 - Coke Oven"]["temperature"]   = random.randint(70, 95)
        factory_state["Zone 1 - Coke Oven"]["permit_active"] = True   # worker issued a permit
        factory_state["Zone 1 - Coke Oven"]["worker_count"]  = random.randint(3, 8)
        return

    if scenario == "reset":
        # Reset everything back to safe
        for zone in factory_state:
            factory_state[zone]["gas_level"]     = random.randint(5, 25)
            factory_state[zone]["temperature"]   = random.randint(25, 40)
            factory_state[zone]["permit_active"] = False
            factory_state[zone]["worker_count"]  = random.randint(0, 2)
        return

    # NORMAL MODE — random realistic fluctuations
    for zone in factory_state:
        current_gas  = factory_state[zone]["gas_level"]
        current_temp = factory_state[zone]["temperature"]

        # Gas level drifts up or down by a small amount each tick
        factory_state[zone]["gas_level"]     = max(0, min(100, current_gas  + random.randint(-5, 7)))
        factory_state[zone]["temperature"]   = max(20, min(120, current_temp + random.randint(-3, 4)))

        # Small random chance a permit gets issued or cancelled
        if random.random() < 0.05:   # 5% chance each tick
            factory_state[zone]["permit_active"] = not factory_state[zone]["permit_active"]

        factory_state[zone]["worker_count"] = random.randint(0, 6)

# ─────────────────────────────────────────────
#  SNAPSHOT — returns a clean dictionary of the
#  full factory state that other files can use
# ─────────────────────────────────────────────
def get_snapshot():
    snapshot = {}
    for zone, data in factory_state.items():
        risk_level, risk_color = calculate_risk(data)
        snapshot[zone] = {
            "gas_level":     data["gas_level"],
            "temperature":   data["temperature"],
            "permit_active": data["permit_active"],
            "worker_count":  data["worker_count"],
            "risk_level":    risk_level,
            "risk_color":    risk_color,
            "timestamp":     datetime.now().strftime("%H:%M:%S"),
        }
    return snapshot

# ─────────────────────────────────────────────
#  RUN THIS FILE DIRECTLY to test it in terminal
#  You'll see the factory state printing live
# ─────────────────────────────────────────────
if __name__ == "__main__":
    print("Factory simulator running... Press Ctrl+C to stop.\n")

    tick = 0
    while True:
        tick += 1

        # Every 15 ticks, simulate the Vizag scenario so you can see it trigger
        if tick == 15:
            print("\n⚠️  TRIGGERING VIZAG SCENARIO...\n")
            update_factory_state("vizag")
        elif tick == 25:
            print("\n✅  RESETTING TO SAFE STATE...\n")
            update_factory_state("reset")
            tick = 0
        else:
            update_factory_state()

        snapshot = get_snapshot()

        # Print each zone clearly in the terminal
        print(f"── Tick {tick} at {datetime.now().strftime('%H:%M:%S')} ──────────────────")
        for zone, data in snapshot.items():
            status_icon = "🔴" if data["risk_level"] == "CRITICAL" else "🟡" if data["risk_level"] == "WARNING" else "🟢"
            permit_icon = "📋 PERMIT ON" if data["permit_active"] else "   no permit"
            print(
                f"  {status_icon} {zone:<28} "
                f"Gas: {data['gas_level']:>3}%  "
                f"Temp: {data['temperature']:>3}°C  "
                f"Workers: {data['worker_count']}  "
                f"{permit_icon}  "
                f"→ {data['risk_level']}"
            )
        print()

        time.sleep(2)  # update every 2 seconds