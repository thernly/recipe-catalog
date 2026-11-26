"""The "new member joined" email links to the household section of Settings."""

from unittest.mock import AsyncMock

from app.core.email import EmailService


async def test_joined_email_links_to_the_household_settings_section():
    service = EmailService()
    service.send_email = AsyncMock(return_value=True)

    await service.send_household_invitation_accepted_email(
        to_email="owner@example.com",
        household_name="Home",
        invitee_name="Sam",
        owner_name="Alex",
    )

    sent = service.send_email.call_args.kwargs
    # Settings sections live in the address fragment (/settings#household)
    assert "/settings#household" in sent["html_content"]
    assert "/settings#household" in sent["text_content"]
    assert "section=" not in sent["html_content"] + sent["text_content"]
