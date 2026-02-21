import streamlit as st
import pandas as pd
import lasio
import numpy as np
import segyio
from plotly.subplots import make_subplots
import plotly.graph_objects as go
import plotly.express as px
from matplotlib import pyplot as plt
from PIL import Image
import requests
from io import BytesIO



###  NEEDED FOR LAS  ###

columns = []

# Function to fetch and display image
def fetch_image(url):
    response = requests.get(url)
    if response.status_code == 200:
        image = Image.open(BytesIO(response.content))
        st.image(image, caption='picture')
    else:
        st.write(f"Failed to fetch the image. Status code: {response.status_code}")

# Function to load LAS data
def load_data(uploadedfile):
    if uploadedfile:
        uploadedfile.seek(0) 
        string = uploadedfile.read().decode()
        las_file = lasio.read(string)
        well_data = las_file.df()
    else:
        las_file = None
        well_data = None
    return las_file, well_data

# Function to plot Vshale types
def plot_vshale(vs, well_df, Vsh_linear, Vsh_Larinor_older, Vsh_Larinor_tertiary, Vsh_clavier):
    fig, ax = plt.subplots(figsize=(2, 5))
    color_dict = {
        'Linear': ('teal', Vsh_linear),
        'Vsh_Larinor_older': ('green', Vsh_Larinor_older),
        'Vsh_Larinor_tertiary': ('magenta', Vsh_Larinor_tertiary),
        'Vsh_clavier': ('c', Vsh_clavier)
    }
    
    if vs in color_dict:
        color, data = color_dict[vs]
        ax.plot(data, well_df.DEPT, lw=0.5, color=color)
        ax.set_xlabel(vs)
        ax.set_ylabel('Depth (m)')
        ax.set_xlabel(vs, color=color, fontsize=11)
        ax.grid(which='both', color='black', axis='both', alpha=1, linestyle='--', linewidth=0.8)
        ax.invert_yaxis()
        return fig
    else:
        st.write("Invalid Vshale type selected.")
        return None

# Function to plot well data
def plot(well_data):
    cola, colb, colc = st.columns(3)
    plot_type = cola.radio('Plot type:', ['Line', 'Scatter', 'Histogram', 'Cross-plot'])
    
    if plot_type in ['Line', 'Scatter']:
        curves = colb.multiselect('Select Curves To Plot', columns, key="multiselect1")
        
        if len(curves) <= 1:
            st.warning('Please select at least 2 curves.')
            return
        
        curve_index = 1
        fig = make_subplots(rows=1, cols=len(curves), subplot_titles=curves, shared_yaxes=True)
        for curve in curves:
            mode = 'lines' if plot_type == 'Line' else 'markers'
            fig.add_trace(go.Scatter(x=well_data[curve], y=well_data['DEPT'], mode=mode, marker={'size': 4} if plot_type == 'Scatter' else None), row=1, col=curve_index)
            curve_index += 1
        
        fig.update_layout(height=1000, showlegend=False, yaxis={'title': 'DEPTH', 'autorange': 'reversed'}, template='plotly_dark')
        st.plotly_chart(fig, use_container_width=True)
    
    elif plot_type == 'Histogram':
        hist_curve = colb.selectbox('Select a Curve', columns, index=2)
        hist_col = colc.color_picker('Select Histogram Colour', value='#1aa2aa')
        histogram = px.histogram(well_data, x=hist_curve, log_x=False)
        histogram.update_traces(marker_color=hist_col)
        histogram.update_layout(template='plotly_dark')
        st.plotly_chart(histogram, use_container_width=True)
    
    elif plot_type == 'Cross-plot':
        xplot_x = colb.selectbox('X-Axis', columns, index=1)
        xplot_x_log = colb.radio('X Axis - Linear or Logarithmic', ('Linear', 'Logarithmic')) == 'Logarithmic'
        xplot_y = colc.selectbox('Y-Axis', columns, index=2)
        xplot_y_log = colc.radio('Y Axis - Linear or Logarithmic', ('Linear', 'Logarithmic')) == 'Logarithmic'
        xplot_col = st.selectbox('Colour-Bar', columns, index=0)
        
        xplot = px.scatter(well_data, x=xplot_x, y=xplot_y, color=xplot_col, log_x=xplot_x_log, log_y=xplot_y_log)
        xplot.update_layout(template='plotly_dark')
        st.plotly_chart(xplot, use_container_width=True)


def main():
    global columns

    st.set_page_config(page_title="GeoVIZ", layout="wide", page_icon="🌍")

    # ─── PROFESSIONAL DARK INDUSTRIAL CSS ───────────────────────────────────────
    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;600;900&family=Share+Tech+Mono&family=DM+Sans:wght@300;400;500&display=swap');

        /* ── Root Variables ── */
        :root {
            --bg-base:       #080c10;
            --bg-panel:      #0d1117;
            --bg-card:       #111820;
            --bg-card-hover: #16202b;
            --border:        #1e2d3d;
            --border-bright: #00e5ff;
            --accent:        #00e5ff;
            --accent-2:      #00ff9d;
            --accent-warm:   #ff6b35;
            --text-primary:  #e8f4f8;
            --text-secondary:#7a99b0;
            --text-dim:      #3a5568;
            --glow-cyan:     0 0 20px rgba(0,229,255,0.3);
            --glow-green:    0 0 20px rgba(0,255,157,0.3);
        }

        /* ── Global Reset ── */
        html, body, [class*="css"] {
            background-color: var(--bg-base) !important;
            color: var(--text-primary) !important;
            font-family: 'DM Sans', sans-serif !important;
        }

        .stApp {
            background: var(--bg-base) !important;
            background-image:
                linear-gradient(rgba(0,229,255,0.03) 1px, transparent 1px),
                linear-gradient(90deg, rgba(0,229,255,0.03) 1px, transparent 1px);
            background-size: 60px 60px;
        }

        /* ── Hide Streamlit Branding ── */
        #MainMenu, footer, header { visibility: hidden; }

        /* ── Hero Header ── */
        .geo-hero {
            text-align: center;
            padding: 60px 20px 40px;
            position: relative;
        }
        .geo-hero::before {
            content: '';
            position: absolute;
            top: 0; left: 50%;
            transform: translateX(-50%);
            width: 600px; height: 2px;
            background: linear-gradient(90deg, transparent, var(--accent), transparent);
        }
        .geo-title {
            font-family: 'Orbitron', monospace !important;
            font-size: 5rem !important;
            font-weight: 900 !important;
            letter-spacing: 0.3em !important;
            background: linear-gradient(135deg, #00e5ff 0%, #00ff9d 50%, #00e5ff 100%);
            -webkit-background-clip: text !important;
            -webkit-text-fill-color: transparent !important;
            background-clip: text !important;
            text-shadow: none !important;
            margin: 0 !important;
            line-height: 1 !important;
            filter: drop-shadow(0 0 30px rgba(0,229,255,0.5));
        }
        .geo-subtitle {
            font-family: 'Share Tech Mono', monospace !important;
            font-size: 0.95rem !important;
            color: var(--text-secondary) !important;
            letter-spacing: 0.25em !important;
            margin-top: 12px !important;
            text-transform: uppercase !important;
        }
        .geo-divider {
            width: 120px;
            height: 1px;
            background: linear-gradient(90deg, transparent, var(--accent), transparent);
            margin: 24px auto;
        }
        .geo-tagline {
            font-family: 'Share Tech Mono', monospace !important;
            font-size: 0.75rem !important;
            color: var(--text-dim) !important;
            letter-spacing: 0.4em !important;
            text-transform: uppercase !important;
        }

        /* ── Section Label ── */
        .section-label {
            font-family: 'Share Tech Mono', monospace !important;
            font-size: 0.7rem !important;
            color: var(--accent) !important;
            letter-spacing: 0.35em !important;
            text-transform: uppercase !important;
            margin-bottom: 8px !important;
            display: block;
        }

        /* ── Selectbox / Dropdowns ── */
        .stSelectbox > div > div {
            background: var(--bg-card) !important;
            border: 1px solid var(--border) !important;
            border-radius: 4px !important;
            color: var(--text-primary) !important;
            font-family: 'Share Tech Mono', monospace !important;
            transition: border-color 0.2s;
        }
        .stSelectbox > div > div:hover,
        .stSelectbox > div > div:focus-within {
            border-color: var(--accent) !important;
            box-shadow: var(--glow-cyan) !important;
        }

        /* ── Tabs ── */
        .stTabs [data-baseweb="tab-list"] {
            background: var(--bg-panel) !important;
            border-bottom: 1px solid var(--border) !important;
            padding: 0 8px !important;
            gap: 4px !important;
        }
        .stTabs [data-baseweb="tab"] {
            font-family: 'Share Tech Mono', monospace !important;
            font-size: 0.75rem !important;
            letter-spacing: 0.2em !important;
            color: var(--text-secondary) !important;
            background: transparent !important;
            border: 1px solid transparent !important;
            border-bottom: none !important;
            border-radius: 4px 4px 0 0 !important;
            padding: 10px 24px !important;
            transition: all 0.2s !important;
            text-transform: uppercase !important;
        }
        .stTabs [data-baseweb="tab"]:hover {
            color: var(--accent) !important;
            background: rgba(0,229,255,0.05) !important;
        }
        .stTabs [aria-selected="true"] {
            color: var(--accent) !important;
            border-color: var(--border) !important;
            border-bottom-color: var(--bg-base) !important;
            background: var(--bg-base) !important;
            box-shadow: var(--glow-cyan) !important;
        }
        .stTabs [data-baseweb="tab-panel"] {
            background: var(--bg-base) !important;
            border: 1px solid var(--border) !important;
            border-top: none !important;
            padding: 24px !important;
            border-radius: 0 0 8px 8px !important;
        }

        /* ── File Uploader ── */
        .stFileUploader > div {
            background: var(--bg-card) !important;
            border: 1px dashed var(--border) !important;
            border-radius: 8px !important;
            transition: all 0.3s !important;
        }
        .stFileUploader > div:hover {
            border-color: var(--accent) !important;
            background: var(--bg-card-hover) !important;
            box-shadow: var(--glow-cyan) !important;
        }
        .stFileUploader label {
            color: var(--text-secondary) !important;
            font-family: 'Share Tech Mono', monospace !important;
            font-size: 0.8rem !important;
            letter-spacing: 0.1em !important;
        }

        /* ── Buttons ── */
        .stButton > button {
            background: transparent !important;
            border: 1px solid var(--accent) !important;
            color: var(--accent) !important;
            font-family: 'Share Tech Mono', monospace !important;
            font-size: 0.75rem !important;
            letter-spacing: 0.2em !important;
            text-transform: uppercase !important;
            padding: 10px 24px !important;
            border-radius: 3px !important;
            transition: all 0.2s !important;
        }
        .stButton > button:hover {
            background: var(--accent) !important;
            color: var(--bg-base) !important;
            box-shadow: var(--glow-cyan) !important;
        }

        /* ── Radio Buttons ── */
        .stRadio > div {
            gap: 8px !important;
        }
        .stRadio label {
            font-family: 'Share Tech Mono', monospace !important;
            font-size: 0.78rem !important;
            color: var(--text-secondary) !important;
            letter-spacing: 0.1em !important;
        }
        .stRadio [data-baseweb="radio"] span:first-child {
            background: transparent !important;
            border-color: var(--border-bright) !important;
        }

        /* ── Multiselect ── */
        .stMultiSelect > div > div {
            background: var(--bg-card) !important;
            border: 1px solid var(--border) !important;
            border-radius: 4px !important;
        }
        .stMultiSelect [data-baseweb="tag"] {
            background: rgba(0,229,255,0.1) !important;
            border: 1px solid var(--accent) !important;
            color: var(--accent) !important;
            font-family: 'Share Tech Mono', monospace !important;
            font-size: 0.72rem !important;
        }

        /* ── Text Inputs ── */
        .stTextInput > div > div > input {
            background: var(--bg-card) !important;
            border: 1px solid var(--border) !important;
            border-radius: 4px !important;
            color: var(--text-primary) !important;
            font-family: 'Share Tech Mono', monospace !important;
        }
        .stTextInput > div > div > input:focus {
            border-color: var(--accent) !important;
            box-shadow: var(--glow-cyan) !important;
        }

        /* ── Sliders ── */
        .stSlider [data-baseweb="slider"] {
            margin-top: 8px;
        }
        .stSlider [data-testid="stThumbValue"] {
            font-family: 'Share Tech Mono', monospace !important;
            background: var(--bg-card) !important;
            border: 1px solid var(--accent) !important;
            color: var(--accent) !important;
            font-size: 0.7rem !important;
        }

        /* ── DataFrames ── */
        .stDataFrame {
            border: 1px solid var(--border) !important;
            border-radius: 6px !important;
            overflow: hidden !important;
        }
        .stDataFrame [data-testid="stTable"] {
            background: var(--bg-card) !important;
        }

        /* ── Success / Warning / Error ── */
        .stSuccess {
            background: rgba(0,255,157,0.08) !important;
            border: 1px solid var(--accent-2) !important;
            border-radius: 4px !important;
            color: var(--accent-2) !important;
            font-family: 'Share Tech Mono', monospace !important;
            font-size: 0.8rem !important;
        }
        .stWarning {
            background: rgba(255,107,53,0.08) !important;
            border: 1px solid var(--accent-warm) !important;
            border-radius: 4px !important;
            color: var(--accent-warm) !important;
            font-family: 'Share Tech Mono', monospace !important;
        }

        /* ── Titles inside tabs ── */
        h1, h2, h3 {
            font-family: 'Orbitron', monospace !important;
            letter-spacing: 0.1em !important;
        }
        h1 { font-size: 1.6rem !important; color: var(--text-primary) !important; }
        h2 { font-size: 1.2rem !important; color: var(--text-secondary) !important; }
        h3 { font-size: 0.95rem !important; color: var(--accent) !important; }

        /* ── Metrics / Stats ── */
        [data-testid="stMetric"] {
            background: var(--bg-card) !important;
            border: 1px solid var(--border) !important;
            border-radius: 6px !important;
            padding: 16px !important;
        }
        [data-testid="stMetricLabel"] {
            font-family: 'Share Tech Mono', monospace !important;
            font-size: 0.7rem !important;
            color: var(--text-secondary) !important;
            letter-spacing: 0.2em !important;
            text-transform: uppercase !important;
        }
        [data-testid="stMetricValue"] {
            font-family: 'Orbitron', monospace !important;
            color: var(--accent) !important;
        }

        /* ── Sidebar ── */
        [data-testid="stSidebar"] {
            background: var(--bg-panel) !important;
            border-right: 1px solid var(--border) !important;
        }

        /* ── Scrollbar ── */
        ::-webkit-scrollbar { width: 4px; height: 4px; }
        ::-webkit-scrollbar-track { background: var(--bg-base); }
        ::-webkit-scrollbar-thumb { background: var(--border); border-radius: 2px; }
        ::-webkit-scrollbar-thumb:hover { background: var(--accent); }

        /* ── Links ── */
        a { color: var(--accent) !important; text-decoration: none !important; }
        a:hover { text-shadow: var(--glow-cyan); }

        /* ── Corner Accents ── */
        .corner-box {
            border: 1px solid var(--border);
            border-radius: 6px;
            padding: 16px 20px;
            position: relative;
            background: var(--bg-card);
            margin: 8px 0;
        }
        .corner-box::before, .corner-box::after {
            content: '';
            position: absolute;
            width: 10px; height: 10px;
            border-color: var(--accent);
            border-style: solid;
        }
        .corner-box::before {
            top: -1px; left: -1px;
            border-width: 2px 0 0 2px;
            border-radius: 4px 0 0 0;
        }
        .corner-box::after {
            bottom: -1px; right: -1px;
            border-width: 0 2px 2px 0;
            border-radius: 0 0 4px 0;
        }

        /* ── Status Badge ── */
        .status-badge {
            display: inline-block;
            padding: 3px 10px;
            background: rgba(0,229,255,0.1);
            border: 1px solid var(--accent);
            border-radius: 2px;
            font-family: 'Share Tech Mono', monospace;
            font-size: 0.65rem;
            color: var(--accent);
            letter-spacing: 0.2em;
            text-transform: uppercase;
            vertical-align: middle;
            margin-left: 10px;
        }

        /* ── Info Panel ── */
        .info-panel {
            background: var(--bg-card);
            border-left: 3px solid var(--accent);
            padding: 12px 16px;
            border-radius: 0 4px 4px 0;
            margin: 12px 0;
            font-family: 'Share Tech Mono', monospace;
            font-size: 0.75rem;
            color: var(--text-secondary);
            letter-spacing: 0.05em;
        }

        /* ── Data Type Selector ── */
        .stSelectbox label {
            font-family: 'Share Tech Mono', monospace !important;
            font-size: 0.72rem !important;
            color: var(--accent) !important;
            letter-spacing: 0.25em !important;
            text-transform: uppercase !important;
        }

        /* ── Write / paragraph text ── */
        p, .stMarkdown p {
            font-family: 'DM Sans', sans-serif !important;
            color: var(--text-secondary) !important;
            font-size: 0.88rem !important;
        }

        /* ── Color Picker ── */
        .stColorPicker label {
            font-family: 'Share Tech Mono', monospace !important;
            font-size: 0.72rem !important;
            color: var(--text-secondary) !important;
        }

        </style>
    """, unsafe_allow_html=True)

    # ─── HERO HEADER ────────────────────────────────────────────────────────────
    st.markdown("""
        <div class="geo-hero">
            <div class="geo-title">GeoVIZ</div>
            <div class="geo-divider"></div>
            <div class="geo-subtitle">Subsurface Intelligence Platform</div>
            <div style="height:10px"></div>
            <div class="geo-tagline">◈ &nbsp; LAS &nbsp;·&nbsp; SEGY &nbsp;·&nbsp; Formation Evaluation &nbsp; ◈</div>
        </div>
    """, unsafe_allow_html=True)

    # ─── DATA TYPE SELECTION ─────────────────────────────────────────────────────
    st.markdown('<span class="section-label">▸ SELECT DATA TYPE</span>', unsafe_allow_html=True)
    data_type = st.selectbox('', ('WELL LOG DATA', 'SEISMIC DATA'))

    st.markdown(f"""
        <div class="info-panel">
            ACTIVE MODULE &nbsp;▸&nbsp; <strong style="color:#00e5ff">{data_type}</strong>
            &nbsp;&nbsp;|&nbsp;&nbsp; STATUS <span class="status-badge">READY</span>
        </div>
    """, unsafe_allow_html=True)

    # ─── WELL LOG DATA ───────────────────────────────────────────────────────────
    if data_type == 'WELL LOG DATA':
        st.markdown("## WELL LOG VIEWER")
        
        t1, t2, t3 = st.tabs(['◈  DATA LOADING', '◈  FORMATION EVALUATION', '◈  VISUALISATION'])
        
        url = "https://drive.google.com/drive/folders/1FPe7tuvOthk0__yzZsXhWevjPucsS5lF?usp=sharing"
        st.markdown(
            f'<div class="info-panel">📁 &nbsp; Sample dataset → <a href="{url}" target="_blank">Google Drive Repository</a></div>',
            unsafe_allow_html=True
        )

        with t1:
            st.markdown('<span class="section-label">▸ UPLOAD LAS FILE</span>', unsafe_allow_html=True)
            uploaded_file = st.file_uploader("Drag and drop or click to upload a .LAS file", type=["las", "LAS"])
            
            if uploaded_file is not None:
                st.success("✓  LAS FILE LOADED SUCCESSFULLY")
                las_file, well_data = load_data(uploaded_file)
                
                if well_data is not None:
                    well_data.reset_index(inplace=True)
                    well_df = pd.DataFrame(well_data)
                    columns = well_df.columns

                    st.markdown('<span class="section-label" style="margin-top:20px">▸ WELL DATA TABLE</span>', unsafe_allow_html=True)
                    st.dataframe(well_df, use_container_width=True)

                    st.markdown('<span class="section-label" style="margin-top:20px">▸ STATISTICAL SUMMARY</span>', unsafe_allow_html=True)
                    st.dataframe(well_df.describe(), use_container_width=True)
                else:
                    st.markdown('<div class="info-panel" style="border-left-color:#ff6b35">⚠ Data not available.</div>', unsafe_allow_html=True)
            else:
                st.markdown("""
                    <div class="corner-box" style="text-align:center; padding:40px;">
                        <div style="font-family:'Share Tech Mono',monospace; font-size:0.8rem; color:#3a5568; letter-spacing:0.3em;">
                            ◈ &nbsp; AWAITING FILE UPLOAD &nbsp; ◈
                        </div>
                        <div style="font-family:'DM Sans',sans-serif; font-size:0.75rem; color:#3a5568; margin-top:8px;">
                            Supported format: .LAS / .las
                        </div>
                    </div>
                """, unsafe_allow_html=True)
        
        with t2:
            if uploaded_file is not None and 'GR' in well_df.columns and 'DEPT' in well_df.columns:
                st.markdown("## VSHALE CALCULATOR")
                st.markdown('<div class="info-panel">Volume of Shale computation using Gamma Ray normalization</div>', unsafe_allow_html=True)

                gammaray = well_df['GR']
                c1, c2 = st.columns(2)
                max_val_per = c2.text_input("Percentile for max GR:", value="95")
                min_val_per = c1.text_input("Percentile for min GR:", value="5")
                
                if max_val_per.replace('.', '', 1).isdigit() and min_val_per.replace('.', '', 1).isdigit():
                    max_val_per = float(max_val_per)
                    min_val_per = float(min_val_per)
                    
                    if 0 <= min_val_per <= 100 and 0 <= max_val_per <= 100:
                        pmax = gammaray.quantile(max_val_per / 100)
                        pmin = gammaray.quantile(min_val_per / 100)
                        Igr = (gammaray - pmin) / (pmax - pmin)
                        
                        Vsh_linear = Igr
                        Vsh_Larinor_older = 0.33 * (2**(2 * Igr) - 1)
                        Vsh_Larinor_tertiary = 0.083 * (2**(3.7 * Igr) - 1)
                        Vsh_clavier = 1.7 - (3.38 - (Igr + 0.7)**2)**0.5
                        
                        st.markdown('<span class="section-label">▸ SELECT METHOD</span>', unsafe_allow_html=True)
                        vs = st.selectbox('Vshale type', ['Linear', 'Vsh_Larinor_older', 'Vsh_Larinor_tertiary', 'Vsh_clavier'])
                        fig = plot_vshale(vs, well_df, Vsh_linear, Vsh_Larinor_older, Vsh_Larinor_tertiary, Vsh_clavier)
                        if fig:
                            st.pyplot(fig)
                    else:
                        st.markdown('<div class="info-panel" style="border-left-color:#ff6b35">⚠ Percentile values must be between 0 and 100.</div>', unsafe_allow_html=True)
                else:
                    st.markdown('<div class="info-panel" style="border-left-color:#ff6b35">⚠ Invalid input. Enter valid percentile values (0–100).</div>', unsafe_allow_html=True)
            else:
                st.markdown("""
                    <div class="corner-box" style="text-align:center; padding:40px;">
                        <div style="font-family:'Share Tech Mono',monospace; font-size:0.78rem; color:#3a5568; letter-spacing:0.25em;">
                            GR or DEPT columns not detected — upload a valid LAS file first
                        </div>
                    </div>
                """, unsafe_allow_html=True)
        
        with t3:
            if uploaded_file is not None:
                st.markdown('<span class="section-label">▸ CURVE VISUALISATION</span>', unsafe_allow_html=True)
                plot(well_df)
            else:
                st.markdown("""
                    <div class="corner-box" style="text-align:center; padding:40px;">
                        <div style="font-family:'Share Tech Mono',monospace; font-size:0.78rem; color:#3a5568; letter-spacing:0.25em;">
                            ◈ &nbsp; Upload a LAS file in DATA LOADING to begin &nbsp; ◈
                        </div>
                    </div>
                """, unsafe_allow_html=True)


    # ─── SEISMIC DATA ────────────────────────────────────────────────────────────
    elif data_type == 'SEISMIC DATA':
        st.markdown("## SEGY VIEWER")

        st.markdown('<span class="section-label">▸ UPLOAD SEGY FILE</span>', unsafe_allow_html=True)
        filepath_in = st.file_uploader("UPLOAD YOUR SEGY FILE", accept_multiple_files=False, type=None)

        url = "https://drive.google.com/drive/folders/1FPe7tuvOthk0__yzZsXhWevjPucsS5lF?usp=sharing"
        st.markdown(
            f'<div class="info-panel">📁 &nbsp; Sample 2D SEGY data → <a href="{url}" target="_blank">Google Drive Repository</a></div>',
            unsafe_allow_html=True
        )

        if filepath_in is None:
            st.markdown("""
                <div class="corner-box" style="text-align:center; padding:40px;">
                    <div style="font-family:'Share Tech Mono',monospace; font-size:0.8rem; color:#3a5568; letter-spacing:0.3em;">
                        ◈ &nbsp; AWAITING SEGY FILE &nbsp; ◈
                    </div>
                    <div style="font-family:'DM Sans',sans-serif; font-size:0.75rem; color:#3a5568; margin-top:8px;">
                        Supports Post-stack 2D / 3D · SEG-Y format
                    </div>
                </div>
            """, unsafe_allow_html=True)
        else:
            filepath_in = filepath_in.name
            
            try:
                with segyio.open(filepath_in, ignore_geometry=True) as f:
                    data_format = f.format
                
                inline_xline = [[189,193], [9,13], [9,21], [5,21]]
                state = False
                
                for k, byte_loc in enumerate(inline_xline):
                    try:
                        with segyio.open(filepath_in, iline=byte_loc[0], xline=byte_loc[1], ignore_geometry=False) as f:
                            seismic_data = segyio.tools.cube(f)
                            n_traces = f.tracecount    
                            tr = f.attributes(segyio.TraceField.TraceNumber)[-1]
                            if not isinstance(tr, int):
                                tr = f.attributes(segyio.TraceField.TraceNumber)[-2] + 1
                            tr = int(tr[0])
                            spec = segyio.spec()
                            spec.sorting = f.sorting
                            data_sorting = spec.sorting == segyio.TraceSortingFormat.INLINE_SORTING
                            twt = f.samples
                            sample_rate = segyio.tools.dt(f) / 1000
                            n_samples = f.samples.size

                            TraceSequenceFile = [f.attributes(segyio.TraceField.TRACE_SEQUENCE_FILE)[i] for i in range(n_traces)]
                            Field_Record = [f.attributes(segyio.TraceField.FieldRecord)[i] for i in range(n_traces)]
                            Trace_Field = [f.attributes(segyio.TraceField.TraceNumber)[i] for i in range(n_traces)]
                            CDP = [f.attributes(segyio.TraceField.CDP)[i] for i in range(n_traces)]
                            Inline_3D = [f.attributes(segyio.TraceField.INLINE_3D)[i] for i in range(n_traces)]
                            Crossline_3D = [f.attributes(segyio.TraceField.CROSSLINE_3D)[i] for i in range(n_traces)]
                        
                        inline3d = np.unique(Inline_3D)
                        crossline3d = np.unique(Crossline_3D)
                        fieldrecord = np.unique(Field_Record)
                        tracefield = np.unique(Trace_Field)
                        tracesequence = np.unique(TraceSequenceFile)
                        cdpnumber = np.unique(CDP)

                        state = True
                    except:
                        pass

                    if state:
                        if len(seismic_data.shape) == 3:
                            if seismic_data.shape[0] != 1:
                                data_type = 'Post-stack 3D'
                            else:
                                data_type = 'Post-stack 3D' if n_traces > tr > 1 else 'Post-stack 2D'
                        else:
                            if len(f.offsets) > 1:
                                data_type = 'Pre-Stack 2D' if seismic_data.shape[0] == 1 else 'Pre-Stack 3D'
                            else:
                                st.write('Error: Please check inline and crossline byte locations')

                        if k == 0:
                            inline_number = inline3d 
                            xline_number = crossline3d
                        elif k == 1:
                            inline_number = fieldrecord 
                            xline_number = tracefield
                        elif k == 2:
                            inline_number = fieldrecord 
                            xline_number = cdpnumber
                        elif k == 3:
                            inline_number = tracesequence 
                            xline_number = cdpnumber

                        if data_type == 'Post-stack 3D':
                            if len(inline_number) != 1 and len(xline_number) != 1:
                                break
                        else:
                            break

            except FileNotFoundError:
                st.markdown('<div class="info-panel" style="border-left-color:#ff6b35">⚠ File not found or unsupported data format.</div>', unsafe_allow_html=True)
                st.stop()

            try:
                inline, cdp, samples = seismic_data.shape
            except:
                st.markdown('<div class="info-panel" style="border-left-color:#ff6b35">⚠ Data load failed — unsupported format or invalid byte locations.</div>', unsafe_allow_html=True)
                st.stop()

            if data_type == 'Post-stack 2D':
                data_display = seismic_data.reshape(cdp, samples).T
                diff_inline = 1
                diff_xline = 1
                st.markdown(f'<div class="info-panel">DATA TYPE &nbsp;▸&nbsp; <strong style="color:#00e5ff">{data_type}</strong> &nbsp;|&nbsp; SHAPE &nbsp;▸&nbsp; {data_display.shape}</div>', unsafe_allow_html=True)

            elif data_type == 'Post-stack 3D':
                if inline == 1 and tr > 1 and n_traces % tr == 0:
                    inline_no = n_traces / tr
                    data_display = seismic_data.reshape(int(inline_no), int(tr), int(samples)).T
                    xline_number = np.arange(tr)
                    inline_number = np.arange(inline_no)
                    cdp_no = xline_number
                else:
                    data_display = seismic_data.reshape(inline, cdp, samples).T
                    cdp_no = np.arange(cdp)

                diff_inline = np.diff(inline_number)[0]
                diff_xline = np.diff(xline_number)[0]
                st.markdown(f'<div class="info-panel">DATA TYPE &nbsp;▸&nbsp; <strong style="color:#00e5ff">{data_type}</strong> &nbsp;|&nbsp; SHAPE &nbsp;▸&nbsp; {data_display.shape}</div>', unsafe_allow_html=True)

            def plot1(seismic_data, direction=None, segy='seismic'):
                color = plt.cm.seismic if segy == 'seismic' else plt.cm.jet
                if direction == 'inline':
                    extent = (np.min(xline_number), np.max(xline_number), np.max(twt), np.min(twt))
                    plt.xlabel("Crossline No.")
                    plt.ylabel("Time (ms)")
                    label = 'Inline Visualization'
                elif direction == 'xline':
                    extent = (np.min(inline_number), np.max(inline_number), np.max(twt), np.min(twt))
                    plt.xlabel("Inline No.")
                    plt.ylabel("Time (ms)")
                    label = 'Crossline Visualization'
                elif direction == 'time-slice':
                    extent = (np.min(inline_number), np.max(inline_number), np.max(xline_number), np.min(xline_number))
                    plt.xlabel("Inline No.")
                    plt.ylabel("Crossline No.")
                    label = 'Time-Slice Visualization'
                elif direction == '2D Line':
                    extent = (np.min(xline_number), np.max(xline_number), np.max(twt), np.min(twt))
                    plt.xlabel("CDP No.")
                    plt.ylabel("Time (ms)")
                    label = '2D Line Visualization'

                plt.imshow(seismic_data, interpolation='nearest', cmap=color, aspect='auto', vmin=-np.max(seismic_data), vmax=np.max(seismic_data), extent=extent)
                plt.grid(True)
                plt.colorbar()
                plt.show()

            if data_type == 'Post-stack 2D':
                plot1(data_display, direction='2D Line', segy='seismic')
                st.pyplot(plt.gcf())

            if data_type == 'Post-stack 3D':
                st.markdown('<span class="section-label">▸ INLINE SECTION</span>', unsafe_allow_html=True)
                mid_inline = len(inline_number) // 2
                Inline = st.slider('Choose inline', min_value=inline_number[0], max_value=inline_number[-1], step=diff_inline, value=inline_number[mid_inline])
                Iline = int((Inline - inline_number[0]) / diff_inline)
                seismic_data_inline = data_display[:, :, Iline]
                plt.clf()
                plot1(seismic_data_inline, direction='inline', segy='seismic')
                st.pyplot(plt.gcf())

                st.markdown('<span class="section-label">▸ CROSSLINE SECTION</span>', unsafe_allow_html=True)
                mid_xline = len(xline_number) // 2
                Crossline = st.slider('Choose crossline', min_value=xline_number[0], max_value=xline_number[-1], step=diff_xline, value=xline_number[mid_xline])
                Xline = int((Crossline - xline_number[0]) / diff_xline)
                seismic_data_xline = data_display[:, Xline, :]
                plt.clf()
                plot1(seismic_data_xline, direction='xline', segy='seismic')
                st.pyplot(plt.gcf())

                st.markdown('<span class="section-label">▸ TIME SLICE</span>', unsafe_allow_html=True)
                mid_twt = len(twt) // 2
                Time = st.slider('Choose Time (ms)', min_value=int(twt[0]), max_value=int(twt[-1]), step=int(sample_rate), value=int(twt[mid_twt]))
                Time_slice = int((Time - twt[0]) / sample_rate)
                seismic_data_time = data_display[Time_slice, :, :]
                plt.clf()
                plot1(seismic_data_time, direction='time-slice', segy='seismic')
                st.pyplot(plt.gcf())


if __name__ == "__main__":
    main()
