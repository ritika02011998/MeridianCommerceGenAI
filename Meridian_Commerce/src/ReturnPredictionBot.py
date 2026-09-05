import streamlit as st
import pandas as pd
import joblib
import anthropic
from dotenv import load_dotenv
from datetime import datetime

# ---------------------------------------------------
# Load environment variables
# ---------------------------------------------------

load_dotenv()

# ---------------------------------------------------
# Streamlit page configuration
# ---------------------------------------------------

st.set_page_config(
    page_title="Meridian Commerce Return Predictor",
    page_icon="📦",
    layout="centered"
)

st.title("📦 Meridian Commerce - Product Return Predictor")

st.write(
    "Enter the product and order details below to predict "
    "whether the product is likely to be returned."
)

# ---------------------------------------------------
# Load trained model and scaler
# ---------------------------------------------------

@st.cache_resource
def load_models():
    scaler = joblib.load("scaler.pkl")
    model = joblib.load("logistic_regression_model.pkl")

    return scaler, model


scaler, model = load_models()

# ---------------------------------------------------
# Initialize Anthropic client
# ---------------------------------------------------

client = anthropic.Anthropic()


# ---------------------------------------------------
# Category and subcategory mapping
# ---------------------------------------------------

subcategory_mapping = {
    "Electronics": [
        "Earbuds",
        "Tablets",
        "Smartwatches",
        "Bluetooth Speakers",
        "Laptops",
        "Smartphones",
        "Power Banks",
        "Cameras",
        "Headphones",
        "Chargers"
    ],

    "Apparel": [
        "Jeans",
        "T-Shirts",
        "Sweaters",
        "Dresses",
        "Activewear",
        "Jackets"
    ],

    "Footwear": [
        "Loafers",
        "Boots",
        "Sneakers",
        "Running Shoes",
        "Formal Shoes",
        "Sandals"
    ],

    "Home Goods": [
        "Storage Bins",
        "Coffee Makers",
        "Blenders",
        "Air Fryers",
        "Vacuum Cleaners",
        "Bedsheets",
        "Cookware Sets",
        "Lamps"
    ]
}


# ---------------------------------------------------
# Input fields
# ---------------------------------------------------

category = st.selectbox(
    "Category",
    [
        "Electronics",
        "Apparel",
        "Footwear",
        "Home Goods"
    ]
)

# Subcategory changes dynamically based on category

sub_category = st.selectbox(
    "Sub Category",
    subcategory_mapping[category]
)

price = st.number_input(
    "Price",
    min_value=0.0,
    value=1000.0
)

discount_pct = st.number_input(
    "Discount Percentage",
    min_value=0.0,
    max_value=100.0,
    value=10.0
)

delivery_days = st.number_input(
    "Expected Delivery Days",
    min_value=0,
    value=5
)

payment_method = st.selectbox(
    "Payment Method",
    [
        "card",
        "COD",
        "UPI",
        "netbanking",
        "wallet"
    ]
)

avg_rating = st.number_input(
    "Average Rating",
    min_value=0.0,
    max_value=5.0,
    value=4.0,
    step=0.1
)

order_date = st.date_input(
    "Order Date",
    value=datetime.today()
)


# ---------------------------------------------------
# Exact feature columns used during model training
# ---------------------------------------------------

feature_columns = [
    "price",
    "discount_pct",
    "delivery_days",
    "avg_rating",
    "order_month",
    "order_dayofweek",
    "is_weekend",

    "category_Electronics",
    "category_Footwear",
    "category_Home Goods",

    "sub_category_Air Fryers",
    "sub_category_Bedsheets",
    "sub_category_Blenders",
    "sub_category_Bluetooth Speakers",
    "sub_category_Boots",
    "sub_category_Cameras",
    "sub_category_Chargers",
    "sub_category_Coffee Makers",
    "sub_category_Cookware Sets",
    "sub_category_Dresses",
    "sub_category_Earbuds",
    "sub_category_Formal Shoes",
    "sub_category_Headphones",
    "sub_category_Jackets",
    "sub_category_Jeans",
    "sub_category_Lamps",
    "sub_category_Laptops",
    "sub_category_Loafers",
    "sub_category_Power Banks",
    "sub_category_Running Shoes",
    "sub_category_Sandals",
    "sub_category_Smartphones",
    "sub_category_Smartwatches",
    "sub_category_Sneakers",
    "sub_category_Storage Bins",
    "sub_category_Sweaters",
    "sub_category_T-Shirts",
    "sub_category_Tablets",
    "sub_category_Vacuum Cleaners",

    "payment_method_UPI",
    "payment_method_card",
    "payment_method_netbanking",
    "payment_method_wallet"
]


# ---------------------------------------------------
# Prediction button
# ---------------------------------------------------

if st.button("Predict Return Probability", type="primary"):

    # -----------------------------------------------
    # Convert order date
    # -----------------------------------------------

    order_date = pd.to_datetime(order_date)

    order_month = order_date.month

    # Monday = 0, Sunday = 6
    order_dayofweek = order_date.dayofweek

    is_weekend = int(order_dayofweek >= 5)


    # -----------------------------------------------
    # Create empty input dictionary
    # Set all encoded columns to 0 initially
    # -----------------------------------------------

    input_data = {
        column: 0
        for column in feature_columns
    }


    # -----------------------------------------------
    # Add numerical values
    # -----------------------------------------------

    input_data["price"] = price
    input_data["discount_pct"] = discount_pct
    input_data["delivery_days"] = delivery_days
    input_data["avg_rating"] = avg_rating

    input_data["order_month"] = order_month
    input_data["order_dayofweek"] = order_dayofweek
    input_data["is_weekend"] = is_weekend


    # -----------------------------------------------
    # One-hot encode Category
    #
    # Apparel is assumed to be the baseline category
    # because there is no category_Apparel column
    # -----------------------------------------------

    category_column = f"category_{category}"

    if category_column in input_data:
        input_data[category_column] = 1


    # -----------------------------------------------
    # One-hot encode Sub Category
    #
    # Activewear is assumed to be the baseline because
    # there is no sub_category_Activewear column
    # -----------------------------------------------

    subcategory_column = f"sub_category_{sub_category}"

    if subcategory_column in input_data:
        input_data[subcategory_column] = 1


    # -----------------------------------------------
    # One-hot encode Payment Method
    #
    # COD is assumed to be the baseline category
    # -----------------------------------------------

    payment_column = f"payment_method_{payment_method}"

    if payment_column in input_data:
        input_data[payment_column] = 1


    # -----------------------------------------------
    # Create DataFrame
    # -----------------------------------------------

    input_df = pd.DataFrame(
        [input_data],
        columns=feature_columns
    )


    # -----------------------------------------------
    # Display transformed input data
    # Optional - useful for debugging
    # -----------------------------------------------

    with st.expander("View Model Input Data"):
        st.dataframe(input_df)


    # -----------------------------------------------
    # Scale input data
    # -----------------------------------------------

    input_scaled = scaler.transform(input_df)


    # -----------------------------------------------
    # Get probability of Returned = Class 1
    # -----------------------------------------------

    return_probability = model.predict_proba(
        input_scaled
    )[0][1]


    # -----------------------------------------------
    # Apply threshold
    # -----------------------------------------------

    threshold = 0.34

    prediction = int(
        return_probability >= threshold
    )


    # -----------------------------------------------
    # Display prediction
    # -----------------------------------------------

    st.divider()

    st.subheader("Prediction Result")

    # st.metric(
    #     "Return Probability",
    #     f"{return_probability:.2%}"
    # )

    # st.write(
    #     f"Decision Threshold: **{threshold}**"
    # )


    if prediction == 1:

        st.warning("⚠️ Prediction: This product is likely to be returned.")

        prediction_text = "LIKELY TO BE RETURNED"

    else:

        st.success(
            "✅ Prediction: This product is unlikely to be returned."
        )

        prediction_text = "UNLIKELY TO BE RETURNED"


    # -----------------------------------------------
    # Generate LLM explanation
    # -----------------------------------------------

    prompt = f"""
You are an assistant for StrideWell, an e-commerce company.

A machine learning model has analyzed the following product
and order information:

Category: {category}
Sub Category: {sub_category}
Price: {price}
Discount Percentage: {discount_pct}%
Expected Delivery Days: {delivery_days}
Payment Method: {payment_method}
Average Rating: {avg_rating}
Order Date: {order_date.date()}

The machine learning model calculated:

Return Probability: {return_probability:.2%}
Decision Threshold: {threshold}

Final Model Prediction:
{prediction_text}

Explain this prediction clearly and concisely to the user.

Important rules:
- Do not claim certainty.
- Clearly state that this is a machine learning prediction.
- Explain whether the product is likely or unlikely to be returned.
- Mention the calculated return probability.
- Keep the response under 150 words.
- Do not invent specific reasons that the model did not explicitly provide.
"""


    try:

        with st.spinner("Generating explanation..."):

            response = client.messages.create(
                model="claude-sonnet-4-5",
                max_tokens=300,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )

            reply = response.content[0].text

        st.subheader("AI Explanation")

        st.chat_message("assistant").write(reply)


    except Exception as e:

        st.warning(
            "Prediction was generated, but the AI explanation "
            "could not be generated."
        )

        st.exception(e)