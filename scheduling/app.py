import streamlit as st
import pandas as pd
import json
import sys
import os
tab1, tab2 = st.tabs(["Data", "ranker"])
df = pd.DataFrame(pd.read_csv('m.csv'))

with open("avgs.json", "r") as goy:
    avgs = json.load(goy)

extra_df = pd.DataFrame(pd.read_csv('custom.csv'))
def update(col_num, selector, multiplier):
    try:
        selector_1_multiplier = float(st.session_state[multiplier])
    except:
        selector_1_multiplier = 1.0
    row = {
        f"multiplier{col_num}": multiplier,
        f"selector{col_num}": selector}
    add_df = pd.read_csv('custom.csv')
    add_df = pd.concat([add_df, pd.DataFrame([row])], ignore_index=True)
    add_df.to_csv('custom.csv', index=False)


max_rows = len(df[["Team_Number"]])

st.data_editor(
    df,
    column_order=("Team_Number","Pickability","Available_Teams", "Values1", "Values2", "Values3", "Values4"),
    num_rows= "dynamic",
    hide_index=True,
    disabled=["widgets"],
    key = "chud"
    )
st.write(st.session_state["chud"])


with tab1:
    col1, col2, col3, col4, col5, col6, col7, col8 = st.columns(8)
    st.write("work in progress")
with tab2:
    col1, col2, col3, col4, col5, col6, col7, col8 = st.columns(8)
    label = "multiplier"
    with col1:
        if st.button("run"):
            update(5, st.session_state["selector_1"], st.session_state["multiplier_1"])
            update(6, st.session_state["selector_2"], st.session_state["multiplier_2"])
            update(7, st.session_state["selector_3"], st.session_state["multiplier_3"])
            update(8, st.session_state["selector_4"], st.session_state["multiplier_4"])
            update(None, st.session_state)

    with col5:
        selector_1 = st.selectbox("Criteria", ["AUTO points", "Teleop Points", "Endgame Points", "Climb"], key = "selector_1")
        selector_1_multiplier = st.text_input(label, key = "multiplier_1")
        

    with col6:
        selector_2 = st.selectbox("Criteria", ["AUTO points", "Teleop Points", "Endgame Points", "Climb"],key = "selector_2")
        selector_2_multiplier = st.text_input(label, key = "multiplier_2")

    with col7:
        selector_3 = st.selectbox("Criteria", ["AUTO points", "Teleop Points", "Endgame Points", "Climb"], key = "selector_3")
        selector_3_multiplier = st.text_input(label, key = "multiplier_3")

    with col8:
        selector_4 = st.selectbox("Criteria", ["AUTO points", "Teleop Points", "Endgame Points", "Climb"],key = "selector_4")
        selector_4_multiplier = st.text_input(label, key = "multiplier_4")
