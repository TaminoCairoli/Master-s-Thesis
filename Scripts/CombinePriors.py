#!/usr/bin/env python3
import sys
import re
import os

    """
    Execute: python3 CombinePrios.py InputFile_WithPriors.star InputFile_NoPriors.star
    """

def parse_star_file(filename):
    """
    Reads a STAR file and separates header lines from data lines.
    Header lines include blank lines and lines starting with '_', 'data_', or 'loop_'.
    """
    header_lines = []
    data_lines = []
    with open(filename, 'r') as f:
        lines = f.readlines()

    header_complete = False
    for line in lines:
        # Consider these lines part of the header.
        if not header_complete:
            if line.strip() == "" or line.startswith("_") or line.lstrip().startswith("data_") or line.lstrip().startswith("loop_"):
                header_lines.append(line)
            else:
                header_complete = True
        if header_complete:
            if line.strip():
                data_lines.append(line)
    return header_lines, data_lines

def find_column_index(header_lines, colname):
    """
    Searches for a header line that starts exactly with the given colname.
    Expects a format like:
       _rlnSomeColumnName #N
    Returns the 0-based index (e.g. "#1" gives index 0).
    """
    for line in header_lines:
        if line.startswith(colname):
            parts = line.strip().split()
            if len(parts) >= 2 and parts[1].startswith("#"):
                try:
                    return int(parts[1].lstrip("#")) - 1
                except ValueError:
                    pass
    return None

def extract_block_number(micrograph_name):
    """
    Extracts a block number from a micrograph name.
    The regex looks for an underscore followed by digits occurring before a dot or at the end.
    For example, 'rec_PD272_03.tomostar' returns the number 3.
    """
    match = re.search(r'_(\d+)(?:\.|$)', micrograph_name)
    if match:
        return int(match.group(1))
    else:
        return 9999

def sort_source_file(source_file):
    """
    Reads the source STAR file, sorts its data rows based on the block number
    (extracted from the _rlnMicrographName #1 column), and returns the header lines and sorted rows.
    """
    header_lines, data_lines = parse_star_file(source_file)
    micrograph_index = find_column_index(header_lines, "_rlnMicrographName")
    if micrograph_index is None:
        sys.exit("Error: Could not find _rlnMicrographName column in the source file header.")
    data_rows = [line.strip().split() for line in data_lines if line.strip()]
    sorted_data = []
    for row in data_rows:
        if len(row) <= micrograph_index:
            continue
        block_num = extract_block_number(row[micrograph_index])
        sorted_data.append((block_num, row))
    sorted_data.sort(key=lambda x: x[0])
    sorted_rows = [row for (_, row) in sorted_data]
    return header_lines, sorted_rows

def extract_new_columns_from_sorted_source(header_lines, sorted_rows):
    """
    From the sorted source file (header and sorted rows), extracts the values of:
      - _rlnHelicalTubeID
      - _rlnAngleTiltPrior
      - _rlnAnglePsiPrior
    Returns a list where each element is a list of the three values for that row.
    """
    idx_helical = find_column_index(header_lines, "_rlnHelicalTubeID")
    idx_tilt    = find_column_index(header_lines, "_rlnAngleTiltPrior")
    idx_psi     = find_column_index(header_lines, "_rlnAnglePsiPrior")
    if idx_helical is None or idx_tilt is None or idx_psi is None:
        sys.exit("Error: Could not find one or more required columns (_rlnHelicalTubeID, _rlnAngleTiltPrior, _rlnAnglePsiPrior) in the source file.")
    new_columns = []
    for row in sorted_rows:
        if len(row) > max(idx_helical, idx_tilt, idx_psi):
            new_columns.append([row[idx_helical], row[idx_tilt], row[idx_psi]])
        else:
            new_columns.append(["", "", ""])
    return new_columns

def process_target_file(target_file, new_columns):
    """
    Reads the target STAR file and appends the three new columns to the particles block.
    It finds the 'data_particles' section, locates the loop header, appends new header definitions,
    and then appends the new column values to each data row.
    Returns the modified file lines.
    """
    with open(target_file, 'r') as f:
        lines = f.readlines()

    out_lines = []
    i = 0
    n = len(lines)
    in_particles = False
    loop_found = False

    # Write lines until reaching the data_particles block.
    while i < n:
        line = lines[i]
        out_lines.append(line)
        if not in_particles and line.strip().startswith("data_particles"):
            in_particles = True
        elif in_particles and not loop_found:
            if line.strip().startswith("loop_"):
                loop_found = True
                i += 1
                # Collect header lines for the particles loop.
                header_block = []
                while i < n and lines[i].strip().startswith("_"):
                    header_block.append(lines[i])
                    i += 1
                # Determine the highest column number from the current header.
                last_num = 0
                for header_line in header_block:
                    parts = header_line.strip().split()
                    for part in parts:
                        if part.startswith("#"):
                            try:
                                num = int(part.lstrip("#"))
                                if num > last_num:
                                    last_num = num
                            except:
                                pass
                # Write out the existing header lines.
                for h in header_block:
                    out_lines.append(h)
                # Append new header definitions.
                new_header_lines = []
                new_header_lines.append("_rlnHelicalTubeID #{}".format(last_num+1) + "\n")
                new_header_lines.append("_rlnAngleTiltPrior #{}".format(last_num+2) + "\n")
                new_header_lines.append("_rlnAnglePsiPrior #{}".format(last_num+3) + "\n")
                for nh in new_header_lines:
                    out_lines.append(nh)
                # Exit the header section and process data rows.
                break
        i += 1

    # The remaining lines are assumed to be particle data rows.
    data_rows = lines[i:]
    new_data_rows = []
    for j, row in enumerate(data_rows):
        if row.strip() == "":
            new_data_rows.append(row)
            continue
        # Append new column values if available.
        if j < len(new_columns):
            appended = "  " + "  ".join(new_columns[j])
        else:
            appended = ""
        new_row = row.rstrip("\n") + appended + "\n"
        new_data_rows.append(new_row)
    
    final_lines = out_lines + new_data_rows
    return final_lines

def main():
    if len(sys.argv) != 3:
        print("Usage: python3 {} sourcefile_needs_sorting.star targetfile_will_get_new_columns.star".format(sys.argv[0]))
        sys.exit(1)
    
    source_file = sys.argv[1]
    target_file = sys.argv[2]

    # Compute output filenames.
    source_base, source_ext = os.path.splitext(source_file)
    sorted_source_file = source_base + "_sorted" + source_ext

    target_base, target_ext = os.path.splitext(target_file)
    modified_target_file = target_base + "_modified" + target_ext

    # Step 1: Sort the source file.
    source_header, sorted_rows = sort_source_file(source_file)
    # Write out the sorted source file.
    with open(sorted_source_file, 'w') as f:
        for line in source_header:
            f.write(line)
        for row in sorted_rows:
            f.write("  ".join(row) + "\n")
    print("Sorted source file written to {}".format(sorted_source_file))

    # Step 2: Extract the three new columns from the sorted source.
    new_columns = extract_new_columns_from_sorted_source(source_header, sorted_rows)

    # Step 3: Process the target file by appending the new columns.
    modified_lines = process_target_file(target_file, new_columns)
    with open(modified_target_file, 'w') as f:
        f.writelines(modified_lines)
    print("Modified target file written to {}".format(modified_target_file))

if __name__ == '__main__':
    main()
