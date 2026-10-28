"""Tests for the helper scripts. Run with: python -m pytest"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from fastq_utils import gc_count, mean_quality, phred_scores, read_fastq  # noqa: E402
from filter_reads import filter_reads  # noqa: E402
from read_stats import read_stats  # noqa: E402
from summarize import summarize  # noqa: E402

# Two reads: the first is high quality ("I" = 40), the second low ("#" = 2).
FASTQ = "@good\nGGCCAATT\n+\nIIIIIIII\n@bad\nAAAAAAAA\n+\n########\n"


def write_fastq(tmp_path):
    path = tmp_path / "test.fastq"
    path.write_text(FASTQ)
    return path


def test_phred_scores():
    assert phred_scores("!+5I") == [0, 10, 20, 40]


def test_mean_quality():
    assert mean_quality("II##") == 21


def test_gc_count_ignores_case():
    assert gc_count("GgCcAaTt") == 4


def test_read_fastq(tmp_path):
    reads = list(read_fastq(write_fastq(tmp_path)))
    assert [name for name, _, _ in reads] == ["@good", "@bad"]


def test_filter_reads_keeps_only_good_reads(tmp_path):
    output = tmp_path / "out.fastq"
    kept, total = filter_reads(write_fastq(tmp_path), output, min_quality=20)
    assert (kept, total) == (1, 2)
    assert output.read_text().startswith("@good")


def test_read_stats(tmp_path):
    stats = read_stats(write_fastq(tmp_path), "X")
    assert stats["reads"] == 2
    assert stats["mean_length"] == 8
    assert stats["gc_percent"] == 25.0  # 4 G/C letters out of 16


def test_summarize_sorts_samples(tmp_path):
    b = tmp_path / "b.tsv"
    a = tmp_path / "a.tsv"
    b.write_text("sample\treads\nB\t5\n")
    a.write_text("sample\treads\nA\t3\n")
    lines = summarize([b, a], tmp_path / "summary.tsv")
    assert lines == ["sample\treads", "A\t3", "B\t5"]
