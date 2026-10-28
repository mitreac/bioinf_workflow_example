"""Step 2: compute the statistics of one sample.

Usage:
    python3 scripts/read_stats.py --input A.filtered.fastq --sample A --output A.stats.tsv

Writes a TSV file with a header and one row:
    sample  reads  mean_length  gc_percent  mean_quality

One small file per sample, instead of appending to a shared file, because the
samples run in parallel. Two jobs writing to the same file at the same time
would mix their lines. The summarize step merges the files at the end.
"""
import argparse

from fastq_utils import gc_count, mean_quality, read_fastq

COLUMNS = ["sample", "reads", "mean_length", "gc_percent", "mean_quality"]


def read_stats(path, sample):
    """Return a dict with the statistics of one FASTQ file."""
    # Running totals instead of lists of values, so memory use stays the same
    # for 2,500 reads or 50 million reads.
    reads = 0
    letters = 0
    gc = 0
    quality_sum = 0.0
    for _, sequence, quality in read_fastq(path):
        reads += 1
        letters += len(sequence)
        gc += gc_count(sequence)
        quality_sum += mean_quality(quality)

    # GC percent is computed over all letters, not per read and then averaged,
    # so longer reads count more. This is how most QC tools report it.
    # The "if reads" checks are needed: with a high threshold all reads of a
    # sample can be removed (try --min-quality 30 on sample C).
    return {
        "sample": sample,
        "reads": reads,
        "mean_length": round(letters / reads, 1) if reads else 0,
        "gc_percent": round(100 * gc / letters, 2) if letters else 0,
        "mean_quality": round(quality_sum / reads, 2) if reads else 0,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, help="FASTQ file")
    # The sample name is passed by the workflow instead of being parsed from
    # the file name. File names change between steps (A.fastq,
    # A.filtered.fastq), and the workflow already knows the name.
    parser.add_argument("--sample", required=True, help="sample name")
    parser.add_argument("--output", required=True, help="output TSV file")
    args = parser.parse_args()

    stats = read_stats(args.input, args.sample)
    with open(args.output, "w") as out:
        out.write("\t".join(COLUMNS) + "\n")
        out.write("\t".join(str(stats[c]) for c in COLUMNS) + "\n")


if __name__ == "__main__":
    main()
