# OBD-II Codes Reference

This document provides a quick reference for the comprehensive OBD-II diagnostic trouble codes included in the Vehicle Diagnosis Assistant.

## Dataset Overview

**Total Codes: 190+**

The system includes codes across all major systems:
- **Powertrain (P-codes)**: ~150 codes
- **Chassis (C-codes)**: ~10 codes  
- **Body (B-codes)**: ~12 codes
- **Network (U-codes)**: ~10 codes

## Code Categories

### Powertrain System (P-codes)

#### Air/Fuel Metering (P0100-P0199)
- **P0100-P0113**: Mass Air Flow (MAF) and Intake Air Temperature (IAT) sensors
- **P0106-P0108**: Manifold Absolute Pressure (MAP) sensor issues
- **P0170-P0175**: Fuel trim and air/fuel mixture problems

#### Oxygen Sensors (P0130-P0167)
- **P0130-P0141**: Bank 1 oxygen sensors (upstream and downstream)
- Includes heater circuit malfunctions

#### Fuel & Air Metering Issues
- **P0171**: System Too Lean (Bank 1) - Very common
- **P0172**: System Too Rich (Bank 1) - Very common
- **P0174/P0175**: Bank 2 lean/rich conditions

#### Ignition System (P0300-P0369)
- **P0300**: Random/Multiple Cylinder Misfire
- **P0301-P0308**: Individual cylinder misfires (1-8)
- **P0351-P0354**: Ignition coil circuit malfunctions

#### Camshaft/Crankshaft Position
- **P0335**: Crankshaft Position Sensor
- **P0340-P0341**: Camshaft Position Sensor
- **P0010-P0021**: Variable Valve Timing (VVT) issues

#### Catalyst System
- **P0420**: Catalyst Efficiency Below Threshold (Bank 1) - Very common
- **P0430**: Catalyst Efficiency Below Threshold (Bank 2)

#### EVAP System (P0440-P0459)
- **P0440**: EVAP System Malfunction
- **P0442**: Small EVAP leak - Very common (often loose gas cap)
- **P0455**: Large EVAP leak
- **P0456**: Very small EVAP leak

#### Fuel Injection (P0200-P0208)
- **P0200**: Injector Circuit Malfunction
- **P0201-P0208**: Individual cylinder injector issues

#### Transmission (P0700-P0799)
- **P0700**: Transmission Control System Malfunction
- **P0705**: Transmission Range Sensor
- **P0730**: Incorrect Gear Ratio
- **P0740**: Torque Converter Clutch
- **P0750-P0765**: Shift Solenoid Malfunctions

#### Engine Temperature & Oil
- **P0217**: Engine Coolant Over Temperature
- **P0218**: Transmission Fluid Over Temperature
- **P0520**: Engine Oil Pressure Sensor

#### EGR System (P0400-P0409)
- **P0401**: EGR Flow Insufficient
- **P0402**: EGR Flow Excessive
- **P0404**: EGR Range/Performance

#### Idle Control (P0505-P0509)
- **P0505**: Idle Control System Malfunction
- **P0506**: Idle RPM Lower Than Expected
- **P0507**: Idle RPM Higher Than Expected

#### Electrical System
- **P0562**: System Voltage Low
- **P0563**: System Voltage High
- **P0600-P0606**: ECM/PCM internal errors

### Chassis System (C-codes)

#### ABS & Wheel Speed Sensors
- **C0035**: Left Front Wheel Speed Sensor
- **C0040**: Right Front Wheel Speed Sensor
- **C0045**: Left Rear Wheel Speed Sensor
- **C0050**: Right Rear Wheel Speed Sensor

#### ABS System
- **C0060**: ABS Motor Circuit
- **C0070**: ABS Control Module
- **C0121**: ABS Valve Circuit
- **C0265**: Electronic Brake Control Module

### Body System (B-codes)

#### Airbag System
- **B0001**: Driver Airbag Circuit
- **B0002**: Passenger Airbag Circuit
- **B0010**: Side Airbag (Driver)
- **B0015**: Side Airbag (Passenger)
- **B0020**: Curtain Airbag
- **B0032**: Airbag Control Module

#### Electrical System
- **B0050**: Battery Voltage Low
- **B0100**: Battery Voltage High
- **B1317**: Battery Voltage Out of Range
- **B1342**: ECU Defective

#### Body Control
- **B1000**: Door Ajar Switch

### Network System (U-codes)

#### Communication Bus Issues
- **U0001**: High Speed CAN Communication Bus
- **U0073**: Control Module Communication Bus Off

#### Module Communication
- **U0100**: Lost Communication with ECM/PCM
- **U0101**: Lost Communication with TCM
- **U0121**: Lost Communication with ABS Module
- **U0122**: Lost Communication with VDC Module
- **U0126**: Lost Communication with Steering Angle Sensor
- **U0140**: Lost Communication with BCM
- **U0155**: Lost Communication with Instrument Cluster
- **U0164**: Lost Communication with HVAC Module

## Severity Levels

### High Severity
- **Immediate attention required**
- May cause engine damage if driven
- Safety-critical systems affected
- Examples: Misfires (P0300-P0308), Overheating (P0217), Airbag issues (B0001-B0032)

### Medium Severity
- Should be addressed soon
- May affect performance or emissions
- Could lead to more serious issues
- Examples: O2 sensors, MAF sensor, Catalyst efficiency (P0420)

### Low Severity
- Can be addressed at next service
- Minimal performance impact
- Often emissions-related
- Examples: Small EVAP leaks (P0442, P0456), IAT sensor

## Common Code Patterns

### Most Frequent Codes
1. **P0420/P0430** - Catalyst efficiency (very common on high-mileage vehicles)
2. **P0442** - Small EVAP leak (often just loose gas cap)
3. **P0171/P0172** - Fuel trim issues (lean/rich conditions)
4. **P0300-P0308** - Misfire codes (spark plugs, coils, injectors)
5. **P0420** - Catalytic converter efficiency

### Quick Fixes
- **P0442, P0455, P0456**: Check gas cap first!
- **P0171**: Look for vacuum leaks
- **P0300-P0308**: Start with spark plugs
- **P0420**: Check O2 sensors before replacing expensive cat
- **P0506/P0507**: Clean throttle body

## Testing With Real Users

This comprehensive dataset provides:
- ✅ All common codes users will encounter
- ✅ Detailed symptoms for each code
- ✅ Multiple possible causes
- ✅ Generic fix recommendations
- ✅ Severity levels for prioritization
- ✅ Coverage across all vehicle systems

## Importing the Dataset

To import all codes into your Supabase database:

```bash
python scripts/import_obd_datasets.py
```

This will:
1. Load 190+ codes from the local comprehensive dataset
2. Optionally download additional codes from GitHub
3. Import all codes to Supabase with upsert (no duplicates)
4. Provide detailed progress and summary

## Code Format

Each code includes:
- **Code**: The DTC code (e.g., P0420)
- **Description**: What the code means
- **Common Causes**: Most likely reasons for this code
- **Symptoms**: What the user might experience
- **Generic Fixes**: Recommended troubleshooting steps
- **System**: Which system (Powertrain, Chassis, Body, Network)
- **Severity**: Low, Medium, or High

## Future Enhancements

Consider adding:
- Manufacturer-specific codes (P1000+, C1000+, etc.)
- Vehicle-specific known issues
- Cost estimates for common repairs
- Related codes that often appear together
- Diagnostic flowcharts
