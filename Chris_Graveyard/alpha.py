import requests
import configparser
import argparse
import csv
import subprocess
import os
import multiprocessing
import time

asf_baseurl = 'https://api.daac.asf.alaska.edu/services/search/param?'
aws_baseurl = 'http://sentinel1-slc-seasia-pds.s3-website-ap-southeast-1.amazonaws.com/datasets/slc/v1.1/'

def downloadGranule(row):
    orig_dir = os.getcwd()
    download_site = row['Download Site']
    frame_dir = 'P' + row['Path Number'].zfill(3) + '/F' + row['Frame Number'].zfill(4)
    print('Downloading granule ', row['Granule Name'], 'to directory', frame_dir)
    
    os.makedirs(frame_dir, exist_ok=True)
    os.chdir(frame_dir)
    status = 0
    
    if download_site == 'AWS' or download_site == 'both':
        print('Try AWS download first.')
        row_date = row['Acquisition Date']
        row_year = row_date[0:4]
        row_month = row_date[5:7]
        row_day = row_date[8:10]
        datefolder = row_year + '/' + row_month + '/' + row_day + '/'
        aws_url = aws_baseurl + datefolder + row['Granule Name'] + '/' + row['Granule Name'] + '.zip'
        status = downloadGranule_wget(aws_url)
        
        if status != 0:
            if download_site == 'AWS':
                print('AWS download failed. Granule not downloaded.')
            else:
                print('AWS download failed. Trying ASF download instead.')
    
    if (status != 0 and download_site == 'both') or download_site == 'ASF':
        asf_url = row['asf_wget_str'] + ' ' + row['URL']
        status = downloadGranule_wget(asf_url)
        if status != 0:
            print('ASF download failed. Granule not downloaded.')
    
    os.chdir(orig_dir)

def downloadGranule_wget(options_and_url):
    # Get the current directory of the script
    script_directory = os.path.dirname(os.path.realpath(__file__))
    
    # Define the path to wget executable in the 'Dpn' project folder
    wget_path = os.path.join(script_directory, 'Dpn', 'wget.exe')
    
    # Check if wget executable exists
    if not os.path.exists(wget_path):
        print("Error: wget executable not found at specified path:", wget_path)
        return 1
    
    # Construct the command with the path to wget
    cmd = f'"{wget_path}" -c --no-check-certificate -q {options_and_url}'
    print(cmd)
    
    # Run wget command
    result = subprocess.run(cmd, shell=True, capture_output=True)
    
    if result.returncode != 0:
        print("Error occurred during download:")
        print(result.stderr.decode('utf-8'))  # Print error output from wget
        return result.returncode
    else:
        return 0

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Use http requests and wget to search and download data from the ASF archive, based on parameters in a config file.')
    parser.add_argument('config', type=str, help='supply name of config file to set up API query. Required.')
    parser.add_argument('--download', action='store_true', help='Download the resulting scenes (default: false)')
    parser.add_argument('--verbose', action='store_true', help='Print the query result to the screen (default: false)')
    args = parser.parse_args()

    config = configparser.ConfigParser()
    config.optionxform = str
    config.read(args.config)
    download_site = config.get('download', 'download_site', fallback='both')
    nproc = config.getint('download', 'nproc', fallback=1)
    output_format = config.get('api_search', 'output', fallback='csv')
    
    arg_list = config.items('api_search')
    arg_str = '&'.join('%s=%s' % (item[0], item[1]) for item in arg_list)
    argurl = asf_baseurl + arg_str
    
    print('\nRunning ASF API query:')
    print(argurl + '\n')
    
    try:
        r = requests.post(argurl)
        r.raise_for_status()  # Raise an error for bad responses
        if output_format == 'csv':
            reader = csv.DictReader(r.text.splitlines())
            rows = list(reader)
        
        logtime = time.strftime("%Y_%m_%d-%H_%M_%S")
        query_log = 'asf_query_%s.%s' % (logtime, output_format)
        with open(query_log, 'w')as f:
            print('Query result saved to asf_query_%s.%s' % (logtime, output_format))
            f.write(r.text)
        
        if args.verbose:
            if output_format == 'csv':
                numscenes = len(rows)
                plural_s = 's' if numscenes > 1 else ''
                if numscenes > 0:
                    print("Found %s scene%s." % (numscenes, plural_s))
                    for row in rows:
                        print('Scene %s, Path %s / Frame %s' % (row['Granule Name'], row['Path Number'], row['Frame Number']))
            else:
                print(r.text)
        
        if output_format != 'csv' and args.download:
            print('Error: cannot download unless output format is set to csv. Doing nothing.')
        
        if output_format == 'csv' and args.download:
            if nproc > 1:
                print('\nRunning %d downloads in parallel.' % nproc)
            else:
                print('\nDownloading 1 at a time.')
            
            if download_site != 'AWS':
                if not (config.has_section('asf_download') and config.has_option('asf_download', 'http-user') \
                        and config.has_option('asf_download', 'http-password') and len(
                            config.get('asf_download', 'http-user')) > 0 \
                        and len(config.get('asf_download', 'http-password')) > 0):
                    raise ValueError('ASF username or password missing in config file.')
                asf_wget_options = config.items('asf_download')
                asf_wget_str = ' '.join('--%s=%s' % (item[0], item[1]) for item in asf_wget_options)
            else:
                asf_wget_str = ''
            
            downloadList = []
            for row in rows:
                downloadDict = row
                downloadDict['Download Site'] = download_site
                downloadDict['asf_wget_str'] = asf_wget_str
                downloadList.append(downloadDict)
            
            multiprocessing.set_start_method("spawn")
            with multiprocessing.get_context("spawn").Pool(processes=nproc) as pool:
                pool.map(downloadGranule, downloadList, chunksize=1)
            print('\nDownload complete.\n')
        else:
            print('\nNot downloading.\n')
        
        print('Sentinel query complete.\n')
    
    except requests.exceptions.RequestException as e:
        print("Request failed:", e)
    except Exception as e:
        print("An unexpected error occurred:", e)
