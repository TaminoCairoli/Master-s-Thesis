import sys
import re

def modify_star_file(input_file, output_file):
    with open(input_file, 'r') as f:
        lines = f.readlines()
    
    in_particles_loop = False
    angle_rot_index = None
    modified_lines = []
    
    for line in lines:
        if line.startswith("data_particles"):
            in_particles_loop = False  # Reset flag in case of multiple loops
        
        if line.startswith("loop_"):
            in_particles_loop = True
            modified_lines.append(line)
            continue
        
        if in_particles_loop and "_rlnAngleRot" in line:
            angle_rot_index = int(line.split("#")[-1]) - 1
        
        if in_particles_loop and angle_rot_index is not None and not line.startswith("_"):
            parts = re.split(r'(\s+)', line)  # Preserve spacing
            if len(parts) > angle_rot_index * 2:
                parts[angle_rot_index * 2] = str(float(parts[angle_rot_index * 2]) + 180)
            modified_lines.append("".join(parts))
        else:
            modified_lines.append(line)
    
    with open(output_file, 'w') as f:
        f.writelines(modified_lines)

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(f"Usage: python3 {sys.argv[0]} <inputfile.star> <outputfile.star>")
        sys.exit(1)
    
    modify_star_file(sys.argv[1], sys.argv[2])
