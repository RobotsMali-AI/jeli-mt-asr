"""Script to remove some of the most common issues in the .tsv transcription file"""

import csv
import re
import os
import sys
import glob

def clean_tsv(input_file : str, output_file: str, revision_file: str) -> None:
    """Generic function

    Args:
        input_file (str): The path to the tsv file to clean
        output_file (str): The path to the file to save the cleaned rows in. (Typically the same file)
        revision_file (str): The path to the file to save still inconsistent rows in

    Returns:
        _type_: _description_
    """
    cleaned_rows = []
    revision_rows = []

    # Helper function to clean the line
    def clean_line(line):
        # Remove unwanted characters
        line = re.sub(r'[<>"]', '', line)

        # Replace consecutive tabs with a single tab
        line = re.sub(r'\t+', '\t', line)

        return line

    # Open the input file and process each row
    with open(input_file, 'r', encoding='utf-8') as infile:
        reader = csv.reader(infile, delimiter='\t')

        for row in reader:
            # Clean the row
            row = [clean_line(item) for item in row]

            # If the row has exactly 4 items, ensure the first two are numbers
            if len(row) == 4:
                try:
                    # Ensure the first two items are numbers
                    start_time = int(row[0])
                    end_time = int(row[1])

                    # Append the cleaned row
                    cleaned_rows.append(row)
                except ValueError:
                    # If timestamps are not valid integers, move to revision
                    revision_rows.append(row)
                    print("One problematic row has been added to revision")
            # If the row has more than 4 items and no consecutive \t, check for \t swapped with space
            elif len(row) > 4:
                row_str = "\t".join(row)
                if ',' in row_str:
                    row_str = re.sub(r',\t', ', ', row_str)
                # After fixing spaces, split again and check the length
                row_fixed = row_str.split('\t')
                if len(row_fixed) == 4:
                    cleaned_rows.append(row_fixed)
                else:
                    revision_rows.append(row_fixed)
                    print("One problematic row has been added to revision")
            else:
                # For rows with incorrect number of elements, move to revision
                revision_rows.append(row)
                print("One problematic row has been added to revision")

    # Write the cleaned rows to the output file
    with open(output_file, 'w', encoding='utf-8', newline='') as outfile:
        writer = csv.writer(outfile, delimiter='\t')
        writer.writerows(cleaned_rows)
        print(f"**** New cleaned tsv file saved at {output_file} ****")

    if revision_rows:
        # Write the revision rows to the revision file if there are rows to review
        with open(revision_file, 'w', encoding='utf-8', newline='') as revfile:
            writer = csv.writer(revfile, delimiter='\t')
            writer.writerows(revision_rows)
            print(f"**** New revision file saved at {revision_file} ****")

if __name__ == "__main__":
    transcription_dir = sys.argv[1]

    # Ensure revision directory exist
    rev_dir = f'{transcription_dir}/revisions'
    os.makedirs(rev_dir, exist_ok=True)

    # get the paths to all the tsv files
    tsv_files = glob.glob(transcription_dir + "/*.tsv")

    for tsv_file in tsv_files:
        in_file = tsv_file
        out_file = in_file
        rev_file = rev_dir + "/" + tsv_file.split("/")[-1][:-4] + "-rev.tsv"
        clean_tsv(input_file=in_file, output_file=out_file, revision_file=rev_file)
