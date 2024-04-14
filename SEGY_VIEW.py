import streamlit as st
import ipywidgets as widgets
from ipywidgets import interact
import os
import sys
import numpy as np
import segyio 
from matplotlib import pyplot as plt
st.header('SEGY VIEWER')
st.title('DEMO1')
filepath_in = st.file_uploader("UPLOAD YOUR SEGY FILE", accept_multiple_files=False, type=None)

url = "https://drive.google.com/drive/folders/1FPe7tuvOthk0__yzZsXhWevjPucsS5lF?usp=sharing"
st.write("check out this [link](%s)" % url)
st.markdown(" [link](%s) for sample data " % url)
st.write('Ignore the error')
# if filepath_in is None:
#   filepath_in = ""
# else:
#   filepath_in = filepath_in.name
  
#   st.write(f"You uploaded: {filepath_in}")
  
if filepath_in is not None:
    filepath_in = filepath_in.name
    print(filepath_in)
else:
    filepath_in = ""

# # def identify_seismic_data_parameters(filepath_in):
data_type='' 


        





with segyio.open(filepath_in, ignore_geometry=True ) as f:
    data_format = f.format

# Supported inline and crossline byte locations
inline_xline = [[189,193], [9,13], [9,21], [5,21]]
state = False
# data_type=''
# Read segy data with the specified byte location of geometry 
for k, byte_loc in enumerate(inline_xline):

    try:
        with segyio.open(filepath_in, iline = byte_loc[0], xline = byte_loc[1], ignore_geometry=False) as f:
            # Get the attributes
            seismic_data = segyio.tools.cube(f)
            n_traces = f.tracecount    
            # data = f.trace.raw[:].T 
            # tr = f.bin[segyio.BinField.Traces]
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
            
            # TRACE_SEQUENCE_FILE _ byte location:5
            TraceSequenceFile = []
            # FieldRecord _ byte location:9
            Field_Record = []
            # Trace_Field _ byte location:13
            Trace_Field = []
            # CDP _ byte location:21
            CDP = []
            # INLINE_3D _ byte location:189
            Inline_3D = []
            # CROSSLINE_3D _ byte location:193
            Crossline_3D = []

            for i in range(n_traces):
                trace_no = f.attributes(segyio.TraceField.TRACE_SEQUENCE_FILE)[i]; TraceSequenceFile.append(trace_no)
                field_record = f.attributes(segyio.TraceField.FieldRecord)[i]; Field_Record.append(field_record)
                trace_field = f.attributes(segyio.TraceField.TraceNumber)[i]; Trace_Field.append(trace_field)
                cdp = f.attributes(segyio.TraceField.CDP)[i]; CDP.append(cdp)
                inline = f.attributes(segyio.TraceField.INLINE_3D)[i]; Inline_3D.append(inline)
                xline = f.attributes(segyio.TraceField.CROSSLINE_3D)[i]; Crossline_3D.append(xline)

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
        
        # Identify data as 2D/3D and Post-stack/Pre-stack
        if len(seismic_data.shape) == 3:
            if seismic_data.shape[0] != 1:
                data_type = 'Post-stack 3D'
            else:
                if n_traces > tr > 1:   
                    data_type = 'Post-stack 3D'
                else:
                    data_type = 'Post-stack 2D'
                
        else:        
            if len(f.offsets) > 1:
                if seismic_data.shape[0] == 1:
                    data_type = 'Pre-Stack 2D'
                else:
                    data_type = 'Pre-Stack 3D'    
            else:
                print('Error, Please check inline and crossline byte locations')

        # create geometry-related parameters
        if k==0:
            inline_number = inline3d 
            xline_number = crossline3d
        elif k==1:
            inline_number = fieldrecord 
            xline_number = tracefield
        elif k==2:
            inline_number = fieldrecord 
            xline_number = cdpnumber
        elif k==3:
            inline_number = tracesequence 
            xline_number = cdpnumber

        if data_type == 'Post-stack 3D':
            if len(inline_number) == 1 or len(xline_number) == 1:
                pass
            else:
                break
        else:
            break


# reshape seismic data to the corresponding format based on data type
try:
    inline, cdp, samples = seismic_data.shape
except:
    print("Error, data was not loaded successfully, this could happen due to unsupported data format: {0}.".format(data_format)) 
    print("In addition, please check inline and crossline byte locations, that might not be supported in this script.")  
    print("Data format 4-byte IBM float and 4-byte IEEE float are supported.")

            
if data_type == 'Post-stack 2D':
    data_display = seismic_data.reshape(cdp, samples).T
    cdp_no = np.arange(n_traces) 

    diff_inline = 1
    diff_xline = 1

    print('Data Type: {0}'.format(data_type))
    print('Seismic Data Shape (Time sample, CDP number) : {0}'.format(data_display.shape))

elif data_type == 'Post-stack 3D':
    if inline == 1 and tr > 1 and n_traces % tr == 0:  
        inline_no =  n_traces / tr
        data_display = seismic_data.reshape(int(inline_no), int(tr), int(samples)).T
        xline_number = np.arange(tr)
        inline_number = np.arange(inline_no)
        cdp_no = xline_number

    else:  
        data_display = seismic_data.reshape(inline, cdp, samples).T
        cdp_no = np.arange(cdp)
        
    diff_inline = np.diff(inline_number)[0]
    diff_xline = np.diff(xline_number)[0]

    print('Data Type: {0}'.format(data_type))
    print('Seismic Data Shape (Time sample, crossline number, inline number) : {0}'.format(data_display.shape))

# return data_display, data_type, data_display.shape, cdp_no, sample_rate, twt, inline_number, xline_number, diff_inline, diff_xline

# data_display, data_type, seismic_data_shape, cdp_no, sample_rate, twt , inline_number, xline_number, diff_inline, diff_xline= identify_seismic_data_parameters(filepath_in)




def plot(seismic_data, direction = None, segy = 'seismic'):

    '''
    Function to plot seismic amplitude traces
    '''

    if segy == 'seismic':
        color = plt.cm.seismic
    elif segy == 'property':
        color = plt.cm.jet

    # Plot seismic data 
    if direction == 'inline':
        extent = (np.min(xline_number), np.max(xline_number), np.max(twt), np.min(twt))
        plt.xlabel("Crossline No.")
        plt.ylabel("Time (ms)")
        label = 'Interactive In-line Visualization'
        
    elif direction == 'xline':
        extent = (np.min(inline_number), np.max(inline_number), np.max(twt), np.min(twt))
        plt.xlabel("Inline No.")
        plt.ylabel("Time (ms)")
        label = 'Interactive Cross-line Visualization'

    elif direction == 'time-slice':
        extent = (np.min(inline_number), np.max(inline_number), np.max(xline_number), np.min(xline_number))
        plt.xlabel("Inline No.")
        plt.ylabel("Crossline No.")
        label = 'Interactive Time-Slice Visualization'

    elif direction == '2D Line':
        extent = (np.min(xline_number), np.max(xline_number), np.max(twt), np.min(twt))
        plt.xlabel("CDP No.")
        plt.ylabel("Time (ms)")
        label = '2D Line Visualization'

    # plt.figure(figsize=(10,10))
    plt.imshow(seismic_data, interpolation = 'nearest', cmap = color, aspect = 'auto', 
               vmin = -np.max(seismic_data), vmax = np.max(seismic_data), extent = extent)
    # plt.title("{0} \n Seismic file name: {1}".format(label, os.path.splitext(os.path.basename(filepath))[0]))
    plt.grid(True)
    plt.colorbar()
    plt.show()

sgy_file = 'seismic_amplitude' # default
# sgy_file = 'property'

if sgy_file == 'seismic_amplitude':
    cmp = 'seismic'
else:
    cmp = 'property'

if data_type == 'Post-stack 2D':
    plot(data_display, direction='2D Line', segy = cmp)
    st.pyplot(plt.gcf())

if data_type == 'Post-stack 3D':

    mid = len(inline_number)//2
    # @interact(Inline=widgets.IntSlider(min=inline_number[0], max=inline_number[-1], step=diff_inline, value=inline_number[mid]))
    # inline_min, inline_max = int(np.min(inline_number)), int(np.max(inline_number))
    Inline = st.slider('choose inline',min_value=inline_number[0], max_value=inline_number[-1], step=diff_inline, value=inline_number[mid])
    
    # def display_seismic_data(Inline):    
    Iline = int((Inline - inline_number[0])/diff_inline)
    seismic_data = data_display[:,:,Iline]
    plt.clf()
    plot(seismic_data, direction='inline', segy = cmp)
    
    st.pyplot(plt.gcf())

if data_type == 'Post-stack 3D':

    mid = len(xline_number)//2
    # @interact(Crossline=widgets.IntSlider(min=xline_number[0], max=xline_number[-1], step=diff_xline, value=xline_number[mid]))
    Crossline = st.slider('choose crossline',min_value=xline_number[0], max_value=xline_number[-1], step=diff_xline, value=xline_number[mid])
    # def display_seismic_data(Crossline):    
    Xline = int((Crossline - xline_number[0])/diff_xline)
    seismic_data = data_display[:,Xline,:]
    plt.clf()
    plot(seismic_data, direction='xline', segy = cmp)
    
    st.pyplot(plt.gcf())

if data_type == 'Post-stack 3D':

    mid = len(twt)//2
    # @interact(TWT=widgets.IntSlider(min=twt[0], max=twt[-1], step=sample_rate, value=twt[mid]))
    TWT = st.slider('choose time',min_value=twt[0], max_value=twt[-1], step=sample_rate, value=twt[mid])
    # def display_seismic_data(TWT):    
    Time_ms = int((TWT - twt[0])/sample_rate)
    seismic_data = data_display[Time_ms,:,:]
    plt.clf()
    plot(seismic_data, direction='time-slice', segy = cmp)
    
    st.pyplot(plt.gcf())

        

