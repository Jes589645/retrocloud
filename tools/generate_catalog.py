import os
import json
from pathlib import Path

# ⚠️ Ajusta esta ruta a donde tengas las ROMs SNES en tu PC
ROMS_DIR = Path(r"C:\REPOSITORIOS\retrocloud\roms\snes")

# Dónde se guardará el catálogo dentro del backend
OUTPUT_PATH = Path("backend/app/games_catalog.json")

# Extensiones válidas de ROMs
VALID_EXTENSIONS = {".smc", ".sfc", ".zip", ".7z"}  # añade/quita si usas otras


def clean_name(filename: str) -> str:
    """
    Limpia el nombre de la ROM para que se vea bonito en el frontend.
    """
    name, _ = os.path.splitext(filename)
    name = name.replace("_", " ").replace(".", " ")
    name = " ".join(name.split())
    return name.strip()


def main():
    if not ROMS_DIR.exists():
        raise SystemExit(f"La ruta de ROMs no existe: {ROMS_DIR}")

    games = []
    game_id = 1

    for entry in sorted(ROMS_DIR.iterdir()):
        if not entry.is_file():
            continue
        if entry.suffix.lower() not in VALID_EXTENSIONS:
            continue

        games.append(
            {
                "id": game_id,
                "name": clean_name(entry.name),
                "console": "SNES",
                "filename": entry.name,
            }
        )
        game_id += 1

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT_PATH.open("w", encoding="utf-8") as f:
        json.dump(games, f, ensure_ascii=False, indent=2)

    print(f"Se generó catálogo con {len(games)} juegos en {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
