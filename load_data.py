import pandas as pd
import numpy as np

def load_dataset(file, sheet_name):
    """
    Reads the provided Excel sheet into a DataFrame, reshapes it, and returns the result.

    Parameters:
    - file (str): The path to the Excel file.
    - sheet_name (str): The name of the sheet in the Excel file.

    Returns:
    pd.DataFrame: Reshaped DataFrame containing the data from the specified sheet.
    """

    # Read Excel file into a DataFrame
    df = pd.read_excel(
        file,
        sheet_name=sheet_name,
        index_col=0,        # Use the first column as the index
        header=None          # Do not use any header information
    )

    # Combine the first two rows to create column names
    colnames = zip(df.iloc[0, :], df.iloc[1, :])

    # Remove rows with NaN values in the index
    df = df[~df.index.isna()]

    # Rename the index to "Firm"
    df.index = df.index.rename("Firm")

    # Create a MultiIndex for columns using the combined names
    df.columns = pd.MultiIndex.from_tuples(colnames).set_names(["Metric", "Year"])

    # Reshape the DataFrame using the melt function
    ff = df.melt(
        value_name="Value",   # Name for the values column
        ignore_index=False     # Keep the original index in the melted DataFrame
    ).reset_index()

    return ff

def report_on_dataset_join(dataset1, dataset2):
    """
    Compares the firms in two datasets and prints the count of common and unique firms.

    Parameters:
    - dataset1 (pd.DataFrame): The first dataset.
    - dataset2 (pd.DataFrame): The second dataset.
    """

    # Generate list of firms in both source files
    general_firms = set(dataset1["Firm"].unique())
    underwriting_firms = set(dataset2["Firm"].unique())

    # Calculate the number of values that exist in both arrays
    intersection_count = len(general_firms.intersection(underwriting_firms))

    # Calculate the number that exists only in general_firms
    general_only_count = len(general_firms - underwriting_firms)

    # Calculate the number that exists only in underwriting_firms
    underwriting_only_count = len(underwriting_firms - general_firms)

    # Print the results
    print(f"Number of values that exist in both datasests: {intersection_count}")
    print(f"Number that exists only in Dataset 1 - General: {general_only_count}")
    print(f"Number that exists only in Dataset 2 - Underwriting: {underwriting_only_count}")

def report_on_zero_values(ff):
    """
    Prints the percentage of records in a DataFrame containing zero values.

    Parameters:
    - ff (pd.DataFrame): The DataFrame to analyze.
    """

    # Report on the number of records containing zero values
    number_of_zero_records = (ff["Value"] == 0).sum()
    total_number_of_records = ff.shape[0]
    print(f"{number_of_zero_records / total_number_of_records:.1%} of records contain zero values")

def load_data(print_reports=False):
    """
    Loads data from an Excel file, combines two datasets, and performs data conversions.

    Parameters:
    - print_reports (bool): If True, prints reports on dataset join and zero values.

    Returns:
    pd.DataFrame: Combined and processed DataFrame.
    """

    # Specify the file path
    file = "01 Raw Data/DataScientist_009749_Dataset.xlsx"

    # Load datasets from two different sheets and concatenate them
    general_ff = load_dataset(file, "Dataset 1 - General")
    underwriting_ff = load_dataset(file, "Dataset 2 - Underwriting")
    ff = pd.concat([
        general_ff,
        underwriting_ff
    ]).reset_index(drop=True)

    # Convert Year column to a number
    ff["Year"] = ff["Year"].str.replace("YE", "").astype(int)

    # Convert Value column to a float
    ff["Value"] = ff["Value"].astype(float)

    if print_reports:
        report_on_dataset_join(general_ff, underwriting_ff)
        print("")
        report_on_zero_values(ff)
        print("")
        print("Data loaded.")

    return ff

def zero_test(firm):
    """
    Checks if all values in a Series are zero and counts consecutive zeros from the start/end.

    Parameters:
    - firm (pd.Series): The Series to test.

    Returns:
    bool: True if all values are zero or there are only consecutive zeros.
    """

    # Check if all values in the firm are zero
    is_zero = firm == 0
    
    # Count the number of zeros and non-zeros
    zero_count = is_zero.sum()
    non_zero_count = len(firm) - zero_count
    
    # Count consecutive zeros at the beginning
    consecutive_zeros_first = 0
    for value in firm:
        if value == 0:
            consecutive_zeros_first += 1
        else:
            break
    
    # Count consecutive zeros at the end
    consecutive_zeros_last = 0
    for value in firm.iloc[::-1]:
        if value == 0:
            consecutive_zeros_last += 1
        else:
            break
    
    # Total consecutive zeros
    consecutive_zero_total = consecutive_zeros_first + consecutive_zeros_last
    
    # Return True if either all values are zero or there are consecutive zeros
    return (non_zero_count == 0) or (consecutive_zero_total == zero_count)

def impute_zeros(ff, print_reports=False):
    """
    Imputes zero values in a DataFrame with the average of surrounding non-zero values.

    Parameters:
    - ff (pd.DataFrame): The DataFrame to impute.
    - print_reports (bool): If True, prints the number of values imputed.

    Returns:
    pd.DataFrame: DataFrame with imputed values.
    """

    # Pivot the ff DataFrame to have years as columns
    test_metric_pivot = ff.pivot(columns="Year", index=["Firm", "Metric"], values="Value")

    # Keep rows where at least one value is zero
    test_metric_pivot = test_metric_pivot[(test_metric_pivot == 0).sum(axis=1) > 0]

    # Reset index to have Firm and Metric as columns
    test_metric_pivot = test_metric_pivot.reset_index()
    test_metric_pivot.columns = test_metric_pivot.columns.rename("")

    # Create a mask to filter rows based on zero_test function
    test_mask = test_metric_pivot.loc[:, 2016:2020].apply(zero_test, axis=1)
    temp_table = test_metric_pivot.copy()
    temp_table["Mask"] = test_mask

    # Keep rows where zero_test is False
    test_metric_pivot = test_metric_pivot[~test_mask].reset_index(drop=True)

    # Melt the DataFrame back to long format
    test_metric_ff = test_metric_pivot.melt(id_vars=["Firm", "Metric"], value_vars=[2016, 2017, 2018, 2019, 2020], var_name="Year", value_name="Value")

    # For each row calculate the average value based on the next and previous non-zero value
    test_metric_ff = test_metric_ff.sort_values(["Firm", "Metric", "Year"])
    values_with_missing = test_metric_ff["Value"].replace(0, np.nan)
    test_metric_ff["Prev"] = values_with_missing.ffill()
    test_metric_ff["Next"] = values_with_missing.bfill()
    test_metric_ff["Average"] = test_metric_ff[["Prev", "Next"]].mean(axis=1)

    # Replace NaN values in "Value" column with the calculated average
    test_metric_ff["New Value"] = values_with_missing.fillna(test_metric_ff[["Prev", "Next"]].mean(axis=1))

    # Keep rows where the original "Value" column is 0
    test_metric_ff = test_metric_ff[test_metric_ff["Value"] == 0]

    # Merge back to the original DataFrame based on Firm, Metric, and Year columns
    merged_ff = ff.merge(test_metric_ff[["Firm", "Metric", "Year", "New Value"]], on=["Firm", "Metric", "Year"], how="left")

    # Update the "Value" column in ff with "New Value" from test_metric_ff where it matches
    merged_ff["Value"] = merged_ff["New Value"].combine_first(merged_ff["Value"])

    # Drop the "New Value" column from merged_ff
    merged_ff = merged_ff.drop(columns=["New Value"])

    # Replace ff with the updated version
    ff = merged_ff

    if print_reports:
        print(f"{test_metric_ff.shape[0]} values imputed")

    return ff

def full_data_load(print_reports=False):
    """
    Loads and processes data from an Excel file, including imputing zero values.

    Parameters:
    - print_reports (bool): If True, prints reports on dataset join and zero values.

    Returns:
    pd.DataFrame: Combined, processed, and imputed DataFrame.
    """

    # Load data from file and transform to flat file format
    ff = load_data(print_reports=print_reports)

    # Impute zeros
    ff = impute_zeros(ff, print_reports=print_reports)

    return ff

