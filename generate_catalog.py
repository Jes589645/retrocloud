import os
import json
import hashlib

# --- CONFIGURACIÓN ---
# Ruta local donde tienes las mismas ROMs que subiste a la VM
LOCAL_ROMS_PATH = r"C:\REPOSITORIOS\retrocloud\roms"

# Ruta donde el Frontend espera el JSON
OUTPUT_JSON_PATH = r"frontend\src\assets\games_catalog.json"

# Mapeo simple para mejorar nombres e imagenes (Opcional)
# Si no encuentra imagen, usará un placeholder
GAME_METADATA = {
    "SuperMarioWorld.smc": {
        "name": "Super Mario World", 
        "img": "https://upload.wikimedia.org/wikipedia/en/3/32/Super_Mario_World_Coverart.png"
    },
    "DonkeyKongCountry.sfc": {
        "name": "Donkey Kong Country", 
        "img": "https://upload.wikimedia.org/wikipedia/en/c/c1/Donkey_Kong_Country_SNES_cover.png"
    },
    "Zelda.sfc": {
        "name": "The Legend of Zelda: A Link to the Past",
        "img": "https://upload.wikimedia.org/wikipedia/en/2/21/The_Legend_of_Zelda_A_Link_to_the_Past_SNES_Game_Cover.jpg"
    }
}

def generate_catalog():
    if not os.path.exists(LOCAL_ROMS_PATH):
        print(f"❌ Error: No encuentro la carpeta {LOCAL_ROMS_PATH}")
        return

    games_list = []
    print(f"🔍 Escaneando {LOCAL_ROMS_PATH}...")

    for filename in os.listdir(LOCAL_ROMS_PATH):
        # Filtrar solo archivos de SNES (ajusta según tus extensiones)
        if filename.lower().endswith(('.sfc', '.smc', '.zip')):
            
            # Datos por defecto (si no están en GAME_METADATA)
            display_name = filename.replace("_", " ").replace(".sfc", "").replace(".smc", "")
            cover_img = "https://via.placeholder.com/300x200?text=RetroGame" # Placeholder genérico

            # Si tenemos metadata manual, la usamos
            if filename in GAME_METADATA:
                display_name = GAME_METADATA[filename]["name"]
                cover_img = GAME_METADATA[filename]["img"]

            game_entry = {
                "id": filename, # ESTO ES LO IMPORTANTE: El nombre exacto del archivo
                "name": display_name,
                "img": cover_img
            }
            
            games_list.append(game_entry)
            print(f"  ✅ Agregado: {filename}")

    # Guardar JSON
    os.makedirs(os.path.dirname(OUTPUT_JSON_PATH), exist_ok=True)
    with open(OUTPUT_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(games_list, f, indent=2, ensure_ascii=False)

    print(f"\n💾 Catálogo generado en: {OUTPUT_JSON_PATH}")
    print(f"🕹️  Total juegos: {len(games_list)}")

if __name__ == "__main__":
    generate_catalog()
