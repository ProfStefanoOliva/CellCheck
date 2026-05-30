from cellcheck.models import CorrectionProfile, CorrectionRule, RuleType, WorksheetProfile


def test_profile_serializes_and_restores_workbook_names() -> None:
    profile = CorrectionProfile(
        exercise_name="Profilo modelli",
        max_grade=10.0,
        blank_workbook_name="modello_vuoto.xlsx",
        solved_workbook_name="modello_risolto.xlsx",
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
                    )
                ],
            )
        ],
    )

    restored = CorrectionProfile.from_json_string(profile.to_json_string())

    assert restored.blank_workbook_name == "modello_vuoto.xlsx"
    assert restored.solved_workbook_name == "modello_risolto.xlsx"


def test_old_profiles_without_workbook_names_remain_valid() -> None:
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
          "enabled": true
        }
      ]
    }
  ]
}
"""

    restored = CorrectionProfile.from_json_string(payload)

    assert restored.blank_workbook_name is None
    assert restored.solved_workbook_name is None
