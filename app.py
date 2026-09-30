import json
import os
import uuid
from datetime import date, datetime, timedelta

import pandas as pd
import plotly.express as px
import streamlit as st


# ============================================================
# APPLICATION CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="Expense Tracker",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ============================================================
# CONSTANTS
# ============================================================

DATA_FILE = "expenses.json"

CATEGORIES = [
    "Food",
    "Travel",
    "Education",
    "Shopping",
    "Bills",
    "Entertainment",
    "Health",
    "Other"
]

PAYMENT_METHODS = [
    "Cash",
    "UPI",
    "Credit Card",
    "Debit Card",
    "Bank Transfer",
    "Other"
]


# ============================================================
# CUSTOM CSS
# ============================================================

def load_css():
    st.markdown(
        """
        <style>

        .main {
            background-color: #f7f9fc;
        }

        .block-container {
            padding-top: 2rem;
            padding-bottom: 2rem;
        }

        .app-title {
            font-size: 2.2rem;
            font-weight: 700;
            color: #17365d;
            margin-bottom: 0.2rem;
        }

        .app-subtitle {
            color: #64748b;
            font-size: 1rem;
            margin-bottom: 1.5rem;
        }

        .metric-card {
            background: white;
            padding: 1.2rem;
            border-radius: 14px;
            border: 1px solid #e5e7eb;
            box-shadow: 0 3px 12px rgba(0, 0, 0, 0.05);
            min-height: 120px;
        }

        .metric-title {
            color: #64748b;
            font-size: 0.9rem;
            margin-bottom: 0.5rem;
        }

        .metric-value {
            color: #17365d;
            font-size: 1.7rem;
            font-weight: 700;
        }

        .section-title {
            color: #17365d;
            font-size: 1.35rem;
            font-weight: 650;
            margin-top: 1rem;
            margin-bottom: 0.8rem;
        }

        .info-box {
            padding: 1rem;
            background-color: #eef5ff;
            border-left: 4px solid #2563eb;
            border-radius: 8px;
            margin-bottom: 1rem;
        }

        div[data-testid="stForm"] {
            background-color: white;
            padding: 1rem;
            border-radius: 14px;
            border: 1px solid #e5e7eb;
        }

        </style>
        """,
        unsafe_allow_html=True
    )


load_css()


# ============================================================
# JSON FILE FUNCTIONS
# ============================================================

def initialize_data_file():
    """
    Create expenses.json if it does not already exist.
    """

    if not os.path.exists(DATA_FILE):
        with open(DATA_FILE, "w", encoding="utf-8") as file:
            json.dump([], file, indent=4)


def load_expenses():
    """
    Read all expenses from expenses.json.
    """

    initialize_data_file()

    try:
        with open(DATA_FILE, "r", encoding="utf-8") as file:
            data = json.load(file)

        if isinstance(data, list):
            return data

        return []

    except (json.JSONDecodeError, OSError):
        return []


def save_expenses(expenses):
    """
    Save all expenses to expenses.json.

    A temporary file is used first so that the original file
    is less likely to be left partially written.
    """

    temporary_file = DATA_FILE + ".tmp"

    with open(temporary_file, "w", encoding="utf-8") as file:
        json.dump(expenses, file, indent=4, ensure_ascii=False)

    os.replace(temporary_file, DATA_FILE)


# ============================================================
# EXPENSE CRUD FUNCTIONS
# ============================================================

def generate_expense_id():
    """
    Generate a unique expense ID.
    """

    today = datetime.now().strftime("%Y%m%d")
    random_part = uuid.uuid4().hex[:6].upper()

    return f"EXP-{today}-{random_part}"


def add_expense(expense_date, category, description, amount, payment_method):
    """
    Add a new expense.
    """

    expenses = load_expenses()

    new_expense = {
        "id": generate_expense_id(),
        "date": expense_date.isoformat(),
        "category": category,
        "description": description.strip(),
        "amount": round(float(amount), 2),
        "payment_method": payment_method
    }

    expenses.append(new_expense)
    save_expenses(expenses)


def update_expense(
    expense_id,
    expense_date,
    category,
    description,
    amount,
    payment_method
):
    """
    Update an existing expense using its ID.
    """

    expenses = load_expenses()

    for expense in expenses:
        if expense["id"] == expense_id:
            expense["date"] = expense_date.isoformat()
            expense["category"] = category
            expense["description"] = description.strip()
            expense["amount"] = round(float(amount), 2)
            expense["payment_method"] = payment_method

            save_expenses(expenses)
            return True

    return False


def delete_expense(expense_id):
    """
    Delete an expense using its ID.
    """

    expenses = load_expenses()

    updated_expenses = [
        expense
        for expense in expenses
        if expense["id"] != expense_id
    ]

    if len(updated_expenses) == len(expenses):
        return False

    save_expenses(updated_expenses)

    return True


# ============================================================
# VALIDATION
# ============================================================

def validate_expense(
    expense_date,
    category,
    description,
    amount,
    payment_method
):
    """
    Validate expense form values.
    """

    errors = []

    if expense_date is None:
        errors.append("Please select a date.")

    if not category:
        errors.append("Please select a category.")

    if not description.strip():
        errors.append("Description cannot be empty.")

    if amount is None:
        errors.append("Please enter an amount.")
    elif amount <= 0:
        errors.append("Amount must be greater than zero.")

    if not payment_method:
        errors.append("Please select a payment method.")

    return errors


# ============================================================
# DATAFRAME FUNCTION
# ============================================================

def expenses_to_dataframe(expenses):
    """
    Convert expense list into a Pandas DataFrame.
    """

    if not expenses:
        return pd.DataFrame(
            columns=[
                "id",
                "date",
                "category",
                "description",
                "amount",
                "payment_method"
            ]
        )

    dataframe = pd.DataFrame(expenses)

    dataframe["date"] = pd.to_datetime(
        dataframe["date"],
        errors="coerce"
    )

    dataframe["amount"] = pd.to_numeric(
        dataframe["amount"],
        errors="coerce"
    )

    return dataframe


# ============================================================
# FILTER FUNCTION
# ============================================================

def apply_filters(
    dataframe,
    selected_dates,
    selected_categories,
    selected_payment_methods
):
    """
    Apply dashboard filters.
    """

    filtered = dataframe.copy()

    if not filtered.empty:

        # Date filter
        if selected_dates and len(selected_dates) == 2:

            start_date = pd.Timestamp(selected_dates[0])
            end_date = pd.Timestamp(selected_dates[1])

            filtered = filtered[
                (filtered["date"] >= start_date)
                & (filtered["date"] <= end_date)
            ]

        # Category filter
        if selected_categories:
            filtered = filtered[
                filtered["category"].isin(selected_categories)
            ]

        # Payment method filter
        if selected_payment_methods:
            filtered = filtered[
                filtered["payment_method"].isin(selected_payment_methods)
            ]

    return filtered


# ============================================================
# DASHBOARD METRICS
# ============================================================

def calculate_metrics(dataframe):
    """
    Calculate dashboard statistics.
    """

    if dataframe.empty:
        return {
            "total": 0,
            "transactions": 0,
            "average": 0,
            "highest": 0
        }

    total = dataframe["amount"].sum()
    transactions = len(dataframe)
    average = dataframe["amount"].mean()
    highest = dataframe["amount"].max()

    return {
        "total": total,
        "transactions": transactions,
        "average": average,
        "highest": highest
    }


# ============================================================
# FORMAT CURRENCY
# ============================================================

def format_currency(value):
    """
    Format number as Indian Rupee.
    """

    return f"₹{value:,.2f}"


# ============================================================
# PAGE HEADER
# ============================================================

st.markdown(
    '<div class="app-title">💰 Expense Tracker</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="app-subtitle">'
    'Track, manage, and understand your personal expenses.'
    '</div>',
    unsafe_allow_html=True
)


# ============================================================
# SESSION STATE
# ============================================================

if "message" not in st.session_state:
    st.session_state.message = None

if "message_type" not in st.session_state:
    st.session_state.message_type = "success"

if "selected_expense" not in st.session_state:
    st.session_state.selected_expense = None


# ============================================================
# LOAD DATA
# ============================================================

expenses = load_expenses()
df = expenses_to_dataframe(expenses)


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.header("⚙️ Controls")

    page = st.radio(
        "Navigate",
        [
            "📊 Dashboard",
            "➕ Add Expense",
            "✏️ Edit Expense",
            "🗑️ Delete Expense",
            "📋 View Expenses"
        ]
    )

    st.divider()

    st.markdown("### 📁 Storage")

    st.caption(
        "All expenses are stored locally in "
        "`expenses.json`."
    )

    st.divider()

    st.markdown("### 📌 Categories")

    for category in CATEGORIES:
        st.caption(f"• {category}")


# ============================================================
# SHOW SESSION MESSAGE
# ============================================================

if st.session_state.message:

    if st.session_state.message_type == "success":
        st.success(st.session_state.message)

    elif st.session_state.message_type == "error":
        st.error(st.session_state.message)

    else:
        st.info(st.session_state.message)

    st.session_state.message = None


# ============================================================
# DASHBOARD
# ============================================================

if page == "📊 Dashboard":

    st.markdown(
        '<div class="section-title">📊 Dashboard</div>',
        unsafe_allow_html=True
    )

    if df.empty:

        st.info(
            "No expenses have been added yet. "
            "Use 'Add Expense' from the sidebar to get started."
        )

    else:

        # ----------------------------------------------------
        # FILTERS
        # ----------------------------------------------------

        st.markdown("### 🔎 Filters")

        filter_col1, filter_col2, filter_col3 = st.columns(3)

        minimum_date = df["date"].min().date()
        maximum_date = df["date"].max().date()

        with filter_col1:

            selected_dates = st.date_input(
                "Date Range",
                value=(minimum_date, maximum_date),
                min_value=minimum_date,
                max_value=maximum_date
            )

        with filter_col2:

            selected_categories = st.multiselect(
                "Category",
                options=CATEGORIES,
                default=[]
            )

        with filter_col3:

            available_payment_methods = sorted(
                df["payment_method"].dropna().unique().tolist()
            )

            selected_payment_methods = st.multiselect(
                "Payment Method",
                options=available_payment_methods,
                default=[]
            )

        filtered_df = apply_filters(
            df,
            selected_dates,
            selected_categories,
            selected_payment_methods
        )

        # ----------------------------------------------------
        # METRICS
        # ----------------------------------------------------

        metrics = calculate_metrics(filtered_df)

        metric1, metric2, metric3, metric4 = st.columns(4)

        with metric1:
            st.markdown(
                f"""
                <div class="metric-card">
                    <div class="metric-title">💰 Total Expenses</div>
                    <div class="metric-value">
                        {format_currency(metrics["total"])}
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

        with metric2:
            st.markdown(
                f"""
                <div class="metric-card">
                    <div class="metric-title">🧾 Transactions</div>
                    <div class="metric-value">
                        {metrics["transactions"]}
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

        with metric3:
            st.markdown(
                f"""
                <div class="metric-card">
                    <div class="metric-title">📈 Average Expense</div>
                    <div class="metric-value">
                        {format_currency(metrics["average"])}
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

        with metric4:
            st.markdown(
                f"""
                <div class="metric-card">
                    <div class="metric-title">🔥 Highest Expense</div>
                    <div class="metric-value">
                        {format_currency(metrics["highest"])}
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

        st.write("")

        # ----------------------------------------------------
        # CHARTS
        # ----------------------------------------------------

        if filtered_df.empty:

            st.warning(
                "No expenses match the selected filters."
            )

        else:

            chart_col1, chart_col2 = st.columns(2)

            # Expenses by Category
            with chart_col1:

                category_data = (
                    filtered_df
                    .groupby("category", as_index=False)["amount"]
                    .sum()
                    .sort_values("amount", ascending=False)
                )

                fig_category = px.bar(
                    category_data,
                    x="category",
                    y="amount",
                    title="Expenses by Category",
                    labels={
                        "category": "Category",
                        "amount": "Amount (₹)"
                    },
                    text_auto=".2f"
                )

                fig_category.update_layout(
                    template="plotly_white",
                    height=420
                )

                st.plotly_chart(
                    fig_category,
                    use_container_width=True
                )

            # Payment Method Distribution
            with chart_col2:

                payment_data = (
                    filtered_df
                    .groupby(
                        "payment_method",
                        as_index=False
                    )["amount"]
                    .sum()
                )

                fig_payment = px.pie(
                    payment_data,
                    names="payment_method",
                    values="amount",
                    title="Payment Method Distribution",
                    hole=0.45
                )

                fig_payment.update_layout(
                    template="plotly_white",
                    height=420
                )

                st.plotly_chart(
                    fig_payment,
                    use_container_width=True
                )

            # ------------------------------------------------
            # EXPENSES OVER TIME
            # ------------------------------------------------

            daily_data = (
                filtered_df
                .groupby("date", as_index=False)["amount"]
                .sum()
                .sort_values("date")
            )

            fig_time = px.line(
                daily_data,
                x="date",
                y="amount",
                markers=True,
                title="Expenses Over Time",
                labels={
                    "date": "Date",
                    "amount": "Amount (₹)"
                }
            )

            fig_time.update_layout(
                template="plotly_white",
                height=420
            )

            st.plotly_chart(
                fig_time,
                use_container_width=True
            )


# ============================================================
# ADD EXPENSE
# ============================================================

elif page == "➕ Add Expense":

    st.markdown(
        '<div class="section-title">➕ Add Expense</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        """
        <div class="info-box">
            Enter your expense details below. All required fields
            must be completed before saving.
        </div>
        """,
        unsafe_allow_html=True
    )

    with st.form("add_expense_form", clear_on_submit=True):

        col1, col2 = st.columns(2)

        with col1:

            expense_date = st.date_input(
                "Date *",
                value=date.today()
            )

            category = st.selectbox(
                "Category *",
                CATEGORIES
            )

            description = st.text_input(
                "Description *",
                placeholder="Example: Lunch at restaurant"
            )

        with col2:

            amount = st.number_input(
                "Amount *",
                min_value=0.0,
                step=10.0,
                format="%.2f"
            )

            payment_method = st.selectbox(
                "Payment Method *",
                PAYMENT_METHODS
            )

        submitted = st.form_submit_button(
            "💾 Save Expense",
            use_container_width=True
        )

        if submitted:

            errors = validate_expense(
                expense_date,
                category,
                description,
                amount,
                payment_method
            )

            if errors:

                for error in errors:
                    st.error(error)

            else:

                add_expense(
                    expense_date,
                    category,
                    description,
                    amount,
                    payment_method
                )

                st.session_state.message = (
                    "Expense added successfully."
                )

                st.session_state.message_type = "success"

                st.rerun()


# ============================================================
# EDIT EXPENSE
# ============================================================

elif page == "✏️ Edit Expense":

    st.markdown(
        '<div class="section-title">✏️ Edit Expense</div>',
        unsafe_allow_html=True
    )

    expenses = load_expenses()

    if not expenses:

        st.info("There are no expenses available to edit.")

    else:

        expense_options = {
            f'{expense["id"]} | '
            f'{expense["description"]} | '
            f'₹{expense["amount"]:,.2f}':
            expense["id"]
            for expense in expenses
        }

        selected_label = st.selectbox(
            "Select Expense",
            list(expense_options.keys())
        )

        selected_id = expense_options[selected_label]

        selected_expense = next(
            (
                expense
                for expense in expenses
                if expense["id"] == selected_id
            ),
            None
        )

        if selected_expense:

            original_date = datetime.strptime(
                selected_expense["date"],
                "%Y-%m-%d"
            ).date()

            category_index = (
                CATEGORIES.index(
                    selected_expense["category"]
                )
                if selected_expense["category"] in CATEGORIES
                else 0
            )

            payment_index = (
                PAYMENT_METHODS.index(
                    selected_expense["payment_method"]
                )
                if selected_expense["payment_method"]
                in PAYMENT_METHODS
                else 0
            )

            with st.form("edit_expense_form"):

                col1, col2 = st.columns(2)

                with col1:

                    edit_date = st.date_input(
                        "Date *",
                        value=original_date
                    )

                    edit_category = st.selectbox(
                        "Category *",
                        CATEGORIES,
                        index=category_index
                    )

                    edit_description = st.text_input(
                        "Description *",
                        value=selected_expense["description"]
                    )

                with col2:

                    edit_amount = st.number_input(
                        "Amount *",
                        min_value=0.0,
                        value=float(selected_expense["amount"]),
                        step=10.0,
                        format="%.2f"
                    )

                    edit_payment_method = st.selectbox(
                        "Payment Method *",
                        PAYMENT_METHODS,
                        index=payment_index
                    )

                update_button = st.form_submit_button(
                    "🔄 Update Expense",
                    use_container_width=True
                )

                if update_button:

                    errors = validate_expense(
                        edit_date,
                        edit_category,
                        edit_description,
                        edit_amount,
                        edit_payment_method
                    )

                    if errors:

                        for error in errors:
                            st.error(error)

                    else:

                        updated = update_expense(
                            selected_id,
                            edit_date,
                            edit_category,
                            edit_description,
                            edit_amount,
                            edit_payment_method
                        )

                        if updated:

                            st.session_state.message = (
                                "Expense updated successfully."
                            )

                            st.session_state.message_type = "success"

                            st.rerun()

                        else:

                            st.error(
                                "The selected expense could not be found."
                            )


# ============================================================
# DELETE EXPENSE
# ============================================================

elif page == "🗑️ Delete Expense":

    st.markdown(
        '<div class="section-title">🗑️ Delete Expense</div>',
        unsafe_allow_html=True
    )

    expenses = load_expenses()

    if not expenses:

        st.info("There are no expenses available to delete.")

    else:

        expense_options = {
            f'{expense["id"]} | '
            f'{expense["description"]} | '
            f'₹{expense["amount"]:,.2f}':
            expense["id"]
            for expense in expenses
        }

        selected_label = st.selectbox(
            "Select Expense to Delete",
            list(expense_options.keys())
        )

        selected_id = expense_options[selected_label]

        selected_expense = next(
            (
                expense
                for expense in expenses
                if expense["id"] == selected_id
            ),
            None
        )

        if selected_expense:

            st.warning(
                f'You are about to delete '
                f'"{selected_expense["description"]}" '
                f'for {format_currency(selected_expense["amount"])}.'
            )

            confirm_delete = st.checkbox(
                "I understand that this expense will be permanently deleted."
            )

            if st.button(
                "🗑️ Delete Expense",
                type="primary",
                disabled=not confirm_delete,
                use_container_width=True
            ):

                deleted = delete_expense(selected_id)

                if deleted:

                    st.session_state.message = (
                        "Expense deleted successfully."
                    )

                    st.session_state.message_type = "success"

                    st.rerun()

                else:

                    st.error(
                        "The selected expense could not be found."
                    )


# ============================================================
# VIEW EXPENSES
# ============================================================

elif page == "📋 View Expenses":

    st.markdown(
        '<div class="section-title">📋 All Expenses</div>',
        unsafe_allow_html=True
    )

    expenses = load_expenses()

    if not expenses:

        st.info(
            "No expenses available. "
            "Add your first expense from the sidebar."
        )

    else:

        view_df = expenses_to_dataframe(expenses)

        # ----------------------------------------------------
        # VIEW FILTERS
        # ----------------------------------------------------

        filter_col1, filter_col2, filter_col3 = st.columns(3)

        minimum_date = view_df["date"].min().date()
        maximum_date = view_df["date"].max().date()

        with filter_col1:

            view_dates = st.date_input(
                "Date Range",
                value=(minimum_date, maximum_date),
                min_value=minimum_date,
                max_value=maximum_date,
                key="view_date_filter"
            )

        with filter_col2:

            view_categories = st.multiselect(
                "Category",
                CATEGORIES,
                key="view_category_filter"
            )

        with filter_col3:

            view_payment_methods = st.multiselect(
                "Payment Method",
                PAYMENT_METHODS,
                key="view_payment_filter"
            )

        filtered_view_df = apply_filters(
            view_df,
            view_dates,
            view_categories,
            view_payment_methods
        )

        # ----------------------------------------------------
        # TABLE
        # ----------------------------------------------------

        if filtered_view_df.empty:

            st.warning(
                "No expenses match the selected filters."
            )

        else:

            display_df = filtered_view_df.copy()

            display_df["date"] = display_df[
                "date"
            ].dt.strftime("%d-%m-%Y")

            display_df["amount"] = display_df[
                "amount"
            ].apply(format_currency)

            display_df = display_df.rename(
                columns={
                    "id": "Expense ID",
                    "date": "Date",
                    "category": "Category",
                    "description": "Description",
                    "amount": "Amount",
                    "payment_method": "Payment Method"
                }
            )

            display_df = display_df[
                [
                    "Expense ID",
                    "Date",
                    "Category",
                    "Description",
                    "Amount",
                    "Payment Method"
                ]
            ]

            st.dataframe(
                display_df,
                use_container_width=True,
                hide_index=True
            )

            st.caption(
                f"Showing {len(filtered_view_df)} "
                f"transaction(s)."
            )


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.caption(
    "💰 Expense Tracker • Built with Python, Streamlit and Plotly"
)