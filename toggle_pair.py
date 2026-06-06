from utils import load_config, save_config

def main():
    config = load_config()

    pairs = config["pairs"]

    if not pairs:
        print("No pairs configured.")
        return

    print("\nConfigured Pairs\n")
    print("-" * 80)

    for index, pair in enumerate(pairs, start=1):
        status = "Enabled" if pair.get("enabled", True) else "Disabled"

        print(f"{index}.")
        print(f"Source      : {pair['source']}")
        print(f"Destination : {pair['destination']}")
        print(f"Status      : {status}")
        print("-" * 80)

    try:
        choice = int(
            input("\nEnter pair number to toggle: ")
        )

        if choice < 1 or choice > len(pairs):
            print("Invalid choice.")
            return

        pair = pairs[choice - 1]

        current = pair.get("enabled", True)

        pair["enabled"] = not current

        save_config(config)

        new_status = (
            "Enabled"
            if pair["enabled"]
            else "Disabled"
        )

        print("\nPair updated successfully!")
        print(
            f"{pair['source']} -> "
            f"{pair['destination']}"
        )
        print(f"New Status: {new_status}")

    except ValueError:
        print("Please enter a valid number.")


if __name__ == "__main__":
    main()