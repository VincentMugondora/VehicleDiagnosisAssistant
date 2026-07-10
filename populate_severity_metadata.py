#!/usr/bin/env python3
"""
Populate enhanced severity metadata for all OBD-II codes.

This script analyzes each code's description and current severity to populate
the multi-dimensional severity_metadata JSONB field with:
- drivability flags
- safety indicators
- repair urgency
- driving restrictions
"""

import os
import json
from supabase import create_client, Client
from dotenv import load_dotenv
from datetime import datetime
from typing import Dict, Any

load_dotenv()

url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY") or os.environ.get("SUPABASE_SERVICE_KEY")
supabase: Client = create_client(url, key)

def analyze_code(code: str, description: str, severity: str, system: str) -> Dict[str, Any]:
    """
    Analyze code and generate enhanced severity metadata.

    Returns confidence score (0-100) and metadata dict.
    """
    desc_lower = description.lower()
    code_upper = code.upper()

    # Initialize with defaults
    metadata = {
        'severity': severity,
        'drivable': True,
        'stop_driving': False,
        'may_cause_engine_damage': False,
        'may_cause_safety_issue': False,
        'affects_emissions_only': False,
        'requires_urgent_repair': False,
        'repair_urgency': 'within_week',
        'drive_restrictions': {
            'max_distance': None,
            'avoid_highway': False,
            'reduced_performance': False
        }
    }

    confidence = 70  # Default confidence

    # CRITICAL CONDITIONS - Stop Driving
    if any(term in desc_lower for term in [
        'over temperature', 'overtemperature', 'over-temperature',
        'coolant temperature high', 'coolant temp high',
        'engine temperature high', 'transmission temperature high',
        'oil pressure low', 'no oil pressure'
    ]) and 'sensor' not in desc_lower and 'circuit' not in desc_lower:
        # Actual condition, not sensor fault
        metadata.update({
            'severity': 'Critical',
            'drivable': False,
            'stop_driving': True,
            'may_cause_engine_damage': True,
            'requires_urgent_repair': True,
            'repair_urgency': 'immediate',
            'drive_restrictions': {
                'max_distance': 0,
                'avoid_highway': True,
                'reduced_performance': True
            }
        })
        confidence = 95

    # SENSOR/CIRCUIT FAULTS - Sensor may be bad, actual condition unknown
    elif any(term in desc_lower for term in [
        'sensor circuit', 'sensor/switch circuit', 'sensor malfunction',
        'circuit malfunction', 'circuit range/performance'
    ]):
        if any(critical in desc_lower for critical in ['oil pressure', 'coolant', 'temperature']):
            # Critical system sensor - cannot trust gauge
            metadata.update({
                'severity': 'High',
                'drivable': True,
                'stop_driving': False,
                'may_cause_engine_damage': False,
                'requires_urgent_repair': True,
                'repair_urgency': 'within_day',
                'drive_restrictions': {
                    'max_distance': 50,
                    'avoid_highway': False,
                    'reduced_performance': False
                }
            })
            confidence = 85
        else:
            # Non-critical sensor
            metadata.update({
                'severity': 'Moderate',
                'repair_urgency': 'within_week'
            })
            confidence = 80

    # EMISSIONS-ONLY CODES
    elif any(term in desc_lower for term in [
        'catalyst', 'evaporative emission', 'evap emission',
        'secondary air', 'egr', 'exhaust gas recirculation'
    ]) and not any(bad in desc_lower for bad in ['stuck', 'stuck open', 'stuck closed', 'malfunction']):
        metadata.update({
            'severity': 'Moderate',
            'affects_emissions_only': True,
            'requires_urgent_repair': False,
            'repair_urgency': 'within_month'
        })
        confidence = 90

    # ABS/TRACTION CONTROL - Safety but not total brake failure
    elif system == 'ABS' or 'abs' in desc_lower or 'anti-lock' in desc_lower:
        metadata.update({
            'severity': 'Moderate',
            'may_cause_safety_issue': True,
            'requires_urgent_repair': True,
            'repair_urgency': 'within_week',
            'drive_restrictions': {
                'avoid_highway': False,
                'reduced_performance': False
            }
        })
        confidence = 80

    # AIRBAG SYSTEM - Safety critical
    elif system == 'SRS' or 'airbag' in desc_lower or 'srs' in desc_lower:
        metadata.update({
            'severity': 'High',
            'may_cause_safety_issue': True,
            'requires_urgent_repair': True,
            'repair_urgency': 'within_day'
        })
        confidence = 85

    # TRANSMISSION ISSUES
    elif 'transmission' in desc_lower:
        if any(term in desc_lower for term in ['slip', 'slipping', 'stuck', 'mechanical']):
            metadata.update({
                'severity': 'High',
                'may_cause_engine_damage': True,
                'requires_urgent_repair': True,
                'repair_urgency': 'within_day',
                'drive_restrictions': {
                    'max_distance': 100,
                    'avoid_highway': True,
                    'reduced_performance': True
                }
            })
            confidence = 85
        else:
            metadata.update({
                'severity': 'Moderate',
                'repair_urgency': 'within_week'
            })
            confidence = 75

    # IDLE/PERFORMANCE ISSUES
    elif any(term in desc_lower for term in ['idle', 'rpm lower', 'rpm higher']):
        metadata.update({
            'severity': 'Moderate',
            'repair_urgency': 'within_week',
            'drive_restrictions': {
                'reduced_performance': True
            }
        })
        confidence = 85

    # MISFIRE CODES
    elif 'misfire' in desc_lower:
        if 'random' in desc_lower or 'multiple' in desc_lower:
            metadata.update({
                'severity': 'High',
                'may_cause_engine_damage': True,
                'requires_urgent_repair': True,
                'repair_urgency': 'within_day',
                'drive_restrictions': {
                    'max_distance': 50,
                    'reduced_performance': True
                }
            })
            confidence = 90
        else:
            metadata.update({
                'severity': 'Moderate',
                'repair_urgency': 'within_week',
                'drive_restrictions': {
                    'reduced_performance': True
                }
            })
            confidence = 85

    # SPECIFIC CODE OVERRIDES
    code_overrides = {
        'P0217': {  # Engine coolant over-temp
            'severity': 'Critical',
            'stop_driving': True,
            'drivable': False,
            'may_cause_engine_damage': True,
            'repair_urgency': 'immediate',
            'drive_restrictions': {'max_distance': 0, 'avoid_highway': True, 'reduced_performance': True}
        },
        'P0218': {  # Transmission fluid over-temp
            'severity': 'Critical',
            'stop_driving': True,
            'drivable': False,
            'may_cause_engine_damage': True,
            'repair_urgency': 'immediate',
            'drive_restrictions': {'max_distance': 0, 'avoid_highway': True, 'reduced_performance': True}
        },
        'P0420': {  # Catalyst efficiency Bank 1
            'severity': 'Moderate',
            'affects_emissions_only': True,
            'repair_urgency': 'within_month'
        },
        'P0430': {  # Catalyst efficiency Bank 2
            'severity': 'Moderate',
            'affects_emissions_only': True,
            'repair_urgency': 'within_month'
        }
    }

    if code_upper in code_overrides:
        metadata.update(code_overrides[code_upper])
        confidence = 95

    return confidence, metadata

def main():
    print("=" * 80)
    print("POPULATE ENHANCED SEVERITY METADATA")
    print("=" * 80)
    print()

    # Fetch all codes
    print("Fetching all codes from database...")
    result = supabase.table('obd_codes').select('*').execute()
    codes = result.data
    print(f"Found {len(codes)} codes\n")

    # Analyze and categorize
    high_confidence = []  # >= 90%
    medium_confidence = []  # 60-89%
    low_confidence = []  # < 60%

    print("Analyzing codes...")
    for code_data in codes:
        confidence, metadata = analyze_code(
            code_data['code'],
            code_data['description'],
            code_data.get('severity', 'Low'),
            code_data.get('system', '')
        )

        item = {
            'code': code_data['code'],
            'description': code_data['description'],
            'current_severity': code_data.get('severity', 'Low'),
            'metadata': metadata,
            'confidence': confidence
        }

        if confidence >= 90:
            high_confidence.append(item)
        elif confidence >= 60:
            medium_confidence.append(item)
        else:
            low_confidence.append(item)

    print()
    print("=" * 80)
    print("ANALYSIS COMPLETE")
    print("=" * 80)
    print(f"High confidence (>=90%): {len(high_confidence)} codes -> AUTO-APPLY")
    print(f"Medium confidence (60-89%): {len(medium_confidence)} codes -> REVIEW QUEUE")
    print(f"Low confidence (<60%): {len(low_confidence)} codes -> LEAVE DEFAULT")
    print()

    # Show sample high confidence
    print("Sample HIGH confidence metadata (first 5):")
    for item in high_confidence[:5]:
        print(f"\n  {item['code']} - {item['description'][:60]}...")
        print(f"    Confidence: {item['confidence']}%")
        print(f"    Stop driving: {item['metadata']['stop_driving']}")
        print(f"    Repair urgency: {item['metadata']['repair_urgency']}")

    # Ask for confirmation
    print()
    response = input(f"Apply {len(high_confidence)} high-confidence metadata updates? [y/N]: ")

    if response.lower() != 'y':
        print("Aborted.")
        return

    # Apply high confidence updates
    print("\nApplying high confidence metadata...")
    applied = 0
    errors = []

    for i, item in enumerate(high_confidence):
        try:
            supabase.table('obd_codes').update({
                'severity_metadata': item['metadata']
            }).eq('code', item['code']).execute()

            applied += 1
            if (i + 1) % 50 == 0:
                print(f"  Applied {i + 1}/{len(high_confidence)}...")

        except Exception as e:
            errors.append(f"{item['code']}: {str(e)}")

    print()
    print("=" * 80)
    print("COMPLETE")
    print("=" * 80)
    print(f"Applied: {applied}/{len(high_confidence)}")
    print(f"Errors: {len(errors)}")

    if errors:
        print("\nErrors:")
        for error in errors[:10]:
            print(f"  {error}")

    # Generate review queue for medium confidence
    if medium_confidence:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        review_file = f'metadata_review_queue_{timestamp}.md'

        with open(review_file, 'w', encoding='utf-8') as f:
            f.write(f"# Enhanced Metadata Review Queue\n\n")
            f.write(f"**Total Codes Needing Review:** {len(medium_confidence)}\n\n")
            f.write("---\n\n")

            for item in medium_confidence:
                f.write(f"## {item['code']} - {item['description'][:80]}...\n\n")
                f.write(f"**Current Severity:** {item['current_severity']}\n")
                f.write(f"**Confidence:** {item['confidence']}%\n\n")
                f.write("**Proposed Metadata:**\n")
                f.write(f"```json\n{json.dumps(item['metadata'], indent=2)}\n```\n\n")
                f.write("**Review Decision:**\n")
                f.write("- [ ] APPROVE\n")
                f.write("- [ ] REJECT\n")
                f.write("- [ ] MODIFY (edit JSON above)\n\n")
                f.write("**Notes:**\n\n\n")
                f.write("---\n\n")

        print(f"\nReview queue generated: {review_file}")

    print()
    print("Next steps:")
    print("1. Review medium confidence codes")
    print("2. Run migration 005_add_severity_metadata.sql")
    print("3. Update WhatsApp bot to use enhanced metadata")
    print()

if __name__ == '__main__':
    main()
