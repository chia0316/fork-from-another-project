import json

import altair as alt
import pandas as pd
import streamlit as st

from helper_functions.utility import check_password


# region <--------- Streamlit App Configuration --------->
st.set_page_config(
    layout="wide",
    page_title="Course Dashboard"
)

# Check if the password is correct.
if not check_password():
    st.stop()
# endregion <--------- Streamlit App Configuration --------->

SERIES_COLOR = "#2a78d6"   # single-series marks
MUTED_COLOR = "#b4b2a9"    # de-emphasised marks when a category is highlighted


@st.cache_data
def load_courses():
    with open('./data/courses-full.json', 'r', encoding='utf-8') as file:
        dict_of_courses = json.load(file)

    df = pd.DataFrame(list(dict_of_courses.values()))
    df['weeks'] = df['duration'].str.extract(r'(\d+)').astype(int)
    df['price_per_week'] = (df['price'] / df['weeks']).round(2)
    df['skills'] = df['skills_covered'].apply(', '.join)
    return df


df_all = load_courses()

st.title("Course Dashboard")
st.caption("Explore our course catalogue - compare categories, prices, ratings and value for money.")


# region <--------- Filters --------->
f1, f2, f3, f4 = st.columns(4)
categories = f1.multiselect("Category", sorted(df_all['category'].unique()), placeholder="All categories")
providers = f2.multiselect("Provider", sorted(df_all['provider'].unique()), placeholder="All providers")
min_price, max_price = float(df_all['price'].min()), float(df_all['price'].max())
price_range = f3.slider("Price ($)", min_price, max_price, (min_price, max_price), step=50.0)
min_rating = f4.slider("Minimum rating", 4.0, 5.0, 4.0, step=0.1)

df = df_all[
    (df_all['category'].isin(categories) if categories else True)
    & (df_all['provider'].isin(providers) if providers else True)
    & df_all['price'].between(*price_range)
    & (df_all['rating'] >= min_rating)
]

if df.empty:
    st.info("No courses match these filters. Try widening the price range or lowering the minimum rating.")
    st.stop()
# endregion <--------- Filters --------->


# region <--------- KPIs --------->
k1, k2, k3, k4 = st.columns(4)
k1.metric("Courses", len(df), border=True)
k2.metric("Average price", f"${df['price'].mean():,.2f}", border=True)
k3.metric("Average rating", f"{df['rating'].mean():.2f} / 5", border=True)
k4.metric("Average duration", f"{df['weeks'].mean():.1f} weeks", border=True)
# endregion <--------- KPIs --------->


# region <--------- Category overview --------->
by_category = (
    df.groupby('category')
    .agg(courses=('name', 'count'), avg_price=('price', 'mean'), avg_rating=('rating', 'mean'))
    .reset_index()
)

c1, c2 = st.columns(2)

with c1:
    st.subheader("Courses per category")
    chart = alt.Chart(by_category).mark_bar(
        color=SERIES_COLOR, cornerRadiusEnd=4, size=18
    ).encode(
        x=alt.X('courses:Q', title='Courses', axis=alt.Axis(tickMinStep=1)),
        y=alt.Y('category:N', title=None, sort='-x'),
        tooltip=[
            alt.Tooltip('category:N', title='Category'),
            alt.Tooltip('courses:Q', title='Courses'),
        ],
    )
    st.altair_chart(chart, use_container_width=True)

with c2:
    st.subheader("Average price by category")
    chart = alt.Chart(by_category).mark_bar(
        color=SERIES_COLOR, cornerRadiusEnd=4, size=18
    ).encode(
        x=alt.X('avg_price:Q', title='Average price ($)', axis=alt.Axis(format='$,.0f')),
        y=alt.Y('category:N', title=None, sort='-x'),
        tooltip=[
            alt.Tooltip('category:N', title='Category'),
            alt.Tooltip('avg_price:Q', title='Average price', format='$,.2f'),
            alt.Tooltip('avg_rating:Q', title='Average rating', format='.2f'),
            alt.Tooltip('courses:Q', title='Courses'),
        ],
    )
    st.altair_chart(chart, use_container_width=True)
# endregion <--------- Category overview --------->


# region <--------- Value for money --------->
st.divider()
st.header("Value for money")

v1, v2 = st.columns([3, 2])

with v1:
    st.subheader("Price vs rating")
    highlight = st.selectbox(
        "Highlight a category",
        ["None"] + sorted(df['category'].unique()),
        help="Dot size shows course length in weeks.",
    )
    df_scatter = df.assign(highlighted=(df['category'] == highlight) | (highlight == "None"))
    chart = alt.Chart(df_scatter).mark_circle(
        opacity=0.85, stroke='white', strokeWidth=2
    ).encode(
        x=alt.X('price:Q', title='Price ($)', scale=alt.Scale(zero=False, padding=20),
                axis=alt.Axis(format='$,.0f')),
        y=alt.Y('rating:Q', title='Rating', scale=alt.Scale(zero=False, padding=20)),
        size=alt.Size('weeks:Q', title='Weeks', scale=alt.Scale(range=[80, 600])),
        color=alt.condition('datum.highlighted', alt.value(SERIES_COLOR), alt.value(MUTED_COLOR)),
        order=alt.Order('highlighted:O'),  # draw highlighted dots on top
        tooltip=[
            alt.Tooltip('name:N', title='Course'),
            alt.Tooltip('category:N', title='Category'),
            alt.Tooltip('provider:N', title='Provider'),
            alt.Tooltip('price:Q', title='Price', format='$,.2f'),
            alt.Tooltip('rating:Q', title='Rating'),
            alt.Tooltip('duration:N', title='Duration'),
        ],
    )
    st.altair_chart(chart, use_container_width=True)

with v2:
    st.subheader("Best value courses")
    st.caption("Lowest price per week of learning, then highest rating.")
    best_value = df.sort_values(['price_per_week', 'rating'], ascending=[True, False]).head(5)
    st.dataframe(
        best_value[['name', 'price_per_week', 'rating', 'duration']],
        hide_index=True,
        use_container_width=True,
        column_config={
            'name': st.column_config.TextColumn('Course'),
            'price_per_week': st.column_config.NumberColumn('Price / week', format='$%.2f'),
            'rating': st.column_config.NumberColumn('Rating', format='%.1f ⭐'),
            'duration': st.column_config.TextColumn('Duration'),
        },
    )

st.subheader("Price per week")
chart = alt.Chart(df).mark_bar(
    color=SERIES_COLOR, cornerRadiusEnd=4, size=14
).encode(
    x=alt.X('price_per_week:Q', title='Price per week ($)', axis=alt.Axis(format='$,.0f')),
    y=alt.Y('name:N', title=None, sort='x'),
    tooltip=[
        alt.Tooltip('name:N', title='Course'),
        alt.Tooltip('price_per_week:Q', title='Price / week', format='$,.2f'),
        alt.Tooltip('price:Q', title='Total price', format='$,.2f'),
        alt.Tooltip('duration:N', title='Duration'),
    ],
).properties(height=max(200, 28 * len(df)))
st.altair_chart(chart, use_container_width=True)
# endregion <--------- Value for money --------->


# region <--------- Course table --------->
st.divider()
st.header("All matching courses")
st.dataframe(
    df[['name', 'category', 'provider', 'course_code', 'duration', 'rating', 'price', 'price_per_week', 'skills']],
    hide_index=True,
    use_container_width=True,
    column_config={
        'name': st.column_config.TextColumn('Course'),
        'category': st.column_config.TextColumn('Category'),
        'provider': st.column_config.TextColumn('Provider'),
        'course_code': st.column_config.TextColumn('Code'),
        'duration': st.column_config.TextColumn('Duration'),
        'rating': st.column_config.NumberColumn('Rating', format='%.1f'),
        'price': st.column_config.NumberColumn('Price', format='$%.2f'),
        'price_per_week': st.column_config.NumberColumn('Price / week', format='$%.2f'),
        'skills': st.column_config.TextColumn('Skills covered'),
    },
)
# endregion <--------- Course table --------->
