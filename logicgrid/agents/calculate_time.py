import csv
import sys

def calculate_average_time(csv_file):
    total_time = 0
    count = 0
    
    with open(csv_file, 'r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        for row in reader:
            if row['solve_time'] and row['status'] == 'solved':
                total_time += float(row['solve_time'])
                count += 1
    
    return total_time / count if count > 0 else 0

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python calculate_time.py <csv_file>")
        sys.exit(1)
    
    csv_file = sys.argv[1]
    avg_time = calculate_average_time(csv_file)
    print(f"Average solve time: {avg_time:.2f} seconds")