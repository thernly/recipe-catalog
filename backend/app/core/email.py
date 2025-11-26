"""
Email service for sending verification and password reset emails
"""

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import aiosmtplib

from app.core.config import settings
from app.core.logging import get_logger


logger = get_logger(__name__)


class EmailService:
    """Email service for sending emails via SMTP"""

    def __init__(self):
        self.smtp_host = settings.SMTP_HOST
        self.smtp_port = settings.SMTP_PORT
        self.smtp_user = settings.SMTP_USER
        self.smtp_password = settings.SMTP_PASSWORD
        self.from_email = settings.FROM_EMAIL
        self.from_name = settings.FROM_NAME

    def is_configured(self) -> bool:
        """
        Check if email service is properly configured.

        Returns:
            True if SMTP configuration is complete, False otherwise
        """
        return bool(self.smtp_host and self.smtp_port and self.smtp_user and self.smtp_password)

    async def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: str | None = None,
    ) -> bool:
        """
        Send an email via SMTP asynchronously

        Args:
            to_email: Recipient email address
            subject: Email subject
            html_content: HTML email content
            text_content: Plain text fallback (optional)

        Returns:
            True if email sent successfully, False otherwise
        """
        # Check if email service is configured
        if not self.is_configured():
            logger.warning(
                f"Email service not configured. Skipping email to {to_email}. "
                "Please configure SMTP_HOST, SMTP_PORT, SMTP_USER, and SMTP_PASSWORD."
            )
            return False

        try:
            # Create message
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = f"{self.from_name} <{self.from_email}>"
            msg["To"] = to_email

            # Add text content if provided
            if text_content:
                part1 = MIMEText(text_content, "plain")
                msg.attach(part1)

            # Add HTML content
            part2 = MIMEText(html_content, "html")
            msg.attach(part2)

            # Determine if we should use TLS or SSL
            use_tls = self.smtp_port != 465

            # Send email asynchronously
            async with aiosmtplib.SMTP(
                hostname=self.smtp_host,
                port=self.smtp_port,
                use_tls=not use_tls,  # Use SSL for port 465
                start_tls=use_tls,  # Use STARTTLS for other ports
            ) as server:
                # Login if credentials provided
                if self.smtp_user and self.smtp_password:
                    await server.login(self.smtp_user, self.smtp_password)

                await server.send_message(msg)

            logger.info(f"Email sent successfully to {to_email}")
            return True

        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {str(e)}")
            return False

    async def send_verification_email(
        self, to_email: str, verification_token: str, user_name: str
    ) -> bool:
        """
        Send email verification link asynchronously

        Args:
            to_email: User's email address
            verification_token: Verification token
            user_name: User's display name

        Returns:
            True if email sent successfully
        """
        # Build verification URL
        verification_url = f"{settings.FRONTEND_URL}/auth/verify-email/{verification_token}"

        # HTML content
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #F59E0B; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 30px 20px; background-color: #f9f9f9; }}
                .button {{ display: inline-block; padding: 12px 24px; background-color: #F59E0B;
                          color: white; text-decoration: none; border-radius: 5px; margin: 20px 0; }}
                .footer {{ text-align: center; padding: 20px; font-size: 12px; color: #666; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Recipe Catalog</h1>
                </div>
                <div class="content">
                    <h2>Welcome, {user_name}!</h2>
                    <p>Thank you for signing up for Recipe Catalog. Please verify your email address to activate your account.</p>
                    <p style="text-align: center;">
                        <a href="{verification_url}" class="button">Verify Email Address</a>
                    </p>
                    <p>Or copy and paste this link into your browser:</p>
                    <p style="word-break: break-all; background: #fff; padding: 10px; border-radius: 3px;">
                        {verification_url}
                    </p>
                    <p><strong>This link will expire in 24 hours.</strong></p>
                    <p>If you did not create an account, please ignore this email.</p>
                </div>
                <div class="footer">
                    <p>&copy; 2024 Recipe Catalog. All rights reserved.</p>
                </div>
            </div>
        </body>
        </html>
        """

        # Plain text content
        text_content = f"""
        Welcome to Recipe Catalog, {user_name}!

        Please verify your email address by clicking the link below:
        {verification_url}

        This link will expire in 24 hours.

        If you did not create an account, please ignore this email.

        ---
        Recipe Catalog
        """

        return await self.send_email(
            to_email=to_email,
            subject="Verify Your Email - Recipe Catalog",
            html_content=html_content,
            text_content=text_content,
        )

    async def send_password_reset_email(
        self, to_email: str, reset_token: str, user_name: str
    ) -> bool:
        """
        Send password reset link asynchronously

        Args:
            to_email: User's email address
            reset_token: Password reset token
            user_name: User's display name

        Returns:
            True if email sent successfully
        """
        # Build reset URL
        reset_url = f"{settings.FRONTEND_URL}/auth/reset-password/{reset_token}"

        # HTML content
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #F59E0B; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 30px 20px; background-color: #f9f9f9; }}
                .button {{ display: inline-block; padding: 12px 24px; background-color: #F59E0B;
                          color: white; text-decoration: none; border-radius: 5px; margin: 20px 0; }}
                .footer {{ text-align: center; padding: 20px; font-size: 12px; color: #666; }}
                .warning {{ background: #FEF3C7; padding: 15px; border-left: 4px solid #F59E0B; margin: 20px 0; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Recipe Catalog</h1>
                </div>
                <div class="content">
                    <h2>Password Reset Request</h2>
                    <p>Hello {user_name},</p>
                    <p>We received a request to reset your password. Click the button below to create a new password:</p>
                    <p style="text-align: center;">
                        <a href="{reset_url}" class="button">Reset Password</a>
                    </p>
                    <p>Or copy and paste this link into your browser:</p>
                    <p style="word-break: break-all; background: #fff; padding: 10px; border-radius: 3px;">
                        {reset_url}
                    </p>
                    <div class="warning">
                        <p><strong>⚠️ Important Security Information:</strong></p>
                        <ul>
                            <li>This link will expire in 1 hour</li>
                            <li>This link can only be used once</li>
                            <li>If you didn't request a password reset, please ignore this email</li>
                        </ul>
                    </div>
                </div>
                <div class="footer">
                    <p>&copy; 2024 Recipe Catalog. All rights reserved.</p>
                </div>
            </div>
        </body>
        </html>
        """

        # Plain text content
        text_content = f"""
        Password Reset Request - Recipe Catalog

        Hello {user_name},

        We received a request to reset your password. Click the link below to create a new password:
        {reset_url}

        IMPORTANT:
        - This link will expire in 1 hour
        - This link can only be used once
        - If you didn't request a password reset, please ignore this email

        ---
        Recipe Catalog
        """

        return await self.send_email(
            to_email=to_email,
            subject="Reset Your Password - Recipe Catalog",
            html_content=html_content,
            text_content=text_content,
        )

    async def send_household_member_removed_email(
        self, to_email: str, household_name: str, user_name: str
    ) -> bool:
        """
        Send notification when user is removed from household

        Args:
            to_email: User's email address
            household_name: Name of the household
            user_name: User's display name

        Returns:
            True if email sent successfully
        """
        # HTML content
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #F59E0B; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 30px 20px; background-color: #f9f9f9; }}
                .button {{ display: inline-block; padding: 12px 24px; background-color: #F59E0B;
                          color: white; text-decoration: none; border-radius: 5px; margin: 20px 0; }}
                .footer {{ text-align: center; padding: 20px; font-size: 12px; color: #666; }}
                .info-box {{ background: #E0F2FE; padding: 15px; border-left: 4px solid #0EA5E9; margin: 20px 0; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Recipe Catalog</h1>
                </div>
                <div class="content">
                    <h2>Household Membership Update</h2>
                    <p>Hello {user_name},</p>
                    <p>You have been removed from the household <strong>"{household_name}"</strong>.</p>
                    <div class="info-box">
                        <p><strong>What this means:</strong></p>
                        <ul>
                            <li>You no longer have access to recipes and collections shared by this household</li>
                            <li>Your personal recipes remain safe and accessible</li>
                            <li>You can create a new household or join another one</li>
                        </ul>
                    </div>
                    <p>If you have questions about this change, please contact the household owner.</p>
                </div>
                <div class="footer">
                    <p>&copy; 2024 Recipe Catalog. All rights reserved.</p>
                </div>
            </div>
        </body>
        </html>
        """

        # Plain text content
        text_content = f"""
        Household Membership Update - Recipe Catalog

        Hello {user_name},

        You have been removed from the household "{household_name}".

        What this means:
        - You no longer have access to recipes and collections shared by this household
        - Your personal recipes remain safe and accessible
        - You can create a new household or join another one

        If you have questions about this change, please contact the household owner.

        ---
        Recipe Catalog
        """

        return await self.send_email(
            to_email=to_email,
            subject=f"Removed from Household - {household_name}",
            html_content=html_content,
            text_content=text_content,
        )

    async def send_household_invitation_accepted_email(
        self, to_email: str, household_name: str, invitee_name: str, owner_name: str
    ) -> bool:
        """
        Send notification to household owner when invitation is accepted

        Args:
            to_email: Household owner's email address
            household_name: Name of the household
            invitee_name: Name of the user who accepted
            owner_name: Owner's display name

        Returns:
            True if email sent successfully
        """
        # HTML content
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #F59E0B; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 30px 20px; background-color: #f9f9f9; }}
                .button {{ display: inline-block; padding: 12px 24px; background-color: #F59E0B;
                          color: white; text-decoration: none; border-radius: 5px; margin: 20px 0; }}
                .footer {{ text-align: center; padding: 20px; font-size: 12px; color: #666; }}
                .success-box {{ background: #D1FAE5; padding: 15px; border-left: 4px solid #10B981; margin: 20px 0; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Recipe Catalog</h1>
                </div>
                <div class="content">
                    <h2>New Household Member!</h2>
                    <p>Hello {owner_name},</p>
                    <div class="success-box">
                        <p><strong>{invitee_name}</strong> has joined your household <strong>"{household_name}"</strong>.</p>
                    </div>
                    <p>They can now:</p>
                    <ul>
                        <li>View and edit shared recipes</li>
                        <li>Access shared collections</li>
                        <li>Collaborate on meal planning</li>
                    </ul>
                    <p style="text-align: center;">
                        <a href="{settings.FRONTEND_URL}/settings?section=household" class="button">Manage Household</a>
                    </p>
                </div>
                <div class="footer">
                    <p>&copy; 2024 Recipe Catalog. All rights reserved.</p>
                </div>
            </div>
        </body>
        </html>
        """

        # Plain text content
        text_content = f"""
        New Household Member! - Recipe Catalog

        Hello {owner_name},

        {invitee_name} has joined your household "{household_name}".

        They can now:
        - View and edit shared recipes
        - Access shared collections
        - Collaborate on meal planning

        Manage your household at: {settings.FRONTEND_URL}/settings?section=household

        ---
        Recipe Catalog
        """

        return await self.send_email(
            to_email=to_email,
            subject=f"New Member Joined - {household_name}",
            html_content=html_content,
            text_content=text_content,
        )


# Create singleton instance
email_service = EmailService()
