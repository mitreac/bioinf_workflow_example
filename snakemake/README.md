# Snakemake

Snakemake is a workflow management system written in Python and developed in
the bioinformatics community. A workflow is written in a file called
`Snakefile`. The Snakefile is Python with extra keywords for rules, so normal
Python (variables, functions, imports, loops) can be used anywhere in it.

Run all commands from the repository folder.


## How Snakemake works

Snakemake is based on files, like `make`. Each rule says which output files it
can create, from which input files, with which command. Rules are not called
in order. Snakemake decides which rules to run by looking at file names.

When you run `snakemake`, it:

1. Reads the Snakefile. This is normal Python execution, so the code at the
   top (`configfile`, `glob_wildcards`) runs first.
2. Takes the target: the files given on the command line, or the input of the
   first rule if none are given.
3. Works backwards. For each file it needs, it looks for a rule whose output
   pattern matches the file name. Matching sets the wildcards, and the
   wildcards give the input files of that rule, which in turn are matched to
   other rules. The result is the graph of jobs (DAG) from the raw data to
   the target.
4. Decides which jobs must run. A job runs if its output is missing, or if
   something changed since the output was created: an input file is newer,
   or the params, the command or the software environment changed.
   This information is stored in the `.snakemake/` folder.
5. Runs the jobs, as many at the same time as `--cores` allows, always
   after the jobs they depend on.

Because Snakemake works backwards from file names, the main design decision
in a Snakefile is the naming of the files. In this example every file name
contains the sample name, so `{sample}` can be extracted from any path.


## The Snakefile of this example

```
rule all            needs results/snakemake/summary.tsv
rule summarize      makes summary.tsv from stats/{A,B,C}.stats.tsv
rule read_stats     makes stats/{sample}.stats.tsv from filtered/{sample}.filtered.fastq
rule filter_reads   makes filtered/{sample}.filtered.fastq from data/samples/{sample}.fastq
```

Snakemake starts from `all`, sees that it needs `summary.tsv`, finds that
`summarize` can make it, and so on back to the FASTQ files in `data/samples/`.

```python
rule filter_reads:
    input:
        "data/samples/{sample}.fastq",
    output:
        "results/snakemake/filtered/{sample}.filtered.fastq",
    params:
        min_quality=config["min_quality"],
    log:
        "results/snakemake/logs/filter_{sample}.log",
    shell:
        "python3 scripts/filter_reads.py --input {input} --output {output} "
        "--min-quality {params.min_quality} 2> {log}"
```

In the command, `{input}`, `{output}`, `{params.min_quality}` and `{log}` are
replaced with the values of the job. For sample A the command becomes:

```bash
python3 scripts/filter_reads.py --input data/samples/A.fastq \
    --output results/snakemake/filtered/A.filtered.fastq --min-quality 20 \
    2> results/snakemake/logs/filter_A.log
```

The comments in the [Snakefile](Snakefile) explain each decision.


## Main features

Features used in this example:

- Wildcards. `{sample}` in input and output makes one rule work for any
  number of samples.
- `glob_wildcards()` finds the sample names from the files on disk.
- `expand()` builds a list of file names, one per sample. A rule with a list
  as input waits for all of them, which is how `summarize` collects all samples.
- `configfile:` loads settings from YAML. Any value can be changed with
  `--config key=value`.
- `params:` passes settings to the command and makes Snakemake rerun the
  rule when they change.
- `log:` saves the messages of each job in its own file.

Other important features:

- Three ways to run a step: `shell:` runs a command, `run:` runs Python code
  directly in the Snakefile, `script:` runs a Python or R script that gets a
  `snakemake` object with `input`, `output` and `params`.

  ```python
  rule plot:
      input: "results/snakemake/summary.tsv"
      output: "results/snakemake/gc.png"
      script: "scripts/plot_gc.py"     # uses snakemake.input[0], snakemake.output[0]
  ```

- Software environments for each rule. The tools of each step can be
  installed automatically, so the workflow runs on another computer with the
  same versions. Run with `--software-deployment-method conda` (or
  `apptainer`).

  ```python
  rule align:
      conda: "envs/bwa.yaml"
      container: "docker://biocontainers/bwa:v0.7.17_cv1"
  ```

- Resources: `threads:` and `resources: mem_mb=...` tell the scheduler what
  each job needs, so jobs are not started when there are not enough cores or
  memory.
- `benchmark:` saves run time and memory use of each job to a file.
- `temp()` deletes an intermediate file when no other job needs it, useful
  for large files. `protected()` makes an output read-only.
- Input functions and checkpoints: inputs can be computed by a Python
  function, and checkpoints let the graph change during the run, when the
  number of files is only known after a step (for example splitting a file
  into an unknown number of parts).
- Executor plugins and profiles: the same Snakefile runs on a cluster or in the
  cloud with `--executor slurm` (plugin `snakemake-executor-plugin-slurm`) or
  with a profile that stores these options.
- Reuse: `module` imports rules from another workflow, and
  [Snakemake wrappers](https://snakemake-wrappers.readthedocs.io) are ready
  rules for common bioinformatics tools.
- Checks and reports: `--lint` reviews the Snakefile, `--summary` shows the
  status of every output, `--report` creates an HTML report.


## Run the workflow

```bash
snakemake --snakefile snakemake/Snakefile --cores 2
cat results/snakemake/summary.tsv
cat results/snakemake/logs/*.log
```

If there is no error and `results/snakemake/summary.tsv` exists, the workflow
ran successfully.


## Exercises

1. Run the workflow again. Nothing runs, all the files are up to date.

   ```bash
   snakemake --snakefile snakemake/Snakefile --cores 2
   ```

2. Dry run: show the jobs and the commands without running them.

   ```bash
   snakemake --snakefile snakemake/Snakefile --dry-run --printshellcmds
   ```

3. Change the quality threshold. Snakemake detects the change of the param,
   and the filter step and the steps after it run again.

   ```bash
   snakemake --snakefile snakemake/Snakefile --cores 2 --config min_quality=30
   cat results/snakemake/summary.tsv
   ```

4. Delete the stats file of sample B and the summary. Only these 2 jobs run
   again.

   ```bash
   rm results/snakemake/stats/B.stats.tsv results/snakemake/summary.tsv
   snakemake --snakefile snakemake/Snakefile --cores 2
   ```

5. Add a sample. The Snakefile does not change.

   ```bash
   cp data/samples/A.fastq data/samples/D.fastq
   snakemake --snakefile snakemake/Snakefile --cores 2
   rm data/samples/D.fastq
   ```

6. Run only part of the workflow, up to the filter step.

   ```bash
   snakemake --snakefile snakemake/Snakefile --cores 2 --forceall --until filter_reads
   ```

7. Show the graph of jobs. Paste the output in https://mermaid.live

   ```bash
   snakemake --snakefile snakemake/Snakefile --dag mermaid-js
   ```

8. Run the linter and follow its suggestions (add a `log:` to every rule, add
   a conda environment).

   ```bash
   snakemake --snakefile snakemake/Snakefile --lint
   ```


## Start over

```bash
rm -rf results/snakemake .snakemake
```

Documentation: https://snakemake.readthedocs.io
