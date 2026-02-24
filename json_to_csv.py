import json
import csv
import os


def convert_avgs_to_csv(json_file="jsons/avgs.json", csv_file="avgs.csv"):
    """Convert jsons/avgs.json to CSV format."""
    try:
        # Read JSON file
        with open(json_file, "r") as f:
            data = json.load(f)

        # Get headers (keys from JSON)
        headers = list(data.keys())

        # Get the number of rows (assuming all lists have same length)
        num_rows = len(data[headers[0]])

        # Create rows by zipping the values
        rows = []
        for i in range(num_rows):
            row = [data[header][i] for header in headers]
            rows.append(row)

        # Write to CSV
        with open(csv_file, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(headers)  # Write headers
            writer.writerows(rows)  # Write data rows

        print(f"✓ Successfully converted {json_file} to {csv_file}")
        print(f"  Headers: {', '.join(headers)}")
        print(f"  Rows written: {num_rows}")

    except FileNotFoundError:
        print(f"Error: {json_file} not found")
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    convert_avgs_to_csv()
