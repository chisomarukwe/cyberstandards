from flask import Flask, request, jsonify, render_template
import pandas as pd
import os

app = Flask(__name__)

# Define the path to your single, multi-sheet Excel file
# Make sure your Excel file (e.g., "Cybersecurity Standards Database.xlsx")
# is placed inside the 'static/data/' directory.
EXCEL_FILE_NAME = "Cybersecurity Standards Database.xlsx" # <--- IMPORTANT: Match your actual Excel file name
EXCEL_FILE_PATH = os.path.join("static", "data", EXCEL_FILE_NAME)


# Load and clean standards data from a multi-sheet Excel file
def load_clean_standards():
    all_data = []
    all_sections = set()
    all_sources = set()

    # Ensure the Excel file exists
    if not os.path.exists(EXCEL_FILE_PATH):
        print(f"[ERROR] Excel file not found at: {EXCEL_FILE_PATH}. Please ensure your Excel file is in place.")
        # Return an empty DataFrame and lists if file not found
        return pd.DataFrame(columns=['Section', 'Source', 'Description', 'Keywords', 'ControlID', 'Title', 'Page Number', 'Requirement Text', 'Simplified Summary', 'Control Category']), [], []

    try:
        # Load the Excel file
        excel_file = pd.ExcelFile(EXCEL_FILE_PATH)
        print(f"[INFO] Found Excel file: {EXCEL_FILE_PATH}. Loading data from sheets...")
        print(f"[INFO] Discovered sheets: {excel_file.sheet_names}")

        # Iterate through each sheet in the Excel file
        for sheet_name in excel_file.sheet_names:
            try:
                # Read each sheet into a DataFrame
                df = excel_file.parse(sheet_name)

                # Clean column names by stripping whitespace
                df.columns = df.columns.str.strip()
                print(f"[DEBUG] Columns in sheet '{sheet_name}': {list(df.columns)}") # Log columns for debugging

                # Convert relevant columns to string type to prevent .str accessor errors
                # and fill NaN values with empty strings before stripping
                columns_to_process = [
                    'Section', 'Description', 'Keywords', 'ControlID', 'Title',
                    'Page Number', 'Requirement Text', 'Simplified Summary',
                    'Control Category', 'Internal Control ID' # Added Internal Control ID here as it's used
                ]
                for col in columns_to_process:
                    if col in df.columns:
                        # Convert column to string, filling NaN values with an empty string
                        df[col] = df[col].fillna('').astype(str)

                # The sheet name will be the source for all entries in this sheet
                source = sheet_name.strip()
                # Standardize source names if needed, e.g., 'IEC 62433-3' to 'IEC 62443-3-3'
                if source == 'IEC 62433-3': # If your sheet name has this specific variant
                    source = 'IEC 62443-3-3' # Standardize to the common name

                # Iterate through rows and extract data
                for _, row in df.iterrows():
                    # Prioritize 'Section', then 'Control Category' if 'Section' is missing
                    # These are already converted to string and NaN-filled above
                    section_val = row.get('Section', '').strip()
                    if not section_val: # If 'Section' is empty, try 'Control Category'
                        section_val = row.get('Control Category', '').strip()
                    
                    # Filter out 'nan' strings from sections
                    if section_val.lower() == 'nan':
                        section_val = '' # Treat 'nan' as empty for filtering purposes

                    # Prioritize 'Description', then 'Requirement Text', then 'Simplified Summary' for the main description
                    # These are already converted to string and NaN-filled above
                    description_val = row.get('Description', '').strip()
                    if not description_val:
                        description_val = row.get('Requirement Text', '').strip()
                    if not description_val:
                        description_val = row.get('Simplified Summary', '').strip()
                    
                    # Ensure we have at least a non-empty section and a description before adding
                    if not section_val or not description_val:
                        # print(f"[DEBUG] Skipping row due to missing Section or Description in sheet '{sheet_name}'. Section: '{section_val}', Description: '{description_val}'")
                        continue

                    # Extract all other fields - already converted to string and NaN-filled above
                    keywords_val = row.get('Keywords', '').strip()
                    control_id_val = row.get('ControlID', row.get('Internal Control ID', 'N/A')).strip() # Check for ControlID or Internal Control ID
                    title_val = row.get('Title', '').strip()
                    page_number_val = row.get('Page Number', '').strip()
                    requirement_text_val = row.get('Requirement Text', '').strip()
                    simplified_summary_val = row.get('Simplified Summary', '').strip()
                    control_category_val = row.get('Control Category', '').strip() # Store separately, even if used for section fallback

                    all_data.append({
                        'Section': section_val,
                        'Source': source, # Source is now the sheet name
                        'Description': description_val, # Main description field
                        'Keywords': keywords_val,
                        'ControlID': control_id_val,
                        'Title': title_val,
                        'Page Number': page_number_val,
                        'Requirement Text': requirement_text_val, # Additional field
                        'Simplified Summary': simplified_summary_val, # Additional field
                        'Control Category': control_category_val # Additional field
                    })
                    # Add to sets for filter options, only if not empty
                    if section_val: # Only add non-empty sections to the set
                        all_sections.add(section_val)
                    if source: # Only add non-empty sources to the set
                        all_sources.add(source)

            except Exception as e:
                print(f"[ERROR] Error processing sheet '{sheet_name}' in '{EXCEL_FILE_NAME}': {e}")
                # Print columns of the problematic sheet for debugging
                if 'df' in locals(): # Check if df was created before error
                    print(f"[DEBUG] Columns in problematic sheet '{sheet_name}': {list(df.columns)}")
                continue # Continue to next sheet even if one fails

    except Exception as e:
        print(f"[CRITICAL] Failed to load Excel file '{EXCEL_FILE_PATH}': {e}")
        # If the entire Excel file fails to load, return empty data
        return pd.DataFrame(columns=['Section', 'Source', 'Description', 'Keywords', 'ControlID', 'Title', 'Page Number', 'Requirement Text', 'Simplified Summary', 'Control Category']), [], []


    # Convert to DataFrame and remove duplicates
    if all_data:
        df_final = pd.DataFrame(all_data)
        # Drop duplicates based on a combination of identifying fields
        df_final.drop_duplicates(subset=['Section', 'Source', 'Description', 'ControlID'], inplace=True)
    else:
        df_final = pd.DataFrame(columns=['Section', 'Source', 'Description', 'Keywords', 'ControlID', 'Title', 'Page Number', 'Requirement Text', 'Simplified Summary', 'Control Category'])

    print(f"[INFO] Successfully loaded {len(df_final)} unique rows from Excel file.")
    print(f"[INFO] Discovered Sections: {sorted(list(all_sections))}")
    print(f"[INFO] Discovered Sources: {sorted(list(all_sources))}")
    return df_final, sorted(list(all_sections)), sorted(list(all_sources))


# Load data once at startup
try:
    df, all_sections, all_sources = load_clean_standards()
except Exception as e:
    print(f"[CRITICAL] Failed to load standards database during app startup: {e}")
    print("Application will start with empty data. Please check your Excel file in 'static/data/' and its format.")
    df = pd.DataFrame(columns=['Section', 'Source', 'Description', 'Keywords', 'ControlID', 'Title', 'Page Number', 'Requirement Text', 'Simplified Summary', 'Control Category'])
    all_sections = []
    all_sources = []

# Serve the home page
@app.route("/")
def index():
    return render_template("index.html")

# API: Search with filters
@app.route("/api/standards", methods=["GET"])
def search_standards():
    query = request.args.get("query", "").strip().lower()
    section = request.args.get("section", "")
    source = request.args.get("source", "")

    filtered = df.copy()

    try:
        if query:
            # Search across Description, Keywords, ControlID, Title, Requirement Text, Simplified Summary, Control Category
            filtered = filtered[
                filtered['Description'].str.contains(query, case=False, na=False) |
                filtered['Keywords'].str.contains(query, case=False, na=False) |
                filtered['ControlID'].str.contains(query, case=False, na=False) |
                filtered['Title'].str.contains(query, case=False, na=False) |
                filtered['Requirement Text'].str.contains(query, case=False, na=False) |
                filtered['Simplified Summary'].str.contains(query, case=False, na=False) |
                filtered['Control Category'].str.contains(query, case=False, na=False)
            ]

        if section and section != "All Sections":
            if 'Section' in filtered.columns:
                filtered = filtered[filtered["Section"] == section]
            else:
                app.logger.warning("Attempted to filter by 'Section' but column not found in DataFrame.")

        if source and source != "All Sources":
            if 'Source' in filtered.columns:
                filtered = filtered[filtered["Source"] == source]
            else:
                app.logger.warning("Attempted to filter by 'Source' but column not found in DataFrame.")

        print(f"[DEBUG] Returning {len(filtered)} results for query='{query}', section='{section}', source='{source}'")
        return jsonify(filtered.to_dict(orient="records"))
        
    except KeyError as ke:
        print(f"[ERROR] Column not found in DataFrame during search: {ke}")
        return jsonify([]), 500


@app.route("/api/filters", methods=["GET"])
def get_filters():
    return jsonify({
        "sections": all_sections,
        "sources": all_sources
    })


@app.errorhandler(500)
def internal_error(error):
    app.logger.error('Server Error: %s', error, exc_info=True)
    return jsonify({"error": "An internal server error occurred."}), 500


if __name__ == "__main__":
    print(f"[INFO] Starting Flask app. Data directory: {os.path.dirname(EXCEL_FILE_PATH)}") # Indicate the directory for clarity
    app.run(debug=True)