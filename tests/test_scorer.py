"""Tests for the severity scoring service."""

from apps.api.services.scorer import calculate_severity


class TestCalculateSeverity:
    def test_severity_5_breaking(self):
        assert calculate_severity("Breaking change in API", "Endpoints removed") == 5

    def test_severity_5_deprecation(self):
        assert calculate_severity("API v1 deprecation notice", "Please migrate") == 5

    def test_severity_5_shutdown(self):
        assert calculate_severity("Service shutdown announced", "Will be unavailable") == 5

    def test_severity_4_new_model(self):
        assert calculate_severity("New model GPT-5 released", "Available for all") == 4

    def test_severity_4_launch(self):
        assert calculate_severity("Feature launch", "Now available") == 4

    def test_severity_4_generally_available(self):
        assert calculate_severity("GPT-4.5 generally available", "Rolling out") == 4

    def test_severity_3_pricing(self):
        assert calculate_severity("Pricing update", "New tier structure") == 3

    def test_severity_3_rate_limit(self):
        assert calculate_severity("Rate limit changes", "New limits apply") == 3

    def test_severity_2_feature(self):
        assert calculate_severity("New feature added", "Small improvement") == 2

    def test_severity_2_improvement(self):
        assert calculate_severity("Quality improvement", "Better results") == 2

    def test_severity_1_fix(self):
        assert calculate_severity("Bug fix for login", "Resolved issue") == 1

    def test_severity_1_patch(self):
        # "patch" matches severity 1, but "minor" also matches severity 1
        # No higher-level keywords present, so result is 1
        assert calculate_severity("Security patch applied", "Resolved crash") == 1

    def test_default_severity(self):
        """When no keyword matches, default to 2."""
        assert calculate_severity("Something happened", "No keywords here") == 2

    def test_highest_severity_wins(self):
        """When multiple severities match, the highest one wins."""
        # Contains "breaking" (5) and "feature" (2)
        result = calculate_severity("Breaking feature change", "New approach")
        assert result == 5

    def test_case_insensitive(self):
        assert calculate_severity("BREAKING CHANGE", "DEPRECATION notice") == 5
