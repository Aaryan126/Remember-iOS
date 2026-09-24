import importlib.util
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location("deployment", Path(__file__).with_name("deploy.py"))
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class InventoryTests(unittest.TestCase):
    def entry(self, path="Library/file", size=4, directory=False, link=False):
        return {"relativePath": path, "metadata": {"size": size},
                "resources": {"isDirectory": directory, "isSymbolicLink": link}}

    def test_files_only(self):
        self.assertEqual(module.file_inventory([self.entry(directory=True), self.entry("Library/file2")]), {"Library/file2": 4})

    def test_rejects_unsafe_paths_and_links(self):
        for entry in [self.entry("/tmp/file"), self.entry("../file"), self.entry(link=True)]:
            with self.assertRaises(ValueError): module.file_inventory([entry])

    def test_rejects_duplicate_and_invalid_sizes(self):
        for entries in [[self.entry(), self.entry()], [self.entry(size=-1)], [self.entry(size=True)]]:
            with self.assertRaises(ValueError): module.file_inventory(entries)


if __name__ == "__main__": unittest.main()
