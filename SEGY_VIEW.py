import streamlit as st 
import numpy as np
import segyio 
from matplotlib import pyplot as plt

st.header('SEGY VIEWER')
st.title('DEMO1')

# File uploader for SEGY file
filepath_in = st.file_uploader("UPLOAD YOUR SEGY FILE", accept_multiple_files=False, type=None)

# Provide link to sample data
url = "https://drive.google.com/drive/folders/1FPe7tuvOthk0__yzZsXhWevjPucsS5lF?usp=sharing"
st.markdown("[link](%s) for sample data" % url)

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
    def plot(seismic_data, direction=None, segy='seismic'):
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
        plot(data_display, direction='2D Line', segy='seismic')
        st.pyplot(plt.gcf())

    if data_type == 'Post-stack 3D':
        mid_inline = len(inline_number) // 2
        Inline = st.slider('Choose inline', min_value=inline_number[0], max_value=inline_number[-1], step=diff_inline, value=inline_number[mid_inline])
        Iline = int((Inline - inline_number[0]) / diff_inline)
        seismic_data_inline = data_display[:, :, Iline]
        plt.clf()
        plot(seismic_data_inline, direction='inline', segy='seismic')
        st.pyplot(plt.gcf())

        mid_xline = len(xline_number) // 2
        Crossline = st.slider('Choose crossline', min_value=xline_number[0], max_value=xline_number[-1], step=diff_xline, value=xline_number[mid_xline])
        Xline = int((Crossline - xline_number[0]) / diff_xline)
        seismic_data_xline = data_display[:, Xline, :]
        plt.clf()
        plot(seismic_data_xline, direction='xline', segy='seismic')
        st.pyplot(plt.gcf())

        mid_twt = len(twt) // 2
        Time = st.slider('Choose Time (ms)', min_value=int(twt[0]), max_value=int(twt[-1]), step=int(sample_rate), value=int(twt[mid_twt]))
        Time_slice = int((Time - twt[0]) / sample_rate)
        seismic_data_time = data_display[Time_slice, :, :]
        plt.clf()
        plot(seismic_data_time, direction='time-slice', segy='seismic')
        st.pyplot(plt.gcf())
