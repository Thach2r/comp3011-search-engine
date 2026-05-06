from src.crawler import crawl
from src.indexer import build_index, save_index, load_index
from src.search import print_word, find_pages

START_URL = "https://quotes.toscrape.com"


def run() -> None:
    """Main command-line interface loop."""
    print("Search Engine ready. Commands: build | load | print <word> | find <query> | quit")
    
    index = None

    while True:
        try:
            user_input = input("\n> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nExiting.")
            break

        if not user_input:
            continue

        parts = user_input.split()
        command = parts[0].lower()

        if command == "quit":
            print("Goodbye.")
            break

        elif command == "build":
            print("Building index... this will take several minutes due to politeness window.")
            pages = crawl(START_URL)
            index = build_index(pages)
            save_index(index)
            print(f"Index built with {len(index)} unique words.")

        elif command == "load":
            index = load_index()

        elif command == "print":
            if len(parts) < 2:
                print("Usage: print <word>")
                continue
            if index is None:
                print("No index loaded. Run 'build' or 'load' first.")
                continue
            print_word(index, parts[1])

        elif command == "find":
            if len(parts) < 2:
                print("Usage: find <word> [word2] ...")
                continue
            if index is None:
                print("No index loaded. Run 'build' or 'load' first.")
                continue
            query = " ".join(parts[1:])
            find_pages(index, query)

        else:
            print(f"Unknown command: '{command}'. Commands: build | load | print <word> | find <query> | quit")


if __name__ == "__main__":
    run()
