import os

baseDir = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-change-me")

    UPLOAD_LOGO_FOLDER = os.path.join(baseDir, "static", "uploads", "logos")
    ALLOWED_LOGO_EXTENSIONS = {"png", "jpg", "jpeg", "svg", "webp"}
    DEFAULT_LOGO_FILENAME = "defaultLogo.svg"
    BRANDING_STATE_FILENAME = "siteBranding.json"
    BRANDING_STATE_PATH = os.path.join(baseDir, "branding", "siteBranding.json")
    STATS_STATE_PATH = os.path.join(baseDir, "statsConfig.json")

    THEME_BACKGROUND_COLOR = "lightblue"
    THEME_BUTTON_COLOR = "#2c6bed"
    THEME_BUTTON_TEXT_COLOR = "#ffffff"

    MAX_CONTENT_LENGTH = 2 * 1024 * 1024
