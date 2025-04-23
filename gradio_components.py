import numpy as np
import plotly.graph_objs as go

def generate_line_graph(df):
    fig = go.Figure()
    if df is not None and not df.empty:
        if 'timestamp' in df:
            x = df['timestamp']
        else:
            x = np.arange(len(df))
        if 'heart_rate' in df:
            fig.add_trace(go.Scatter(
                x=x, y=df['heart_rate'],
                mode='lines', name='Heart Rate',
                line=dict(color='red', width=2),
                opacity=0.7
            ))
        if 'cadence' in df:
            fig.add_trace(go.Scatter(
                x=x, y=df['cadence'],
                mode='lines', name='Cadence',
                line=dict(color='blue', width=2),
                opacity=0.7
            ))
        if 'speed' in df:
            fig.add_trace(go.Scatter(
                x=x, y=df['speed'],
                mode='lines', name='Speed',
                line=dict(color='purple', width=2),
                opacity=0.7
            ))
        if 'power' in df:
            fig.add_trace(go.Scatter(
                x=x, y=df['power'],
                mode='lines', name='Power',
                line=dict(color='orange', width=2),
                opacity=0.7
            ))
        fig.update_layout(
            template='plotly_dark',
            plot_bgcolor='#222222',
            paper_bgcolor='#222222',
            font=dict(color='#FFFFFF'),
            title='Ride Metrics Over Time',
            xaxis_title='Time',
            yaxis_title='Value',
            xaxis=dict(
                tickangle=30,
                gridcolor='#444444',
                tickformat='%H:%M:%S' if 'timestamp' in df else None  # Only show time
            ),
            yaxis=dict(
                gridcolor='#444444'
            ),
            margin=dict(l=20, r=20, t=40, b=20)  # Tighten up borders
        )
    else:
        fig.update_layout(
            template='plotly_dark',
            plot_bgcolor='#222222',
            paper_bgcolor='#222222',
            font=dict(color='#FFFFFF'),
            title='No Data Loaded',
            margin=dict(l=20, r=20, t=40, b=20)
        )
    return fig

def generate_map_scatter(df):
    fig = go.Figure()
    if df is not None and not df.empty and 'position_lat' in df and 'position_long' in df:
        fig.add_trace(go.Scattermapbox(
            lat=df['position_lat'],
            lon=df['position_long'],
            mode='markers+lines',
            marker=go.scattermapbox.Marker(size=7, color='#FFD700'),
            name='Ride Path'
        ))
        lat_center = df['position_lat'].mean()
        lon_center = df['position_long'].mean()
        # Calculate bounds
        lat_min, lat_max = df['position_lat'].min(), df['position_lat'].max()
        lon_min, lon_max = df['position_long'].min(), df['position_long'].max()
        # Calculate zoom level based on bounds (approximate)
        def calc_zoom(lat_min, lat_max, lon_min, lon_max):
            lat_range = max(abs(lat_max - lat_min), 1e-6)
            lon_range = max(abs(lon_max - lon_min), 1e-6)
            max_range = max(lat_range, lon_range)
            if max_range < 0.001:
                return 15
            elif max_range < 0.01:
                return 13
            elif max_range < 0.05:
                return 11
            elif max_range < 0.1:
                return 10
            elif max_range < 0.5:
                return 8
            elif max_range < 1:
                return 7
            else:
                return 5
        zoom = calc_zoom(lat_min, lat_max, lon_min, lon_max)
        fig.update_layout(
            mapbox_style="carto-darkmatter",
            mapbox=dict(
                center=dict(lat=lat_center, lon=lon_center),
                zoom=zoom,
            ),
            margin=dict(l=20, r=20, t=40, b=20),  # Tighten up borders
            title="Ride Map",
            font=dict(color='#FFFFFF'),
            paper_bgcolor='#222222',
            plot_bgcolor='#222222'
        )
    else:
        fig.update_layout(
            template='plotly_dark',
            plot_bgcolor='#222222',
            paper_bgcolor='#222222',
            font=dict(color='#FFFFFF'),
            title='No GPS Data',
            margin=dict(l=20, r=20, t=40, b=20)
        )
    return fig

def generate_histogram(df, column, color, title):
    fig = go.Figure()
    if df is not None and not df.empty and column in df:
        fig.add_trace(go.Histogram(
            x=df[column],
            marker_color=color,
            nbinsx=30,
            name=title
        ))
        fig.update_layout(
            template='plotly_dark',
            plot_bgcolor='#222222',
            paper_bgcolor='#222222',
            font=dict(color='#FFFFFF'),
            title=title,
            xaxis_title=column.capitalize(),
            yaxis_title='Count',
            margin=dict(l=20, r=20, t=40, b=20)  # Tighten up borders
        )
    else:
        fig.update_layout(
            template='plotly_dark',
            plot_bgcolor='#222222',
            paper_bgcolor='#222222',
            font=dict(color='#FFFFFF'),
            title=f'No {column.capitalize()} Data',
            margin=dict(l=20, r=20, t=40, b=20)
        )
    return fig

def generate_altitude_graph(df):
    fig = go.Figure()
    if df is not None and not df.empty:
        if 'timestamp' in df:
            x = df['timestamp']
        else:
            x = np.arange(len(df))
        y = None
        if 'altitude' in df:
            y = df['altitude']
            label = 'Altitude'
        elif 'enhanced_altitude' in df:
            y = df['enhanced_altitude']
            label = 'Enhanced Altitude'
        else:
            y = None
            label = 'Altitude'
        if y is not None:
            fig.add_trace(go.Scatter(
                x=x, y=y,
                mode='lines', name=label,
                line=dict(color='green')
            ))
            fig.update_layout(
                template='plotly_dark',
                plot_bgcolor='#222222',
                paper_bgcolor='#222222',
                font=dict(color='#FFFFFF'),
                title='Altitude Profile (Full Ride)',
                yaxis_title='Altitude (m)',
                xaxis=dict(
                    tickangle=30,
                    gridcolor='#444444',
                    fixedrange=True,
                    tickformat='%H:%M:%S' if 'timestamp' in df else None  # Only show time
                ),
                yaxis=dict(
                    gridcolor='#444444',
                    fixedrange=True
                ),
                dragmode=False,
                height=200,
                margin=dict(l=20, r=20, t=40, b=20)  # Tighten up borders
            )
        else:
            fig.update_layout(
                template='plotly_dark',
                plot_bgcolor='#222222',
                paper_bgcolor='#222222',
                font=dict(color='#FFFFFF'),
                title='No Altitude Data',
                xaxis=dict(fixedrange=True),
                yaxis=dict(fixedrange=True),
                dragmode=False,
                height=180,
                margin=dict(l=20, r=20, t=40, b=20)
            )
    else:
        fig.update_layout(
            template='plotly_dark',
            plot_bgcolor='#222222',
            paper_bgcolor='#222222',
            font=dict(color='#FFFFFF'),
            title='No Data Loaded',
            xaxis=dict(fixedrange=True),
            yaxis=dict(fixedrange=True),
            dragmode=False,
            height=180,
            margin=dict(l=20, r=20, t=40, b=20)
        )
    return fig
