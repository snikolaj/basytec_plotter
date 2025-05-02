# graph_gen/generate_plots.py
import pandas as pd
import matplotlib.pyplot as plt
import os
import numpy as np # Import numpy for checking numeric types

def add_command_highlights(axes, df, highlight_commands, label_highlights=False):
    """
    Adds vertical background highlights and optional, potentially overlapping labels
    to axes based on DataFrame commands. Labels are attempted for all durations
    and placed at a fixed vertical position.

    Args:
        axes (list): A list of matplotlib axes objects to draw on.
        df (pd.DataFrame): DataFrame containing 'Time[h]' and 'Command' columns.
        highlight_commands (dict): Dictionary mapping command strings to color strings
                                  (e.g., {'charge': 'lightcoral'}).
        label_highlights (bool): If True, adds the command name as text onto the
                                 highlighted region on the first subplot. Defaults to False.
    """
    if not highlight_commands or df.empty:
         if not label_highlights and highlight_commands and not df.empty:
             pass
         else:
            return

    if 'Command' not in df.columns:
        print("Warning: 'Command' column not found, cannot add command highlights.")
        return
    if not pd.api.types.is_numeric_dtype(df['Time[h]']):
         print("Warning: 'Time[h]' column is not numeric, cannot add command highlights.")
         return

    df_reset = df.reset_index()

    ax_for_labels = axes[0]
    ymin, ymax = ax_for_labels.get_ylim()

    # Define a single vertical position for labels
    label_y_position = ymax - (ymax - ymin) * 0.05 # Position near the top (95% mark)

    # --- Pass 1: Draw all highlights ---
    for command, color in highlight_commands.items():
        start_time = None
        for i in range(len(df_reset)):
            time = df_reset.loc[i, 'Time[h]']
            current_command = str(df_reset.loc[i, 'Command'])
            is_target = (current_command == command)

            if is_target and start_time is None: start_time = time

            if (not is_target or i == len(df_reset) - 1) and start_time is not None:
                end_time = time
                for ax in axes:
                    ax.axvspan(start_time, end_time, color=color, alpha=0.3, zorder=-1, label=f'_{command}_highlight')
                if not is_target: start_time = None

    # --- Pass 2: Add labels if enabled ---
    if label_highlights:
        sorted_commands = sorted(highlight_commands.keys())

        for command in sorted_commands:
            start_time = None
            for i in range(len(df_reset)):
                time = df_reset.loc[i, 'Time[h]']
                current_command = str(df_reset.loc[i, 'Command'])
                is_target = (current_command == command)

                if is_target and start_time is None: start_time = time

                if (not is_target or i == len(df_reset) - 1) and start_time is not None:
                    end_time = time
                    span_duration = end_time - start_time

                    # Add text label if span has *any* positive duration
                    if span_duration > 0:
                        text_x_position = start_time + span_duration / 2

                        # Use the single fixed vertical position
                        ax_for_labels.text(text_x_position, label_y_position, command,
                                            ha='center', va='center', fontsize=8, color='black',
                                            clip_on=True, bbox=dict(boxstyle='round,pad=0.1', fc='white', alpha=0.5, ec='none'))

                    if not is_target: start_time = None


def add_vertical_markers(axes, df, column_name, marker_options):
    """
    Adds vertical lines to axes when the value in a specified column changes.

    Args:
        axes (list): A list of matplotlib axes objects to draw on.
        df (pd.DataFrame): DataFrame containing 'Time[h]' and the column_name.
        column_name (str): The name of the column to watch for changes.
        marker_options (dict): Dictionary with line style options for axvline
                               (e.g., {'color': 'red', 'linestyle': '--', 'linewidth': 1}).
                               Must include at least 'color'.
    """
    if df.empty or column_name not in df.columns:
        print(f"Warning: Column '{column_name}' not found or DataFrame empty, cannot add vertical markers.")
        return
    if not pd.api.types.is_numeric_dtype(df['Time[h]']):
         print(f"Warning: 'Time[h]' column is not numeric, cannot add {column_name} markers.")
         return

    last_value = None
    # Use reset_index to ensure standard integer index for iloc
    df_reset = df.reset_index()
    for i in range(len(df_reset)):
        current_value = df_reset.loc[i, column_name]
        current_time = df_reset.loc[i, 'Time[h]']
        # Check for change (and skip the very first point)
        if i > 0 and current_value != last_value:
            # Add a vertical line on all axes
            for ax in axes:
                ax.axvline(current_time, label=f'_{column_name}_change_at_{i}', **marker_options) # Use ** to unpack style options
        last_value = current_value


# --- Default Basytec Column Order ---
# Define this outside the function so it can be used as a default
DEFAULT_BASYTEC_COLUMNS = [
    'Time[h]', 'DataSet', 't-Step[h]', 't-Set[h]', 'Line', 'Command',
    'U[V]', 'I[A]', 'Ah[Ah]', 'Ah-Step', 'Wh[Wh]', 'Wh-Step',
    'T1[C]', 'Cyc-Count', 'State'
]

def generate_basytec_plots(input_filepath,
                           output_dir='.',
                           output_filename='basytec_plot.pdf',
                           dpi=300,
                           columns_to_plot=None,
                           highlight_commands=None,
                           label_highlighted_commands=False,
                           basytec_column_names=None, # <-- New parameter for column names
                           mark_state_changes=None,
                           mark_cycle_changes=None,
                           mark_dataset_changes=None
                           ):
    """
    Generates plots from Basytec data files with optional customizations.

    Reads a semicolon-separated data file, ignoring lines starting with '~', using a specified
    or default column name list. Creates subplots for specified variables vs. Time.
    Optionally adds background highlights for specified commands, potentially with labels.
    Optionally adds vertical lines marking changes in State, Cycle Count, or DataSet.
    Saves the combined plot as a PDF file.

    Args:
        input_filepath (str): Path to the Basytec input data file.
        output_dir (str): Directory to save the output plot file.
        output_filename (str): Name for the output PDF file.
        dpi (int): Resolution for the saved plot.
        columns_to_plot (list of dict, optional): List defining which columns to plot.
            See example usage for format. Defaults to plotting 'U[V]', 'I[A]', 'T1[C]'.
        highlight_commands (dict, optional): Dictionary mapping command strings to color strings
            for background highlighting. See example usage below.
        label_highlighted_commands (bool): If True, adds command names as text labels on top
            of the highlighted regions (on the first subplot). Defaults to False.
        basytec_column_names (list, optional): The exact list of column names corresponding
            to the fields in the Basytec file. If None, uses DEFAULT_BASYTEC_COLUMNS.
        mark_state_changes (dict, optional): If provided, draws vertical lines when 'State' column changes.
            Dict contains axvline style options (e.g., {'color': 'red', 'linestyle': '--'}).
        mark_cycle_changes (dict, optional): If provided, draws vertical lines when 'Cyc-Count' column changes.
            Dict contains axvline style options (e.g., {'color': 'purple', 'linestyle': ':'}).
        mark_dataset_changes (dict, optional): If provided, draws vertical lines when 'DataSet' column changes.
            Dict contains axvline style options (e.g., {'color': 'cyan', 'linestyle': '-.'}).
    """
    try:
        # --- Use provided column names or default ---
        if basytec_column_names is None:
            basytec_column_names = DEFAULT_BASYTEC_COLUMNS

        # --- Default Plot Configuration ---
        if columns_to_plot is None:
            # Check if default columns exist in the (potentially custom) column name list
            default_plot_cols_to_use = []
            for default_col_info in [
                {'column': 'U[V]', 'label': 'Voltage (V)', 'color': 'blue'},
                {'column': 'I[A]', 'label': 'Current (A)', 'color': 'orange'},
                {'column': 'T1[C]', 'label': 'Temperature (°C)', 'color': 'green'}
            ]:
                if default_col_info['column'] in basytec_column_names:
                    default_plot_cols_to_use.append(default_col_info)
            if not default_plot_cols_to_use:
                 print("Warning: Default columns U[V], I[A], T1[C] not found in provided basytec_column_names. No columns specified to plot.")
                 # Decide if you want to raise an error or just return an empty plot
                 return
            columns_to_plot = default_plot_cols_to_use


        # --- Read Data ---
        df = pd.read_csv(
            input_filepath,
            sep=';',
            comment='~',
            header=None,
            names=basytec_column_names, # Use the provided or default list
            encoding='latin1',
            low_memory=False
        )

        # --- Data Cleaning & Validation ---
        needed_cols = ['Time[h]'] + [p['column'] for p in columns_to_plot]
        # Add columns needed for optional features, checking if they exist in the provided list
        if highlight_commands and 'Command' in basytec_column_names: needed_cols.append('Command')
        if mark_state_changes and 'State' in basytec_column_names: needed_cols.append('State')
        if mark_cycle_changes and 'Cyc-Count' in basytec_column_names: needed_cols.append('Cyc-Count')
        if mark_dataset_changes and 'DataSet' in basytec_column_names: needed_cols.append('DataSet')
        needed_cols = list(set(needed_cols))

        # Check if all needed columns *actually exist* in the loaded DataFrame
        # (This handles cases where the provided basytec_column_names list might be wrong)
        missing_cols = [col for col in needed_cols if col not in df.columns]
        if missing_cols:
            print(f"Error: DataFrame loaded from {input_filepath} is missing columns required for requested plots/features: {missing_cols}")
            print(f"Columns available in DataFrame after loading: {df.columns.tolist()}")
            print(f"Column names expected based on basytec_column_names parameter: {basytec_column_names}")
            return

        # Convert numeric columns, coercing errors
        numeric_plot_cols = ['Time[h]'] + [p['column'] for p in columns_to_plot]
        for col in numeric_plot_cols:
            # Check column exists before conversion
            if col in df.columns:
                 df[col] = pd.to_numeric(df[col], errors='coerce')
            else:
                 print(f"Warning: Column '{col}' specified for plotting not found in DataFrame.")
                 # Handle missing plot column - maybe remove it from columns_to_plot?
                 # For now, let dropna handle it later if conversion wasn't possible.

        # Drop rows where essential numeric plotting data or time is missing
        valid_numeric_cols = [col for col in numeric_plot_cols if col in df.columns] # Only check cols that actually exist
        if valid_numeric_cols:
            df.dropna(subset=valid_numeric_cols, inplace=True)
        else:
            print(f"Error: No valid numeric columns found to plot in {input_filepath}.")
            return


        # Strip potential whitespace from Command column if used and exists
        if 'Command' in df.columns and highlight_commands:
            df['Command'] = df['Command'].astype(str).str.strip()

        # Check if DataFrame is empty after cleaning
        if df.empty:
            print(f"Error: DataFrame is empty after cleaning data from {input_filepath}. Check filters or numeric conversions.")
            return

        # --- Plotting Setup ---
        num_plots = len(columns_to_plot)
        if num_plots == 0:
             print(f"Warning: No columns left to plot for {input_filepath}. Skipping plot generation.")
             return
        fig, axes = plt.subplots(num_plots, 1, figsize=(10, 4 * num_plots), sharex=True)
        if num_plots == 1:
            axes = [axes] # Ensure axes is always iterable

        # --- Create Plots ---
        for i, plot_info in enumerate(columns_to_plot):
            col_name = plot_info['column']
            label = plot_info['label']
            color = plot_info.get('color', None)
            # Ensure the column actually exists before plotting
            if col_name in df.columns:
                axes[i].plot(df['Time[h]'], df[col_name], label=col_name, color=color)
                axes[i].set_ylabel(label)
                axes[i].grid(True)
                axes[i].legend()
            else:
                 print(f"Internal Warning: Skipped plotting '{col_name}' as it was not found post-cleaning.")


        # Add overall title and xlabel (These lines are now unconditional if num_plots > 0)
        axes[0].set_title(f'Basytec Data Analysis: {os.path.basename(input_filepath)}')
        axes[-1].set_xlabel('Time (h)')

        # --- Add Optional Features ---
        # Check if required columns exist before calling helpers
        if highlight_commands and 'Command' in df.columns:
            add_command_highlights(
                axes, df, highlight_commands,
                label_highlights=label_highlighted_commands
            )
        elif highlight_commands:
             print("Warning: Cannot add command highlights because 'Command' column is missing.")

        if mark_state_changes and 'State' in df.columns:
            add_vertical_markers(axes, df, 'State', mark_state_changes)
        elif mark_state_changes:
             print("Warning: Cannot mark state changes because 'State' column is missing.")

        if mark_cycle_changes and 'Cyc-Count' in df.columns:
            add_vertical_markers(axes, df, 'Cyc-Count', mark_cycle_changes)
        elif mark_cycle_changes:
             print("Warning: Cannot mark cycle changes because 'Cyc-Count' column is missing.")

        if mark_dataset_changes and 'DataSet' in df.columns:
            add_vertical_markers(axes, df, 'DataSet', mark_dataset_changes)
        elif mark_dataset_changes:
             print("Warning: Cannot mark dataset changes because 'DataSet' column is missing.")


        # --- Final Touches ---
        # These lines are now unconditional if num_plots > 0
        plt.tight_layout(rect=[0, 0.03, 1, 0.97])

        os.makedirs(output_dir, exist_ok=True)
        output_filepath = os.path.join(output_dir, output_filename)
        plt.savefig(output_filepath, dpi=dpi, bbox_inches='tight')
        plt.close(fig) # Close the figure to free memory
        print(f"Plot saved successfully to {output_filepath}")


    except FileNotFoundError:
        print(f"Error: Input file not found at {input_filepath}")
    except pd.errors.EmptyDataError:
        print(f"Error: Input file {input_filepath} is empty or contains only comments.")
    except Exception as e:
        print(f"An unexpected error occurred while processing {input_filepath}: {e}")
        import traceback
        traceback.print_exc()

# --- Example Usage ---
if __name__ == "__main__":
    data_file = 'Example Data For Testing Graphs.txt'
    output_directory = 'graph_gen/generated_graphs'

    # --- Example using default column names and plotting V, I ---
    output_name_vi = 'volt_current_plot.pdf'
    print(f"\nGenerating V/I plot (default columns): {output_name_vi}")
    generate_basytec_plots(
        input_filepath=data_file,
        output_dir=output_directory,
        output_filename=output_name_vi,
        columns_to_plot=[ # Override default plots
             {'column': 'U[V]', 'label': 'Voltage (V)', 'color': 'blue'},
             {'column': 'I[A]', 'label': 'Current (A)', 'color': 'orange'}
        ],
        # basytec_column_names=None, # Explicitly use default
        label_highlighted_commands=False
    )


    # --- Example using custom column names and plotting Voltage only w/ labels ---
    # Assume your file *actually* had columns like this:
    custom_basytec_cols = [
        'Time_Hours', 'SetNum', 'Step_Time', 'Set_Time', 'Row', 'Action',
        'Voltage', 'Current', 'Capacity_Ah', 'Cap_Step', 'Energy_Wh', 'Eng_Step',
        'Temp1', 'Cycle', 'Mode'
    ]
    # We will use the *default* columns here since the example file uses them,
    # but this shows how you would pass a custom list if needed.
    # If you had a file matching custom_basytec_cols, you would uncomment the
    # basytec_column_names line below and adjust columns_to_plot accordingly.

    custom_plot_cols = [
        {'column': 'U[V]', 'label': 'Cell Voltage (V)', 'color': 'navy'}
    ]

    custom_highlights = {
        'charge': 'lightcoral',
        'Discharge': 'lightgreen'
    }

    output_name_custom_cols = 'custom_cols_volt_labels.pdf'
    print(f"\nGenerating custom plot (demonstrates custom cols param): {output_name_custom_cols}")
    generate_basytec_plots(
        input_filepath=data_file,
        output_dir=output_directory,
        output_filename=output_name_custom_cols,
        columns_to_plot=custom_plot_cols,
        highlight_commands=custom_highlights,
        label_highlighted_commands=True,
        basytec_column_names=None # Using None here to run with example file, replace with custom_basytec_cols if needed
        # If using custom_basytec_cols list above, pass it here:
        # basytec_column_names=custom_basytec_cols
    )

    # --- Basic Example (No labels, default columns V, I, T) ---
    output_name_basic = 'basic_plot.pdf'
    print(f"\nGenerating basic plot: {output_name_basic}")
    generate_basytec_plots(
        input_filepath=data_file,
        output_dir=output_directory,
        output_filename=output_name_basic
        # Uses default columns_to_plot and default basytec_column_names
    )
