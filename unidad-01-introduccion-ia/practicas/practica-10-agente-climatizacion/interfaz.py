"""Consulta por acción, tabla, gráficas y CRUD de la práctica 10 con Streamlit."""

import altair as alt
import pandas as pd
import streamlit as st

from agente_climatizacion import ACCIONES, ALUMNO, AgenteClimatizacion
from almacenamiento_atlas import AlmacenamientoAtlas, ErrorAtlas, TAMANO_PAGINA

TODAS = 'Todas las acciones'
REGLAS = {
    ACCIONES[0]: 'Temperatura mayor de 30 °C y humedad mayor de 70 %.',
    ACCIONES[1]: 'Temperatura mayor de 30 °C y humedad menor o igual a 70 %.',
    ACCIONES[2]: 'Temperatura menor de 18 °C.',
    ACCIONES[3]: 'Temperatura entre 18 y 30 °C, incluidos ambos límites.',
}
COLUMNAS = {
    '_id': 'ID', 'fecha': 'Fecha (UTC)', 'temperatura': 'Temperatura (°C)',
    'humedad': 'Humedad (%)', 'accion': 'Acción', 'actualizado_en': 'Actualizado (UTC)',
}


def preparar_tabla(registros):
    """La tabla y las gráficas comparten los mismos registros consultados en Atlas."""
    tabla = pd.DataFrame(registros).reindex(columns=list(COLUMNAS)).rename(columns=COLUMNAS)
    for columna in ('Fecha (UTC)', 'Actualizado (UTC)'):
        tabla[columna] = pd.to_datetime(tabla[columna], format='ISO8601', errors='coerce', utc=True)
    for columna in ('Temperatura (°C)', 'Humedad (%)'):
        valores = pd.to_numeric(tabla[columna], errors='coerce')
        tabla[columna] = valores.mask(valores.isin([float('inf'), float('-inf')]))
    return tabla


def crear_grafica(tabla, variable, color):
    """Una línea con puntos permite visualizar también una consulta de un solo registro."""
    datos = tabla.dropna(subset=['Fecha (UTC)', variable]).sort_values(['Fecha (UTC)', 'ID'])
    datos['Fecha de registro UTC'] = datos['Fecha (UTC)'].dt.strftime('%Y-%m-%d %H:%M:%S')
    escala = alt.Scale(domain=[0, 100]) if variable == 'Humedad (%)' else alt.Scale(zero=False)
    return alt.Chart(datos).mark_line(point=True, color=color).encode(
        x=alt.X('Fecha (UTC):T', title='Fecha de registro (UTC)',
                scale=alt.Scale(type='utc'), axis=alt.Axis(format='%d/%m %H:%M')),
        y=alt.Y(f'{variable}:Q', scale=escala),
        tooltip=[alt.Tooltip('ID:N'), alt.Tooltip('Fecha de registro UTC:N'),
                 alt.Tooltip(f'{variable}:Q'), alt.Tooltip('Acción:N')],
    ).properties(height=270)


def iniciar_estado():
    valores = {'pagina': 0, 'consulta_accion': None, 'listado': None,
               'consultar': True, 'revision': 0, 'error_consulta': '', 'aviso': '', 'destino': ''}
    for clave, valor in valores.items():
        if clave not in st.session_state:
            st.session_state[clave] = valor


def solicitar_consulta(pagina=0):
    st.session_state.pagina = pagina
    st.session_state.consultar = True


def consultar_registros(almacenamiento, accion):
    estado = st.session_state
    estado.consultar = False
    estado.listado = None
    estado.error_consulta = ''
    estado.revision += 1  # Una selección nunca se reutiliza en otra página o filtro.
    try:
        with st.spinner('Consultando registros en Atlas…'):
            listado = almacenamiento.listar(estado.pagina, accion)
            if not listado['registros'] and estado.pagina > 0:
                listado = almacenamiento.listar(estado.pagina - 1, accion)
        estado.listado = listado
        estado.pagina = listado['pagina']
        estado.destino = f'Base: {almacenamiento.base} · Colección: {almacenamiento.coleccion}'
    except ErrorAtlas as error:
        estado.error_consulta = str(error)


def confirmar_escritura(mensaje, accion=None, nuevo=False):
    """Separar una escritura confirmada de la consulta posterior, que puede fallar."""
    estado = st.session_state
    if accion and estado.consulta_accion not in (TODAS, accion):
        mensaje += f' Para verlo, selecciona «{accion}» o «{TODAS}» en el filtro.'
    estado.aviso = mensaje
    solicitar_consulta(0 if nuevo else estado.pagina)
    st.rerun()


def informar_fallo_escritura(error):
    # No repetir un envío incierto; exigir una consulta antes de otra escritura.
    st.session_state.listado = None
    st.session_state.error_consulta = str(error) + ' Pulsa Actualizar registros para revisar el resultado.'
    st.session_state.aviso = ''
    st.rerun()


def formulario_lectura(almacenamiento, registro=None):
    identificador = registro['_id'] if registro else None
    prefijo = f'lectura_{identificador or "nueva"}_{st.session_state.revision}'
    with st.form(prefijo):
        temperatura = st.text_input('Temperatura (°C)',
                                    value=str(registro['temperatura']) if registro else '',
                                    key=f'{prefijo}_temperatura')
        humedad = st.text_input('Humedad (%)', value=str(registro['humedad']) if registro else '',
                               key=f'{prefijo}_humedad')
        st.caption('Admite punto o coma decimal. Humedad: de 0 a 100 %.')
        enviado = st.form_submit_button('Guardar cambios' if registro else 'Crear registro', type='primary')
    if not enviado:
        return
    agente = AgenteClimatizacion()
    try:
        agente.percibir(temperatura, humedad)
        with st.spinner('Guardando la decisión del agente…'):
            resultado = agente.ejecutar(almacenamiento, identificador)
    except ValueError as error:
        st.error(str(error))
        return
    except ErrorAtlas as error:
        informar_fallo_escritura(error)
        return
    operacion = 'Cambios guardados' if registro else 'Registro creado'
    confirmar_escritura(f'{operacion} y confirmados por Atlas. ID: {resultado["_id"]}. '
                        f'Acción: {agente.accion}.', agente.accion, nuevo=registro is None)


def mostrar_crud(almacenamiento):
    with st.sidebar:
        st.header('Gestionar registros')
        st.caption('El agente decide la acción al crear o editar una lectura.')
        modo = st.radio('Operación', ['Crear', 'Editar', 'Eliminar'], key='operacion')
        listado = st.session_state.listado
        if listado is None:
            st.info('Actualiza los registros para habilitar el CRUD.')
            return
        if modo == 'Crear':
            formulario_lectura(almacenamiento)
            return
        registros = {d['_id']: d for d in listado['registros']}
        if not registros:
            st.info('No hay registros en esta consulta. Selecciona otra acción o crea una lectura.')
            return
        st.caption('Selecciona un registro de la página visible.')
        identificador = st.selectbox(
            'Registro', list(registros), index=None, placeholder='Selecciona un registro',
            format_func=lambda clave: f'{registros[clave]["temperatura"]} °C · '
                                     f'{registros[clave]["humedad"]} % · {clave[-8:]}',
            key=f'registro_{st.session_state.revision}_{modo}',
        )
        if identificador is None:
            return
        registro = registros[identificador]
        st.caption(f'ID: {identificador}')
        st.write(f'Acción guardada: {registro["accion"]}')
        if modo == 'Editar':
            formulario_lectura(almacenamiento, registro)
            return
        with st.form(f'eliminar_{identificador}_{st.session_state.revision}'):
            st.warning('Se eliminará este registro del clúster del profesor.')
            confirmado = st.checkbox('Confirmo eliminar el registro seleccionado')
            enviado = st.form_submit_button('Eliminar registro')
        if enviado:
            if not confirmado:
                st.error('Marca la confirmación para eliminar este registro.')
                return
            try:
                with st.spinner('Eliminando el registro…'):
                    almacenamiento.eliminar(identificador)
            except ErrorAtlas as error:
                informar_fallo_escritura(error)
                return
            confirmar_escritura(f'Eliminación confirmada por Atlas. ID: {identificador}.')


def mostrar_registros_y_graficas():
    estado = st.session_state
    st.subheader('Registros de la acción seleccionada')
    if estado.listado is None:
        st.info('No hay una consulta vigente para mostrar. Pulsa Actualizar registros.')
        st.subheader('Gráficas de estos registros')
        st.info('Las gráficas estarán disponibles cuando se complete la consulta.')
        return
    listado = estado.listado
    registros = listado['registros']
    st.caption(f'Página {estado.pagina + 1} · {len(registros)} registros · '
               f'Hasta {TAMANO_PAGINA} por página, del más reciente al más antiguo.')
    tabla = preparar_tabla(registros)
    if registros:
        st.dataframe(tabla, hide_index=True, width='stretch', height=330,
                     column_config={
                         'ID': st.column_config.TextColumn('ID', width='medium'),
                         'Acción': st.column_config.TextColumn('Acción', width='large'),
                         'Fecha (UTC)': st.column_config.DatetimeColumn(format='YYYY-MM-DD HH:mm:ss'),
                         'Actualizado (UTC)': st.column_config.DatetimeColumn(format='YYYY-MM-DD HH:mm:ss'),
                     })
    else:
        st.info('No hay registros para esta acción. Puedes elegir otra o crear una lectura.')
    anterior, siguiente, _ = st.columns([1, 1, 4])
    anterior.button('Anterior', disabled=estado.pagina == 0,
                    on_click=solicitar_consulta, args=(estado.pagina - 1,))
    siguiente.button('Siguiente', disabled=not listado['hay_siguiente'],
                     on_click=solicitar_consulta, args=(estado.pagina + 1,))
    st.divider()
    st.subheader('Gráficas de estos registros')
    st.caption('Se usan exactamente los registros de la tabla de esta página. '
               'Las fechas se ordenan de la más antigua a la más reciente y se muestran en UTC.')
    if not registros:
        st.info('Sin datos para graficar con esta acción.')
        return
    metricas = st.columns(3)
    metricas[0].metric('Registros en esta página', len(tabla))
    for columna, variable in zip(metricas[1:], ['Temperatura (°C)', 'Humedad (%)']):
        promedio = tabla[variable].mean()
        columna.metric(f'Promedio · {variable}', 'Sin dato' if pd.isna(promedio) else f'{promedio:.1f}')
    for columna, variable, color in zip(st.columns(2), ['Temperatura (°C)', 'Humedad (%)'],
                                        ['#c85b32', '#167d98']):
        with columna:
            st.markdown(f'**{variable}**')
            validos = tabla[['Fecha (UTC)', variable]].notna().all(axis=1)
            if not validos.any():
                st.info('No hay fechas y valores válidos para esta gráfica.')
                continue
            if not validos.all():
                st.caption(f'Se omiten {int((~validos).sum())} registros con fecha o valor inválido.')
            st.altair_chart(crear_grafica(tabla, variable, color), width='stretch')


def iniciar():
    st.set_page_config(page_title='Práctica 10 · Climatización', page_icon='🌡️', layout='wide')
    iniciar_estado()
    estado = st.session_state
    st.caption(f'PRÁCTICA 10 · FUNDAMENTOS DE IA · {ALUMNO}')
    st.title('Agente de climatización')
    st.write('Elige una acción para consultar sus lecturas y observar cómo cambian la temperatura y la humedad.')
    accion_elegida = st.selectbox('¿Qué acción quieres consultar?', [TODAS, *ACCIONES], key='filtro_accion')
    if accion_elegida != estado.consulta_accion:
        estado.consulta_accion = accion_elegida
        estado.aviso = ''
        solicitar_consulta()
    if accion_elegida in REGLAS:
        st.info(REGLAS[accion_elegida])
    else:
        st.caption('Se consultan todas las acciones de tus registros de la práctica 10.')
    st.button('Actualizar registros', on_click=solicitar_consulta, args=(estado.pagina,))
    almacenamiento = AlmacenamientoAtlas()
    try:
        if estado.consultar:
            consultar_registros(almacenamiento, None if accion_elegida == TODAS else accion_elegida)
        if estado.destino:
            st.caption(estado.destino)
        if estado.aviso:
            st.success(estado.aviso)
        if estado.error_consulta:
            st.error(estado.error_consulta)
        mostrar_crud(almacenamiento)
        mostrar_registros_y_graficas()
    finally:
        almacenamiento.cerrar()
