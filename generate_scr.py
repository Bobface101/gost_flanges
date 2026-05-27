import csv
import os

script_dir = os.path.dirname(os.path.abspath(__file__))
input_file = os.path.join(script_dir, 'B_mod.txt')
output_file = os.path.join(script_dir, 'flange_plotter.scr')

scr_lines = []

startpos_x = 0
startpos_y = 0


def fmt(pt):
    """format point as an AutoCAD coordinate string."""
    x, y = pt
    return f"{x:g},{y:g}"

def midpoint(*points):   
    num_points = len(points)
    print([p[0] for p in points])
    x_avg = sum(p[0] for p in points) / num_points
    y_avg = sum(p[1] for p in points) / num_points
    return (x_avg, y_avg)

def conjugate(pt):
    x, y = pt
    return (x, -y)


def add_sysvar(name, value):
    """Add a system variable setting to the script.
      VARNAME
      value
    """
    scr_lines.append(name)
    scr_lines.append(str(value))


with open(input_file, 'r') as f:
    reader = csv.reader(f)
    header = next(reader)  # Skip header


    # Disable smooth view transitions
    add_sysvar("VTENABLE", 0)
    #disable Dynamic Input
    add_sysvar("DYNMODE", 0)
    #disable command echo
    add_sysvar("CMDECHO", 0)
    #disable object snaps
    add_sysvar("OSMODE", 0)
    
    scr_lines.append("VIEWRES")
    scr_lines.append("Y")
    scr_lines.append("20000")

    for row in reader:
        flange = row[0]
        OD   = float(row[1])
        D1  = float(row[2])
        D2  = float(row[3])
        d_b = float(row[4])
        b   = float(row[5])
        h   = float(row[6])
        d   = float(row[7])
        n   = int(row[8])
        bolt_size = row[9]

        sx = startpos_x
        sy = startpos_y

        # Calculate points with startpos offset
        A =  (sx,         sy)
        B  = (sx + 0,     sy + OD / 2)
        C  = (sx + b - h, sy + OD / 2)
        D = (sx + b - h, sy + (D1 / 2) + d / 2)  
        E  = (sx + 0,     sy + (D1 / 2) + d / 2)
        F  = (sx + b - h, sy + (D1 / 2) - d / 2)
        G  = (sx + 0,     sy + (D1 / 2) - d / 2)
        H  = (sx + 0,     sy + d_b / 2)
        I  = (sx + b,     sy + d_b / 2)
        J  = (sx + b,     sy + D2 / 2)
        K  = (sx + b - h, sy + D2 / 2 + h)
        L =  (sx + b,     sy)

        # bounding box for crossing selection & zoom
        all_y = [B[1], C[1], D[1], E[1], F[1], G[1], H[1], I[1], J[1], K[1]]
        min_y = min(all_y)
        max_y = max(all_y)

        sel_x1 = sx - 1
        sel_y1 = min_y - 1
        sel_x2 = sx + b + 1
        sel_y2 = max_y + 1

        #Zoom to the area for this flange


        scr_lines.append("ZOOM")
        scr_lines.append("W")
        scr_lines.append(fmt((sel_x1, -(max_y + 1))))
        scr_lines.append(fmt((sel_x2, sel_y2)))

        #Change to 0 layer
        scr_lines.append("CLAYER")
        scr_lines.append("0")

        #Write title 
        scr_lines.append("TEXT")
        scr_lines.append(fmt((sx, max_y + 100)))
        scr_lines.append("14")
        scr_lines.append("0")
        scr_lines.append(flange)
        scr_lines.append("\n\n")

        #--- Draw line segments

        # Chain 1: A -> H -> B -> C -> D -> E  (segments HB, BC, CD, DE)
        scr_lines.append("LINE")
        scr_lines.append(fmt(A))
        scr_lines.append(fmt(H))
        scr_lines.append(fmt(B))
        scr_lines.append(fmt(C))
        scr_lines.append(fmt(D))
        scr_lines.append(fmt(E))
        scr_lines.append("")  # Enter to end LINE command

        # Chain 2: G -> F  (segment GF)
        scr_lines.append("LINE")
        scr_lines.append(fmt(G))
        scr_lines.append(fmt(F))
        scr_lines.append("")  # Enter to end LINE command

        # Chain 3: I -> L  (segment IL)
        scr_lines.append("LINE")
        scr_lines.append(fmt(I))
        scr_lines.append(fmt(L))
        scr_lines.append("")  # Enter to end LINE command

        # Chain 3: D -> F -> K -> J -> I -> H
        overlap = K[1] - F[1]
        if overlap > 0:
            # Overlap case: skip the FK segment
            scr_lines.append("LINE")
            scr_lines.append(fmt(D))
            scr_lines.append(fmt(K))
            scr_lines.append(fmt(J))
            scr_lines.append(fmt(I))
            scr_lines.append(fmt(H))
            scr_lines.append("")  # Enter to end LINE command

            scr_lines.append("LINE")
            scr_lines.append(fmt(F))
            scr_lines.append(f"@{overlap},0")
            scr_lines.append("")
        else:
            #normal case: no overlap, draw full chain
            scr_lines.append("LINE")
            scr_lines.append(fmt(D))
            scr_lines.append(fmt(F))
            scr_lines.append(fmt(K))
            scr_lines.append(fmt(J))
            scr_lines.append(fmt(I))
            scr_lines.append(fmt(H))
            scr_lines.append("")  # Enter to end LINE command

        #Change to DIM layer
        scr_lines.append("CLAYER")
        scr_lines.append("DIM")

        # Bolt Centerlines
        scr_lines.append("CENTERLINE")
        scr_lines.append(fmt(midpoint(E, D)))
        scr_lines.append(fmt(midpoint(G, F)))

        # Hatching 
        scr_lines.append("HATCH")
        scr_lines.append(fmt(midpoint(B,C,D,E)))
        scr_lines.append(fmt(midpoint(F,G,H,I)))
        scr_lines.append("")   

        # --- Mirror across x-axis 
        scr_lines.append("MIRROR")
        scr_lines.append("C")                          # Crossing selection
        scr_lines.append(fmt((sel_x1, sel_y1)))         # First corner
        scr_lines.append(fmt((sel_x2, sel_y2)))         # Opposite corner
        scr_lines.append("")                            # Enter to end selection
        scr_lines.append(fmt((sx, 0)))                  # First point of mirror line (x-axis)
        scr_lines.append(fmt((sx + 1, 0)))              # Second point of mirror line
        scr_lines.append("N")                           # Don't erase source objects

        # Main Centerline 
        scr_lines.append("CENTERLINE")
        scr_lines.append(fmt(midpoint(H, I)))
        scr_lines.append(fmt(midpoint(conjugate(H), conjugate(I))))

        # Update startpos for next shape
        startpos_x += 300

    # 
    scr_lines.append("ZOOM")
    scr_lines.append("E")
    # Restore defaults
    add_sysvar("CMDECHO", 1)
    add_sysvar("DYNMODE", 3)
    add_sysvar("OSMODE", 4133)

# Write .scr file
#join with newlines
with open(output_file, 'w') as f:
    f.write('\n'.join(scr_lines))
    f.write('\n')  # Single trailing newline to execute the last command

print(f"Generated {output_file}")
