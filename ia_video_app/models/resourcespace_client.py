import hashlib
import os
from urllib.parse import quote_plus
import requests


class ResourceSpaceAPI:
    """
    Infraestructura de red: autenticación, firmado SHA256 y ejecución HTTP.
    """

    def __init__(self, base_url: str, user: str, private_key: str):
        self.base_url = base_url
        self.user = user
        self.private_key = private_key

    def _sign_query(self, query_string: str) -> str:
        string_to_hash = f"{self.private_key}{query_string}"
        return hashlib.sha256(string_to_hash.encode("utf-8")).hexdigest()

    def call_function(self, function_name: str, **kwargs):
        query_parts = [
            f"user={quote_plus(str(self.user))}",
            f"function={quote_plus(str(function_name))}",
        ]
        for key, value in kwargs.items():
            query_parts.append(f"{quote_plus(str(key))}={quote_plus(str(value))}")

        query_string = "&".join(query_parts)
        signature = self._sign_query(query_string)
        final_url = f"{self.base_url}?{query_string}&sign={signature}"

        try:
            response = requests.get(final_url, timeout=30)
            if response.status_code == 200:
                return response.json()
            return None
        except Exception:
            return None


class ResourceSpaceRepository:
    """
    Repositorio de negocio para operaciones sobre recursos de video en ResourceSpace.
    """

    def __init__(self, api_connector: ResourceSpaceAPI):
        self.api = api_connector

    def get_all_video_ids(self) -> list:
        data = self.api.call_function("do_search", search="", restypes="3,4")
        if data is None:
            return None
        if isinstance(data, list):
            return [int(resource["ref"]) for resource in data if "ref" in resource]
        return []

    def get_user_collections(self) -> list:
        collections = []
        seen_refs = set()

        data_user = self.api.call_function("get_user_collections")
        if isinstance(data_user, list):
            for col in data_user:
                if isinstance(col, dict) and "ref" in col:
                    ref = int(col["ref"])
                    if ref not in seen_refs:
                        seen_refs.add(ref)
                        collections.append(
                            {
                                "ref": ref,
                                "name": col.get("name", f"Colección {col['ref']}"),
                                "count": int(col.get("count", 0)),
                            }
                        )

        data_public = self.api.call_function(
            "search_public_collections", search="", exclude_themes=0
        )
        if isinstance(data_public, list):
            for col in data_public:
                if isinstance(col, dict) and "ref" in col:
                    ref = int(col["ref"])
                    if ref not in seen_refs:
                        seen_refs.add(ref)
                        collections.append(
                            {
                                "ref": ref,
                                "name": col.get("name", f"Colección {col['ref']}"),
                                "count": None,
                            }
                        )

        collections.sort(key=lambda x: x["name"].lower())
        return collections

    def get_collection_video_ids(self, collection_id: int) -> list:
        data = self.api.call_function(
            "do_search", search=f"!collection{collection_id}", restypes="3,4"
        )
        if data is None:
            return []
        if isinstance(data, list):
            return [int(resource["ref"]) for resource in data if "ref" in resource]
        return []

    def update_resource_description(self, resource_id: int, value: str) -> bool:
        if not str(value).strip():
            raise ValueError("La descripción no puede estar vacía.")

        data = self.api.call_function(
            "update_field",
            resource=int(resource_id),
            field="DESCRIPCION",
            value=str(value),
        )
        return data is True or data == 1 or isinstance(data, dict)

    def get_video_download_url(self, resource_id: int) -> str:
        data = self.api.call_function(
            "get_resource_path", ref=resource_id, geturl=1, size="pre"
        )
        if not isinstance(data, str) or "thm_" in data:
            data = self.api.call_function("get_resource_path", ref=resource_id, geturl=1)
        return data if isinstance(data, str) else ""

    def download_video(self, resource_id: int, dest_folder: str = "temp_videos") -> str:
        url = self.get_video_download_url(resource_id)
        if not url:
            return None

        if not os.path.exists(dest_folder):
            os.makedirs(dest_folder, exist_ok=True)

        ext = "mp4"
        if "ext=" in url:
            try:
                ext = url.split("ext=")[1].split("&")[0].lower()
            except IndexError:
                pass

        if ext in ["jpg", "jpeg", "png"]:
            if "ext=" in url:
                url = url.replace(f"ext={ext}", "ext=mp4")
            ext = "mp4"

        local_path = os.path.join(dest_folder, f"resource_{resource_id}.{ext}")
        try:
            response = requests.get(url, stream=True, timeout=(30, 120))
            if response.status_code == 200:
                with open(local_path, "wb") as f:
                    for chunk in response.iter_content(chunk_size=1024 * 1024):
                        if chunk:
                            f.write(chunk)
                return os.path.abspath(local_path)
            return None
        except Exception:
            return None

    def cleanup_video(self, local_path: str):
        if local_path and os.path.exists(local_path):
            try:
                os.remove(local_path)
            except Exception:
                pass
