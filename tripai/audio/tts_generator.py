import pyttsx3
import os
from typing import Dict, Any, List
from config.settings import settings

class TTSGenerator:
    def __init__(self, voice_type: str = "female"):
        self.engine = pyttsx3.init()
        self.set_voice(voice_type)
    
    def set_voice(self, voice_type: str):
        voices = self.engine.getProperty('voices')
        
        if voice_type == "female":
            for voice in voices:
                if "female" in voice.name.lower() or "女" in voice.name:
                    self.engine.setProperty('voice', voice.id)
                    break
        else:
            for voice in voices:
                if "male" in voice.name.lower() or "男" in voice.name:
                    self.engine.setProperty('voice', voice.id)
                    break
    
    def set_rate(self, rate: int = 150):
        self.engine.setProperty('rate', rate)
    
    def set_volume(self, volume: float = 1.0):
        self.engine.setProperty('volume', volume)
    
    def generate_audio(self, text: str, output_path: str) -> str:
        self.engine.save_to_file(text, output_path)
        self.engine.runAndWait()
        return output_path
    
    def generate_attraction_audio(self, itinerary: Dict[str, Any], voice_type: str = "female") -> List[str]:
        self.set_voice(voice_type)
        
        audio_files = []
        os.makedirs(settings.OUTPUT_DIR, exist_ok=True)
        
        for day in itinerary['daily_itinerary']:
            morning_text = f"第{day['day']}天上午，我们将前往{day['morning']['attraction']}。{day['morning']['description']}"
            morning_audio_path = os.path.join(settings.OUTPUT_DIR, f"day{day['day']}_morning.mp3")
            self.generate_audio(morning_text, morning_audio_path)
            audio_files.append({
                "day": day['day'],
                "period": "上午",
                "attraction": day['morning']['attraction'],
                "path": morning_audio_path
            })
            
            afternoon_text = f"第{day['day']}天下午，我们将前往{day['afternoon']['attraction']}。{day['afternoon']['description']}"
            afternoon_audio_path = os.path.join(settings.OUTPUT_DIR, f"day{day['day']}_afternoon.mp3")
            self.generate_audio(afternoon_text, afternoon_audio_path)
            audio_files.append({
                "day": day['day'],
                "period": "下午",
                "attraction": day['afternoon']['attraction'],
                "path": afternoon_audio_path
            })
        
        return audio_files
    
    def stop(self):
        self.engine.stop()