# graph_gen/generate_plots.py
import pandas as pd
import matplotlib.pyplot as plt
import os

def generate_basytec_plots(input_filepath, output_dir='.', output_filename='basytec_plot.pdf', dpi=300):
    """
    Generates plots from Basytec data files.

    Reads a semicolon-separated data file, ignoring lines starting with '~'.
    Creates two subplots: Voltage vs. Time and Current vs. Time.
    Saves the combined plot as a PDF file.

    Args:
        input_filepath (str): Path to the Basytec input data file.
        output_dir (str): Directory to save the output plot file. Defaults to current directory.
        output_filename (str): Name for the output PDF file. Defaults to 'basytec_plot.pdf'.
        dpi (int): Resolution for the saved plot. Defaults to 300.
    """
    try:
        # Define column names based on the given format: Time[h];DataSet;t-Step[h];t-Set[h];Line;Command;U[V];I[A];Ah[Ah];Ah-Step;Wh[Wh];Wh-Step;T1[C];Cyc-Count;State
        # The column format with results is <name>[<unit>]
        column_names = [
            'Time[h]', 'DataSet', 't-Step[h]', 't-Set[h]', 'Line', 'Command',
            'U[V]', 'I[A]', 'Ah[Ah]', 'Ah-Step', 'Wh[Wh]', 'Wh-Step',
            'T1[C]', 'Cyc-Count', 'State'
        ]

        # Read the data file using pandas
        # Skip lines starting with '~' (commented lines), specify no header, and provide column names
        # Specify encoding as 'latin1' to handle special characters
        df = pd.read_csv(
            input_filepath,
            sep=';',
            comment='~',
            header=None, # Indicate that the file has no header row
            names=column_names, # Provide the list of column names
            encoding='latin1'
        )

        # Basic check if expected columns are present
        required_cols = ['Time[h]', 'U[V]', 'I[A]']
        if not all(col in df.columns for col in required_cols):
            print(f"Error: DataFrame is missing one or more required columns: {required_cols}")
            print(f"Available columns: {df.columns.tolist()}")
            return

        # Create the figure and axes for subplots
        fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(10, 12), sharex=True) # Share x-axis (Time)

        # Plot Voltage vs. Time on the first subplot
        ax1.plot(df['Time[h]'], df['U[V]'], label='Voltage')
        ax1.set_ylabel('Voltage (V)')
        ax1.grid(True)
        ax1.legend()
        ax1.set_title('Basytec Data Analysis') # Overall title for the figure

        # Plot Current vs. Time on the second subplot
        ax2.plot(df['Time[h]'], df['I[A]'], label='Current', color='orange')
        ax2.set_xlabel('Time (h)')
        ax2.set_ylabel('Current (A)')
        ax2.grid(True)
        ax2.legend()

        # Plot Temperature vs. Time on the third subplot
        ax3.plot(df['Time[h]'], df['T1[C]'], label='Temperature', color='green')
        ax3.set_xlabel('Time (h)')
        ax3.set_ylabel('Temperature (C)')
        ax3.grid(True)
        ax3.legend()

        # Follow this format for additional plots
        # ax4.plot(df['Time[h]'], df['T2[C]'], label='Temperature', color='red')
        # ax4.set_xlabel('Time (h)')
        # ax4.set_ylabel('Temperature (C)')
        # ax4.grid(True)
        # ax4.legend()

        # Adjust layout to prevent overlap
        plt.tight_layout(rect=[0, 0, 1, 0.97]) # Adjust rect to make space for the main title

        # Ensure output directory exists
        os.makedirs(output_dir, exist_ok=True)

        # Save the plot
        output_filepath = os.path.join(output_dir, output_filename)
        plt.savefig(output_filepath, dpi=dpi, bbox_inches='tight')
        plt.close(fig) # Close the figure to free memory
        print(f"Plot saved successfully to {output_filepath}")

    except FileNotFoundError:
        print(f"Error: Input file not found at {input_filepath}")
    except pd.errors.EmptyDataError:
        print(f"Error: Input file {input_filepath} is empty or contains only comments.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

# --- Example Usage ---
if __name__ == "__main__":
    # Assume the data file is in the same directory or provide the correct path
    data_file = 'Example Data For Testing Graphs.txt'
    output_directory = 'graph_gen/generated_graphs' # Directory to store the generated plots
    output_name = 'voltage_current_vs_time.pdf'

    generate_basytec_plots(data_file, output_dir=output_directory, output_filename=output_name)
