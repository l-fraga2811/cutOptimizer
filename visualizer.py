import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np
from collections import defaultdict

def visualize_cutting_pattern(roll_width, roll_length, placements, unit):
    """
    Visualize the cutting pattern on the roll.
    
    Args:
        roll_width (float): Width of the roll in cm
        roll_length (float): Length of the roll in cm
        placements (list): List of tuples (x, y, width, length) for each piece
        unit (str): Unit of measurement (meters or centimeters)
    
    Returns:
        matplotlib.figure.Figure: Figure object with the visualization
    """
    # Create figure and axis with inverted axes (width on y-axis, length on x-axis)
    # Swap width and height for the figure size
    aspect_ratio = roll_length / roll_width  # Aspect ratio for inverted axes
    # Use a fixed height that's larger than width for landscape orientation with inverted axes
    fig_width = 10
    fig_height = min(fig_width * aspect_ratio, 6)  # Ensure height is appropriate
    
    # Create figure in landscape orientation
    fig, ax = plt.subplots(figsize=(fig_width, fig_height))
    
    # Set limits and labels with inverted axes
    ax.set_xlim(0, roll_length)  # X-axis now represents length
    ax.set_ylim(roll_width, 0)   # Y-axis now represents width (inverted for coordinate system)
    
    # Convert units for display
    conversion = 100 if unit == "meters" else 1
    
    # Add title and labels with inverted axes
    ax.set_title(f"Cutting Pattern - Roll: {roll_width/conversion:.3f}×{roll_length/conversion:.3f} {unit}")
    ax.set_xlabel(f"Length ({unit})")  # Now x-axis is length
    ax.set_ylabel(f"Width ({unit})")   # Now y-axis is width
    
    # Draw the roll with inverted axes (length on x, width on y)
    roll = patches.Rectangle(
        (0, 0), roll_length, roll_width,  # Inverted: (length, width)
        linewidth=2, edgecolor='black', facecolor='white'
    )
    ax.add_patch(roll)
    
    # Define a colormap for the pieces
    colors = plt.cm.tab20.colors
    
    # Group identical pieces
    piece_groups = defaultdict(list)
    for i, (x, y, width, length) in enumerate(placements):
        piece_groups[(width, length)].append((i, x, y))
    
    # Draw pieces with grouped colors and labels
    color_idx = 0
    for (width, length), positions in piece_groups.items():
        color = colors[color_idx % len(colors)]
        color_idx += 1
        
        # Draw each piece in this group - with inverted axes
        for i, x, y in positions:
            # For inverted axes, we draw the rectangle with (y, x) coordinates
            # and (length, width) dimensions
            piece = patches.Rectangle(
                (y, x), length, width,  # Inverted: (y, x, length, width)
                linewidth=1, edgecolor='black', facecolor=color, alpha=0.7
            )
            ax.add_patch(piece)
            
            # Add text label in the center of the piece with size proportional to piece
            # Calculate better font size based on the piece dimensions
            piece_area = width * length
            min_dimension = min(width, length)
            
            # Adjust font size dynamically based on piece dimensions
            if min_dimension < 20:  # Very small pieces
                font_size = 5
            else:
                # Make font size proportional to the smallest dimension of the piece
                font_size = min(max(6, min_dimension / 25), 10)
            
            # Create label text - short format for small pieces
            if min_dimension < 30:
                # Compact format for small pieces
                label_text = f"{i+1}"
            elif min_dimension < 60:
                # Medium size pieces with slightly more info
                label_text = f"{i+1}"
            else:
                # Normal format with dimensions for larger pieces
                label_text = f"{i+1}\n{width/conversion:.2f}×{length/conversion:.2f}"
            
            # Center position is also inverted: (y+length/2, x+width/2)
            ax.text(
                y + length/2, x + width/2,  # Inverted text position
                label_text,
                horizontalalignment='center',
                verticalalignment='center',
                fontsize=font_size,
                fontweight='bold',
                bbox=dict(facecolor='white', alpha=0.7, edgecolor='none', pad=1)
            )
    
    # Add grid
    ax.grid(True, linestyle='--', alpha=0.5)
    
    # Add legend showing each unique piece size with counts
    legend_entries = []
    for (width, length), positions in piece_groups.items():
        count = len(positions)
        legend_entries.append(
            f"{width/conversion:.3f}×{length/conversion:.3f} {unit} ({count}x)"
        )
    
    # Place the legend outside the plot area
    if legend_entries:
        leg = ax.legend(
            handles=[patches.Patch(color=colors[i % len(colors)]) for i in range(len(legend_entries))],
            labels=legend_entries,
            title="Piece Dimensions (Quantity)",
            loc='upper center', 
            bbox_to_anchor=(0.5, -0.15),
            ncol=min(3, len(legend_entries)),
            frameon=True,
            fancybox=True,
            shadow=True
        )
    
    # Add utilization information
    total_area = roll_width * roll_length
    used_area = sum(p[2] * p[3] for p in placements)
    utilization = used_area / total_area * 100
    waste_area = total_area - used_area
    
    info_text = (
        f"Material Usage: {utilization:.2f}%\n"
        f"Total Pieces: {len(placements)}\n"
        f"Waste Area: {waste_area/conversion**2:.3f} {unit}²"
    )
    
    # Position info text in inverted coordinates (length, width)
    ax.text(
        roll_length * 0.02, roll_width * 0.98,  # Inverted position for info text
        info_text,
        verticalalignment='top',
        bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="black", alpha=0.9)
    )
    
    # Make layout tight but with extra space for the legend
    plt.tight_layout()
    plt.subplots_adjust(bottom=0.2)
    
    return fig
