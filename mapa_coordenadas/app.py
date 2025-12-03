

from flask import Flask, render_template, request, jsonify
import pandas as pd
import folium
from folium import plugins
import os

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload():
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': 'No se envió ningún archivo'})
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({'success': False, 'error': 'No se seleccionó ningún archivo'})
        
        # Leer Excel
        df = pd.read_excel(file)
        
        # Verificar columnas
        if 'Descripcion' not in df.columns or 'Coordenadas' not in df.columns:
            return jsonify({'success': False, 'error': 'El archivo debe tener columnas "Descripcion" y "Coordenadas"'})
        
        # Procesar coordenadas
        locations = []
        for idx, row in df.iterrows():
            try:
                coords = str(row['Coordenadas']).strip()
                parts = coords.split(',')
                if len(parts) == 2:
                    lat = float(parts[0].strip())
                    lon = float(parts[1].strip())
                    locations.append({
                        'desc': str(row['Descripcion']),
                        'lat': lat,
                        'lon': lon
                    })
            except:
                continue
        
        if not locations:
            return jsonify({'success': False, 'error': 'No se encontraron coordenadas válidas'})
        
        # Calcular centro
        center_lat = sum(loc['lat'] for loc in locations) / len(locations)
        center_lon = sum(loc['lon'] for loc in locations) / len(locations)
        
        # Crear mapa con múltiples capas
        m = folium.Map(
            location=[center_lat, center_lon],
            zoom_start=15,
            tiles='OpenStreetMap'
        )
        
        # Agregar capas de mapa
        folium.TileLayer(
            tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
            attr='Esri',
            name='🛰️ Satélite',
            overlay=False,
            control=True
        ).add_to(m)
        
        folium.TileLayer(
            tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Topo_Map/MapServer/tile/{z}/{y}/{x}',
            attr='Esri',
            name='⛰️ Relieve',
            overlay=False,
            control=True
        ).add_to(m)
        
        folium.TileLayer(
            'OpenStreetMap',
            name='🗺️ Calles',
            overlay=False,
            control=True
        ).add_to(m)
        
        folium.TileLayer(
            tiles='https://{s}.tile.openstreetmap.fr/hot/{z}/{x}/{y}.png',
            attr='OpenStreetMap',
            name='🚌 Transporte',
            overlay=False,
            control=True
        ).add_to(m)
        
        # Añadir marcadores con colores diferentes
        colores = ['red', 'blue', 'green', 'purple', 'orange', 'darkred', 'lightred', 'beige', 'darkblue', 'darkgreen']
        
        for idx, loc in enumerate(locations):
            color = colores[idx % len(colores)]
            
            folium.Marker(
                [loc['lat'], loc['lon']],
                popup=folium.Popup(f"""
                    <div style='width:200px'>
                        <h4 style='color:#667eea;margin:0'>{loc['desc']}</h4>
                        <hr style='margin:5px 0'>
                        <b>📍 Coordenadas:</b><br>
                        Lat: {loc['lat']:.6f}<br>
                        Lon: {loc['lon']:.6f}
                    </div>
                """, max_width=300),
                tooltip=loc['desc'],
                icon=folium.Icon(color=color, icon='home', prefix='fa')
            ).add_to(m)
        
        # Añadir líneas conectando los puntos
        if len(locations) > 1:
            coordinates = [[loc['lat'], loc['lon']] for loc in locations]
            folium.PolyLine(
                coordinates,
                color='#667eea',
                weight=2,
                opacity=0.7,
                popup='Ruta entre ubicaciones'
            ).add_to(m)
        
        # Añadir controles
        folium.LayerControl(position='topright').add_to(m)
        
        plugins.MeasureControl(
            position='topleft',
            primary_length_unit='meters',
            secondary_length_unit='kilometers',
            primary_area_unit='sqmeters'
        ).add_to(m)
        
        plugins.Fullscreen(
            position='topright',
            title='Pantalla completa',
            title_cancel='Salir de pantalla completa'
        ).add_to(m)
        
        minimap = plugins.MiniMap(toggle_display=True)
        m.add_child(minimap)
        
        plugins.LocateControl(auto_start=False).add_to(m)
        
        # Convertir mapa a HTML
        map_html = m._repr_html_()
        
        return jsonify({
            'success': True,
            'map': map_html,
            'locations': locations,
            'total': len(locations)
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

if __name__ == '__main__':
    if not os.path.exists('templates'):
        os.makedirs('templates')
    
    print("\n" + "="*60)
    print("🚀 SERVIDOR INICIADO CORRECTAMENTE")
    print("="*60)
    print("📍 URL: http://localhost:5000")
    print("📁 Carpeta: templates/")
    print("⏹️  Detener: Ctrl+C")
    print("="*60 + "\n")
    
    app.run(debug=True, host='0.0.0.0', port=5000)