# Nextflow

Nextflow is a workflow management system based on Groovy, a language that
runs on Java. It is developed by Seqera and used by the nf-core community.
You do not need to know Groovy or Java for this example. The workflow is in
`main.nf` and the settings are in `nextflow.config`.

Run all commands from the repository folder.


## How Nextflow works

Snakemake starts from the files you want and works backwards. Nextflow starts
from the input data and pushes it forward. This is called the dataflow model.

There are two building blocks:

- A process is one step: inputs, outputs and a script (bash by default).
- A channel is a queue of items (file names, values, or tuples of both) that
  connects processes.

A process starts one task for every item that arrives in its input channel,
as soon as it arrives. There is no global plan made in advance: tasks start
when their data is ready. So sample A can be in step 2 while sample C is
still in step 1.

When you run `nextflow run`, it:

1. Reads `nextflow.config` and the command line parameters.
2. Runs the `workflow` block, which creates the channels and connects the
   processes.
3. For each task, creates a folder `work/xx/xxxxxx...`, links the input files
   into it, and runs the script there. Every task is isolated: it sees only
   its own input files.
4. Collects the output files from the task folder and sends them to the
   next channel.
5. Copies the final files to the output folder (`publishDir`).

Each task folder name is a hash of the script, the input files and the
parameters. With `-resume`, Nextflow computes the hash again and, if a
folder with that hash exists and the task succeeded, it reuses the result
instead of running the task.


## main.nf of this example

```groovy
workflow {
    samples = channel
        .fromPath(params.reads)
        .map { file -> tuple(file.baseName, file) }

    filtered = FILTER_READS(samples)
    stats = READ_STATS(filtered)
    SUMMARIZE(stats.collect())
}
```

The items that flow through the channels:

```
channel.fromPath     A.fastq, B.fastq, C.fastq
.map                 ("A", A.fastq), ("B", B.fastq), ("C", C.fastq)
FILTER_READS         ("A", A.filtered.fastq), ...       one task per item
READ_STATS           A.stats.tsv, B.stats.tsv, ...      one task per item
.collect()           [A.stats.tsv, B.stats.tsv, C.stats.tsv]   one item
SUMMARIZE            summary.tsv                        one task
```

The sample name travels together with the file as a tuple. This is a common
pattern in Nextflow: the name is used for the output file names and the logs,
and no step has to parse it from a file name.

A process declares the shape of the items it receives:

```groovy
process FILTER_READS {
    tag "${sample}"
    publishDir "${params.outdir}/filtered", mode: 'copy'

    input:
    tuple val(sample), path(reads)

    output:
    tuple val(sample), path("${sample}.filtered.fastq")

    script:
    """
    python3 ${params.scripts}/filter_reads.py \\
        --input ${reads} \\
        --output ${sample}.filtered.fastq \\
        --min-quality ${params.min_quality}
    """
}
```

`val` is a value, `path` is a file that Nextflow links into the task folder.
The output is only a file name, because the script writes it in the task
folder. The comments in [main.nf](main.nf) explain each decision.

To see what a task did, open its folder (the hash is printed in the log, for
example `[4f/0e6d8f]`):

```
work/4f/0e6d8f.../
    .command.sh     the script, with the variables replaced
    .command.run    the wrapper Nextflow uses to run .command.sh
    .command.out    standard output of the script
    .command.err    error messages (standard error)
    .exitcode       exit status
    A.fastq         link to the input file
    A.filtered.fastq
```


## Main features

Features used in this example:

- Processes and channels, as described above.
- Operators change channels: `map` transforms each item, `collect` gathers
  all items into one list.
- `params` in `nextflow.config`. Any param can be changed on the command line
  with `--name value` (two dashes). Options of Nextflow itself have one
  dash, for example `-resume`.
- `publishDir` copies final outputs out of `work/`.
- `tag` labels the tasks in the log.
- `-resume` reuses the results of tasks whose hash did not change.

Other important features:

- More operators: `filter`, `groupTuple` (group items by sample), `join`
  (match two channels by key), `channel.fromFilePairs` (paired files such as
  `A_1.fastq` and `A_2.fastq`), `splitFastq` (split a file into chunks).
- Directives that set how each process runs:

  ```groovy
  process ALIGN {
      cpus 8
      memory '16 GB'
      time '2h'
      container 'biocontainers/bwa:v0.7.17_cv1'
      errorStrategy 'retry'
      maxRetries 2
      ...
  }
  ```

- Executors: the same workflow runs locally, on a cluster (SLURM, PBS, SGE,
  LSF), on Kubernetes or in the cloud (AWS Batch, Google Batch, Azure Batch).
  Only the config changes, for example `process.executor = 'slurm'`.
- Profiles group settings in `nextflow.config` and are selected with
  `-profile`, for example `-profile docker,cluster`.
- Software: containers (Docker, Apptainer, Podman) or conda environments for
  each process, enabled with `-with-docker` or `-with-conda`.
- Modules and subworkflows: processes can be placed in separate files and
  imported with `include { FILTER_READS } from './modules/filter_reads'`.
  nf-core shares more than 2000 ready modules for bioinformatics tools.
- Reports: `-with-report` (HTML report with CPU and memory per task),
  `-with-timeline`, `-with-trace` (table of all tasks) and `-with-dag`.
- Run history: `nextflow log` lists previous runs, `nextflow clean` deletes
  their `work/` folders.
- Pipelines from GitHub: `nextflow run nf-core/rnaseq -profile test,docker`
  downloads and runs a published pipeline.


## Run the workflow

```bash
nextflow run nextflow/main.nf
cat results/nextflow/summary.tsv
```

If there is no error and `results/nextflow/summary.tsv` exists, the workflow
ran successfully.


## Exercises

1. Run the workflow again with `-resume`. All tasks are cached.

   ```bash
   nextflow run nextflow/main.nf -resume
   ```

   Without `-resume` Nextflow runs all tasks again. Snakemake does the
   opposite by default.

2. Change the quality threshold. The hash of the filter tasks changes, so
   they run again, and the steps after them too.

   ```bash
   nextflow run nextflow/main.nf -resume --min_quality 30
   cat results/nextflow/summary.tsv
   ```

3. Add a sample. Only the tasks of the new sample and the summary run.

   ```bash
   cp data/samples/A.fastq data/samples/D.fastq
   nextflow run nextflow/main.nf -resume
   rm data/samples/D.fastq
   ```

4. Open a task folder in `work/` and read `.command.sh`, the exact command
   that ran.

5. Create the graph of the workflow and a report with run time and memory use.

   ```bash
   nextflow run nextflow/main.nf -resume -with-dag results/dag.html -with-report results/report.html
   ```

6. List the previous runs.

   ```bash
   nextflow log
   ```


## Snakemake and Nextflow

| | Snakemake | Nextflow |
|---|---|---|
| Language | Python | Groovy |
| Step | rule | process |
| Steps connected by | file names | channels |
| Plans the run | backwards, from the output files | forwards, as data arrives |
| Decides what to rerun | file times, params, code, stored in `.snakemake/` | hash of script, inputs and params, stored in `work/` |
| Runs only what changed | by default | with `-resume` |
| Settings | `config.yaml`, `--config key=value` | `nextflow.config`, `--key value` |
| Intermediate files | where you choose | `work/` folder |
| Shared pipelines | Snakemake workflow catalog, wrappers | nf-core pipelines and modules |


## Start over

```bash
rm -rf results/nextflow work .nextflow .nextflow.log*
```

Documentation: https://www.nextflow.io/docs/latest/
