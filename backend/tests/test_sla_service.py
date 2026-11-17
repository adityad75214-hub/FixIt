from app.services.sla_service import check_ticket_sla


def test_malformed_sla_deadline_is_flagged_as_overdue():
    overdue, remaining = check_ticket_sla({"status": "open", "sla_deadline": "not-a-date"})
    assert overdue is True
    assert remaining == 0


def test_ticket_without_sla_deadline_is_not_flagged():
    overdue, remaining = check_ticket_sla({"status": "open"})
    assert overdue is False
    assert remaining == 999999
