# Motor Control Center (MCC) Designer 
# Industrial motor panel design, cable sizing, feeder planning, and BOM costing
# Developed by Haripal Singh

import math
from dataclasses import dataclass
from io import BytesIO
from typing import Dict, List

import pandas as pd
import streamlit as st

# ---------------- PAGE CONFIG ---------------- #

st.set_page_config(
    page_title="Motor Control Center Designer by Haripal Singh",
    page_icon="⚡",
    layout="wide"
)

st.title("⚡ Motor Control Center (MCC) Professional Designer By Haripal Singh")
st.caption("Industrial motor panel design, cable sizing, feeder planning, and BOM costing")

# ---------------- DATA TABLES ---------------- #

CABLE_CATALOG = pd.DataFrame([
{"Size (mm²)":2.5,"Copper XLPE Ampacity (A)":27,"Approx Cost /m (USD)":1.9},
{"Size (mm²)":4,"Copper XLPE Ampacity (A)":36,"Approx Cost /m (USD)":2.6},
{"Size (mm²)":6,"Copper XLPE Ampacity (A)":46,"Approx Cost /m (USD)":3.3},
{"Size (mm²)":10,"Copper XLPE Ampacity (A)":63,"Approx Cost /m (USD)":5.0},
{"Size (mm²)":16,"Copper XLPE Ampacity (A)":85,"Approx Cost /m (USD)":7.2},
{"Size (mm²)":25,"Copper XLPE Ampacity (A)":112,"Approx Cost /m (USD)":10.4},
{"Size (mm²)":35,"Copper XLPE Ampacity (A)":138,"Approx Cost /m (USD)":13.8},
{"Size (mm²)":50,"Copper XLPE Ampacity (A)":168,"Approx Cost /m (USD)":18.2},
{"Size (mm²)":70,"Copper XLPE Ampacity (A)":213,"Approx Cost /m (USD)":24.5},
{"Size (mm²)":95,"Copper XLPE Ampacity (A)":258,"Approx Cost /m (USD)":32.0},
{"Size (mm²)":120,"Copper XLPE Ampacity (A)":298,"Approx Cost /m (USD)":39.4},
{"Size (mm²)":150,"Copper XLPE Ampacity (A)":340,"Approx Cost /m (USD)":48.6},
{"Size (mm²)":185,"Copper XLPE Ampacity (A)":388,"Approx Cost /m (USD)":58.3},
{"Size (mm²)":240,"Copper XLPE Ampacity (A)":467,"Approx Cost /m (USD)":74.8},
])


# ---------------- DATA CLASS ---------------- #

@dataclass
class MotorDesign:
    full_load_current: float
    overload_relay: float
    synchronous_speed: float
    motor_speed: float
    busbar_area: float
    selected_cable_size: float
    selected_cable_ampacity: float

# ---------------- CALCULATION FUNCTION ---------------- #

def motor_calculation(power_kw,voltage,pf,efficiency,frequency,poles,slip,current_density,margin):

    current=(power_kw*1000)/(math.sqrt(3)*voltage*pf*efficiency)

    overload=current*1.1

    ns=(120*frequency)/poles

    rpm=ns*(1-slip)

    busbar=current/current_density

    design_current=current*margin

    cable=CABLE_CATALOG[CABLE_CATALOG["Copper XLPE Ampacity (A)"]>=design_current].head(1)

    if cable.empty:
        cable=CABLE_CATALOG.tail(1)

    return MotorDesign(
        full_load_current=current,
        overload_relay=overload,
        synchronous_speed=ns,
        motor_speed=rpm,
        busbar_area=busbar,
        selected_cable_size=float(cable["Size (mm²)"].iloc[0]),
        selected_cable_ampacity=float(cable["Copper XLPE Ampacity (A)"].iloc[0])
    )

# ---------------- BOM FUNCTION ---------------- #

def build_bom(design,feeders,cable_len,markup):

    items=[
    {"Item":"MCC Panel","Qty":1,"Unit Cost":1450},
    {"Item":"MCCB","Qty":1,"Unit Cost":320},
    {"Item":"Contactor","Qty":feeders,"Unit Cost":120},
    {"Item":"Overload Relay","Qty":feeders,"Unit Cost":65},
    {"Item":"Control Kit","Qty":feeders,"Unit Cost":35},
    {"Item":f"Power Cable {design.selected_cable_size} mm²","Qty":feeders*cable_len,
     "Unit Cost":float(CABLE_CATALOG.loc[CABLE_CATALOG["Size (mm²)"]==design.selected_cable_size,
     "Approx Cost /m (USD)"].iloc[0])},
    {"Item":"Copper Busbar","Qty":1,"Unit Cost":max(180,design.busbar_area*6)}
    ]

    df=pd.DataFrame(items)

    df["Total"]=df["Qty"]*df["Unit Cost"]

    subtotal=df["Total"].sum()

    margin=subtotal*(markup/100)

    summary=pd.DataFrame([
    {"Item":"Subtotal","Qty":None,"Unit Cost":None,"Total":subtotal},
    {"Item":"Engineering Margin","Qty":None,"Unit Cost":None,"Total":margin},
    {"Item":"Grand Total","Qty":None,"Unit Cost":None,"Total":subtotal+margin}
    ])

    return pd.concat([df,summary],ignore_index=True)

# ---------------- EXCEL EXPORT ---------------- #

def export_excel(df):

    buffer=BytesIO()

    with pd.ExcelWriter(buffer,engine="openpyxl") as writer:
        df.to_excel(writer,index=False)

    return buffer.getvalue()

# ---------------- SIDEBAR INPUTS ---------------- #

with st.sidebar:

    st.header("Motor Inputs")

    motor_kw=st.number_input("Motor Power (kW)",value=45.0)

    voltage=st.number_input("Voltage",value=415.0)

    pf=st.slider("Power Factor",0.5,0.99,0.85)

    efficiency=st.slider("Efficiency",0.6,0.99,0.92)

    frequency=st.selectbox("Frequency",[50,60])

    poles=st.selectbox("Motor Poles",[2,4,6,8])

    slip=st.slider("Slip",0.01,0.1,0.03)

    current_density=st.slider("Busbar Current Density",0.8,2.0,1.4)

    margin=st.slider("Cable Design Margin",1.0,1.5,1.25)

    st.header("Panel Settings")

    feeders=st.number_input("Number of Feeders",1,20,4)

    cable_len=st.number_input("Cable Length (m)",5.0,200.0,35.0)

    markup=st.slider("Engineering Margin %",0.0,40.0,15.0)

# ---------------- CALCULATIONS ---------------- #

design=motor_calculation(
motor_kw,voltage,pf,efficiency,frequency,poles,slip,current_density,margin
)

bom=build_bom(design,int(feeders),cable_len,markup)

# ---------------- KPI DISPLAY ---------------- #

k1,k2,k3,k4=st.columns(4)

k1.metric("Full Load Current",f"{design.full_load_current:.2f} A")
k2.metric("OL Relay",f"{design.overload_relay:.2f} A")
k3.metric("Motor Speed",f"{design.motor_speed:.0f} RPM")
k4.metric("Cable Size",f"{design.selected_cable_size} mm²")

# ---------------- TABLES ---------------- #

st.subheader("Cable Selection Table")

st.dataframe(CABLE_CATALOG,use_container_width=True)

st.subheader("Bill of Materials")

st.dataframe(bom,use_container_width=True)

# ---------------- COMPONENT IMAGES ---------------- #





# ---------------- EXCEL DOWNLOAD ---------------- #

excel=export_excel(bom)

st.download_button(
"Download BOM Excel",
data=excel,
file_name="MCC_BOM.xlsx"
)

st.success("Panel design completed successfully.")
