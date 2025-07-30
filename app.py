from flask import Flask, request, jsonify, render_template
import pandas as pd
import os
import re
import logging

# --- Flask App Initialization ---
app = Flask(__name__)

# --- Configuration for Data Files ---
EXCEL_FILE_NAME = "Cybersecurity Standards Database.xlsx"  # Updated to .xlsx format
EXCEL_FILE_PATH = os.path.join("static", "data", EXCEL_FILE_NAME)

# --- Logging Setup ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Helper Functions ---
def natural_sort_key(s):
    """Custom sorting key for mixed numeric/dot strings."""
    return [int(text) if text.isdigit() else text for text in re.split(r'([0-9]+)', s)]

def load_clean_standards():
    """Load and clean standards data from Excel."""
    all_data = []
    all_sections_raw = set()
    all_sources = set()

    if not os.path.exists(EXCEL_FILE_PATH):
        logger.error(f"Excel file not found: {EXCEL_FILE_PATH}")
        return pd.DataFrame(), [], []

    try:
        excel_file = pd.ExcelFile(EXCEL_FILE_PATH)
        logger.info(f"Discovered sheets: {excel_file.sheet_names}")

        expected_excel_cols = [
            'Section', 'Sub-Section', 'Keywords', 'ControlID', 'Title',
            'Page Number', 'Requirement Text', 'Simplified Summary',
            'Control Category', 'Internal Control ID', 'Notes', 'Mapped',
            'Foundation Requirements', 'System Requirements', 'Requirement Text.1', 'Simplified Summary.1'
        ]

        for sheet_name in excel_file.sheet_names:
            if sheet_name.strip().lower() == 'example':
                logger.info(f"Skipping sheet: '{sheet_name}'")
                continue

            try:
                df = excel_file.parse(sheet_name)
                if df.empty:
                    logger.warning(f"Sheet '{sheet_name}' is empty. Skipping.")
                    continue

                # Debug: Print the first few rows of the DataFrame
                logger.debug(f"DataFrame loaded from sheet '{sheet_name}':\n{df.head()}")

                # Clean column names and data
                df.columns = [col.strip().replace('_x000D_', '') for col in df.columns]
                df = df.fillna('').applymap(lambda x: str(x).replace('_x000D_', '').strip())

                # Add missing columns
                for col in expected_excel_cols:
                    if col not in df.columns:
                        logger.debug(f"Adding missing column: {col}")
                        df[col] = ''

                source = sheet_name.strip()
                if source == 'IEC 62433-3':
                    source = 'IEC 62443-3-3'

                for _, row in df.iterrows():
                    section_val = row.get('Sub-Section', '').strip() or row.get('Section', '').strip()
                    main_description_val = row.get('Requirement Text', '').strip() or row.get('Simplified Summary', '').strip()
                    control_id_val = row.get('ControlID', '').strip() or row.get('Internal Control ID', 'N/A').strip()

                    if not section_val and not main_description_val:
                        continue

                    all_data.append({
                        'Section': section_val,
                        'Source': source,
                        'Description': main_description_val,
                        'Keywords': row.get('Keywords', '').strip(),
                        'ControlID': control_id_val,
                        'Title': row.get('Title', '').strip(),
                        'Page Number': row.get('Page Number', '').strip(),
                        'Requirement Text': row.get('Requirement Text', '').strip(),
                        'Simplified Summary': row.get('Simplified Summary', '').strip(),
                        'Control Category': row.get('Control Category', '').strip()
                    })

                    all_sections_raw.add(section_val)
                    all_sources.add(source)

            except Exception as e:
                logger.error(f"Error processing sheet '{sheet_name}': {e}")
                continue

        final_sections = {sec for sec in all_sections_raw if re.fullmatch(r'[\d.]+', sec)}
        sorted_sections = sorted(final_sections, key=natural_sort_key)
        return pd.DataFrame(all_data), sorted_sections, sorted(all_sources)

    except Exception as e:
        logger.critical(f"Failed to load Excel file: {e}")
        return pd.DataFrame(), [], []

# --- Load Data Once at Startup ---
try:
    df, all_sections, all_sources = load_clean_standards()
    logger.info(f"Successfully loaded {len(df)} unique rows from Excel file.")
    logger.info(f"Discovered Sections (filtered and sorted): {all_sections}")
    logger.info(f"Discovered Sources: {all_sources}")
except Exception as e:
    logger.critical(f"Failed to load standards database during app startup: {e}")
    df = pd.DataFrame(columns=['Section', 'Source', 'Description', 'Keywords', 'ControlID', 'Title', 'Page Number', 'Requirement Text', 'Simplified Summary', 'Control Category'])
    all_sections = []
    all_sources = []

# --- Routes ---
@app.route("/")
def index():
    return render_template("index.html")

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
                    query_mask |= filtered[col].str.contains(query, case=False, na=False)
            filtered = filtered[query_mask]

        if section and section != "All Sections":
            filtered = filtered[filtered["Section"] == section]

        if source and source != "All Sources":
            filtered = filtered[filtered["Source"] == source]

        logger.debug(f"Returning {len(filtered)} results for query='{query}', section='{section}', source='{source}'")
        return jsonify(filtered.to_dict(orient="records"))

    except Exception as e:
        logger.error(f"Error during search: {e}")
        return jsonify([]), 500

@app.route("/api/filters", methods=["GET"])
def get_filters():
    return jsonify({
        "sections": all_sections,
        "sources": all_sources
    })

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Server Error: {error}")
    return jsonify({"error": "An internal server error occurred."}), 500

# --- Main Entry Point ---
if __name__ == "__main__":
    logger.info(f"Starting Flask app. Data directory: {os.path.dirname(EXCEL_FILE_PATH)}")
    app.run(debug=True)