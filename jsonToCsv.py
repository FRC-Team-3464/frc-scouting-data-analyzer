import json
import csv

def convertAvgsToCsv(json_file="jsons/avgs.json", csv_file="jsons/avgs.csv"):
    """Convert jsons/avgs.json to CSV format."""
    try:
        with open(json_file, "r") as f:
            data = json.load(f)

        headers = list(data.keys())

        num_rows = len(data[headers[0]])

        rows = []
        for i in range(num_rows):
            row = [data[header][i] for header in headers]
            rows.append(row)

        with open(csv_file, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(headers)
            writer.writerows(rows)

        print(f"Successfully converted {json_file} to {csv_file}")
        print(f"Headers: {', '.join(headers)}")
        print(f"Rows written: {num_rows}")
    except FileNotFoundError:
        print(f"Error: {json_file} not found")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    convert_avgs_to_csv()
