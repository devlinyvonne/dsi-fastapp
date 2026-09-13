from fastapi import FastAPI
from fastapi.responses import HTMLResponse
import pandas as pd


# -------------------------------------------------
# Create FastAPI app
# -------------------------------------------------
app = FastAPI()


#--------------------------------------------------
# Define functions
#--------------------------------------------------

def load_data():
    data = pd.read_csv("skin clinic campaign.csv")

    return data


def prepare_data(data):
    # Convert Products purchased to category column by grouping in ranges
    data['Products_Purchased_Group'] = pd.cut(data['Unique_Products_Purchased'], bins=[0, 4, 8, float('inf')], labels=['1-4', '5-8', '>8'])

    # Convert categorical features 
    cat_cols = ["Gender", "AgeGroup", "Purchase_Last_Quarter", "Response_to_Campaign", "Products_Purchased_Group"]
    for col in cat_cols:
        data[col] = data[col].astype('category')

    return data

def get_response_rate(df, col):
    response_counts = df.groupby(col,observed=True)['Response_to_Campaign'].value_counts().rename('Count').reset_index()

    # Convert to percentages
    response_counts['Percentage'] = (response_counts.groupby(col,observed=True)['Count'].transform(lambda x: (100 * x / x.sum()).round(2)))

    return response_counts[response_counts['Response_to_Campaign'] == 'Yes'][[col, 'Count', 'Percentage']]


# -------------------------------------------------
# Health check endpoint
# -------------------------------------------------
@app.get("/health")
def health_check():
    return {"message": "Campaign analysis app is running"}


# -------------------------------------------------
# Main endpoint
# -------------------------------------------------
@app.get("/campaign-analysis", response_class=HTMLResponse)
def campaign_analysis():

    data = load_data()

    data = prepare_data(data)

    gender = get_response_rate(data, 'Gender').to_dict(orient='records'),
    age = get_response_rate(data, 'AgeGroup').to_dict(orient='records'),
    last_quarter = get_response_rate(data, 'Purchase_Last_Quarter').to_dict(orient='records'),
    products_purchased = get_response_rate(data, 'Products_Purchased_Group').to_dict(orient='records')

    def table_html(title, df, group_col):
        rows = "".join(
            f"<tr><td>{r[0]}</td><td>{r[1]}</td><td>{r[2]}</td></tr>"
            for r in df.itertuples(index=False)
        )
        return (
            f"<h3>{title}</h3>"
            f"<table border='1' style='border-collapse:collapse;width:100%;margin-bottom:30px'>"
            f"<tr style='background:#f4f4f4'><th>{group_col}</th><th>Count</th><th>Response Rate (%)</th></tr>"
            f"{rows}</table>"
        )


    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Campaign Response Analysis Summary</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 40px; }}
            h2 {{ text-align: center; }}
            th, td {{ border: 1px solid #ccc; padding: 8px; text-align: center; }}
        </style>
    </head>
    <body>
        <h2>Campaign Response Analysis Summary</h2>
        {table_html('Gender vs Campaign Response', gender, 'Gender')}
        {table_html('Age Group vs Campaign Response', age, 'AgeGroup')}
        {table_html('Purchase in Last Quarter vs Campaign Response', last_quarter, 'Purchase Last Quarter')}
        {table_html('Product Usage vs Campaign Response', products_purchased, 'Products Purchased')}
    </body>
    </html>
    """

    return html_content

