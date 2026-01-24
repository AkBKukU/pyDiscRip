import json
import tempfile
import unittest
from pathlib import Path

import discrip


class TestRipListRead(unittest.TestCase):
    def test_csv_without_media_type_header(self):
        csv_text = "Drive,Name,Description\n/dev/sr0,StAnger,Metallica - St. Anger\n"
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "samples.csv"
            p.write_text(csv_text, encoding="utf-8")

            rows = discrip.rip_list_read(str(p))
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["drive"], "/dev/sr0")
            self.assertEqual(rows[0]["name"], "StAnger")
            self.assertEqual(rows[0]["description"], "Metallica - St. Anger")
            self.assertNotIn("media_type", rows[0])

    def test_csv_with_media_type_blank_defaults_to_auto(self):
        csv_text = "drive,name,description,media_type\n/dev/sr0,StAnger,Metallica - St. Anger,\n"
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "samples.csv"
            p.write_text(csv_text, encoding="utf-8")

            rows = discrip.rip_list_read(str(p))
            self.assertEqual(rows[0]["media_type"], "AUTO")

    def test_csv_with_media_type_is_uppercased(self):
        csv_text = "media_type,drive,name,description\nfloppy,a,doomsharev1.1_1-2,Doom Shareware v1.1 Disk 1 of 2\n"
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "samples.csv"
            p.write_text(csv_text, encoding="utf-8")

            rows = discrip.rip_list_read(str(p))
            self.assertEqual(rows[0]["media_type"], "FLOPPY")
            self.assertEqual(rows[0]["drive"], "a")

    def test_csv_missing_required_headers_raises(self):
        csv_text = "drive,name\n/dev/sr0,StAnger\n"
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "samples.csv"
            p.write_text(csv_text, encoding="utf-8")

            with self.assertRaises(ValueError):
                discrip.rip_list_read(str(p))


class TestConfigRead(unittest.TestCase):
    def test_config_read_ok(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "cfg.json"
            p.write_text(json.dumps({"a": 1, "b": {"c": 2}}), encoding="utf-8")

            cfg = discrip.config_read(str(p))
            self.assertEqual(cfg["a"], 1)
            self.assertEqual(cfg["b"]["c"], 2)

    def test_config_read_bad_json_exits(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "cfg.json"
            p.write_text("{not: valid json", encoding="utf-8")

            with self.assertRaises(SystemExit):
                discrip.config_read(str(p))

    def test_config_read_missing_file_exits(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "does_not_exist.json"
            with self.assertRaises(SystemExit):
                discrip.config_read(str(p))


if __name__ == "__main__":
    unittest.main()
