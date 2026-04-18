"""
upload_nist_dataset.py
Uploads the NIST-inspired dataset to your running pipeline server.
Handles the extra columns (process_type, build_orientation, nist_benchmark)
by mapping them into the notes field since the API schema does not have
dedicated columns for those.
"""

import csv
import requests
import json
import time

API_BASE   = "http://localhost:8000/api/v1"
INPUT_FILE = "nist_inspired_am_dataset.csv"

def parse_float(val):
    try:
        return float(val) if val not in ("", None) else None
    except:
        return None

def parse_int(val):
    try:
        return int(val) if val not in ("", None) else None
    except:
        return None

def parse_bool(val):
    return str(val).lower() in ("true", "1", "yes")

def row_to_payload(row):
    # Combine NIST-specific fields into notes
    notes = (
        f"NIST Benchmark: {row.get('nist_benchmark', '')} | "
        f"Process: {row.get('process_type', '')} | "
        f"Orientation: {row.get('build_orientation', '')} | "
        f"Ref: {row.get('nist_dataset_ref', '')} | "
        f"{row.get('notes', '')}"
    )
    return {
        "experiment_id":   row["experiment_id"],
        "experiment_name": row["experiment_name"],
        "material_type":   row["material_type"] or None,
        "material_batch":  row["material_batch"] or None,
        "build_platform":  row["build_platform"] or None,
        "build_date":      row["build_date"] or None,
        "operator":        row["operator"] or None,
        "status":          row["status"] or "completed",
        "notes":           notes,
        "process_parameters": {
            "layer_height":       parse_float(row.get("layer_height")),
            "print_speed":        parse_float(row.get("print_speed")),
            "nozzle_temperature": parse_float(row.get("nozzle_temperature")),
            "bed_temperature":    parse_float(row.get("bed_temperature")),
            "infill_percentage":  parse_float(row.get("infill_percentage")),
            "infill_pattern":     row.get("infill_pattern") or None,
            "shell_count":        parse_int(row.get("shell_count")),
            "support_enabled":    parse_bool(row.get("support_enabled")),
            "print_time_hours":   parse_float(row.get("print_time_hours")),
        },
        "geometry_data": {
            "volume_mm3":       parse_float(row.get("volume_mm3")),
            "surface_area_mm2": parse_float(row.get("surface_area_mm2")),
            "bounding_box_x":   parse_float(row.get("bounding_box_x")),
            "bounding_box_y":   parse_float(row.get("bounding_box_y")),
            "bounding_box_z":   parse_float(row.get("bounding_box_z")),
        },
        "quality_metrics": {
            "tensile_strength_mpa": parse_float(row.get("tensile_strength_mpa")),
            "yield_strength_mpa":   parse_float(row.get("yield_strength_mpa")),
            "elongation_percent":   parse_float(row.get("elongation_percent")),
            "surface_roughness_um": parse_float(row.get("surface_roughness_um")),
            "porosity_percent":     parse_float(row.get("porosity_percent")),
            "density_g_per_cm3":    parse_float(row.get("density_g_per_cm3")),
            "hardness_hb":          parse_float(row.get("hardness_hb")),
            "defect_count":         parse_int(row.get("defect_count")),
        }
    }

def main():
    # Verify server
    try:
        r = requests.get(f"{API_BASE}/health", timeout=5)
        print(f"Server: {r.json().get('status')}\n")
    except Exception as e:
        print(f"Server not reachable: {e}")
        return

    with open(INPUT_FILE, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    total   = len(rows)
    created = skipped = failed = 0
    start   = time.time()

    print(f"Uploading {total} NIST-inspired experiments...\n")

    # Group by material for progress reporting
    by_material = {}
    for row in rows:
        m = row["material_type"]
        by_material.setdefault(m, []).append(row)

    for material, mat_rows in by_material.items():
        print(f"  Material: {material} ({len(mat_rows)} experiments)")
        for row in mat_rows:
            try:
                payload  = row_to_payload(row)
                response = requests.post(
                    f"{API_BASE}/experiments",
                    json=payload,
                    headers={"Content-Type": "application/json"},
                    timeout=15
                )
                if response.status_code == 201:
                    created += 1
                elif response.status_code == 409:
                    skipped += 1
                else:
                    failed += 1
                    print(f"    FAILED {row['experiment_id']}: {response.text[:80]}")
            except Exception as e:
                failed += 1
                print(f"    ERROR {row['experiment_id']}: {e}")

        print(f"    Done — running totals: {created} created, {skipped} skipped, {failed} failed")

    elapsed = round(time.time() - start, 2)

    print(f"\n{'='*55}")
    print(f"NIST DATASET UPLOAD COMPLETE")
    print(f"{'='*55}")
    print(f"  Created  : {created}")
    print(f"  Skipped  : {skipped}")
    print(f"  Failed   : {failed}")
    print(f"  Time     : {elapsed}s")
    print(f"\nCheck results in the UI:")
    print(f"  http://localhost:8000")
    print(f"  http://localhost:8000/dashboard/advanced")
    print(f"  http://localhost:8000/api/analytics/summary")

if __name__ == "__main__":
    main()