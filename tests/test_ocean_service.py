import textwrap
import pytest

from app.psychology import ocean_analysis
from app.supabase.supabase_ocean import Ocean


class MockOceanRepository:
    def __init__(self):
        self.ocean = None

    def get_ocean(self, user_id: str):
        return self.ocean

    def upsert_ocean(self, user_id: str, ocean: Ocean):
        self.ocean = ocean


@pytest.fixture(autouse=True)
def patch_repository(monkeypatch):
    monkeypatch.setattr(ocean_analysis, "OceanRepository", MockOceanRepository)
    monkeypatch.setattr(ocean_analysis.OceanAnalysisService, "load_ocean", lambda self: None)


def create_service():
    service = ocean_analysis.OceanAnalysisService(user_id="test")
    service.ocean = Ocean(
        openness=0.8,
        conscientiousness=0.3,
        extraversion=0.9,
        agreeableness=0.4,
        neuroticism=0.2,
    )
    return service


def test_get_trait_description():
    service = create_service()

    openness = service.get_trait_description(service.ocean.openness, "openness")
    assert openness.level == "High"
    assert openness.description == "Curious and open to new experiences"

    conscientiousness = service.get_trait_description(service.ocean.conscientiousness, "conscientiousness")
    assert conscientiousness.level == "Low"
    assert conscientiousness.description == "Flexible and spontaneous"


def test_pretty_print_format():
    service = create_service()
    expected = (
        "\n"
        "        Openness: High (0.8) - Curious and open to new experiences\n"
        "        Conscientiousness: Low (0.3) - Flexible and spontaneous\n"
        "        Extraversion: High (0.9) - Outgoing and sociable\n"
        "        Agreeableness: Low (0.4) - Direct and self-focused\n"
        "        Neuroticism: Low (0.2) - Emotionally stable\n"
        "        "
    )
    assert service.get_pretty_print_ocean_format() == expected
