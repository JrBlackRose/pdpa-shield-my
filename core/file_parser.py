import pandas as pd

def parse_uploaded_file(uploaded_file) -> pd.DataFrame:
    filename = uploaded_file.name.lower()
    try:
        if filename.endswith(".csv"):
            return pd.read_csv(uploaded_file)
        elif filename.endswith((".xls", ".xlsx")):
            return pd.read_excel(uploaded_file)
        else:
            raise ValueError("Unsupported file extension.")
    except Exception as e:
        raise Exception(f"Failed to parse file: {str(e)}")