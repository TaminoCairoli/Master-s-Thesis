#!/usr/bin/env python3
import sys
import os

def process_star_file(input_filename, output_filename):
    with open(input_filename, 'r') as infile:
        lines = infile.readlines()

    output_lines = []
    in_particles_section = False
    in_loop = False
    headers = []
    psi_index = None  # column index for _rlnAnglePsiPrior

    for line in lines:
        stripped = line.strip()
        
        # Check for the start of the data_particles section
        if stripped.startswith("data_particles"):
            in_particles_section = True
            in_loop = False
            headers = []
            psi_index = None
            output_lines.append(line)
            continue
        elif stripped.startswith("data_") and not stripped.startswith("data_particles"):
            # Exit the data_particles block when another data_ block begins
            in_particles_section = False
            in_loop = False
            headers = []
            psi_index = None
            output_lines.append(line)
            continue

        if in_particles_section:
            # Look for the start of a loop block
            if stripped.startswith("loop_"):
                in_loop = True
                headers = []
                psi_index = None
                output_lines.append(line)
                continue

            # Capture header lines and record the index for _rlnAnglePsiPrior
            if in_loop and stripped.startswith("_"):
                headers.append(stripped)
                if "_rlnAnglePsiPrior" in stripped:
                    psi_index = len(headers) - 1
                output_lines.append(line)
                continue

            # Process data lines in the loop
            if in_loop and stripped != "":
                tokens = line.split()
                if psi_index is not None and len(tokens) > psi_index:
                    try:
                        original_value = float(tokens[psi_index])
                        new_value = original_value + 90.0
                        tokens[psi_index] = f"{new_value:.6f}"
                    except ValueError:
                        # Leave the token unchanged if conversion fails.
                        pass
                    new_line = "  ".join(tokens) + "\n"
                    output_lines.append(new_line)
                else:
                    output_lines.append(line)
                continue

            output_lines.append(line)
        else:
            output_lines.append(line)

    with open(output_filename, 'w') as outfile:
        outfile.writelines(output_lines)

def main():
    if len(sys.argv) != 2:
        print("Usage: python3 scriptname.py inputfile")
        sys.exit(1)
    
    input_filename = sys.argv[1]
    base, _ = os.path.splitext(input_filename)
    output_filename = base + "_rotated_Psi.star"
    process_star_file(input_filename, output_filename)
    print(f"Modified file written to {output_filename}")

if __name__ == '__main__':
    main()
