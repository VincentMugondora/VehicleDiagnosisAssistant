#!/usr/bin/env python3
"""
Enrich P3497 with researched data from DTC_DETAILS_FOR_REVIEW.md
"""
import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()
supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_SERVICE_KEY"))

print("=" * 70)
print("ENRICHING P3497 - Cylinder Deactivation System Bank 2")
print("=" * 70)

# Get P3497 from database
print("\n[1] Looking up P3497 in database...")
result = supabase.table("obd_codes").select("code, description").eq("code", "P3497").execute()

if not result.data:
    print("ERROR: P3497 not found in database!")
    exit(1)

p3497 = result.data[0]
code_id = p3497['code']  # Use the code string itself as the foreign key
print(f"  Found: {p3497['code']}")
print(f"  Description: {p3497['description']}")

# Enrichment data from DTC_DETAILS_FOR_REVIEW.md
symptoms = [
    "Check engine light illuminated",
    "Reduced fuel economy (deactivation system not working)",
    "Rough idle or vibration",
    "Engine noise or ticking sounds",
    "Reduced power or performance",
    "May have no symptoms beyond warning light"
]

repair_steps = [
    ("Check engine oil level - low oil prevents proper cylinder deactivation operation", 1),
    ("Verify correct engine oil type is used (must meet manufacturer specifications for VCM/cylinder deactivation)", 2),
    ("Change oil and filter if overdue or wrong oil type was used", 3),
    ("Check for Technical Service Bulletins specific to your vehicle model and year", 4),
    ("Inspect VCM oil pressure relief valve for sticking (known issue in 2013 Honda Pilots)", 5),
    ("Test oil pressure switch operation and readings", 6),
    ("Apply available software updates from manufacturer (known fix for some 2011 Honda models)", 7),
    ("Check valve deactivation solenoids in cylinder head for proper operation", 8),
    ("If persistent after oil service, professional diagnosis required for internal cylinder head components", 9)
]

parts = [
    ("Engine Oil (correct specification)", None),
    ("Oil Filter", None),
    ("VCM Oil Pressure Relief Valve", None),
    ("Oil Pressure Switch", None),
    ("Cylinder Deactivation Solenoids", None),
    ("ECM Software Update", None)
]

related_codes = ["P3400", "P3401", "P3496"]

# Update main obd_codes entry with symptoms/causes/fixes summary
print("\n[2] Updating obd_codes table with enrichment summary...")

enrichment_summary = {
    "symptoms": "Check engine light, reduced fuel economy, rough idle, engine noise, reduced power",
    "common_causes": "Low engine oil level, incorrect oil type, stuck VCM oil pressure relief valve, faulty oil pressure switch, faulty cylinder deactivation solenoids",
    "generic_fixes": "Check oil level and type, change oil and filter, inspect VCM relief valve, test oil pressure switch, check for TSBs and software updates"
}

result = supabase.table("obd_codes").update(enrichment_summary).eq("code", "P3497").execute()
print(f"  Updated obd_codes entry for P3497")

# Insert symptoms
print("\n[3] Inserting symptoms...")
for symptom in symptoms:
    supabase.table("common_symptoms").insert({
        "code_id": code_id,
        "symptom": symptom
    }).execute()
    print(f"  + {symptom}")

# Insert repair steps
print("\n[4] Inserting repair steps...")
for instruction, step_num in repair_steps:
    supabase.table("repair_steps").insert({
        "code_id": code_id,
        "step_number": step_num,
        "instruction": instruction
    }).execute()
    print(f"  {step_num}. {instruction[:60]}...")

# Insert parts
print("\n[5] Inserting parts...")
for part_name, part_number in parts:
    supabase.table("parts").insert({
        "code_id": code_id,
        "part_name": part_name,
        "part_number": part_number
    }).execute()
    print(f"  + {part_name}")

# Insert related codes
print("\n[6] Inserting related codes...")
for related in related_codes:
    supabase.table("related_codes").insert({
        "code_id": code_id,
        "related_code": related
    }).execute()
    print(f"  -> {related}")

print("\n" + "=" * 70)
print("SUCCESS: P3497 fully enriched!")
print("=" * 70)
print(f"  Symptoms: {len(symptoms)}")
print(f"  Repair steps: {len(repair_steps)}")
print(f"  Parts: {len(parts)}")
print(f"  Related codes: {len(related_codes)}")
print()
print("Note: Honda-specific code primarily for V6/V8 engines with cylinder")
print("deactivation (VCM). Oil level/type is the primary cause.")
print("=" * 70)
