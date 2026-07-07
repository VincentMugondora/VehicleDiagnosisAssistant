#!/usr/bin/env python3
"""
DTC Details Population Script

Populates repair_steps, parts, common_symptoms, and related_codes tables
with curated data for priority OBD-II codes from production logs.

Data sourced from: dtclookup.com, obdguide.com, dtcsearch.com
Cross-referenced and paraphrased for quality and copyright compliance.
"""
import os
from pathlib import Path
from supabase import create_client
from typing import Dict, List

# Load environment variables
env_file = Path(".env")
if env_file.exists():
    with open(env_file) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ[key] = value

# Initialize Supabase client
url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_SERVICE_KEY")

if not url or not key:
    raise ValueError("SUPABASE_URL and SUPABASE_SERVICE_KEY must be set in .env")

client = create_client(url, key)

# ============================================================================
# DTC DATA - Priority codes from production logs
# ============================================================================

DTC_DATA: List[Dict] = [
    # ========================================================================
    # TOP TIER - Most Requested Codes
    # ========================================================================
    {
        'code': 'P0171',
        'common_symptoms': [
            {'code_id': 'P0171', 'symptom_text': 'Check engine light on', 'severity': 'medium'},
            {'code_id': 'P0171', 'symptom_text': 'Rough idle or engine misfiring', 'severity': 'medium'},
            {'code_id': 'P0171', 'symptom_text': 'Loss of power or difficulty accelerating', 'severity': 'high'},
            {'code_id': 'P0171', 'symptom_text': 'Hard starting or engine stalling', 'severity': 'high'},
            {'code_id': 'P0171', 'symptom_text': 'Sometimes no noticeable symptoms except warning light', 'severity': 'low'},
        ],
        'repair_steps': [
            {'code_id': 'P0171', 'step_number': 1, 'description': 'Inspect all vacuum hoses and intake manifold gaskets for leaks or cracks', 'difficulty': 'easy'},
            {'code_id': 'P0171', 'step_number': 2, 'description': 'Clean or test the Mass Air Flow (MAF) sensor - dirty sensors often cause false readings', 'difficulty': 'easy'},
            {'code_id': 'P0171', 'step_number': 3, 'description': 'Check fuel system components - test fuel pressure, inspect fuel filter and injectors for clogs', 'difficulty': 'medium'},
            {'code_id': 'P0171', 'step_number': 4, 'description': 'Test oxygen sensors for proper operation and response time', 'difficulty': 'medium'},
            {'code_id': 'P0171', 'step_number': 5, 'description': 'Examine PCV system hoses and connections for damage', 'difficulty': 'easy'},
            {'code_id': 'P0171', 'step_number': 6, 'description': 'If all else checks out, inspect for engine mechanical issues like worn valve guides', 'difficulty': 'hard'},
        ],
        'parts': [
            {'code_id': 'P0171', 'part_name': 'Mass Air Flow (MAF) Sensor', 'part_number': None},
            {'code_id': 'P0171', 'part_name': 'Oxygen Sensor (Bank 1)', 'part_number': None},
            {'code_id': 'P0171', 'part_name': 'Vacuum Hoses', 'part_number': None},
            {'code_id': 'P0171', 'part_name': 'Intake Manifold Gasket', 'part_number': None},
            {'code_id': 'P0171', 'part_name': 'Fuel Filter', 'part_number': None},
            {'code_id': 'P0171', 'part_name': 'Fuel Injectors', 'part_number': None},
            {'code_id': 'P0171', 'part_name': 'Fuel Pressure Regulator', 'part_number': None},
            {'code_id': 'P0171', 'part_name': 'PCV Valve and Hoses', 'part_number': None},
        ],
        'related_codes': [
            {'code_id': 'P0171', 'related_code_id': 'P0174', 'relationship_type': 'similar_condition'},
            {'code_id': 'P0171', 'related_code_id': 'P0170', 'relationship_type': 'related_system'},
            {'code_id': 'P0171', 'related_code_id': 'P0172', 'relationship_type': 'opposite_condition'},
        ],
    },
    {
        'code': 'P0100',
        'common_symptoms': [
            {'code_id': 'P0100', 'symptom_text': 'Check engine light illuminated', 'severity': 'medium'},
            {'code_id': 'P0100', 'symptom_text': 'Engine running rough or jerking', 'severity': 'medium'},
            {'code_id': 'P0100', 'symptom_text': 'Hard starting or stalling shortly after start', 'severity': 'high'},
            {'code_id': 'P0100', 'symptom_text': 'Engine stalling during driving', 'severity': 'high'},
            {'code_id': 'P0100', 'symptom_text': 'May have no symptoms in some vehicles', 'severity': 'low'},
        ],
        'repair_steps': [
            {'code_id': 'P0100', 'step_number': 1, 'description': 'Inspect MAF sensor wiring and connectors for damage, corrosion, or loose connections', 'difficulty': 'easy'},
            {'code_id': 'P0100', 'step_number': 2, 'description': 'Check air filter condition - dirty filter can affect MAF readings', 'difficulty': 'easy'},
            {'code_id': 'P0100', 'step_number': 3, 'description': 'Clean the MAF sensor using proper MAF cleaner spray (not regular cleaners)', 'difficulty': 'easy'},
            {'code_id': 'P0100', 'step_number': 4, 'description': 'Test MAF sensor voltage output at idle and various RPMs with scan tool', 'difficulty': 'medium'},
            {'code_id': 'P0100', 'step_number': 5, 'description': 'Check for air leaks between MAF sensor and throttle body', 'difficulty': 'medium'},
            {'code_id': 'P0100', 'step_number': 6, 'description': 'Replace MAF sensor if cleaning and wiring checks don\'t resolve the issue', 'difficulty': 'medium'},
        ],
        'parts': [
            {'code_id': 'P0100', 'part_name': 'Mass Air Flow (MAF) Sensor', 'part_number': None},
            {'code_id': 'P0100', 'part_name': 'Air Filter', 'part_number': None},
            {'code_id': 'P0100', 'part_name': 'MAF Sensor Wiring Harness', 'part_number': None},
            {'code_id': 'P0100', 'part_name': 'Sensor Connectors', 'part_number': None},
            {'code_id': 'P0100', 'part_name': 'Intake Ducting', 'part_number': None},
        ],
        'related_codes': [
            {'code_id': 'P0100', 'related_code_id': 'P0101', 'relationship_type': 'related_system'},
            {'code_id': 'P0100', 'related_code_id': 'P0102', 'relationship_type': 'related_system'},
            {'code_id': 'P0100', 'related_code_id': 'P0103', 'relationship_type': 'related_system'},
            {'code_id': 'P0100', 'related_code_id': 'P0104', 'relationship_type': 'related_system'},
        ],
    },
    {
        'code': 'P0609',
        'common_symptoms': [
            {'code_id': 'P0609', 'symptom_text': 'Cruise control not working', 'severity': 'medium'},
            {'code_id': 'P0609', 'symptom_text': 'Multiple warning lights on dashboard', 'severity': 'medium'},
            {'code_id': 'P0609', 'symptom_text': 'Speedometer reading incorrectly or not working', 'severity': 'high'},
            {'code_id': 'P0609', 'symptom_text': 'Anti-lock brake system (ABS) warning light', 'severity': 'high'},
            {'code_id': 'P0609', 'symptom_text': 'Poor idle quality or transmission shifting problems', 'severity': 'medium'},
        ],
        'repair_steps': [
            {'code_id': 'P0609', 'step_number': 1, 'description': 'Check battery voltage and charging system - code often triggered by low voltage (below 9.5V)', 'difficulty': 'easy'},
            {'code_id': 'P0609', 'step_number': 2, 'description': 'Inspect all ground straps on engine control module for looseness or corrosion', 'difficulty': 'easy'},
            {'code_id': 'P0609', 'step_number': 3, 'description': 'Examine wiring harnesses for visible damage from collisions, water intrusion, or rodents', 'difficulty': 'medium'},
            {'code_id': 'P0609', 'step_number': 4, 'description': 'Check all connectors to control module - ensure properly seated with no bent pins', 'difficulty': 'medium'},
            {'code_id': 'P0609', 'step_number': 5, 'description': 'Test voltage at speed sensor circuit with key on (should be above 9.5V)', 'difficulty': 'medium'},
            {'code_id': 'P0609', 'step_number': 6, 'description': 'Verify speedometer operation as indicator of speed signal function', 'difficulty': 'easy'},
            {'code_id': 'P0609', 'step_number': 7, 'description': 'Only consider ECM replacement after eliminating all wiring, voltage, and ground issues', 'difficulty': 'hard'},
        ],
        'parts': [
            {'code_id': 'P0609', 'part_name': 'Engine Control Module (ECM)', 'part_number': None},
            {'code_id': 'P0609', 'part_name': 'Battery', 'part_number': None},
            {'code_id': 'P0609', 'part_name': 'Ground Straps', 'part_number': None},
            {'code_id': 'P0609', 'part_name': 'Wiring Harness Connectors', 'part_number': None},
            {'code_id': 'P0609', 'part_name': 'Fuses', 'part_number': None},
        ],
        'related_codes': [
            {'code_id': 'P0609', 'related_code_id': 'P0600', 'relationship_type': 'related_system'},
            {'code_id': 'P0609', 'related_code_id': 'P0601', 'relationship_type': 'related_system'},
            {'code_id': 'P0609', 'related_code_id': 'P0602', 'relationship_type': 'related_system'},
        ],
    },
    {
        'code': 'P0300',
        'common_symptoms': [
            {'code_id': 'P0300', 'symptom_text': 'Check engine light on (may flash if misfire is severe)', 'severity': 'high'},
            {'code_id': 'P0300', 'symptom_text': 'Rough idle with engine shaking or jerking', 'severity': 'high'},
            {'code_id': 'P0300', 'symptom_text': 'Poor acceleration and hesitation', 'severity': 'medium'},
            {'code_id': 'P0300', 'symptom_text': 'Hard starting or extended cranking', 'severity': 'medium'},
            {'code_id': 'P0300', 'symptom_text': 'Reduced fuel economy', 'severity': 'low'},
        ],
        'repair_steps': [
            {'code_id': 'P0300', 'step_number': 1, 'description': 'Check spark plugs for wear, fouling, or incorrect gap - replace if needed', 'difficulty': 'easy'},
            {'code_id': 'P0300', 'step_number': 2, 'description': 'Inspect ignition coils and spark plug wires for damage or weak spark', 'difficulty': 'easy'},
            {'code_id': 'P0300', 'step_number': 3, 'description': 'Look for vacuum leaks in hoses and intake manifold gaskets', 'difficulty': 'medium'},
            {'code_id': 'P0300', 'step_number': 4, 'description': 'Test fuel pressure and inspect fuel injectors for clogs or leaks', 'difficulty': 'medium'},
            {'code_id': 'P0300', 'step_number': 5, 'description': 'Check for engine codes indicating specific cylinder misfires for additional clues', 'difficulty': 'easy'},
            {'code_id': 'P0300', 'step_number': 6, 'description': 'Examine crankshaft position sensor operation with scan tool', 'difficulty': 'medium'},
            {'code_id': 'P0300', 'step_number': 7, 'description': 'If problem persists, check engine compression and timing chain/belt condition', 'difficulty': 'hard'},
        ],
        'parts': [
            {'code_id': 'P0300', 'part_name': 'Spark Plugs', 'part_number': None},
            {'code_id': 'P0300', 'part_name': 'Ignition Coils', 'part_number': None},
            {'code_id': 'P0300', 'part_name': 'Spark Plug Wires', 'part_number': None},
            {'code_id': 'P0300', 'part_name': 'Fuel Injectors', 'part_number': None},
            {'code_id': 'P0300', 'part_name': 'Vacuum Hoses', 'part_number': None},
            {'code_id': 'P0300', 'part_name': 'Intake Manifold Gasket', 'part_number': None},
            {'code_id': 'P0300', 'part_name': 'Crankshaft Position Sensor', 'part_number': None},
            {'code_id': 'P0300', 'part_name': 'Mass Air Flow Sensor', 'part_number': None},
            {'code_id': 'P0300', 'part_name': 'Fuel Pump', 'part_number': None},
        ],
        'related_codes': [
            {'code_id': 'P0300', 'related_code_id': 'P0301', 'relationship_type': 'related_system'},
            {'code_id': 'P0300', 'related_code_id': 'P0302', 'relationship_type': 'related_system'},
            {'code_id': 'P0300', 'related_code_id': 'P0171', 'relationship_type': 'often_appears_with'},
            {'code_id': 'P0300', 'related_code_id': 'P0401', 'relationship_type': 'often_appears_with'},
        ],
    },
    {
        'code': 'P0420',
        'common_symptoms': [
            {'code_id': 'P0420', 'symptom_text': 'Check engine light illuminated', 'severity': 'medium'},
            {'code_id': 'P0420', 'symptom_text': 'Failed emissions testing', 'severity': 'high'},
            {'code_id': 'P0420', 'symptom_text': 'Rotten egg smell from exhaust', 'severity': 'medium'},
            {'code_id': 'P0420', 'symptom_text': 'Reduced engine power', 'severity': 'medium'},
            {'code_id': 'P0420', 'symptom_text': 'Poor acceleration', 'severity': 'medium'},
        ],
        'repair_steps': [
            {'code_id': 'P0420', 'step_number': 1, 'description': 'Check for and repair any other codes first - misfires and lean conditions damage catalytic converters', 'difficulty': 'medium'},
            {'code_id': 'P0420', 'step_number': 2, 'description': 'Inspect for exhaust leaks before catalytic converter that could affect sensor readings', 'difficulty': 'medium'},
            {'code_id': 'P0420', 'step_number': 3, 'description': 'Test oxygen sensors (both upstream and downstream) to ensure they\'re functioning properly', 'difficulty': 'medium'},
            {'code_id': 'P0420', 'step_number': 4, 'description': 'Drive vehicle under conditions similar to when code was set and monitor sensor voltages', 'difficulty': 'medium'},
            {'code_id': 'P0420', 'step_number': 5, 'description': 'Verify downstream oxygen sensor isn\'t simply mirroring upstream readings (indicates cat failure)', 'difficulty': 'medium'},
            {'code_id': 'P0420', 'step_number': 6, 'description': 'Check for damaged or loose exhaust manifold', 'difficulty': 'medium'},
            {'code_id': 'P0420', 'step_number': 7, 'description': 'Replace catalytic converter if all sensors and exhaust system check out properly', 'difficulty': 'hard'},
        ],
        'parts': [
            {'code_id': 'P0420', 'part_name': 'Catalytic Converter', 'part_number': None},
            {'code_id': 'P0420', 'part_name': 'Upstream Oxygen Sensor (Bank 1 Sensor 1)', 'part_number': None},
            {'code_id': 'P0420', 'part_name': 'Downstream Oxygen Sensor (Bank 1 Sensor 2)', 'part_number': None},
            {'code_id': 'P0420', 'part_name': 'Exhaust Manifold', 'part_number': None},
            {'code_id': 'P0420', 'part_name': 'Exhaust Gaskets', 'part_number': None},
            {'code_id': 'P0420', 'part_name': 'Spark Plugs', 'part_number': None},
        ],
        'related_codes': [
            {'code_id': 'P0420', 'related_code_id': 'P0430', 'relationship_type': 'similar_condition'},
            {'code_id': 'P0420', 'related_code_id': 'P0421', 'relationship_type': 'related_system'},
            {'code_id': 'P0420', 'related_code_id': 'P0171', 'relationship_type': 'often_appears_with'},
            {'code_id': 'P0420', 'related_code_id': 'P0174', 'relationship_type': 'often_appears_with'},
        ],
    },

    # ========================================================================
    # SECOND TIER - Production + User Priority Codes
    # ========================================================================
    {
        'code': 'P0301',
        'common_symptoms': [
            {'code_id': 'P0301', 'symptom_text': 'Check engine light on (may flash if misfire is severe)', 'severity': 'high'},
            {'code_id': 'P0301', 'symptom_text': 'Loss of power and sluggish acceleration', 'severity': 'medium'},
            {'code_id': 'P0301', 'symptom_text': 'Engine shaking, bucking, or shuddering', 'severity': 'high'},
            {'code_id': 'P0301', 'symptom_text': 'Significant drop in fuel economy', 'severity': 'low'},
            {'code_id': 'P0301', 'symptom_text': 'Rough idle with noticeable vibration', 'severity': 'medium'},
        ],
        'repair_steps': [
            {'code_id': 'P0301', 'step_number': 1, 'description': 'Swap the spark plug and ignition coil from cylinder 1 with another cylinder to see if misfire moves', 'difficulty': 'easy'},
            {'code_id': 'P0301', 'step_number': 2, 'description': 'If misfire follows the spark plug, replace spark plugs', 'difficulty': 'easy'},
            {'code_id': 'P0301', 'step_number': 3, 'description': 'If misfire follows the coil, replace ignition coil for that cylinder', 'difficulty': 'easy'},
            {'code_id': 'P0301', 'step_number': 4, 'description': 'Check spark plug wires (if equipped) for damage or arcing', 'difficulty': 'easy'},
            {'code_id': 'P0301', 'step_number': 5, 'description': 'If ignition system checks out, perform compression test on affected cylinder', 'difficulty': 'medium'},
            {'code_id': 'P0301', 'step_number': 6, 'description': 'Test fuel injector operation using noid light or oscilloscope to verify proper pulse', 'difficulty': 'medium'},
            {'code_id': 'P0301', 'step_number': 7, 'description': 'For persistent issues, perform leak-down test to identify valve or gasket problems', 'difficulty': 'hard'},
        ],
        'parts': [
            {'code_id': 'P0301', 'part_name': 'Spark Plugs', 'part_number': None},
            {'code_id': 'P0301', 'part_name': 'Ignition Coil (Cylinder 1)', 'part_number': None},
            {'code_id': 'P0301', 'part_name': 'Spark Plug Wires', 'part_number': None},
            {'code_id': 'P0301', 'part_name': 'Fuel Injector (Cylinder 1)', 'part_number': None},
        ],
        'related_codes': [
            {'code_id': 'P0301', 'related_code_id': 'P0300', 'relationship_type': 'related_system'},
            {'code_id': 'P0301', 'related_code_id': 'P0302', 'relationship_type': 'similar_condition'},
            {'code_id': 'P0301', 'related_code_id': 'P0171', 'relationship_type': 'often_appears_with'},
            {'code_id': 'P0301', 'related_code_id': 'P0420', 'relationship_type': 'often_appears_with'},
        ],
    },
    {
        'code': 'P0302',
        'common_symptoms': [
            {'code_id': 'P0302', 'symptom_text': 'Check engine light on (may flash if misfire is severe)', 'severity': 'high'},
            {'code_id': 'P0302', 'symptom_text': 'Loss of power and sluggish acceleration', 'severity': 'medium'},
            {'code_id': 'P0302', 'symptom_text': 'Engine shaking, bucking, or shuddering', 'severity': 'high'},
            {'code_id': 'P0302', 'symptom_text': 'Significant drop in fuel economy', 'severity': 'low'},
            {'code_id': 'P0302', 'symptom_text': 'Rough idle with noticeable vibration', 'severity': 'medium'},
        ],
        'repair_steps': [
            {'code_id': 'P0302', 'step_number': 1, 'description': 'Swap the spark plug and ignition coil from cylinder 2 with another cylinder to see if misfire moves', 'difficulty': 'easy'},
            {'code_id': 'P0302', 'step_number': 2, 'description': 'If misfire follows the spark plug, replace spark plugs', 'difficulty': 'easy'},
            {'code_id': 'P0302', 'step_number': 3, 'description': 'If misfire follows the coil, replace ignition coil for that cylinder', 'difficulty': 'easy'},
            {'code_id': 'P0302', 'step_number': 4, 'description': 'Check spark plug wires (if equipped) for damage or arcing', 'difficulty': 'easy'},
            {'code_id': 'P0302', 'step_number': 5, 'description': 'If ignition system checks out, perform compression test on affected cylinder', 'difficulty': 'medium'},
            {'code_id': 'P0302', 'step_number': 6, 'description': 'Test fuel injector operation using noid light or oscilloscope to verify proper pulse', 'difficulty': 'medium'},
            {'code_id': 'P0302', 'step_number': 7, 'description': 'For persistent issues, perform leak-down test to identify valve or gasket problems', 'difficulty': 'hard'},
        ],
        'parts': [
            {'code_id': 'P0302', 'part_name': 'Spark Plugs', 'part_number': None},
            {'code_id': 'P0302', 'part_name': 'Ignition Coil (Cylinder 2)', 'part_number': None},
            {'code_id': 'P0302', 'part_name': 'Spark Plug Wires', 'part_number': None},
            {'code_id': 'P0302', 'part_name': 'Fuel Injector (Cylinder 2)', 'part_number': None},
        ],
        'related_codes': [
            {'code_id': 'P0302', 'related_code_id': 'P0300', 'relationship_type': 'related_system'},
            {'code_id': 'P0302', 'related_code_id': 'P0301', 'relationship_type': 'similar_condition'},
            {'code_id': 'P0302', 'related_code_id': 'P0171', 'relationship_type': 'often_appears_with'},
            {'code_id': 'P0302', 'related_code_id': 'P0420', 'relationship_type': 'often_appears_with'},
        ],
    },
    {
        'code': 'P0304',
        'common_symptoms': [
            {'code_id': 'P0304', 'symptom_text': 'Check engine light on (may flash if misfire is severe)', 'severity': 'high'},
            {'code_id': 'P0304', 'symptom_text': 'Loss of power and sluggish acceleration', 'severity': 'medium'},
            {'code_id': 'P0304', 'symptom_text': 'Engine shaking, bucking, or shuddering', 'severity': 'high'},
            {'code_id': 'P0304', 'symptom_text': 'Significant drop in fuel economy', 'severity': 'low'},
            {'code_id': 'P0304', 'symptom_text': 'Rough idle with noticeable vibration', 'severity': 'medium'},
        ],
        'repair_steps': [
            {'code_id': 'P0304', 'step_number': 1, 'description': 'Swap the spark plug and ignition coil from cylinder 4 with another cylinder to see if misfire moves', 'difficulty': 'easy'},
            {'code_id': 'P0304', 'step_number': 2, 'description': 'If misfire follows the spark plug, replace spark plugs', 'difficulty': 'easy'},
            {'code_id': 'P0304', 'step_number': 3, 'description': 'If misfire follows the coil, replace ignition coil for that cylinder', 'difficulty': 'easy'},
            {'code_id': 'P0304', 'step_number': 4, 'description': 'Check spark plug wires (if equipped) for damage or arcing', 'difficulty': 'easy'},
            {'code_id': 'P0304', 'step_number': 5, 'description': 'If ignition system checks out, perform compression test on affected cylinder', 'difficulty': 'medium'},
            {'code_id': 'P0304', 'step_number': 6, 'description': 'Test fuel injector operation using noid light or oscilloscope to verify proper pulse', 'difficulty': 'medium'},
            {'code_id': 'P0304', 'step_number': 7, 'description': 'For persistent issues, perform leak-down test to identify valve or gasket problems', 'difficulty': 'hard'},
        ],
        'parts': [
            {'code_id': 'P0304', 'part_name': 'Spark Plugs', 'part_number': None},
            {'code_id': 'P0304', 'part_name': 'Ignition Coil (Cylinder 4)', 'part_number': None},
            {'code_id': 'P0304', 'part_name': 'Spark Plug Wires', 'part_number': None},
            {'code_id': 'P0304', 'part_name': 'Fuel Injector (Cylinder 4)', 'part_number': None},
        ],
        'related_codes': [
            {'code_id': 'P0304', 'related_code_id': 'P0300', 'relationship_type': 'related_system'},
            {'code_id': 'P0304', 'related_code_id': 'P0301', 'relationship_type': 'similar_condition'},
            {'code_id': 'P0304', 'related_code_id': 'P0271', 'relationship_type': 'often_appears_with'},
            {'code_id': 'P0304', 'related_code_id': 'P0420', 'relationship_type': 'often_appears_with'},
        ],
    },
    {
        'code': 'P0101',
        'common_symptoms': [
            {'code_id': 'P0101', 'symptom_text': 'Check engine light illuminated', 'severity': 'medium'},
            {'code_id': 'P0101', 'symptom_text': 'Difficulty starting the engine', 'severity': 'high'},
            {'code_id': 'P0101', 'symptom_text': 'Poor idle quality or rough running', 'severity': 'medium'},
            {'code_id': 'P0101', 'symptom_text': 'Reduced power and sluggish acceleration', 'severity': 'medium'},
            {'code_id': 'P0101', 'symptom_text': 'Decreased fuel economy (engine in limp mode)', 'severity': 'low'},
        ],
        'repair_steps': [
            {'code_id': 'P0101', 'step_number': 1, 'description': 'Inspect air filter condition - replace if dirty or clogged', 'difficulty': 'easy'},
            {'code_id': 'P0101', 'step_number': 2, 'description': 'Check for intake air leaks between MAF sensor and throttle body', 'difficulty': 'easy'},
            {'code_id': 'P0101', 'step_number': 3, 'description': 'Examine all vacuum hoses for cracks, splits, or disconnections', 'difficulty': 'easy'},
            {'code_id': 'P0101', 'step_number': 4, 'description': 'Clean MAF sensor element with proper MAF sensor cleaner spray (not brake cleaner)', 'difficulty': 'easy'},
            {'code_id': 'P0101', 'step_number': 5, 'description': 'Inspect MAF sensor electrical connector for corrosion or damage', 'difficulty': 'easy'},
            {'code_id': 'P0101', 'step_number': 6, 'description': 'Check PCV valve operation and replace if stuck', 'difficulty': 'easy'},
            {'code_id': 'P0101', 'step_number': 7, 'description': 'Look for signs of oil contamination on MAF sensor (from oiled aftermarket air filters)', 'difficulty': 'easy'},
            {'code_id': 'P0101', 'step_number': 8, 'description': 'Test MAF sensor voltage output with scan tool at different RPMs', 'difficulty': 'medium'},
            {'code_id': 'P0101', 'step_number': 9, 'description': 'Replace MAF sensor if cleaning doesn\'t resolve the issue', 'difficulty': 'medium'},
        ],
        'parts': [
            {'code_id': 'P0101', 'part_name': 'Mass Air Flow Sensor', 'part_number': None},
            {'code_id': 'P0101', 'part_name': 'Air Filter', 'part_number': None},
            {'code_id': 'P0101', 'part_name': 'Vacuum Hoses', 'part_number': None},
            {'code_id': 'P0101', 'part_name': 'PCV Valve', 'part_number': None},
            {'code_id': 'P0101', 'part_name': 'Intake Ducting', 'part_number': None},
            {'code_id': 'P0101', 'part_name': 'MAF Sensor Connector', 'part_number': None},
        ],
        'related_codes': [
            {'code_id': 'P0101', 'related_code_id': 'P0100', 'relationship_type': 'related_system'},
            {'code_id': 'P0101', 'related_code_id': 'P0102', 'relationship_type': 'related_system'},
            {'code_id': 'P0101', 'related_code_id': 'P0103', 'relationship_type': 'related_system'},
            {'code_id': 'P0101', 'related_code_id': 'P0171', 'relationship_type': 'often_appears_with'},
        ],
    },
    {
        'code': 'P0102',
        'common_symptoms': [
            {'code_id': 'P0102', 'symptom_text': 'Check engine light on', 'severity': 'medium'},
            {'code_id': 'P0102', 'symptom_text': 'Hard starting or extended cranking', 'severity': 'high'},
            {'code_id': 'P0102', 'symptom_text': 'Rough idle', 'severity': 'medium'},
            {'code_id': 'P0102', 'symptom_text': 'Reduced engine power', 'severity': 'medium'},
            {'code_id': 'P0102', 'symptom_text': 'Poor fuel economy due to limp mode operation', 'severity': 'low'},
        ],
        'repair_steps': [
            {'code_id': 'P0102', 'step_number': 1, 'description': 'Inspect MAF sensor for oil contamination or debris on sensing element', 'difficulty': 'easy'},
            {'code_id': 'P0102', 'step_number': 2, 'description': 'Clean MAF sensor using isopropyl alcohol or dedicated MAF cleaner spray', 'difficulty': 'easy'},
            {'code_id': 'P0102', 'step_number': 3, 'description': 'Check for low battery voltage or poor electrical connections', 'difficulty': 'easy'},
            {'code_id': 'P0102', 'step_number': 4, 'description': 'Examine MAF sensor wiring and connector for corrosion, damage, or loose pins', 'difficulty': 'easy'},
            {'code_id': 'P0102', 'step_number': 5, 'description': 'Inspect intake system for vacuum leaks or damaged hoses', 'difficulty': 'medium'},
            {'code_id': 'P0102', 'step_number': 6, 'description': 'Check PCV valve for proper operation', 'difficulty': 'easy'},
            {'code_id': 'P0102', 'step_number': 7, 'description': 'Replace air filter with OEM-quality filter (avoid over-oiled aftermarket filters)', 'difficulty': 'easy'},
            {'code_id': 'P0102', 'step_number': 8, 'description': 'Test MAF sensor output voltage with scan tool (should increase with engine speed)', 'difficulty': 'medium'},
            {'code_id': 'P0102', 'step_number': 9, 'description': 'Replace MAF sensor if contamination cleaning doesn\'t fix the issue', 'difficulty': 'medium'},
        ],
        'parts': [
            {'code_id': 'P0102', 'part_name': 'Mass Air Flow Sensor', 'part_number': None},
            {'code_id': 'P0102', 'part_name': 'Air Filter (OEM recommended)', 'part_number': None},
            {'code_id': 'P0102', 'part_name': 'MAF Sensor Wiring/Connector', 'part_number': None},
            {'code_id': 'P0102', 'part_name': 'Vacuum Hoses', 'part_number': None},
            {'code_id': 'P0102', 'part_name': 'PCV Valve', 'part_number': None},
            {'code_id': 'P0102', 'part_name': 'Battery', 'part_number': None},
        ],
        'related_codes': [
            {'code_id': 'P0102', 'related_code_id': 'P0100', 'relationship_type': 'related_system'},
            {'code_id': 'P0102', 'related_code_id': 'P0101', 'relationship_type': 'related_system'},
            {'code_id': 'P0102', 'related_code_id': 'P0103', 'relationship_type': 'opposite_condition'},
            {'code_id': 'P0102', 'related_code_id': 'P0171', 'relationship_type': 'often_appears_with'},
        ],
    },
    {
        'code': 'P0103',
        'common_symptoms': [
            {'code_id': 'P0103', 'symptom_text': 'Check engine light illuminated', 'severity': 'medium'},
            {'code_id': 'P0103', 'symptom_text': 'Difficulty starting engine', 'severity': 'high'},
            {'code_id': 'P0103', 'symptom_text': 'Rough idle', 'severity': 'medium'},
            {'code_id': 'P0103', 'symptom_text': 'Reduced power output', 'severity': 'medium'},
            {'code_id': 'P0103', 'symptom_text': 'Poor fuel economy with limp mode active', 'severity': 'low'},
        ],
        'repair_steps': [
            {'code_id': 'P0103', 'step_number': 1, 'description': 'Check for voltage interference in MAF sensor wiring from nearby power sources', 'difficulty': 'medium'},
            {'code_id': 'P0103', 'step_number': 2, 'description': 'Test alternator output voltage - excessive voltage can trigger this code', 'difficulty': 'medium'},
            {'code_id': 'P0103', 'step_number': 3, 'description': 'Inspect MAF sensor wiring for short circuits or exposed wires touching metal', 'difficulty': 'medium'},
            {'code_id': 'P0103', 'step_number': 4, 'description': 'Examine electrical connector at MAF sensor for corrosion or moisture', 'difficulty': 'easy'},
            {'code_id': 'P0103', 'step_number': 5, 'description': 'Check for vacuum leaks or damaged intake hoses', 'difficulty': 'easy'},
            {'code_id': 'P0103', 'step_number': 6, 'description': 'Test MAF sensor voltage with scan tool (should be consistent with airflow)', 'difficulty': 'medium'},
            {'code_id': 'P0103', 'step_number': 7, 'description': 'Verify ground connections are secure and not corroded', 'difficulty': 'easy'},
            {'code_id': 'P0103', 'step_number': 8, 'description': 'Replace MAF sensor if electrical system checks out properly', 'difficulty': 'medium'},
        ],
        'parts': [
            {'code_id': 'P0103', 'part_name': 'Mass Air Flow Sensor', 'part_number': None},
            {'code_id': 'P0103', 'part_name': 'Alternator', 'part_number': None},
            {'code_id': 'P0103', 'part_name': 'MAF Sensor Wiring Harness', 'part_number': None},
            {'code_id': 'P0103', 'part_name': 'Electrical Connectors', 'part_number': None},
            {'code_id': 'P0103', 'part_name': 'Intake Hoses', 'part_number': None},
        ],
        'related_codes': [
            {'code_id': 'P0103', 'related_code_id': 'P0100', 'relationship_type': 'related_system'},
            {'code_id': 'P0103', 'related_code_id': 'P0101', 'relationship_type': 'related_system'},
            {'code_id': 'P0103', 'related_code_id': 'P0102', 'relationship_type': 'opposite_condition'},
            {'code_id': 'P0103', 'related_code_id': 'P0171', 'relationship_type': 'often_appears_with'},
        ],
    },
    {
        'code': 'P0402',
        'common_symptoms': [
            {'code_id': 'P0402', 'symptom_text': 'Check engine light on', 'severity': 'medium'},
            {'code_id': 'P0402', 'symptom_text': 'Rough idle or idle surging', 'severity': 'medium'},
            {'code_id': 'P0402', 'symptom_text': 'Engine stalling at idle', 'severity': 'high'},
            {'code_id': 'P0402', 'symptom_text': 'Hesitation during acceleration', 'severity': 'medium'},
            {'code_id': 'P0402', 'symptom_text': 'Reduced fuel economy', 'severity': 'low'},
        ],
        'repair_steps': [
            {'code_id': 'P0402', 'step_number': 1, 'description': 'Inspect EGR valve for carbon buildup preventing it from closing fully', 'difficulty': 'medium'},
            {'code_id': 'P0402', 'step_number': 2, 'description': 'Clean EGR valve passages and intake manifold EGR ports with carburetor cleaner', 'difficulty': 'medium'},
            {'code_id': 'P0402', 'step_number': 3, 'description': 'Check EGR valve operation - it should be closed at idle and open under load', 'difficulty': 'medium'},
            {'code_id': 'P0402', 'step_number': 4, 'description': 'Test DPFE sensor (Ford vehicles) or EGR pressure sensor for proper readings', 'difficulty': 'medium'},
            {'code_id': 'P0402', 'step_number': 5, 'description': 'Inspect vacuum hoses to EGR system for leaks or incorrect routing', 'difficulty': 'easy'},
            {'code_id': 'P0402', 'step_number': 6, 'description': 'Check for blockages in EGR tube or passages', 'difficulty': 'medium'},
            {'code_id': 'P0402', 'step_number': 7, 'description': 'Test EGR valve electrical connector and wiring for proper signal', 'difficulty': 'medium'},
            {'code_id': 'P0402', 'step_number': 8, 'description': 'Verify intake manifold gaskets aren\'t allowing unmetered air', 'difficulty': 'hard'},
            {'code_id': 'P0402', 'step_number': 9, 'description': 'Replace EGR valve if cleaning doesn\'t resolve excessive flow', 'difficulty': 'medium'},
        ],
        'parts': [
            {'code_id': 'P0402', 'part_name': 'EGR Valve', 'part_number': None},
            {'code_id': 'P0402', 'part_name': 'DPFE Sensor (Ford)', 'part_number': None},
            {'code_id': 'P0402', 'part_name': 'EGR Pressure Transducer', 'part_number': None},
            {'code_id': 'P0402', 'part_name': 'EGR Tube', 'part_number': None},
            {'code_id': 'P0402', 'part_name': 'Vacuum Hoses', 'part_number': None},
            {'code_id': 'P0402', 'part_name': 'Intake Manifold Gaskets', 'part_number': None},
        ],
        'related_codes': [
            {'code_id': 'P0402', 'related_code_id': 'P0401', 'relationship_type': 'opposite_condition'},
            {'code_id': 'P0402', 'related_code_id': 'P0404', 'relationship_type': 'related_system'},
            {'code_id': 'P0402', 'related_code_id': 'P0403', 'relationship_type': 'related_system'},
            {'code_id': 'P0402', 'related_code_id': 'P0171', 'relationship_type': 'often_appears_with'},
        ],
    },
    {
        'code': 'P0142',
        'common_symptoms': [
            {'code_id': 'P0142', 'symptom_text': 'Check engine light illuminated', 'severity': 'medium'},
            {'code_id': 'P0142', 'symptom_text': 'Reduced fuel economy', 'severity': 'low'},
            {'code_id': 'P0142', 'symptom_text': 'Rough idle or engine hesitation', 'severity': 'medium'},
            {'code_id': 'P0142', 'symptom_text': 'Black smoke from exhaust (in severe cases)', 'severity': 'high'},
            {'code_id': 'P0142', 'symptom_text': 'May have no noticeable symptoms beyond warning light', 'severity': 'low'},
        ],
        'repair_steps': [
            {'code_id': 'P0142', 'step_number': 1, 'description': 'Inspect oxygen sensor wiring and connector for damage, corrosion, or oil contamination', 'difficulty': 'easy'},
            {'code_id': 'P0142', 'step_number': 2, 'description': 'Check for exhaust leaks near the sensor that could affect readings', 'difficulty': 'medium'},
            {'code_id': 'P0142', 'step_number': 3, 'description': 'Test sensor heater circuit resistance (should be 8-12 ohms typically)', 'difficulty': 'medium'},
            {'code_id': 'P0142', 'step_number': 4, 'description': 'Verify sensor ground connection is clean and secure', 'difficulty': 'easy'},
            {'code_id': 'P0142', 'step_number': 5, 'description': 'Check sensor voltage output with scan tool (should cycle between 0.1-0.9V when warm)', 'difficulty': 'medium'},
            {'code_id': 'P0142', 'step_number': 6, 'description': 'Look for oil fouling on sensor tip (common in BMW, Audi, VW, Mercedes)', 'difficulty': 'medium'},
            {'code_id': 'P0142', 'step_number': 7, 'description': 'Test continuity in wiring harness between sensor and ECM', 'difficulty': 'medium'},
            {'code_id': 'P0142', 'step_number': 8, 'description': 'Replace oxygen sensor if electrical tests indicate sensor failure', 'difficulty': 'medium'},
            {'code_id': 'P0142', 'step_number': 9, 'description': 'Clear codes and drive through multiple cycles to confirm repair', 'difficulty': 'easy'},
        ],
        'parts': [
            {'code_id': 'P0142', 'part_name': 'Oxygen Sensor (Bank 1 Sensor 3)', 'part_number': None},
            {'code_id': 'P0142', 'part_name': 'Sensor Wiring Harness', 'part_number': None},
            {'code_id': 'P0142', 'part_name': 'Electrical Connectors', 'part_number': None},
            {'code_id': 'P0142', 'part_name': 'Exhaust Gaskets', 'part_number': None},
        ],
        'related_codes': [
            {'code_id': 'P0142', 'related_code_id': 'P0136', 'relationship_type': 'related_system'},
            {'code_id': 'P0142', 'related_code_id': 'P0140', 'relationship_type': 'related_system'},
            {'code_id': 'P0142', 'related_code_id': 'P0141', 'relationship_type': 'related_system'},
            {'code_id': 'P0142', 'related_code_id': 'P0420', 'relationship_type': 'often_appears_with'},
        ],
    },
    {
        'code': 'P0271',
        'common_symptoms': [
            {'code_id': 'P0271', 'symptom_text': 'Check engine light illuminated', 'severity': 'medium'},
            {'code_id': 'P0271', 'symptom_text': 'Rough idle', 'severity': 'medium'},
            {'code_id': 'P0271', 'symptom_text': 'Engine misfire on cylinder 4', 'severity': 'high'},
            {'code_id': 'P0271', 'symptom_text': 'Reduced power and acceleration', 'severity': 'medium'},
            {'code_id': 'P0271', 'symptom_text': 'Black smoke from exhaust', 'severity': 'medium'},
        ],
        'repair_steps': [
            {'code_id': 'P0271', 'step_number': 1, 'description': 'Inspect fuel injector wiring harness for damage, chafing, or exposed wires', 'difficulty': 'easy'},
            {'code_id': 'P0271', 'step_number': 2, 'description': 'Check injector connector for corrosion, bent pins, or loose connection', 'difficulty': 'easy'},
            {'code_id': 'P0271', 'step_number': 3, 'description': 'Test injector resistance with multimeter (typically 12-16 ohms when cold)', 'difficulty': 'medium'},
            {'code_id': 'P0271', 'step_number': 4, 'description': 'Check for short circuit to power in wiring between ECM and injector', 'difficulty': 'medium'},
            {'code_id': 'P0271', 'step_number': 5, 'description': 'Swap injector from cylinder 4 with another cylinder to see if code follows', 'difficulty': 'medium'},
            {'code_id': 'P0271', 'step_number': 6, 'description': 'Test injector operation using noid light to verify proper pulse signal', 'difficulty': 'medium'},
            {'code_id': 'P0271', 'step_number': 7, 'description': 'Replace fuel injector if testing shows high resistance or intermittent operation', 'difficulty': 'medium'},
            {'code_id': 'P0271', 'step_number': 8, 'description': 'Repair or replace wiring harness if short to voltage is found', 'difficulty': 'hard'},
        ],
        'parts': [
            {'code_id': 'P0271', 'part_name': 'Fuel Injector (Cylinder 4)', 'part_number': None},
            {'code_id': 'P0271', 'part_name': 'Injector Wiring Harness', 'part_number': None},
            {'code_id': 'P0271', 'part_name': 'Injector Connector', 'part_number': None},
            {'code_id': 'P0271', 'part_name': 'Fuel Injector O-rings', 'part_number': None},
        ],
        'related_codes': [
            {'code_id': 'P0271', 'related_code_id': 'P0267', 'relationship_type': 'similar_condition'},
            {'code_id': 'P0271', 'related_code_id': 'P0270', 'relationship_type': 'opposite_condition'},
            {'code_id': 'P0271', 'related_code_id': 'P0275', 'relationship_type': 'similar_condition'},
            {'code_id': 'P0271', 'related_code_id': 'P0304', 'relationship_type': 'often_appears_with'},
        ],
    },
    {
        'code': 'P0389',
        'common_symptoms': [
            {'code_id': 'P0389', 'symptom_text': 'Check engine light on', 'severity': 'medium'},
            {'code_id': 'P0389', 'symptom_text': 'Hard starting or no-start condition', 'severity': 'high'},
            {'code_id': 'P0389', 'symptom_text': 'Engine stalling', 'severity': 'high'},
            {'code_id': 'P0389', 'symptom_text': 'Rough idle', 'severity': 'medium'},
            {'code_id': 'P0389', 'symptom_text': 'Hesitation or stumbling during acceleration', 'severity': 'medium'},
        ],
        'repair_steps': [
            {'code_id': 'P0389', 'step_number': 1, 'description': 'Visually inspect crankshaft position sensor and connector for damage or corrosion', 'difficulty': 'easy'},
            {'code_id': 'P0389', 'step_number': 2, 'description': 'Check sensor wiring harness for cuts, chafing, or rodent damage', 'difficulty': 'easy'},
            {'code_id': 'P0389', 'step_number': 3, 'description': 'Test sensor connector for tight fit and clean pins', 'difficulty': 'easy'},
            {'code_id': 'P0389', 'step_number': 4, 'description': 'Measure sensor resistance with multimeter and compare to specifications', 'difficulty': 'medium'},
            {'code_id': 'P0389', 'step_number': 5, 'description': 'Check sensor air gap clearance to reluctor ring (typically 0.020-0.050 inches)', 'difficulty': 'medium'},
            {'code_id': 'P0389', 'step_number': 6, 'description': 'Test sensor output voltage while cranking engine (should produce AC voltage signal)', 'difficulty': 'medium'},
            {'code_id': 'P0389', 'step_number': 7, 'description': 'Look for loose sensor mounting or damaged mounting bracket', 'difficulty': 'easy'},
            {'code_id': 'P0389', 'step_number': 8, 'description': 'Check for interference from alternator or other electrical sources', 'difficulty': 'medium'},
            {'code_id': 'P0389', 'step_number': 9, 'description': 'Replace crankshaft position sensor if tests show intermittent signal', 'difficulty': 'medium'},
        ],
        'parts': [
            {'code_id': 'P0389', 'part_name': 'Crankshaft Position Sensor B', 'part_number': None},
            {'code_id': 'P0389', 'part_name': 'Sensor Wiring Harness', 'part_number': None},
            {'code_id': 'P0389', 'part_name': 'Electrical Connector', 'part_number': None},
            {'code_id': 'P0389', 'part_name': 'Sensor Mounting Bracket', 'part_number': None},
        ],
        'related_codes': [
            {'code_id': 'P0389', 'related_code_id': 'P0385', 'relationship_type': 'related_system'},
            {'code_id': 'P0389', 'related_code_id': 'P0386', 'relationship_type': 'related_system'},
            {'code_id': 'P0389', 'related_code_id': 'P0387', 'relationship_type': 'related_system'},
            {'code_id': 'P0389', 'related_code_id': 'P0300', 'relationship_type': 'often_appears_with'},
        ],
    },
    {
        'code': 'P0442',
        'common_symptoms': [
            {'code_id': 'P0442', 'symptom_text': 'Check engine light illuminated', 'severity': 'medium'},
            {'code_id': 'P0442', 'symptom_text': 'Faint gasoline smell near vehicle when parked', 'severity': 'low'},
            {'code_id': 'P0442', 'symptom_text': 'Dashboard message about loose gas cap', 'severity': 'low'},
            {'code_id': 'P0442', 'symptom_text': 'Difficulty fueling (slow fill or pump clicking off)', 'severity': 'medium'},
            {'code_id': 'P0442', 'symptom_text': 'Often no noticeable symptoms beyond warning light', 'severity': 'low'},
        ],
        'repair_steps': [
            {'code_id': 'P0442', 'step_number': 1, 'description': 'Check gas cap first - ensure it clicks at least 3 times when tightening', 'difficulty': 'easy'},
            {'code_id': 'P0442', 'step_number': 2, 'description': 'Inspect gas cap seal for cracks, damage, or debris', 'difficulty': 'easy'},
            {'code_id': 'P0442', 'step_number': 3, 'description': 'Look for corrosion on fuel filler neck sealing surface', 'difficulty': 'easy'},
            {'code_id': 'P0442', 'step_number': 4, 'description': 'Use smoke machine (professional tool) to locate small leaks in EVAP system', 'difficulty': 'hard'},
            {'code_id': 'P0442', 'step_number': 5, 'description': 'Inspect EVAP hoses and lines for cracks, especially near heat sources', 'difficulty': 'medium'},
            {'code_id': 'P0442', 'step_number': 6, 'description': 'Test vent valve solenoid operation (should be normally open, closes when powered)', 'difficulty': 'medium'},
            {'code_id': 'P0442', 'step_number': 7, 'description': 'Test purge valve with vacuum pump - should hold vacuum when not powered', 'difficulty': 'medium'},
            {'code_id': 'P0442', 'step_number': 8, 'description': 'Check charcoal canister for cracks or damage', 'difficulty': 'medium'},
            {'code_id': 'P0442', 'step_number': 9, 'description': 'Inspect fuel tank and filler neck for rust holes or damage', 'difficulty': 'hard'},
        ],
        'parts': [
            {'code_id': 'P0442', 'part_name': 'Gas Cap', 'part_number': None},
            {'code_id': 'P0442', 'part_name': 'EVAP Vent Valve Solenoid', 'part_number': None},
            {'code_id': 'P0442', 'part_name': 'EVAP Purge Valve Solenoid', 'part_number': None},
            {'code_id': 'P0442', 'part_name': 'Charcoal Canister', 'part_number': None},
            {'code_id': 'P0442', 'part_name': 'EVAP Hoses and Lines', 'part_number': None},
            {'code_id': 'P0442', 'part_name': 'Fuel Filler Neck', 'part_number': None},
            {'code_id': 'P0442', 'part_name': 'Fuel Tank Pressure Sensor', 'part_number': None},
        ],
        'related_codes': [
            {'code_id': 'P0442', 'related_code_id': 'P0455', 'relationship_type': 'similar_condition'},
            {'code_id': 'P0442', 'related_code_id': 'P0456', 'relationship_type': 'similar_condition'},
            {'code_id': 'P0442', 'related_code_id': 'P0446', 'relationship_type': 'related_system'},
            {'code_id': 'P0442', 'related_code_id': 'P0440', 'relationship_type': 'related_system'},
        ],
    },
    {
        'code': 'P0507',
        'common_symptoms': [
            {'code_id': 'P0507', 'symptom_text': 'Check engine light on', 'severity': 'medium'},
            {'code_id': 'P0507', 'symptom_text': 'Engine idling too high (usually above 800-1000 RPM)', 'severity': 'medium'},
            {'code_id': 'P0507', 'symptom_text': 'Rough or fluctuating idle speed', 'severity': 'medium'},
            {'code_id': 'P0507', 'symptom_text': 'Difficulty starting engine', 'severity': 'medium'},
            {'code_id': 'P0507', 'symptom_text': 'Engine stalling when coming to a stop', 'severity': 'high'},
        ],
        'repair_steps': [
            {'code_id': 'P0507', 'step_number': 1, 'description': 'Check for vacuum leaks using carburetor cleaner spray around hoses and gaskets', 'difficulty': 'easy'},
            {'code_id': 'P0507', 'step_number': 2, 'description': 'Inspect all vacuum hoses for cracks, disconnections, or deterioration', 'difficulty': 'easy'},
            {'code_id': 'P0507', 'step_number': 3, 'description': 'Clean throttle body and idle air control valve passages with throttle body cleaner', 'difficulty': 'easy'},
            {'code_id': 'P0507', 'step_number': 4, 'description': 'Check PCV valve and hose for proper operation', 'difficulty': 'easy'},
            {'code_id': 'P0507', 'step_number': 5, 'description': 'Test idle air control valve operation with scan tool (should respond to commands)', 'difficulty': 'medium'},
            {'code_id': 'P0507', 'step_number': 6, 'description': 'Inspect intake manifold gaskets for leaks allowing unmetered air', 'difficulty': 'hard'},
            {'code_id': 'P0507', 'step_number': 7, 'description': 'Check for stuck open PCV valve or brake booster vacuum leak', 'difficulty': 'medium'},
            {'code_id': 'P0507', 'step_number': 8, 'description': 'Verify throttle plate closes completely and isn\'t sticking', 'difficulty': 'medium'},
            {'code_id': 'P0507', 'step_number': 9, 'description': 'Test coolant temperature sensor - incorrect readings affect idle control', 'difficulty': 'medium'},
        ],
        'parts': [
            {'code_id': 'P0507', 'part_name': 'Idle Air Control (IAC) Valve', 'part_number': None},
            {'code_id': 'P0507', 'part_name': 'Throttle Body', 'part_number': None},
            {'code_id': 'P0507', 'part_name': 'Vacuum Hoses', 'part_number': None},
            {'code_id': 'P0507', 'part_name': 'PCV Valve', 'part_number': None},
            {'code_id': 'P0507', 'part_name': 'Intake Manifold Gaskets', 'part_number': None},
            {'code_id': 'P0507', 'part_name': 'Throttle Position Sensor', 'part_number': None},
            {'code_id': 'P0507', 'part_name': 'Coolant Temperature Sensor', 'part_number': None},
        ],
        'related_codes': [
            {'code_id': 'P0507', 'related_code_id': 'P0505', 'relationship_type': 'related_system'},
            {'code_id': 'P0507', 'related_code_id': 'P0506', 'relationship_type': 'opposite_condition'},
            {'code_id': 'P0507', 'related_code_id': 'P0508', 'relationship_type': 'related_system'},
            {'code_id': 'P0507', 'related_code_id': 'P0171', 'relationship_type': 'often_appears_with'},
        ],
    },
    {
        'code': 'C0035',
        'common_symptoms': [
            {'code_id': 'C0035', 'symptom_text': 'ABS warning light illuminated', 'severity': 'high'},
            {'code_id': 'C0035', 'symptom_text': 'Traction control light on or system disabled', 'severity': 'medium'},
            {'code_id': 'C0035', 'symptom_text': 'ABS system not functioning', 'severity': 'high'},
            {'code_id': 'C0035', 'symptom_text': 'Speedometer reading incorrectly or erratically', 'severity': 'medium'},
            {'code_id': 'C0035', 'symptom_text': 'Stability control disabled', 'severity': 'high'},
        ],
        'repair_steps': [
            {'code_id': 'C0035', 'step_number': 1, 'description': 'Inspect left front wheel speed sensor wiring harness for damage, cuts, or chafing', 'difficulty': 'easy'},
            {'code_id': 'C0035', 'step_number': 2, 'description': 'Check sensor connector for corrosion, moisture, or bent pins', 'difficulty': 'easy'},
            {'code_id': 'C0035', 'step_number': 3, 'description': 'Clean wheel speed sensor and tone ring (reluctor ring) of brake dust and debris', 'difficulty': 'easy'},
            {'code_id': 'C0035', 'step_number': 4, 'description': 'Measure sensor resistance with multimeter and compare to specifications', 'difficulty': 'medium'},
            {'code_id': 'C0035', 'step_number': 5, 'description': 'Check sensor air gap to tone ring (typically 0.020-0.050 inches)', 'difficulty': 'medium'},
            {'code_id': 'C0035', 'step_number': 6, 'description': 'Inspect tone ring for damaged, missing, or worn teeth', 'difficulty': 'medium'},
            {'code_id': 'C0035', 'step_number': 7, 'description': 'Test sensor signal with scan tool while rotating wheel slowly', 'difficulty': 'medium'},
            {'code_id': 'C0035', 'step_number': 8, 'description': 'Compare left front sensor readings to right front sensor for discrepancies', 'difficulty': 'medium'},
            {'code_id': 'C0035', 'step_number': 9, 'description': 'Check for bearing play in wheel hub assembly affecting sensor gap', 'difficulty': 'hard'},
        ],
        'parts': [
            {'code_id': 'C0035', 'part_name': 'Left Front Wheel Speed Sensor', 'part_number': None},
            {'code_id': 'C0035', 'part_name': 'Wheel Speed Sensor Wiring Harness', 'part_number': None},
            {'code_id': 'C0035', 'part_name': 'Sensor Connector', 'part_number': None},
            {'code_id': 'C0035', 'part_name': 'Wheel Bearing/Hub Assembly', 'part_number': None},
            {'code_id': 'C0035', 'part_name': 'ABS Tone Ring', 'part_number': None},
        ],
        'related_codes': [
            {'code_id': 'C0035', 'related_code_id': 'C0040', 'relationship_type': 'similar_condition'},
            {'code_id': 'C0035', 'related_code_id': 'C0045', 'relationship_type': 'similar_condition'},
            {'code_id': 'C0035', 'related_code_id': 'C0050', 'relationship_type': 'similar_condition'},
        ],
    },
    {
        'code': 'P3497',
        'common_symptoms': [
            {'code_id': 'P3497', 'symptom_text': 'Check engine light illuminated', 'severity': 'medium'},
            {'code_id': 'P3497', 'symptom_text': 'Reduced fuel economy (deactivation system not working)', 'severity': 'low'},
            {'code_id': 'P3497', 'symptom_text': 'Rough idle or vibration', 'severity': 'medium'},
            {'code_id': 'P3497', 'symptom_text': 'Engine noise or ticking sounds', 'severity': 'medium'},
            {'code_id': 'P3497', 'symptom_text': 'Reduced power or performance', 'severity': 'medium'},
        ],
        'repair_steps': [
            {'code_id': 'P3497', 'step_number': 1, 'description': 'Check engine oil level - low oil prevents proper cylinder deactivation operation', 'difficulty': 'easy'},
            {'code_id': 'P3497', 'step_number': 2, 'description': 'Verify correct engine oil type is used (must meet manufacturer specifications for VCM/cylinder deactivation)', 'difficulty': 'easy'},
            {'code_id': 'P3497', 'step_number': 3, 'description': 'Change oil and filter if overdue or wrong oil type was used', 'difficulty': 'easy'},
            {'code_id': 'P3497', 'step_number': 4, 'description': 'Check for Technical Service Bulletins specific to your vehicle model and year', 'difficulty': 'easy'},
            {'code_id': 'P3497', 'step_number': 5, 'description': 'Inspect VCM oil pressure relief valve for sticking (known issue in 2013 Honda Pilots)', 'difficulty': 'hard'},
            {'code_id': 'P3497', 'step_number': 6, 'description': 'Test oil pressure switch operation and readings', 'difficulty': 'medium'},
            {'code_id': 'P3497', 'step_number': 7, 'description': 'Apply available software updates from manufacturer (known fix for some 2011 Honda models)', 'difficulty': 'medium'},
            {'code_id': 'P3497', 'step_number': 8, 'description': 'Check valve deactivation solenoids in cylinder head for proper operation', 'difficulty': 'hard'},
        ],
        'parts': [
            {'code_id': 'P3497', 'part_name': 'Engine Oil (correct specification)', 'part_number': None},
            {'code_id': 'P3497', 'part_name': 'Oil Filter', 'part_number': None},
            {'code_id': 'P3497', 'part_name': 'VCM Oil Pressure Relief Valve', 'part_number': None},
            {'code_id': 'P3497', 'part_name': 'Oil Pressure Switch', 'part_number': None},
            {'code_id': 'P3497', 'part_name': 'Cylinder Deactivation Solenoids', 'part_number': None},
        ],
        'related_codes': [
            {'code_id': 'P3497', 'related_code_id': 'P3400', 'relationship_type': 'similar_condition'},
            {'code_id': 'P3497', 'related_code_id': 'P3401', 'relationship_type': 'similar_condition'},
            {'code_id': 'P3497', 'related_code_id': 'P3496', 'relationship_type': 'related_system'},
        ],
    },
]


def insert_code_data(code_data: Dict) -> Dict[str, int]:
    """Insert all data for a single code."""
    code = code_data['code']
    counts = {
        'symptoms': 0,
        'repair_steps': 0,
        'parts': 0,
        'related_codes': 0
    }

    print(f"\n[*] Inserting data for {code}...")

    # Insert symptoms
    if code_data.get('common_symptoms'):
        try:
            response = client.table('common_symptoms').insert(
                code_data['common_symptoms']
            ).execute()
            counts['symptoms'] = len(response.data) if response.data else 0
            print(f"  [OK] {counts['symptoms']} symptoms")
        except Exception as e:
            print(f"  [FAIL] Symptoms failed: {e}")

    # Insert repair steps
    if code_data.get('repair_steps'):
        try:
            response = client.table('repair_steps').insert(
                code_data['repair_steps']
            ).execute()
            counts['repair_steps'] = len(response.data) if response.data else 0
            print(f"  [OK] {counts['repair_steps']} repair steps")
        except Exception as e:
            print(f"  [FAIL] Repair steps failed: {e}")

    # Insert parts
    if code_data.get('parts'):
        try:
            response = client.table('parts').insert(
                code_data['parts']
            ).execute()
            counts['parts'] = len(response.data) if response.data else 0
            print(f"  [OK] {counts['parts']} parts")
        except Exception as e:
            print(f"  [FAIL] Parts failed: {e}")

    # Insert related codes
    if code_data.get('related_codes'):
        try:
            response = client.table('related_codes').insert(
                code_data['related_codes']
            ).execute()
            counts['related_codes'] = len(response.data) if response.data else 0
            print(f"  [OK] {counts['related_codes']} related codes")
        except Exception as e:
            print(f"  [FAIL] Related codes failed: {e}")

    return counts


def main():
    """Main population routine"""
    print("=" * 60)
    print("DTC DETAILS POPULATION")
    print("=" * 60)
    print(f"\nCodes to populate: {len(DTC_DATA)}")
    print("\nCodes included:")
    for data in DTC_DATA:
        print(f"  - {data['code']}")

    # Confirm before proceeding
    print("\n" + "=" * 60)
    response = input("\nProceed with insertion? (yes/no): ")
    if response.lower() != 'yes':
        print("Aborted.")
        return

    # Insert all codes
    total_counts = {
        'symptoms': 0,
        'repair_steps': 0,
        'parts': 0,
        'related_codes': 0
    }

    success_codes = []
    failed_codes = []

    for code_data in DTC_DATA:
        code = code_data['code']
        try:
            counts = insert_code_data(code_data)
            success_codes.append(code)

            # Add to totals
            for key, value in counts.items():
                total_counts[key] += value

        except Exception as e:
            print(f"\n[FAIL] {code} FAILED: {e}")
            failed_codes.append(code)

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"\n[OK] Successfully populated: {len(success_codes)} codes")
    if success_codes:
        print(f"   Codes: {', '.join(success_codes)}")

    if failed_codes:
        print(f"\n[FAIL] Failed: {len(failed_codes)} codes")
        print(f"   Codes: {', '.join(failed_codes)}")

    print(f"\nTotal rows inserted:")
    print(f"  - Common Symptoms: {total_counts['symptoms']}")
    print(f"  - Repair Steps: {total_counts['repair_steps']}")
    print(f"  - Parts: {total_counts['parts']}")
    print(f"  - Related Codes: {total_counts['related_codes']}")

    print(f"\nGrand Total: {sum(total_counts.values())} rows")
    print("\n[SUCCESS] Population complete!")


if __name__ == '__main__':
    main()
