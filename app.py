import streamlit as st
import numpy as np
import pandas as pd
from optimizer import optimize_cutting
from visualizer import visualize_cutting_pattern

st.set_page_config(
    page_title="Material Cutting Optimizer",
    page_icon="✂️",
    layout="wide"
)

st.title("✂️ Material Cutting Optimizer")
st.markdown("""
This tool helps you maximize material usage by calculating optimal cutting patterns
for films, sheets, or any rectangular material.
""")

# Sidebar for inputs
with st.sidebar:
    st.header("Roll Specifications")
    unit = st.selectbox("Unit", ["meters", "centimeters"], index=0)
    
    # Determine conversion factor
    conversion = 100 if unit == "meters" else 1  # Convert to cm internally
    
    roll_width = st.number_input(
        f"Roll Width ({unit})", 
        min_value=0.001 if unit == "meters" else 0.1,
        max_value=10.0 if unit == "meters" else 1000.0,
        value=1.52 if unit == "meters" else 152.0,
        step=0.001 if unit == "meters" else 0.1,
        format="%.3f" if unit == "meters" else "%.1f"
    )
    
    roll_length = st.number_input(
        f"Roll Length ({unit})",
        min_value=0.001 if unit == "meters" else 0.1,
        max_value=100.0 if unit == "meters" else 10000.0,
        value=30.0 if unit == "meters" else 3000.0, 
        step=0.001 if unit == "meters" else 0.1,
        format="%.3f" if unit == "meters" else "%.1f"
    )
    
    # Convert to cm for internal calculations
    roll_width_cm = roll_width * conversion
    roll_length_cm = roll_length * conversion
    
    st.header("Piece Specifications")
    st.markdown("Add the pieces you need to cut from the roll")

# Initialize session state for pieces
if 'pieces' not in st.session_state:
    st.session_state.pieces = []

# Add piece form
with st.sidebar:
    with st.form(key="add_piece"):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            piece_width = st.number_input(
                f"Width ({unit})", 
                min_value=0.001 if unit == "meters" else 0.1,
                max_value=roll_width,
                value=0.5 if unit == "meters" else 50.0,
                step=0.001 if unit == "meters" else 0.1,
                format="%.3f" if unit == "meters" else "%.1f"
            )
        
        with col2:
            piece_length = st.number_input(
                f"Length ({unit})", 
                min_value=0.001 if unit == "meters" else 0.1,
                max_value=roll_length,
                value=0.5 if unit == "meters" else 50.0,
                step=0.001 if unit == "meters" else 0.1,
                format="%.3f" if unit == "meters" else "%.1f"
            )
        
        with col3:
            quantity = st.number_input(
                "Quantity", 
                min_value=1, 
                value=1, 
                step=1
            )
        
        submit_button = st.form_submit_button(label="Add Piece")
        
        if submit_button:
            # Convert to cm if needed
            width_cm = piece_width * conversion
            length_cm = piece_length * conversion
            
            if width_cm > roll_width_cm or length_cm > roll_length_cm:
                st.error("Piece dimensions cannot exceed roll dimensions!")
            else:
                st.session_state.pieces.append({
                    "width": width_cm,
                    "length": length_cm,
                    "quantity": quantity,
                    "width_display": piece_width,
                    "length_display": piece_length,
                    "unit": unit
                })
                st.success("Piece added!")
                st.rerun()

# Main content area
col1, col2 = st.columns([1, 2])

# Display pieces table
with col1:
    if st.session_state.pieces:
        st.subheader("Pieces to Cut")
        
        # Create a DataFrame for display
        pieces_data = []
        for i, piece in enumerate(st.session_state.pieces):
            pieces_data.append({
                "Piece #": i + 1,
                "Width": f"{piece['width_display']} {piece['unit']}",
                "Length": f"{piece['length_display']} {piece['unit']}",
                "Quantity": piece['quantity']
            })
        
        df = pd.DataFrame(pieces_data)
        st.dataframe(df, use_container_width=True)
        
        if st.button("Clear All Pieces"):
            st.session_state.pieces = []
            st.rerun()
        
        if st.button("Remove Last Piece"):
            if st.session_state.pieces:
                st.session_state.pieces.pop()
                st.rerun()
    else:
        st.info("Add pieces to get started")

# Run optimization and show results
with col2:
    if st.session_state.pieces:
        # Prepare data for optimization
        pieces_for_optimizer = []
        for piece in st.session_state.pieces:
            for _ in range(piece["quantity"]):
                pieces_for_optimizer.append((piece["width"], piece["length"]))
        
        if st.button("Run Optimization"):
            with st.spinner("Calculating optimal cutting pattern..."):
                try:
                    placements, waste_percentage = optimize_cutting(
                        roll_width_cm, roll_length_cm, pieces_for_optimizer,
                        force_horizontal=True
                    )
                    
                    # Create a metrics display
                    cols = st.columns(3)
                    with cols[0]:
                        st.metric(
                            "Material Utilization", 
                            f"{100 - waste_percentage:.3f}%",
                            f"-{waste_percentage:.3f}% waste"
                        )
                    
                    with cols[1]:
                        total_pieces = len(pieces_for_optimizer)
                        placed_pieces = len(placements)
                        st.metric(
                            "Pieces Placed",
                            f"{placed_pieces}/{total_pieces}",
                            f"{placed_pieces/total_pieces*100:.1f}% of pieces" if total_pieces > 0 else "0%"
                        )
                    
                    with cols[2]:
                        total_area = roll_width_cm * roll_length_cm
                        waste_area = (total_area - sum(p[2] * p[3] for p in placements)) / conversion**2
                        st.metric(
                            f"Waste Area ({unit}²)",
                            f"{waste_area:.3f}",
                            f"{waste_area/(total_area/conversion**2)*100:.1f}% of total area"
                        )
                    
                    # Visualize
                    fig = visualize_cutting_pattern(
                        roll_width_cm, roll_length_cm, placements, unit
                    )
                    st.pyplot(fig)
                    
                    # Group identical pieces for more organized cutting instructions
                    from collections import defaultdict
                    piece_groups = defaultdict(list)
                    
                    for i, (x, y, w, h) in enumerate(placements):
                        piece_groups[(w, h)].append((i, x, y))
                    
                    # Display cutting instructions
                    st.subheader("Cutting Instructions")
                    
                    # Show summary table first
                    summary_data = []
                    piece_id = 1
                    
                    for (width, height), positions in piece_groups.items():
                        summary_data.append({
                            "Type": f"Type {piece_id}",
                            "Width": f"{width/conversion:.3f} {unit}",
                            "Length": f"{height/conversion:.3f} {unit}",
                            "Quantity": len(positions),
                            "Area": f"{(width*height)/(conversion**2):.3f} {unit}²"
                        })
                        piece_id += 1
                    
                    if summary_data:
                        st.markdown("#### Piece Types Summary")
                        st.dataframe(pd.DataFrame(summary_data), use_container_width=True)
                    
                    # Show detailed placement instructions
                    instructions_data = []
                    
                    for i, (x, y, w, h) in enumerate(placements):
                        instructions_data.append({
                            "Piece #": i + 1,
                            "Position X": f"{x/conversion:.3f} {unit}",
                            "Position Y": f"{y/conversion:.3f} {unit}",
                            "Width": f"{w/conversion:.3f} {unit}",
                            "Length": f"{h/conversion:.3f} {unit}"
                        })
                    
                    if instructions_data:
                        st.markdown("#### Detailed Placement Coordinates")
                        st.dataframe(pd.DataFrame(instructions_data), use_container_width=True)
                    else:
                        st.warning("No pieces could be placed on the roll.")
                    
                    # Unplaced pieces
                    unplaced = len(pieces_for_optimizer) - len(placements)
                    if unplaced > 0:
                        st.error(f"❗ {unplaced} pieces couldn't be placed on the roll. Consider using a larger roll or adjusting piece dimensions.")
                
                except Exception as e:
                    st.error(f"An error occurred: {str(e)}")
    else:
        st.info("Add pieces and click 'Run Optimization' to calculate the optimal cutting pattern")

# Add help information
st.sidebar.markdown("---")
with st.sidebar.expander("How to use this tool"):
    st.markdown("""
    1. Specify the roll dimensions (width and length)
    2. Add the pieces you need to cut with their dimensions and quantities
    3. Click "Run Optimization" to calculate the optimal cutting pattern
    4. Review the cutting pattern visualization and instructions
    
    **Notes:**
    - All pieces must be smaller than the roll dimensions
    - Pieces will be placed to minimize waste
    - The algorithm prioritizes larger pieces first
    """)
