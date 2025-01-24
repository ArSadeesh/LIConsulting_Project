import streamlit as st 
import pandas as pd
import numpy as np 
import plotly.graph_objects as go
import time
#----------------Sidebar--------------------------------------------------
side = st.sidebar
with side:
    st.markdown(
    "<h1 style='text-align: center; padding: 0px 10px 20px;'> A Real Options Model for Universal Life Insurance </h1>",
    unsafe_allow_html=True
    )
    st.markdown(
        """
        <div style='display: flex; align-items: center; justify-content: center; color: white; background-color: black; padding: 8px;'>
            <p style='margin: 0; margin-right: 6px;'>Created by</p>
            <a href='https://www.linkedin.com/in/arnav-sadeesh/' target='_blank' style='color: lightblue; text-decoration: none;'>
                <img src="https://cdn-icons-png.flaticon.com/512/174/174857.png" alt="LinkedIn" style="width: 15px; height: 15px; margin-right: 6px;">
                Arnav Sadeesh
            </a>
        </div>
        """,
        unsafe_allow_html=True
    )
side.markdown("---")
side.subheader("Policy Parameters")

face_amt = side.number_input(
    label="Face Amount ($)",
    value=250000,
    help="Your policy's death benefit paid to beneficiaries."
)

premium = side.number_input(
    label="Annual Premium ($)",
    value=21000,
    help="Yearly amount paid to keep the policy in force."
)

cash = side.number_input(
    label="Initial Cash Value (if any)",
    value=1000,
    help="Value of your policy that grows over time"
)

rate = side.slider(
    label="Estimated Interest Rate (%)",
    min_value=0.0,
    max_value=5.0,
    value=3.0,
    help="The estimated annual rate at which your cash value grows."
)

DISCOUNT = 0.0425
with side.expander(f"Discount Rate: **:green[{DISCOUNT:.2%}]**") :
    st.write("""
              Standard risk-neutral options pricing -- 
              future benefits discounted at the risk-free rate (*10-year UST*)""")
    
side.markdown("---")   

default_df = pd.DataFrame({
    "Year" : np.arange(1,11), "Surrender Charge (%)" : [95,45,30,20,15,12.5,10,8.5,6.5,6 ]})
default_df.set_index("Year", inplace = True)

side.subheader(
    "Your Surrender Schedule", 
    help = "Yearly fee (as a % of cash value) if you end the policy early. This fee usually decreases over time."
    )

surrender = side.data_editor(default_df, num_rows= "dynamic")
side.markdown("---")   


# Age & Mortality Table
age = side.slider(
    label="Age",
    min_value=0,
    max_value=100,
    value= 50,
    step = 1, 
)

mortality = pd.read_csv("Mortality_data.csv")
mortality.columns = ["Years", "Rate (%)"]
mortality.set_index("Years", inplace= True)
side.subheader("2024 U.S Mortality Rates")
side.dataframe(mortality)

#------#Function for Premium Percentage Going Into Cash Value---------

def prem_pct(years) : 
    if years < 5 : 
        return 0.1
    elif years < 10 :
        return 0.5
    else : 
        return 0.8
    

#-------Calculating Decision Values with Foward/Backward Induction----------------

values = np.zeros((118-age,2))

#Surrender Values
for i in range(0,len(values)) :     
    if i>=(len(surrender)) : 
        values[i][0] = (cash + premium*prem_pct(i+1))*(1+(rate/100))
    else :
        values[i][0] = (cash + premium*prem_pct(i+1)) * (1+(rate/100)) * (1-(surrender["Surrender Charge (%)"].iloc[i]/100))
    cash = values[i][0]

#Hold Values
values[-1][1] = face_amt 

policy_values = np.zeros((118-age,1))
policy_values[-1] = max(face_amt, values[-1][0])


for j in range (117, age, -1) : 
    future_val = policy_values[j-age]
    expected_val = face_amt*mortality.iloc[j] + future_val*(1-mortality.iloc[j])
    values[j-age-1][1] = np.exp(-DISCOUNT*(1))*(expected_val) - (premium*(1-prem_pct(j-age)))

    policy_values[j-age-1] = max(values[j-age-1][0], values[j-age-1][1])


#Create the DataFrame using calculations
val = pd.DataFrame(values)
val = val.round().astype(int)
val["Year"] = np.arange(1,118-age+1)
val.set_index("Year", inplace = True)
val.columns = ["Surrender", "Hold"]

#------Main Page Instructions --------------

header_placeholder = st.empty()
subheader_placeholder = st.empty()
body_placeholder = st.empty()

def populate_text() : 
    header_placeholder.header("Real Options Modeling in Life Insurance")
    subheader_placeholder.subheader("Instructions: ")
    body_placeholder.write("""
        This Real Options Model for **Universal Life Insurance** allows users to analyze and optimize policy 
        decisions by leveraging real options analysis. **_Input key policy parameters on the left_** for the model to 
        dynamically calculate and visualize the surrender value versus the continuation value at each policy year to 
        determine the choice the creates most value for your beneficiary.
        
        Using recursion, the model factors in an American-style options perspective, accounting
        for mortality risk, the accumulation of cash value, the time value of money, and the influence
        of future expected value. 
        """)

populate_text()
st.markdown("---")

#-----------Bottom Insights ------------------------------

#Finding Crossing Point 
cross_value = val[val["Surrender"] > val["Hold"]]
cross_surr = cross_value["Surrender"].iloc[0]
cross_hold = cross_value["Hold"].iloc[0]
cross_index = cross_value.index[0]

def insights() : 
    st.markdown("---")

    if (not cross_value.empty) : 
        st.markdown(
            """
            <style>
            .stAlert {
                text-align: center; 
            }
            </style>
            """,
            unsafe_allow_html=True
        )
        st.info(f"""
                **Year *{cross_index}* of your policy is your threshold -- after which your surrender 
                value reaches *\${cross_surr:,}* over your the hold value of *\${cross_hold:,}***.
                After this point, is optimal to consider taking your cash value over holding out for the death
                benefit.
                """)
        c1, c2, c3 = st.columns(3) 
        with c2: 
            with st.expander ("See All Calculated Data", ) : 
                val

        time.sleep(2)
        st.write("***")
        st.warning("""
                *Note that this model is NOT financial advice --- please use it solely as a visualization tool to 
                build a a more informed perspective on your policy!*
                """)
    else : 
        st.info("""
                Your policy does not have a point where surrender values overtake hold values. It is always more
                optimal to hold out for your death benefit vs. surrendering your cash value!
                """)
    
#-------------Visualizations-----------------------------

col1, col2, col3 = st.columns(3)
with col2: 
    st.markdown(
    """
    <style>
    div.stButton > button {
        color: black; /* Changes text color to black */
    }
    </style>
    """,
    unsafe_allow_html=True
    )
    viz = st.button("Visualize My Policy", type = "primary", icon = "📊")

with st.container() : 
    chart_placeholder = st.empty()

fig1 = go.Figure()

fig1.add_trace(go.Scatter (
    x=[], 
    y=[], 
    mode='lines+markers',  
    name='Surrender Values' 
))

fig1.add_trace(go.Scatter(
    x=[], 
    y=[], 
    mode='lines+markers',
    name='Hold Values'
))

fig1.update_layout(
    title="Surrender vs. Hold Value",
    xaxis_title="Years",
    yaxis_title="Value",
    legend_title="Legend",
    legend=dict(
        x=1.05,  
        y=1,     
        bgcolor="rgba(255, 255, 255, 0.5)",  
        bordercolor="black",                
        borderwidth=1                        
    )
)

if viz : 
    header_placeholder.empty()
    subheader_placeholder.empty()
    body_placeholder.empty()
    
    for i in range(1,len(val)-17) : 

        # Update traces with new data
        fig1.data[0].x = val.index[:i]  
        fig1.data[0].y = val["Surrender"][:i] 
        fig1.data[1].x = val.index[:i]  
        fig1.data[1].y = val["Hold"][:i]  
        
        # Update the plot in Streamlit
        chart_placeholder.plotly_chart(fig1)
        time.sleep(0.1)

    populate_text()
    time.sleep(2)
    insights()

#-------------Re-invest Option--------------------------------
#Updates for the future.....

#Assumptions Made 

# - No Income Tax
# - Cost of Insurance effects on Premium pct contributions to cash value are secondary to duration of the policy
# - Fixed Death Benefit
# - Fixed rate of growth for cash value 









