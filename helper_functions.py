def generate_markdown_table(dataframe, filename="table.md"):
    """
    Generates a Markdown table from a Pandas DataFrame and saves it to a file.

    Parameters:
        dataframe (pd.DataFrame): The Pandas DataFrame containing the table data.
        filename (str): The name of the file to save the Markdown table. Default is "table.md".

    Returns:
        None
    """

    # Ensure the DataFrame is not empty
    if dataframe.empty:
        raise ValueError("DataFrame is empty. Cannot generate a table.")

    # Ensure the filename has the ".md" extension
    if not filename.endswith(".md"):
        filename += ".md"

    # Open the file for writing
    with open(filename, "w", encoding="utf-8") as file:

        # Write the header row
        file.write("| " + " | ".join(dataframe.columns) + " |\n")

        # Write the header separator
        file.write("|" + "|".join(["---"] * len(dataframe.columns)) + "|\n")

        # Write the data rows
        for _, row in dataframe.iterrows():
            file.write("| " + " | ".join(map(str, row)) + " |\n")

    print(f"Markdown table has been generated and saved to {filename}.")