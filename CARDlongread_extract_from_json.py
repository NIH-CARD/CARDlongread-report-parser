#!/usr/bin/env python3
# long read sequencing report JSON parser
# output fields are Experiment Name, Sample Name, Run Date, PROM ID, Flow Cell Position, Flow Cell ID, Flow Cell Product Code, Data output (Gb), Read Count (M), N50 (kb), MinKNOW Version, Sample Rate (Hz), Passed Modal Q Score, Failed Modal Q Score, Starting Active Pores, Second Pore Count, Start Run ISO Timestamp, Start Run Timestamp
# look for Q score in the future and possibly also total reads
import glob
# import json
# try importing jsons with orjson instead for rusty speed boost
import orjson
import pandas as pd
import numpy as np
import argparse
import dataclasses
from dateutil.parser import isoparse
# get fields from json
def get_fields_from_json(input_json_dict):
    # define fields_from_json class
    @dataclasses.dataclass
    class fields_from_json:
        experiment_name : ''
        sample_name : ''
        run_date : ''
        prom_id : ''
        flow_cell_id : ''
        flow_cell_product_code : ''
        flow_cell_position : ''
        minknow_version : ''
        iso_timestamp : ''
        data_output : float = 0
        read_count : float = 0
        n50 : float = 0
        modal_q_score_passed : float = 0
        modal_q_score_failed : float = 0
        starting_active_pores : float = 0
        second_active_pore_count : float = 0
        timestamp : float = 0
        sample_rate : float = 0
        # new fields added 10/7/2025
        average_active_pores : float = 0
        active_pore_auc : float = 0
        average_active_pore_change_rate : float = 0
        starting_pore_occupancy : float = 0 # percentage occupancy
        average_pore_occupancy : float = 0 # percentage occupancy
        starting_adapter_sequencing_percentage : float = 0
        average_adapter_sequencing_percentage : float = 0
        # below fields require basecalling to have been turned on during sequencing
        starting_median_translocation_speed : float = 0
        starting_median_q_score : float = 0
        average_median_translocation_speed_over_time : float = 0
        average_median_q_score_over_time : float = 0
        weighted_average_median_translocation_speed_over_time : float = 0
        weighted_average_median_q_score_over_time : float = 0
        # additional pass/fail characteristics
        passed_reads : float = 0
        failed_reads : float = 0
        passed_bases : float = 0
        failed_bases : float = 0
        percentage_reads_passed : float = 0
        percentage_bases_passed : float = 0
    # get elements from json-based dictionary
    fields_from_json.experiment_name = input_json_dict['protocol_run_info']['user_info']['protocol_group_id']
    fields_from_json.sample_name = input_json_dict['protocol_run_info']['user_info']['sample_id']
    fields_from_json.run_date = input_json_dict['protocol_run_info']['start_time'][0:10]
    fields_from_json.prom_id = input_json_dict['host']['serial']
    # get flow cell id either acquired from flow cell or user inputted
    if 'flow_cell_id' in input_json_dict['protocol_run_info']['flow_cell']:
        fields_from_json.flow_cell_id = input_json_dict['protocol_run_info']['flow_cell']['flow_cell_id']
    else:
        if 'user_specified_flow_cell_id' in input_json_dict['protocol_run_info']['flow_cell']:
            fields_from_json.flow_cell_id = input_json_dict['protocol_run_info']['flow_cell']['user_specified_flow_cell_id']
        else:
            fields_from_json.flow_cell_id = 'NA'
    # get flow cell product code acquired from flow cell or user inputted
    if 'product_code' in input_json_dict['protocol_run_info']['flow_cell']:
        fields_from_json.flow_cell_product_code = input_json_dict['protocol_run_info']['flow_cell']['product_code']
    else:
        if 'user_specified_product_code' in input_json_dict['protocol_run_info']['flow_cell']:
            fields_from_json.flow_cell_product_code = input_json_dict['protocol_run_info']['flow_cell']['user_specified_product_code']
        else:
            fields_from_json.flow_cell_product_code = 'NA'
    # get flow cell position
    fields_from_json.flow_cell_position = input_json_dict['protocol_run_info']['device']['device_id']
    # get timestamp of run start in ISO 8601 format
    fields_from_json.iso_timestamp = input_json_dict['acquisitions'][3]['acquisition_run_info']['data_read_start_time']
    # convert timestamp for data_read_start_time (corresponds to starting active pores) from ISO 8601 to Unix timestamp format
    fields_from_json.timestamp = round(isoparse(input_json_dict['acquisitions'][3]['acquisition_run_info']['data_read_start_time']).timestamp())
    # be sure to handle exception of no data output
    # convert data output from bases to Gb with three decimal places
    # use total estimated bases as output
    if 'estimated_selected_bases' in input_json_dict['acquisitions'][3]['acquisition_run_info']['yield_summary']:
        fields_from_json.data_output = round(pd.to_numeric(input_json_dict['acquisitions'][3]['acquisition_run_info']['yield_summary']['estimated_selected_bases'])/1e9, 3)
    else:
        # changed from 0 to NA
        fields_from_json.data_output = 'NA'
    # get total read count from json dictionary
    if 'read_count' in input_json_dict['acquisitions'][3]['acquisition_run_info']['yield_summary']:
        fields_from_json.read_count = round(pd.to_numeric(input_json_dict['acquisitions'][3]['acquisition_run_info']['yield_summary']['read_count'])/1e6, 3)
    else:
        # changed from 0 to NA
        fields_from_json.read_count = 'NA'
    # get sample rate from fourth element of acquisitions array, acquisition_run_info, config_summary
    if 'sample_rate' in input_json_dict['acquisitions'][3]['acquisition_run_info']['config_summary']:
        fields_from_json.sample_rate = input_json_dict['acquisitions'][3]['acquisition_run_info']['config_summary']['sample_rate']
    else:
        # changed from 0 to NA
        fields_from_json.sample_rate = 'NA'
    # get n50 in kb to two decimal places for estimated bases, not basecalled bases
    # add conditional for MinKNOW 24.11.11 (acquisitions[1] instead of acquisitions[3] )
    # probably can just test on software version in future...
    # For MinKNOW versions <24.11.11
    # first check if JSON dict has enough read length histogram entries
    if len(input_json_dict['acquisitions'][3]['read_length_histogram'])>=4:
        read_length_histogram=input_json_dict['acquisitions'][3]['read_length_histogram'][3]
    else:
        read_length_histogram=input_json_dict['acquisitions'][3]['read_length_histogram'][1]
    # first check that critical keys exist
    MinKNOW_before_241111_N50_depth_test=('read_length_type' in read_length_histogram) and ('bucket_value_type' in read_length_histogram) # and ('n50' in read_length_histogram['plot']['histogram_data'][0])
    # test for existence
    if MinKNOW_before_241111_N50_depth_test is True:
        # if they exist, make sure critical keys have expected content (Estimated Bases, Read Lengths)
        MinKNOW_before_241111_N50_content_test=(read_length_histogram['read_length_type'] == "EstimatedBases") and (read_length_histogram['bucket_value_type'] == "ReadLengths") and ('n50' in read_length_histogram['plot']['histogram_data'][0])
        # test content
        if MinKNOW_before_241111_N50_content_test is True:
            fields_from_json.n50 = round(pd.to_numeric(read_length_histogram['plot']['histogram_data'][0]['n50'])/1e3, 2)
        else:
            # changed from 0 to NA
            fields_from_json.n50 = 'NA'
    # For MinKNOW versions >24.11.11
    else: 
        read_length_histogram=input_json_dict['acquisitions'][3]['read_length_histogram'][1]
        MinKNOW_241111_after_N50_content_test=(read_length_histogram['read_length_type'] == "EstimatedBases") and (read_length_histogram['bucket_value_type'] == "ReadLengths") and ('n50' in read_length_histogram['plot']['histogram_data'][0])
        if MinKNOW_241111_after_N50_content_test is True:
            fields_from_json.n50 = round(pd.to_numeric(read_length_histogram['plot']['histogram_data'][0]['n50'])/1e3, 2)
        # if not found altogether
        else:
            # changed from 0 to NA
            fields_from_json.n50 = 'NA'
    # need to branch here because minknow version is in different locations depending on json version type
    if 'software_versions' not in input_json_dict:
        # new software_versions path in 2024
        fields_from_json.minknow_version = input_json_dict['protocol_run_info']['software_versions']['distribution_version']
    else:
        # old software_versions path in 2023
        fields_from_json.minknow_version = input_json_dict['software_versions']['distribution_version']
    # base n50 value on software version
    # get modal q score for passed and failed reads if found in json file
    if 'qscore_histograms' in input_json_dict['acquisitions'][3]:
        # test if passed reads present as element
        if len(input_json_dict['acquisitions'][3]['qscore_histograms'][0]['histogram_data']) >= 1:
            # test if passed reads present as element but no reads actually passed
            if 'modal_q_score' in input_json_dict['acquisitions'][3]['qscore_histograms'][0]['histogram_data'][0]:
                fields_from_json.modal_q_score_passed = input_json_dict['acquisitions'][3]['qscore_histograms'][0]['histogram_data'][0]['modal_q_score']
            else:
                fields_from_json.modal_q_score_passed = 'NA'
        else:
            fields_from_json.modal_q_score_passed = 'NA'
        # test if failed reads present
        if len(input_json_dict['acquisitions'][3]['qscore_histograms'][0]['histogram_data']) >= 2:
            # test if failed reads present as element but no reads actually failed
            if 'modal_q_score' in input_json_dict['acquisitions'][3]['qscore_histograms'][0]['histogram_data'][1]:
                fields_from_json.modal_q_score_failed = input_json_dict['acquisitions'][3]['qscore_histograms'][0]['histogram_data'][1]['modal_q_score']
            else:
                fields_from_json.modal_q_score_failed = 'NA'
        else:
            fields_from_json.modal_q_score_failed = 'NA'
    else:
        fields_from_json.modal_q_score_passed = 'NA'
        fields_from_json.modal_q_score_failed = 'NA'
    # get pass and fail read statistics
    if 'yield_summary' in input_json_dict['acquisitions'][3]['acquisition_run_info']:
        # get pass vs. fail for final data point (last_capture_index)
        # last_capture_index=len(input_json_dict['acquisitions'][3]['acquisition_output'][0]['plot'][0]['snapshots'][0]['snapshots'])-1
        # get passed/failed read counts, total bases, and fraction read counts or bases passing
        # convert read count to millions
        # passed_reads = round(pd.to_numeric(input_json_dict['acquisitions'][3]['acquisition_output'][0]['plot'][0]['snapshots'][0]['snapshots'][last_capture_index]['yield_summary']['basecalled_pass_read_count'])/1e6,3)
        if 'basecalled_pass_read_count' in input_json_dict['acquisitions'][3]['acquisition_run_info']['yield_summary']:
            fields_from_json.passed_reads = round(pd.to_numeric(input_json_dict['acquisitions'][3]['acquisition_run_info']['yield_summary']['basecalled_pass_read_count'])/1e6,3)
        else:
            fields_from_json.passed_reads = 'NA'
        # failed_reads = round(pd.to_numeric(input_json_dict['acquisitions'][3]['acquisition_output'][0]['plot'][0]['snapshots'][0]['snapshots'][last_capture_index]['yield_summary']['basecalled_fail_read_count'])/1e6,3)
        if 'basecalled_fail_read_count' in input_json_dict['acquisitions'][3]['acquisition_run_info']['yield_summary']:
            fields_from_json.failed_reads = round(pd.to_numeric(input_json_dict['acquisitions'][3]['acquisition_run_info']['yield_summary']['basecalled_fail_read_count'])/1e6,3)
        else:
            fields_from_json.failed_reads = 'NA'
        # convert base total to Gbp
        # passed_bases = round(pd.to_numeric(input_json_dict['acquisitions'][3]['acquisition_output'][0]['plot'][0]['snapshots'][0]['snapshots'][last_capture_index]['yield_summary']['basecalled_pass_bases'])/1e9,3)
        if 'basecalled_pass_bases' in input_json_dict['acquisitions'][3]['acquisition_run_info']['yield_summary']:
            fields_from_json.passed_bases = round(pd.to_numeric(input_json_dict['acquisitions'][3]['acquisition_run_info']['yield_summary']['basecalled_pass_bases'])/1e9,3)
        else:
            fields_from_json.passed_bases = 'NA'
        # failed_bases = round(pd.to_numeric(input_json_dict['acquisitions'][3]['acquisition_output'][0]['plot'][0]['snapshots'][0]['snapshots'][last_capture_index]['yield_summary']['basecalled_fail_bases'])/1e9,3)
        if 'basecalled_fail_bases' in input_json_dict['acquisitions'][3]['acquisition_run_info']['yield_summary']:
            fields_from_json.failed_bases = round(pd.to_numeric(input_json_dict['acquisitions'][3]['acquisition_run_info']['yield_summary']['basecalled_fail_bases'])/1e9,3)
        else:
            fields_from_json.failed_bases = 'NA'
        # calculate percentage of reads passing
        if ((fields_from_json.passed_reads != 'NA') and (fields_from_json.failed_reads != 'NA')):
            fields_from_json.percentage_reads_passed=round(100*(fields_from_json.passed_reads/(fields_from_json.passed_reads+fields_from_json.failed_reads)),3) if (fields_from_json.passed_reads+fields_from_json.failed_reads) else 0
        else:
            fields_from_json.percentage_reads_passed = 'NA'
        # calculate percentage of bases passing
        if ((fields_from_json.passed_bases != 'NA') and (fields_from_json.failed_bases != 'NA')):
            fields_from_json.percentage_bases_passed=round(100*(fields_from_json.passed_bases/(fields_from_json.passed_bases+fields_from_json.failed_bases)),3) if (fields_from_json.passed_bases+fields_from_json.failed_bases) else 0
        else:
            fields_from_json.percentage_bases_passed = 'NA'
    else:
        fields_from_json.passed_reads = 'NA'
        fields_from_json.failed_reads = 'NA'
        fields_from_json.passed_bases = 'NA'
        fields_from_json.failed_bases = 'NA'
        fields_from_json.percentage_reads_passed = 'NA'
        fields_from_json.percentage_bases_passed = 'NA'
    # get translocation speed and q score over time statistics
    # note to check if input_json_dict['acquisitions'][3]['basecall_boxplot'][0]['plot']['datasets'] has any entries (none seen in PPMI test case)
    if (('basecall_boxplot' in input_json_dict['acquisitions'][3]) and ('datasets' in input_json_dict['acquisitions'][3]['basecall_boxplot'][0]['plot']) and (len(input_json_dict['acquisitions'][3]['basecall_boxplot'][0]['plot']['datasets']) > 0)):
        # get number of time points recorded; use Q score data
        total_time_points=len(input_json_dict['acquisitions'][3]['basecall_boxplot'][0]['plot']['datasets'])
        # initialize empty lists for speeds, q scores, and read counts
        median_translocation_speeds=[0] * total_time_points
        median_q_scores=[0] * total_time_points
        median_corresponding_counts=[0] * total_time_points
        # initialize empty lists for speeds and q scores weighted by read counts
        weighted_median_translocation_speeds=[0] * total_time_points
        weighted_median_q_scores=[0] * total_time_points
        # convert all translocation speeds to array
        for i in range(total_time_points):
            # get median translocation speed from q50 value (quartile 50%?) for basecall_boxplot[1] (translocation speed)
            if 'q50' in input_json_dict['acquisitions'][3]['basecall_boxplot'][1]['plot']['datasets'][i]:
                median_translocation_speeds[i]=input_json_dict['acquisitions'][3]['basecall_boxplot'][1]['plot']['datasets'][i]['q50']
            else:
                median_translocation_speeds[i]=np.nan
            # get median q score from q50 value (quartile 50%?) for basecall_boxplot[0] (Q score)
            if 'q50' in input_json_dict['acquisitions'][3]['basecall_boxplot'][0]['plot']['datasets'][i]:
                median_q_scores[i]=input_json_dict['acquisitions'][3]['basecall_boxplot'][0]['plot']['datasets'][i]['q50']
            else:
                median_q_scores[i]=np.nan
            if 'count' in input_json_dict['acquisitions'][3]['basecall_boxplot'][1]['plot']['datasets'][i]:
                median_corresponding_counts[i]=pd.to_numeric(input_json_dict['acquisitions'][3]['basecall_boxplot'][1]['plot']['datasets'][i]['count'])
            else:
                median_corresponding_counts[i]=np.nan
            # weighted translocation speeds and q scores by counts
            if (not np.isnan(median_corresponding_counts[i])) and (not np.isnan(median_translocation_speeds[i])):
                weighted_median_translocation_speeds[i]=median_translocation_speeds[i] * median_corresponding_counts[i]
            else:
                weighted_median_translocation_speeds[i]=np.nan
            if (not np.isnan(median_corresponding_counts[i])) and (not np.isnan(median_translocation_speeds[i])):
                weighted_median_q_scores[i]=median_q_scores[i] * median_corresponding_counts[i]
            else:
                weighted_median_q_scores[i]=np.nan
        # drop nas
        median_translocation_speeds=[x for x in median_translocation_speeds if not np.isnan(x)]
        median_q_scores=[x for x in median_q_scores if not np.isnan(x)]
        median_corresponding_counts=[x for x in median_corresponding_counts if not np.isnan(x)]
        weighted_median_translocation_speeds=[x for x in weighted_median_translocation_speeds if not np.isnan(x)]
        weighted_median_q_scores=[x for x in weighted_median_q_scores if not np.isnan(x)]
        # check array lengths before reporting any of these statistics (perhaps nothing left after dropping nas)
        if len(median_translocation_speeds) > 0:
            # first median translocation speed
            fields_from_json.starting_median_translocation_speed = round(median_translocation_speeds[0],3)
            # then average median translocation speed
            fields_from_json.average_median_translocation_speed_over_time = round(sum(median_translocation_speeds)/total_time_points,3)
            # then weighted average median translocation speed only if counts are over 0
            if sum(median_corresponding_counts)>0:
                fields_from_json.weighted_average_median_translocation_speed_over_time = round(sum(weighted_median_translocation_speeds)/sum(median_corresponding_counts),3)
            else:
                fields_from_json.weighted_average_median_translocation_speed_over_time = 'NA'
        else:
            fields_from_json.starting_median_translocation_speed = 'NA'
            fields_from_json.average_median_translocation_speed_over_time = 'NA'
            fields_from_json.weighted_average_median_translocation_speed_over_time = 'NA'
        # check array lengths before reporting any of these statistics (perhaps nothing left after dropping nas)
        if len(median_q_scores) > 0:
            # first median q score
            fields_from_json.starting_median_q_score = round(median_q_scores[0],3)
            # then average q score
            fields_from_json.average_median_q_score_over_time = round(sum(median_q_scores)/total_time_points,3)
            # then weighted average median q score only if counts are over 0
            if sum(median_corresponding_counts)>0:
                fields_from_json.weighted_average_median_q_score_over_time = round(sum(weighted_median_q_scores)/sum(median_corresponding_counts),3)
            else:
                fields_from_json.weighted_average_median_q_score_over_time = 'NA'
        else:
            fields_from_json.starting_median_q_score = 'NA'
            fields_from_json.average_median_q_score_over_time = 'NA'
            fields_from_json.weighted_average_median_q_score_over_time = 'NA'
    else:
        fields_from_json.starting_median_translocation_speed = 'NA'
        fields_from_json.starting_median_q_score = 'NA'
        fields_from_json.average_median_translocation_speed_over_time = 'NA'
        fields_from_json.average_median_q_score_over_time = 'NA'
        fields_from_json.weighted_average_median_translocation_speed_over_time = 'NA'
        fields_from_json.weighted_average_median_q_score_over_time = 'NA'
    # get starting active pores if in json file
    # get average active pores and active pore AUC (area under the curve) as well if in json file
    if 'mux_scan_results' in input_json_dict['acquisitions'][3]['acquisition_run_info']['bream_info']:
        if (len(input_json_dict['acquisitions'][3]['acquisition_run_info']['bream_info']['mux_scan_results']) >= 1) and ('counts' in input_json_dict['acquisitions'][3]['acquisition_run_info']['bream_info']['mux_scan_results'][0]):
            # get first (index 0) mux scan results
            fields_from_json.starting_active_pores = input_json_dict['acquisitions'][3]['acquisition_run_info']['bream_info']['mux_scan_results'][0]['counts']['single_pore'] + input_json_dict['acquisitions'][3]['acquisition_run_info']['bream_info']['mux_scan_results'][0]['counts']['reserved_pore']
        else:
            fields_from_json.starting_active_pores = 'NA'
            # get second active pore count if in json file
        if (len(input_json_dict['acquisitions'][3]['acquisition_run_info']['bream_info']['mux_scan_results']) >= 2) and ('counts' in input_json_dict['acquisitions'][3]['acquisition_run_info']['bream_info']['mux_scan_results'][1]):
            # get second (index 1) mux scan results
            fields_from_json.second_active_pore_count = input_json_dict['acquisitions'][3]['acquisition_run_info']['bream_info']['mux_scan_results'][1]['counts']['single_pore'] + input_json_dict['acquisitions'][3]['acquisition_run_info']['bream_info']['mux_scan_results'][1]['counts']['reserved_pore']
            # make average active pore/active pore AUC/average active pore loss from time point to time point if at least two counts present
            # number of pore counts (in essence, time points) is number of mux scan results
            pore_counts = len(input_json_dict['acquisitions'][3]['acquisition_run_info']['bream_info']['mux_scan_results'])
            # initialize empty list to store pore counts
            pore_count_list = [0] * pore_counts
            # iterate over pore counts to fill list
            for i in range(pore_counts):
                # active pore count is single pores plus reserve pores as above
                pore_count_list[i] = input_json_dict['acquisitions'][3]['acquisition_run_info']['bream_info']['mux_scan_results'][i]['counts']['single_pore'] + input_json_dict['acquisitions'][3]['acquisition_run_info']['bream_info']['mux_scan_results'][i]['counts']['reserved_pore']
            # calculate active pore AUC as sum of active pore counts in new array
            fields_from_json.active_pore_auc=sum(pore_count_list)
            # calculate average active pores from new array as active pore AUC (active pore sum over time) divided by number of time points
            fields_from_json.average_active_pores=round(fields_from_json.active_pore_auc/pore_counts,3)
            # calculate average active pore drop from timepoint to timepoint
            # number of pore change calculations
            pore_changes = pore_counts - 1
            # initialize empty list to store pore changes
            pore_change_list = [0] * pore_changes
            pore_change_list = [a - b for a, b in zip(pore_count_list[:-1],pore_count_list[1:])]
            # now calculate average pore change per time point by sum of change list divided by number of changes (time periods, 90 minutes default)
            fields_from_json.average_active_pore_change_rate=round(sum(pore_change_list)/pore_changes,3)
        else:
            fields_from_json.second_active_pore_count = 'NA'
            # added new fields on 10/7/2025 - set these as NA if fewer than two counts present
            fields_from_json.average_active_pores = 'NA'
            fields_from_json.active_pore_auc = 'NA'
            fields_from_json.average_active_pore_change_rate = 'NA'
    else:
        fields_from_json.starting_active_pores = 'NA'
        fields_from_json.second_active_pore_count = 'NA'
        # added new fields on 10/7/2025 - set these as NA if mux_scan_results not in bream_info for acquisitions[3]
        fields_from_json.average_active_pores = 'NA'
        fields_from_json.active_pore_auc = 'NA'
        fields_from_json.average_active_pore_change_rate = 'NA'
    # pore occupancy and adapter sequencing percentage based on duty time data - initially validated on NABEC R9 JSONs
    # check if duty time in fourth acquisitions key
    if 'duty_time' in input_json_dict['acquisitions'][3]:
        # get duty time lists for pore occupancy (actively sequencing vs. available for sequencing)
        # make sure to convert from string to int
        # get duty time for strand state (sequencing actual sample DNA)
        strand_duty_time_list=list(map(int,input_json_dict['acquisitions'][3]['duty_time'][0]['channel_states']['strand']['state_times']))
        # get duty time for adapter state (sequencing attached library adapters)
        adapter_duty_time_list=list(map(int,input_json_dict['acquisitions'][3]['duty_time'][0]['channel_states']['adapter']['state_times']))
        # get duty time for pore state (available for sequencing but not actively sequencing)
        pore_duty_time_list=list(map(int,input_json_dict['acquisitions'][3]['duty_time'][0]['channel_states']['pore']['state_times']))
        # already got duty time lists for percentage of actively sequencing pores sequencing adapter (strand vs. adapter) above
        # calculate actively sequencing total duty time (strand + adapter)
        active_sequencing_duty_time_list = [a + b for a, b in zip(strand_duty_time_list,adapter_duty_time_list)]
        # calculate total available for sequencing OR actively sequencing
        available_or_active_sequencing_duty_time_list = [a + b + c for a, b, c in zip(strand_duty_time_list,adapter_duty_time_list,pore_duty_time_list)]
        # calculate pore occupancy percentage in list
        # make sure to convert to percentage by multiplying by 100
        # correct zero division errors by setting quotient to zero when denominator zero
        pore_occupancy_percentage_list = [(a / b) * 100 if b else 0 for a, b in zip(active_sequencing_duty_time_list,available_or_active_sequencing_duty_time_list)]
        # first entry in pore occupancy list is starting pore occupancy
        fields_from_json.starting_pore_occupancy = round(pore_occupancy_percentage_list[0],3)
        # calculate average pore occupancy over run
        fields_from_json.average_pore_occupancy = round(sum(pore_occupancy_percentage_list)/len(pore_occupancy_percentage_list),3)
        # calculate percentage of sequencing pores sequencing adapter
        # correct zero division errors by setting quotient to zero when denominator zero
        adapter_sequencing_percentage_list = [(a / b) * 100 if b else 0 for a, b in zip(adapter_duty_time_list,active_sequencing_duty_time_list)]
        # first entry in percentage of sequencing pores sequencing adapter list is starting adapter sequencing percentage
        fields_from_json.starting_adapter_sequencing_percentage = round(adapter_sequencing_percentage_list[0],3)
        # calculate average adapter sequencing percentage over run
        fields_from_json.average_adapter_sequencing_percentage = round(sum(adapter_sequencing_percentage_list)/len(adapter_sequencing_percentage_list),3)
    else:
        fields_from_json.starting_pore_occupancy = 'NA'
        fields_from_json.average_pore_occupancy = 'NA'
        fields_from_json.starting_adapter_sequencing_percentage = 'NA'
        fields_from_json.average_adapter_sequencing_percentage = 'NA'
    return fields_from_json
# load json file list
# user input
inparser = argparse.ArgumentParser(description = 'Extract data from long read JSON report')
inparser.add_argument('--json_dir', default=None, type=str, help = 'path to directory containing JSON files, if converting whole directory')
inparser.add_argument('--filelist', default=None, type=str, help = 'text file containing list of all JSON reports to parse')
inparser.add_argument('--output', action="store", type=str, dest="output_file", help="Output long read JSON report summary table in tab-delimited format")
args = inparser.parse_args()
# get list of files
if args.json_dir is not None:
    files = glob.glob(f'{args.json_dir}/*.json')
elif args.filelist is not None:
    with open(args.filelist, 'r') as infile:
        files = [x.strip() for x in infile.readlines()]
else:
    quit('ERROR: No directory (--json_dir) or file list (--filelist) provided!')
# create output data frame
# set indices
sequencing_report_df_indices = [np.arange(0,len(files))]
# set column names in same order as described in GitHub readme
sequencing_report_column_names = ['Experiment Name',
'Sample Name',
'Run Date',
'Sequencer ID',
'Flow Cell Position',
'Flow Cell ID',
'Flow Cell Product Code',
'Data output (Gb)',
'Read Count (M)',
'N50 (kb)',
'MinKNOW Version',
'Sample Rate (Hz)',
'Starting Median Translocation Speed',
'Average Median Translocation Speed Over Time',
'Weighted Average Median Translocation Speed Over Time',
'Starting Median Q Score',
'Average Median Q Score Over Time',
'Weighted Average Median Q Score Over Time',
'Passed Bases (Gb)',
'Failed Bases (Gb)',
'Passed Reads (M)',
'Failed Reads (M)',
'Percentage Passed Bases',
'Percentage Passed Reads',
'Passed Modal Q Score',
'Failed Modal Q Score',
'Starting Active Pores',
'Second Active Pore Count',
'Average Active Pores',
'Active Pore AUC',
'Average Active Pore Change Per Mux Scan',
'Starting Pore Occupancy',
'Average Pore Occupancy',
'Starting Adapter Sequencing Percentage',
'Average Adapter Sequencing Percentage',
'Start Run ISO Timestamp',
'Start Run Timestamp']
# initialize data frame with said column names and filenames as indexes
sequencing_report_df = pd.DataFrame(index=sequencing_report_df_indices,columns=sequencing_report_column_names)
# main loop to process files
for idx, x in enumerate(files):
    try:
        # JSON file
        # debug by printing JSON file to stdout
        # print(x)
        f = open (x, "r")
        # Reading Python dictionary from JSON file
        data = orjson.loads(f.read())
        # get important information
        current_data_fields = get_fields_from_json(data)
        sequencing_report_df.loc[idx] = [current_data_fields.experiment_name,
        current_data_fields.sample_name,
        current_data_fields.run_date,
        current_data_fields.prom_id,
        current_data_fields.flow_cell_position,
        current_data_fields.flow_cell_id,
        current_data_fields.flow_cell_product_code,
        current_data_fields.data_output,
        current_data_fields.read_count,
        current_data_fields.n50,
        current_data_fields.minknow_version,
        current_data_fields.sample_rate,
        current_data_fields.starting_median_translocation_speed,
        current_data_fields.average_median_translocation_speed_over_time,
        current_data_fields.weighted_average_median_translocation_speed_over_time,
        current_data_fields.starting_median_q_score,
        current_data_fields.average_median_q_score_over_time,
        current_data_fields.weighted_average_median_q_score_over_time,
        current_data_fields.passed_bases,
        current_data_fields.failed_bases,
        current_data_fields.passed_reads,
        current_data_fields.failed_reads,
        current_data_fields.percentage_bases_passed,
        current_data_fields.percentage_reads_passed,
        current_data_fields.modal_q_score_passed,
        current_data_fields.modal_q_score_failed,
        current_data_fields.starting_active_pores,
        current_data_fields.second_active_pore_count,
        current_data_fields.average_active_pores,
        current_data_fields.active_pore_auc,
        current_data_fields.average_active_pore_change_rate,
        current_data_fields.starting_pore_occupancy,
        current_data_fields.average_pore_occupancy,
        current_data_fields.starting_adapter_sequencing_percentage,
        current_data_fields.average_adapter_sequencing_percentage,
        current_data_fields.iso_timestamp,
        current_data_fields.timestamp]
    except ValueError as e:
        print("File causing error:",x)
        print(e)
        continue
# print output data frame to tab delimited tsv file
sequencing_report_df.to_csv(args.output_file,sep='\t',index=False)
# end program
quit()

