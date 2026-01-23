import streamlit as st
import pandas as pd
tab1, tab2 = st.tabs(["Data", "ranker"])
df = pd.DataFrame(pd.read_csv('m.csv'))
import time
extra_df = pd.DataFrame(pd.read_csv('custom.csv'))

def update(s1,m1,s2,m2,s3,m3,s4,m4):
    row = {
        "multiplier1":m1, "selector1" :s1,
        "multiplier2":m2, "selector2" :s2,
        "multiplier3":m3, "selector3" :s3,
        "multiplier4":m4, "selector4" :s4,
}
    extra_df = pd.read_csv('custom.csv')
    extra_df = pd.concat([extra_df, pd.DataFrame([row])], ignore_index=True)
    extra_df.to_csv('custom.csv', index=False)
    

max_rows = len(df[["Team_Number"]])



with tab1:
    col1, col2, col3, col4, col5, col6, col7, col8 = st.columns(8)
    st.write("work in progress")
with tab2:

    col1, col2, col3, col4, col5, col6, col7, col8 = st.columns(8)
    label = "multiplier"
    with col1:
        if st.button("run"):
            update(st.session_state["selector_1"], st.session_state["multiplier_1"], 
                   st.session_state["selector_2"], st.session_state["multiplier_2"],
                   st.session_state["selector_3"], st.session_state["multiplier_3"],
                   st.session_state["selector_4"], st.session_state["multiplier_4"])
            extra_df = pd.DataFrame(pd.read_csv("custom.csv"))
            df["Values1"]=df["Values1"].astype(object) *extra_df.iloc[-1][f"multiplier1"]
            df["Values2"]=df["Values2"].astype(object) *extra_df.iloc[-1][f"multiplier2"]
            df["Values3"]=df["Values3"].astype(object) *extra_df.iloc[-1][f"multiplier3"]
            df["Values4"]=df["Values4"].astype(object) *extra_df.iloc[-1][f"multiplier4"]

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
        
    st.data_editor(
    df,
    column_order=("Team_Number","Selected","Pickability","Available_Teams", "Values1", "Values2", "Values3", "Values4"),
    hide_index=True,
    disabled=["widgets"],
    key = "chud"
    )

