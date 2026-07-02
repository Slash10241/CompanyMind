"""
Generate realistic synthetic industrial documents for Sunrise Refinery.
Uses Claude to produce authentic-sounding work orders, inspection reports,
safety procedures, equipment data sheets, incident reports, and operating procedures.
Saves as both .txt and PDF (via reportlab).
"""
import os
import sys
import json
import time
from pathlib import Path
from dotenv import load_dotenv

# Allow running from project root
sys.path.insert(0, str(Path(__file__).parent.parent))

# Load .env from project root
load_dotenv(Path(__file__).parent.parent / ".env")

import google.generativeai as genai
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors

OUTPUT_DIR = Path("backend/data/synthetic")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

genai.configure(api_key=os.environ["GEMINI_API_KEY"])
_gen_model = genai.GenerativeModel("gemini-2.5-flash")

DOCUMENTS = [
    # Work Orders
    {
        "filename": "WO_2024_0312_P101_BearingReplacement",
        "doc_type": "Work Order",
        "prompt": """Generate a realistic industrial maintenance work order for Sunrise Refinery with the following details:
- Work Order #: WO-2024-0312
- Equipment: Crude Feed Pump P-101 (Centrifugal, 185 kW, rated 450 m³/h at 12 bar)
- Failure: Bearing failure indicated by high vibration (8.5 mm/s RMS at drive end) and elevated bearing temperature (92°C)
- Technician: Rajesh Kumar (Mechanical Technician, Badge MT-047)
- Supervisor: Priya Sharma (Maintenance Supervisor)
- Date: 15-March-2024
- Duration: 8 hours (planned), 11 hours (actual)
- Parts used: SKF 6315-2RS1 bearing (2 units), bearing housing seal kit
- Root cause identified: Lubrication failure — grease nipple blocked, causing dry running
- Corrective action: Replace bearings, clean grease lines, install automatic lubrication system
- Next inspection due: 15-June-2024
Include: permit to work number, isolation procedure reference (SOP-ISOL-001), safety checks completed, post-work vibration reading (2.1 mm/s). Format as a formal maintenance work order document."""
    },
    {
        "filename": "WO_2024_0445_P102_SealLeak",
        "doc_type": "Work Order",
        "prompt": """Generate a realistic industrial maintenance work order for Sunrise Refinery:
- Work Order #: WO-2024-0445
- Equipment: Crude Feed Pump P-102 (standby to P-101, same specification)
- Failure: Mechanical seal leak — visible crude oil leakage from seal area, ~2 litres/hour
- Technician: Amit Verma (Mechanical Technician, Badge MT-023)
- Supervisor: Priya Sharma
- Date: 28-April-2024
- Duration: 6 hours
- Parts: John Crane Type 8B1 mechanical seal assembly
- Root cause: Seal face wear due to dry running during previous startup after maintenance
- Corrective action: Replace seal, flush seal flush plan, update startup procedure
- OISD-118 clause 5.3.2 reference for rotating equipment maintenance
- Next PM due: 28-October-2024
Format as a formal maintenance work order."""
    },
    {
        "filename": "WO_2024_0521_HE201_TubeCleaning",
        "doc_type": "Work Order",
        "prompt": """Generate a realistic maintenance work order for Sunrise Refinery:
- Work Order #: WO-2024-0521
- Equipment: Crude Preheat Heat Exchanger HE-201 (Shell & Tube, TEMA type BEM, surface area 420 m², duty 8.5 MW)
- Activity: Planned tube-side cleaning (hydroblasting) — fouling causing 15% reduction in heat transfer efficiency
- Technicians: Mohammed Iqbal (MT-031), Suresh Nair (MT-019)
- Supervisor: Vikram Tiwari (Maintenance Engineer)
- Date: 10-May-2024 to 12-May-2024
- Shell side: crude oil 180°C, 8 bar. Tube side: atmospheric residue 260°C.
- Cleaning method: Hydroblasting at 700 bar with rotary lance
- Tubes inspected: 312 tubes, 8 found with 40%+ wall loss by UT (plugged per TEMA standard)
- Efficiency restored to 97% post-cleaning
- Next cleaning: November 2024 (6-month cycle)
- Regulatory reference: OISD-STD-137 for heat exchanger inspection
Format as formal work order with safety permits and isolation certificate reference."""
    },
    {
        "filename": "WO_2024_0688_C401_ValveOverhaul",
        "doc_type": "Work Order",
        "prompt": """Generate a realistic maintenance work order for Sunrise Refinery:
- Work Order #: WO-2024-0688
- Equipment: Recycle Gas Compressor C-401 (Reciprocating, 2-stage, 750 kW, API 618 compliant)
- Activity: Planned major overhaul — inlet/discharge valve replacement (scheduled every 8000 running hours)
- Running hours at overhaul: 8,247 hours (indicator: 8000 hr PM)
- Technicians: Ravi Pillai (MT-055), Deepak Joshi (MT-038), OEM specialist from Dresser-Rand
- Supervisor: Anil Bose (Senior Mechanical Engineer)
- Dates: 20-June-2024 to 22-June-2024
- Valves replaced: 8 suction valves, 8 discharge valves (Dresser-Rand OEM parts)
- Also replaced: piston rings, rider bands, packing rings
- Gas: hydrogen-rich recycle gas, MOC considerations for H2 service
- Post-overhaul performance test: capacity 4,200 Nm³/h at 35 bar discharge, within 2% of design
- Reference: OISD-STD-113 for compressor maintenance
Format as a comprehensive maintenance work order."""
    },
    {
        "filename": "WO_2024_0789_V301_LevelTransmitter",
        "doc_type": "Work Order",
        "prompt": """Generate a maintenance work order for Sunrise Refinery:
- Work Order #: WO-2024-0789
- Equipment: Crude Storage Vessel V-301 (floating roof tank, 50,000 kL capacity, API 650)
- Activity: Level transmitter LT-301A replacement — instrument giving erratic readings
- Failure: LT-301A (Rosemount 3300 guided wave radar) — signal failure due to antenna coating by paraffin
- Technician: Kavitha Menon (Instrument Technician, Badge IT-012)
- Supervisor: Deepak Sharma (Instrument Engineer)
- Date: 5-July-2024
- Duration: 4 hours
- Part: Rosemount 3300 GWR antenna replacement
- Calibration: 0-18m range, 4-20mA output verified against manual tape measurement
- Loop test completed, DCS display verified
- HAZOP deviation reference: deviation report DR-2024-089
Format as instrument work order."""
    },
    {
        "filename": "WO_2024_0834_P101_PreventiveMaintenance",
        "doc_type": "Work Order",
        "prompt": """Generate a preventive maintenance work order for Sunrise Refinery:
- Work Order #: WO-2024-0834
- Equipment: Crude Feed Pump P-101 (post-bearing replacement from WO-2024-0312)
- Activity: 3-month scheduled PM check
- Technician: Rajesh Kumar (MT-047)
- Date: 18-June-2024
- PM activities: Vibration measurement (1.8 mm/s — within acceptable limits < 4.5 mm/s per ISO 10816-3), bearing temperature check (58°C — normal), alignment check (0.05mm angular, 0.03mm parallel — within tolerance), lubrication auto-system verified functional, coupling inspect, shaft seal condition check
- All parameters within acceptable range
- Next PM: 18-September-2024
- Trend: vibration improving since bearing replacement, no anomalies detected
Format as a concise preventive maintenance record."""
    },
    {
        "filename": "WO_2024_0901_HE201_InspectionFollowup",
        "doc_type": "Work Order",
        "prompt": """Generate a follow-up inspection work order for Sunrise Refinery:
- Work Order #: WO-2024-0901
- Equipment: Heat Exchanger HE-201 — follow-up external visual inspection post-cleaning
- Inspector: Sanjay Malhotra (NDT Level II Inspector, ASNT certified, Badge NDT-007)
- Date: 14-May-2024
- Activity: External visual inspection, shell-side nozzle ultrasonic thickness measurement
- Findings: Shell thickness 14.2mm (nominal 16mm, minimum 12mm per API 510 — acceptable), one nozzle weld showing surface indication — liquid penetrant test confirmed as surface crack 25mm length
- Action: Weld repair performed by qualified welder (WPS-CR-007), post-weld PT re-inspection clear
- Statutory compliance: Inspection per OISD-STD-137, record filed with Chief Inspector of Factories
Format as an inspection follow-up work order."""
    },
    {
        "filename": "WO_2024_1023_C401_UnplannedShutdown",
        "doc_type": "Work Order",
        "prompt": """Generate an unplanned maintenance work order for Sunrise Refinery:
- Work Order #: WO-2024-1023
- Equipment: Recycle Gas Compressor C-401 — unplanned shutdown
- Fault: High vibration trip (>12 mm/s RMS) on 2nd stage crankshaft
- Date: 15-September-2024, 03:47 hours
- On-call technician: Ravi Pillai (MT-055)
- Root cause investigation: loose connecting rod bolts — torque found at 180 Nm vs. specified 250 Nm (Dresser-Rand service manual, Chapter 4)
- Cause of under-torquing: post-overhaul bolt torque verification step missed (procedural gap identified)
- Corrective action: Re-torque all connecting rod bolts to specification, run-up test, vibration 3.2 mm/s — acceptable
- Total downtime: 6 hours 20 minutes
- Economic impact: 6,200 Nm³/h production loss (recycle gas supply)
- CAPA: Update WO-2024-0688 overhaul procedure to include mandatory torque verification checklist
Format as an emergency maintenance work order with RCA summary."""
    },

    # Inspection Reports
    {
        "filename": "INSP_2024_Q1_P101_P102_RotatingEquipment",
        "doc_type": "Inspection Report",
        "prompt": """Generate a quarterly rotating equipment inspection report for Sunrise Refinery:
- Report #: INSP-2024-Q1-RE-001
- Equipment scope: P-101, P-102, C-401 (crude feed pumps and recycle compressor)
- Inspector: Sanjay Malhotra (NDT Level II), supervised by Anil Bose (Senior Mech. Eng.)
- Period: January–March 2024
- P-101: Bearing vibration 6.8 mm/s (elevated, threshold 4.5 mm/s) — ALERT status. Bearing replacement recommended within 30 days.
- P-102: Vibration 2.1 mm/s (normal), seal condition satisfactory, no leaks
- C-401: Running hours 7,450 at end of Q1, approaching 8,000-hour PM trigger. Schedule overhaul for June 2024.
- Overall assessment: P-101 requires urgent attention; others at scheduled intervals
- OISD-118 compliance status: P-101 — non-compliant pending repair; others compliant
- Next inspection: April 2024 (P-101 post-repair), July 2024 (quarterly)
Format as a formal quarterly inspection report with a summary table."""
    },
    {
        "filename": "INSP_2024_HE201_ThermalEfficiency",
        "doc_type": "Inspection Report",
        "prompt": """Generate a heat exchanger performance inspection report for Sunrise Refinery:
- Report #: INSP-2024-HE-001
- Equipment: HE-201 Crude Preheat Heat Exchanger
- Inspector: Vikram Tiwari (Mechanical/Process Engineer)
- Date: 2-May-2024
- Method: Process performance monitoring (inlet/outlet temperatures and flow rates)
- Shell side (crude): Inlet 95°C, outlet 163°C (design outlet 175°C — 12°C shortfall)
- Tube side (residue): Inlet 290°C, outlet 215°C
- Heat transfer efficiency: 82.3% of design (threshold for cleaning action: 85%)
- Fouling resistance measured: 0.00028 m²K/W (design fouling factor 0.00015 — significantly exceeded)
- Recommendation: Immediate tube-side cleaning required
- OISD-STD-137 reference: Section 4.2 — fouling monitoring requirements
- Energy impact: Fouling causing 4.2 MW additional furnace duty, fuel equivalent ~85,000 SCM/month natural gas
Format as a formal performance inspection report."""
    },
    {
        "filename": "INSP_2024_V301_AnnualTankInspection",
        "doc_type": "Inspection Report",
        "prompt": """Generate an annual above-ground storage tank inspection report for Sunrise Refinery:
- Report #: INSP-2024-TANK-001
- Tank: V-301 (Crude Oil Floating Roof Tank, 50,000 kL, API 650, built 2014)
- Inspector: Sanjay Malhotra (API 653 certified inspector, License #IND-0445)
- Date: January 2024 (10-year out-of-service inspection)
- Findings:
  - Bottom plate: 14 areas of internal corrosion, deepest 3.2mm (original 8mm, minimum 6mm acceptable per API 653 — 5 plates require replacement)
  - Shell plates: Ultrasonic thickness survey — all within minimum allowable shell thickness
  - Floating roof seals: Primary seal worn, secondary seal in good condition
  - Roof drain: Operational, no blockage
  - Appurtenances: All vents, gauges, drain valves functional
- Required actions: Replace 5 bottom plates, replace primary floating roof seal
- Fitness for service: Conditional — must complete repairs before returning to service
- Regulatory: Inspection per OISD-STD-129 (storage tank), API 653 standard
- Next inspection: 5 years (2029) if repairs completed satisfactorily
Format as a detailed API 653 tank inspection report."""
    },
    {
        "filename": "INSP_2024_Q2_ComplianceAudit",
        "doc_type": "Inspection Report",
        "prompt": """Generate a statutory compliance audit inspection report for Sunrise Refinery:
- Report #: INSP-2024-COMPLIANCE-Q2
- Scope: Factories Act compliance, OISD adherence, PESO license status
- Conducted by: Internal Safety & Compliance team + External auditor from Bureau of Industrial Safety
- Date: June 2024
- Findings:
  1. Pressure vessel inspection certificates: 12 vessels — all current. Next due: V-302 (October 2024).
  2. Fire & explosion protection: 3 detector heads in CDU area past calibration due date (6 months overdue) — NON-COMPLIANT
  3. Work permit system: 98% compliance on PTW documentation review — minor gaps in post-job close-out signatures
  4. PESO license: Current, valid until March 2026
  5. Factory Act registers: Form 7 (accident register), Form 24 (health register) — up to date
  6. Emergency response drill: Last conducted February 2024 — due again August 2024
  7. P-101 bearing failure (WO-2024-0312): Not reported to factory inspector within 24 hours as required — VIOLATION
- Critical actions: Calibrate fire detectors within 30 days, submit late accident report to Chief Inspector
- Overall compliance score: 84% (threshold 90% for green status)
Format as a formal compliance audit report."""
    },
    {
        "filename": "INSP_2024_NDT_Pipeline_Survey",
        "doc_type": "Inspection Report",
        "prompt": """Generate an NDT pipeline inspection report for Sunrise Refinery:
- Report #: INSP-2024-NDT-PIPE-001
- Scope: Crude oil transfer lines from tank farm to CDU, total 2.3 km, 8-inch CS pipe (API 5L Gr. B)
- Inspector: Kavitha NDT team (Sanjay Malhotra lead, Badge NDT-007)
- Method: Guided Wave UT (GWT) screening, followed by conventional UT at anomaly locations
- Date: March 2024
- Findings: 14 anomaly locations identified by GWT. UT follow-up:
  - 3 locations: active corrosion, wall loss >30% — immediate repair recommended
  - 7 locations: wall loss 15-30% — monitor quarterly
  - 4 locations: surface indication only — no action
- Worst case: Location PL-07 (adjacent to road crossing) — 42% wall loss, pipe original 8.18mm, current 4.7mm
- Repair method recommended: Full encirclement repair sleeve or pipe replacement section
- OISD-STD-141 reference (cross-country pipeline) — applicable sections
- Cathodic protection system: Last survey 2022, re-survey due 2024 — overdue by 3 months
Format as a formal NDT inspection survey report."""
    },

    # Safety Procedures
    {
        "filename": "SOP_SAFE_001_HotWorkPermit",
        "doc_type": "Safety Procedure",
        "prompt": """Generate a comprehensive Hot Work Permit procedure for Sunrise Refinery:
- Document #: SOP-SAFE-001 Rev. 4
- Title: Hot Work Permit Procedure
- Regulatory basis: OISD-STD-105 (Work Permit System), Factory Act 1948 Section 36
- Scope: All cutting, welding, grinding, and open-flame activities in process areas
- Risk: Fire and explosion from flammable vapours (crude oil flash point 32°C)
- Procedure sections:
  1. Applicability and exemptions
  2. Gas testing requirements (LEL < 10% before work, continuous monitoring if LEL > 0%)
  3. Isolation requirements — reference SOP-ISOL-001
  4. Fire watch duties and equipment (dry chemical extinguisher minimum 9 kg, fire hose connected)
  5. Permit validity: Maximum 8 hours, must be renewed for next shift
  6. Approval matrix: Area operator → Shift supervisor → Safety officer → Area engineer
  7. Atmospheric conditions: Work suspended if wind speed > 45 km/h
  8. PPE requirements: Face shield, leather gloves, fire-retardant coveralls (EN ISO 11612), safety boots
  9. Post-job requirements: Area inspection, gas test, permit close-out
  10. Emergency procedure: Evacuation signal, muster point locations
- Include OISD-118 clause references throughout
Format as a formal controlled procedure document."""
    },
    {
        "filename": "SOP_SAFE_002_ConfinedSpaceEntry",
        "doc_type": "Safety Procedure",
        "prompt": """Generate a confined space entry procedure for Sunrise Refinery:
- Document #: SOP-SAFE-002 Rev. 3
- Title: Confined Space Entry Procedure
- Regulatory basis: OISD-STD-105, OISD-GDN-192, Factory Act Section 36
- Applies to: Vessels (V-series), heat exchanger shells, storage tanks, drains, pits
- Hazards: Oxygen deficiency, toxic atmosphere (H2S, hydrocarbons), engulfment
- Procedure:
  1. Definition of confined space at Sunrise Refinery
  2. Pre-entry atmospheric testing: O2 19.5-23.5%, LEL < 10%, H2S < 1 ppm (TLV-TWA 1 ppm per ACGIH)
  3. Isolation requirements: Positive isolation (spectacle blind or spool removal — no valve isolation alone)
  4. Standby/attendant duties: Must remain at entry point, may not enter
  5. Retrieval system: Tripod and harness required for vertical entry > 1.5m
  6. Communication: Radio contact every 10 minutes
  7. Rescue procedure: Rescue team briefed and on standby
  8. Permit approval: Area supervisor + Safety officer + Area engineer mandatory
  9. PPE: SCBA for initial entry if atmosphere unverified, safety harness, intrinsically safe torch
  10. Special requirements for H2S environments (sour service equipment, buddy system mandatory)
- PESO reference for H2S monitoring equipment certification
Format as a detailed safety procedure."""
    },
    {
        "filename": "SOP_OPS_001_CrudeUnitStartup",
        "doc_type": "Safety Procedure",
        "prompt": """Generate a crude distillation unit (CDU) startup procedure for Sunrise Refinery:
- Document #: SOP-OPS-001 Rev. 6
- Title: CDU Cold Startup Procedure
- Equipment involved: P-101, P-102, HE-201, Atmospheric Distillation Column T-101, Furnace F-101
- Startup conditions: Unit in cold condition following planned shutdown
- Key steps:
  1. Pre-startup safety checks (30 items checklist)
  2. P-101/P-102 pump priming and startup (reference P-101 operating manual, Section 3.2)
  3. HE-201 preparation — ensure tube/shell vents open, drain valves closed
  4. Furnace F-101 purge procedure (minimum 5 air changes before ignition)
  5. Column T-101 pressure build-up procedure (nitrogen blanket 0.5 barg minimum before crude introduction)
  6. Crude introduction: Start at 20% of design rate (90 m³/h), stabilise before rate increase
  7. Temperature ramp-up: Max 25°C/hour to avoid thermal shock
  8. Product routing: Initial products to slop until on-specification
  9. Alarm setpoints: T-101 overhead pressure 1.8 barg (HH alarm 2.0 barg, trip 2.2 barg)
  10. Emergency shutdown: Automatic on P-101/P-102 both loss of flow
- References: OISD-GDN-105, specific equipment manuals
- Estimated startup time: 12-16 hours from cold condition
Format as a detailed operating procedure with clear step numbering."""
    },
    {
        "filename": "SOP_SAFE_003_H2S_Emergency",
        "doc_type": "Safety Procedure",
        "prompt": """Generate an H2S emergency response procedure for Sunrise Refinery:
- Document #: SOP-SAFE-003 Rev. 5
- Title: H2S Emergency Response Procedure
- Basis: OISD-GDN-192, OSHA 29 CFR 1910.1000, Factory Act
- Background: Sunrise Refinery processes sour crude with H2S content up to 5000 ppm in crude oil
- H2S concentration action levels:
  1. < 1 ppm: Normal conditions — personnel may work without SCBA
  2. 1-10 ppm: Alert — investigate source, standby SCBA
  3. 10-50 ppm: Evacuation of non-essential personnel, SCBA mandatory for all in area
  4. > 50 ppm: Emergency — evacuate immediately, activate muster alarm, emergency response team
  5. > 300 ppm (immediately dangerous to life/health — IDLH): Full emergency response, no entry without SCBA
- Emergency response steps:
  1. Activate H2S alarm (three blasts on plant siren)
  2. Wind direction check — muster upwind at designated points (A, B, C identified on plant map)
  3. Emergency shutdown of affected section (follow ESD procedure ESD-001)
  4. Casualty first aid: Remove victim from area with SCBA, commence CPR if not breathing
  5. Notify: Shift Supervisor → Safety Officer → Plant Manager → Emergency services
  6. Regulatory notification: PESO and Factory Inspector within 1 hour of major release
- Detector locations: HD-101 (pump house), HD-201 (HE-201 area), HD-301 (tank farm) [all Crowcon Gasman units]
Format as an emergency response procedure."""
    },

    # Equipment Data Sheets
    {
        "filename": "EDS_P101_CrudeFeedPump",
        "doc_type": "Equipment Data Sheet",
        "prompt": """Generate a detailed equipment data sheet for Sunrise Refinery:
- Equipment: Crude Feed Pump P-101
- OEM: Flowserve Corporation (Model: DVMX 150-400)
- Type: Horizontal, between-bearings, double-suction centrifugal pump
- Service: Crude oil transfer from tank farm V-301 to CDU
- Design data:
  - Flow: 450 m³/h design, max 540 m³/h
  - Head: 120 m (design), 145 m (shutoff head)
  - Speed: 1480 rpm (50 Hz, 4-pole motor)
  - Motor: 185 kW, 11 kV, Siemens 1LE0 frame, IP55, ATEX Zone 1 rated
  - Fluid: Crude oil, SG 0.855, viscosity 12 cSt at 50°C
  - Temperature: Operating 50°C, maximum allowable 120°C
  - Suction pressure: 1.2 barg, discharge 13.5 barg
  - NPSHr: 4.2 m at design flow
  - Efficiency: 82% at design point
- Materials: Casing: CS A216 WCB; Impeller: 12% Cr SS; Shaft: 17-4 PH SS; Seal: John Crane Type 8B1 cartridge mechanical seal
- Bearings: Drive end SKF 6315-2RS1, non-drive end SKF 6311-2RS1
- Lubrication: Grease-packed bearings with automatic lubrication (Lincoln Quicklub system, 120cc/point/week)
- Vibration limit: ISO 10816-3 Zone B (2.3-4.5 mm/s RMS) alert, Zone C (>4.5 mm/s) action
- Preventive maintenance: Quarterly vibration measurement, annual bearing replacement
- Spare parts criticality: Bearing set (critical, maintain 2 sets), seal kit (critical, maintain 1 set)
Format as a formal equipment data sheet."""
    },
    {
        "filename": "EDS_HE201_CrudePreheatExchanger",
        "doc_type": "Equipment Data Sheet",
        "prompt": """Generate an equipment data sheet for a heat exchanger at Sunrise Refinery:
- Equipment: HE-201 Crude Preheat Heat Exchanger
- Manufacturer: Alfa Laval (custom shell & tube, built 2015)
- Type: Shell & Tube, 2-pass tube-side, TEMA type BEM, ASME Section VIII Div. 1
- Service: Crude oil preheating using atmospheric residue
- Shell side (crude oil): Inlet 95°C / Outlet 175°C, Flow 450 m³/h, Pressure 13 bar design, 12 bar operating
- Tube side (atmospheric residue): Inlet 290°C / Outlet 215°C, Flow 95 m³/h, Pressure 4 bar design
- Design duty: 9.2 MW
- Heat transfer area: 420 m² (312 tubes, 6m length, 25mm OD, 2mm wall, triangular pitch 32mm)
- Materials: Shell: CS A516 Gr. 70; Tubes: SS 316L (due to sour crude service); Tube sheets: CS + SS 316L overlay; Baffles: CS
- Design temperature: Shell 200°C, Tube 350°C
- Test pressure: Shell 18.5 bar, Tube 6.5 bar (hydro test)
- Fouling factors: Shell 0.00015 m²K/W, Tube 0.00015 m²K/W (design basis)
- Inspection period: 6-monthly tube cleaning, annual shell inspection (OISD-STD-137)
- MAWP: Shell 12 bar at 200°C, Tube 4 bar at 320°C
Format as a formal equipment data sheet with all process design data."""
    },
    {
        "filename": "EDS_C401_RecycleGasCompressor",
        "doc_type": "Equipment Data Sheet",
        "prompt": """Generate an equipment data sheet for a compressor at Sunrise Refinery:
- Equipment: Recycle Gas Compressor C-401
- OEM: Dresser-Rand (Model: VECTRA HHE 2-throw)
- Type: Reciprocating, 2-stage, double-acting, API 618 3rd edition
- Service: Hydrogen-rich recycle gas, hydrotreater recycle loop
- Gas composition: 72% H2, 18% CH4, 6% C2H6, 4% other hydrocarbons
- Design data:
  - Capacity: 4,500 Nm³/h (design), 3,500 Nm³/h (minimum)
  - Suction: 1st stage 5 bar, 45°C; 2nd stage 16 bar, 50°C (after intercooler)
  - Discharge: 1st stage 17 bar; 2nd stage 36 bar
  - Shaft power: 750 kW
  - Speed: 428 rpm
  - Stroke: 250 mm
  - Motor: 800 kW, 11 kV, 3-phase, 50 Hz
- Materials: Cylinders: Ductile iron; Piston rods: 17-4 PH SS; Packing: PTFE/carbon composite (H2 service)
- Valves: Hoerbiger MOPPET plate valves, replacement interval 8,000 hours
- Piston rings: PTFE-filled graphite, replacement at 8,000 hours
- Vibration: API 618 limits — frame vibration < 1.0 mm/s, unbalanced force < 50% of guideline
- Critical interlocks: High discharge temperature trip (130°C), High vibration trip (12 mm/s), Low lube oil pressure trip
- PM schedule: 8,000 hour major overhaul, 4,000 hour minor (valves and packing inspection)
Format as a formal equipment data sheet."""
    },
    {
        "filename": "EDS_V301_CrudeStorageTank",
        "doc_type": "Equipment Data Sheet",
        "prompt": """Generate an equipment data sheet for a storage tank at Sunrise Refinery:
- Equipment: V-301 Crude Oil Storage Tank
- Builder: McDermott India (constructed 2014)
- Type: External Floating Roof Tank (EFRT), API 650 standard
- Service: Crude oil storage (sour, H2S content up to 5000 ppm)
- Capacity: 50,000 kL (nominal), 47,500 kL (working)
- Dimensions: Diameter 60m, Height 18m
- Design conditions: Atmospheric pressure, operating temperature ambient (max 55°C summer)
- Materials: Shell: CS IS 2062 Gr. E250, Shell thickness 8-14mm (variable by course); Bottom: CS IS 2062, 8mm; Roof: Pontoon type external floating roof, CS
- Floating Roof Seals: Primary (mechanical shoe seal), Secondary (rim-mounted fabric seal)
- Appurtenances: Level gauge (LT-301A/B redundant GWR), Temperature elements (3 locations), High-high level switch (LSH-301), Pressure/vacuum vent, Emergency drain
- Fire protection: Fixed foam system (3 foam chambers), rim seal fire detection, sprinkler on shell
- Cathodic protection: Impressed current system (2 transformer-rectifier units), survey every 2 years
- Regulatory: OISD-STD-129 (storage tank), PESO license required
- Inspection: API 653 every 10 years (out-of-service), annual external visual inspection
Format as a formal equipment data sheet."""
    },

    # Incident Reports
    {
        "filename": "INC_2024_003_P101_BearingFailure",
        "doc_type": "Incident Report",
        "prompt": """Generate a formal incident/near-miss report for Sunrise Refinery:
- Incident #: INC-2024-003
- Equipment: P-101 Crude Feed Pump
- Date/Time: 14-March-2024, 22:15 hours
- Category: Equipment failure (no injury, no release) — Near Miss to production disruption
- Description: P-101 high vibration alarm activated. Operator Suresh Nair responded. Vibration reading 8.5 mm/s (alarm 4.5, trip 10 mm/s). Unit switched to standby pump P-102. P-101 isolated for inspection. Found: Drive-end bearing in advanced wear stage — would have failed within estimated 4-8 hours if not caught.
- Immediate cause: Bearing failure due to lubrication starvation
- Root cause (5-Why analysis):
  1. Bearing failed → 2. Bearing ran dry → 3. Grease not reaching bearing → 4. Grease nipple blocked by hardened grease → 5. No periodic grease nipple flushing in PM procedure
- Contributing factors: PM procedure gap (no grease nipple check), operator rounds not catching early temperature rise (no trend monitoring)
- Corrective actions:
  1. Install automatic lubrication system (completed, WO-2024-0312)
  2. Update PM procedure to include grease nipple condition check
  3. Implement bearing temperature trending in DCS
  4. Operator training on early warning signs of bearing failure
- Regulatory notification: Not reportable (no injury, no release) — factory inspector informed for information
- Lessons learned: Preventable with proper lubrication PM — similar risk exists on P-102 (action taken proactively)
Format as a formal incident investigation report with 5-Why analysis."""
    },
    {
        "filename": "INC_2024_007_H2S_DetectorAlarm",
        "doc_type": "Incident Report",
        "prompt": """Generate an incident report for a gas detector alarm at Sunrise Refinery:
- Incident #: INC-2024-007
- Location: HE-201 area, CDU section
- Date/Time: 22-April-2024, 14:30 hours
- Category: Near-miss (potential H2S release) — No injury, no confirmed release
- H2S detector HD-201 alarmed at 8 ppm H2S (alarm level 1 ppm)
- Response: Area evacuated, SCBA donned by emergency response team, source investigation
- Investigation: Maintenance crew performing valve packing replacement on crude line isolation valve XV-201. Improper isolation — valve not fully depressurised before packing removal
- Technician involved: Contract maintenance worker (not Sunrise Refinery employee) — contractor company: Bharat Maintenance Services
- Root cause: Contractor worker bypassed lockout/tagout procedure; supervisor not present at critical step
- Contributing factors: Contractor safety induction not completed (signing-in record shows gap); permit did not specify packing removal as high-risk activity
- H2S reading at PPE removal: 0.5 ppm (within limits) — no injuries
- Corrective actions:
  1. All contractor workers must complete enhanced H2S safety induction (30 hours, includes practical)
  2. Packing replacement on hydrocarbon lines classified as high-risk requiring safety officer presence
  3. Contractor management procedure revised — supervisor must sign off at isolation verification stage
  4. PESO notification made (near-miss report per PESO guidelines)
Format as a formal incident investigation report."""
    },
    {
        "filename": "INC_2024_012_C401_Vibration_Unplanned",
        "doc_type": "Incident Report",
        "prompt": """Generate an incident investigation report for Sunrise Refinery:
- Incident #: INC-2024-012
- Equipment: C-401 Recycle Gas Compressor
- Date/Time: 15-September-2024, 03:47 hours
- Category: Equipment failure with production loss
- Description: C-401 tripped on high vibration (12.3 mm/s, trip setpoint 12 mm/s) at 03:47 hours. Night-shift operator Mohan Prasad attempted restart — second trip occurred. Maintenance called. Hydrotreater unit partially shutdown due to loss of recycle gas supply.
- Investigation: Connecting rod bolts found under-torqued (180 Nm vs. specification 250 Nm). This allowed micro-movement at rod-crankpin interface → fretting → vibration buildup.
- Root cause: Post-overhaul (WO-2024-0688) torque verification step absent from work order checklist. OEM specialist completed work but did not document final torque values.
- Production loss: 6 hours 20 minutes, 6,200 Nm³/h recycle gas → estimated throughput loss 800 MT hydrotreated diesel
- Financial impact: Estimated INR 32 lakhs revenue loss + INR 8 lakhs repair cost
- Regulatory: Reported to Chief Inspector of Factories within 24 hours (plant stoppage > 4 hours reportable per Factory Act)
- Corrective actions:
  1. All future C-401 overhaul procedures must include torque verification hold point with supervisor countersignature
  2. OEM specialists must be inducted on Sunrise Refinery documentation requirements
  3. Post-overhaul test-run protocol implemented: 2-hour monitored run-up before handover to operations
- Systemic action: Audit all recent overhaul work orders for documentation completeness
Format as a formal incident investigation report with financial impact."""
    },

    # Operating Procedures
    {
        "filename": "OPS_P101_P102_OperatingManual",
        "doc_type": "Operating Procedure",
        "prompt": """Generate an operating manual section for crude feed pumps at Sunrise Refinery:
- Document #: OPS-PUMP-001 Rev. 8
- Title: P-101 / P-102 Crude Feed Pump Operating Manual
- Equipment: Flowserve DVMX 150-400 centrifugal pumps
- Normal operating parameters:
  - Flow: 420-470 m³/h (DCS tag FI-101)
  - Discharge pressure: 12.5-13.5 barg (PI-101A)
  - Bearing temperature: < 70°C (TI-101A/B)
  - Vibration: < 4.5 mm/s RMS (VI-101)
  - Seal flush: 0.5 barg differential (PDI-101)
  - Motor current: 23-26 A (normal load)
- Startup procedure (7 steps): verify suction valve open, vent pump casing, start motor, crack open discharge valve, ramp to operating flow, check all parameters, log startup in DCS historian
- Normal shutdown (5 steps)
- Emergency shutdown: Automatic on loss of flow for 60 seconds (FSL-101 low flow switch). Manual ESD button at local panel.
- Switchover P-101 to P-102 (or vice versa) procedure: 8 steps — start standby, synchronise flow, stop duty
- Alarm response guide: 6 alarms with response instructions
- Common problems and troubleshooting: 8 scenarios (cavitation, seal leak, high vibration, motor overload, etc.)
- Reference: OISD-118 operating requirements, Flowserve DVMX maintenance manual
Format as a formal operator manual with clear numbered steps."""
    },
    {
        "filename": "OPS_HE201_FoulingMonitoring",
        "doc_type": "Operating Procedure",
        "prompt": """Generate an operating procedure for heat exchanger performance monitoring at Sunrise Refinery:
- Document #: OPS-HE-001 Rev. 3
- Title: HE-201 Performance Monitoring and Fouling Control Procedure
- Frequency: Monthly performance calculation, daily operator monitoring
- Operator daily checks:
  1. Record shell-side inlet/outlet temperatures (TI-201A, TI-201B) — target outlet 170-180°C
  2. Record tube-side inlet/outlet temperatures (TI-202A, TI-202B)
  3. Record shell-side pressure drop (PDI-201) — normal 0.8 bar, action if > 1.5 bar
  4. Record crude flow rate (FI-101)
- Monthly efficiency calculation: Process engineer calculates overall heat transfer coefficient (U-value) vs. clean baseline. Action if U < 85% of clean value.
- Fouling response matrix:
  - U = 85-100%: Normal, continue monitoring
  - U = 75-85%: Increase monitoring frequency, plan cleaning within 60 days
  - U < 75%: Initiate cleaning within 30 days (work order to Maintenance)
- Chemical treatment: Antifoulant injection at FI-101 injection point (Product: Nalco EC1022A, dose rate 5 ppm)
- Energy efficiency KPI: Monthly fuel savings calculation from HE-201 performance
- Reference: OISD-STD-137 Section 5 — heat exchanger operation
Format as a clear operating procedure."""
    },
    {
        "filename": "OPS_EMERGENCY_PlantShutdown",
        "doc_type": "Operating Procedure",
        "prompt": """Generate an emergency plant shutdown procedure for Sunrise Refinery:
- Document #: OPS-ESD-001 Rev. 9
- Title: Emergency Plant Shutdown Procedure (CDU Section)
- Triggers: Fire, explosion, major H2S release, loss of cooling water, loss of instrument air, operator discretion
- Emergency shutdown sequence (automated + manual):
  1. Activate plant ESD (PSHH or manual pushbutton in control room)
  2. P-101/P-102: Automatic trip on ESD signal (solenoid valve SV-101 closes)
  3. F-101 Furnace: Fuel gas trip, pilots remain lit (fail-safe)
  4. XV-series isolation valves: Auto-close on ESD signal
  5. Column T-101: Pressure relief valves PSV-101A/B auto-lift if required
  6. Flare system: All vapours routed to flare — verify flare pilot flame (FI-FLARE > 0)
  7. Operator actions: Control room operator confirms all trips, monitors pressure decay
  8. Field operator: Check all isolation valves physically, report to control room
  9. Head count: All personnel to muster stations within 5 minutes
  10. Emergency contact: Shift supervisor notifies plant manager, emergency services if required
- Restart after ESD: Requires written clearance from Plant Manager + Safety Officer
- Common ESD scenarios and specific responses: 5 scenarios
- Important: All ESD activations must be reported and investigated (INC report mandatory)
- Regulatory: OISD-GDN-105 — emergency shutdown requirements
Format as a detailed emergency procedure with numbered steps and responsible parties."""
    },
]


def text_to_pdf(text: str, output_path: Path, title: str):
    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=A4,
        rightMargin=2*cm,
        leftMargin=2*cm,
        topMargin=2*cm,
        bottomMargin=2*cm,
    )
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "DocTitle",
        parent=styles["Title"],
        fontSize=14,
        spaceAfter=12,
        textColor=colors.HexColor("#1a1a2e"),
    )
    body_style = ParagraphStyle(
        "Body",
        parent=styles["Normal"],
        fontSize=9,
        leading=14,
        spaceAfter=6,
    )
    story = [
        Paragraph(f"SUNRISE REFINERY — DOCUMENT MANAGEMENT SYSTEM", styles["Heading2"]),
        Spacer(1, 0.3*cm),
        Paragraph(title, title_style),
        Spacer(1, 0.5*cm),
    ]
    for line in text.split("\n"):
        line = line.strip()
        if not line:
            story.append(Spacer(1, 0.2*cm))
            continue
        if line.startswith("##") or line.isupper() and len(line) < 80:
            story.append(Paragraph(line.lstrip("#").strip(), styles["Heading3"]))
        else:
            # Escape XML special characters
            line = line.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            story.append(Paragraph(line, body_style))
    doc.build(story)


def generate_document(doc_spec: dict) -> str:
    print(f"  Generating: {doc_spec['filename']}...")
    attempt = 0
    while True:
        try:
            response = _gen_model.generate_content(
                doc_spec["prompt"],
                generation_config=genai.types.GenerationConfig(
                    temperature=0.3,
                    max_output_tokens=2000,
                ),
            )
            return response.text
        except Exception as e:
            err = str(e)
            if "429" in err or "RESOURCE_EXHAUSTED" in err or "quota" in err.lower() or "rate" in err.lower():
                attempt += 1
                print(f"    Rate limit hit (attempt {attempt}), retrying in 10s...")
                time.sleep(10)
            else:
                raise


def main():
    print(f"Generating {len(DOCUMENTS)} synthetic industrial documents for Sunrise Refinery...\n")
    manifest = []

    for i, doc_spec in enumerate(DOCUMENTS, start=1):
        print(f"[{i}/{len(DOCUMENTS)}] {doc_spec['doc_type']}: {doc_spec['filename']}")
        try:
            content = generate_document(doc_spec)

            # Save as text
            txt_path = OUTPUT_DIR / f"{doc_spec['filename']}.txt"
            txt_path.write_text(content, encoding="utf-8")

            # Save as PDF
            pdf_path = OUTPUT_DIR / f"{doc_spec['filename']}.pdf"
            text_to_pdf(content, pdf_path, doc_spec["filename"].replace("_", " "))

            manifest.append({
                "filename": doc_spec["filename"],
                "doc_type": doc_spec["doc_type"],
                "txt_file": str(txt_path),
                "pdf_file": str(pdf_path),
            })
            print(f"    Saved: {txt_path.name} + {pdf_path.name}")

        except Exception as e:
            print(f"    ERROR: {e}")
            continue

    # Save manifest
    manifest_path = OUTPUT_DIR / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2))
    print(f"\nDone! Generated {len(manifest)}/{len(DOCUMENTS)} documents.")
    print(f"Manifest: {manifest_path}")
    print(f"Output dir: {OUTPUT_DIR.resolve()}")


if __name__ == "__main__":
    main()
