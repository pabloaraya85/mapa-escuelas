
import pandas as pd
import plotly.express as px
from dash import Dash, dcc, html, Input, Output
from geopy.distance import geodesic

# --- Cargar datos ---
df = pd.read_excel("/Users/pabloaraya/Library/CloudStorage/OneDrive-Personal/Datos Educativos/directorio_2024.xlsx")
df["LATITUD"] = pd.to_numeric(df["LATITUD"], errors="coerce")
df["LONGITUD"] = pd.to_numeric(df["LONGITUD"], errors="coerce")

df = df[
    (df["MATRICULA"] == 1) &
    df["LATITUD"].notna() &
    df["LONGITUD"].notna() &
    df["MAT_TOTAL"].notna()
].copy()

df["COD_DEPE"] = df["COD_DEPE"].astype(str)

# --- Diccionarios ---
etiquetas_cod_depe = {
    "1": "CORP", "2": "DAEM", "3": "PS",
    "4": "PP", "5": "SAD", "6": "SLEP"
}
colores_cod_depe = {
    "CORP": "#3498DB", "DAEM": "#E67E22", "PS": "#2ECC71",
    "PP": "#9B59B6", "SAD": "#F1C40F", "SLEP": "#E74C3C"
}
df["DEP_LABEL"] = df["COD_DEPE"].map(etiquetas_cod_depe)

# --- App Dash ---
app = Dash(__name__)
app.title = "PAC Map (Dash)"

app.layout = html.Div([
    html.H2("PAC - Visualización de Escuelas por RBD"),

    html.Label("Selecciona un RBD:"),
    dcc.Dropdown(
        id="rbd-dropdown",
        options=[{"label": f"{rbd}", "value": rbd} for rbd in sorted(df["RBD"].unique())],
        value=sorted(df["RBD"].unique())[0]
    ),

    html.Label("Radio (metros):"),
    dcc.Slider(
        id="radio-slider",
        min=250, max=5000, step=250, value=2000,
        marks={i: f"{i}m" for i in range(250, 5250, 750)}
    ),

    dcc.Graph(id="mapa"),

    html.H4("HHI del radio seleccionado:"),
    html.Pre(id="info-hhi"),

    html.H4("Estadísticas del radio:"),
    html.Div(id="tabla-estadisticas"),
])

@app.callback(
    Output("mapa", "figure"),
    Output("info-hhi", "children"),
    Output("tabla-estadisticas", "children"),
    Input("rbd-dropdown", "value"),
    Input("radio-slider", "value")
)
def actualizar_vista(rbd_sel, radio):
    seleccionado = df[df["RBD"] == rbd_sel]
    if seleccionado.empty:
        return {}, "No encontrado", "Sin datos"

    latlon = (seleccionado.iloc[0]["LATITUD"], seleccionado.iloc[0]["LONGITUD"])

    df_filtrado = df.copy()
    df_filtrado["distancia"] = df_filtrado.apply(
        lambda row: geodesic((row["LATITUD"], row["LONGITUD"]), latlon).meters,
        axis=1
    )
    df_filtrado = df_filtrado[df_filtrado["distancia"] <= radio]

    conteo = df_filtrado["DEP_LABEL"].value_counts(normalize=True)
    hhi = round((conteo ** 2).sum(), 3)

    fig = px.scatter_mapbox(
        df_filtrado,
        lat="LATITUD",
        lon="LONGITUD",
        color="DEP_LABEL",
        color_discrete_map=colores_cod_depe,
        size=df_filtrado["MAT_TOTAL"]**0.5,
        hover_name="NOM_RBD",
        hover_data={"RBD": True, "MAT_TOTAL": True, "DEP_LABEL": True},
        zoom=12, height=500
    )
    fig.update_layout(mapbox_style="open-street-map", margin=dict(r=0, t=0, l=0, b=0))

    tabla = html.Ul([
        html.Li(f"Cantidad de establecimientos: {len(df_filtrado)}"),
        html.Li(f"Matrícula total: {int(df_filtrado['MAT_TOTAL'].sum())}"),
        html.Li(f"Matrícula promedio: {round(df_filtrado['MAT_TOTAL'].mean(), 1)}")
    ])

    return fig, f"HHI (radio {radio} m): {hhi}", tabla

if __name__ == "__main__":
    app.run_server(debug=True)
