

from __future__ import annotations
import os
import uuid
import json
import re
import secrets
import random
import hashlib
from collections import Counter, defaultdict
from functools import wraps
from decimal import Decimal
from datetime import datetime, timedelta
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from config import Config

app = Flask(__name__)


securityQuestions = [
    {"key": "firstSchool", "text": "What was the name of your first school?"},
    {"key": "childhoodStreet", "text": "What was the name of the street you grew up on?"},
    {"key": "firstPet", "text": "What was the name of your first pet?"},
    {"key": "favouriteTeacher", "text": "What was the surname of your favourite teacher?"},
    {"key": "firstTown", "text": "What town or city were you born in?"},
    {"key": "childhoodFriend", "text": "What was the first name of your childhood best friend?"},
    {"key": "firstHoliday", "text": "What was the first holiday destination you remember?"},
    {"key": "favouriteBook", "text": "What was your favourite book as a child?"},
    {"key": "firstJob", "text": "What was the name of your first workplace?"},
    {"key": "favouriteFood", "text": "What was your favourite food as a child?"},
]


def normalizeRoleName(value):
    return (str(value or "").strip().lower())


def normalizeCredentialText(value):
    return re.sub(r"\s+", " ", str(value or "")).strip()


def normalizeSecurityAnswer(value):
    return normalizeCredentialText(value).lower()


def buildOneTimeCode():
    alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
    return "-".join("".join(secrets.choice(alphabet) for _ in range(5)) for _ in range(4))


def createPlaceholderPasswordHash():
    return generate_password_hash(secrets.token_urlsafe(32))


def getSecurityQuestionMap():
    return {item["key"]: item["text"] for item in securityQuestions}


def passwordMeetsRules(passwordText):
    return len(passwordText or "") >= 8


def issueUserToken(userId, tokenType, minutesValid, createdByAdminId=None):
    rawCode = buildOneTimeCode()
    expiresAt = datetime.utcnow() + timedelta(minutes=int(minutesValid))
    UserSetupToken.query.filter(
        UserSetupToken.user_id == userId,
        UserSetupToken.token_type == tokenType,
        UserSetupToken.used_at.is_(None),
    ).update({"used_at": datetime.utcnow()}, synchronize_session=False)
    db.session.add(UserSetupToken(
        user_id=userId,
        token_type=tokenType,
        token_hash=generate_password_hash(rawCode),
        expires_at=expiresAt,
        created_by_admin_id=createdByAdminId,
    ))
    return rawCode, expiresAt


def getValidUserToken(userObj, rawCode, tokenType):
    if not userObj or not rawCode:
        return None
    tokenRows = (
        UserSetupToken.query
        .filter(
            UserSetupToken.user_id == userObj.user_id,
            UserSetupToken.token_type == tokenType,
            UserSetupToken.used_at.is_(None),
        )
        .order_by(UserSetupToken.created_at.desc(), UserSetupToken.token_id.desc())
        .all()
    )
    nowValue = datetime.utcnow()
    rawDigest = hashlib.sha256(rawCode.encode("utf-8")).hexdigest()
    for tokenRow in tokenRows:
        if tokenRow.expires_at and tokenRow.expires_at < nowValue:
            continue
        storedHash = str(tokenRow.token_hash or "")
        if storedHash == rawDigest or check_password_hash(storedHash, rawCode):
            return tokenRow
    return None


def clearPendingResetSession():
    for key in ("pendingResetUserId", "pendingResetTokenId", "pendingResetQuestionIds"):
        session.pop(key, None)


def ensureBrandingState():
    uploadLogoFolder = app.config.get("UPLOAD_LOGO_FOLDER")
    if not uploadLogoFolder:
        uploadLogoFolder = os.path.join(app.root_path, "static", "uploads", "logos")
    if uploadLogoFolder:
        os.makedirs(uploadLogoFolder, exist_ok=True)
    brandingStatePath = app.config.get("BRANDING_STATE_PATH")
    if not brandingStatePath:
        brandingStateFilename = app.config.get("BRANDING_STATE_FILENAME", "siteBranding.json")
        brandingStatePath = os.path.join(app.root_path, "branding", brandingStateFilename)
    brandingStateFolder = os.path.dirname(brandingStatePath)
    if brandingStateFolder:
        os.makedirs(brandingStateFolder, exist_ok=True)
    if not os.path.exists(brandingStatePath):
        with open(brandingStatePath, "w", encoding="utf-8") as f:
            f.write(json.dumps({"logoFilename": None}, indent=2))
    return brandingStatePath

def getBrandingState():
    brandingStatePath = ensureBrandingState()
    with open(brandingStatePath, "r", encoding="utf-8") as f:
        return json.load(f)

def setBrandingState(logoFilename: str | None):
    brandingStatePath = ensureBrandingState()
    with open(brandingStatePath, "w", encoding="utf-8") as f:
        f.write(json.dumps({"logoFilename": logoFilename}, indent=2))

def allowedLogo(filename: str) -> bool:
    if "." not in filename:
        return False
    ext = filename.rsplit(".", 1)[1].lower()
    allowed = app.config.get("ALLOWED_LOGO_EXTENSIONS", set())
    return ext in allowed


def ensureStatsState():
    statsStatePath = app.config.get("STATS_STATE_PATH")
    if not statsStatePath:
        statsStatePath = os.path.join(app.root_path, "statsConfig.json")
    statsStateFolder = os.path.dirname(statsStatePath)
    if statsStateFolder:
        os.makedirs(statsStateFolder, exist_ok=True)
    if not os.path.exists(statsStatePath):
        with open(statsStatePath, "w", encoding="utf-8") as f:
            f.write(json.dumps({"trackedQuestionKeys": [], "trackedQuestionVersionIds": []}, indent=2))
    return statsStatePath


def getStatsState():
    statsStatePath = ensureStatsState()
    with open(statsStatePath, "r", encoding="utf-8") as f:
        try:
            state = json.load(f)
        except json.JSONDecodeError:
            state = {"trackedQuestionKeys": [], "trackedQuestionVersionIds": []}
    if "trackedQuestionVersionIds" not in state or not isinstance(state.get("trackedQuestionVersionIds"), list):
        state["trackedQuestionVersionIds"] = []
    if "trackedQuestionKeys" not in state or not isinstance(state.get("trackedQuestionKeys"), list):
        state["trackedQuestionKeys"] = []
    return state


def setStatsState(trackedQuestionKeys, trackedQuestionVersionIds=None):
    statsStatePath = ensureStatsState()
    cleanIds = []
    for value in trackedQuestionVersionIds or []:
        try:
            cleanIds.append(int(value))
        except (TypeError, ValueError):
            continue
    cleanKeys = []
    for value in trackedQuestionKeys or []:
        valueText = str(value).strip()
        if valueText != "":
            cleanKeys.append(valueText)
    with open(statsStatePath, "w", encoding="utf-8") as f:
        f.write(json.dumps({"trackedQuestionKeys": cleanKeys, "trackedQuestionVersionIds": cleanIds}, indent=2))


def stats_required(view_func):
    @wraps(view_func)
    def wrapper(*args, **kwargs):
        if not session.get("user_id"):
            return redirect(url_for("index"))
        if session.get("role_name") not in ("admin", "developer"):
            flash("Stats access requires admin or developer permissions.", "error")
            return redirect(url_for("dashboard"))
        return view_func(*args, **kwargs)
    return wrapper


def normalizeStatsText(value):
    return re.sub(r"\s+", " ", str(value or "")).strip()


def normalizeStatsKey(value):
    return normalizeStatsText(value).lower()


def promptLooksLike(promptText, keywords):
    promptKey = normalizeStatsKey(promptText)
    return any(keyword in promptKey for keyword in keywords)


def isIdentityPrompt(promptText):
    promptKey = normalizeStatsKey(promptText)
    identityKeywords = [
        "email",
        "log number",
        "name",
        "supervisor",
        "team",
        "comments",
        "feedback",
        "greeting",
    ]
    if "staff member" in promptKey or "member of staff" in promptKey:
        return True
    return any(keyword in promptKey for keyword in identityKeywords)


def answerLooksLikeIssue(promptText, answerLabel):
    promptKey = normalizeStatsKey(promptText)
    answerKey = normalizeStatsKey(answerLabel)
    if not answerKey:
        return False
    negativeValues = {"no", "incorrect", "not correct", "false", "failed", "fail", "poor", "late", "missed"}
    positiveValues = {"yes", "correct", "true", "passed", "pass", "good", "compliant"}
    if any(keyword in promptKey for keyword in ["correct", "compliant", "right", "accurate"]):
        return answerKey in negativeValues
    if any(keyword in promptKey for keyword in ["missed", "error", "issue", "problem", "negated", "required feedback", "breach", "concern"]):
        return answerKey in positiveValues or answerKey not in {"n/a", "na", "none", "not applicable"}
    return answerKey not in {"n/a", "na", "none", "not applicable", "unknown"}


def monthKeyFromDate(value):
    if not value:
        return None
    return value.strftime("%Y-%m")


def monthLabelFromKey(value):
    try:
        return datetime.strptime(value, "%Y-%m").strftime("%b %Y")
    except ValueError:
        return value


def buildIssueSummary(issues):
    if not issues:
        return "None recorded"
    return issues[0][0]

app.config.from_object(Config)


DB_USER = os.environ.get("DB_USER", "admin")
DB_PASS = os.environ.get("DB_PASS", "A-Strong-Password")
DB_HOST = os.environ.get("DB_HOST", "127.0.0.1")
DB_PORT = os.environ.get("DB_PORT", "3306")
DB_NAME = os.environ.get("DB_NAME", "honoursstageproject")

app.config["SQLALCHEMY_DATABASE_URI"] = (
    f"mysql+pymysql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}?charset=utf8mb4"
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)


class Role(db.Model):
    __tablename__ = "roles"

    role_id = db.Column(db.SmallInteger, primary_key=True, autoincrement=True)
    role_name = db.Column(db.String(32), unique=True, nullable=False)


class User(db.Model):
    __tablename__ = "users"

    user_id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    display_name = db.Column(db.String(120), nullable=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role_id = db.Column(db.SmallInteger, db.ForeignKey("roles.role_id"), nullable=False)
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    must_set_password = db.Column(db.Boolean, nullable=False, default=False)
    recovery_questions_set = db.Column(db.Boolean, nullable=False, default=False)
    password_changed_at = db.Column(db.DateTime, nullable=True)
    session_version = db.Column(db.Integer, nullable=False, default=1)

    role = db.relationship("Role")


class Form(db.Model):
    __tablename__ = "forms"

    form_id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    form_key = db.Column(db.String(64), unique=True, nullable=False)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    created_by = db.Column(db.BigInteger, db.ForeignKey("users.user_id"), nullable=False)


class FormVersion(db.Model):
    __tablename__ = "form_versions"

    form_version_id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    form_id = db.Column(db.BigInteger, db.ForeignKey("forms.form_id"), nullable=False)
    version_number = db.Column(db.Integer, nullable=False)
    title = db.Column(db.String(255), nullable=True)
    description = db.Column(db.Text, nullable=True)
    created_by = db.Column(db.BigInteger, db.ForeignKey("users.user_id"), nullable=False)
    notes = db.Column(db.String(255), nullable=True)


class Question(db.Model):
    __tablename__ = "questions"

    question_id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    question_key = db.Column(db.String(64), unique=True, nullable=False)
    created_by = db.Column(db.BigInteger, db.ForeignKey("users.user_id"), nullable=False)


class QuestionVersion(db.Model):
    __tablename__ = "question_versions"

    question_version_id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    question_id = db.Column(db.BigInteger, db.ForeignKey("questions.question_id"), nullable=False)
    version_number = db.Column(db.Integer, nullable=False)
    prompt_text = db.Column(db.Text, nullable=False)
    response_type = db.Column(db.String(32), nullable=False)
    is_required = db.Column(db.Boolean, nullable=False, default=False)
    hint_text = db.Column(db.Text, nullable=True)
    question_description = db.Column(db.Text, nullable=True)
    is_locked = db.Column(db.Boolean, nullable=False, default=False)
    help_text = db.Column(db.Text, nullable=True)
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    created_by = db.Column(db.BigInteger, db.ForeignKey("users.user_id"), nullable=False)

    options = db.relationship(
        "QuestionVersionOption",
        back_populates="question_version",
        order_by="QuestionVersionOption.sort_order",
        lazy="select",
        cascade="all, delete-orphan",
    )


class QuestionVersionOption(db.Model):
    __tablename__ = "question_version_options"

    option_id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    question_version_id = db.Column(
        db.BigInteger,
        db.ForeignKey("question_versions.question_version_id"),
        nullable=False,
        index=True,
    )
    option_value = db.Column(db.String(128), nullable=False)
    option_label = db.Column(db.String(255), nullable=False)
    sort_order = db.Column(db.Integer, nullable=False, default=0)

    question_version = db.relationship("QuestionVersion", back_populates="options")



class FormVersionSection(db.Model):
    __tablename__ = "form_version_sections"

    section_id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    form_version_id = db.Column(db.BigInteger, db.ForeignKey("form_versions.form_version_id"), nullable=False, index=True)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    sort_order = db.Column(db.Integer, nullable=False, default=0)

class FormVersionQuestion(db.Model):
    __tablename__ = "form_version_questions"

    form_version_question_id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    form_version_id = db.Column(db.BigInteger, db.ForeignKey("form_versions.form_version_id"), nullable=False)
    question_version_id = db.Column(db.BigInteger, db.ForeignKey("question_versions.question_version_id"), nullable=False)
    section_id = db.Column(db.BigInteger, db.ForeignKey("form_version_sections.section_id"), nullable=True)
    sort_order = db.Column(db.Integer, nullable=False, default=0)


class FormQuestionBranching(db.Model):
    __tablename__ = "form_question_branching"

    branching_id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    form_version_id = db.Column(db.BigInteger, db.ForeignKey("form_versions.form_version_id"), nullable=False)
    source_question_version_id = db.Column(db.BigInteger, db.ForeignKey("question_versions.question_version_id"), nullable=False)
    target_question_version_id = db.Column(db.BigInteger, db.ForeignKey("question_versions.question_version_id"), nullable=False)
    operator = db.Column(db.String(32), nullable=False)
    compare_option_value = db.Column(db.String(128), nullable=True)
    compare_number = db.Column(db.Numeric(18, 6), nullable=True)
    compare_text = db.Column(db.String(255), nullable=True)
    action = db.Column(db.String(16), nullable=False)
    priority = db.Column(db.Integer, nullable=False, default=0)


class FormSubmission(db.Model):
    __tablename__ = "form_submissions"

    submission_id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    form_id = db.Column(db.BigInteger, db.ForeignKey("forms.form_id"), nullable=False)
    form_version_id = db.Column(db.BigInteger, db.ForeignKey("form_versions.form_version_id"), nullable=False)
    submitted_by = db.Column(db.BigInteger, db.ForeignKey("users.user_id"), nullable=False)
    submitted_at = db.Column(db.DateTime, nullable=False, server_default=db.func.current_timestamp())


class SubmissionAnswer(db.Model):
    __tablename__ = "submission_answers"

    submission_answer_id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    submission_id = db.Column(db.BigInteger, db.ForeignKey("form_submissions.submission_id"), nullable=False)
    question_version_id = db.Column(db.BigInteger, db.ForeignKey("question_versions.question_version_id"), nullable=False)
    answer_text = db.Column(db.Text, nullable=True)
    answer_number = db.Column(db.Numeric(18, 6), nullable=True)
    answer_option_value = db.Column(db.String(128), nullable=True)


class UserSetupToken(db.Model):
    __tablename__ = "user_setup_tokens"

    token_id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    user_id = db.Column(db.BigInteger, db.ForeignKey("users.user_id"), nullable=False)
    token_type = db.Column(db.String(16), nullable=False)
    token_hash = db.Column(db.String(255), nullable=False)
    expires_at = db.Column(db.DateTime, nullable=False)
    used_at = db.Column(db.DateTime, nullable=True)
    created_by_admin_id = db.Column(db.BigInteger, db.ForeignKey("users.user_id"), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, server_default=db.func.current_timestamp())


class UserSecurityQuestion(db.Model):
    __tablename__ = "user_security_questions"

    security_question_id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    user_id = db.Column(db.BigInteger, db.ForeignKey("users.user_id"), nullable=False)
    question_key = db.Column(db.String(64), nullable=False)
    question_text = db.Column(db.String(255), nullable=False)
    answer_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, server_default=db.func.current_timestamp())


def login_required(view_func):
    @wraps(view_func)
    def wrapper(*args, **kwargs):
        userId = session.get("user_id")
        if not userId:
            return redirect(url_for("index"))
        userObj = User.query.filter_by(user_id=int(userId)).first()
        if not userObj or not userObj.is_active:
            session.clear()
            return redirect(url_for("index"))
        if int(session.get("session_version") or 0) != int(userObj.session_version or 1):
            session.clear()
            flash("Please sign in again.", "info")
            return redirect(url_for("index"))
        if userObj.must_set_password:
            session.clear()
            flash("Account setup is required before you can sign in.", "warning")
            return redirect(url_for("set_password"))
        session["role_name"] = normalizeRoleName(userObj.role.role_name if userObj.role else None)
        return view_func(*args, **kwargs)
    return wrapper


def admin_required(view_func):
    @wraps(view_func)
    def wrapper(*args, **kwargs):
        if not session.get("user_id"):
            return redirect(url_for("index"))
        if session.get("role_name") != "admin":
            flash("Admins only.", "error")
            return redirect(url_for("dashboard"))
        return view_func(*args, **kwargs)
    return wrapper


def editor_required(view_func):
    @wraps(view_func)
    def wrapper(*args, **kwargs):
        if not session.get("user_id"):
            return redirect(url_for("index"))
        role_name = session.get("role_name")
        if role_name not in ("admin", "developer"):
            flash("Editors only.", "error")
            return redirect(url_for("dashboard"))
        return view_func(*args, **kwargs)
    return wrapper

@app.context_processor
def injectBranding():
    brandingState = getBrandingState()
    logoFilename = brandingState.get("logoFilename")
    uploadLogoFolder = app.config.get("UPLOAD_LOGO_FOLDER") or os.path.join(app.root_path, "static", "uploads", "logos")
    defaultLogoFilename = app.config.get("DEFAULT_LOGO_FILENAME")
    logoExists = False
    if logoFilename:
        logoPath = os.path.join(uploadLogoFolder, logoFilename)
        logoExists = os.path.exists(logoPath)
    if logoFilename and logoExists:
        siteLogoUrl = url_for("static", filename=f"uploads/logos/{logoFilename}")
    else:
        siteLogoUrl = url_for("static", filename=f"branding/{defaultLogoFilename}")
    themeBackgroundColor = app.config.get("THEME_BACKGROUND_COLOR")
    themeButtonColor = app.config.get("THEME_BUTTON_COLOR")
    themeButtonTextColor = app.config.get("THEME_BUTTON_TEXT_COLOR")
    return {
        "siteLogoUrl": siteLogoUrl,
        "themeBackgroundColor": themeBackgroundColor,
        "themeButtonColor": themeButtonColor,
        "themeButtonTextColor": themeButtonTextColor,
    }


@app.route("/admin/branding", methods=["GET", "POST"])
@admin_required
def branding():
    if request.method == "POST":
        file = request.files.get("logo")
        if not file or not file.filename:
            flash("No file selected.", "error")
            return redirect(url_for("branding"))
        if not allowedLogo(file.filename):
            flash("Invalid file type.", "error")
            return redirect(url_for("branding"))
        ext = file.filename.rsplit(".", 1)[1].lower()
        logoFilename = secure_filename(f"logo_{uuid.uuid4().hex}.{ext}")
        uploadLogoFolder = app.config.get("UPLOAD_LOGO_FOLDER")
        if not uploadLogoFolder:
            uploadLogoFolder = os.path.join(app.root_path, "static", "uploads", "logos")
        os.makedirs(uploadLogoFolder, exist_ok=True)
        savePath = os.path.join(uploadLogoFolder, logoFilename)
        file.save(savePath)
        setBrandingState(logoFilename)
        flash("Logo updated.", "success")
        return redirect(url_for("branding"))
    return render_template("branding.html")



def ensureDatabaseSchema():
    dbName = db.engine.url.database
    if not dbName:
        return

    def columnExists(tableName, columnName):
        row = db.session.execute(db.text(
            "SELECT 1 FROM information_schema.columns WHERE table_schema = :schemaName AND table_name = :tableName AND column_name = :columnName LIMIT 1"
        ), {"schemaName": dbName, "tableName": tableName, "columnName": columnName}).fetchone()
        return row is not None

    def tableExists(tableName):
        row = db.session.execute(db.text(
            "SELECT 1 FROM information_schema.tables WHERE table_schema = :schemaName AND table_name = :tableName LIMIT 1"
        ), {"schemaName": dbName, "tableName": tableName}).fetchone()
        return row is not None

    usersAlter = [
        ("display_name", "ALTER TABLE users ADD COLUMN display_name VARCHAR(120) NULL AFTER username"),
        ("must_set_password", "ALTER TABLE users ADD COLUMN must_set_password TINYINT(1) NOT NULL DEFAULT 0 AFTER is_active"),
        ("recovery_questions_set", "ALTER TABLE users ADD COLUMN recovery_questions_set TINYINT(1) NOT NULL DEFAULT 0 AFTER must_set_password"),
        ("password_changed_at", "ALTER TABLE users ADD COLUMN password_changed_at DATETIME NULL AFTER recovery_questions_set"),
        ("session_version", "ALTER TABLE users ADD COLUMN session_version INT NOT NULL DEFAULT 1 AFTER password_changed_at"),
    ]
    for columnName, statement in usersAlter:
        if not columnExists("users", columnName):
            db.session.execute(db.text(statement))

    formVersionsAlter = [
        ("title", "ALTER TABLE form_versions ADD COLUMN title VARCHAR(255) NULL AFTER version_number"),
        ("description", "ALTER TABLE form_versions ADD COLUMN description TEXT NULL AFTER title"),
        ("notes", "ALTER TABLE form_versions ADD COLUMN notes VARCHAR(255) NULL AFTER created_by"),
    ]
    for columnName, statement in formVersionsAlter:
        if tableExists("form_versions") and not columnExists("form_versions", columnName):
            db.session.execute(db.text(statement))

    questionVersionsAlter = [
        ("hint_text", "ALTER TABLE question_versions ADD COLUMN hint_text TEXT NULL AFTER is_required"),
        ("question_description", "ALTER TABLE question_versions ADD COLUMN question_description TEXT NULL AFTER hint_text"),
        ("is_locked", "ALTER TABLE question_versions ADD COLUMN is_locked TINYINT(1) NOT NULL DEFAULT 0 AFTER question_description"),
        ("help_text", "ALTER TABLE question_versions ADD COLUMN help_text TEXT NULL AFTER is_locked"),
        ("is_active", "ALTER TABLE question_versions ADD COLUMN is_active TINYINT(1) NOT NULL DEFAULT 1 AFTER help_text"),
    ]
    for columnName, statement in questionVersionsAlter:
        if tableExists("question_versions") and not columnExists("question_versions", columnName):
            db.session.execute(db.text(statement))

    if tableExists("form_version_questions") and not columnExists("form_version_questions", "section_id"):
        db.session.execute(db.text("ALTER TABLE form_version_questions ADD COLUMN section_id BIGINT UNSIGNED NULL AFTER question_version_id"))

    if not tableExists("form_version_sections"):
        db.session.execute(db.text("""
            CREATE TABLE form_version_sections (
              section_id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
              form_version_id BIGINT UNSIGNED NOT NULL,
              title VARCHAR(255) NOT NULL,
              description TEXT NULL,
              sort_order INT UNSIGNED NOT NULL DEFAULT 0,
              PRIMARY KEY (section_id),
              KEY idx_form_version_sections_form_version (form_version_id, sort_order),
              CONSTRAINT fk_form_version_sections_form_version FOREIGN KEY (form_version_id) REFERENCES form_versions(form_version_id) ON DELETE CASCADE ON UPDATE RESTRICT
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """))

    if not tableExists("user_setup_tokens"):
        db.session.execute(db.text("""
            CREATE TABLE user_setup_tokens (
              token_id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
              user_id BIGINT UNSIGNED NOT NULL,
              token_type VARCHAR(16) NOT NULL,
              token_hash VARCHAR(255) NOT NULL,
              expires_at DATETIME NOT NULL,
              used_at DATETIME NULL,
              created_by_admin_id BIGINT UNSIGNED NULL,
              created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
              PRIMARY KEY (token_id),
              KEY idx_user_setup_tokens_user (user_id, token_type, used_at),
              KEY idx_user_setup_tokens_expires (expires_at),
              CONSTRAINT fk_user_setup_tokens_user FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE ON UPDATE RESTRICT,
              CONSTRAINT fk_user_setup_tokens_admin FOREIGN KEY (created_by_admin_id) REFERENCES users(user_id) ON DELETE SET NULL ON UPDATE RESTRICT
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """))

    if not tableExists("user_security_questions"):
        db.session.execute(db.text("""
            CREATE TABLE user_security_questions (
              security_question_id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
              user_id BIGINT UNSIGNED NOT NULL,
              question_key VARCHAR(64) NOT NULL,
              question_text VARCHAR(255) NOT NULL,
              answer_hash VARCHAR(255) NOT NULL,
              created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
              PRIMARY KEY (security_question_id),
              UNIQUE KEY uq_user_security_question (user_id, question_key),
              KEY idx_user_security_questions_user (user_id),
              CONSTRAINT fk_user_security_questions_user FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE ON UPDATE RESTRICT
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """))

    db.session.commit()


def seed_roles_if_missing():
    existingRoles = {normalizeRoleName(role.role_name): role for role in Role.query.all()}
    for roleName in ("admin", "standard", "developer"):
        if roleName not in existingRoles:
            db.session.add(Role(role_name=roleName))
    db.session.commit()


@app.before_request
def _ensure_db_ready():
    if not app.config.get("_SEEDED_ROLES"):
        db.session.execute(db.text("SELECT 1"))
        ensureDatabaseSchema()
        seed_roles_if_missing()
        app.config["_SEEDED_ROLES"] = True


def _get_active_form_and_latest_version():
    f = db.session.query(Form).filter(Form.is_active == 1).first()
    if not f:
        return None, None
    v = (
        db.session.query(FormVersion)
        .filter(FormVersion.form_id == f.form_id)
        .order_by(FormVersion.version_number.desc())
        .first()
    )
    return f, v


def _get_sections_for_version(form_version_id: int):
    sections = (
        db.session.query(FormVersionSection)
        .filter(FormVersionSection.form_version_id == form_version_id)
        .order_by(FormVersionSection.sort_order.asc(), FormVersionSection.section_id.asc())
        .all()
    )

    rows = (
        db.session.query(FormVersionQuestion, QuestionVersion)
        .join(
            QuestionVersion,
            FormVersionQuestion.question_version_id == QuestionVersion.question_version_id,
        )
        .filter(FormVersionQuestion.form_version_id == form_version_id)
        .all()
    )

    unsectioned = []
    section_questions = {}

    for fvq, qv in rows:
        sid = fvq.section_id
        if sid is None:
            unsectioned.append((int(fvq.sort_order or 0), qv))
        else:
            section_questions.setdefault(int(sid), []).append((int(fvq.sort_order or 0), qv))

    unsectioned_questions = [q for _, q in sorted(unsectioned, key=lambda t: t[0])]

    sections_with_questions = []
    for s in sections:
        q_list = section_questions.get(int(s.section_id), [])
        q_sorted = [q for _, q in sorted(q_list, key=lambda t: t[0])]
        sections_with_questions.append({"section": s, "questions": q_sorted})

    return unsectioned_questions, sections_with_questions


def _get_questions_for_version(form_version_id: int):
    unsectioned_questions, sections_with_questions = _get_sections_for_version(form_version_id)
    out = []
    out.extend(unsectioned_questions)
    for item in sections_with_questions:
        out.extend(item.get("questions") or [])
    return out



def _get_branching_for_version(form_version_id: int):
    rows = (
        db.session.query(FormQuestionBranching)
        .filter(FormQuestionBranching.form_version_id == form_version_id)
        .order_by(FormQuestionBranching.priority.asc(), FormQuestionBranching.branching_id.asc())
        .all()
    )
    return [
        {
            "source": int(r.source_question_version_id),
            "target": int(r.target_question_version_id),
            "operator": r.operator,
            "compare_option_value": r.compare_option_value,
            "compare_text": r.compare_text,
            "compare_number": str(r.compare_number) if r.compare_number is not None else None,
            "action": r.action,
            "priority": int(r.priority or 0),
        }
        for r in rows
        if (r.action or "").strip() in ("show", "goto")
    ]


@app.route("/api/branching/<int:form_version_id>", methods=["GET"])
@login_required
def api_branching(form_version_id: int):
    return jsonify(_get_branching_for_version(form_version_id))


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        username = normalizeCredentialText(request.form.get("username") or "")
        password = request.form.get("password") or ""

        user = User.query.filter_by(username=username).first()
        if user and user.is_active and user.must_set_password:
            flash("This account still needs first-time setup. Use your one-time setup code on the Set password page.", "warning")
            return redirect(url_for("set_password", username=username))
        if not user or not user.is_active or not check_password_hash(user.password_hash, password):
            flash("Invalid username or password.", "error")
            return render_template("index.html"), 401

        session.clear()
        session["user_id"] = int(user.user_id)
        session["username"] = user.username
        session["role_name"] = normalizeRoleName(user.role.role_name if user.role else None)
        session["session_version"] = int(user.session_version or 1)
        return redirect(url_for("dashboard"))

    return render_template("index.html")


@app.route("/signup", methods=["GET", "POST"])
def signup():
    flash("Accounts can only be created by an admin.", "warning")
    return redirect(url_for("index"))


@app.route("/set-password", methods=["GET", "POST"])
def set_password():
    questionMap = getSecurityQuestionMap()
    if request.method == "POST":
        username = normalizeCredentialText(request.form.get("username") or "")
        setupCode = normalizeCredentialText(request.form.get("setup_code") or "")
        newPassword = request.form.get("new_password") or ""
        confirmPassword = request.form.get("confirm_new_password") or ""
        selectedKeys = request.form.getlist("question_key")
        answerValues = request.form.getlist("question_answer")

        user = User.query.filter_by(username=username).first()
        if not user or not user.is_active:
            flash("User not found.", "error")
            return render_template("set_password.html", securityQuestions=securityQuestions, presetUsername=username), 404
        tokenRow = getValidUserToken(user, setupCode, "setup")
        if not tokenRow:
            flash("Invalid or expired setup code.", "error")
            return render_template("set_password.html", securityQuestions=securityQuestions, presetUsername=username), 400
        if not passwordMeetsRules(newPassword) or newPassword != confirmPassword:
            flash("Password must be at least 8 characters and both password fields must match.", "error")
            return render_template("set_password.html", securityQuestions=securityQuestions, presetUsername=username), 400
        if len(selectedKeys) != 5 or len(answerValues) != 5:
            flash("Please choose and answer all 5 security questions.", "error")
            return render_template("set_password.html", securityQuestions=securityQuestions, presetUsername=username), 400
        cleanKeys = [normalizeCredentialText(value) for value in selectedKeys]
        if len(set(cleanKeys)) != 5 or any(key not in questionMap for key in cleanKeys):
            flash("Please choose 5 different security questions.", "error")
            return render_template("set_password.html", securityQuestions=securityQuestions, presetUsername=username), 400
        cleanAnswers = [normalizeSecurityAnswer(value) for value in answerValues]
        if any(not value for value in cleanAnswers):
            flash("Please answer all 5 security questions.", "error")
            return render_template("set_password.html", securityQuestions=securityQuestions, presetUsername=username), 400

        UserSecurityQuestion.query.filter_by(user_id=user.user_id).delete()
        for questionKey, answerValue in zip(cleanKeys, cleanAnswers):
            db.session.add(UserSecurityQuestion(
                user_id=user.user_id,
                question_key=questionKey,
                question_text=questionMap[questionKey],
                answer_hash=generate_password_hash(answerValue),
            ))

        user.password_hash = generate_password_hash(newPassword)
        user.must_set_password = False
        user.recovery_questions_set = True
        user.password_changed_at = datetime.utcnow()
        user.session_version = int(user.session_version or 1) + 1
        tokenRow.used_at = datetime.utcnow()
        db.session.commit()

        flash("Password set successfully. You can now sign in.", "success")
        return redirect(url_for("index"))

    presetUsername = normalizeCredentialText(request.args.get("username") or "")
    return render_template("set_password.html", securityQuestions=securityQuestions, presetUsername=presetUsername)


@app.route("/reset-password", methods=["GET", "POST"])
def reset_password():
    questionRows = []
    pendingUserId = session.get("pendingResetUserId")
    pendingQuestionIds = session.get("pendingResetQuestionIds") or []
    if pendingUserId and pendingQuestionIds:
        questionRows = UserSecurityQuestion.query.filter(
            UserSecurityQuestion.user_id == int(pendingUserId),
            UserSecurityQuestion.security_question_id.in_([int(value) for value in pendingQuestionIds]),
        ).order_by(UserSecurityQuestion.security_question_id.asc()).all()

    if request.method == "POST":
        formStep = request.form.get("form_step") or "verify"
        if formStep == "verify":
            clearPendingResetSession()
            username = normalizeCredentialText(request.form.get("username") or "")
            resetCode = normalizeCredentialText(request.form.get("reset_code") or "")
            user = User.query.filter_by(username=username).first()
            if not user or not user.is_active or not user.recovery_questions_set:
                flash("Invalid reset details.", "error")
                return render_template("reset_password.html"), 400
            tokenRow = getValidUserToken(user, resetCode, "reset")
            if not tokenRow:
                flash("Invalid or expired reset code.", "error")
                return render_template("reset_password.html"), 400
            availableQuestions = UserSecurityQuestion.query.filter_by(user_id=user.user_id).all()
            if len(availableQuestions) < 2:
                flash("This account does not have enough recovery questions configured.", "error")
                return render_template("reset_password.html"), 400
            chosenQuestions = random.sample(availableQuestions, 2)
            session["pendingResetUserId"] = int(user.user_id)
            session["pendingResetTokenId"] = int(tokenRow.token_id)
            session["pendingResetQuestionIds"] = [int(item.security_question_id) for item in chosenQuestions]
            return render_template("reset_password.html", resetQuestions=chosenQuestions, presetUsername=username, questionStep=True)

        if formStep == "complete":
            pendingUserId = session.get("pendingResetUserId")
            pendingTokenId = session.get("pendingResetTokenId")
            pendingQuestionIds = session.get("pendingResetQuestionIds") or []
            username = normalizeCredentialText(request.form.get("username") or "")
            newPassword = request.form.get("new_password") or ""
            confirmPassword = request.form.get("confirm_new_password") or ""
            if not pendingUserId or not pendingTokenId or len(pendingQuestionIds) != 2:
                flash("Your reset session has expired. Please start again.", "error")
                clearPendingResetSession()
                return redirect(url_for("reset_password"))
            user = User.query.filter_by(user_id=int(pendingUserId), username=username).first()
            tokenRow = UserSetupToken.query.filter_by(token_id=int(pendingTokenId), token_type="reset", user_id=int(pendingUserId)).first()
            questionRows = UserSecurityQuestion.query.filter(
                UserSecurityQuestion.user_id == int(pendingUserId),
                UserSecurityQuestion.security_question_id.in_([int(value) for value in pendingQuestionIds]),
            ).order_by(UserSecurityQuestion.security_question_id.asc()).all()
            if not user or not tokenRow or tokenRow.used_at is not None or tokenRow.expires_at < datetime.utcnow() or len(questionRows) != 2:
                flash("Your reset session has expired. Please start again.", "error")
                clearPendingResetSession()
                return redirect(url_for("reset_password"))
            if not passwordMeetsRules(newPassword) or newPassword != confirmPassword:
                flash("Password must be at least 8 characters and both password fields must match.", "error")
                return render_template("reset_password.html", resetQuestions=questionRows, presetUsername=username, questionStep=True), 400
            answerOne = normalizeSecurityAnswer(request.form.get(f"question_answer_{questionRows[0].security_question_id}") or "")
            answerTwo = normalizeSecurityAnswer(request.form.get(f"question_answer_{questionRows[1].security_question_id}") or "")
            if not check_password_hash(questionRows[0].answer_hash, answerOne) or not check_password_hash(questionRows[1].answer_hash, answerTwo):
                flash("Your recovery answers were not correct.", "error")
                return render_template("reset_password.html", resetQuestions=questionRows, presetUsername=username, questionStep=True), 400
            user.password_hash = generate_password_hash(newPassword)
            user.must_set_password = False
            user.password_changed_at = datetime.utcnow()
            user.session_version = int(user.session_version or 1) + 1
            tokenRow.used_at = datetime.utcnow()
            db.session.commit()
            clearPendingResetSession()
            flash("Password reset successfully. You can now sign in.", "success")
            return redirect(url_for("index"))

    return render_template("reset_password.html", resetQuestions=questionRows, questionStep=bool(questionRows), presetUsername="")


@app.route("/admin/users", methods=["GET", "POST"])
@admin_required
def manage_users():
    adminId = int(session.get("user_id"))
    revealCode = None
    revealTitle = None
    revealMeta = None

    if request.method == "POST":
        formAction = request.form.get("form_action") or ""
        if formAction == "create_user":
            username = normalizeCredentialText(request.form.get("username") or "")
            displayName = normalizeCredentialText(request.form.get("display_name") or "")
            roleIdRaw = request.form.get("role_id") or ""
            roleObj = Role.query.filter_by(role_id=int(roleIdRaw)).first() if str(roleIdRaw).isdigit() else None
            if not username or len(username) > 64:
                flash("Please enter a valid username.", "error")
                return redirect(url_for("manage_users"))
            if not roleObj:
                flash("Please choose an account role.", "error")
                return redirect(url_for("manage_users"))
            if User.query.filter_by(username=username).first():
                flash("That username already exists.", "error")
                return redirect(url_for("manage_users"))
            userObj = User(
                username=username,
                display_name=displayName or None,
                password_hash=createPlaceholderPasswordHash(),
                role_id=int(roleObj.role_id),
                is_active=True,
                must_set_password=True,
                recovery_questions_set=False,
                session_version=1,
            )
            db.session.add(userObj)
            db.session.flush()
            rawCode, expiresAt = issueUserToken(userObj.user_id, "setup", 24 * 60, adminId)
            db.session.commit()
            revealCode = rawCode
            revealTitle = f"One-time setup code for {username}"
            revealMeta = f"Expires: {expiresAt.strftime('%d %b %Y %H:%M UTC')}"
            flash("Account created. Give the one-time setup code to the user securely.", "success")

        elif formAction == "issue_reset":
            userIdRaw = request.form.get("user_id") or ""
            userObj = User.query.filter_by(user_id=int(userIdRaw)).first() if str(userIdRaw).isdigit() else None
            if not userObj or not userObj.is_active:
                flash("User not found.", "error")
                return redirect(url_for("manage_users"))
            if userObj.must_set_password or not userObj.recovery_questions_set:
                flash("That account has not completed first-time setup yet, so issue a new setup code instead.", "warning")
                return redirect(url_for("manage_users"))
            rawCode, expiresAt = issueUserToken(userObj.user_id, "reset", 30, adminId)
            db.session.commit()
            revealCode = rawCode
            revealTitle = f"One-time reset code for {userObj.username}"
            revealMeta = f"Expires: {expiresAt.strftime('%d %b %Y %H:%M UTC')}"
            flash("Reset code created. Give it to the user securely.", "success")

        elif formAction == "issue_setup":
            userIdRaw = request.form.get("user_id") or ""
            userObj = User.query.filter_by(user_id=int(userIdRaw)).first() if str(userIdRaw).isdigit() else None
            if not userObj or not userObj.is_active:
                flash("User not found.", "error")
                return redirect(url_for("manage_users"))
            rawCode, expiresAt = issueUserToken(userObj.user_id, "setup", 24 * 60, adminId)
            userObj.must_set_password = True
            db.session.commit()
            revealCode = rawCode
            revealTitle = f"One-time setup code for {userObj.username}"
            revealMeta = f"Expires: {expiresAt.strftime('%d %b %Y %H:%M UTC')}"
            flash("A fresh setup code has been created.", "success")

    roleOptions = Role.query.order_by(Role.role_name.asc()).all()
    userRows = User.query.join(Role, Role.role_id == User.role_id).order_by(User.username.asc()).all()
    return render_template("manage_users.html", roleOptions=roleOptions, userRows=userRows, revealCode=revealCode, revealTitle=revealTitle, revealMeta=revealMeta)


@app.route("/dashboard")
@login_required
def dashboard():
    is_admin = normalizeRoleName(session.get("role_name")) == "admin"
    user_id = int(session.get("user_id"))

    q = (
        db.session.query(FormSubmission, Form, FormVersion, User)
        .join(Form, Form.form_id == FormSubmission.form_id)
        .join(FormVersion, FormVersion.form_version_id == FormSubmission.form_version_id)
        .join(User, User.user_id == FormSubmission.submitted_by)
    )

    if not is_admin:
        q = q.filter(FormSubmission.submitted_by == user_id)

    submissions = q.order_by(FormSubmission.submitted_at.desc(), FormSubmission.submission_id.desc()).all()

    return render_template("dashboard.html", submissions=submissions, is_admin=is_admin)


@app.route("/submission/<int:submission_id>")
@login_required
def view_submission(submission_id: int):
    is_admin = normalizeRoleName(session.get("role_name")) == "admin"
    user_id = int(session.get("user_id"))

    submission = FormSubmission.query.filter_by(submission_id=submission_id).first()
    if not submission:
        flash("Submission not found.", "error")
        return redirect(url_for("dashboard"))

    if not is_admin and int(submission.submitted_by) != user_id:
        flash("You do not have permission to view that submission.", "error")
        return redirect(url_for("dashboard"))

    form_obj = Form.query.filter_by(form_id=submission.form_id).first()
    form_version = FormVersion.query.filter_by(form_version_id=submission.form_version_id).first()

    unsectioned_questions, sections_with_questions = _get_sections_for_version(submission.form_version_id)

    answer_rows = (
        SubmissionAnswer.query.filter_by(submission_id=submission.submission_id)
        .all()
    )

    answers = {}
    for a in answer_rows:
        answers[int(a.question_version_id)] = {
            "text": a.answer_text,
            "number": str(a.answer_number) if a.answer_number is not None else None,
            "option": a.answer_option_value,
            "multi": (a.answer_text or "").splitlines() if a.answer_text else [],
        }

    return render_template(
        "form.html",
        form=form_obj,
        form_version=form_version,
        unsectioned_questions=unsectioned_questions,
        sections_with_questions=sections_with_questions,
        questions=(unsectioned_questions + [q for s in sections_with_questions for q in (s.get("questions") or [])]),
        is_admin=is_admin,
        view_only=True,
        answers=answers,
        submission=submission,
    )


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))


@app.route("/form", methods=["GET", "POST"])
@login_required
def form():
    form_obj, latest_version = _get_active_form_and_latest_version()

    if not form_obj:
        return render_template("form.html", form=None)

    if not latest_version:
        return render_template(
            "form.html",
            form=form_obj,
            form_version=None,
            questions=[],
            is_admin=session.get("role_name") == "admin",
        )

    if request.method == "POST":
        user_id = int(session["user_id"])
        unsectioned_questions, sections_with_questions = _get_sections_for_version(latest_version.form_version_id)
        questions = unsectioned_questions + [q for s in sections_with_questions for q in (s.get("questions") or [])]

        sub = FormSubmission(
            form_id=form_obj.form_id,
            form_version_id=latest_version.form_version_id,
            submitted_by=user_id,
        )
        db.session.add(sub)
        db.session.flush()

        for q in questions:
            field = f"q_{q.question_version_id}"
            raw = request.form.get(field)

            ans = SubmissionAnswer(
                submission_id=sub.submission_id,
                question_version_id=q.question_version_id,
            )

            if q.response_type == "number" or q.response_type == "rating":
                if raw is not None and str(raw).strip() != "":
                    try:
                        ans.answer_number = Decimal(str(raw).strip())
                    except Exception:
                        ans.answer_text = str(raw)
            elif q.response_type == "select":
                if raw is not None and str(raw).strip() != "":
                    ans.answer_option_value = str(raw).strip()
            elif q.response_type == "multi_select":
                vals = request.form.getlist(field)
                if vals:
                    ans.answer_text = "\n".join([str(v).strip() for v in vals if str(v).strip() != ""])
            else:
                if raw is not None and str(raw).strip() != "":
                    ans.answer_text = str(raw)

            db.session.add(ans)

        db.session.commit()
        flash("Form submitted.", "success")
        return redirect(url_for("form"))

    unsectioned_questions, sections_with_questions = _get_sections_for_version(latest_version.form_version_id)

    return render_template(
        "form.html",
        form=form_obj,
        form_version=latest_version,
        unsectioned_questions=unsectioned_questions,
        sections_with_questions=sections_with_questions,
        questions=(unsectioned_questions + [q for s in sections_with_questions for q in (s.get("questions") or [])]),
        is_admin=session.get("role_name") == "admin",
    )


@app.route("/edit-form", methods=["GET", "POST"])
@editor_required
def editform():
    form_obj, latest_version = _get_active_form_and_latest_version()

    if not form_obj:
        flash("No active form available.", "error")
        return redirect(url_for("dashboard"))

    if not latest_version:
        flash("No form version exists yet.", "error")
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        user_id = int(session["user_id"])
        isDeveloper = session.get("role_name") == "developer"
        next_version_number = int(latest_version.version_number) + 1

        formTitle = (request.form.get("form_title") or "").strip()
        formDescription = (request.form.get("form_description") or "").strip()
        if not formTitle:
            formTitle = (latest_version.title or form_obj.title or "").strip() or "Untitled form"

        ordered_items = request.form.getlist("ordered_item")
        if not ordered_items:
            ordered_existing = request.form.getlist("existing_qv_id")
            ordered_items = [f"existing:{x}" for x in ordered_existing if x]
        delete_ids = set(request.form.getlist("delete_qv_id"))
        if session.get("role_name") != "developer":
            filtered = set()
            for x in delete_ids:
                try:
                    qv = QuestionVersion.query.filter_by(question_version_id=int(x)).first()
                    if qv and not qv.is_locked:
                        filtered.add(x)
                except Exception:
                    pass
            delete_ids = filtered

        all_qv_ids = []
        qv_id_map = {}

        label_to_value_for_old_qvid = {}

        for item in ordered_items:
            raw = (item or "").strip()
            if not raw or ":" not in raw:
                continue
            kind, ident = raw.split(":", 1)
            kind = kind.strip()
            ident = ident.strip()

            if kind == "existing":
                if not ident:
                    continue
                if ident in delete_ids:
                    continue

                qv_id = int(ident)
                current_qv = QuestionVersion.query.filter_by(question_version_id=qv_id).first()
                if not current_qv:
                    continue

                new_prompt = (request.form.get(f"existing_prompt_{qv_id}") or "").strip()
                new_type = (request.form.get(f"existing_type_{qv_id}") or "").strip()
                new_required = (request.form.get(f"existing_required_{qv_id}") or "0").strip()
                new_hint = (request.form.get(f"existing_hint_{qv_id}") or "").strip()
                new_desc = (request.form.get(f"existing_desc_{qv_id}") or "").strip()
                new_locked_raw = (request.form.get(f"existing_locked_{qv_id}") or "").strip()
                new_options_text = request.form.get(f"existing_options_{qv_id}") or ""

                if not new_prompt:
                    new_prompt = current_qv.prompt_text

                if new_type not in ("text", "number", "rating", "select", "multi_select"):
                    new_type = current_qv.response_type

                req_bool = (new_required == "1")
                hint_val = new_hint if new_hint else None
                desc_val = new_desc if new_desc else None
                locked_val = (new_locked_raw == "1") if isDeveloper else bool(current_qv.is_locked)

                current_options_lines = []
                if current_qv.response_type in ("select", "multi_select"):
                    for opt in current_qv.options:
                        t = (opt.option_label or "").strip()
                        if t:
                            current_options_lines.append(t)

                new_options_lines = []
                if new_type in ("select", "multi_select"):
                    for line in (new_options_text or "").splitlines():
                        t = line.strip()
                        if t:
                            new_options_lines.append(t)

                changed = False

                if (current_qv.prompt_text or "").strip() != new_prompt:
                    changed = True
                if (current_qv.response_type or "").strip() != new_type:
                    changed = True
                if bool(current_qv.is_required) != req_bool:
                    changed = True
                cur_hint = (current_qv.hint_text or current_qv.help_text or "")
                if (cur_hint or "") != (hint_val or ""):
                    changed = True
                if (current_qv.question_description or "") != (desc_val or ""):
                    changed = True
                if bool(current_qv.is_locked) != bool(locked_val):
                    changed = True
                if new_type in ("select", "multi_select") or current_qv.response_type in ("select", "multi_select"):
                    if current_options_lines != new_options_lines:
                        changed = True

                if not changed:
                    all_qv_ids.append(qv_id)
                    qv_id_map[qv_id] = qv_id
                    if current_qv.response_type in ("select", "multi_select"):
                        m = {}
                        for opt in current_qv.options:
                            lbl = (opt.option_label or "").strip()
                            val = (opt.option_value or "").strip()
                            if lbl:
                                m[lbl] = val if val else lbl
                        label_to_value_for_old_qvid[qv_id] = m
                    else:
                        label_to_value_for_old_qvid[qv_id] = {}
                    continue

                max_ver = (
                    db.session.query(db.func.max(QuestionVersion.version_number))
                    .filter(QuestionVersion.question_id == current_qv.question_id)
                    .scalar()
                )
                next_qv_ver = int(max_ver or 0) + 1

                new_qv = QuestionVersion(
                    question_id=current_qv.question_id,
                    version_number=next_qv_ver,
                    prompt_text=new_prompt,
                    response_type=new_type,
                    is_required=req_bool,
                    hint_text=hint_val,
                    question_description=desc_val,
                    is_locked=locked_val,
                    help_text=None,
                    is_active=True,
                    created_by=user_id,
                )
                db.session.add(new_qv)
                db.session.flush()

                if new_type in ("select", "multi_select"):
                    options_unchanged = (
                        (current_qv.response_type in ("select", "multi_select"))
                        and (current_options_lines == new_options_lines)
                    )

                    if options_unchanged and current_qv.response_type in ("select", "multi_select"):
                        m = {}
                        for opt in current_qv.options:
                            lbl = (opt.option_label or "").strip()
                            val = (opt.option_value or "").strip()
                            if not lbl:
                                continue
                            db.session.add(
                                QuestionVersionOption(
                                    question_version_id=new_qv.question_version_id,
                                    option_value=val if val else lbl,
                                    option_label=lbl,
                                    sort_order=int(opt.sort_order or 0),
                                )
                            )
                            m[lbl] = val if val else lbl
                        label_to_value_for_old_qvid[qv_id] = m
                    else:
                        for idx, label in enumerate(new_options_lines):
                            db.session.add(
                                QuestionVersionOption(
                                    question_version_id=new_qv.question_version_id,
                                    option_value=label,
                                    option_label=label,
                                    sort_order=idx,
                                )
                            )
                        label_to_value_for_old_qvid[qv_id] = {lbl: lbl for lbl in new_options_lines}
                else:
                    label_to_value_for_old_qvid[qv_id] = {}

                all_qv_ids.append(int(new_qv.question_version_id))
                qv_id_map[qv_id] = int(new_qv.question_version_id)

            elif kind == "new":
                key = ident
                prompt = (request.form.get(f"new_prompt_{key}") or "").strip()
                rtype = (request.form.get(f"new_type_{key}") or "").strip()
                req = (request.form.get(f"new_required_{key}") or "0").strip()
                hint_text = (request.form.get(f"new_hint_{key}") or "").strip()
                qdesc = (request.form.get(f"new_desc_{key}") or "").strip()
                new_locked_raw = (request.form.get(f"new_locked_{key}") or "").strip()
                options_text = (request.form.get(f"new_options_{key}") or "")

                if not prompt:
                    continue
                if rtype not in ("text", "number", "rating", "select", "multi_select"):
                    continue

                q = Question(question_key=uuid.uuid4().hex, created_by=user_id)
                db.session.add(q)
                db.session.flush()

                qv = QuestionVersion(
                    question_id=q.question_id,
                    version_number=1,
                    prompt_text=prompt,
                    response_type=rtype,
                    is_required=(req == "1"),
                    hint_text=(hint_text if hint_text else None),
                    question_description=(qdesc if qdesc else None),
                    is_locked=((new_locked_raw == "1") if isDeveloper else False),
                    help_text=None,
                    is_active=True,
                    created_by=user_id,
                )
                db.session.add(qv)
                db.session.flush()

                if rtype in ("select", "multi_select"):
                    lines = []
                    for line in (options_text or "").splitlines():
                        t = line.strip()
                        if t:
                            lines.append(t)
                    for idx, label in enumerate(lines):
                        db.session.add(
                            QuestionVersionOption(
                                question_version_id=qv.question_version_id,
                                option_value=label,
                                option_label=label,
                                sort_order=idx,
                            )
                        )

                all_qv_ids.append(int(qv.question_version_id))
                qv_id_map[key] = int(qv.question_version_id)

        new_fv = FormVersion(
            form_id=form_obj.form_id,
            version_number=next_version_number,
            title=formTitle,
            description=(formDescription if formDescription else None),
            created_by=user_id,
            notes=None,
        )
        db.session.add(new_fv)
        db.session.flush()

        sectionOrder = 0
        currentSectionId = None
        sortCounters = {None: 0}
        sectionIdMap = {}
        all_set = set(int(x) for x in all_qv_ids)

        for item in ordered_items:
            raw = (item or "").strip()
            if not raw or ":" not in raw:
                continue
            kind, ident = raw.split(":", 1)
            kind = kind.strip()
            ident = ident.strip()

            if kind == "section":
                title = (request.form.get(f"section_title_{ident}") or "").strip()
                desc = (request.form.get(f"section_desc_{ident}") or "").strip()
                if not title:
                    currentSectionId = None
                    continue
                sec = FormVersionSection(
                    form_version_id=new_fv.form_version_id,
                    title=title,
                    description=(desc if desc else None),
                    sort_order=sectionOrder,
                )
                db.session.add(sec)
                db.session.flush()
                currentSectionId = int(sec.section_id)
                sectionIdMap[ident] = currentSectionId
                sortCounters[currentSectionId] = 0
                sectionOrder += 1
                continue

            if kind == "existing":
                if not ident or ident in delete_ids:
                    continue
                oldId = int(ident)
                newId = int(qv_id_map.get(oldId, oldId))
                if newId not in all_set:
                    continue
                so = sortCounters.get(currentSectionId, 0)
                db.session.add(
                    FormVersionQuestion(
                        form_version_id=new_fv.form_version_id,
                        question_version_id=newId,
                        section_id=currentSectionId,
                        sort_order=so,
                    )
                )
                sortCounters[currentSectionId] = so + 1
                continue

            if kind == "new":
                key = ident
                if key not in qv_id_map:
                    continue
                newId = int(qv_id_map.get(key))
                if newId not in all_set:
                    continue
                so = sortCounters.get(currentSectionId, 0)
                db.session.add(
                    FormVersionQuestion(
                        form_version_id=new_fv.form_version_id,
                        question_version_id=newId,
                        section_id=currentSectionId,
                        sort_order=so,
                    )
                )
                sortCounters[currentSectionId] = so + 1
                continue

        branch_state_sources = request.form.getlist("branch_state_source")
        branch_state_enableds = request.form.getlist("branch_state_enabled")

        branch_state = {}
        for i in range(max(len(branch_state_sources), len(branch_state_enableds))):
            s = (branch_state_sources[i] if i < len(branch_state_sources) else "").strip()
            e = (branch_state_enableds[i] if i < len(branch_state_enableds) else "").strip()
            if not s:
                continue
            try:
                branch_state[int(s)] = (e == "1")
            except ValueError:
                continue

        map_sources = request.form.getlist("branch_map_source")
        map_options = request.form.getlist("branch_map_option")
        map_targets = request.form.getlist("branch_map_target")

        submitted_has_maps = any((s or "").strip() for s in map_sources)

        used_sources = set()
        if submitted_has_maps:
            m = max(len(map_sources), len(map_options), len(map_targets))
            per_source = {}
            for i in range(m):
                src_raw = (map_sources[i] if i < len(map_sources) else "").strip()
                opt_raw = (map_options[i] if i < len(map_options) else "").strip()
                tgt_raw = (map_targets[i] if i < len(map_targets) else "").strip()
                if not src_raw:
                    continue
                try:
                    src_old = int(src_raw)
                except ValueError:
                    continue
                if src_old in branch_state and not branch_state.get(src_old):
                    continue
                used_sources.add(src_old)
                if not tgt_raw or not opt_raw:
                    continue
                try:
                    tgt_old = int(tgt_raw)
                except ValueError:
                    continue
                per_source.setdefault(src_old, []).append((opt_raw, tgt_old))

            for src_old, pairs in per_source.items():
                src = int(qv_id_map.get(src_old, src_old))
                if src not in all_set:
                    continue
                pr = 0
                for opt_label, tgt_old in pairs:
                    opt_val = label_to_value_for_old_qvid.get(src_old, {}).get(opt_label, opt_label)
                    tgt = int(qv_id_map.get(int(tgt_old), int(tgt_old)))
                    if tgt not in all_set:
                        continue
                    db.session.add(
                        FormQuestionBranching(
                            form_version_id=new_fv.form_version_id,
                            source_question_version_id=src,
                            target_question_version_id=tgt,
                            operator="equals",
                            compare_option_value=opt_val,
                            compare_text=None,
                            compare_number=None,
                            action="show",
                            priority=pr,
                        )
                    )
                    pr += 1

        old_show = (
            FormQuestionBranching.query
            .filter(
                FormQuestionBranching.form_version_id == latest_version.form_version_id,
                FormQuestionBranching.action == "show",
            )
            .order_by(FormQuestionBranching.priority.asc(), FormQuestionBranching.branching_id.asc())
            .all()
        )
        for b in old_show:
            src_old = int(b.source_question_version_id)
            if src_old in branch_state and not branch_state.get(src_old):
                continue
            if submitted_has_maps and src_old in used_sources:
                continue

            src = int(qv_id_map.get(src_old, src_old))
            tgt_old = int(b.target_question_version_id)
            tgt = int(qv_id_map.get(tgt_old, tgt_old))

            if src not in all_set or tgt not in all_set:
                continue

            cov = (b.compare_option_value or "").strip()
            if not cov:
                continue

            db.session.add(
                FormQuestionBranching(
                    form_version_id=new_fv.form_version_id,
                    source_question_version_id=src,
                    target_question_version_id=tgt,
                    operator="equals",
                    compare_option_value=cov,
                    compare_text=None,
                    compare_number=None,
                    action="show",
                    priority=int(b.priority or 0),
                )
            )
        form_obj.title = formTitle
        form_obj.description = (formDescription if formDescription else None)
        db.session.commit()
        flash(f"Form updated. New version: {next_version_number}", "success")
        return redirect(url_for("form"))

    unsectioned_questions, sections_with_questions = _get_sections_for_version(latest_version.form_version_id)
    questions = unsectioned_questions + [q for s in sections_with_questions for q in (s.get("questions") or [])]

    value_to_label_by_qvid = {}
    for q in questions:
        qid = int(q.question_version_id)
        if q.response_type in ("select", "multi_select"):
            m = {}
            for opt in q.options:
                v = (opt.option_value or "").strip()
                lbl = (opt.option_label or "").strip()
                if v and lbl:
                    m[v] = lbl
            value_to_label_by_qvid[qid] = m
        else:
            value_to_label_by_qvid[qid] = {}

    branches = (
        FormQuestionBranching.query
        .filter(
            FormQuestionBranching.form_version_id == latest_version.form_version_id,
            FormQuestionBranching.action == "show",
        )
        .order_by(FormQuestionBranching.priority.asc(), FormQuestionBranching.branching_id.asc())
        .all()
    )

    branch_maps = {}
    for b in branches:
        src = int(b.source_question_version_id)
        cov = (b.compare_option_value or "").strip()
        if not cov:
            continue
        lbl = value_to_label_by_qvid.get(src, {}).get(cov, cov)
        if src not in branch_maps:
            branch_maps[src] = {}
        branch_maps[src][lbl] = int(b.target_question_version_id)

    return render_template(
        "editform.html",
        form=form_obj,
        form_version=latest_version,
        questions=questions,
        unsectioned_questions=unsectioned_questions,
        sections_with_questions=sections_with_questions,
        is_developer=(session.get("role_name") == "developer"),
        branch_maps=branch_maps,
    )


@app.route("/stats", methods=["GET", "POST"])
@stats_required
def stats():
    formObj = Form.query.filter_by(is_active=True).order_by(Form.form_id.desc()).first()
    if not formObj:
        return render_template(
            "stats.html",
            statsReady=False,
            canEditStats=(session.get("role_name") in ("admin", "developer")),
            isDeveloper=(session.get("role_name") == "developer"),
            trackedQuestionKeys=[],
            candidateQuestions=[],
            versionFilters=[],
            selectedFormVersionIds=[],
        )

    formVersions = (
        FormVersion.query
        .filter_by(form_id=formObj.form_id)
        .order_by(FormVersion.version_number.asc(), FormVersion.form_version_id.asc())
        .all()
    )
    if not formVersions:
        return render_template(
            "stats.html",
            statsReady=False,
            canEditStats=(session.get("role_name") in ("admin", "developer")),
            isDeveloper=(session.get("role_name") == "developer"),
            trackedQuestionKeys=[],
            candidateQuestions=[],
            versionFilters=[],
            selectedFormVersionIds=[],
        )

    versionById = {int(item.form_version_id): item for item in formVersions}
    latestVersion = formVersions[-1]

    allFormLinks = (
        db.session.query(FormVersionQuestion, QuestionVersion)
        .join(QuestionVersion, FormVersionQuestion.question_version_id == QuestionVersion.question_version_id)
        .filter(FormVersionQuestion.form_version_id.in_(list(versionById.keys())))
        .order_by(FormVersionQuestion.form_version_id.asc(), FormVersionQuestion.sort_order.asc(), FormVersionQuestion.form_version_question_id.asc())
        .all()
    )

    questionById = {}
    optionLabelByQuestion = {}
    latestQuestionKeySet = set()
    latestQuestionKeyById = {}
    subjectQuestionIds = []
    supervisorQuestionIds = []
    teamQuestionIds = []
    feedbackQuestionIds = []
    candidateQuestionMap = {}

    for formVersionQuestion, questionVersion in allFormLinks:
        qid = int(questionVersion.question_version_id)
        questionById[qid] = questionVersion
        optionMap = {}
        for option in questionVersion.options:
            optionMap[normalizeStatsText(option.option_value)] = normalizeStatsText(option.option_label) or normalizeStatsText(option.option_value)
        optionLabelByQuestion[qid] = optionMap

        promptText = normalizeStatsText(questionVersion.prompt_text)
        promptKey = normalizeStatsKey(promptText)

        if ("staff member" in promptKey or "member of staff" in promptKey or "requiring feedback" in promptKey) and "supervisor" not in promptKey:
            subjectQuestionIds.append(qid)
        if "supervisor" in promptKey and "email" not in promptKey:
            supervisorQuestionIds.append(qid)
        if "team" in promptKey:
            teamQuestionIds.append(qid)
        if "comment" in promptKey or "feedback" in promptKey:
            feedbackQuestionIds.append(qid)

        isCandidate = questionVersion.response_type in ("select", "multi_select", "rating") and not isIdentityPrompt(promptText)
        if isCandidate and promptKey not in candidateQuestionMap:
            candidateQuestionMap[promptKey] = {
                "questionKey": promptKey,
                "promptText": promptText,
                "responseType": questionVersion.response_type,
            }

        if int(formVersionQuestion.form_version_id) == int(latestVersion.form_version_id):
            latestQuestionKeyById[qid] = promptKey
            latestQuestionKeySet.add(promptKey)

    candidateQuestions = sorted(candidateQuestionMap.values(), key=lambda item: item["promptText"].lower())

    statsState = getStatsState()
    trackedQuestionKeys = [str(x) for x in statsState.get("trackedQuestionKeys", []) if str(x).strip() != ""]
    if not trackedQuestionKeys:
        legacyTrackedIds = [int(x) for x in statsState.get("trackedQuestionVersionIds", []) if str(x).isdigit()]
        for qid in legacyTrackedIds:
            promptKey = latestQuestionKeyById.get(int(qid))
            if promptKey and promptKey not in trackedQuestionKeys:
                trackedQuestionKeys.append(promptKey)

    if request.method == "POST" and session.get("role_name") in ("admin", "developer"):
        selectedKeys = request.form.getlist("trackedQuestionKeys")
        trackedQuestionKeys = [str(x) for x in selectedKeys if str(x).strip() != ""]
        trackedQuestionVersionIds = [qid for qid, promptKey in latestQuestionKeyById.items() if promptKey in trackedQuestionKeys]
        setStatsState(trackedQuestionKeys, trackedQuestionVersionIds)
        flash("Stats tracked questions updated.", "success")
        return redirect(url_for("stats", versions=request.form.getlist("versions")))

    if not trackedQuestionKeys:
        trackedQuestionKeys = [item["questionKey"] for item in candidateQuestions]

    selectedFormVersionIds = []
    for value in request.args.getlist("versions"):
        if str(value).isdigit() and int(value) in versionById:
            selectedFormVersionIds.append(int(value))
    if not selectedFormVersionIds:
        selectedFormVersionIds = [int(item.form_version_id) for item in formVersions]

    versionFilters = []
    for item in sorted(formVersions, key=lambda value: (int(value.version_number), int(value.form_version_id)), reverse=True):
        versionTitle = normalizeStatsText(item.title) or normalizeStatsText(formObj.title) or "Untitled form"
        versionFilters.append({
            "formVersionId": int(item.form_version_id),
            "versionNumber": int(item.version_number),
            "title": versionTitle,
            "isSelected": int(item.form_version_id) in selectedFormVersionIds,
        })

    submissions = (
        FormSubmission.query
        .filter(FormSubmission.form_id == formObj.form_id)
        .filter(FormSubmission.form_version_id.in_(selectedFormVersionIds))
        .order_by(FormSubmission.submitted_at.asc(), FormSubmission.submission_id.asc())
        .all()
    )
    submissionIds = [int(sub.submission_id) for sub in submissions]
    answers = []
    if submissionIds:
        answers = (
            SubmissionAnswer.query
            .filter(SubmissionAnswer.submission_id.in_(submissionIds))
            .all()
        )

    answersBySubmission = defaultdict(list)
    for answer in answers:
        answersBySubmission[int(answer.submission_id)].append(answer)

    staffCounter = Counter()
    issueCounter = Counter()
    issueByMonthCounter = Counter()
    submissionByMonthCounter = Counter()
    teamCounter = Counter()
    teamIssueCounter = defaultdict(Counter)
    supervisorCounter = Counter()
    supervisorIssueCounter = defaultdict(Counter)
    staffIssueCounter = defaultdict(Counter)
    staffSupervisorMap = {}
    recentFeedback = []

    trackedQuestionKeySet = set(trackedQuestionKeys)

    for submission in submissions:
        submissionMonthKey = monthKeyFromDate(submission.submitted_at)
        if submissionMonthKey:
            submissionByMonthCounter[submissionMonthKey] += 1
        submissionAnswers = answersBySubmission.get(int(submission.submission_id), [])
        subjectName = "Unknown"
        supervisorName = "Unknown"
        teamValues = []
        feedbackText = None

        for answer in submissionAnswers:
            qid = int(answer.question_version_id)
            if qid not in questionById:
                continue
            questionVersion = questionById[qid]
            promptText = normalizeStatsText(questionVersion.prompt_text)
            promptKey = normalizeStatsKey(promptText)
            answerLabels = []
            if answer.answer_option_value is not None:
                optionValue = normalizeStatsText(answer.answer_option_value)
                answerLabels.append(optionLabelByQuestion.get(qid, {}).get(optionValue, optionValue))
            elif answer.answer_text is not None:
                if questionVersion.response_type == "multi_select":
                    answerLabels.extend([normalizeStatsText(value) for value in str(answer.answer_text).splitlines() if normalizeStatsText(value) != ""])
                else:
                    answerLabels.append(normalizeStatsText(answer.answer_text))
            elif answer.answer_number is not None:
                numberText = str(answer.answer_number)
                if isinstance(answer.answer_number, Decimal) and answer.answer_number == answer.answer_number.to_integral():
                    numberText = str(int(answer.answer_number))
                answerLabels.append(numberText)

            if qid in subjectQuestionIds and answerLabels:
                subjectName = answerLabels[0]
            if qid in supervisorQuestionIds and answerLabels:
                supervisorName = answerLabels[0]
            if qid in teamQuestionIds and answerLabels:
                teamValues.extend(answerLabels)
            if qid in feedbackQuestionIds and answerLabels and not feedbackText:
                feedbackText = answerLabels[0]

            if promptKey not in trackedQuestionKeySet:
                continue
            for answerLabel in answerLabels:
                if not answerLooksLikeIssue(promptText, answerLabel):
                    continue
                issueLabel = f"{promptText}: {answerLabel}"
                issueCounter[issueLabel] += 1
                if submissionMonthKey:
                    issueByMonthCounter[submissionMonthKey] += 1
                staffIssueCounter[subjectName][issueLabel] += 1
                if teamValues:
                    for teamValue in teamValues:
                        teamIssueCounter[teamValue][issueLabel] += 1
                else:
                    teamIssueCounter["Unknown"][issueLabel] += 1
                supervisorIssueCounter[supervisorName][issueLabel] += 1

        staffCounter[subjectName] += 1
        supervisorCounter[supervisorName] += 1
        staffSupervisorMap[subjectName] = supervisorName
        if teamValues:
            for teamValue in teamValues:
                teamCounter[teamValue] += 1
        else:
            teamCounter["Unknown"] += 1

        currentVersion = versionById.get(int(submission.form_version_id))
        versionText = f"Version {int(currentVersion.version_number)}" if currentVersion else "Unknown version"
        recentFeedback.append({
            "submittedAt": submission.submitted_at,
            "staffName": subjectName,
            "supervisorName": supervisorName,
            "feedbackText": feedbackText or "No comment recorded",
            "versionText": versionText,
        })

    topStaff = staffCounter.most_common(10)
    topIssues = issueCounter.most_common(10)
    topTeams = teamCounter.most_common(10)
    topSupervisors = supervisorCounter.most_common(10)

    staffTable = []
    for staffName, count in staffCounter.most_common(15):
        staffTable.append({
            "staffName": staffName,
            "submissionCount": count,
            "supervisorName": staffSupervisorMap.get(staffName, "Unknown"),
            "topIssue": buildIssueSummary(staffIssueCounter.get(staffName, Counter()).most_common(1)),
        })

    teamTable = []
    for teamName, count in teamCounter.most_common(15):
        teamTable.append({
            "teamName": teamName,
            "submissionCount": count,
            "topIssue": buildIssueSummary(teamIssueCounter.get(teamName, Counter()).most_common(1)),
        })

    supervisorTable = []
    for supervisorName, count in supervisorCounter.most_common(15):
        supervisorTable.append({
            "supervisorName": supervisorName,
            "submissionCount": count,
            "topIssue": buildIssueSummary(supervisorIssueCounter.get(supervisorName, Counter()).most_common(1)),
        })

    allMonthKeys = sorted(set(list(submissionByMonthCounter.keys()) + list(issueByMonthCounter.keys())))
    monthLabels = [monthLabelFromKey(value) for value in allMonthKeys]
    submissionTrendData = [submissionByMonthCounter.get(value, 0) for value in allMonthKeys]
    issueTrendData = [issueByMonthCounter.get(value, 0) for value in allMonthKeys]

    nowDate = datetime.utcnow()
    recentWindowStart = nowDate - timedelta(days=30)
    previousWindowStart = nowDate - timedelta(days=60)
    recentIssues = 0
    previousIssues = 0
    recentSubmissions = 0
    previousSubmissions = 0
    for submission in submissions:
        submissionDate = submission.submitted_at or nowDate
        issueCountForSubmission = 0
        for answer in answersBySubmission.get(int(submission.submission_id), []):
            qid = int(answer.question_version_id)
            if qid not in questionById:
                continue
            questionVersion = questionById[qid]
            promptText = normalizeStatsText(questionVersion.prompt_text)
            promptKey = normalizeStatsKey(promptText)
            if promptKey not in trackedQuestionKeySet:
                continue
            answerValues = []
            if answer.answer_option_value is not None:
                optionValue = normalizeStatsText(answer.answer_option_value)
                answerValues.append(optionLabelByQuestion.get(qid, {}).get(optionValue, optionValue))
            elif answer.answer_text is not None:
                if questionVersion.response_type == "multi_select":
                    answerValues.extend([normalizeStatsText(value) for value in str(answer.answer_text).splitlines() if normalizeStatsText(value) != ""])
                else:
                    answerValues.append(normalizeStatsText(answer.answer_text))
            elif answer.answer_number is not None:
                answerValues.append(str(answer.answer_number))
            for answerValue in answerValues:
                if answerLooksLikeIssue(promptText, answerValue):
                    issueCountForSubmission += 1
        if submissionDate >= recentWindowStart:
            recentSubmissions += 1
            recentIssues += issueCountForSubmission
        elif submissionDate >= previousWindowStart:
            previousSubmissions += 1
            previousIssues += issueCountForSubmission

    alertItems = []
    if topIssues:
        alertItems.append(f"Most common issue right now is {topIssues[0][0]} ({topIssues[0][1]}).")
    if topStaff:
        alertItems.append(f"{topStaff[0][0]} has the most forms submitted about them ({topStaff[0][1]}).")
    if topTeams:
        alertItems.append(f"{topTeams[0][0]} currently has the highest feedback volume ({topTeams[0][1]}).")
    if recentIssues > previousIssues:
        alertItems.append(f"Issue volume has increased in the last 30 days ({recentIssues} vs {previousIssues}).")
    elif recentIssues < previousIssues:
        alertItems.append(f"Issue volume has reduced in the last 30 days ({recentIssues} vs {previousIssues}).")
    else:
        alertItems.append(f"Issue volume is unchanged across the last two 30 day windows ({recentIssues}).")

    summaryCards = [
        {"label": "Total submissions", "value": len(submissions)},
        {"label": "Unique staff members", "value": len([name for name in staffCounter.keys() if normalizeStatsKey(name) != "unknown"])},
        {"label": "Most common issue", "value": topIssues[0][0] if topIssues else "No issue data yet"},
        {"label": "Most submitted about", "value": topStaff[0][0] if topStaff else "No data yet"},
        {"label": "Highest volume team", "value": topTeams[0][0] if topTeams else "No data yet"},
    ]

    chartData = {
        "staffLabels": [name for name, _ in topStaff],
        "staffValues": [count for _, count in topStaff],
        "issueLabels": [name for name, _ in topIssues],
        "issueValues": [count for _, count in topIssues],
        "trendLabels": monthLabels,
        "submissionTrendValues": submissionTrendData,
        "issueTrendValues": issueTrendData,
    }

    recentFeedback = sorted(recentFeedback, key=lambda item: item["submittedAt"] or nowDate, reverse=True)[:10]
    for item in recentFeedback:
        if item["submittedAt"]:
            item["submittedAtText"] = item["submittedAt"].strftime("%d/%m/%Y %H:%M")
        else:
            item["submittedAtText"] = "Unknown"

    return render_template(
        "stats.html",
        statsReady=True,
        canEditStats=(session.get("role_name") in ("admin", "developer")),
        isDeveloper=(session.get("role_name") == "developer"),
        trackedQuestionKeys=trackedQuestionKeys,
        candidateQuestions=candidateQuestions,
        summaryCards=summaryCards,
        chartData=chartData,
        topIssues=topIssues,
        topStaff=topStaff,
        teamTable=teamTable,
        supervisorTable=supervisorTable,
        staffTable=staffTable,
        recentFeedback=recentFeedback,
        alertItems=alertItems,
        versionFilters=versionFilters,
        selectedFormVersionIds=selectedFormVersionIds,
    )

if __name__ == "__main__":
    app.run(debug=True)