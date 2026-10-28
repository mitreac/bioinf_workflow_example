"""Step 1: remove the reads with low quality.

Usage:
    python3 scripts/filter_reads.py --input data/samples/A.fastq \
        --output A.filtered.fastq --min-quality 20

A read is kept if its average quality is at least --min-quality.
Tools used in practice (fastp, Trimmomatic, cutadapt) usually trim the low
quality end of a read instead of removing the whole read. We use the average
because it is easy to follow and still shows the effect of the threshold.
"""
import argparse
import sys

# Works because Python adds the folder of the running script (scripts/) to
# sys.path. Both workflows call the script by its path, so the import is found
# no matter which folder the workflow runs in.
from fastq_utils import mean_quality, read_fastq


def filter_reads(input_path, output_path, min_quality):
    """Write the reads with mean quality >= min_quality.

    Returns (kept, total) so the caller can report how many reads were removed.
    The output is written while reading, so memory use does not depend on the
    size of the file.
    """
    kept = 0
    total = 0
    with open(output_path, "w") as out:
        for name, sequence, quality in read_fastq(input_path):
            total += 1
            if mean_quality(quality) >= min_quality:
                out.write(f"{name}\n{sequence}\n+\n{quality}\n")
                kept += 1
    return kept, total


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, help="raw FASTQ file")
    parser.add_argument("--output", required=True, help="filtered FASTQ file")
    parser.add_argument("--min-quality", type=float, default=20)
    args = parser.parse_args()

    kept, total = filter_reads(args.input, args.output, args.min_quality)

    # An empty input file would give a division by zero.
    percent = 100 * kept / total if total else 0

    # The message goes to stderr, not stdout. Snakemake saves it in the log
    # file of the rule (2> {log}) and Nextflow in .command.err of the task.
    # Keeping stdout free means the script could also be used in a pipe.
    print(f"{args.input}: kept {kept} of {total} reads ({percent:.1f}%)", file=sys.stderr)


if __name__ == "__main__":
    main()
