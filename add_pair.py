from utils import load_config, save_config


def main():
    config = load_config()

    print("\n=== Add New Channel Pair ===\n")

    source = int(
        input("Source Channel ID: ").strip()
    )

    destination = int(
        input("Destination Channel ID: ").strip()
    )

    # Check if pair already exists
    for pair in config["pairs"]:
        if (
            pair["source"] == source
            and pair["destination"] == destination
        ):
            print("\nPair already exists.")
            return

    config["pairs"].append(
        {
            "source": source,
            "destination": destination,
            "enabled": True
        }
    )

    save_config(config)

    print("\nPair added successfully!")
    print(f"Source      : {source}")
    print(f"Destination : {destination}")


if __name__ == "__main__":
    main()