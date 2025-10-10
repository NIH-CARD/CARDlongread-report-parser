# NIA CARD Long Read Sequencing ONT JSON Run Report Parsing and Visualization Dashboard

The NIA CARD Long-Read Sequencing group sequences some 30-50 human genomes per week from brain and blood genomic DNA using Oxford Nanopore Technologies (ONT) PromethION sequencers. Given these samples both often belong to larger cohorts (more than 30-50 samples), batch to batch variation is inevitable, and ONT has steadily modified sequencing library chemistry, flow cells, instrument software, and basecalling models, regular sequencing quality control is critical to examine how our sequencing efforts change over time. The included Python scripts automate the process of collecting key sequencing statistics from weekly and cohort-wide ONT sequencing runs and generate QC analytics as an Excel spreadsheet. They take run output MinKNOW run report JSON files as input and pull sequencing statistics from exact locations in each JSON hierarchical data structure. The scripts have been written to handle JSON files from MinKNOW version 25.05.14 and earlier, with validation on JSONs going back to MinKNOW version 22.05.7. Recent updates make it possible to incorporate platform QC flow cell checks from before sequencing into the QC visualization dashboard as well. Grouping functions to handle multiple input summary TSVs and color code by input name (e.g., cohort name) have been implemented (see usage below) and will be further documented with a tutorial example. Please report any bugs in the Issues tab to further improve the parser.

Compared to downstream nanopore QC tools (e.g., NanoComp, NanoPlot), this raw QC JSON parser has the advantage of speed and taking small (500KB-65MB) JSONs available immediately after sequencing as input to calculate a number of run QC metrics, while other QC tools require a much larger (on the order of 1-2GB) sequencing_summary.txt input file or even basecalled nanopore data.

## Quality control metrics tracked and parser output fields

The following quality control metrics are extracted from each MinKNOW raw QC report JSON and output in order as a table used for further QC dashboard generation. When these are not found in a JSON, they are listed in the raw QC output table as 'NA'. Numeric values are rounded to three decimal places with the exception of read N50 (kb), which is rounded to two decimal places.

| Metric | Definition |
| ------ | ---------- |
| Experiment Name | Name of experiment as entered into MinKNOW before initiating the sequencing run |
| Sample Name | Name of sample within above experiment as entered into MinKNOW before initiating sequencing run |
| Run Date | The month, day, and year the sequencing run was conducted (e.g., 2024-05-14) |
| Sequencer ID | Serial number for the instrument on which the sequencing run was conducted; formerly named PROM ID |
| Flow Cell Position | Alphanumeric designation for position in which sequencing run flow cell was inserted into the sequencer (e.g., 1A, 2D, 6F) |
| Flow Cell ID | Eight digit alphanumeric serial number identifying flow cell (e.g., PAW33034) |
| Flow Cell Product Code | Identification of flow cell type used for sequencing (e.g., FLO-PRO114M) |
| Data output (Gb) | Amount of sequencing data generated within run in gigabases; reported for estimated bases, not basecalled bases, as shown in MinKNOW HTML report |
| Read Count (M) | Total number of reads sequenced during run in millions |
| N50 (kb) | Read length at which 50% of total bases are included, ranking reads from shortest to longest; reported for estimated bases, not basecalled bases, as shown in MinKNOW HTML report |
| MinKNOW Version | Version of MinKNOW software used to sequence run (e.g., 25.05.14) |
| Sample Rate (Hz) | Number of times current is measured per second for each channel in the flow cell |
| Starting Median Translocation Speed | Median number of bases passing through each channel per second by the first measurement |
| Average Median Translocation Speed Over Time | Average median number of bases passing through each channel per second over the course of the run |
| Weighted Average Median Translocation Speed Over Time | Average median number of bases passing through each channel per second over the course of the run, weighted by the number of translocation events at each time point |
| Starting Median Q Score | Median basecalling quality (Q) score of reads collected by first measurment |
| Average Median Q Score Over Time | Average median basecalling quality (Q) score of reads collected over the course of the run |
| Weighted Average Median Translocation Speed Over Time | Average median basecalling quality (Q) score of reads collected over the course of the run, weighted by the number of reads at each time point |
| Passed Bases (Gb) | Total gigabases (Gb) of reads above the per read average Q score filter (Q8 for fast, Q9 for high-accuracy, and Q10 for super-accurate basecalling) |
| Failed Bases (Gb) | Total gigabases (Gb) of reads below the per read average Q score filter (Q8 for fast, Q9 for high-accuracy, and Q10 for super-accurate basecalling) |
| Passed Reads (M) | Total number of reads in millions above the per read average Q score filter (Q8 for fast, Q9 for high-accuracy, and Q10 for super-accurate basecalling) |
| Failed Reads (M) | Total number of reads in millions below the per read average Q score filter (Q8 for fast, Q9 for high-accuracy, and Q10 for super-accurate basecalling) |
| Percentage Passed Bases | Percentage of total bases above the per read average Q score filter (Q8 for fast, Q9 for high-accuracy, and Q10 for super-accurate basecalling) |
| Percentage Passed Reads | Percentage of total reads above the per read average Q score filter (Q8 for fast, Q9 for high-accuracy, and Q10 for super-accurate basecalling) |
| Passed Modal Q Score | Basecalling quality score mode (most often value) for reads above the per read average Q score filter (Q8 for fast, Q9 for high-accuracy, and Q10 for super-accurate basecalling) |
| Failed Modal Q Score | Basecalling quality score mode (most often value) for reads below the per read average Q score filter (Q8 for fast, Q9 for high-accuracy, and Q10 for super-accurate basecalling) |
| Starting Active Pores | Initial number of pores available for sequencing based on the first mux scan |
| Second Active Pore Count | Pores available for sequencing at the second mux scan if available in the run report |
| Average Active Pores | Average number of pores available for sequencing over the course of the sequencing run, based on all mux scans provided in run report |
| Active Pore AUC | Area Under the Curve (AUC) of pores available for sequencing calculated as the active pore total for all mux scans |
| Average Active Pore Change Per Mux Scan | Average number of pores available for sequencing lost or gained per mux scan (run every 90 minutes by default), calculated from consecutive mux scan results (e.g., mux scan active pore count - previous mux scan active pore count) |
| Starting Pore Occupancy | Initial percentage of total pores available for sequencing that are in an actively sequencing state (strand or adapter); further defined and described here: https://nanoporetech.com/support/flow-cells/general-flow-cell-FAQs/pore-occupancy |
| Average Pore Occupancy | Average percentage of total pores available for sequencing that are in an actively sequencing state (strand or adapter) over the course of the run |
| Starting Adapter Sequencing Percentage | Initial percentage of actively sequencing pores that are sequencing adapter rather than sample DNA (strand) |
| Average Adapter Sequencing Percentage | Average percentage of actively sequencing pores that are sequencing adapter rather than sample DNA (strand) over the course of the run |
| Start Run ISO Timestamp | When sequencing run began, given in ISO 8601 date format (e.g., 2024-05-14T21:23:35.883780864Z) |
| Start Run Timestamp | When sequencing run began, given in Unix epoch date format (e.g., 1715721816) |

## Dependencies

The Python scripts were tested and developed with the following dependency modules (and respective versions where applicable). We have recently substituted the default Python JSON handling library json for the faster, more correct, Rust-enhanced orjson (https://github.com/ijl/orjson) library, leading to a 40% speed boost in preliminary testing on JSONs exported from MinKNOW 24.11.11 and 25.05.14. We have also noted that we have commonly had to inactivate default conda environments in order to run the parser and analytics dashboard generator on our HPC cluster (NIH Biowulf).

Python 3.10.8  
numpy 1.26.4  
pandas 2.0.3  
seaborn 0.12.2  
matplotlib 3.7.2  
orjson 3.9.2  
argparse 1.1  
dateutil 2.8.2  
openpyxl 3.1.2  
xlsxwriter 3.1.2  
datetime  
dateutil  
statistics  
dataclasses  
glob  
io  

## Usage

```CARDlongread_extract_from_json.py``` takes a list of Oxford Nanopore sequencing report JSON files as inputs (or a directory containing all JSON files to analyze) and returns a table with the following fields per JSON, as described above:

Experiment Name, Sample Name, Run Date, Sequencer ID, Flow Cell Position, Flow Cell ID, Flow Cell Product Code, Data output (Gb), Read Count (M), N50 (kb), MinKNOW Version, Sample Rate (Hz), Starting Median Translocation Speed, Average Median Translocation Speed Over Time, Weighted Average Median Translocation Speed Over Time, Starting Median Q Score, Average Median Q Score Over Time, Weighted Average Median Q Score Over Time, Passed Bases (Gb), Failed Bases (Gb), Passed Reads (M), Failed Reads (M), Percentage Passed Bases, Percentage Passed Reads, Passed Modal Q Score, Failed Modal Q Score, Starting Active Pores, Second Active Pore Count, Average Active Pores, Active Pore AUC, Average Active Pore Change Per Mux Scan, Starting Pore Occupancy, Average Pore Occupancy, Starting Adapter Sequencing Percentage, Average Adapter Sequencing Percentage, Start Run ISO Timestamp, Start Run Timestamp

N50 (kb) refers to the read N50 for estimated bases read lengths (not basecalled bases). N50 extraction has been patched to extract this field from the corresponding estimated bases read length histogram in JSONs from MinKNOW versions older and newer than 24.11.11.

Below is sample output from the script:
```
Experiment Name	Sample Name	Run Date	Sequencer ID	Flow Cell Position	Flow Cell ID	Flow Cell Product Code	Data output (Gb)	Read Count (M)	N50 (kb)	MinKNOW Version	Sample Rate (Hz)	Starting Median Translocation Speed	Average Median Translocation Speed Over Time	Weighted Average Median Translocation Speed Over Time	Starting Median Q Score	Average Median Q Score Over Time	Weighted Average Median Q Score Over Time	Passed Bases (Gb)	Failed Bases (Gb)	Passed Reads (M)	Failed Reads (M)	Percentage Passed Bases	Percentage Passed Reads	Passed Modal Q Score	Failed Modal Q Score	Starting Active Pores	Second Active Pore Count	Average Active Pores	Active Pore AUC	Average Active Pore Change Per Mux Scan	Starting Pore Occupancy	Average Pore Occupancy	Starting Adapter Sequencing Percentage	Average Adapter Sequencing Percentage	Start Run ISO Timestamp	Start Run Timestamp
Chile_404	Chile_404	2024-05-14	PC24B302	2D	PAW33034	FLO-PRO114M	141.083	7.345	23.39	24.02.10	5000	NA	NA	NA	NA	NA	NA	NA	NA	NA	NA	NA	NA	NA	NA	7644	7295	4312.5	198375	133.556	97.306	97.243	0.154	0.111	2024-05-14T21:23:35.883780864Z	1715721816
Chile_406	Chile_406	2024-05-01	PC24B302	2E	PAW73369	FLO-PRO114M	131.699	7.426	22.79	24.02.10	5000	NA	NA	NA	NA	NA	NA	NA	NA	NA	NA	NA	NA	NA	NA	7431	7118	4108.0	188968	127.622	97.547	97.305	0.087	0.081	2024-05-01T19:49:27.062103580Z	1714592967
Chile_509	Chile_509	2024-05-14	PC24B302	2F	PAW61512	FLO-PRO114M	117.861	7.947	17.12	24.02.10	5000	NA	NA	NA	NA	NA	NA	NA	NA	NA	NA	NA	NA	NA	NA	7604	7028	3559.674	163745	138.4	97.486	97.088	0.186	0.137	2024-05-14T21:28:27.860263815Z	1715722108
Chile_511	Chile_511	2024-05-08	PC24B302	2D	PAW71368	FLO-PRO114M	133.097	7.548	20.69	24.02.10	5000	NA	NA	NA	NA	NA	NA	NA	NA	NA	NA	NA	NA	NA	NA	7370	6972	4125.326	189765	123.111	97.833	97.86	0.102	0.088	2024-05-08T20:46:57.642743302Z	1715201218
Chile_516	Chile_516	2024-05-01	PC24B302	2D	PAW71977	FLO-PRO114M	129.544	6.625	23.63	24.02.10	5000	NA	NA	NA	NA	NA	NA	NA	NA	NA	NA	NA	NA	NA	NA	7837	7424	4021.457	184987	143.467	97.207	96.481	0.121	0.119	2024-05-01T19:47:57.769730497Z	1714592878
```

The file list should contain paths to each report on each line, like so:
```
/data/CARD_AUX/LRS_temp/CHILE/SEQ_REPORTS/Chile_404/PAW33034/other_reports_PAW33034/report_PAW33034_20240514_2123_c7d4ac03.json
/data/CARD_AUX/LRS_temp/CHILE/SEQ_REPORTS/Chile_406/PAW73369/other_reports_PAW73369/report_PAW73369_20240501_1949_4e83275d.json
/data/CARD_AUX/LRS_temp/CHILE/SEQ_REPORTS/Chile_509/PAW61512/other_reports_PAW61512/report_PAW61512_20240514_2128_5a659d71.json
/data/CARD_AUX/LRS_temp/CHILE/SEQ_REPORTS/Chile_511/PAW71368/other_reports_PAW71368/report_PAW71368_20240508_2046_20d811c8.json
/data/CARD_AUX/LRS_temp/CHILE/SEQ_REPORTS/Chile_516/PAW71977/other_reports_PAW71977/report_PAW71977_20240501_1947_c6a80210.json
```

Example usage (```python CARDlongread_extract_from_json.py -h```):
```
usage: CARDlongread_extract_from_json.py [-h] [--json_dir JSON_DIR] [--filelist FILELIST] [--output OUTPUT_FILE]

Extract data from long read JSON report

optional arguments:
  -h, --help            show this help message and exit
  --json_dir JSON_DIR   path to directory containing JSON files, if converting whole directory
  --filelist FILELIST   text file containing list of all JSON reports to parse
  --output OUTPUT_FILE  Output long read JSON report summary table in tab-delimited format
```

```CARDlongread_extract_summary_statistics.py``` then generates an sequencing QC analytics spreadsheet from the output table of ```CARDlongread_extract_from_json.py``` containing a sequencing statistics summary table and both violin plot and scatter plot visualizations of data output, read N50, and starting active pores (active pores after starting sequencing). It also can take a platform QC flow cell check table generated with MinKNOW API helper scripts on an ONT sequencer itself as described [here](https://github.com/molleraj/CARDlongread_MinKNOW_api_scripts) to calculate statistics for platform QC active pores and pore changes per flow cell from platform QC flow cell checks to the start of sequencing. Recent updates incorporate evaluation of active pores per flow cell at the time of initial checks (platform QC) as well, further calculating differences in active pore count between platform QC and the start of sequencing, and visualizing relationships between these differences and run data output. Violin plots are provided separately for output (Gbp) per run (corresponding to each line in the input TSV table), per flow cell, and per experiment. Individual runs (lines in TSV table) are highlighted indicating whether they are an initial run, top up, reconnection, or recovery.

Sequencing runs are typically conducted over 72 hours, with one 20 fmol library load every 24 hours.

A **standard run** corresponds to a sequencing run that went through three full loads successfully (one every 24 hours), while **interrupted** refers to the first part of a full sequencing run where the flow cell was later reconnected at a distinct position (e.g., 1E to 3C) or temporarily disconnected and reconnected at the same position (e.g., 1E). These run types were both designated as initial runs in past versions of the dashboard.

A **reconnection** is the second part of a run after a flow cell is disconnected and reconnected, as described above. Reconnections are identified from lines in the JSON parser output TSV that have the same sample name and same flow cell ID.

A **recovery** run is conducted when either insufficient library is prepared for three full loads (over three days) or when active pores substantially decrease from pre-sequencing checks after the first load. Library is recovered by slow aspiration from the flow cell sample port itself. Library is generally recovered after the first load (often due to active pore drop off) and either loaded onto a new flow cell or to the same flow cell for a subsequent load. 

A **top up** run is conducted on a new flow cell when an experiment has not yielded the desired 90 Gbp (30x coverage) from the initial run (and reconnections/recoveries where applicable). Top up runs are conducted either with initial library if there is sufficient library for more than three loads or with new library if not.

Top up runs are labeled with the suffix _topup and recovery runs are labeled with the suffix _recovery in the sample name column.

Example data visualizations corresponding to data snippets shown earlier:
<br></br>
Total per flow cell output violin plot with embedded box plot, displayed data points, and 30x/90Gbp cutoff line:
<br></br>
<img width="720" alt="image" src="https://github.com/user-attachments/assets/3ff9c40a-c584-4c3f-9476-b945cee64e23" />
<br></br>
<!-- img width="720" alt="image" src="https://github.com/user-attachments/assets/f576c444-65c7-4c66-9a1a-a6a7ebdfa6e4" -->
Per run data output vs. starting active pore scatter plot with run type annotated by color and cutoffs provided for starting active pores (red - less than 5000 pores for ONT warranty return, green - 6500 pores or higher for internal QC) and data output (gray - desired 30X human genome coverage or 90 Gbp sequencing output).
<br></br>
<img width="720" alt="image" src="https://github.com/user-attachments/assets/dd234caf-b772-4d4f-9944-7b51fab96f5f" />
<!-- img width="720" alt="image" src="https://github.com/user-attachments/assets/5e4c3038-d747-4373-b59d-dde6db8dabf3" -->
<br></br>
Example usage (```python CARDlongread_extract_summary_statistics.py -h```):

```
usage: CARDlongread_extract_summary_statistics.py [-h] [-input INPUT_FILE [INPUT_FILE ...]] [-names [NAMES ...]] [-output OUTPUT_FILE] [-platform_qc PLATFORM_QC] [-plot_title PLOT_TITLE] [--plot_cutoff | --no-plot_cutoff]
                                                  [-run_cutoff RUN_CUTOFF] [--strip_plot | --no-strip_plot] [-colors [COLORS ...]] [-legend_colors [LEGEND_COLORS ...]] [-legend_labels [LEGEND_LABELS ...]] [--group_count | --no-group_count]
                                                  [-output_table_with_platform_qc OUTPUT_TABLE_WITH_PLATFORM_QC] [-output_table_with_run_type OUTPUT_TABLE_WITH_RUN_TYPE]

This program gets summary statistics from long read sequencing report data.

optional arguments:
  -h, --help            show this help message and exit
  -input INPUT_FILE [INPUT_FILE ...]
                        Input tab-delimited tsv file(s) containing features extracted from long read sequencing reports.
  -names [NAMES ...]    Names corresponding to input tsv file(s); required if more than one tsv provided.
  -output OUTPUT_FILE   Output long read sequencing summary statistics XLSX
  -platform_qc PLATFORM_QC
                        Input platform QC table to calculate active pore dropoff upon sequencing (optional)
  -plot_title PLOT_TITLE
                        Title for each plot in output XLSX (optional)
  --plot_cutoff, --no-plot_cutoff
                        Include cutoff lines in violin plots (optional; default true; --no-plot_cutoff to override) (default: True)
  -run_cutoff RUN_CUTOFF
                        Minimum data output per flow cell run to include (optional, 1 Gb default)
  --strip_plot, --no-strip_plot
                        Show strip plots instead of swarm plots inside violin plots (optional; default false) (default: False)
  -colors [COLORS ...]  Color palette corresponding to sequential groups displayed (e.g., 'blue', 'red', 'blue'); optional and used only if more than one tsv provided.
  -legend_colors [LEGEND_COLORS ...]
                        Colors shown in the legend (e.g., 'blue', 'red'); optional and used only if more color palette included above. Must be palette subset.
  -legend_labels [LEGEND_LABELS ...]
                        Labels for each color in legend in order specified in -legend_colors.
  --group_count, --no-group_count
                        Show group count in x-axis labels (optional; default false) (default: False)
  -output_table_with_platform_qc OUTPUT_TABLE_WITH_PLATFORM_QC
                        Output filename for run report summary table joined with platform QC flow cell check information (optional).
  -output_table_with_run_type OUTPUT_TABLE_WITH_RUN_TYPE
                        Output filename for run report summary table with appended run type, such as 'top up' or 'reconnection' (optional).
```
## Tutorial

To clone from GitHub and do a test run:
```bash
# Download this repo
git clone https://github.com/molleraj/CARDlongread-report-parser.git
cd CARDlongread-report-parser

# Test on pregenerated set of 50 random PPMI JSON files (use exact file provided)
# Random JSON file set generated like so with Linux coreutils shuf (shuffle) command
# shuf -n 50 full_PPMI_json_report_list_090524.txt > random_50_test_PPMI_json_paths_090524.txt
# random_50_test_PPMI_json_paths_090524.txt included in repository as example_json_reports.txt

# Execute with file list of json reports (one per line):
python3 CARDlongread_extract_from_json.py --filelist example_json_reports.txt --output example_output.tsv

# Alternatively, execute on all json files within a directory
# (does not descend into subdirectories)
python3 CARDlongread_extract_from_json.py --json_dir /data/CARDPB/data/PPMI/SEQ_REPORTS/example_json_reports/ --output example_output.tsv

# Make sequencing QC analytics spreadsheet from above QC output table (example_output.tsv)
python3 CARDlongread_extract_summary_statistics.py -input example_output.tsv -output example_summary_spreadsheet.xlsx -platform_qc example_platform_qc.csv -plot_title "PPMI tutorial example" -output_table_with_platform_qc example_output_with_platform_qc.tsv -output_table_with_run_type example_output_with_run_type.tsv
```

Example sequencing QC visualizations from tutorial summary spreadsheet:
<br></br>
Per run output violin plot with embedded box plot and displayed data points, plus run type annotated by point color and red cutoff line for desired 30x coverage/90 Gbp output:
<br></br>
<img width="720" alt="image" src="https://github.com/user-attachments/assets/5fccccb4-71ca-484b-904f-414fccf2e12b">
<br></br>
Per run starting active pores violin plot with embedded box plot and displayed data points, plus run type annotated by point color and red cutoff line for recommended minimum 6500 starting active pores:
<br></br>
<img width="720" alt="image" src="https://github.com/user-attachments/assets/67643dc9-5011-4b8d-ba54-d5551eb774eb">
<br></br>
Per run data output vs. starting active pore scatter plot with run type annotated by point color and cutoffs provided for starting active pores (red - less than 5000 active pores for ONT warranty return, green - 6500 active pores or higher for internal QC) and data output (gray - desired output of 30X human genome coverage or 90 Gbp sequencing output).
<br></br>
<img width="720" alt="image" src="https://github.com/user-attachments/assets/6cf2041b-429f-45ed-b759-658480fdc943">
<br></br>
Per run data output vs. difference between starting active pores (after sequencing) and platform QC active pores at the initial flow cell check with run type annotated by point color and cutoff provided for data output (gray - desired output of 30X human genome coverage or 90 Gbp sequencing output).
<br></br>
<img width="642" alt="image" src="https://github.com/user-attachments/assets/2eb5196d-7cf0-4abb-86b9-760a457362a4" />
<br></br>
Per run data output vs. date sequencing run was conducted with run type annotated by point color and cutoff provided for data output (gray - desired output of 30X human genome coverage or 90 Gbp sequencing output).
<br></br>
<img width="642" alt="image" src="https://github.com/user-attachments/assets/1378ce87-5f45-45a8-8de3-325935a3ad96" />
<br></br>

## Comparing QC metrics across groups

Having sequenced more than five cohorts and often over 10 samples each week, we found it often advantageous to compare raw QC metrics across different arbitrarily defined groups. We thus implemented group comparison functionality available through the ```-input [INPUT_FILE ...]```, ```-names [NAMES ...]```, and/or ```-colors [COLORS ...]``` command line options. These options take a list of files along with corresponding names and colors to be applied to each input file, in the order given for the ```-input``` option. We have provided an additional tutorial below demonstrating group comparison with custom coloring and labeling for 20 sequencing runs randomly selected from each of five different cohorts. Cohorts are colored and labeled based on sample type (blood in red, brain in blue, colors from tableau palette). Cohorts are set in order to corresponding brain/blood colors with ```-colors```, while the legend is set to blood/brain and red/blue with ```-legend_colors``` and ```-legend_labels```, respectively. We also provide a command to generate a companion dashboard based on the same cohorts with default coloring. Paths provided in JSON lists are paths to corresponding JSONs on the NIH Biowulf HPC cluster. Input and output files for the group comparison tutorial are provided in the provided ```group_comparison``` folder.

```bash
# run in CARDlongread-report-parser directory
cd CARDlongread-report-parser

# prepare input tables for each cohort
# cohort json lists include 20 randomly selected JSONs per cohort
# cohort 1
python CARDlongread_extract_from_json.py --filelist group_comparison/cohort_1_json_list.txt --output group_comparison/cohort_1_output.tsv
# cohort 2
python CARDlongread_extract_from_json.py --filelist group_comparison/cohort_2_json_list.txt --output group_comparison/cohort_2_output.tsv
# cohort 3
python CARDlongread_extract_from_json.py --filelist group_comparison/cohort_3_json_list.txt --output group_comparison/cohort_3_output.tsv
# cohort 4
python CARDlongread_extract_from_json.py --filelist group_comparison/cohort_4_json_list.txt --output group_comparison/cohort_4_output.tsv
# cohort 5
python CARDlongread_extract_from_json.py --filelist group_comparison/cohort_5_json_list.txt --output group_comparison/cohort_5_output.tsv

# make dashboard for all five cohorts, coloring cohorts by sample type (blood or brain)
# overlay violinplots with strip plots instead of beeswarm plots
python CARDlongread_extract_summary_statistics.py \
  -input group_comparison/cohort_1_output.tsv group_comparison/cohort_2_output.tsv group_comparison/cohort_3_output.tsv group_comparison/cohort_4_output.tsv group_comparison/cohort_5_output.tsv \
  -names "Cohort 1" "Cohort 2" "Cohort 3" "Cohort 4" "Cohort 5" \
  -colors "tab:blue" "tab:red" "tab:blue" "tab:blue" "tab:blue" \
  -legend_colors "tab:red" "tab:blue" \
  -legend_labels "Blood" "Brain" \
  -plot_title "Group comparison tutorial with custom colors and legend" \
  -output group_comparison/five_cohort_sample_comparison_dashboard_custom_colors.xlsx \
  -platform_qc group_comparison/group_comparison_platform_qc.csv \
  --strip_plot

# make dashboard as above, but don't use custom color/labeling options
# instead use 'top up' colors for runs and seaborn defaults for output per flow cell/per experiment
python CARDlongread_extract_summary_statistics.py \
  -input group_comparison/cohort_1_output.tsv group_comparison/cohort_2_output.tsv group_comparison/cohort_3_output.tsv group_comparison/cohort_4_output.tsv group_comparison/cohort_5_output.tsv \
  -names "Cohort 1" "Cohort 2" "Cohort 3" "Cohort 4" "Cohort 5" \
  -plot_title "Group comparison tutorial with default output" \
  -output group_comparison/five_cohort_sample_comparison_dashboard_default_colors.xlsx \
  -platform_qc group_comparison/group_comparison_platform_qc.csv \
  --strip_plot
```

Below are example grouped violinplots from the dashboard that colors blood sample cohorts red and brain sample cohorts blue:

<img width="720" alt="image" src="https://github.com/user-attachments/assets/00886cae-e602-4eeb-8013-48ad5cf555d0" />
<img width="720" alt="image" src="https://github.com/user-attachments/assets/e25df7eb-ac5c-4cea-8f4d-18201a480663" />

And below are corresponding grouped violinplots (read N50, run data output) from the default color dashboard:

<img width="720" alt="image" src="https://github.com/user-attachments/assets/d815e558-e47e-4184-8d88-cb0275ac20c4" />
<img width="720" alt="image" src="https://github.com/user-attachments/assets/9c82fb88-f213-4ceb-855b-6f8313aa954c" />

The two grouped violinplots shown below compare custom coloring with default coloring for data output per sample:

<img width="720" alt="image" src="https://github.com/user-attachments/assets/34bc26e0-cc7c-431a-84f6-669421125f46" />
<img width="720" alt="image" src="https://github.com/user-attachments/assets/60f97ecb-c11d-4ca0-acf4-bab1c7d8743a" />

Both custom and default point coloring override top up based point coloring in provided scatterplots:

<img width="642" alt="image" src="https://github.com/user-attachments/assets/ca1e5ca4-2a89-4fa4-b1c4-d51e77a36e08" />
<img width="642" alt="image" src="https://github.com/user-attachments/assets/de5106b4-9b23-44fd-a1fc-633ee5c060f8" />


