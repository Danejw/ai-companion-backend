import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import pytest
from app.utils.similarity import cosine_similarity


def test_identical_vectors():
    vec = [1.0, 2.0, 3.0]
    assert cosine_similarity(vec, vec) == pytest.approx(1.0)


def test_opposite_vectors():
    vec1 = [1, 0, 0]
    vec2 = [-1, 0, 0]
    assert cosine_similarity(vec1, vec2) == pytest.approx(-1.0)


def test_vectors_with_zeros():
    vec1 = [0, 1, 0]
    vec2 = [0, 1, 0]
    assert cosine_similarity(vec1, vec2) == pytest.approx(1.0)
