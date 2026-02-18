"""
iTaK Email Tool - Email operations and management.
"""

import smtplib
import imaplib
import email
import httpx
import random
import string
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from tools.base import BaseTool, ToolResult


class EmailTool(BaseTool):
    """Send and manage emails.

    Supports creating new email accounts, sending emails via SMTP, 
    reading emails via IMAP, and managing mailboxes. Can work with 
    various email providers like Gmail, Outlook, or custom SMTP/IMAP 
    servers. Can also create temporary email accounts via Mail.tm API.
    """

    name = "email_tool"
    description = "Create email accounts, send, read, and manage emails."

    async def execute(
        self,
        action: str = "",
        to: str = "",
        subject: str = "",
        body: str = "",
        from_email: str = "",
        folder: str = "INBOX",
        limit: int = 10,
        username: str = "",
        password: str = "",
        **kwargs,
    ) -> ToolResult:
        """Execute an email operation.

        Args:
            action: The action to perform (create_account, send, read, list_folders, check_temp_mail)
            to: Recipient email address (for send)
            subject: Email subject (for send)
            body: Email body content (for send)
            from_email: Sender email address (for send)
            folder: IMAP folder name (for read, default: INBOX)
            limit: Number of emails to retrieve (for read)
            username: Username/email for account creation (optional, auto-generated if not provided)
            password: Password for account creation (optional, auto-generated if not provided)
        """
        if not action:
            return ToolResult(output="Error: 'action' is required.", error=True)

        try:
            if action == "create_account":
                return await self._create_temp_email_account(username, password)
            elif action == "check_temp_mail":
                return await self._check_temp_mail(username, password, limit)
            elif action == "send":
                return await self._send_email(to, subject, body, from_email)
            elif action == "read":
                return await self._read_emails(folder, limit)
            elif action == "list_folders":
                return await self._list_folders()
            else:
                return ToolResult(
                    output=f"Unknown email action: {action}. Supported: create_account, check_temp_mail, send, read, list_folders",
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

            # Send email with TLS
            with smtplib.SMTP(smtp_server, smtp_port, timeout=30) as server:
                server.starttls()  # Upgrade to TLS
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
                    output="Available folders:\n" + "\n".join(folder_list)
                )

        except Exception as e:
            return ToolResult(output=f"Failed to list folders: {e}", error=True)

    async def _create_temp_email_account(
        self, username: str = "", password: str = ""
    ) -> ToolResult:
        """Create a temporary email account using Mail.tm API.
        
        This creates a free, temporary email address that can be used
        for receiving emails. The account is created via the Mail.tm
        public API which requires no API key.
        """
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                # Step 1: Get available domains
                domains_response = await client.get("https://api.mail.tm/domains")
                domains_response.raise_for_status()
                domains_data = domains_response.json()
                
                if not domains_data.get("hydra:member"):
                    return ToolResult(
                        output="No available domains from Mail.tm service",
                        error=True,
                    )
                
                # Pick the first available domain
                domain = domains_data["hydra:member"][0]["domain"]
                
                # Step 2: Generate username and password if not provided
                if not username:
                    # Generate random username (8 chars)
                    username = "itak_" + "".join(
                        random.choices(string.ascii_lowercase + string.digits, k=8)
                    )
                
                email_address = f"{username}@{domain}"
                
                if not password:
                    # Generate secure random password
                    password = "".join(
                        random.choices(
                            string.ascii_letters + string.digits + string.punctuation, k=16
                        )
                    )
                
                # Step 3: Create the account
                create_response = await client.post(
                    "https://api.mail.tm/accounts",
                    json={"address": email_address, "password": password},
                )
                create_response.raise_for_status()
                account_data = create_response.json()
                
                # Step 4: Get authentication token
                token_response = await client.post(
                    "https://api.mail.tm/token",
                    json={"address": email_address, "password": password},
                )
                token_response.raise_for_status()
                token_data = token_response.json()
                
                result = (
                    f"✅ Successfully created temporary email account!\n\n"
                    f"Email Address: {email_address}\n"
                    f"Password: {password}\n"
                    f"Account ID: {account_data.get('id', 'N/A')}\n"
                    f"Auth Token: {token_data.get('token', 'N/A')}\n\n"
                    f"⚠️ IMPORTANT:\n"
                    f"- This is a temporary email address from Mail.tm\n"
                    f"- Emails may be deleted after a period of inactivity\n"
                    f"- Use 'check_temp_mail' action with username='{email_address}' and password to read emails\n"
                    f"- Store these credentials securely if you need to access this account later\n"
                )
                
                return ToolResult(output=result)
                
        except httpx.HTTPStatusError as e:
            error_detail = ""
            try:
                error_data = e.response.json()
                error_detail = f": {error_data.get('detail', error_data)}"
            except Exception:
                error_detail = f": {e.response.text}"
            return ToolResult(
                output=f"Failed to create email account - HTTP {e.response.status_code}{error_detail}",
                error=True,
            )
        except Exception as e:
            return ToolResult(
                output=f"Failed to create email account: {e}",
                error=True,
            )

    async def _check_temp_mail(
        self, username: str, password: str, limit: int = 10
    ) -> ToolResult:
        """Check emails from a Mail.tm temporary email account."""
        if not username or not password:
            return ToolResult(
                output="Error: 'username' and 'password' are required to check temp mail",
                error=True,
            )
        
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                # Step 1: Authenticate and get token
                token_response = await client.post(
                    "https://api.mail.tm/token",
                    json={"address": username, "password": password},
                )
                token_response.raise_for_status()
                token_data = token_response.json()
                auth_token = token_data.get("token")
                
                if not auth_token:
                    return ToolResult(
                        output="Failed to authenticate with Mail.tm",
                        error=True,
                    )
                
                # Step 2: Fetch messages
                headers = {"Authorization": f"Bearer {auth_token}"}
                messages_response = await client.get(
                    "https://api.mail.tm/messages",
                    headers=headers,
                )
                messages_response.raise_for_status()
                messages_data = messages_response.json()
                
                messages = messages_data.get("hydra:member", [])
                
                if not messages:
                    return ToolResult(output=f"No emails found for {username}")
                
                # Limit results
                messages = messages[:limit]
                
                # Format output
                output_parts = [f"Found {len(messages)} email(s) for {username}:\n"]
                for i, msg in enumerate(messages, 1):
                    from_addr = msg.get("from", {}).get("address", "Unknown")
                    subject = msg.get("subject", "No subject")
                    date = msg.get("createdAt", "Unknown date")
                    is_read = msg.get("seen", False)
                    status = "📖 Read" if is_read else "📧 New"
                    
                    output_parts.append(
                        f"\n{i}. {status}\n"
                        f"   From: {from_addr}\n"
                        f"   Subject: {subject}\n"
                        f"   Date: {date}\n"
                        f"   ID: {msg.get('id', 'N/A')}"
                    )
                
                return ToolResult(output="\n".join(output_parts))
                
        except httpx.HTTPStatusError as e:
            return ToolResult(
                output=f"Failed to check temp mail - HTTP {e.response.status_code}: {e.response.text}",
                error=True,
            )
        except Exception as e:
            return ToolResult(
                output=f"Failed to check temp mail: {e}",
                error=True,
            )
