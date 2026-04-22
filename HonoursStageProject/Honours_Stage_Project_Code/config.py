
# This section loads the configuration module dependencies.
import os


# this  Section stores teh base directory used ot build local file paths
baseDir = os.path.abspath(os.path.dirname(__file__))


# this  Section groups the configuration values used across the Flask application
# this class stores the shared configuration values used by the application.
class Config:
    # Change  this before deployment by setting teh SECRET_KEY environment variable instead of keeping teh development fallback value
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-change-me")

    UPLOAD_LOGO_FOLDER = os.path.join(baseDir, "static", "uploads", "logos")
    ALLOWED_LOGO_EXTENSIONS = {"png", "jpg", "jpeg", "svg", "webp"}
    DEFAULT_LOGO_FILENAME = "defaultLogo.svg"
    BRANDING_STATE_FILENAME = "siteBranding.json"
    BRANDING_STATE_PATH = os.path.join(baseDir, "branding", "siteBranding.json")
    STATS_STATE_PATH = os.path.join(baseDir, "statsConfig.json")

    THEME_BACKGROUND_COLOUR = "lightblue"
    THEME_BUTTON_COLOUR = "#2c6bed"
    THEME_BUTTON_TEXT_COLOUR = "#ffffff"

    MAX_CONTENT_LENGTH = 2 * 1024 * 1024

    # Set EMAIL_DELIVERY_MODE to graph, mock, or auto depending on whether Microsoft Graph has been configured in this environment.
    EMAIL_DELIVERY_MODE = os.environ.get("EMAIL_DELIVERY_MODE", "auto")
    MOCK_EMAIL_LOG_PATH = os.path.join(baseDir, "mockEmailLog.jsonl")


    # Set  these Microsoft Graph values as environment variables before using live email sending adn keep real secrets out of source control
    GRAPH_CLIENT_ID = os.environ.get("GRAPH_CLIENT_ID", "")
    GRAPH_CLIENT_SECRET = os.environ.get("GRAPH_CLIENT_SECRET", "")
    GRAPH_TENANT_ID = os.environ.get("GRAPH_TENANT_ID", "")
    GRAPH_SENDER_EMAIL = os.environ.get("GRAPH_SENDER_EMAIL", "")
    # Change  these local summariser settings only if teh deployment needs a different mode, label, or summary length
    LOCAL_SUMMARY_MODE = os.environ.get("LOCAL_SUMMARY_MODE", "rule_based")
    LOCAL_SUMMARY_MODEL_NAME = os.environ.get("LOCAL_SUMMARY_MODEL_NAME", "localRuleBasedSummariser-v1")
    LOCAL_SUMMARY_MAX_DETAIL_CHARS = os.environ.get("LOCAL_SUMMARY_MAX_DETAIL_CHARS", "320")
