from flask import Flask, request, jsonify, render_template
import pandas as pd
import os
import re

app = Flask(__name__)

# --- Configuration for Data Files ---
EXCEL_FILE_NAME = "Cybersecurity Standards Database..xltx"
EXCEL_FILE_PATH = os.path.join("static", "data", EXCEL_FILE_NAME)

# Custom sorting key for mixed numeric/dot strings (e.g., '1', '4.1', '4.1.1')
def natural_sort_key(s):
    # Split the string by dots and convert numeric parts to integers for comparison
    return [int(text) if text.isdigit() else text for text in re.split('([0-9]+)', s)]

# Load and clean standards data from a multi-sheet Excel file
def load_clean_standards():
    all_data = []
    all_sections_raw = set()  # Temporary set to collect all section values before strict filtering
    all_sources = set()

    # --- Excel Loading Logic ---
    if os.path.exists(EXCEL_FILE_PATH):
        print(f"[INFO] Loading data from Excel file: {EXCEL_FILE_PATH}...")
        try:
            excel_file = pd.ExcelFile(EXCEL_FILE_PATH)
            print(f"[INFO] Discovered sheets: {excel_file.sheet_names}")

            expected_excel_cols = [
                'Section', 'Sub-Section', 'Keywords', 'ControlID', 'Title',
                'Page Number', 'Requirement Text', 'Simplified Summary',
                'Control Category', 'Internal Control ID', 'Notes', 'Mapped',
                'Foundation Requirements', 'System Requirements', 'Requirement Text.1', 'Simplified Summary.1'
            ]

            for sheet_name in excel_file.sheet_names:
                # Skip the 'Example' sheet as requested
                if sheet_name.strip().lower() == 'example':
                    print(f"[INFO] Skipping sheet: '{sheet_name}'")
                    continue

                try:
                    df = excel_file.parse(sheet_name)
                    if df.empty:
                        print(f"[WARNING] Sheet '{sheet_name}' is empty or could not be parsed. Skipping.")
                        continue

                    # Clean column names first, including removing _x000D_
                    df.columns = [str(col).strip().replace('_x000D_', '') for col in df.columns]
                    print(f"[DEBUG] Columns in sheet '{sheet_name}': {list(df.columns)}")

                    for col in expected_excel_cols:
                        if col not in df.columns:
                            df[col] = ''
                        else:
                            # Fill NaN values with empty string and convert entire column to string type
                            # Also remove _x000D_ from the content of these columns
                            df[col] = df[col].fillna('').astype(str).str.replace('_x000D_', '').str.strip()

                    source = sheet_name.strip()
                    if source == 'IEC 62433-3':
                        source = 'IEC 62443-3-3'
                    source = source.strip()

                    for _, row in df.iterrows():
                        section_val = row.get('Sub-Section', '').strip()
                        if not section_val:
                            section_val = row.get('Section', '').strip()
                        if not section_val:
                            section_val = row.get('Control Category', '').strip()
                        if section_val.lower() == 'nan':
                            section_val = ''

                        main_description_val = row.get('Requirement Text', '').strip()
                        if not main_description_val:
                            main_description_val = row.get('Simplified Summary', '').strip()
                        if main_description_val.lower() == 'nan':
                            main_description_val = ''

                        keywords_val = row.get('Keywords', '').strip()
                        if keywords_val.lower() == 'nan':
                            keywords_val = ''

                        control_id_val = row.get('ControlID', '').strip()
                        if not control_id_val or control_id_val.lower() == 'nan':
                            control_id_val = row.get('Internal Control ID', 'N/A').strip()
                        if control_id_val.lower() == 'nan':
                            control_id_val = 'N/A'

                        title_val = row.get('Title', '').strip()
                        if title_val.lower() == 'nan':
                            title_val = ''

                        page_number_val = row.get('Page Number', '').strip()
                        if page_number_val.lower() == 'nan':
                            page_number_val = ''

                        requirement_text_val = row.get('Requirement Text', '').strip()
                        if requirement_text_val.lower() == 'nan':
                            requirement_text_val = ''
                        if not requirement_text_val and 'Requirement Text.1' in row and row.get('Requirement Text.1', '').strip():
                            requirement_text_val = row.get('Requirement Text.1', '').strip()
                            if requirement_text_val.lower() == 'nan':
                                requirement_text_val = ''

                        simplified_summary_val = row.get('Simplified Summary', '').strip()
                        if simplified_summary_val.lower() == 'nan':
                            simplified_summary_val = ''
                        if not simplified_summary_val and 'Simplified Summary.1' in row and row.get('Simplified Summary.1', '').strip():
                            simplified_summary_val = row.get('Simplified Summary.1', '').strip()
                            if simplified_summary_val.lower() == 'nan':
                                simplified_summary_val = ''

                        control_category_val = row.get('Control Category', '').strip()
                        if control_category_val.lower() == 'nan':
                            control_category_val = ''

                        if not section_val and not main_description_val:
                            continue

                        all_data.append({
                            'Section': section_val,
                            'Source': source,
                            'Description': main_description_val,
                            'Keywords': keywords_val,
                            'ControlID': control_id_val,
                            'Title': title_val,
                            'Page Number': page_number_val,
                            'Requirement Text': requirement_text_val,
                            'Simplified Summary': simplified_summary_val,
                            'Control Category': control_category_val
                        })

                        if section_val:
                            all_sections_raw.add(section_val)
                        if source:
                            all_sources.add(source)

                except Exception as e:
                    print(f"[ERROR] Error processing sheet '{sheet_name}' in '{EXCEL_FILE_NAME}': {e}")
                    if 'df' in locals() and df is not None:
                        if not df.empty:
                            print(f"[DEBUG] Columns in problematic sheet '{sheet_name}': {list(df.columns)}")
                        else:
                            print(f"[DEBUG] DataFrame for sheet '{sheet_name}' was empty after parsing or during processing.")
                    else:
                        print(f"[DEBUG] DataFrame for sheet '{sheet_name}' was not initialized or accessible.")
                    continue

        except Exception as e:
            print(f"[CRITICAL] Failed to load Excel file '{EXCEL_FILE_PATH}': {e}")
    # --- End Excel Loading Logic ---

    # --- Post-processing for sections and duplicates ---
    final_sections = set()
    for sec in all_sections_raw:
        if re.fullmatch(r'[\d.]+', sec):
            final_sections.add(sec)
        else:
            print(f"[DEBUG] Filtering out non-numeric section: '{sec}'")

    if all_data:
        df_final = pd.DataFrame(all_data)
        if 'Description' not in df_final.columns:
            df_final['Description'] = df_final['Requirement Text'].fillna('')

        df_final.drop_duplicates(subset=[
            'Source', 'ControlID', 'Requirement Text', 'Simplified Summary', 'Title'
        ], inplace=True)
    else:
        df_final = pd.DataFrame(columns=['Section', 'Source', 'Description', 'Keywords', 'ControlID', 'Title', 'Page Number', 'Requirement Text', 'Simplified Summary', 'Control Category'])
        df_final['Description'] = ''

    print(f"[INFO] Successfully loaded {len(df_final)} unique rows from Excel file.")
    # Sort sections using the natural_sort_key
    sorted_sections = sorted(list(final_sections), key=natural_sort_key)
    print(f"[INFO] Discovered Sections (filtered and sorted): {sorted_sections}")
    print(f"[INFO] Discovered Sources: {sorted(list(all_sources))}")
    return df_final, sorted_sections, sorted(list(all_sources))

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
            search_cols = [
                'Description', 'Keywords', 'ControlID', 'Title',
                'Requirement Text', 'Simplified Summary', 'Control Category', 'Section'
            ]

            query_mask = pd.Series([False] * len(filtered), index=filtered.index)
            for col in search_cols:
                if col in filtered.columns:
                    query_mask = query_mask | filtered[col].astype(str).str.contains(query, case=False, na=False)
            filtered = filtered[query_mask]

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
        print(f"[ERROR] Column not found in DataFrame during search: {ke}. This should ideally not happen with current data loading.")
        return jsonify([]), 500


@app.route("/api/filters", methods=["GET"])
def get_filters():
    return jsonify({
        "sections": all_sections,  # This will now contain only numeric values and be sorted
        "sources": all_sources
    })


@app.errorhandler(500)
def internal_error(error):
    app.logger.error('Server Error: %s', error, exc_info=True)
    return jsonify({"error": "An internal server error occurred."}), 500


if __name__ == "__main__":
    print(f"[INFO] Starting Flask app. Data directory: {os.path.dirname(EXCEL_FILE_PATH)}")
    app.run(debug=True)