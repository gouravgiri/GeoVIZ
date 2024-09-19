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
        # log_curves = colc.multiselect('Log plot of:', columns, key="multiselect2")
        
        if len(curves) <= 1:
            st.warning('Please select at least 2 curves.')
            return
        
        curve_index = 1
        fig = make_subplots(rows=1, cols=len(curves), subplot_titles=curves, shared_yaxes=True)
        for curve in curves:
            # log_bool = 'log' if curve in log_curves else 'linear'
            mode = 'lines' if plot_type == 'Line' else 'markers'
            fig.add_trace(go.Scatter(x=well_data[curve], y=well_data['DEPT'], mode=mode, marker={'size': 4} if plot_type == 'Scatter' else None), row=1, col=curve_index)
            # fig.update_xaxes(type=log_bool, row=1, col=curve_index)
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

    st.set_page_config(page_title="GeoVIZ", layout="wide")

    # Custom CSS to improve aesthetics
    st.markdown("""
        <style>
        .main {
            background-color: #f0f0f0;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        }
        h1 {
            color: #2a9d8f;
        }
        h2 {
            color: #264653;
        }
        .option-box {
            background-color: #2a9d8f;
            color: white;
            padding: 10px;
            border-radius: 10px;
            margin: 10px;
            text-align: center;
            transition: background-color 0.3s;
        }
        .option-box:hover {
            background-color: #21867b;
        }
        </style>
    """, unsafe_allow_html=True)

    # Title and Subtitle
    st.markdown("<h1 style='text-align: center;'>GeoVIZ</h1>", unsafe_allow_html=True)
    st.markdown("<h2 style='text-align: center;'>Analyze LAS and SEGY data with ease!</h2>", unsafe_allow_html=True)

    # Data Type Selection
    st.markdown("<h3 style='text-align: center;'>Select Data Type</h3>", unsafe_allow_html=True)
    data_type = st.selectbox('', ('WELL LOG DATA', 'SEISMIC DATA'))
    
    # Create colored boxes for options
    col1, col2 = st.columns(2)
    
    # with col1:
    #     if st.button('LAS', key='las_option', help='Load and analyze LAS data'):
    #         data_type = 'LAS'
            
    # with col2:
    #     if st.button('SEGY', key='segy_option', help='Load and visualize SEGY data'):
    #         data_type = 'SEGY'

    st.write('You have selected:', data_type)

    # Tabs for different sections with improved styling

    if data_type == 'WELL LOG DATA':
        st.title('WELL LOG VIEWER')
        # Tabs for different sections
        
        t1, t2, t3 = st.tabs(['DATA LOADING', 'FORMATION EVALUATION', 'VISUALISATION'])
        
        with t1:
            uploaded_file = st.file_uploader("Upload a LAS file", type=["las", "LAS"])
            
            if uploaded_file is not None:
                st.success("LAS file loaded successfully")
                las_file, well_data = load_data(uploaded_file)
                
                if well_data is not None:
                    well_data.reset_index(inplace=True)
                    well_df = pd.DataFrame(well_data)
                    columns = well_df.columns  # Update the global variable
                    st.write("Well Data:")
                    st.write(well_df)
                    st.write("Statistics:")
                    st.write(well_df.describe())
                else:
                    st.write('Data not available.')
            else:
                st.write("File Upload is Required.")
        
        with t2:
            if uploaded_file is not None and 'GR' in well_df.columns and 'DEPT' in well_df.columns:
                st.title("Vshale Plot")
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
                        
                        vs = st.selectbox('Vshale type', ['Linear', 'Vsh_Larinor_older', 'Vsh_Larinor_tertiary', 'Vsh_clavier'])
                        fig = plot_vshale(vs, well_df, Vsh_linear, Vsh_Larinor_older, Vsh_Larinor_tertiary, Vsh_clavier)
                        if fig:
                            st.pyplot(fig)
                    else:
                        st.write("Percentile values should be between 0 and 100.")
                else:
                    st.write("Invalid input. Please enter valid percentile values (0-100).")
            else:
                st.write("GR or DEPT column missing in the data.")
        
        with t3:
            if uploaded_file is not None:
                plot(well_df)
            else:
                st.write("Please upload a LAS file first.")


    elif data_type == 'SEISMIC DATA':
        st.title('SEGY VIEWER')
        

        # File uploader for SEGY file
        filepath_in = st.file_uploader("UPLOAD YOUR SEGY FILE", accept_multiple_files=False, type=None)

        # Provide link to sample data
        url = "https://drive.google.com/drive/folders/1FPe7tuvOthk0__yzZsXhWevjPucsS5lF?usp=sharing"
        st.markdown("[LINK](%s) for small sie 2D sample data" % url)

        # Check if a file is uploaded
        if filepath_in is None:
            st.write("Please upload a SEGY file to proceed.")
        else:
            filepath_in = filepath_in.name
            
            try:
                with segyio.open(filepath_in, ignore_geometry=True) as f:
                    data_format = f.format
                
                # Supported inline and crossline byte locations
                inline_xline = [[189,193], [9,13], [9,21], [5,21]]
                state = False
                
                # Read SEGY data with different byte locations
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

                            # Trace attributes
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
                st.write("Error: File not found or unsupported data format.")
                st.stop()

            # Reshape seismic data to the corresponding format
            try:
                inline, cdp, samples = seismic_data.shape
            except:
                st.write("Error: Data was not loaded successfully due to unsupported data format or invalid inline and crossline byte locations.")
                st.stop()

            # Display data based on type
            if data_type == 'Post-stack 2D':
                data_display = seismic_data.reshape(cdp, samples).T
                diff_inline = 1
                diff_xline = 1
                st.write(f'Data Type: {data_type}')
                st.write(f'Seismic Data Shape (Time sample, CDP number): {data_display.shape}')
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
                st.write(f'Data Type: {data_type}')
                st.write(f'Seismic Data Shape (Time sample, crossline number, inline number): {data_display.shape}')

            # Function to plot seismic data
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

            # Plot based on data type
            if data_type == 'Post-stack 2D':
                plot1(data_display, direction='2D Line', segy='seismic')
                st.pyplot(plt.gcf())

            if data_type == 'Post-stack 3D':
                mid_inline = len(inline_number) // 2
                Inline = st.slider('Choose inline', min_value=inline_number[0], max_value=inline_number[-1], step=diff_inline, value=inline_number[mid_inline])
                Iline = int((Inline - inline_number[0]) / diff_inline)
                seismic_data_inline = data_display[:, :, Iline]
                plt.clf()
                plot1(seismic_data_inline, direction='inline', segy='seismic')
                st.pyplot(plt.gcf())

                mid_xline = len(xline_number) // 2
                Crossline = st.slider('Choose crossline', min_value=xline_number[0], max_value=xline_number[-1], step=diff_xline, value=xline_number[mid_xline])
                Xline = int((Crossline - xline_number[0]) / diff_xline)
                seismic_data_xline = data_display[:, Xline, :]
                plt.clf()
                plot1(seismic_data_xline, direction='xline', segy='seismic')
                st.pyplot(plt.gcf())

                mid_twt = len(twt) // 2
                Time = st.slider('Choose Time (ms)', min_value=int(twt[0]), max_value=int(twt[-1]), step=int(sample_rate), value=int(twt[mid_twt]))
                Time_slice = int((Time - twt[0]) / sample_rate)
                seismic_data_time = data_display[Time_slice, :, :]
                plt.clf()
                plot1(seismic_data_time, direction='time-slice', segy='seismic')
                st.pyplot(plt.gcf())

        #working good but onlt sample_2d.sgy no 3d

if __name__ == "__main__":
    main()
