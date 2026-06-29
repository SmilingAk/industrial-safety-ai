# risk_engine.py
# This file reads the factory snapshot and decides what to do about it.
# It also calls the AI to generate human-readable alerts and incident reports.

import os
from openai import OpenAI
from simulator import get_snapshot, update_factory_state

# ─────────────────────────────────────────────
#  Connect to OpenAI
#  It reads your API key from the .env file
#  (we'll create that file next)
# ─────────────────────────────────────────────
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# ─────────────────────────────────────────────
#  ALERT GENERATOR
#  When a zone goes CRITICAL, this function
#  calls the AI and asks it to write:
#  1. A plain-English alert for the worker
#  2. A short incident report citing OISD rules
# ─────────────────────────────────────────────
def generate_alert(zone_name, zone_data):
    prompt = f"""
You are an industrial safety AI assistant at an Indian heavy industry plant.

A CRITICAL safety alert has been triggered in {zone_name}.

Current readings:
- Gas level: {zone_data['gas_level']}% (safe threshold is below 40%)
- Temperature: {zone_data['temperature']}°C (safe threshold is below 60°C)  
- Active work permit: {"YES - workers are currently operating in this zone" if zone_data['permit_active'] else "NO"}
- Number of workers in zone: {zone_data['worker_count']}
- Time: {zone_data['timestamp']}

This is a COMPOUND RISK situation — high gas levels combined with an active work permit
is exactly the combination that caused the Visakhapatnam Steel Plant explosion in January 2025.

Please generate TWO things:

1. WORKER ALERT (2-3 sentences, simple language, urgent tone):
   A message the floor worker will understand immediately. Start with "⚠️ DANGER —"

2. INCIDENT REPORT (4-5 sentences, formal):
   A preliminary incident report for the safety officer citing:
   - What compound risk was detected
   - Which OISD standard is being violated (reference OISD-STD-117 for petroleum/gas safety)
   - Immediate recommended actions
   - Escalation requirement

Format your response exactly like this:
WORKER_ALERT: [your alert here]
INCIDENT_REPORT: [your report here]
"""

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",   # cheap and fast, good enough for demo
        messages=[
            {"role": "system", "content": "You are an industrial safety AI. Be precise, urgent, and cite regulations."},
            {"role": "user",   "content": prompt}
        ],
        max_tokens=400,
        temperature=0.3   # lower = more consistent, less random
    )

    raw = response.choices[0].message.content

    # Parse the two sections out of the AI response
    worker_alert    = ""
    incident_report = ""

    for line in raw.split("\n"):
        if line.startswith("WORKER_ALERT:"):
            worker_alert = line.replace("WORKER_ALERT:", "").strip()
        elif line.startswith("INCIDENT_REPORT:"):
            incident_report = line.replace("INCIDENT_REPORT:", "").strip()

    return worker_alert, incident_report


# ─────────────────────────────────────────────
#  WHATSAPP QUERY HANDLER
#  When a worker texts "Is Zone 1 safe?"
#  this function checks the live data and replies
# ─────────────────────────────────────────────
def answer_worker_query(worker_message):
    snapshot = get_snapshot()

    # Build a summary of all zones to give the AI context
    zone_summary = ""
    for zone, data in snapshot.items():
        zone_summary += f"\n- {zone}: Gas {data['gas_level']}%, Temp {data['temperature']}°C, Permit: {'YES' if data['permit_active'] else 'NO'}, Risk: {data['risk_level']}"

    prompt = f"""
You are a safety assistant for an Indian industrial plant. 
A floor worker just sent this message: "{worker_message}"

Current live factory status:
{zone_summary}

Reply in simple, clear English (max 3 sentences).
If any zone they're asking about is CRITICAL or WARNING, tell them clearly to stop work / stay away.
If they ask generally, summarise the current risk status of all zones.
Always end with the safety helpline: "For emergencies call Safety Control Room: Ext. 100"
"""

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a safety assistant. Keep replies short and clear."},
            {"role": "user",   "content": prompt}
        ],
        max_tokens=150,
        temperature=0.2
    )

    return response.choices[0].message.content.strip()


# ─────────────────────────────────────────────
#  MAIN MONITORING LOOP
#  Run this file directly to test the AI alerts
#  It checks the factory every 3 seconds
#  and fires alerts whenever a CRITICAL is found
# ─────────────────────────────────────────────
if __name__ == "__main__":
    import time
    from dotenv import load_dotenv
    load_dotenv()   # loads your API key from .env file

    # Re-initialise the client after loading env
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    print("Risk engine running... watching all zones.\n")

    alerted_zones = set()   # tracks which zones we've already alerted (avoid spam)

    tick = 0
    while True:
        tick += 1

        # Trigger the Vizag scenario at tick 8 so you can see the AI alert fire
        if tick == 8:
            print("⚠️  Triggering Vizag scenario...\n")
            update_factory_state("vizag")
        elif tick == 20:
            update_factory_state("reset")
            alerted_zones.clear()
            tick = 0
            print("✅  Reset. Watching again...\n")
        else:
            update_factory_state()

        snapshot = get_snapshot()

        for zone, data in snapshot.items():
            if data["risk_level"] == "CRITICAL" and zone not in alerted_zones:
                print(f"🔴 CRITICAL DETECTED in {zone}!")
                print(f"   Gas: {data['gas_level']}%  Temp: {data['temperature']}°C  Permit: {data['permit_active']}")
                print(f"   Calling AI to generate alert...\n")

                worker_alert, incident_report = generate_alert(zone, data)

                print(f"WORKER ALERT:\n{worker_alert}\n")
                print(f"INCIDENT REPORT:\n{incident_report}\n")
                print("─" * 60 + "\n")

                alerted_zones.add(zone)   # don't alert the same zone twice

        time.sleep(3)