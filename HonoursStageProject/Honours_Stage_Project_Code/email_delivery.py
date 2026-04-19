
# This section imports the tools used by the email delivery strategies.
from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from urllib import parse, request


# This data class stores the outcome of an email delivery attempt.
@dataclass
class EmailDeliveryResult:
    status: str
    message: str
    recipients: list[str]


# This base class defines the interface used by all email delivery strategies.
class BaseEmailDeliveryStrategy:

    # This method defines the shared email-sending interface used by delivery strategies.
    def sendSubmissionEmail(self, recipients, subject, body, metadata):
        raise NotImplementedError


# This strategy writes email payloads to a local log instead of sending them live.
class MockEmailDeliveryStrategy(BaseEmailDeliveryStrategy):

    # This method handles init for mock email delivery strategy.
    def __init__(self, logPath):
        self.logPath = logPath


    # This method handles submission email for mock email delivery strategy.
    def sendSubmissionEmail(self, recipients, subject, body, metadata):
        recipients = [str(value).strip() for value in recipients or [] if str(value).strip()]
        if not recipients:
            return EmailDeliveryResult(status="skipped", message="No recipients were supplied.", recipients=[])
        logFolder = os.path.dirname(self.logPath)
        if logFolder:
            os.makedirs(logFolder, exist_ok=True)
        payload = {
            "timestampUtc": datetime.now(timezone.utc).isoformat(),
            "strategy": "mock",
            "recipients": recipients,
            "subject": subject,
            "body": body,
            "metadata": metadata,
        }
        with open(self.logPath, "a", encoding="utf-8") as f:
            f.write(json.dumps(payload, ensure_ascii=False) + "\n")
        return EmailDeliveryResult(status="mocked", message=f"Mock email written to {self.logPath}", recipients=recipients)


# This strategy sends submission emails through Microsoft Graph when configured.
# Set the Graph client, tenant, and sender values in config before switching a deployment to live email sending.
class GraphEmailDeliveryStrategy(BaseEmailDeliveryStrategy):

    # This method handles init for graph email delivery strategy.
    def __init__(self, clientId, clientSecret, tenantId, senderEmail):
        self.clientId = str(clientId or "").strip()
        self.clientSecret = str(clientSecret or "").strip()
        self.tenantId = str(tenantId or "").strip()
        self.senderEmail = str(senderEmail or "").strip()


    # This method handles configured for graph email delivery strategy.
    def isConfigured(self):
        return bool(self.clientId and self.clientSecret and self.tenantId and self.senderEmail)


    # This method handles access token for graph email delivery strategy.
    def getAccessToken(self):
        tokenUrl = f"https://login.microsoftonline.com/{self.tenantId}/oauth2/v2.0/token"
        tokenBody = parse.urlencode({
            "client_id": self.clientId,
            "client_secret": self.clientSecret,
            "scope": "https://graph.microsoft.com/.default",
            "grant_type": "client_credentials",
        }).encode("utf-8")
        req = request.Request(tokenUrl, data=tokenBody, headers={"Content-Type": "application/x-www-form-urlencoded"}, method="POST")
        with request.urlopen(req, timeout=20) as response:
            payload = json.loads(response.read().decode("utf-8"))
        return str(payload.get("access_token") or "").strip()


    # This method handles submission email for graph email delivery strategy.
    def sendSubmissionEmail(self, recipients, subject, body, metadata):
        recipients = [str(value).strip() for value in recipients or [] if str(value).strip()]
        if not recipients:
            return EmailDeliveryResult(status="skipped", message="No recipients were supplied.", recipients=[])
        if not self.isConfigured():
            return EmailDeliveryResult(status="unavailable", message="Graph email delivery is not configured.", recipients=recipients)
        accessToken = self.getAccessToken()
        if not accessToken:
            return EmailDeliveryResult(status="failed", message="Graph access token could not be obtained.", recipients=recipients)
        graphUrl = f"https://graph.microsoft.com/v1.0/users/{parse.quote(self.senderEmail)}/sendMail"
        payload = {
            "message": {
                "subject": subject,
                "body": {
                    "contentType": "Text",
                    "content": body,
                },
                "toRecipients": [{"emailAddress": {"address": item}} for item in recipients],
            },
            "saveToSentItems": True,
        }
        bodyBytes = json.dumps(payload).encode("utf-8")
        req = request.Request(graphUrl, data=bodyBytes, headers={
            "Authorization": f"Bearer {accessToken}",
            "Content-Type": "application/json",
        }, method="POST")
        with request.urlopen(req, timeout=20):
            pass
        return EmailDeliveryResult(status="sent", message="Email sent through Microsoft Graph.", recipients=recipients)


# This service wraps the active email strategy and standardizes error handling.
class EmailDeliveryService:

    # This method handles init for email delivery service.
    def __init__(self, strategy):
        self.strategy = strategy


    # This method handles submission email for email delivery service.
    def sendSubmissionEmail(self, recipients, subject, body, metadata):
        try:
            return self.strategy.sendSubmissionEmail(recipients, subject, body, metadata)
        except Exception as ex:
            return EmailDeliveryResult(status="failed", message=str(ex), recipients=[str(value).strip() for value in recipients or [] if str(value).strip()])


# This factory chooses the most suitable email delivery service for the current config.
class EmailDeliveryServiceFactory:

    # This method builds the right email delivery service for the current configuration.
    @staticmethod
    def create(config):
        graphStrategy = GraphEmailDeliveryStrategy(
            clientId=config.get("GRAPH_CLIENT_ID"),
            clientSecret=config.get("GRAPH_CLIENT_SECRET"),
            tenantId=config.get("GRAPH_TENANT_ID"),
            senderEmail=config.get("GRAPH_SENDER_EMAIL"),
        )
        mode = str(config.get("EMAIL_DELIVERY_MODE") or "auto").strip().lower()
        if mode == "graph" and graphStrategy.isConfigured():
            return EmailDeliveryService(graphStrategy)
        if mode == "graph" and not graphStrategy.isConfigured():
            # Configure the Graph environment values first or this will safely fall back to the mock email log instead of sending live mail.
            return EmailDeliveryService(MockEmailDeliveryStrategy(config.get("MOCK_EMAIL_LOG_PATH") or "mockEmailLog.jsonl"))
        if mode == "mock":
            return EmailDeliveryService(MockEmailDeliveryStrategy(config.get("MOCK_EMAIL_LOG_PATH") or "mockEmailLog.jsonl"))
        if graphStrategy.isConfigured():
            return EmailDeliveryService(graphStrategy)
        return EmailDeliveryService(MockEmailDeliveryStrategy(config.get("MOCK_EMAIL_LOG_PATH") or "mockEmailLog.jsonl"))
