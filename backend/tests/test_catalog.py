import pytest

from app.catalog import GovernanceError


def test_columns_limited_to_grant(svc):
    assert "salary" not in svc.catalog.columns("analyst", "employees")
    assert "salary" in svc.catalog.columns("hr_admin", "employees")


def test_ungranted_table_denied(svc):
    with pytest.raises(GovernanceError, match="no access to table 'secrets'"):
        svc.catalog.rewrite("analyst", "SELECT * FROM deals JOIN secrets ON 1=1")
    with pytest.raises(GovernanceError, match="no access to table 'deals'"):
        svc.catalog.run_select("hr_admin", "SELECT * FROM deals")


def test_ungranted_column_denied(svc):
    with pytest.raises(GovernanceError, match="column 'salary'"):
        svc.catalog.run_select("analyst", "SELECT name, salary FROM employees")


def test_ungranted_column_in_where_denied(svc):
    """Inference attack: filter on a hidden column without selecting it."""
    with pytest.raises(GovernanceError, match="column 'salary'"):
        svc.catalog.run_select("analyst", "SELECT name FROM employees WHERE salary > 150000")


def test_star_only_exposes_granted_columns(svc):
    res = svc.catalog.run_select("analyst", "SELECT * FROM employees")
    assert res["columns"] == ["id", "name", "department", "title", "region"]


def test_row_filter_applied(svc):
    res = svc.catalog.run_select("analyst", "SELECT DISTINCT region FROM deals")
    assert {r[0] for r in res["rows"]} == {"EMEA", "APAC"}


def test_row_filter_applied_through_aggregate(svc):
    res = svc.catalog.run_select("analyst", "SELECT COUNT(*) FROM deals")
    assert res["rows"] == [[7]]  # 10 deals, 3 are AMER


def test_mask_applied(svc):
    res = svc.catalog.run_select("hr_admin", "SELECT name, email FROM employees WHERE id = 1")
    assert res["rows"] == [["Asha Rao", "as***"]]


def test_mask_cannot_be_bypassed_in_where(svc):
    res = svc.catalog.run_select("hr_admin", "SELECT name FROM employees WHERE email = 'asha.rao@example.com'")
    assert res["rows"] == []


@pytest.mark.parametrize("sql", [
    "DROP TABLE employees",
    "DELETE FROM deals",
    "UPDATE deals SET amount = 0",
    "INSERT INTO deals VALUES (99,'x','EMEA',1,'Won','y')",
    "SELECT 1; DROP TABLE deals",
    "PRAGMA table_info(deals)",
    "ATTACH DATABASE 'x.db' AS x",
    "WITH t AS (SELECT * FROM deals) SELECT * FROM t",
    "SELECT * FROM sqlite_master",
    "SELECT * FROM main.deals",
])
def test_hostile_sql_rejected(svc, sql):
    with pytest.raises(GovernanceError):
        svc.catalog.run_select("analyst", sql)


def test_union_cannot_reach_hidden_table(svc):
    with pytest.raises(GovernanceError):
        svc.catalog.run_select("analyst", "SELECT account FROM deals UNION SELECT email FROM employees")


def test_subquery_cannot_reach_hidden_column(svc):
    with pytest.raises(GovernanceError):
        svc.catalog.run_select(
            "analyst", "SELECT name FROM employees WHERE id IN (SELECT id FROM employees WHERE salary > 1)")


def test_alias_and_join_work(svc):
    res = svc.catalog.run_select(
        "analyst", "SELECT e.name, d.account FROM employees e JOIN deals d ON d.owner = e.name ORDER BY d.id")
    assert res["rows"]


def test_row_cap(svc):
    svc.catalog.max_rows = 3
    res = svc.catalog.run_select("analyst", "SELECT * FROM employees")
    assert len(res["rows"]) == 3 and res["truncated"]


def test_unknown_role(svc):
    with pytest.raises(GovernanceError):
        svc.catalog.tables("intern")


def test_get_row_masks_customer(svc):
    row = svc.catalog.get_row("support", "tickets", 101)
    assert row["customer"] == "an***"
