import hashlib
import requests
from urllib.parse import quote_plus

# =============================================================================
# 1. EL CONECTOR DE RED (Clase de Bajo Nivel)
# =============================================================================
class ResourceSpaceAPI:
    """
    Se encarga exclusivamente de la infraestructura de red: 
    Autenticación, firmado de URLs y ejecución de peticiones HTTP.
    """
    def __init__(self, base_url: str, user: str, private_key: str):
        self.base_url = base_url
        self.user = user
        self.private_key = private_key

    def _sign_query(self, query_string: str) -> str:
        """Genera la firma SHA256 obligatoria de la API."""
        string_to_hash = f"{self.private_key}{query_string}"
        return hashlib.sha256(string_to_hash.encode('utf-8')).hexdigest()

    def call_function(self, function_name: str, **kwargs) -> list or dict:
        """
        Método genérico para ejecutar CUALQUIER función de ResourceSpace.
        Recibe el nombre de la función y los parámetros que requiera.
        """
        # Construimos los parámetros base obligatorios
        query_parts = [
            f"user={quote_plus(str(self.user))}",
            f"function={quote_plus(str(function_name))}",
        ]
        
        # Añadimos dinámicamente los parámetros extra que nos pasen (param1, search, ref, etc.)
        for key, value in kwargs.items():
            query_parts.append(f"{quote_plus(str(key))}={quote_plus(str(value))}")
        
        # Unimos todo con ampersands (&) para formar la Query String
        query_string = "&".join(query_parts)
        
        # Firmamos la consulta
        signature = self._sign_query(query_string)
        
        # Construimos la URL definitiva
        final_url = f"{self.base_url}?{query_string}&sign={signature}"
        
        try:
            response = requests.get(final_url, timeout=30)
            if response.status_code == 200:
                return response.json()
            else:
                print(f"Error ResourceSpace API ({function_name}): {response.status_code}")
                return None
        except Exception as e:
            print(f"Error de conexión en API ({function_name}): {e}")
            return None


# =============================================================================
# 2. EL REPOSITORIO DE NEGOCIO (Clase de Alto Nivel)
# =============================================================================
class ResourceSpaceRepository:
    """
    Usa el conector de red para ejecutar acciones específicas del negocio.
    """
    def __init__(self, api_connector: ResourceSpaceAPI):
        self.api = api_connector

    def get_all_video_ids(self) -> list:
        """Obtiene la lista total de referencias de videos usando 'do_search'."""
        data = self.api.call_function("do_search", search="", restypes="3,4")
        if data is None:
            return None
        if isinstance(data, list):
            return [resource['ref'] for resource in data if 'ref' in resource]
        return []

    def get_user_collections(self) -> list:
        """Obtiene tanto las colecciones privadas del usuario como las públicas y destacadas (temas)."""
        collections = []
        seen_refs = set()
        
        # 1. Colecciones privadas del usuario
        data_user = self.api.call_function("get_user_collections")
        if isinstance(data_user, list):
            for col in data_user:
                if isinstance(col, dict) and 'ref' in col:
                    ref = int(col['ref'])
                    if ref not in seen_refs:
                        seen_refs.add(ref)
                        collections.append({
                            "ref": ref,
                            "name": col.get('name', f"Colección {col['ref']}"),
                            "count": int(col.get('count', 0))
                        })
                        
        # 2. Colecciones públicas y destacadas (temas)
        data_public = self.api.call_function("search_public_collections", search="", exclude_themes=0)
        if isinstance(data_public, list):
            for col in data_public:
                if isinstance(col, dict) and 'ref' in col:
                    ref = int(col['ref'])
                    if ref not in seen_refs:
                        seen_refs.add(ref)
                        collections.append({
                            "ref": ref,
                            "name": col.get('name', f"Colección {col['ref']}"),
                            "count": None  # No disponible directamente sin realizar búsquedas extras
                        })
                        
        # Ordenamos las colecciones alfabéticamente por su nombre
        collections.sort(key=lambda x: x["name"].lower())
        return collections

    def get_collection_video_ids(self, collection_id: int) -> list:
        """Obtiene los IDs de video que pertenecen a una colección."""
        # Se usa do_search con la sintaxis especial !collection<id> de ResourceSpace
        data = self.api.call_function("do_search", search=f"!collection{collection_id}", restypes="3,4")
        if data is None:
            return []
        if isinstance(data, list):
            return [resource['ref'] for resource in data if 'ref' in resource]
        return []

    def update_resource_description(self, resource_id: int, value: str) -> bool:
        """Actualiza el campo DESCRIPCION mediante la función update_field."""
        if not str(value).strip():
            raise ValueError("La descripción no puede estar vacía.")

        data = self.api.call_function(
            "update_field",
            resource=int(resource_id),
            field="DESCRIPCION",
            value=str(value),
        )
        # ResourceSpace suele devolver true/1; algunas instalaciones devuelven
        # un objeto de confirmación.
        return data is True or data == 1 or isinstance(data, dict)

    def get_video_download_url(self, resource_id: int) -> str:
        """
        Pide el path del recurso. Probamos tres variantes de tamaño comunes 
        en ResourceSpace para archivos de video originales.
        """
        # Variante 1: Intentar obtener el archivo máster original de video
        data = self.api.call_function("get_resource_path", ref=resource_id, geturl=1, size="pre")
        
        # Si no devuelve un string válido, intentamos sin el parámetro size
        if not isinstance(data, str) or "thm_" in data:
            data = self.api.call_function("get_resource_path", ref=resource_id, geturl=1)
            
        return data if isinstance(data, str) else ""

    def download_video(self, resource_id: int, dest_folder: str = "temp") -> str:
        """
        Descarga el archivo desde ResourceSpace. Si detecta que la URL entregada
        apunta a una extensión de imagen (.jpg, .jpeg, .png), intenta forzar el formato de video (.mp4).
        """
        import os
        import requests
        
        url = self.get_video_download_url(resource_id)
        if not url:
            print(f"No se obtuvo URL de descarga para el ID {resource_id}")
            return None
            
        if not os.path.exists(dest_folder):
            os.makedirs(dest_folder)
            
        # Detectamos la extensión real desde la URL
        ext = "mp4"
        if "ext=" in url:
            try:
                ext = url.split("ext=")[1].split("&")[0].lower()
            except IndexError:
                pass
        
        # CORRECCIÓN CLAVE: Si la API te da un JPG de previsualización por defecto,
        # nosotros sabemos que el recurso raíz original es un video, así que forzamos la extensión de video 
        # y cambiamos el parámetro en la URL si es necesario.
        if ext in ["jpg", "jpeg", "png"]:
            print(f"Alerta: La API devolvio una imagen ({ext}). Forzando peticion de video original...")
            if "ext=" in url:
                url = url.replace(f"ext={ext}", "ext=mp4")
            ext = "mp4"

        local_path = os.path.join(dest_folder, f"resource_{resource_id}.{ext}")
        
        try:
            response = requests.get(url, stream=True, timeout=(30, 120))
            if response.status_code == 200:
                with open(local_path, "wb") as f:
                    for chunk in response.iter_content(chunk_size=1024 * 1024): # Chunks de 1MB
                        if chunk:
                            f.write(chunk)
                return os.path.abspath(local_path)
            else:
                print(f"Error descargando ID {resource_id}: HTTP {response.status_code}")
                return None
        except Exception as e:
            print(f"Excepcion descargando ID {resource_id}: {e}")
            return None

    def cleanup_video(self, local_path: str):
        """
        Elimina el archivo de video temporal del disco duro local.
        """
        import os
        if local_path and os.path.exists(local_path):
            try:
                os.remove(local_path)
            except Exception as e:
                print(f"Error al intentar eliminar el archivo {local_path}: {e}")