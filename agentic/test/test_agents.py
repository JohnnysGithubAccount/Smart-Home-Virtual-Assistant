import unittest
from unittest.mock import patch
from io import StringIO
import agents

class TestLightingAgent(unittest.TestCase):
    def test_dim(self):
        with patch('sys.stdout', new=StringIO()) as output:
            agents.lighting_agent(dim=30)
            self.assertIn("Dimming lights to 30%", output.getvalue())

    def test_color(self):
        with patch('sys.stdout', new=StringIO()) as output:
            agents.lighting_agent(color='warm')
            self.assertIn("Setting lights to warm", output.getvalue())

    def test_off(self):
        with patch('sys.stdout', new=StringIO()) as output:
            agents.lighting_agent(off=True)
            self.assertIn("Turning off all lights", output.getvalue())

class TestClimateAgent(unittest.TestCase):
    def test_set_temperature(self):
        with patch('sys.stdout', new=StringIO()) as output:
            agents.climate_agent(set_temp=24)
            self.assertIn("Setting temperature to 24°C", output.getvalue())

class TestSecurityAgent(unittest.TestCase):
    def test_lock_doors(self):
        with patch('sys.stdout', new=StringIO()) as output:
            agents.security_agent(lock_doors=True)
            self.assertIn("Locking all doors", output.getvalue())

class TestMediaAgent(unittest.TestCase):
    def test_play_media(self):
        with patch('sys.stdout', new=StringIO()) as output:
            agents.media_agent(play="Jazz Playlist")
            self.assertIn("Playing: Jazz Playlist", output.getvalue())

if __name__ == "__main__":
    unittest.main()
