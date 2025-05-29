import pandas as pd


def get_arrival_data():
    """
    return a dataframe of arrival data returned by the "generate_data" function.
    this is a placeholder.
    """
    file_path = (
        "2025-01-01-2025-04-30,REF29094.csv"  # Update this path to your actual CSV file
    )
    return pd.read_csv(file_path)
