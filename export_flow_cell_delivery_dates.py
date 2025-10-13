# script to convert delivery date spreadsheet from ONT into single table in TSV format
import pandas as pd
import numpy as np
import argparse
from datetime import datetime

# subroutine to parse command line arguments
def parse_args():
    parser = argparse.ArgumentParser(description="Convert ONT ship date/sales info/QC spreadsheet into delivery date table ready for incorporation into the MinKNOW run report dashboard.")
    # argument for input ONT ship date/QC spreadsheet
    parser.add_argument("--input_ont_spreadsheet", required=True, help="Input ONT ship date/sales info/QC spreadsheet in xlsx format (required).")
    # argument for output table
    parser.add_argument("--output_delivery_table", required=True, help="Output file name for delivery date table in TSV format with batch info and timestamps included for dashboard import.")
    # return parsed arguments
    return parser.parse_args()

# main script subroutine
def main():
    # Parse the arguments
    args = parse_args()
    # import ONT spreadsheet
    input_ONT_spreadsheet=pd.ExcelFile(args.input_ont_spreadsheet)
    # get sheet names
    sheets_of_interest = input_ONT_spreadsheet.sheet_names
    # drop FC Utilization Calc
    sheets_of_interest.remove('FC Utilization Calc')
    # get data frames to pull and stitch together
    input_ONT_spreadsheet_dfs={sheet_name: input_ONT_spreadsheet.parse(sheet_name) for sheet_name in sheets_of_interest}
    # initialize delivery date/batch data frame
    delivery_date_batch_df=pd.DataFrame()
    # fill it in with Flowcell ID, Batch (aka TPL Batch), and Shipped date columns from each sheet of interest
    for sheet_name in sheets_of_interest:
        # rename TPL Batch to Batch if necessary
        if 'TPL Batch' in input_ONT_spreadsheet_dfs[sheet_name].columns:
            input_ONT_spreadsheet_dfs[sheet_name]['Batch'] = input_ONT_spreadsheet_dfs[sheet_name]['TPL Batch']
        # get fields of interest from current sheet to incorporate into delivery date/batch data frame
        current_sheet_fields_of_interest=input_ONT_spreadsheet_dfs[sheet_name][['Flowcell ID','Batch','Shipped date']].dropna()
        delivery_date_batch_df=pd.concat([delivery_date_batch_df, current_sheet_fields_of_interest], ignore_index=True)
    # rename Flowcell ID column to Flow Cell ID
    delivery_date_batch_df = delivery_date_batch_df.rename(columns={'Flowcell ID':'Flow Cell ID'})
    # get unique rows
    delivery_date_batch_df=delivery_date_batch_df.drop_duplicates()
    # calculate delivery date by adding one to shipped date
    delivery_date_batch_df['Delivery date']=delivery_date_batch_df['Shipped date']+pd.Timedelta(days=1)
    # make delivery date timestamps for dashboard calculation
    # Unix/Linux epoch time
    delivery_date_batch_df['Delivery date timestamp']=[datetime.timestamp(x) for x in delivery_date_batch_df['Delivery date']]
    # ISO 8601 time
    delivery_date_batch_df['Delivery date timestamp (ISO)']=[datetime.isoformat(x) for x in delivery_date_batch_df['Delivery date']]
    # output final table as TSV
    delivery_date_batch_df.to_csv(args.output_delivery_table,index=False,sep="\t")
    
# run main subroutine
if __name__ == "__main__":
    main()