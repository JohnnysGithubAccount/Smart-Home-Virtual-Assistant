import unittest
from unittest.mock import patch
import planner

class TestPlanner(unittest.TestCase):
    @patch('subprocess.run')
    def test_query_llama(self, mock_run):
        mock_run.return_value.stdout = (
            "lighting_agent(dim=20)\n"
            "climate_agent(set_temp=24)\n"
            "security_agent(lock_doors=True)"
        )
        result = planner.query_llama("Prepare for sleep")
        self.assertIn("lighting_agent", result)
        self.assertIn("climate_agent", result)
        self.assertIn("security_agent", result)

if __name__ == "__main__":
    unittest.main()
