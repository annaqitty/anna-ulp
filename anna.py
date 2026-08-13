import os
import re
from concurrent.futures import ThreadPoolExecutor, as_completed


def get_available_filename(filename):
    """Return a filename that does not overwrite an existing file."""
    if not os.path.exists(filename):
        return filename

    name, extension = os.path.splitext(filename)
    counter = 2

    while True:
        new_filename = f"{name}({counter}){extension}"

        if not os.path.exists(new_filename):
            return new_filename

        counter += 1


# Patterns
host_pattern = re.compile(
    r'^\s*(?:Host|Url|Hostname|Log)\s*:\s*(.+?)\s*$',
    re.IGNORECASE | re.MULTILINE
)

email_pattern = re.compile(
    r'^\s*(?:Email|User|Username|Login)\s*:\s*(.+?)\s*$',
    re.IGNORECASE | re.MULTILINE
)

password_pattern = re.compile(
    r'^\s*(?:Pass|Password|Passwd)\s*:\s*(.+?)\s*$',
    re.IGNORECASE | re.MULTILINE
)


def scan_file(filepath):
    """
    Scan one TXT or LOG file.
    Returns:
        URL|LOGIN:PASS results
        LOGIN:PASS results
    """

    url_log_pass_results = []
    log_pass_results = []

    try:
        with open(
            filepath,
            "r",
            encoding="utf-8",
            errors="ignore"
        ) as f:
            text = f.read()

    except (FileNotFoundError, PermissionError, OSError) as e:
        return filepath, [], [], str(e)

    # Extract values
    hosts = [x.strip() for x in host_pattern.findall(text)]
    emails = [x.strip() for x in email_pattern.findall(text)]
    passwords = [x.strip() for x in password_pattern.findall(text)]

    # Combine results
    for host, email, password in zip(hosts, emails, passwords):

        line_url_log_pass = f"{host}|{email}:{password}"
        line_log_pass = f"{email}:{password}"

        url_log_pass_results.append(line_url_log_pass)
        log_pass_results.append(line_log_pass)

    return filepath, url_log_pass_results, log_pass_results, None


def main():

    # Input folder
    input_folder = input(
        "Enter input folder path: "
    ).strip()

    # Number of threads
    while True:
        try:
            threads = int(
                input("Enter number of threads: ").strip()
            )

            if threads > 0:
                break

            print("Threads must be greater than 0!")

        except ValueError:
            print("Please enter a valid number!")

    # Check folder
    if not os.path.exists(input_folder):
        print("Folder not found!")
        input("Press Enter to exit...")
        return

    # Output filenames
    output_url_log_pass = get_available_filename(
        "Result-URL-LOG-PASS.txt"
    )

    output_log_pass = get_available_filename(
        "Result-LOG-PASS.txt"
    )

    results_url_log_pass = []
    results_log_pass = []

    # Find all TXT and LOG files
    files_to_scan = []

    for root, folders, files in os.walk(input_folder):

        for filename in files:

            if filename.lower().endswith((".txt", ".log")):

                filepath = os.path.join(root, filename)
                files_to_scan.append(filepath)

    print("\n==========================")
    print(f"Files found: {len(files_to_scan)}")
    print(f"Threads: {threads}")
    print("==========================\n")

    # Scan files using threads
    with ThreadPoolExecutor(max_workers=threads) as executor:

        futures = {
            executor.submit(scan_file, filepath): filepath
            for filepath in files_to_scan
        }

        completed = 0
        total_files = len(files_to_scan)

        for future in as_completed(futures):

            completed += 1

            try:
                filepath, url_results, log_results, error = future.result()

                if error:
                    print(
                        f"[{completed}/{total_files}] "
                        f"SKIPPED: {filepath}"
                    )
                    print(f"Reason: {error}")
                    continue

                print(
                    f"[{completed}/{total_files}] "
                    f"Scanned: {filepath}"
                )

                for line in url_results:
                    print(line)

                results_url_log_pass.extend(url_results)
                results_log_pass.extend(log_results)

            except Exception as e:
                filepath = futures[future]

                print(
                    f"[{completed}/{total_files}] "
                    f"ERROR: {filepath}"
                )

                print(f"Reason: {e}")

    # Save URL|LOGIN:PASS
    with open(
        output_url_log_pass,
        "w",
        encoding="utf-8"
    ) as f:

        f.write("\n".join(results_url_log_pass))

    # Save LOGIN:PASS
    with open(
        output_log_pass,
        "w",
        encoding="utf-8"
    ) as f:

        f.write("\n".join(results_log_pass))

    # Finished
    print("\n==========================")
    print("Finished!")
    print(f"Total files scanned: {len(files_to_scan)}")
    print(f"Total extracted: {len(results_url_log_pass)}")
    print("==========================")
    print("Saved URL|LOGIN:PASS:")
    print(output_url_log_pass)
    print("==========================")
    print("Saved LOGIN:PASS:")
    print(output_log_pass)
    print("==========================")

    input("\nPress Enter to exit...")


if __name__ == "__main__":
    main()
