import streamlit as st
import base64
import pyodbc
import pandas as pd
from datetime import datetime, timedelta
import hashlib

# Configuración de la página
st.set_page_config(page_title="Simulador Riesgos BPE", page_icon=":bar_chart:", layout="wide")

# Estilo del botón
st.markdown("""
    <style>
    div.stButton > button {
        background-color: #003366;
        color: white;
        padding: 10px 20px;
        font-size: 18px;
        font-weight: bold;
        letter-spacing: 1px;
        border-radius: 5px;
        border: none;
        margin-top: 10px;
    }
    div.stButton > button:hover {
        background-color: #45a049;
    }
    </style>
""", unsafe_allow_html=True)



# Título con imagen a la derecha y fondo verde
st.markdown(
    f"""
    <div style='
        background-color: #4CAF50;
        padding: 0px;
        border-radius: 10px;
        font-family: Arial, sans-serif;
        display: flex;
        align-items: center;
        position: relative;
    '>
        <div style='
            flex: 1;
            text-align: center;
        '>
            <h1 style='
                color: white;
                font-size: 50px;
                margin: 0;
            '>
                PAY PLANNER
            </h1>
        </div>
    """,
    unsafe_allow_html=True
)

# Subtítulo en negrita y color azul oscuro
st.markdown("<h2 style='color: #a52a2a; font-weight: bold;margin-bottom: 25px'>Simulador Riesgos BPE</h2>", unsafe_allow_html=True)

# Crear dos columnas para Cod. Cliente y Tipo de solicitud
col1, col2 = st.columns(2)

# Columna 1: Ingreso del número de Cod. Cliente
with col1:
    st.markdown('<p style="font-size: 20px; margin-bottom: -50px; font-weight: bold;">Ingrese Cod Cliente:</p>', unsafe_allow_html=True)
    customer_code = st.text_input("", key="customer_code")

# Columna 2: Selección del tipo de solicitud
with col2:
    st.markdown('<p style="font-size: 20px; margin-bottom: -50px;font-weight: bold;">Tipo de Solución:</p>', unsafe_allow_html=True)
    facility_type = st.selectbox("", ["Reprogramación", "Refinanciamiento"], key="facility_type")


# Botón de búsqueda
search_button = st.button("Buscar")


# Función para conectar a SQL Server y realizar la búsqueda según la solicitud
def search_by_facility_type(customer_code, facility_type):
    conn_str = (
        'DRIVER={ODBC Driver 17 for SQL Server};'
        'SERVER=172.29.74.244;'
        'DATABASE=bpe_cruces;'
        'Trusted_Connection=yes;'
    )
    conn = pyodbc.connect(conn_str)
    cursor = conn.cursor()
    
    # Consulta SQL para obtener la información del cliente y sus créditos
    query = f"""
    SELECT *
    FROM BPE_Cruces.B42162.Simulador_inicial
    WHERE codunicocli = '{customer_code}'
    """
    
    # Ejecutar la consulta y obtener los resultados en un DataFrame
    df = pd.read_sql(query, conn)
    
    cursor.close()
    conn.close()
    
    return df

# Función para buscar en Simulador_FINAL_v1
def search_simulador_final(cod_credito, cuotas, tipo_solicitud):
    conn_str = (
        'DRIVER={ODBC Driver 17 for SQL Server};'
        'SERVER=172.29.74.244;'
        'DATABASE=bpe_cruces;'
        'Trusted_Connection=yes;'
    )
    conn = pyodbc.connect(conn_str)
    
    query = f"""
    SELECT cod_credito, producto, cla_ssff, fecha_pago, montocuota, cuotas,
           {'tasainteres' if tipo_solicitud == 'Reprogramación' else 'tasa_ref'} as tasa,
           {'cuota_rep' if tipo_solicitud == 'Reprogramación' else 'cuota_ref'} as cuota,
           saldo_actual  -- Nuevo campo agregado
    FROM BPE_Cruces.B42162.Simulador_FINAL_v1
    WHERE cod_credito = ? AND cuotas = ?
    """
    
    df = pd.read_sql(query, conn, params=[cod_credito, cuotas])
    
    conn.close()
    
    return df

# Mostrar la tabla de resultados si está en session_state
if 'df' in st.session_state:
    st.markdown("<h3 style='color: #00008b; font-weight: bold;'>Información del Cliente y Créditos:</h3>", unsafe_allow_html=True)
    df = st.session_state.df
    st.dataframe(df)
    st.markdown("<h3 style='color: #00008b; font-weight: bold;'>Seleccione los créditos:</h3>", unsafe_allow_html=True)
    
    # Crear checkboxes para seleccionar los créditos
    selected_credits = st.session_state.selected_credits if 'selected_credits' in st.session_state else {}
    

    
    if 'COD_CREDITO' in df.columns:
        for index, row in df.iterrows():
            credit_id = row['COD_CREDITO']
            is_checked = selected_credits.get(credit_id, False)
            checkbox = st.checkbox(f"Crédito: {credit_id}", value=is_checked, key=f"checkbox_{credit_id}")
            if checkbox:
                selected_credits[credit_id] = True
            else:
                selected_credits.pop(credit_id, None)
        
        # Mostrar la sección de opciones de solución de pago si hay créditos seleccionados
        if selected_credits:
            if facility_type == 'Reprogramación':
                st.markdown("""
                    <h3 style='color: #00008b; font-weight: bold; font-size: 18px;'>Opciones de Reprogramación:</h3>
                    <div style='color: #333333; font-size: 16px;'>
                        <p>A) 4 Meses de Gracia y 6 Cuotas Adicionales</p>
                        <p>B) 3 Meses de Gracia y 4 Cuotas Adicionales</p>
                        <p>C) 2 Meses de Gracia y 3 Cuotas Adicionales</p>
                    </div>
                """, unsafe_allow_html=True)
                
            # Título para la sección
            st.markdown("<h3 style='color: #00008b; font-weight: bold;'>Elige tu mejor Opción:</h3>", unsafe_allow_html=True)

            # Crear tres columnas para COD_CREDITO, Total cuotas y Períodos de Gracia
            col_credito, col_cuotas, col_gracia = st.columns(3)

            # Dentro del bucle que maneja cada crédito seleccionado
            for credit in selected_credits.keys():
                with col_credito:
                    # Mostrar el subtítulo "Crédito" para cada crédito
                    st.write("Crédito")
                    st.write(f"{credit}")
                with col_cuotas:
                    total_cuotas = st.selectbox(
                        f"Total cuotas para Crédito: {credit}", 
                        options=list(range(1, 49)), 
                        key=f"cuotas_{credit}"
                    )
                with col_gracia:
                    grace_periods = st.selectbox(
                        f"Períodos de Gracia para Crédito: {credit}", 
                        options=list(range(1, 7)), 
                        key=f"gracia_{credit}"
                    )


        
        # Botón de búsqueda para todos los créditos seleccionados
        if st.button("Buscar Crédito"):
            results_list = []
            for credit in selected_credits.keys():
                total_cuotas = st.session_state.get(f"cuotas_{credit}", 1)
                grace_periods = st.session_state.get(f"gracia_{credit}", 1)
                
                simulador_results = search_simulador_final(credit, total_cuotas, facility_type)
                
                if not simulador_results.empty:
                    # Calcular los intereses por los días de gracia
                    tasa = simulador_results.iloc[0]['tasa']
                    saldo_actual = simulador_results.iloc[0]['saldo_actual']
                    
                    # Días de gracia en función de la selección del usuario
                    grace_days = {
                        1: 30,
                        2: 60,
                        3: 90,
                        4: 120,
                        5: 150,
                        6: 180
                    }[grace_periods]
                    
                    # Calcular los intereses por los días de gracia
                    intereses_gracia = (saldo_actual * tasa / 360) * grace_days
                    
                    # Dividir los intereses de gracia entre las cuotas
                    cuota = simulador_results.iloc[0]['cuota']
                    cuota_final = cuota + (intereses_gracia / total_cuotas)
                    
                    # Agregar los resultados a una lista
                    result = simulador_results.iloc[0].to_dict()
                    result['Cuota_final'] = cuota_final
                    results_list.append(result)
            
            if results_list:
                final_df = pd.DataFrame(results_list)
                st.write("Resultados del Simulador con Cuota Final:")
                st.dataframe(final_df)
            else:
                st.write("No se encontraron resultados para los créditos seleccionados.")
else:
    # Funcionalidad del botón de búsqueda
    if search_button:
        if customer_code and facility_type:
            # Llamar a la función para buscar en la base de datos SQL Server
            search_results = search_by_facility_type(customer_code, facility_type)
            
            # Mostrar los resultados en una tabla
            if not search_results.empty:
                st.session_state.df = search_results  # Guardar los resultados en session_state
                st.markdown("<h3 style='color: #00008b; font-weight: bold;'>Información del Cliente y Créditos:</h3>", unsafe_allow_html=True)
                st.dataframe(search_results)
                        
                # Verificar si el tipo de solución es 'Reprogramación' y si existen los valores "Dudoso", "Deficiente" o "Perdida" en la columna 'cla_ssff'
                if facility_type == "Reprogramación":
                    alert_values = ["Dudoso", "Deficiente", "Perdida"]
                    if search_results['CLA_SSFF'].isin(alert_values).any():
                        st.session_state.df = search_results  # Guardar los resultados en session_state
                        # Mostrar alerta con símbolo de advertencia ⚠️
                        st.markdown("<p style='color: red; font-size: 20px; font-weight: bold;'>⚠️ Cuidado la Clasificación no es la Correcta!!!</p>", unsafe_allow_html=True)
                    if (search_results['DM_ACTUAL'] > 30).any():
                        # Mostrar alerta con símbolo de advertencia ⚠️
                        st.markdown("<p style='color: red; font-size: 20px; font-weight: bold;'>⚠️ Cuidado los días de morosidad no son los correctos!!!</p>", unsafe_allow_html=True)
                

                # Subtítulo para seleccionar los créditos
                st.markdown("<h3 style='color: #00008b; font-weight: bold;'>Seleccione los créditos:</h3>", unsafe_allow_html=True)
                
                # Crear checkboxes para seleccionar los créditos
                selected_credits = st.session_state.selected_credits if 'selected_credits' in st.session_state else {}
                if 'COD_CREDITO' in search_results.columns:
                    for index, row in search_results.iterrows():
                        credit_id = row['COD_CREDITO']
                        is_checked = selected_credits.get(credit_id, False)
                        checkbox = st.checkbox(f"Crédito: {credit_id}", value=is_checked, key=f"checkbox_{credit_id}")
                        if checkbox:
                            selected_credits[credit_id] = True
                        else:
                            selected_credits.pop(credit_id, None)
                    
                    # Actualizar el estado de sesión
                    st.session_state.selected_credits = selected_credits
            else:
                st.write("No se encontraron resultados para el número de Cod. Cliente proporcionado.")
