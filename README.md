# NIA CARD Long Read Sequencing Report Parsing and Visualization Dashboard

The NIA CARD Long-Read Sequencing group sequences some 30-50 human genomes per week from brain and blood genomic DNA. Given these samples both often belong to larger cohorts (more than 30-50 samples), batch to batch variation is inevitable, and Oxford Nanopore Technologies has steadily modified sequencing library chemistry, flow cells, instrument software, and basecalling models, regular sequencing quality control is critical to examine how our sequencing efforts change over time. The included Python scripts automate the process of collecting key sequencing statistics from weekly and cohort-wide sequencing runs and generate QC analytics as an Excel spreadsheet. They take run output JSON files as input and pull sequencing statistics from exact locations in each JSON hierarchical data structure. The scripts have been written to handle JSON files from MinKNOW version 24.02.19 and earlier. Recent updates make it possible to incorporate platform QC flow cell checks from before sequencing into the QC visualization dashboard as well. Please report any bugs in the Issues tab to further improve the parser.

## Dependencies

The Python scripts were tested and developed with the following dependency modules (and respective versions where applicable):  

Python 3.10.8  
numpy 1.26.4  
pandas 2.0.3  
seaborn 0.12.2  
matplotlib 3.7.2  
json 2.0.9  
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

```CARDlongread_extract_from_json.py``` takes a list of Oxford Nanopore sequencing report JSON files as inputs (or a directory containing all JSON files to analyze) and returns a table with the following fields per JSON:

Experiment Name, Sample Name, Run Date, PROM ID, Flow Cell Position, Flow Cell ID, Data output (Gb), N50 (kb), MinKNOW Version, Passed Modal Q Score, Failed Modal Q Score, Starting Active Pores, Second Pore Count, Start Run ISO Timestamp, Start Run Timestamp

Below is sample output from the script:
```
Experiment Name	Sample Name	Run Date	PROM ID	Flow Cell Position	Flow Cell ID	Data output (Gb)	N50 (kb)	MinKNOW Version	Passed Modal Q Score	Failed Modal Q ScoreStarting Active Pores	Second Pore Count	Start Run ISO Timestamp	Start Run Timestamp
Chile_404	Chile_404	2024-05-14	PC24B302	2D	PAW33034	141.083	23.39	24.02.10	NA	NA	7644	7295	2024-05-14T21:23:35.883780864Z	1715721816
Chile_406	Chile_406	2024-05-01	PC24B302	2E	PAW73369	131.699	22.79	24.02.10	NA	NA	7431	7118	2024-05-01T19:49:27.062103580Z	1714592967
Chile_509	Chile_509	2024-05-14	PC24B302	2F	PAW61512	117.861	17.12	24.02.10	NA	NA	7604	7028	2024-05-14T21:28:27.860263815Z	1715722108
Chile_511	Chile_511	2024-05-08	PC24B302	2D	PAW71368	133.097	20.69	24.02.10	NA	NA	7370	6972	2024-05-08T20:46:57.642743302Z	1715201218
Chile_516	Chile_516	2024-05-01	PC24B302	2D	PAW71977	129.544	23.63	24.02.10	NA	NA	7837	7424	2024-05-01T19:47:57.769730497Z	1714592878
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

```CARDlongread_extract_summary_statistics.py``` then generates an sequencing QC analytics spreadsheet from the output table of ```CARDlongread_extract_from_json.py``` containing a sequencing statistics summary table and both violin plot and scatter plot visualizations of data output, read N50, and starting active pores (active pores after starting sequencing). Recent updates incorporate evaluation of active pores per flow cell at the time of initial checks (platform QC) as well, further calculating differences in active pore count between platform QC and the start of sequencing, and visualizing relationships between these differences and run data output. Violin plots are provided separately for output (Gbp) per run (corresponding to each line in the input TSV table), per flow cell, and per experiment. Individual runs (lines in TSV table) are highlighted indicating whether they are an initial run, top up, reconnection, or recovery.

Sequencing runs are typically conducted over 72 hours, with one 20 fmol library load every 24 hours.

An initial run corresponds either to a sequencing run that went through three full loads successfully (one every 24 hours) or to the first part of a full sequencing run where the flow cell was later reconnected at a distinct position (e.g., 1E to 3C) or temporarily disconnected and reconnected at the same position (e.g., 1E).

A reconnection is the second part of a run after a flow cell is disconnected and reconnected, as described above. Reconnections are identified from lines in the JSON parser output TSV that have the same sample name and same flow cell ID.

A recovery run is conducted when either insufficient library is prepared for three full loads (over three days) or when active pores substantially decrease from pre-sequencing checks after the first load. Library is recovered by slow aspiration from the flow cell sample port itself. Library is generally recovered after the first load (often due to active pore drop off) and either loaded onto a new flow cell or to the same flow cell for a subsequent load. 

A top up run is conducted on a new flow cell when an experiment has not yielded the desired 90 Gbp (30x coverage) from the initial run (and reconnections/recoveries where applicable). Top up runs are conducted either with initial library if there is sufficient library for more than three loads or with new library if not.

Top up runs are labeled with the suffix _topup and recovery runs are labeled with the suffix _recovery in the sample name column.

Example data visualizations corresponding to data snippets shown earlier:
<br></br>
Total per flow cell output violin plot with embedded box plot and displayed data points:
<br></br>
<img width="720" alt="image" src="https://github.com/user-attachments/assets/f576c444-65c7-4c66-9a1a-a6a7ebdfa6e4">
<br></br> 
Per run data output vs. starting active pore scatter plot with run type annotated by color and cutoffs provided for starting active pores (red - less than 5000 pores for ONT warranty return, green - 6500 pores or higher for internal QC) and data output (gray - desired 30X human genome coverage or 90 Gbp sequencing output).
<br></br>
<img width="720" alt="image" src="https://github.com/user-attachments/assets/5e4c3038-d747-4373-b59d-dde6db8dabf3">
<br></br>
Example usage (```python CARDlongread_extract_summary_statistics.py -h```):

```
usage: CARDlongread_extract_summary_statistics.py [-h] [-input INPUT_FILE] [-output OUTPUT_FILE] [-platform_qc PLATFORM_QC] [-plot_title PLOT_TITLE]
                                                  [--plot_cutoff | --no-plot_cutoff] [-run_cutoff RUN_CUTOFF]

This program gets summary statistics from long read sequencing report data.

optional arguments:
  -h, --help            show this help message and exit
  -input INPUT_FILE     Input tab-delimited tsv file containing features extracted from long read sequencing reports.
  -output OUTPUT_FILE   Output long read sequencing summary statistics XLSX
  -platform_qc PLATFORM_QC
                        Input platform QC table to calculate active pore dropoff upon sequencing (optional)
  -plot_title PLOT_TITLE
                        Title for each plot in output XLSX (optional)
  --plot_cutoff, --no-plot_cutoff
                        Include cutoff lines in violin plots (optional; default true; --no-plot_cutoff to override) (default: True)
  -run_cutoff RUN_CUTOFF
                        Minimum data output per flow cell run to include (optional, 1 Gb default)
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
python3 CARDlongread_extract_summary_statistics.py -input example_output.tsv -output example_summary_spreadsheet.xlsx -platform_qc example_platform_qc.csv -plot_title "PPMI tutorial example"
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

