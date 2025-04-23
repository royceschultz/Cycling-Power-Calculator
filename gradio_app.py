import gradio as gr
import plotly.graph_objs as go
import plotly.subplots as sp
import numpy as np
from datetime import datetime, timedelta
import os
from utils.load_ride import load_file, get_ride_files
from utils.calculate_metrics import compute_global_metrics
from utils.calculate_power import calculate_power

from gradio_components import (
    generate_line_graph,
    generate_map_scatter,
    generate_histogram,
    generate_altitude_graph
)

def plot_selector(full_df, start_idx, end_idx):
    df = full_df
    # Filter dataframe by index range if available
    if df is not None and not df.empty and start_idx is not None and end_idx is not None:
        start = max(0, int(start_idx))
        end = min(len(df)-1, int(end_idx))
        if start < end:
            df = df.iloc[start:end+1]
    line_plot = generate_line_graph(df)
    map_plot = generate_map_scatter(df)
    power_hist = generate_histogram(df, 'power', 'orange', 'Power Distribution')
    hr_hist = generate_histogram(df, 'heart_rate', 'red', 'Heart Rate Distribution')
    summary = None
    if df is not None and not df.empty:
        summary = df.describe(include='all').T.reset_index().rename(columns={'index': 'field'})
    return map_plot, line_plot, power_hist, hr_hist, df, summary

def load_and_set_df(selected_filename, filetype_filter):
    files, file_map = get_ride_files(filetype_filter)
    selected_file = file_map.get(selected_filename)
    df = None
    if selected_file and selected_file.endswith('.fit'):
        try:
            df = load_file(os.path.basename(selected_file))
        except Exception as e:
            print(f"Error loading fit file: {e}")
    # Set slider range based on df length
    if df is not None and not df.empty:
        max_idx = len(df) - 1
        start_slider_update = gr.update(minimum=0, maximum=max_idx, value=0)
        end_slider_update = gr.update(minimum=0, maximum=max_idx, value=max_idx)
    else:
        start_slider_update = gr.update(minimum=0, maximum=100, value=0)
        end_slider_update = gr.update(minimum=0, maximum=100, value=100)
    altitude_plot = generate_altitude_graph(df)
    # Get the rest of the plots/tables (excluding altitude)
    map_plot, line_plot, power_hist, hr_hist, filtered_df, summary = plot_selector(
        df, start_slider_update["value"], end_slider_update["value"]
    )
    # Compute global metrics
    metrics = compute_global_metrics(df)
    # Stylish HTML for metrics
    metrics_html = f"""
    <div style="display: flex; gap: 2.5em; justify-content: center; align-items: center; font-size: 2em; font-weight: bold; margin: 1em 0;">
      <span style="color:#FFD700;">&#x23F1; {metrics['Total Time']}</span>
      <span style="color:#00BFFF;">&#x1F6B4; {metrics['Total Distance']}</span>
      <span style="color:#A259FF;">&#x27A1;&#xFE0F; {metrics['Average Speed']}</span>
      <span style="color:#FFA500;">&#9889; {metrics['Average Power']}</span>
    </div>
    """
    # --- Add: generate initial calculated power plot using the initial slider range ---
    calc_power_fig = get_calc_power_plot(df, start_slider_update["value"], end_slider_update["value"])
    # Return all outputs in the correct order
    return (
        df, start_slider_update, end_slider_update,
        altitude_plot, map_plot, line_plot, power_hist, hr_hist,
        metrics_html, calc_power_fig
    )

def update_sliders(full_df):
    if full_df is not None and not full_df.empty:
        max_idx = len(full_df) - 1
        return (
            gr.update(minimum=0, maximum=max_idx, value=0),
            gr.update(minimum=0, maximum=max_idx, value=max_idx)
        )
    else:
        return (
            gr.update(minimum=0, maximum=100, value=0),
            gr.update(minimum=0, maximum=100, value=100)
        )

def get_calc_power_plot(full_df, start_idx, end_idx):
    # Only filter, do not recalculate
    if full_df is None or full_df.empty:
        return go.Figure()
    df = full_df
    if start_idx is not None and end_idx is not None:
        start = max(0, int(start_idx))
        end = min(len(df)-1, int(end_idx))
        if start < end:
            df = df.iloc[start:end+1]
    x = df['timestamp'] if 'timestamp' in df else np.arange(len(df))

    # Check if calculated power components exist
    has_calc = (
        'calculated_power' in df and df['calculated_power'].notnull().any() and
        'gravitational_power' in df and 'kinetic_power' in df and 'frictional_power' in df
    )

    if has_calc:
        # --- Subplots: 2 rows, shared x-axis ---
        fig = sp.make_subplots(
            rows=2, cols=1,
            shared_xaxes=True,
            vertical_spacing=0.1,
            subplot_titles=(
                "Calculated Power vs Real Power",
                "Calculated Power Components"
            ),
            row_heights=[0.6, 0.4],
        )

        # --- Top plot: calculated vs real power ---
        avg_real = None
        avg_calc = None
        if 'power' in df and df['power'].notnull().any():
            fig.add_trace(go.Scatter(
                x=x, y=df['power'],
                mode='lines', name='Real Power',
                line=dict(color='orange', width=2),
                opacity=0.6
            ), row=1, col=1)
            avg_real = df['power'].mean()
        if 'calculated_power' in df and df['calculated_power'].notnull().any():
            fig.add_trace(go.Scatter(
                x=x, y=df['calculated_power'],
                mode='lines', name='Calculated Power',
                line=dict(color='cyan', width=2),
                opacity=0.6
            ), row=1, col=1)
            avg_calc = df['calculated_power'].mean()
        # Add metrics as annotation or subtitle
        metrics_text = ""
        if avg_real is not None:
            metrics_text += f"<span style='color:#FFA500'>Avg Real Power: {avg_real:.0f} W</span>"
        if avg_calc is not None:
            if metrics_text:
                metrics_text += " &nbsp;|&nbsp; "
            metrics_text += f"<span style='color:#00FFFF'>Avg Calculated Power: {avg_calc:.0f} W</span>"
        if metrics_text:
            fig.update_layout(
                title=dict(
                    text=f"Calculated Power vs Real Power<br><span style='font-size:1.1em'>{metrics_text}</span>",
                    x=0.5,
                    xanchor='center'
                )
            )

        # --- Bottom plot: power components ---
        if 'gravitational_power' in df:
            fig.add_trace(go.Scatter(
                x=x, y=df['gravitational_power'],
                mode='lines', name='Gravitational Power',
                line=dict(color='green', width=1.5, dash='dot'),
                opacity=0.7
            ), row=2, col=1)
        if 'kinetic_power' in df:
            fig.add_trace(go.Scatter(
                x=x, y=df['kinetic_power'],
                mode='lines', name='Kinetic Power',
                line=dict(color='magenta', width=1.5, dash='dot'),
                opacity=0.7
            ), row=2, col=1)
        if 'frictional_power' in df:
            fig.add_trace(go.Scatter(
                x=x, y=df['frictional_power'],
                mode='lines', name='Frictional Power',
                line=dict(color='yellow', width=1.5, dash='dot'),
                opacity=0.7
            ), row=2, col=1)

        fig.update_yaxes(title_text="Power (W)", row=1, col=1)
        fig.update_yaxes(title_text="Component Power (W)", row=2, col=1)
        fig.update_xaxes(title_text="Time", row=2, col=1)

        fig.update_layout(
            template='plotly_dark',
            plot_bgcolor='#222222',
            paper_bgcolor='#222222',
            font=dict(color='#FFFFFF'),
            margin=dict(l=20, r=20, t=60, b=30),
            height=700,
        )
        return fig
    else:
        # Only show the top plot (no subplots)
        fig = go.Figure()
        avg_real = None
        if 'power' in df and df['power'].notnull().any():
            fig.add_trace(go.Scatter(
                x=x, y=df['power'],
                mode='lines', name='Real Power',
                line=dict(color='orange', width=2),
                opacity=0.6
            ))
            avg_real = df['power'].mean()
        fig.update_layout(
            template='plotly_dark',
            plot_bgcolor='#222222',
            paper_bgcolor='#222222',
            font=dict(color='#FFFFFF'),
            title="Calculated Power vs Real Power" + (
                f"<br><span style='font-size:1.1em'><span style='color:#FFA500'>Avg Real Power: {avg_real:.0f} W</span></span>"
                if avg_real is not None else ""
            ),
            xaxis_title='Time',
            yaxis_title='Power (W)',
            margin=dict(l=20, r=20, t=60, b=30)
        )
        return fig

with gr.Blocks() as demo:
    gr.Markdown("# Ride Data Explorer")
    gr.Markdown("Select a .fit or .gpx file to view ride data, map, and metrics.")

    # File upload and validation
    upload_status = gr.Markdown("", visible=False)

    def handle_upload(uploaded_file):
        import shutil
        import os
        import time
        BASE_FOLDER = "rides"
        if uploaded_file is None:
            return gr.update(visible=False, value=""), gr.update()
        filename = os.path.basename(uploaded_file.name)
        ext = os.path.splitext(filename)[1].lower()
        if ext not in [".fit", ".gpx"]:
            return gr.update(visible=True, value="❌ Invalid file type. Only .fit and .gpx are allowed."), gr.update()
        os.makedirs(BASE_FOLDER, exist_ok=True)
        dest_path = os.path.join(BASE_FOLDER, filename)
        shutil.copy(uploaded_file, dest_path)
        # Ensure file system has flushed the file before refreshing list
        time.sleep(0.2)
        # Now refresh the file list choices
        files, _ = get_ride_files("Both")
        return gr.update(visible=True, value=f"✅ Uploaded: {filename}"), gr.update(choices=files, value=filename)

    with gr.Row():
        with gr.Column(scale=1):
            filetype_filter_radio = gr.Radio(
                choices=["Both", ".fit", ".gpx"],
                value="Both",
                label="File Type Filter",
                interactive=True
            )
            file_upload = gr.File(
                label="Upload .fit or .gpx file",
                file_types=[".fit", ".gpx"],
                type="filepath",  # <-- change from "binary" to "filepath"
                height=80,
            )
        with gr.Column(scale=2):
            file_radio = gr.Radio(
                choices=get_ride_files("Both")[0],
                label="Select .fit or .gpx file from rides folder",
                interactive=True
            )
            file_refresh_btn = gr.Button("Refresh File List")

    file_upload.upload(
        fn=handle_upload,
        inputs=file_upload,
        outputs=[upload_status, file_radio]
    )


    # Move metrics below file selector, use HTML for style
    metrics_html_box = gr.HTML(
        value="""
        <div style="display: flex; gap: 2.5em; justify-content: center; align-items: center; font-size: 2em; font-weight: bold; margin: 1em 0;">
          <span style="color:#FFD700;">&#x23F1; -</span>
          <span style="color:#00BFFF;">&#x1F6B4; -</span>
          <span style="color:#A259FF;">&#x27A1;&#xFE0F; -</span>
          <span style="color:#FFA500;">&#9889; -</span>
        </div>
        """,
        label=None
    )

    full_df_state = gr.State(None)
    altitude_plot_output = gr.Plot(label="Altitude Profile (Full Ride)")
    # Replace Range with two sliders
    start_slider = gr.Slider(
        minimum=0,
        maximum=100,
        value=0,
        step=1,
        label="Start Index",
        interactive=True
    )
    end_slider = gr.Slider(
        minimum=0,
        maximum=100,
        value=100,
        step=1,
        label="End Index",
        interactive=True
    )
    with gr.Row():
        map_output = gr.Plot(label="Ride Map")
        line_output = gr.Plot(label="Ride Metrics")
    with gr.Row():
        power_hist_output = gr.Plot(label="Power Histogram")
        hr_hist_output = gr.Plot(label="Heart Rate Histogram")

    # --- Power Calculation Form ---
    with gr.Accordion("Calculate Estimated Power (Physics Model)", open=False):
        with gr.Row():
            rider_weight_input = gr.Number(
                value=70, label="Rider Weight (kg)", minimum=30, maximum=150, step=0.1
            )
            bike_weight_input = gr.Number(
                value=10, label="Bike Weight (kg)", minimum=5, maximum=30, step=0.1
            )
            tire_type_dropdown = gr.Dropdown(
                choices=[
                    ("Road (23-25mm, 100psi)", 0.003),
                    ("Road (28-32mm, 80psi)", 0.004),
                    ("Gravel (35-40mm, 40psi)", 0.006),
                    ("MTB (2.1-2.4in, 25psi)", 0.010),
                    ("Touring/Commuter", 0.007)
                ],
                label="Tire Type (Rolling Resistance)"
            )
        calc_power_btn = gr.Button("Calculate Power")
        calc_power_status = gr.Markdown("", visible=False)

    # --- Calculated Power Comparison Plot ---
    calc_power_plot = gr.Plot(label="Calculated Power vs Real Power")

    def update_file_choices(filetype_filter):
        files, _ = get_ride_files(filetype_filter)
        return gr.update(choices=files, value=None)

    def update_global_metrics(df):
        metrics = compute_global_metrics(df)
        return (
            f"**Total Time:** {metrics['Total Time']}",
            f"**Total Distance:** {metrics['Total Distance']}",
            f"**Average Speed:** {metrics['Average Speed']}",
            f"**Average Power:** {metrics['Average Power']}"
        )

    file_refresh_btn.click(
        fn=update_file_choices,
        inputs=filetype_filter_radio,
        outputs=file_radio
    )

    filetype_filter_radio.change(
        fn=update_file_choices,
        inputs=filetype_filter_radio,
        outputs=file_radio
    )

    file_radio.change(
        fn=load_and_set_df,
        inputs=[file_radio, filetype_filter_radio],
        outputs=[
            full_df_state, start_slider, end_slider,
            altitude_plot_output, map_output, line_output, power_hist_output, hr_hist_output,
            metrics_html_box, calc_power_plot
        ]
    )

    # When sliders change: use stored df, update plots/tables only
    # Use .release instead of triggers="release"
    def slider_release_handler(full_df, start_idx, end_idx):
        # Unpack outputs from plot_selector
        map_plot, line_plot, power_hist, hr_hist, filtered_df, summary = plot_selector(full_df, start_idx, end_idx)
        # Only filter for the plot, do not recalculate
        calc_power_fig = get_calc_power_plot(full_df, start_idx, end_idx)
        # Just return the filtered_df and summary directly (Gradio will update the Dataframe components)
        return map_plot, line_plot, power_hist, hr_hist, filtered_df, summary, calc_power_fig

    start_slider.release(
        slider_release_handler,
        inputs=[full_df_state, start_slider, end_slider],
        outputs=[map_output, line_output, power_hist_output, hr_hist_output, calc_power_plot]
    )
    end_slider.release(
        slider_release_handler,
        inputs=[full_df_state, start_slider, end_slider],
        outputs=[map_output, line_output, power_hist_output, hr_hist_output, calc_power_plot]
    )

    # Use the global dataframe for slider updates:
    file_radio.change(
        fn=update_sliders,
        inputs=[full_df_state],
        outputs=[start_slider, end_slider]
    )

    # --- Power Calculation Logic ---
    def do_calculate_power(df, rider_weight, bike_weight, tire_type, start_slider, end_slider):
        # tire_type is a tuple (label, value) or just value
        if isinstance(tire_type, (list, tuple)):
            rolling_resistance = float(tire_type[1])
        else:
            rolling_resistance = float(tire_type)
        if df is None or df.empty:
            return df, gr.update(visible=True, value="❌ No data loaded."), go.Figure()
        # Defensive copy
        df = df.copy()
        try:
            calculate_power(df, rider_weight, bike_weight, rolling_resistance)
            fig = get_calc_power_plot(df, start_slider, end_slider)
            return df, gr.update(visible=True, value="✅ Calculated power added to dataframe."), fig
        except Exception as e:
            print(e)
            return df, gr.update(visible=True, value=f"❌ Error: {e}"), go.Figure()

    # --- Power Calculation Button Event ---
    calc_power_btn.click(
        fn=do_calculate_power,
        inputs=[full_df_state, rider_weight_input, bike_weight_input, tire_type_dropdown, start_slider, end_slider],
        outputs=[full_df_state, calc_power_status, calc_power_plot]
    )

if __name__ == "__main__":
    demo.launch()
