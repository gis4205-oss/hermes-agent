"""Tests for hermes_cli/tips.py random startup tips."""

from pathlib import Path

import hermes_cli.tips as tips_module
from hermes_cli.tips import BUILTIN_TIPS, TIPS, get_random_tip, get_tip_corpus


class TestBuiltinTipsCorpus:
    """Validate the bundled fallback corpus."""

    def test_has_at_least_200_tips(self):
        assert len(BUILTIN_TIPS) >= 200, f"Expected 200+ tips, got {len(BUILTIN_TIPS)}"

    def test_no_duplicates(self):
        assert len(BUILTIN_TIPS) == len(set(BUILTIN_TIPS)), "Duplicate tips found"

    def test_all_tips_are_strings(self):
        for i, tip in enumerate(BUILTIN_TIPS):
            assert isinstance(tip, str), f"Tip {i} is not a string: {type(tip)}"

    def test_no_empty_tips(self):
        for i, tip in enumerate(BUILTIN_TIPS):
            assert tip.strip(), f"Tip {i} is empty or whitespace-only"

    def test_max_length_reasonable(self):
        for i, tip in enumerate(BUILTIN_TIPS):
            assert len(tip) <= 180, f"Tip {i} too long ({len(tip)} chars): {tip[:60]}..."

    def test_no_leading_trailing_whitespace(self):
        for i, tip in enumerate(BUILTIN_TIPS):
            assert tip == tip.strip(), f"Tip {i} has leading/trailing whitespace"

    def test_legacy_tips_alias_points_to_builtin_corpus(self):
        assert TIPS is BUILTIN_TIPS


class TestUserLocalOverrides:
    def test_defaults_to_builtin_corpus_without_override(self, monkeypatch, tmp_path):
        home = tmp_path / '.hermes'
        home.mkdir()
        monkeypatch.setenv('HERMES_HOME', str(home))

        assert get_tip_corpus() == BUILTIN_TIPS

    def test_loads_python_override(self, monkeypatch, tmp_path):
        home = tmp_path / '.hermes'
        home.mkdir()
        (home / 'tips.py').write_text("TIPS = ['첫 번째 팁', '두 번째 팁']\n", encoding='utf-8')
        monkeypatch.setenv('HERMES_HOME', str(home))

        assert get_tip_corpus() == ['첫 번째 팁', '두 번째 팁']
        assert get_random_tip() in {'첫 번째 팁', '두 번째 팁'}

    def test_loads_python_get_tips_override(self, monkeypatch, tmp_path):
        home = tmp_path / '.hermes'
        home.mkdir()
        (home / 'tips.py').write_text(
            "def get_tips():\n    return ['함수 팁 1', '함수 팁 2']\n",
            encoding='utf-8',
        )
        monkeypatch.setenv('HERMES_HOME', str(home))

        assert get_tip_corpus() == ['함수 팁 1', '함수 팁 2']

    def test_python_override_wins_over_text_override(self, monkeypatch, tmp_path):
        home = tmp_path / '.hermes'
        home.mkdir()
        (home / 'tips.py').write_text("TIPS = ['python override']\n", encoding='utf-8')
        (home / 'tips.txt').write_text("text override\n", encoding='utf-8')
        monkeypatch.setenv('HERMES_HOME', str(home))

        assert get_tip_corpus() == ['python override']

    def test_loads_text_override(self, monkeypatch, tmp_path):
        home = tmp_path / '.hermes'
        home.mkdir()
        (home / 'tips.txt').write_text(
            "# comment\n\n텍스트 팁 1\n 텍스트 팁 2 \n",
            encoding='utf-8',
        )
        monkeypatch.setenv('HERMES_HOME', str(home))

        assert get_tip_corpus() == ['텍스트 팁 1', '텍스트 팁 2']

    def test_invalid_or_empty_override_falls_back_to_builtin(self, monkeypatch, tmp_path):
        home = tmp_path / '.hermes'
        home.mkdir()
        (home / 'tips.py').write_text('TIPS = []\n', encoding='utf-8')
        monkeypatch.setenv('HERMES_HOME', str(home))

        assert get_tip_corpus() == BUILTIN_TIPS


class TestGetRandomTip:
    def test_returns_string(self, monkeypatch, tmp_path):
        home = tmp_path / '.hermes'
        home.mkdir()
        monkeypatch.setenv('HERMES_HOME', str(home))

        tip = get_random_tip()
        assert isinstance(tip, str)
        assert len(tip) > 0

    def test_returns_tip_from_active_corpus(self, monkeypatch, tmp_path):
        home = tmp_path / '.hermes'
        home.mkdir()
        (home / 'tips.py').write_text("TIPS = ['override one', 'override two']\n", encoding='utf-8')
        monkeypatch.setenv('HERMES_HOME', str(home))

        tip = get_random_tip()
        assert tip in get_tip_corpus()

    def test_randomness(self, monkeypatch, tmp_path):
        home = tmp_path / '.hermes'
        home.mkdir()
        monkeypatch.setenv('HERMES_HOME', str(home))

        seen = set()
        for _ in range(50):
            seen.add(get_random_tip())
        assert len(seen) >= 10, f"Only got {len(seen)} unique tips in 50 draws"


class TestTipIntegrationInCLI:
    def test_tip_import_works(self):
        assert callable(tips_module.get_random_tip)
        assert callable(tips_module.get_tip_corpus)

    def test_tip_display_format(self, monkeypatch, tmp_path):
        home = tmp_path / '.hermes'
        home.mkdir()
        monkeypatch.setenv('HERMES_HOME', str(home))

        tip = get_random_tip()
        color = '#B8860B'
        markup = f'[dim {color}]✦ 팁: {tip}[/]'
        assert markup.count('[/]') == 1
        assert '[dim #B8860B]' in markup
        assert '✦ 팁: ' in markup
