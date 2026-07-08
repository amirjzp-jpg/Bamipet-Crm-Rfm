"""
Bamipet x Navatel -- RFM+Engagement pipeline entry point.

Run:  python main.py
Env:  NAVATEL_BASE_URL, NAVATEL_API_TOKEN (see config.py)

Steps:
  1. Pull contacts, orders, call logs, SMS logs from Navatel.
  2. Score every contact on Recency / Frequency / Monetary / Engagement.
  3. Assign an RFM segment + a persona guess + a recommended messaging pillar.
  4. Write the segment (and persona guess) back onto each contact in Navatel.
  5. Print a distribution summary so the team can sanity-check before this
     feeds into any campaign.
"""
from collections import Counter

from config import SEGMENT_FIELD_NAME, PERSONA_FIELD_NAME
from navatel_client import NavatelClient
from rfm_engine import build_customer_table, score_rfm
from persona_mapper import guess_persona


def main():
    client = NavatelClient()

    print("Fetching contacts...")
    contacts = client.get_contacts()
    print("Fetching orders/invoices...")
    orders = client.get_orders()
    print("Fetching call logs...")
    calls = client.get_call_logs()
    print("Fetching SMS logs...")
    sms = client.get_sms_logs()

    print(f"Loaded: {len(contacts)} contacts, {len(orders)} orders, "
          f"{len(calls)} calls, {len(sms)} sms.")

    table = build_customer_table(contacts, orders, calls, sms)
    scored = score_rfm(table)

    segment_counts = Counter()
    persona_counts = Counter()

    for _, row in scored.iterrows():
        guess = guess_persona(row)  # pass species=... here once that field is confirmed in Navatel's schema
        segment_counts[guess.segment] += 1
        persona_counts[guess.likely_persona] += 1

        # Write back to Navatel -- comment out while validating locally
        # client.update_contact_field(row["contact_id"], SEGMENT_FIELD_NAME, guess.segment)
        # client.update_contact_field(row["contact_id"], PERSONA_FIELD_NAME, guess.likely_persona)

    print("\n--- Segment distribution ---")
    for seg, count in segment_counts.most_common():
        print(f"  {seg:<20} {count}")

    print("\n--- Persona-guess distribution ---")
    for persona, count in persona_counts.most_common():
        print(f"  {persona:<10} {count}")

    print("\nNOTE: write-back calls are commented out above. Uncomment once "
          "you've confirmed SEGMENT_FIELD_NAME / PERSONA_FIELD_NAME exist as "
          "real custom fields in Navatel's CRM schema.")


if __name__ == "__main__":
    main()
