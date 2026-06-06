from utils import load_config


def main():
    config = load_config()
    pairs = config["pairs"]

    if not pairs:
        print("No pairs configured.")
        return

    print("\nConfigured Pairs\n")
    print("-" * 80)

    for index, pair in enumerate(pairs, start=1):
        status = (
            "Enabled"
            if pair.get("enabled", True)
            else "Disabled"
        )

        print(f"{index}.")
        print(f"Source      : {pair['source']}")
        print(f"Destination : {pair['destination']}")
        print(f"Status      : {status}")
        print("-" * 80)


if __name__ == "__main__":
    main()