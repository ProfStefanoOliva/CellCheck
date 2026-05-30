from cellcheck.models import CorrectionProfile, CorrectionRule, RuleType, WorksheetProfile


def test_required_activity_is_serialized_and_restored() -> None:
    profile = CorrectionProfile(
        exercise_name="Profilo attività",
        max_grade=10.0,
        worksheets=[
            WorksheetProfile(
                sheet_name="Foglio1",
                rules=[
                    CorrectionRule(
                        id="rule-1",
                        sheet_name="Foglio1",
                        cell="A1",
                        rule_type=RuleType.NON_EMPTY,
                        weight=1.0,
                        required_activity="Inserire il totale delle vendite annuali.",
                    )
                ],
            )
        ],
    )

    restored = CorrectionProfile.from_json_string(profile.to_json_string())

    assert restored.worksheets[0].rules[0].required_activity == "Inserire il totale delle vendite annuali."


def test_old_profiles_without_required_activity_remain_valid() -> None:
    payload = """
{
  "cellcheck_format": "ccal",
  "format_version": "1.0",
  "document_type": "correction_profile",
  "software_name": "CellCheck",
  "minimum_cellcheck_version": "0.7.0",
  "exercise_name": "Profilo legacy",
  "max_grade": 10.0,
  "worksheets": [
    {
      "sheet_name": "Foglio1",
      "rules": [
        {
          "id": "rule-1",
          "sheet_name": "Foglio1",
          "cell": "A1",
          "rule_type": "non_empty",
          "weight": 1.0,
          "enabled": true,
          "teacher_note": ""
        }
      ]
    }
  ]
}
"""

    restored = CorrectionProfile.from_json_string(payload)

    assert restored.worksheets[0].rules[0].required_activity == ""
