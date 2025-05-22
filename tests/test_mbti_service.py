import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.psychology.mbti_analysis import MBTIAnalysisService
from app.supabase.supabase_mbti import MBTI


class DummyRepository:
    def __init__(self):
        self.storage = {}

    def get_mbti(self, user_id: str):
        return self.storage.get(user_id, MBTI())

    def upsert_mbti(self, user_id: str, mbti: MBTI):
        self.storage[user_id] = mbti

    def reset_mbti(self, user_id: str):
        self.storage[user_id] = MBTI()


def create_service(monkeypatch):
    monkeypatch.setattr(
        'app.psychology.mbti_analysis.MBTIRepository',
        DummyRepository
    )
    return MBTIAnalysisService('dummy_user')


def test_get_mbti_type(monkeypatch):
    service = create_service(monkeypatch)

    service.mbti.extraversion_introversion = 0.8  # I
    service.mbti.sensing_intuition = 0.2          # S
    service.mbti.thinking_feeling = 0.7           # F
    service.mbti.judging_perceiving = 0.3         # J

    assert service.get_mbti_type() == 'ISFJ'


def test_generate_style_prompt():
    prompt = MBTIAnalysisService.generate_style_prompt('ENTP')
    expected = (
        'Your tone should be '
        'energetic, conversational, and expressive; '
        'imaginative, big-picture, and metaphorical; '
        'logical, direct, and objective; '
        'casual, open-ended, and exploratory.'
    )
    assert prompt == expected
