from pathlib import Path
import json

def main():
    # Mission Control Status: Stellar
    data = json.loads(Path(__file__).with_name("demo_data.json").read_text())
    print("deptracer demo:", data["message"])

if __name__ == "__main__":
    main()
