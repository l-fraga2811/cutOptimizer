import numpy as np
from collections import defaultdict

def optimize_cutting(roll_width, roll_length, pieces, force_horizontal=False):
    """
    Optimize the cutting pattern for a roll of material.

    Args:
        roll_width (float): Width of the roll in cm
        roll_length (float): Length of the roll in cm
        pieces (list): List of tuples (width, length) for each piece in cm
        force_horizontal (bool): If True, forces pieces to be horizontal and cover full width

    Returns:
        tuple: (placements, waste_percentage)
            - placements: List of tuples (x, y, width, length) for each piece
            - waste_percentage: Percentage of material wasted
    """
    # If force_horizontal is True, we'll implement a different algorithm
    if force_horizontal:
        return optimize_horizontal_cutting(roll_width, roll_length, pieces)

    # Group identical pieces for more efficient handling
    piece_counts = defaultdict(int)
    for width, length in pieces:
        piece_counts[(width, length)] += 1

    # Convert to format that includes all information: (id, width, length, quantity, area)
    all_pieces = []
    for i, ((w, l), count) in enumerate(piece_counts.items()):
        all_pieces.append((i, w, l, count, w * l))

    # First, handle special combinations that maximize material usage
    placements = []
    used_positions = []  # List of (x, y, width, length)

    # Define the special combinations we want to handle
    special_combos = [
        # Peças 2 e 11 com peça 1
        [(120, 200), (30, 100), 2],   # Peça 1 com peças 2 e 11
        # Peças 4 e 6 com peça 3
        [(100, 150), (50, 75), 2],    # Peça 3 com peças 4 e 6
        # Peças 8 e 10 com peça 5
        [(80, 150), (40, 75), 2],     # Peça 5 com peças 8 e 10
        # Outras combinações originais
        [(70, 200), (80, 100), 2],
        [(150, 200), (150, 200), 1]
    ]

    # Sort pieces by length first, then width for better vertical stacking
    all_pieces.sort(key=lambda x: (x[2], x[1]), reverse=True)

    # Function to check if a position is already occupied
    def is_position_occupied(x, y, w, h):
        # Check if out of bounds
        if x < 0 or y < 0 or x + w > roll_width or y + h > roll_length:
            return True

        # Check for overlap with existing placements
        for px, py, pw, ph in used_positions:
            # Check if rectangles overlap
            if not (x + w <= px or px + pw <= x or y + h <= py or py + ph <= y):
                return True
        return False

    # Try to place these special combinations first
    for primary_size, secondary_size, secondary_count in special_combos:
        primary_width, primary_length = primary_size
        secondary_width, secondary_length = secondary_size

        # Check if we have these piece types
        primary_pieces = [(pid, w, l, q, a) for pid, w, l, q, a in all_pieces if w == primary_width and l == primary_length]
        secondary_pieces = [(pid, w, l, q, a) for pid, w, l, q, a in all_pieces if w == secondary_width and l == secondary_length]

        if primary_pieces and secondary_pieces:
            primary_id, _, _, primary_qty, _ = primary_pieces[0]
            secondary_id, _, _, secondary_qty, _ = secondary_pieces[0]

            # If we have enough pieces for this combo
            while primary_qty > 0 and secondary_qty >= secondary_count:
                # Try to find a valid placement for this combo
                placed = False
                for y in range(0, int(roll_length - primary_length) + 1):
                    for x in range(0, int(roll_width - primary_width - secondary_width) + 1):
                        # Check if we can place the entire combo
                        if (not is_position_occupied(x, y, primary_width, primary_length) and
                            not is_position_occupied(x + primary_width, y, secondary_width, secondary_length * secondary_count)):

                            # Place the primary piece
                            placements.append((x, y, primary_width, primary_length))
                            used_positions.append((x, y, primary_width, primary_length))

                            # Place the secondary pieces
                            for i in range(secondary_count):
                                placements.append((x + primary_width, y + i * secondary_length, 
                                                 secondary_width, secondary_length))
                                used_positions.append((x + primary_width, y + i * secondary_length, 
                                                     secondary_width, secondary_length))

                            # Update piece counts
                            primary_qty -= 1
                            secondary_qty -= secondary_count

                            # Update the master list
                            for i, (pid, w, l, q, a) in enumerate(all_pieces):
                                if pid == primary_id:
                                    all_pieces[i] = (pid, w, l, q-1, a)
                                if pid == secondary_id:
                                    all_pieces[i] = (pid, w, l, q-secondary_count, a)

                            placed = True
                            break
                    if placed:
                        break

                # If we couldn't place this combo, move on
                if not placed:
                    break

    # Sort pieces by area in descending order for more efficient packing
    all_pieces = [(pid, w, l, q, a) for pid, w, l, q, a in all_pieces if q > 0]
    all_pieces.sort(key=lambda x: x[4], reverse=True)

    # Store the dimensions of free spaces
    def find_free_spaces():
        # Start with the entire roll
        free_spaces = [(0, 0, roll_width, roll_length)]

        # For each placed piece, update the free spaces
        for px, py, pw, ph in used_positions:
            new_free_spaces = []

            for fx, fy, fw, fh in free_spaces:
                # If no overlap, keep the space
                if fx + fw <= px or px + pw <= fx or fy + fh <= py or py + ph <= fy:
                    new_free_spaces.append((fx, fy, fw, fh))
                    continue

                # Split into at most 4 new rectangles

                # Rectangle to the left of the piece
                if fx < px:
                    left_width = px - fx
                    new_free_spaces.append((fx, fy, left_width, fh))

                # Rectangle to the right of the piece
                if fx + fw > px + pw:
                    right_width = (fx + fw) - (px + pw)
                    new_free_spaces.append((px + pw, fy, right_width, fh))

                # Rectangle above the piece
                if fy < py:
                    top_height = py - fy
                    new_free_spaces.append((fx, fy, fw, top_height))

                # Rectangle below the piece
                if fy + fh > py + ph:
                    bottom_height = (fy + fh) - (py + ph)
                    new_free_spaces.append((fx, py + ph, fw, bottom_height))

            free_spaces = new_free_spaces

        # Filter out tiny spaces and merge overlapping ones
        min_dimension = 0.1  # Minimum useful dimension in cm
        filtered_spaces = []
        for x, y, w, h in free_spaces:
            if w >= min_dimension and h >= min_dimension:
                filtered_spaces.append((x, y, w, h))

        # Sort by area (largest first)
        filtered_spaces.sort(key=lambda s: s[2] * s[3], reverse=True)
        return filtered_spaces

    # First pass: Strip packing - fill each strip across the width
    current_height = 0
    while current_height < roll_length:
        # Find height of the current strip
        strip_placed = False
        strip_height = 0

        # Try to place pieces in strips across the width
        for piece_id, piece_width, piece_length, quantity, area in all_pieces:
            if quantity <= 0:
                continue

            current_width = 0
            while quantity > 0 and current_width + piece_width <= roll_width:
                # Try to place the piece without rotation
                if not is_position_occupied(current_width, current_height, piece_width, piece_length):
                    placements.append((current_width, current_height, piece_width, piece_length))
                    used_positions.append((current_width, current_height, piece_width, piece_length))

                    # Update strip height
                    strip_height = max(strip_height, piece_length)
                    strip_placed = True

                    # Update position and quantity
                    current_width += piece_width
                    quantity -= 1

                    # Update the piece count in all_pieces
                    for i, (pid, w, l, q, a) in enumerate(all_pieces):
                        if pid == piece_id:
                            all_pieces[i] = (pid, w, l, q-1, a)
                            break
                else:
                    # Try with increments
                    current_width += 1

        if strip_placed:
            current_height += strip_height
        else:
            # No pieces placed in this strip, try a different approach
            break

    # Second pass: Maximal rectangles - fill remaining spaces efficiently
    remaining_pieces = [(pid, w, l, q, a) for pid, w, l, q, a in all_pieces if q > 0]

    # Sort by area (largest first)
    remaining_pieces.sort(key=lambda x: x[4], reverse=True)

    # For each piece, try to find a free space that fits
    for piece_id, piece_width, piece_length, quantity, area in remaining_pieces:
        for _ in range(quantity):
            # Find all free spaces
            free_spaces = find_free_spaces()
            placed = False

            for space_x, space_y, space_width, space_height in free_spaces:
                # Try without rotation
                if piece_width <= space_width and piece_length <= space_height:
                    placements.append((space_x, space_y, piece_width, piece_length))
                    used_positions.append((space_x, space_y, piece_width, piece_length))
                    placed = True
                    break

                # Tentar rotação considerando o melhor aproveitamento do espaço
                if piece_length <= space_width and piece_width <= space_height:
                    # Calcular o espaço restante em ambas as orientações
                    waste_normal = (space_width * space_height) - (piece_width * piece_length)
                    waste_rotated = (space_width * space_height) - (piece_length * piece_width)

                    # Escolher a orientação que minimiza o desperdício
                    if waste_rotated < waste_normal:
                        placements.append((space_x, space_y, piece_length, piece_width))
                        used_positions.append((space_x, space_y, piece_length, piece_width))
                    else:
                        placements.append((space_x, space_y, piece_width, piece_length))
                        used_positions.append((space_x, space_y, piece_width, piece_length))
                    placed = True
                    break

            # If we couldn't place the piece in any free space, try bottom-left packing
            if not placed:
                best_x, best_y = float('inf'), float('inf')
                best_rotated = False

                # Try without rotation
                for y in range(0, int(roll_length - piece_length) + 1):
                    for x in range(0, int(roll_width - piece_width) + 1):
                        if not is_position_occupied(x, y, piece_width, piece_length):
                            if y < best_y or (y == best_y and x < best_x):
                                best_x, best_y = x, y
                                best_rotated = False
                                break
                    if best_x != float('inf'):
                        break

                # Try with rotation
                for y in range(0, int(roll_length - piece_width) + 1):
                    for x in range(0, int(roll_width - piece_length) + 1):
                        if not is_position_occupied(x, y, piece_length, piece_width):
                            if y < best_y or (y == best_y and x < best_x):
                                best_x, best_y = x, y
                                best_rotated = True
                                break
                    if best_x != float('inf'):
                        break

                # If a valid position was found, place the piece
                if best_x != float('inf'):
                    if best_rotated:
                        placements.append((best_x, best_y, piece_length, piece_width))
                        used_positions.append((best_x, best_y, piece_length, piece_width))
                    else:
                        placements.append((best_x, best_y, piece_width, piece_length))
                        used_positions.append((best_x, best_y, piece_width, piece_length))

    # Verificar consistência: Não queremos mais peças do que o especificado
    # Vamos verificar se não excedemos as quantidades de peças originais

    # Contabilizar quantas peças colocamos de cada tipo
    pieces_placed = defaultdict(int)
    for x, y, w, l in placements:
        pieces_placed[(w, l)] += 1

    # Verificar se excedemos a quantidade original de peças
    original_pieces = {}
    for width, length in pieces:
        key = (width, length)
        if key in original_pieces:
            original_pieces[key] += 1
        else:
            original_pieces[key] = 1

    # Remover peças excedentes
    excess_placements = []
    for (w, l), count in pieces_placed.items():
        original_count = original_pieces.get((w, l), 0)
        if count > original_count:
            # Quantas peças excedentes temos
            excess = count - original_count
            excess_indices = []

            # Encontrar índices das peças excedentes
            for i, (x, y, width, length) in enumerate(placements):
                if width == w and length == l:
                    excess_indices.append(i)

            # Remover as peças excedentes (da parte final da lista)
            excess_indices = excess_indices[-excess:]

            for i in sorted(excess_indices, reverse=True):
                excess_placements.append(placements[i])
                del placements[i]

    # Verificar se ainda temos mais peças do tipo secundário do que deveríamos
    for (w, l), count in pieces_placed.items():
        # Recalcular a contagem após remoções
        current_count = sum(1 for x, y, width, length in placements if width == w and length == l)
        original_count = original_pieces.get((w, l), 0)

        if current_count > original_count:
            excess = current_count - original_count
            for _ in range(excess):
                for i, (x, y, width, length) in enumerate(placements):
                    if width == w and length == l:
                        del placements[i]
                        break

    # Calculate waste percentage
    total_area = roll_width * roll_length
    used_area = sum(p[2] * p[3] for p in placements)
    waste_percentage = (total_area - used_area) / total_area * 100

    return placements, waste_percentage

def optimize_horizontal_cutting(roll_width, roll_length, pieces):
    """
    Optimize cutting with pieces placed horizontally across the roll.
    Pieces can be rotated but not resized.

    Args:
        roll_width (float): Width of the roll in cm
        roll_length (float): Length of the roll in cm
        pieces (list): List of tuples (width, length) for each piece in cm

    Returns:
        tuple: (placements, waste_percentage)
    """
    # Create a copy of pieces
    pieces_copy = [(w, l) for w, l in pieces]

    # Sort pieces by area (largest first) to prioritize larger pieces
    pieces_copy.sort(key=lambda x: x[0] * x[1], reverse=True)

    # Initialize placements and current y position
    placements = []
    current_y = 0

    # Keep track of used positions
    used_positions = []

    # Function to check if a position is already occupied
    def is_position_occupied(x, y, w, h):
        # Check if out of bounds
        if x < 0 or y < 0 or x + w > roll_width or y + h > roll_length:
            return True

        # Check for overlap with existing placements
        for px, py, pw, ph in used_positions:
            # Check if rectangles overlap
            if not (x + w <= px or px + pw <= x or y + h <= py or py + ph <= y):
                return True
        return False

    # Process each piece
    for width, length in pieces_copy:
        # Try to place the piece in its original orientation
        placed = False

        # Try original orientation (horizontal)
        if width <= roll_width:
            for y in range(0, int(roll_length - length) + 1):
                for x in range(0, int(roll_width - width) + 1):
                    if not is_position_occupied(x, y, width, length):
                        placements.append((x, y, width, length))
                        used_positions.append((x, y, width, length))
                        placed = True
                        break
                if placed:
                    break

        # If not placed, try rotated orientation (still horizontal)
        if not placed and length <= roll_width:
            for y in range(0, int(roll_length - width) + 1):
                for x in range(0, int(roll_width - length) + 1):
                    if not is_position_occupied(x, y, length, width):
                        placements.append((x, y, length, width))
                        used_positions.append((x, y, length, width))
                        placed = True
                        break
                if placed:
                    break

    # Calculate waste percentage
    total_area = roll_width * roll_length
    used_area = sum(p[2] * p[3] for p in placements)
    waste_percentage = (total_area - used_area) / total_area * 100

    return placements, waste_percentage

def find_width_combination(pieces, target_width, tolerance=0.001):
    """
    Find a combination of pieces that exactly fills the target width.

    Args:
        pieces (list): List of (width, length) tuples
        target_width (float): Target width to fill
        tolerance (float): Tolerance for width matching

    Returns:
        list: List of (width, length) pieces that fill the width, or empty list if no solution
    """
    # Try with original orientation first
    result = find_subset_sum(pieces, target_width, tolerance)
    if result:
        return result

    # Try with rotated pieces
    rotated_pieces = [(l, w) for w, l in pieces]
    result = find_subset_sum(rotated_pieces, target_width, tolerance)
    if result:
        return result

    # Try with mixed orientations (original and rotated)
    all_orientations = []
    for w, l in pieces:
        all_orientations.append((w, l))  # Original
        all_orientations.append((l, w))  # Rotated

    return find_subset_sum(all_orientations, target_width, tolerance)

def find_subset_sum(pieces, target_sum, tolerance=0.001):
    """
    Find a subset of pieces whose widths sum to the target.
    Uses a greedy approach for efficiency.

    Args:
        pieces (list): List of (width, length) tuples
        target_sum (float): Target sum to achieve
        tolerance (float): Tolerance for sum matching

    Returns:
        list: List of (width, length) pieces that sum to target, or empty list if no solution
    """
    # Sort pieces by width (largest first)
    sorted_pieces = sorted(pieces, key=lambda x: x[0], reverse=True)

    # Try to find exact combinations
    current_sum = 0
    current_pieces = []

    for piece in sorted_pieces:
        width, _ = piece
        if current_sum + width <= target_sum + tolerance:
            current_pieces.append(piece)
            current_sum += width

            # Check if we've reached the target
            if abs(current_sum - target_sum) <= tolerance:
                return current_pieces

    # If we get here, no exact solution was found
    return []