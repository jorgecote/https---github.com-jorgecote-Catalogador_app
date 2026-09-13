import sys
import unittest
from pathlib import Path


APP_DIR = Path(__file__).resolve().parent / "mi_proyecto_streamlit"
sys.path.insert(0, str(APP_DIR))

from models.catalogation_result import build_video_result, chronological_description
from models.resourcespace_client import ResourceSpaceRepository


class CatalogationResultTests(unittest.TestCase):
    def test_builds_chronological_description_in_input_order(self):
        frames = [
            {"timestamp": "00:05", "synthesis": "Una calle."},
            {"timestamp": "00:15", "synthesis": "Una persona camina."},
        ]
        self.assertEqual(
            chronological_description(frames),
            "[00:05] Una calle.\n[00:15] Una persona camina.",
        )

    def test_result_contract_keeps_video_and_frames(self):
        frames = [{"timestamp": "00:00", "synthesis": "Una escena."}]
        result = build_video_result(42, frames)
        self.assertEqual(result["video_id"], 42)
        self.assertEqual(result["status"], "completed")
        self.assertEqual(result["frames"], frames)

    def test_update_resource_description_uses_expected_api_call(self):
        class FakeAPI:
            def __init__(self):
                self.call = None

            def call_function(self, name, **kwargs):
                self.call = (name, kwargs)
                return True

        api = FakeAPI()
        repository = ResourceSpaceRepository(api)
        updated = repository.update_resource_description(42, "Descripción revisada")

        self.assertTrue(updated)
        self.assertEqual(
            api.call,
            (
                "update_field",
                {
                    "resource": 42,
                    "field": "DESCRIPCION",
                    "value": "Descripción revisada",
                },
            ),
        )


if __name__ == "__main__":
    unittest.main()
