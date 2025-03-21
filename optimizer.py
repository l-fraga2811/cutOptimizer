import numpy as np
from collections import defaultdict

def optimize_cutting(roll_width, roll_length, pieces, force_horizontal=False):
    """
    Optimize the cutting pattern for a roll of material.
    
    Args:
        roll_width (float): Width of the roll in cm
        roll_length (float): Length of the roll in cm
        pieces (list): List of tuples (width, length) for each piece in cm
        force_horizontal (bool): If True, forces pieces to be placed horizontally
    
    Returns:
        tuple: (placements, waste_percentage)
            - placements: List of tuples (x, y, width, length) for each piece
            - waste_percentage: Percentage of material wasted
    """
    if force_horizontal:
        return optimize_horizontal_cutting(roll_width, roll_length, pieces)
    
    # Default to horizontal cutting for now
    return optimize_horizontal_cutting(roll_width, roll_length, pieces)

def optimize_horizontal_cutting(roll_width, roll_length, pieces):
    """
    Optimize cutting pattern with horizontal placement and gap filling.
    
    Args:
        roll_width (float): Width of the roll in cm
        roll_length (float): Length of the roll in cm
        pieces (list): List of tuples (width, length) for each piece in cm
    
    Returns:
        tuple: (placements, waste_percentage)
    """
    # Create working copy of pieces and sort by width (largest first)
    remaining_pieces = [(w, l) for w, l in pieces]
    remaining_pieces.sort(key=lambda x: x[0], reverse=True)
    
    placements = []
    current_y = 0
    
    while remaining_pieces and current_y < roll_length:
        row_result = place_row(current_y, roll_width, roll_length, remaining_pieces)
        if not row_result:
            break
            
        row_placements, used_pieces, row_height = row_result
        
        # Remove used pieces from remaining pieces
        for _ in range(used_pieces):
            remaining_pieces.pop(0)
        
        # Add row placements to final placements
        placements.extend(row_placements)
        
        # Move to next row
        current_y += row_height
    
    # Calculate waste percentage
    total_area = roll_width * roll_length
    used_area = sum(w * h for _, _, w, h in placements)
    waste_percentage = (total_area - used_area) / total_area * 100
    
    return placements, waste_percentage

def place_row(y, roll_width, roll_length, pieces):
    """
    Place pieces in a single row, including gap filling.
    
    Args:
        y (float): Starting y coordinate for the row
        roll_width (float): Width of the roll
        roll_length (float): Length of the roll
        pieces (list): Available pieces to place
    
    Returns:
        tuple: (placements, used_pieces, row_height) or None if no placement possible
    """
    if not pieces:
        return None
    
    placements = []
    current_x = 0
    row_height = 0
    used_pieces = 0
    
    # First pass: Place pieces horizontally
    while current_x < roll_width and used_pieces < len(pieces):
        width, length = pieces[used_pieces]
        
        # Check if piece fits horizontally
        if current_x + width <= roll_width:
            placements.append((current_x, y, width, length))
            row_height = max(row_height, length)
            current_x = current_x + width
            used_pieces += 1
        else:
            break
    
    if not placements:
        return None
    
    # Second pass: Fill gaps between horizontal pieces
    if len(placements) >= 2:
        for i in range(len(placements) - 1):
            current_piece = placements[i]
            next_piece = placements[i + 1]
            
            gap_start_x = current_piece[0] + current_piece[2]
            gap_width = next_piece[0] - gap_start_x
            
            # Try to fill gap with remaining pieces
            for j in range(used_pieces, len(pieces)):
                width, length = pieces[j]
                
                # Try vertical placement (rotated 90 degrees)
                if length <= gap_width and width <= row_height:
                    # Place piece vertically in gap
                    placements.append((gap_start_x, y, length, width))
                    # Swap this piece with the next unused piece
                    if j > used_pieces:
                        pieces[used_pieces], pieces[j] = pieces[j], pieces[used_pieces]
                    used_pieces += 1
                    break
                # Try other rotation
                elif width <= gap_width and length <= row_height:
                    # Place piece vertically in gap
                    placements.append((gap_start_x, y, width, length))
                    # Swap this piece with the next unused piece
                    if j > used_pieces:
                        pieces[used_pieces], pieces[j] = pieces[j], pieces[used_pieces]
                    used_pieces += 1
                    break
    
    return placements, used_pieces, row_height

def find_width_combination(pieces, target_width, tolerance=0.001):
    """Helper function to find pieces that combine to target width."""
    sorted_pieces = sorted(pieces, key=lambda x: x[0], reverse=True)
    result = []
    current_width = 0
    
    for piece in sorted_pieces:
        if current_width + piece[0] <= target_width + tolerance:
            result.append(piece)
            current_width += piece[0]
            if abs(current_width - target_width) <= tolerance:
                return result
    
    return []