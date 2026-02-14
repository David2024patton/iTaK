"""
iTaK Email Tool - Email operations and management.
"""

import smtplib
import imaplib
import email
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
from tools.base import BaseTool, ToolResult


class EmailTool(BaseTool):
    """Send and manage emails.

    Supports sending emails via SMTP, reading emails via IMAP,
    and managing mailboxes. Can work with various email providers
    like Gmail, Outlook, or custom SMTP/IMAP servers.
    """

    name = "email_tool"
    description = "Send, read, and manage emails."

    async def execute(
        self,
        action: str = "",
        to: str = "",
        subject: str = "",
        body: str = "",
        from_email: str = "",
        folder: str = "INBOX",
        limit: int = 10,
        **kwargs,
    ) -> ToolResult:
        """Execute an email operation.

        Args:
            action: The action to perform (send, read, list_folders, delete)
            to: Recipient email address (for send)
            subject: Email subject (for send)
            body: Email body content (for send)
            from_email: Sender email address (for send)
            folder: IMAP folder name (for read, default: INBOX)
            limit: Number of emails to retrieve (for read)
        """
        if not action:
            return ToolResult(output="Error: 'action' is required.", error=True)

        try:
            if action == "send":
                return await self._send_email(to, subject, body, from_email)
            elif action == "read":
                return await self._read_emails(folder, limit)
            elif action == "list_folders":
                return await self._list_folders()
            else:
                return ToolResult(
                    output=f"Unknown email action: {action}. Supported: send, read, list_folders",
                    error=True,
                )
        except Exception as e:
            return ToolResult(output=f"Email error: {e}", error=True)

    async def _send_email(
        self, to: str, subject: str, body: str, from_email: str = ""
    ) -> ToolResult:
        """Send an email via SMTP."""
        if not to or not subject or not body:
            return ToolResult(
                output="Error: 'to', 'subject', and 'body' are required for sending email.",
                error=True,
            )

        # Get SMTP configuration from agent config
        smtp_config = self.agent.config.get("email", {}).get("smtp", {})
        smtp_server = smtp_config.get("server", "")
        smtp_port = smtp_config.get("port", 587)
        smtp_user = smtp_config.get("username", "")
        smtp_password = smtp_config.get("password", "")

        if not smtp_server or not smtp_user or not smtp_password:
            return ToolResult(
                output="Error: SMTP configuration not found. Please configure email.smtp in config.json",
                error=True,
            )

        from_email = from_email or smtp_user

        try:
            # Create message
            msg = MIMEMultipart()
            msg["From"] = from_email
            msg["To"] = to
            msg["Subject"] = subject
            msg.attach(MIMEText(body, "plain"))

            # Send email
            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.starttls()
                server.login(smtp_user, smtp_password)
                server.send_message(msg)

            return ToolResult(output=f"Email sent successfully to {to}")

        except Exception as e:
            return ToolResult(output=f"Failed to send email: {e}", error=True)

    async def _read_emails(self, folder: str = "INBOX", limit: int = 10) -> ToolResult:
        """Read emails from IMAP server."""
        # Get IMAP configuration from agent config
        imap_config = self.agent.config.get("email", {}).get("imap", {})
        imap_server = imap_config.get("server", "")
        imap_port = imap_config.get("port", 993)
        imap_user = imap_config.get("username", "")
        imap_password = imap_config.get("password", "")

        if not imap_server or not imap_user or not imap_password:
            return ToolResult(
                output="Error: IMAP configuration not found. Please configure email.imap in config.json",
                error=True,
            )

        try:
            # Connect to IMAP server
            with imaplib.IMAP4_SSL(imap_server, imap_port) as mail:
                mail.login(imap_user, imap_password)
                mail.select(folder)

                # Search for all emails
                _, message_numbers = mail.search(None, "ALL")
                email_ids = message_numbers[0].split()

                # Get the last 'limit' emails
                email_ids = email_ids[-limit:]

                emails = []
                for email_id in email_ids:
                    _, msg_data = mail.fetch(email_id, "(RFC822)")
                    email_body = msg_data[0][1]
                    email_message = email.message_from_bytes(email_body)

                    subject = email_message["Subject"]
                    from_addr = email_message["From"]
                    date = email_message["Date"]

                    emails.append(f"From: {from_addr}\nDate: {date}\nSubject: {subject}\n")

                if not emails:
                    return ToolResult(output=f"No emails found in {folder}")

                return ToolResult(
                    output=f"Found {len(emails)} emails in {folder}:\n\n" + "\n---\n".join(emails)
                )

        except Exception as e:
            return ToolResult(output=f"Failed to read emails: {e}", error=True)

    async def _list_folders(self) -> ToolResult:
        """List available IMAP folders."""
        # Get IMAP configuration from agent config
        imap_config = self.agent.config.get("email", {}).get("imap", {})
        imap_server = imap_config.get("server", "")
        imap_port = imap_config.get("port", 993)
        imap_user = imap_config.get("username", "")
        imap_password = imap_config.get("password", "")

        if not imap_server or not imap_user or not imap_password:
            return ToolResult(
                output="Error: IMAP configuration not found. Please configure email.imap in config.json",
                error=True,
            )

        try:
            # Connect to IMAP server
            with imaplib.IMAP4_SSL(imap_server, imap_port) as mail:
                mail.login(imap_user, imap_password)
                _, folders = mail.list()

                folder_list = []
                for folder in folders:
                    # Parse folder name from IMAP LIST response
                    folder_str = folder.decode()
                    folder_list.append(folder_str)

                return ToolResult(
                    output=f"Available folders:\n" + "\n".join(folder_list)
                )

        except Exception as e:
            return ToolResult(output=f"Failed to list folders: {e}", error=True)
