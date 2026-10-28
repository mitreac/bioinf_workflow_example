"""Step 3: merge the statistics of all samples in one table.

Usage:
    python3 scripts/summarize.py --output summary.tsv A.stats.tsv B.stats.tsv C.stats.tsv
"""
import argparse


def summarize(stats_paths, output_path):
    """Merge one-row TSV files into one TSV file, sorted by sample name.

    All input files have the same header, so the header of the last file is
    used and the data rows are collected from all of them.
    """
    header = None
    rows = []
    for path in stats_paths:
        with open(path) as handle:
            lines = handle.read().splitlines()
        header = lines[0]
        rows.extend(lines[1:])

    # Sorting matters. Nextflow passes the files in the order the tasks
    # finished, which changes from run to run. Sorted rows give the same
    # output every time, so the Snakemake and Nextflow results can be
    # compared with diff (see .github/workflows/test.yml).
    rows.sort()

    with open(output_path, "w") as out:
        out.write(header + "\n")
        for row in rows:
            out.write(row + "\n")
    return [header] + rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, help="summary TSV file")
    # nargs="+" accepts any number of files. Both workflows pass the list of
    # files directly on the command line, which is fine for a few hundred
    # samples. For many thousands, pass a file with the list of paths instead.
    parser.add_argument("stats", nargs="+", help="per-sample TSV files")
    args = parser.parse_args()

    for line in summarize(args.stats, args.output):
        print(line.replace("\t", "  "))


if __name__ == "__main__":
    main()
