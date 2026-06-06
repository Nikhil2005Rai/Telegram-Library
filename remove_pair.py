from utils import load_config, save_config

def main():
    config = load_config()

    pairs = config["pairs"]

    if not pairs:
        print("No pairs configured.")
        return

    print("\nConfigured Pairs\n")

    for index, pair in enumerate(pairs, start=1):
        print(
            f"{index}. "
            f"{pair['source']} -> {pair['destination']}"
        )

    try:
        choice = int(
            input(
                "\nEnter pair number to remove: "
            )
        )

        if choice < 1 or choice > len(pairs):
            print("Invalid choice.")
            return

        removed = pairs.pop(choice - 1)

        save_config(config)

        print("\nPair removed successfully!")
        print(
            f"{removed['source']} -> "
            f"{removed['destination']}"
        )

    except ValueError:
        print("Please enter a valid number.")


if __name__ == "__main__":
    main()