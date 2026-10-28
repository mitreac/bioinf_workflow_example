"""Functions to read FASTQ files, shared by the scripts of the workflow.

A FASTQ file stores each read in 4 lines:

    @read_name
    ACGTTGCA...        sequence
    +
    IIIHHGG#...        quality, one character per letter

We use only the standard library so the workflow runs without installing
anything except Snakemake or Nextflow. For real projects Biopython, pysam or
dnaio are faster and handle more cases.
"""


def read_fastq(path):
    """Yield (name, sequence, quality) for every read in a FASTQ file.

    This is a generator: it reads one record at a time instead of loading the
    whole file. Real FASTQ files can be tens of gigabytes.

    It assumes the common 4-line format, where the sequence and the quality
    are each on one line. Very old files can split them on several lines;
    those are not supported here.
    """
    with open(path) as handle:
        while True:
            name = handle.readline().rstrip()
            # readline() returns "" only at the end of the file
            if not name:
                return
            sequence = handle.readline().rstrip()
            handle.readline()  # "+" line, it carries no information
            quality = handle.readline().rstrip()
            yield name, sequence, quality


def phred_scores(quality):
    """Convert a quality string to Phred scores.

    Each character stores a number as its ASCII code minus 33 (Phred+33),
    which is the encoding of all current Illumina machines. So "!" is 0,
    "+" is 10, "5" is 20 and "I" is 40. Old Illumina files (before 2011)
    used an offset of 64 and would give wrong scores here.

    Phred score Q means an error probability of 10^(-Q/10):
    Q20 is 1 error in 100 letters, Q30 is 1 in 1000.
    """
    return [ord(char) - 33 for char in quality]


def mean_quality(quality):
    """Average Phred score of one read."""
    scores = phred_scores(quality)
    return sum(scores) / len(scores)


def gc_count(sequence):
    """Number of G and C letters in a sequence.

    Uppercase first because some tools write part of the sequence in
    lowercase (for example to mark repeated regions).
    """
    sequence = sequence.upper()
    return sequence.count("G") + sequence.count("C")
