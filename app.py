import dash
from dash import html, dcc, Output, Input, State, ctx, ALL, MATCH, callback
import dash_bootstrap_components as dbc
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import ast
from dash import callback_context
from dash.exceptions import PreventUpdate
# --- CONFIGURACIÓN SHEETS ---
SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']
CREDS_FILE = "credenciales.json"
SPREADSHEET_ID = '1It1n3hwNDrIrRvB3hZeuaSVhZerpA17TYtVQE-z0AAs'


def cargar_datos():
    creds = Credentials.from_service_account_file(CREDS_FILE, scopes=SCOPES)
    gc = gspread.authorize(creds)
    sh = gc.open_by_key(SPREADSHEET_ID)

    data = sh.worksheet('Personal').get_all_records()
    df = pd.DataFrame(data)

    vacantes = sh.worksheet('Vacantes').get_all_records()
    vacantes_df = pd.DataFrame(vacantes)

    contratos = sh.worksheet('Contratos').get_all_records()
    contratos_df = pd.DataFrame(contratos)

    contratosvacantes = sh.worksheet('ContratosVacantes').get_all_records()
    contratosvacantes_df = pd.DataFrame(contratosvacantes)

    return df, vacantes_df, contratos_df, contratosvacantes_df

def agrupar_vacantes(vacantes_df):
    vacantes_por_departamento = {}
    for _, row in vacantes_df.iterrows():
        depto = row["Departamento"]
        puesto = row["Nombre del Puesto"]
        if depto not in vacantes_por_departamento:
            vacantes_por_departamento[depto] = {}
        if puesto not in vacantes_por_departamento[depto]:
            vacantes_por_departamento[depto][puesto] = []
        vacantes_por_departamento[depto][puesto].append(row)
    return vacantes_por_departamento

def agrupar_contratos_vacantes(contratos_vacantes_df):
    contratos_vacantes_por_departamento = {}

    for _, row in contratos_vacantes_df.iterrows():
        depto = row["Departamento"]
        puesto = row["Nombre del Puesto"]

        if depto not in contratos_vacantes_por_departamento:
            contratos_vacantes_por_departamento[depto] = {}

        if puesto not in contratos_vacantes_por_departamento[depto]:
            contratos_vacantes_por_departamento[depto][puesto] = []

        contratos_vacantes_por_departamento[depto][puesto].append(row)

    return contratos_vacantes_por_departamento

def agrupar_contratos(df_contratos):
    # Suponiendo que en contratos_df hay una columna 'Departamento'
    contratos_por_depto = {}
    for depto, group in df_contratos.groupby('Departamento'):
        contratos_por_depto[depto] = group.to_dict('records')
    return contratos_por_depto

def generar_tarjetas_contratos(contratos):
    tarjetas = []
    for contrato in contratos:
        tarjeta = html.Div([
            html.Div([
                html.Img(src=contrato["Foto URL"], style={"width": "100%", "border-radius": "10px"}),
                html.P(contrato["NombreC"], style={"font-weight": "bold", "margin": "4px 0","font-size": "14px"}),
                html.P(contrato["Cargo"], style={"font-size": "12px", "color": "#666"}),
            ],
            style={
                "border": "1px solid #ccc",
                "border-radius": "10px",
                #"padding": "2px",
                "text-align": "center",
                "background": "#f9f9f9",
                "cursor": "pointer"  # indica que es clickeable
            })
        ],
        id={'type': 'contrato-tarjeta', 'index': contrato["NombreC"]},
        n_clicks=0,
        style={"cursor": "pointer"})
        tarjetas.append(tarjeta)

    return html.Div(tarjetas, style={
    "display": "grid",
    "gridTemplateColumns": "repeat(auto-fill, minmax(100px, 1fr))",  # reduce ancho mínimo
    "gap": "10px",
    "margin": "10px 0",
    "maxWidth": "500px",  # limita el ancho total para que no se extienda demasiado
    "justifyContent": "center"
    })
# generar modal y tarjetas de secretaria particular
def generar_tarjetas_clickables(personas):
    tarjetas = []

    for i, p in personas.iterrows():
        tarjeta_contenido = [
            dbc.CardImg(src=p.get('Foto URL', ''), top=True,
                        style={'width': '80px', 'height': '80px', 'object-fit': 'cover', 'border-radius': '50%', 'margin-bottom': '10px'}),  # Foto circular
            dbc.CardBody([
                html.H6(p.get('Nombre', 'Sin nombre'), className='card-title', style={'fontSize': '16px', 'fontWeight': 'bold'}),
                html.P(f"Cargo: {p.get('Cargo', '')}", className='card-text', style={'fontSize': '14px', 'color': '#777'}),
                dbc.Button("Ver detalles",
                           id={'type': 'ver-detalles-btn', 'index': i},
                           n_clicks=0,
                           color='primary',
                           size='sm',
                           style={'width': '100%', 'borderRadius': '5px', 'marginTop': '10px'})  # Botón centrado abajo
            ], style={'textAlign': 'center'})
        ]
        
        # Almacenamos el contenido adicional de la tarjeta en una lista
        tarjeta_detalle = html.Div([
            html.P(f"Unidad física: {p.get('Unidad física', '')}", className='card-text', style={'fontSize': '14px', 'color': '#777'}),
            html.P(f"Género: {p.get('Genero', '')}", className='card-text', style={'fontSize': '14px', 'color': '#777'}),
            html.P(f"Fecha de ingreso: {p.get('Fecha de Ingreso', '')}", className='card-text', style={'fontSize': '14px', 'color': '#777'}),
            html.P(f"Sueldo Neto: {p.get('Sueldo', '')}", className='card-text', style={'fontSize': '14px', 'color': '#777'}),
            html.P(f"Cumpleaños: {p.get('Cumpleaños', '')}", className='card-text', style={'fontSize': '14px', 'color': '#777'}),
            # Aquí puedes agregar más datos si lo deseas
        ], id={'type': 'detalle-tarjeta', 'index': i}, style={'display': 'none'})  # Ocultamos esta parte inicialmente
        
        tarjetas.append(
            dbc.Card([
                dbc.CardBody(tarjeta_contenido),
                tarjeta_detalle
            ], style={
                'width': '250px', 
                'margin': '15px', 
                'boxShadow': '0 6px 15px rgba(0, 0, 0, 0.1)',  # Sombra suave
                'borderRadius': '12px',  # Bordes redondeados
                'transition': 'transform 0.3s ease, box-shadow 0.3s ease',  # Efecto de transición
                'cursor': 'pointer',
                'minHeight': '150px'  # Asegura que las tarjetas no queden demasiado pequeñas
            })
        )

    return dbc.Row(tarjetas, justify='center', style={'flexWrap': 'wrap', 'gap': '20px'})
# tarjetas personal
def generar_tarjetas_personal(personal):
    tarjetas = []
    for persona in personal:
                tarjeta = html.Div([
                    html.Img(src=persona["Foto URL"], style={"width": "100%", "border-radius": "10px"}),
                    html.P(persona["Nombre"], style={"font-weight": "bold", "margin": "4px 0","font-size": "14px"}),
                    html.P(persona["Cargo"], style={"font-size": "12px", "color": "#666"}),
                    ],
                id={'type': 'persona-tarjeta', 'index': persona["Nombre"]},  # id para callback
                n_clicks=0,
                style={
                        "border": "1px solid #ccc",
                        "border-radius": "10px",
                        #"padding": "2px",
                        "text-align": "center",
                        "background": "#f9f9f9",
                        "cursor": "pointer"  # indica que es clickeable
                })
                tarjetas.append(tarjeta)

    return html.Div(tarjetas, style={
    "display": "grid",
    "gridTemplateColumns": "repeat(auto-fill, minmax(100px, 1fr))",  # reduce ancho mínimo
    "gap": "10px",
    "margin": "10px 0",
    "maxWidth": "500px",  # limita el ancho total para que no se extienda demasiado
    "justifyContent": "center"
    })

def build_vacantes_component(depto):
    cargos = vacantes_por_departamento.get(depto, {})
    
    if not cargos:
        return html.Div("No hay vacantes", style={'fontStyle': 'italic', 'fontSize': 'small', 'color': '#666'})

    ui = []
    for puesto, plazas in cargos.items():
        ui.append(
            html.Details([
                html.Summary(f"{puesto} ({len(plazas)})", style={'cursor': 'pointer', 'fontWeight': '500'}),
                html.Ul([
                    html.Li(
                        f"Plaza {p['No. de Plaza']} | Tipo: {p['Tipo de Plaza']} | Sueldo Neto: {p['Sueldo Neto']}",
                        style={'fontSize': '13px'}
                    )
                    for p in plazas
                ], style={'marginLeft': '20px'})
            ], style={'marginBottom': '8px'})
        )
    return html.Div(ui, style={'marginTop': '8px'})

def build_contratos_vacantes_component(depto, contratos_vacantes_por_departamento):
    cargos = contratos_vacantes_por_departamento.get(depto, {})

    if not cargos:
        return html.Div("No hay contratos vacantes", style={'fontStyle': 'italic', 'fontSize': 'small', 'color': '#666'})

    ui = []
    for puesto, vacantes in cargos.items():
        ui.append(
            html.Details([
                html.Summary(f"{puesto} ({len(vacantes)})", style={'cursor': 'pointer', 'fontWeight': '500'}),
                html.Ul([
                    html.Li(
                        f"Plaza {v['No. de Plaza']} | Tipo: {v['Tipo de Plaza']} | Rango: {v['Rango']} | Sueldo Neto: {v['Sueldo Neto']}",
                        style={'fontSize': '13px'}
                    )
                    for v in vacantes
                ], style={'marginLeft': '20px'})
            ], style={'marginBottom': '8px'})
        )
    return html.Div(ui, style={'marginTop': '8px'})

df, vacantes_df, contratos_df, contratosvacantes_df = cargar_datos()
# --- Construcción de estructura jerárquica ---
def build_estructura_departamentos(df):
    estructura = {}
    departamentos = df['Departamento'].unique()
    for depto in departamentos:
        fila = df[df['Departamento'] == depto].iloc[0]
        superior = fila['Departamento Superior']
        if pd.isna(superior) or superior == '' or superior is None:
            superior = None
        if depto not in estructura:
            estructura[depto] = {'personas': [], 'subdepartamentos': {}}

    for depto in estructura:
        fila = df[df['Departamento'] == depto].iloc[0]
        superior = fila['Departamento Superior']
        if pd.notna(superior) and superior != '' and superior in estructura:
            estructura[superior]['subdepartamentos'][depto] = estructura[depto]

    for _, row in df.iterrows():
        depto = row['Departamento']
        if depto in estructura:
            estructura[depto]['personas'].append(row)

    raiz = {k: v for k, v in estructura.items() if
            pd.isna(df[df['Departamento'] == k]['Departamento Superior'].iloc[0]) or
            df[df['Departamento'] == k]['Departamento Superior'].iloc[0] == ''}

    return raiz

estructura = build_estructura_departamentos(df)

# --- App ---
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
app.title = "Organigrama Dinámico"
vacantes_por_departamento = agrupar_vacantes(vacantes_df)
app.layout = html.Div([
    html.H1("Organigrama Subsecretaría General de Gobierno", className="titulo-organigrama"),
    dbc.Button("Ver Personal Secretaría Particular", id="abrir-modal-secretaria", n_clicks=0, color="info", style={'display':'none'}),
    dcc.Store(id='visible-departments', data={}),
    html.Div(id='organigrama-container'),
    html.Div(id='dummy-output', style={'display': 'none'}),
    dcc.Location(id='url', refresh=False),
    
        # MODAL SECRETARÍA PARTICULAR con botón y contenedor de vacantes
    dbc.Modal([
        dbc.ModalHeader(dbc.ModalTitle("Personal Secretaría Particular")),
        dbc.ModalBody([
            html.Div(id='modal-secretaria-body'),  # Tarjetas del personal
            
            html.Hr(),

            dbc.Button(
                "Ver Vacantes Secretaría Particular",
                id="btn-ver-vacantes-secretaria",
                color="secondary",
                n_clicks=0,
                style={'marginTop': '10px'}
            ),

            html.Div(id='vacantes-secretaria-container', style={'marginTop': '10px', 'display': 'none'})
        ]),
        dbc.ModalFooter(
            dbc.Button("Cerrar", id="cerrar-modal-secretaria", className="ms-auto", n_clicks=0)
        ),
    ], id='modal-secretaria', is_open=False, size='lg', centered=True),

        dbc.Modal([
            dbc.ModalHeader(dbc.ModalTitle(id='modal-title')),
            dbc.ModalBody(id='modal-content'),
            dbc.ModalFooter(
            dbc.Button("Cerrar", id="close-modal", className="ms-auto", n_clicks=0)
            ),
        ], id='modal-persona', is_open=False, size='md', centered=True),
    ])
app.clientside_callback(
    """
    function(pathname) {
        const nodoPrincipal = document.querySelector('[id^="departamento-nodo.Oficina del C. Subsecretario General"]');
        if (nodoPrincipal) {
            nodoPrincipal.scrollIntoView({behavior: "smooth", block: "center", inline: "center"});
        }
        return "";
    }
    """,
    Output('dummy-output', 'children'),
    Input('url', 'pathname')
),
# --- Nodo visual de una persona ---
def create_node(persona):
    return html.Div([
        html.Img(
            src=persona['Foto URL'],
            className="tarjeta-jefe-img"  # Usamos la clase CSS para la imagen
        ),
        html.P(persona['Nombre'], className="nombre"),  # Usamos la clase CSS para el nombre
        html.P(persona['Cargo'], className="cargo")  # Usamos la clase CSS para el cargo
    ], 
    className="tarjeta-jefe",  # Usamos la clase CSS para la tarjeta
    n_clicks=0,
    id={'type': 'persona', 'index': persona['Nombre']})

def build_tree_departamentos(estructura, visible_departments=None, contratos_por_departamento=None, contratos_vacantes_por_departamento=None):
     
    if contratos_vacantes_por_departamento is None:
        contratos_vacantes_por_departamento = {}

    if contratos_por_departamento is None:
        contratos_por_departamento = {}

    if visible_departments is None:
        visible_departments = {}
    
    children = []
   
    for depto_nombre, depto_data in estructura.items():
        
        # Verificamos si el nodo debe ser visible o no
        is_visible = visible_departments.get(depto_nombre, False)
        
        # Si es el nodo principal, le agregamos el botón extra para "Secretaría Particular"
        if depto_nombre == 'Oficina del C. Subsecretario General':
            boton_secretaria = html.Button(
                "Ver Personal Secretaría Particular",
                id="abrir-modal-secretaria",
                n_clicks=0,
                className="btn-elegante",
                style={'marginBottom': '10px'}
            )
        else:
            boton_secretaria = None
        
        depto_id = {'type': 'depto-toggle', 'index': depto_nombre}
        jefe = None
        for persona in depto_data['personas']:
            jefe_campo = persona.get('Jefe', None)
            if pd.isna(jefe_campo) or jefe_campo == '' or jefe_campo is None:
                jefe = persona
                break

        jefe_node = create_node(jefe) if jefe is not None else None
        personas_sin_jefe = [p for p in depto_data['personas'] if p is not jefe]
        # Calcular totales de cada sección para mostrarlos en los botones
        total_personal = len(personas_sin_jefe)
        total_contratos = len(contratos_por_departamento.get(depto_nombre, []))
        total_vacantes = len(vacantes_por_departamento.get(depto_nombre, []))
        total_contratos_vac = len(contratos_vacantes_por_departamento.get(depto_nombre, []))
        nodo = html.Div([
            # Encabezado con nombre del departamento, ícono y jefe
                html.Div([
    # Título e icono en su propio div
            html.Div(
                html.Span([
                    html.Span('➕', id={'type': 'depto-icono', 'index': depto_nombre}),  # icono inicial
                    f" {depto_nombre}"
                ], id=depto_id, n_clicks=0, className="departamento-box"),
                style={'marginBottom': '8px'}
            ),

            html.Div(jefe_node, style={
            'display': 'inline-block',
            'marginLeft': '15px',
            'verticalAlign': 'middle',

        })
            ], style={
                'textAlign': 'center',
                'marginBottom': '10px',
                'display': 'flex',
                'alignItems': 'center',
                'justifyContent': 'center',
                'font-size': '14px',
                'gap': '15px'# espacio entre nombre del departamento y tarjeta-jefe
            }),
            # Segunda fila: botones en columna debajo
           html.Div([
                html.Button(f'👤 Personal ({total_personal})', id={'type': 'personal-toggle', 'index': depto_nombre}, n_clicks=0, className="btn-elegante"),
                html.Button(f'📌 Vacantes ({total_vacantes})', id={'type': 'vacantes-toggle', 'index': depto_nombre}, n_clicks=0, className="btn-elegante"),
                html.Button(f'📄 Contratos ({total_contratos})', id={'type': 'contratos-toggle', 'index': depto_nombre}, n_clicks=0, className="btn-elegante"),
                html.Button(f'📋 Contratos Vacantes ({total_contratos_vac})', id={'type': 'contratosvacantes-toggle', 'index': depto_nombre}, n_clicks=0, className="btn-elegante"),
               
            ], style={
                'display': 'flex',
                'flexDirection': 'column',
                'alignItems': 'center',
                'marginBottom': '10px'
            }),

            boton_secretaria,  # ⬅️ Aquí insertas el botón
            # Contenido expandible (incluye secciones colapsables)
                        # Contenido expandible con tarjetas debajo del nodo y ramas después
            html.Div([
                
                # Secciones colapsables: Personal, Contratos, Vacantes, etc.
                html.Div([
                    html.Div([
                        html.H6("Personal:", style={'marginTop': '10px', 'marginBottom': '4px'}),
                        generar_tarjetas_personal(
                            [p.to_dict() if isinstance(p, pd.Series) else p for p in personas_sin_jefe]
                        )
                    ], id={'type': 'personal-box', 'index': depto_nombre}, style={'display': 'none'}),

                    html.Div([
                        html.H6("Contratos:", style={'marginTop': '10px', 'marginBottom': '4px'}),
                        generar_tarjetas_contratos(contratos_por_departamento.get(depto_nombre, []))
                    ], id={'type': 'contratos-box', 'index': depto_nombre}, style={'display': 'none'}),

                    html.Div([
                        html.H6("Vacantes:", style={'marginTop': '10px', 'marginBottom': '4px'}),
                        build_vacantes_component(depto_nombre)
                    ], id={'type': 'vacantes-box', 'index': depto_nombre}, style={'display': 'none'}),

                    html.Div([
                        html.H6("Contratos Vacantes:", style={'marginTop': '10px', 'marginBottom': '4px'}),
                        build_contratos_vacantes_component(depto_nombre, contratos_vacantes_por_departamento)
                    ], id={'type': 'contratosvacantes-box', 'index': depto_nombre}, style={'display': 'none'}),
                   
                ], style={
                    'display': 'flex',
                    'flexDirection': 'column',
                    'alignItems': 'center',
                    'gap': '10px',
                    'width': '100%',
                }),
                 
                # Subdepartamentos distribuidos horizontalmente
                html.Div(
                    build_tree_departamentos(depto_data['subdepartamentos'], visible_departments),
                    style={
                        'marginTop': '30px',
                        'display': 'flex',
                        'gap': '30px',
                        'justifyContent': 'center',
                        'alignItems': 'flex-start',
                        'flexDirection': 'row',
                        'width': '100%'
                    }
                )
            ], id={'type': 'contenido-expandible', 'index': depto_nombre},
            className='contenido-expandible' + (' mostrar' if is_visible else ''))
            ], id=f"departamento-nodo.{depto_nombre}", style={'display': 'flex', 'flexDirection': 'column', 'alignItems': 'center'})
        
        # Si el departamento es "Secretaría Particular", lo ocultamos inicialmente
        if depto_nombre == 'Secretaría Particular':
            nodo.style['display'] = 'none'  # Esto oculta la sección de Secretaría Particular
        
        children.append(nodo)

    return html.Div([
            html.Div(children, style={
                'display': 'flex',
                'gap': '30px',
                'justifyContent': 'center',
                'flexWrap': 'nowrap',
                'minWidth': 'fit-content'  # permite que crezca horizontalmente
            })
        ], style={
            'overflow': 'auto',                 # permite scroll completo
            #'width': '100vw',                   # usa todo el ancho visible
            'height': 'calc(100vh - 100px)',    # usa casi toda la altura visible
            'padding': '10px',
            'scrollBehavior': 'smooth',
            'boxSizing': 'border-box'
        })
#boton ver vacantes dentro del modal secretaria particular
@app.callback(
    Output('vacantes-secretaria-container', 'children'),
    Output('vacantes-secretaria-container', 'style'),
    Input('btn-ver-vacantes-secretaria', 'n_clicks'),
    State('vacantes-secretaria-container', 'style'),
    prevent_initial_call=True
)
def toggle_vacantes_secretaria(n_clicks, current_style):
    visible = current_style.get('display') == 'block' if current_style else False
    new_display = 'none' if visible else 'block'
    contenido = build_vacantes_component("Secretaría Particular")
    return contenido, {'marginTop': '10px', 'display': new_display}

#callback secretaria particular ver detalles
@app.callback(
    Output({'type': 'detalle-tarjeta', 'index': MATCH}, 'style'),
    Input({'type': 'ver-detalles-btn', 'index': MATCH}, 'n_clicks'),
    State({'type': 'detalle-tarjeta', 'index': MATCH}, 'style'),
    prevent_initial_call=True
)
def toggle_detalles(n_clicks, current_style):
    if not current_style or current_style.get('display') == 'none':
        return {'display': 'block'}  # Mostrar los detalles
    else:
        return {'display': 'none'}   # Ocultar los detalles

@app.callback(
    Output('organigrama-container', 'children'),
    Input('visible-departments', 'data')
)
def update_organigrama(visible_departments):
    df, vacantes_df, contratos_df, contratosvacantes_df = cargar_datos()  # Cargar datos desde Google Sheets
    estructura = build_estructura_departamentos(df)

    global vacantes_por_departamento
    vacantes_por_departamento = agrupar_vacantes(vacantes_df)  # Agrupar vacantes por departamento

    # Agrupar contratos por departamento (si no lo tienes ya)
    contratos_por_departamento = agrupar_contratos(contratos_df)

    # Agrupar contratos vacantes por departamento (definir esta función si no la tienes)
    contratos_vacantes_por_departamento = agrupar_contratos_vacantes(contratosvacantes_df)

    return build_tree_departamentos(
        estructura,
        visible_departments,
        contratos_por_departamento,
        contratos_vacantes_por_departamento
    )

@app.callback(
    Output({'type': 'contenido-expandible', 'index': MATCH}, 'className'),
    Output({'type': 'depto-icono', 'index': MATCH}, 'children'),  # nuevo: actualiza el ícono
    Input({'type': 'depto-toggle', 'index': MATCH}, 'n_clicks'),
    State({'type': 'contenido-expandible', 'index': MATCH}, 'className'),
    prevent_initial_call=True
)
def toggle_contenido(n_clicks, current_class):
    mostrar = 'mostrar' not in (current_class or '')
    nueva_clase = 'contenido-expandible mostrar' if mostrar else 'contenido-expandible'
    nuevo_icono = '➖' if mostrar else '➕'
    return nueva_clase, nuevo_icono

@app.callback(
Output({'type': 'vacantes-box', 'index': MATCH}, 'style'),
Input({'type': 'vacantes-toggle', 'index': MATCH}, 'n_clicks'),
State({'type': 'vacantes-box', 'index': MATCH}, 'style'),
prevent_initial_call=True
)

def toggle_vacantes(n, style):
    if not style:
        style = {'display': 'none'}
    new_display = 'none' if style.get('display') == 'block' else 'block'
    return {'display': new_display, 'marginTop': '10px'}

@app.callback(
    Output({'type': 'personal-box', 'index': MATCH}, 'style'),
    Input({'type': 'personal-toggle', 'index': MATCH}, 'n_clicks'),
    State({'type': 'personal-box', 'index': MATCH}, 'style'),
    prevent_initial_call=True
    
)

def toggle_personal(n_clicks, current_style):
        if current_style and current_style.get('display') == 'none':
            return {'display': 'block'}
        else:
            return {'display': 'none'}
    #contratos
@app.callback(
    Output({'type': 'contratos-box', 'index': MATCH}, 'style'),
    Input({'type': 'contratos-toggle', 'index': MATCH}, 'n_clicks'),
    State({'type': 'contratos-box', 'index': MATCH}, 'style'),
    prevent_initial_call=True
)
def toggle_modalcontratol(n_clicks, current_style):
    if current_style and current_style.get('display') == 'none':
        return {'display': 'block'}
    else:
        return {'display': 'none'}
    
@app.callback(
    Output({'type': 'contratosvacantes-box', 'index': MATCH}, 'style'),
    Input({'type': 'contratosvacantes-toggle', 'index': MATCH}, 'n_clicks'),
    State({'type': 'contratosvacantes-box', 'index': MATCH}, 'style'),
    prevent_initial_call=True
)
def toggle_contratos_vacantes(n_clicks, current_style):
    if current_style and current_style.get('display') == 'none':
        return {'display': 'block', 'marginTop': '10px'}
    else:
        return {'display': 'none'}
    
@app.callback(
    Output('modal-secretaria', 'is_open'),
    [Input('abrir-modal-secretaria', 'n_clicks'), Input('cerrar-modal-secretaria', 'n_clicks')],
    [State('modal-secretaria', 'is_open')]
)
def toggle_modal_secretaria(open_clicks, close_clicks, is_open):
    if open_clicks or close_clicks:
        return not is_open
    return is_open
    
@app.callback(
    Output('modal-secretaria-body', 'children'),
    Input('modal-secretaria', 'is_open')
)
def cargar_tarjetas_secretaria(is_open):
    if not is_open:
        return dash.no_update
    # Filtrar el personal Secretaría Particular
    df_secretaria = df[df['Departamento'].str.lower() == 'secretaría particular']
    if df_secretaria.empty:
        return html.Div("No hay personal asignado a Secretaría Particular.")
    return generar_tarjetas_clickables(df_secretaria)

@app.callback(
    Output('modal-persona', 'is_open'),
    Output('modal-title', 'children'),
    Output('modal-content', 'children'),
    Input({'type': 'persona', 'index': ALL}, 'n_clicks'),
    Input({'type': 'persona-tarjeta', 'index': ALL}, 'n_clicks'),
    Input({'type': 'contrato-tarjeta', 'index': ALL}, 'n_clicks'),  # nuevo
    Input('close-modal', 'n_clicks'),
    State('modal-persona', 'is_open'),
    prevent_initial_call=True
)
def toggle_modal(n_clicks_jefes, n_clicks_personal, n_clicks_contrato, close_click, is_open):
    ctx = dash.callback_context

    if not ctx.triggered:
        raise dash.exceptions.PreventUpdate

    trigger = ctx.triggered_id

    if trigger == 'close-modal':
        return False, "", ""
    
    # Función auxiliar para generar contenido de modal según persona
    def crear_contenido_modal(persona):
        raw_sueldo = str(persona['Sueldo']).strip()
        try:
            sueldo_num = float(raw_sueldo.replace('$', '').replace(',', '').replace(' ', ''))
            sueldo_fmt = f"${sueldo_num:,.2f}"
        except ValueError:
            sueldo_fmt = raw_sueldo if raw_sueldo else "N/A"
        grado = persona.get('Grado Académico', '')
        if pd.isna(grado) or str(grado).strip() == '':
            grado = "N/A"
            
        content = html.Div([
            html.Div([
                html.Img(src=persona['Foto URL'], className='img-modal-zoom'),
            ], className='modal-imagen'),
            html.Div([
                #html.H4(persona['Nombre']),
                html.P([html.Strong("Cargo: "),persona['Cargo']]),
                html.P([html.Strong("Departamento: "), persona['Departamento']]),
                html.P([html.Strong("Lugar de trabajo: "), persona['Unidad física']]),
                html.P([html.Strong("Género: "), persona['Genero']]),
                html.P([html.Strong("Clave de servidor Público: "), persona['Clave del servidor']]),
                html.P([html.Strong("Tipo de servidor Público: "), persona['Tipo de Servidor Público']]),
                html.P([html.Strong("Tipo de plaza: "), persona['Tipo de Plaza']]),
                html.P([html.Strong("Clave ISSEMYM: "), persona['Clave ISSEMYM']]),
                html.P([html.Strong("Nivel-Rango: "), persona['Nivel']]),
                html.P([html.Strong("Fecha de ingreso: "), persona['Fecha de Ingreso']]),
                html.P([html.Strong("Cumpleaños: "), persona['Cumpleaños']]),
                html.P([html.Strong("Sueldo Neto: "), sueldo_fmt]),
                html.P([html.Strong("Referente: "), persona['Referente']]),
            ], className="modal-datos")
        ], className="tarjeta-personal")
        return content
    
    # Función auxiliar para generar contenido de modal según persona contrato
    def crear_contenido_modal_contrato(contrato):
        raw_sueldo = str(contrato.get('Sueldo', '')).strip()
        try:
            sueldo_num = float(raw_sueldo.replace('$', '').replace(',', '').replace(' ', ''))
            sueldo_fmt = f"${sueldo_num:,.2f}"
        except (ValueError, AttributeError):
            sueldo_fmt = raw_sueldo if raw_sueldo else "N/A"

        content = html.Div([
            # Foto con efecto zoom
            html.Div([
                    html.Img(
                        src=contrato.get('Foto URL', 'https://via.placeholder.com/150'),className='img-modal-zoom',
                    )
                    ], className='modal-imagen'),

             # Información del contrato
                html.Div([
                    html.P([
                        html.Strong("No. de Empleado: "),
                        contrato.get('NO DE EMPLEADO', 'N/A')
                    ]),
                    html.P([
                        html.Strong("No. de Contrato: "),
                        contrato.get('NO DE CONTRATO', 'N/A')
                    ]),
                    html.P([
                        html.Strong("Unidad Física: "),
                        contrato.get('Unidad fisica', 'N/A')
                    ]),
                    html.P([
                        html.Strong("Género: "),
                        contrato.get('Genero', 'N/A')
                    ]),
                    html.P([
                        html.Strong("Esquema: "),
                        contrato.get('Esquema', 'N/A')
                    ]),
                    html.P([
                        html.Strong("Nivel: "),
                        contrato.get('Nivel', 'N/A')
                    ]),
                    html.P([
                        html.Strong("Fecha de Ingreso: "),
                        contrato.get('Fecha de Ingreso', 'N/A')
                    ]),
                    html.P([
                        html.Strong("Cumpleaños: "),
                        contrato.get('Cumpleaños', 'N/A')
                    ]),
                    html.P([
                        html.Strong("Cargo: "),
                        contrato.get('Cargo', 'N/A')
                    ]),
                    html.P([
                        html.Strong("Referente: "),
                        contrato.get('Referente', 'N/A')
                    ]),
                    html.P([
                        html.Strong("Sueldo: "),
                        sueldo_fmt
                    ])
                ],className="modal-datos")
        ], className="tarjeta-personal")
        return content
    # Verificar clicks en jefes
    if isinstance(trigger, dict) and trigger.get('type') == 'persona':
        for i, clicks in enumerate(n_clicks_jefes):
            if clicks and clicks > 0:
                persona_nombre = trigger['index']
                persona = df[df['Nombre'] == persona_nombre].iloc[0]
                content = crear_contenido_modal(persona)
                return True, persona['Nombre'], content

    # Verificar clicks en personal
    if isinstance(trigger, dict) and trigger.get('type') == 'persona-tarjeta':
        
        for i, clicks in enumerate(n_clicks_personal):
            if clicks and clicks > 0:
                persona_nombre = trigger['index']
                persona = df[df['Nombre'] == persona_nombre].iloc[0]
                content = crear_contenido_modal(persona)
                return True, persona['Nombre'], content
            
    # Verificar clics en contratos
    if isinstance(trigger, dict) and trigger.get('type') == 'contrato-tarjeta':
        for i, clicks in enumerate(n_clicks_contrato):
            if clicks and clicks > 0:
                persona_nombre = trigger['index']
                contrato = contratos_df[contratos_df['NombreC'] == persona_nombre].iloc[0]
                content = crear_contenido_modal_contrato(contrato)
                return True, contrato['NombreC'], content
            
    raise dash.exceptions.PreventUpdate

if __name__ == "__main__":
    app.run_server(debug=False, host='0.0.0.0', port=8080)
