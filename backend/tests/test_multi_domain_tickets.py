import pytest
from pydantic import ValidationError

from app.models.ticket import TicketCreate


def valid_payload(**overrides):
    payload = {
        "title": "Need help with an assignment",
        "description": "I need guidance finding the correct academic support resource.",
        "category": "Academic guidance",
        "building": "Not applicable",
        "floor": "Not applicable",
        "room": "Not applicable",
    }
    payload.update(overrides)
    return payload


def test_ticket_defaults_to_technical_campus_request():
    ticket = TicketCreate(**valid_payload())
    assert ticket.problem_domain == "technical"
    assert ticket.location_type == "campus"


@pytest.mark.parametrize(
    "domain",
    ["technical", "academic", "administrative", "facilities", "personal_support", "community", "other"],
)
def test_ticket_accepts_supported_problem_domains(domain):
    ticket = TicketCreate(**valid_payload(problem_domain=domain))
    assert ticket.problem_domain == domain


@pytest.mark.parametrize("location_type", ["campus", "remote", "not_applicable"])
def test_ticket_accepts_supported_location_types(location_type):
    ticket = TicketCreate(**valid_payload(location_type=location_type))
    assert ticket.location_type == location_type


def test_ticket_rejects_unknown_problem_domain():
    with pytest.raises(ValidationError):
        TicketCreate(**valid_payload(problem_domain="unapproved-domain"))


def test_ticket_rejects_unknown_location_type():
    with pytest.raises(ValidationError):
        TicketCreate(**valid_payload(location_type="somewhere-else"))
