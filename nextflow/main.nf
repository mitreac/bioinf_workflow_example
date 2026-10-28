// Nextflow version of the read quality workflow.
//
// Run from the repository folder:
//     nextflow run nextflow/main.nf
//
// Settings are in nextflow.config (params). Change them on the command line
// with two dashes, for example: --min_quality 30
// Options with one dash belong to Nextflow itself, for example: -resume


// Step 1: remove the reads with low quality.
//
// A process does not know about files on disk. Each task runs in its own
// folder under work/, and Nextflow links the input files into that folder.
// That is why the output is just a file name: the script writes it in the
// task folder and Nextflow picks it up from there.
process FILTER_READS {
    // Shows the sample name in the log, instead of only a task number.
    tag "${sample}"

    // work/ is Nextflow's internal storage and has hashed folder names.
    // publishDir copies the outputs to a readable place. The default mode is
    // a symbolic link into work/, which breaks if work/ is deleted, so we copy.
    publishDir "${params.outdir}/filtered", mode: 'copy'

    input:
    // val is a value (the sample name), path is a file to link into the task
    // folder. The name travels with the file through all the steps, so later
    // steps do not have to parse it from the file name.
    tuple val(sample), path(reads)

    output:
    tuple val(sample), path("${sample}.filtered.fastq")

    // The script block is a bash script. ${...} are Nextflow variables and
    // are replaced before the script runs.
    //
    // The scripts are called from the shared scripts/ folder so that Snakemake
    // and Nextflow run the same code. The usual Nextflow convention is a bin/
    // folder next to main.nf: Nextflow adds it to PATH, and the script can be
    // called by name.
    script:
    """
    python3 ${params.scripts}/filter_reads.py \\
        --input ${reads} \\
        --output ${sample}.filtered.fastq \\
        --min-quality ${params.min_quality}
    """
}


// Step 2: compute the statistics of each sample.
process READ_STATS {
    tag "${sample}"
    publishDir "${params.outdir}/stats", mode: 'copy'

    input:
    tuple val(sample), path(reads)

    output:
    // Only the file goes on: summarize does not need the sample name,
    // it is already written in the file.
    path "${sample}.stats.tsv"

    script:
    """
    python3 ${params.scripts}/read_stats.py \\
        --input ${reads} \\
        --sample ${sample} \\
        --output ${sample}.stats.tsv
    """
}


// Step 3: merge the statistics of all samples in one table.
process SUMMARIZE {
    publishDir params.outdir, mode: 'copy'

    input:
    // Receives a list of files. Nextflow links all of them into the task
    // folder and ${stats_files} becomes their names separated by spaces.
    path stats_files

    output:
    path "summary.tsv"

    script:
    """
    python3 ${params.scripts}/summarize.py --output summary.tsv ${stats_files}
    """
}


// The workflow block connects the processes with channels. A channel is a
// queue of items. A process starts one task for each item it receives, as
// soon as the item arrives, so different samples run at the same time and
// sample A can be in READ_STATS while sample C is still in FILTER_READS.
workflow {
    // One item per FASTQ file. map turns each file into a pair
    // (sample name, file); baseName is the file name without the extension,
    // so data/samples/A.fastq gives ("A", A.fastq).
    samples = channel
        .fromPath(params.reads)
        .map { file -> tuple(file.baseName, file) }

    // Calling a process with a channel returns its output channel.
    filtered = FILTER_READS(samples)
    stats = READ_STATS(filtered)

    // collect() waits until the channel is closed (all samples are done) and
    // sends one item: the list of all files. Without it, SUMMARIZE would run
    // once per sample.
    SUMMARIZE(stats.collect())
}
