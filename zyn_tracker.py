import json
import os
from datetime import date

DATA_FILE = "zyn_data.json"

def load_data():
    if not os.path.exists(DATA_FILE):
        return {"date": str(date.today()), "count": 0}

    with open(DATA_FILE, "r") as f:
        data = json.load(f)

    # Reset count if it's a new day
    if data["date"] != str(date.today()):
        return {"date": str(date.today()), "count": 0}

    return data

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)

def main():
    data = load_data()

    while True:
        print("\n--- Zyn Tracker ---")
        print(f"Date: {data['date']}")
        print(f"Zyns today: {data['count']}")
        print("\nOptions:")
        print("1. Add a Zyn")
        print("2. Remove a Zyn")
        print("3. Exit")

        choice = input("Choose an option (1-3): ").strip()

        if choice == "1":
            data["count"] += 1
            save_data(data)
            print("✅ Zyn added.")

        elif choice == "2":
            if data["count"] > 0:
                data["count"] -= 1
                save_data(data)
                print("➖ Zyn removed.")
            else:
                print("⚠️ Count is already zero.")

        elif choice == "3":
            print("👋 See you later. Stay strong.")
            break

        else:
            print("❌ Invalid option. Try again.")

if __name__ == "__main__":
    main()
