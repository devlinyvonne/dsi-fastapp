from fastapi import FastAPI
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
@app.get("/campaign-analysis")
def campaign_analysis():
    data = load_data()
    data = prepare_data(data)

    return {
        "Gender": get_response_rate(data, 'Gender').to_dict(orient='records'),
        "Age": get_response_rate(data, 'AgeGroup').to_dict(orient='records'),
        "Purchase in last Quarter": get_response_rate(data, 'Purchase_Last_Quarter').to_dict(orient='records'),
        "Products Purchased": get_response_rate(data, 'Products_Purchased_Group').to_dict(orient='records')
    }

