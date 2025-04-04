import pandas as pd
import sys

    """
    Script generated with the assistance of ChatGPT (OpenAI)
    Context: Master's Thesis – Establishing a RELION-5-Based Pipeline for Cryo-ET: Structural Analysis of Cilia
    Author: Tamino Cairoli | Date: 04.04.2025
    Description: After classifying the individual opsitions of the ODA, this script roatates the ODA from the "bottom left" position to the "top left" position. Do not forget to
    center the particles (via a classification step) after rotating the particles. The prior information is changed by inverting the sing of the rotation angle (_rlnAngleRot)
    and the tilt angle (_rlnAngleTilt). Additionally, 125 is added to the _rlnAngleRot column. 
    Execute: python3 Rot125_TiltInvert.py InputFile.star OutputFile.star
    """

def invert_tilt_and_adjust_rot_in_star(input_file, output_file):
    with open(input_file, 'r') as file:
        lines = file.readlines()

    header_lines = []
    data_start_idx = None
    loop_start_idx = None

    # Find the particles loop specifically
    for idx, line in enumerate(lines):
        if line.strip() == 'data_particles':
            loop_start_idx = idx
        if loop_start_idx and line.strip() == 'loop_':
            header_start_idx = idx
            break

    for idx, line in enumerate(lines[header_start_idx:], start=header_start_idx):
        if line.startswith('_'):
            header_lines.append(line)
        elif header_lines and line.strip():
            data_start_idx = idx
            break

    columns = [line.split()[0] for line in header_lines]

    if '_rlnAngleTilt' not in columns:
        raise ValueError("Column _rlnAngleTilt not found.")

    if '_rlnAngleRot' not in columns:
        raise ValueError("Column _rlnAngleRot not found.")

    data = pd.read_csv(input_file, delim_whitespace=True, header=None,
                       skiprows=data_start_idx, names=columns, engine='python')

    data['_rlnAngleTilt'] = -data['_rlnAngleTilt']
    data['_rlnAngleRot'] = (-data['_rlnAngleRot']) + 125

    with open(output_file, 'w') as file:
        file.writelines(lines[:data_start_idx])
        data.to_csv(file, sep='\t', index=False, header=False, float_format='%.6f')

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python3 invert_tilt_and_adjust_rot.py input.star output.star")
        sys.exit(1)

    input_star = sys.argv[1]
    output_star = sys.argv[2]

    invert_tilt_and_adjust_rot_in_star(input_star, output_star)
    print(f"Inverted tilt angles and adjusted rotation angles saved to {output_star}")
