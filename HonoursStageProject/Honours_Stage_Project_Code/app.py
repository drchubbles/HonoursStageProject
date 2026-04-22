#In the interest of transparency, I am putting the sources where I got teh coding guidance from.
# No code unless explicitly stated is copied off of the internet but resources were used for structuring the code.
# teh  following links are what I used for developing this code and what inspired teh structure
# teh  first video that was watched on pyflask that inspired the project is: https://youtu.be/Z1RJmh_OqeA
# this project is what layed teh ground work for code structure and how pyflask could be utalised.

# Additional  implementation inspiration also came from practical YouTube walkthroughs adn conference talks viewed during development for guidance:
# Microsoft Graph adn Mail API walkthrough: https://www.youtube.com/watch?v=L-gm25wusIQ
# Microsoft  Graph API introduction walkthrough: https://www.youtube.com/watch?v=TjqrXW5N8HM
# Corey  Schafer Flask tutorila Playlist: https://www.youtube.com/playlist?list=PL-osiE80TeTs4UjLw5MM6OjgkjFeUxCYH
# FlaskCon / Pallets ecosystem talk (general Flask ecosystem awareness): https://www.youtube.com/watch?v=TYeMf0bCbr8

# This section imports the libraries and shared services used across the app.
# Teh  structure and patterns used in this file were informed by teh official documentation for teh main frameworks adn libraries used here:
# Flask Quickstart (application setup, routing, requests, responses, sessions, and URL building): https://flask.palletsprojects.com/en/stable/quickstart/
# Flask View Decorators pattern (used as inspiration fro login/admin/developer/editor rote protection wrappers): https://flask.palletsprojects.com/en/stable/patterns/viewdecorators/
# Flask  Uploading Files pattern (used as inspiration fro secure file upload handling): https://flask.palletsprojects.com/en/stable/patterns/fileuploads/
# Flask  Message Flashing pattern (used as inspiration for success, warning, adn error feedback messages): https://flask.palletsprojects.com/en/stable/patterns/flashing/
# flask templates guidance (used sa inspiration For rendering templates and passing context into pages): https://flask.palletsprojects.com/en/stable/tutorial/templates/
# Flask-SQLAlchemy  Quickstart (used as inspiration fro application/database integration): https://flask-sqlalchemy.readthedocs.io/en/stable/quickstart/
# SQLAlchemy ORM Basic Relationship Patterns (used as inspiration for model relationships such as Role, Uers, QuestionVersion, and QuestionVersionOption): https://docs.sqlalchemy.org/en/20/orm/basic_relationships.html
# Werkzeug  security utilities (used As inspiration for password hashing/checking adn Secire filename handling): https://werkzeug.palletsprojects.com/en/stable/utils/#module-werkzeug.security
# Microsoft  graph auth concepts and sendMail documentation were asol used Where teh email-delivery integration was deisgned:
# https://learn.microsoft.com/en-us/graph/auth/auth-concepts
# https://learn.microsoft.com/en-us/graph/api/user-sendmail?view=graph-rest-1.0

# this  Section imports teh libraries and shared services used across the app
#In the interest of transparency, I am putting the sources where I got teh coding guidance from.
# No code unless explicitly stated is copied off of the internet but resources were used for structuring the code.
# teh  following links are what I used for developing this code and what inspired teh structure
# teh  first video that was watched on pyflask that inspired the project is: https://youtu.be/Z1RJmh_OqeA
# this project is what layed teh ground work for code structure and how pyflask could be utalised.

# Additional  implementation inspiration also came from practical YouTube walkthroughs adn conference talks viewed during development for guidance:
# Microsoft Graph and Mail API walkthrough: https://www.youtube.com/watch?v=L-gm25wusIQ
# Microsoft  Graph API introduction walkthrough: https://www.youtube.com/watch?v=TjqrXW5N8HM
# Corey  Schafer Flask tutorila Playlist: https://www.youtube.com/playlist?list=PL-osiE80TeTs4UjLw5MM6OjgkjFeUxCYH
# FlaskCon / Pallets ecosystem talk (general Flask ecosystem awareness): https://www.youtube.com/watch?v=TYeMf0bCbr8

# this section imports the libraries and shared services used across the app.
# Teh  structure and patterns used in this file were informed by teh official documentation for teh main frameworks adn libraries used here:
# Flask Quickstart (application setup, routing, requests, responses, sessions, and URL building): https://flask.palletsprojects.com/en/stable/quickstart/
# Flask View Decorators pattern (used as inspiration fro login/admin/developer/editor rote protection wrappers): https://flask.palletsprojects.com/en/stable/patterns/viewdecorators/
# Flask  Uploading Files pattern (used as inspiration fro secure file upload handling): https://flask.palletsprojects.com/en/stable/patterns/fileuploads/
# Flask  Message Flashing pattern (used as inspiration for success, warning, adn error feedback messages): https://flask.palletsprojects.com/en/stable/patterns/flashing/
# flask templates guidance (used sa inspiration For rendering templates and passing context into pages): https://flask.palletsprojects.com/en/stable/tutorial/templates/
# Flask-SQLAlchemy  Quickstart (used as inspiration fro application/database integration): https://flask-sqlalchemy.readthedocs.io/en/stable/quickstart/
# SQLAlchemy ORM Basic Relationship Patterns (used as inspiration for model relationships such as Role, Uers, QuestionVersion, and QuestionVersionOption): https://docs.sqlalchemy.org/en/20/orm/basic_relationships.html
# Werkzeug  security utilities (used As inspiration for password hashing/checking adn Secire filename handling): https://werkzeug.palletsprojects.com/en/stable/utils/#module-werkzeug.security
# Microsoft  graph auth concepts and sendMail documentation were asol used Where teh email-delivery integration was deisgned:
# https://learn.microsoft.com/en-us/graph/auth/auth-concepts
# https://learn.microsoft.com/en-us/graph/api/user-sendmail?view=graph-rest-1.0
from __future__ import annotations
import os
import uuid
import json
import re
import secrets
import random
import hashlib
from collections import Counter, defaultdict
from email_delivery import EmailDeliveryServiceFactory, EmailDeliveryResult
from local_summary import LocalSubmissionSummaryServiceFactory
from functools import wraps
from decimal import Decimal
from datetime import datetime, timedelta
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from config import Config


# this  Section creates teh Flask app and shared defaults used across requests
# Do not change this If unsure what it will do!!! it WILL destroy teh code
app = Flask(__name__)


# This section stortes the reusable security questions and reporting defaults used across the form system, more can be added here if you want to add more.
# Please  note that this does NOT make teh questions insecure as teh answers are stored in a secure database
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

# this  Function normalizes role names so permission checks stay consistent, Added due to permissions messing ip previously so was necisarry to ensure proper security so opeopel could only acces what tehy were usppsoed to
def normaliseRoleName(value):
    return (str(value or "").strip().lower())

# This function trims adn tidies credential text before it si saved or compared. 
# this  makes signing in easier for teh user by ignoring accidental extra spaces
def normaliseCredentialText(value):
    return re.sub(r"\s+", " ", str(value or "")).strip()


# This function standardises security answers before they are checked so that if a user capitalises their answer it doesnt matter.
def normaliseSecurityAnswer(value):
    return normaliseCredentialText(value).lower()


# this  Function creates a one time code fro account setup and reset workflows. this allows for secure creation and security of accounts without emailing sign up links
def buildOneTimeCode():
    alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
    return "-".join("".join(secrets.choice(alphabet) for _ in range(5)) for _ in range(4))


# this  Function builds a placeholder password hash for accounts that still need setup
def createPlaceholderPasswordHash():
    return generate_password_hash(secrets.token_urlsafe(32))


# This function returns the security questions in a key-to-label format.
def getSecurityQuestionMap():
    return {item["key"]: item["text"] for item in securityQuestions}


# This function checks whether a submitted password meets the app rules.
def passwordMeetsRules(passwordText):
    return len(passwordText or "") >= 8


# this  Function issues a fresh setup or reset token for a user account
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


# This function finds the newest valid token that matches a supplied code.
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


# This function clears any in-progress password reset data from the session.
def clearPendingResetSession():
    for key in ("pendingResetUserId", "pendingResetTokenId", "pendingResetQuestionIds"):
        session.pop(key, None)


# this  Function makes sure teh branding storage files and folders exist before use
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


# this  Function reads the saved branding state from disk
def getBrandingState():
    brandingStatePath = ensureBrandingState()
    with open(brandingStatePath, "r", encoding="utf-8") as f:
        return json.load(f)


# This function writes the saved branding state back to disk.
def setBrandingState(logoFilename: str | None):
    brandingStatePath = ensureBrandingState()
    with open(brandingStatePath, "w", encoding="utf-8") as f:
        f.write(json.dumps({"logoFilename": logoFilename}, indent=2))


# this  Function checks whether an uploaded logo file type is allowed
def allowedLogo(filename: str) -> bool:
    if "." not in filename:
        return False
    ext = filename.rsplit(".", 1)[1].lower()
    allowed = app.config.get("ALLOWED_LOGO_EXTENSIONS", set())
    return ext in allowed


# This section defines the default stats panels and summary cards shown on the stats page.
DEFAULT_VISIBLE_STATS_SECTIONS = [
    "trainingAlerts",
    "trackedQuestions",
    "staffChart",
    "issueChart",
    "trendChart",
    "topIssuesTable",
    "staffTable",
    "teamTable",
    "supervisorTable",
    "recentFeedback",
]

DEFAULT_VISIBLE_SUMMARY_CARD_KEYS = [
    "totalSubmissions",
    "submittedToday",
    "submittedThisWeek",
    "submittedThisMonth",
    "uniqueStaffMembers",
    "mostCommonIssue",
    "mostSubmittedAbout",
    "highestVolumeTeam",
]

CUSTOM_MONITOR_MEASURE_OPTIONS = [
    {"key": "answeredCount", "label": "Answered submissions"},
    {"key": "yesCount", "label": "Yes answers"},
    {"key": "noCount", "label": "No answers"},
    {"key": "mostCommonAnswer", "label": "Most common answer"},
    {"key": "uniqueAnswers", "label": "Unique answers"},
]


# this  Function makes sure the stats configuration file exists and is valid
def ensureStatsState():
    statsStatePath = app.config.get("STATS_STATE_PATH")
    if not statsStatePath:
        statsStatePath = os.path.join(app.root_path, "statsConfig.json")
    statsStateFolder = os.path.dirname(statsStatePath)
    if statsStateFolder:
        os.makedirs(statsStateFolder, exist_ok=True)
    if not os.path.exists(statsStatePath):
        with open(statsStatePath, "w", encoding="utf-8") as f:
            f.write(json.dumps({
                "trackedQuestionKeys": [],
                "trackedQuestionVersionIds": [],
                "visibleSectionKeys": list(DEFAULT_VISIBLE_STATS_SECTIONS),
                "visibleSummaryCardKeys": list(DEFAULT_VISIBLE_SUMMARY_CARD_KEYS),
                "customMonitorItems": [],
            }, indent=2))
    return statsStatePath


# this  Function reads teh saved stats configuration from disk
def getStatsState():
    statsStatePath = ensureStatsState()
    with open(statsStatePath, "r", encoding="utf-8") as f:
        try:
            state = json.load(f)
        except json.JSONDecodeError:
            state = {
                "trackedQuestionKeys": [],
                "trackedQuestionVersionIds": [],
                "visibleSectionKeys": list(DEFAULT_VISIBLE_STATS_SECTIONS),
                "visibleSummaryCardKeys": list(DEFAULT_VISIBLE_SUMMARY_CARD_KEYS),
                "customMonitorItems": [],
            }
    if "trackedQuestionVersionIds" not in state or not isinstance(state.get("trackedQuestionVersionIds"), list):
        state["trackedQuestionVersionIds"] = []
    if "trackedQuestionKeys" not in state or not isinstance(state.get("trackedQuestionKeys"), list):
        state["trackedQuestionKeys"] = []
    if "visibleSectionKeys" not in state or not isinstance(state.get("visibleSectionKeys"), list):
        state["visibleSectionKeys"] = list(DEFAULT_VISIBLE_STATS_SECTIONS)
    if "visibleSummaryCardKeys" not in state or not isinstance(state.get("visibleSummaryCardKeys"), list):
        state["visibleSummaryCardKeys"] = list(DEFAULT_VISIBLE_SUMMARY_CARD_KEYS)
    if "customMonitorItems" not in state or not isinstance(state.get("customMonitorItems"), list):
        state["customMonitorItems"] = []
    return state


# this function writes the saved stats configuration back to disk.
def setStatsState(trackedQuestionKeys, trackedQuestionVersionIds=None, visibleSectionKeys=None, visibleSummaryCardKeys=None, customMonitorItems=None):
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
    allowedSections = set(DEFAULT_VISIBLE_STATS_SECTIONS)
    cleanVisibleSections = []
    for value in visibleSectionKeys or []:
        valueText = str(value).strip()
        if valueText and valueText in allowedSections and valueText not in cleanVisibleSections:
            cleanVisibleSections.append(valueText)
    if not cleanVisibleSections:
        cleanVisibleSections = list(DEFAULT_VISIBLE_STATS_SECTIONS)
    allowedCards = set(DEFAULT_VISIBLE_SUMMARY_CARD_KEYS)
    cleanVisibleSummaryCards = []
    for value in visibleSummaryCardKeys or []:
        valueText = str(value).strip()
        if valueText and valueText in allowedCards and valueText not in cleanVisibleSummaryCards:
            cleanVisibleSummaryCards.append(valueText)
    if not cleanVisibleSummaryCards:
        cleanVisibleSummaryCards = list(DEFAULT_VISIBLE_SUMMARY_CARD_KEYS)
    with open(statsStatePath, "w", encoding="utf-8") as f:
        f.write(json.dumps({
            "trackedQuestionKeys": cleanKeys,
            "trackedQuestionVersionIds": cleanIds,
            "visibleSectionKeys": cleanVisibleSections,
            "visibleSummaryCardKeys": cleanVisibleSummaryCards,
            "customMonitorItems": customMonitorItems or [],
        }, indent=2))


# This decorator restricts a route to users who can access the stats page.
def statsRequired(view_func):
    @wraps(view_func)
    def wrapper(*args, **kwargs):
        if not session.get("user_id"):
            return redirect(url_for("index"))
        if not currentUserHasRole("admin", "developer"):
            flash("Stats access requires admin or developer permissions.", "error")
            return redirect(url_for("dashboard"))
        return view_func(*args, **kwargs)
    return wrapper


# this  Function tidies stats text values before they are compared or displayed
def normaliseStatsText(value):
    return re.sub(r"\s+", " ", str(value or "")).strip()


# This function converts stats text into a normalised comparison key.
def normaliseStatsKey(value):
    return normaliseStatsText(value).lower()


# This function gets the display label for a custom monitor measure key.
def getCustomMonitorMeasureLabel(measureType):
    for item in CUSTOM_MONITOR_MEASURE_OPTIONS:
        if item["key"] == measureType:
            return item["label"]
    return "Answered submissions"


# this  Function cleans saved custom monitor items before teh stats page uses them
def sanitizeCustomMonitorItems(rawItems, questionMap):
    allowedMeasureTypes = {item["key"] for item in CUSTOM_MONITOR_MEASURE_OPTIONS}
    cleanItems = []
    seenIds = set()
    for rawItem in rawItems or []:
        monitorId = normaliseStatsText((rawItem or {}).get("monitorId")) or uuid.uuid4().hex[:12]
        if monitorId in seenIds:
            monitorId = uuid.uuid4().hex[:12]
        seenIds.add(monitorId)
        title = normaliseStatsText((rawItem or {}).get("title"))
        questionKey = normaliseStatsKey((rawItem or {}).get("questionKey"))
        measureType = normaliseStatsText((rawItem or {}).get("measureType"))
        if questionKey not in questionMap:
            continue
        if measureType not in allowedMeasureTypes:
            measureType = "answeredCount"
        if not title:
            title = f"{questionMap[questionKey]['promptText']} · {getCustomMonitorMeasureLabel(measureType)}"
        cleanItems.append({
            "monitorId": monitorId,
            "title": title,
            "questionKey": questionKey,
            "measureType": measureType,
        })
    return cleanItems


# this  Function calculates the value shown by a custom monitored stat card
def buildCustomMonitorValue(monitorItem, answerCounterByPromptKey, answeredSubmissionCounterByPromptKey):
    questionKey = normaliseStatsKey(monitorItem.get("questionKey"))
    measureType = normaliseStatsText(monitorItem.get("measureType"))
    answerCounter = answerCounterByPromptKey.get(questionKey, Counter())
    answeredCount = int(answeredSubmissionCounterByPromptKey.get(questionKey, 0))

    if measureType == "answeredCount":
        return str(answeredCount)
    if measureType == "yesCount":
        yesCount = sum(count for answer, count in answerCounter.items() if normaliseStatsKey(answer) in {"yes", "true", "correct"})
        return str(yesCount)
    if measureType == "noCount":
        noCount = sum(count for answer, count in answerCounter.items() if normaliseStatsKey(answer) in {"no", "false", "incorrect"})
        return str(noCount)
    if measureType == "uniqueAnswers":
        return str(len(answerCounter))
    if measureType == "mostCommonAnswer":
        topAnswer = answerCounter.most_common(1)
        if not topAnswer:
            return "No answers yet"
        return f"{topAnswer[0][0]} ({topAnswer[0][1]})"
    return str(answeredCount)


# this function checks whether a prompt matches any of the supplied keywords.
def promptLooksLike(promptText, keywords):
    promptKey = normaliseStatsKey(promptText)
    return any(keyword in promptKey for keyword in keywords)


# this  Function checks whether a prompt is asking for teh subject team
def isSubjectTeamPrompt(promptText):
    promptKey = normaliseStatsKey(promptText)
    if "team" not in promptKey:
        return False
    if any(keyword in promptKey for keyword in ["crt", "drt", "dispatch", "multiple answers can be selected", "select which team"]):
        return False
    if "person the form is about" in promptKey:
        return True
    if "if known" in promptKey and any(keyword in promptKey for keyword in ["staff member", "member of staff", "requiring feedback"]):
        return True
    return False


# This function checks whether a prompt is asking for the subject name.
def isSubjectNamePrompt(promptText):
    promptKey = normaliseStatsKey(promptText)
    if not any(keyword in promptKey for keyword in ["staff member", "member of staff", "person the form is about", "requiring feedback"]):
        return False
    if any(keyword in promptKey for keyword in ["supervisor", "email", "team", "select which team", "if known"]):
        return False
    return True


# this  Function checks whether a prompt is asking for the supervisor name
def isSupervisorNamePrompt(promptText):
    promptKey = normaliseStatsKey(promptText)
    return ("supervisor" in promptKey) and ("email" not in promptKey)


# this  Function checks whether a prompt is asking for detailed feedback text
def isFeedbackCommentPrompt(promptText):
    promptKey = normaliseStatsKey(promptText)
    return any(keyword in promptKey for keyword in ["comment", "feedback to be given", "additional detail", "what happened", "summary detail"])


# This function cleans a stats label before it is counted or displayed.
def sanitizeStatsEntityValue(value, entityType="generic"):
    valueText = normaliseStatsText(value)
    if not valueText:
        return ""
    valueKey = normaliseStatsKey(valueText)
    if re.fullmatch(r"example[\s_-]*\d+", valueText, flags=re.IGNORECASE):
        return ""
    if entityType == "team" and valueKey in {"unknown", "n/a", "na", "none", "not known", "not sure", "hello", "test"}:
        return ""
    return valueText


# This function checks whether a prompt should be treated as identity-only data.
def isIdentityPrompt(promptText):
    promptKey = normaliseStatsKey(promptText)
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
    if isSubjectNamePrompt(promptText) or isSubjectTeamPrompt(promptText) or isSupervisorNamePrompt(promptText):
        return True
    return any(keyword in promptKey for keyword in identityKeywords)


# this  Function checks whether an answer should count as an issue signal
def answerLooksLikeIssue(promptText, answerLabel):
    promptKey = normaliseStatsKey(promptText)
    answerKey = normaliseStatsKey(answerLabel)
    if not answerKey:
        return False
    negativeValues = {"no", "incorrect", "not correct", "false", "failed", "fail", "poor", "late", "missed"}
    positiveValues = {"yes", "correct", "true", "passed", "pass", "good", "compliant"}
    if any(keyword in promptKey for keyword in ["correct", "compliant", "right", "accurate"]):
        return answerKey in negativeValues
    if any(keyword in promptKey for keyword in ["missed", "error", "issue", "problem", "negated", "required feedback", "breach", "concern"]):
        return answerKey in positiveValues or answerKey not in {"n/a", "na", "none", "not applicable"}
    return answerKey not in {"n/a", "na", "none", "not applicable", "unknown"}


# This function turns a date into a month key used by the trend chart.
def monthKeyFromDate(value):
    if not value:
        return None
    return value.strftime("%Y-%m")


# This function turns a stored month key into a chart-friendly label.
def monthLabelFromKey(value):
    try:
        return datetime.strptime(value, "%Y-%m").strftime("%b %Y")
    except ValueError:
        return value


# this  Function builds a short issue summary from a submission answer set
def buildIssueSummary(issues):
    if not issues:
        return "None recorded"
    return issues[0][0]


# this  Function formats saved answer values for cards, tables, and summaries
def formatAnswerForDisplay(questionObj, answerObj):
    if not answerObj:
        return ""
    if questionObj.response_type in ("number", "rating"):
        if answerObj.answer_number is not None:
            valueText = str(answerObj.answer_number)
            if "." in valueText:
                valueText = valueText.rstrip("0").rstrip(".")
            return valueText
        return (answerObj.answer_text or "").strip()
    if questionObj.response_type == "select":
        if answerObj.answer_option_value is None:
            return ""
        optionValue = normaliseStatsText(answerObj.answer_option_value)
        for opt in questionObj.options:
            if normaliseStatsText(opt.option_value) == optionValue:
                return (opt.option_label or opt.option_value or "").strip()
        return str(answerObj.answer_option_value).strip()
    if questionObj.response_type == "multi_select":
        rawParts = [normaliseStatsText(value) for value in str(answerObj.answer_text or "").splitlines() if normaliseStatsText(value)]
        if not rawParts:
            return ""
        optionMap = {}
        for opt in questionObj.options:
            optionMap[normaliseStatsText(opt.option_value)] = (opt.option_label or opt.option_value or "").strip()
        return ", ".join([optionMap.get(part, part) for part in rawParts])
    return (answerObj.answer_text or "").strip()


# This function collects the human-readable labels for an answer set.
def buildAnswerLabelList(questionObj, answerObj, optionLabelByQuestion=None):
    if not questionObj or not answerObj:
        return []
    qid = int(questionObj.question_version_id)
    labels = []
    if answerObj.answer_option_value is not None:
        optionValue = normaliseStatsText(answerObj.answer_option_value)
        labels.append((optionLabelByQuestion or {}).get(qid, {}).get(optionValue, optionValue))
    elif answerObj.answer_text is not None:
        if questionObj.response_type == "multi_select":
            optionMap = (optionLabelByQuestion or {}).get(qid, {})
            for value in str(answerObj.answer_text).splitlines():
                valueText = normaliseStatsText(value)
                if valueText:
                    labels.append(optionMap.get(valueText, valueText))
        else:
            valueText = normaliseStatsText(answerObj.answer_text)
            if valueText:
                labels.append(valueText)
    elif answerObj.answer_number is not None:
        numberText = str(answerObj.answer_number)
        if isinstance(answerObj.answer_number, Decimal) and answerObj.answer_number == answerObj.answer_number.to_integral():
            numberText = str(int(answerObj.answer_number))
        labels.append(numberText)
    return [normaliseStatsText(value) for value in labels if normaliseStatsText(value)]


# this  Function prepares a structured answer summary for one submission
def buildSubmissionAnswerSummary(questions, answerByQuestionVersionId):
    answerSummary = []
    for questionObj in questions:
        answerText = formatAnswerForDisplay(questionObj, answerByQuestionVersionId.get(int(questionObj.question_version_id)))
        answerSummary.append({
            "questionVersionId": int(questionObj.question_version_id),
            "promptText": normaliseStatsText(questionObj.prompt_text),
            "promptKey": normaliseStatsKey(questionObj.prompt_text),
            "answerText": answerText,
        })
    return answerSummary


# this function finds the email recipients linked to a submission.
def findSubmissionEmailTargets(answerSummary):
    subjectName = ""
    subjectEmail = ""
    supervisorName = ""
    supervisorEmail = ""
    for item in answerSummary:
        promptKey = item.get("promptKey") or ""
        answerText = (item.get("answerText") or "").strip()
        if not answerText:
            continue
        if ("staff member" in promptKey or "member of staff" in promptKey or "requiring feedback" in promptKey) and "supervisor" not in promptKey and "email" not in promptKey and not subjectName:
            subjectName = answerText
        elif (("staff member" in promptKey or "member of staff" in promptKey or "requiring feedback" in promptKey) and "email" in promptKey and "supervisor" not in promptKey and not subjectEmail):
            subjectEmail = answerText
        elif "supervisor" in promptKey and "email" not in promptKey and not supervisorName:
            supervisorName = answerText
        elif "supervisor" in promptKey and "email" in promptKey and not supervisorEmail:
            supervisorEmail = answerText
    recipientList = []
    for value in (supervisorEmail, subjectEmail):
        cleanValue = str(value or "").strip()
        if cleanValue and cleanValue not in recipientList:
            recipientList.append(cleanValue)
    return {
        "subjectName": subjectName,
        "subjectEmail": subjectEmail,
        "supervisorName": supervisorName,
        "supervisorEmail": supervisorEmail,
        "recipientList": recipientList,
    }


# this  Function builds the default subject and body used for submission emails
def buildDefaultSubmissionEmail(formObj, formVersionObj, submissionObj, answerSummary, targetInfo):
    formTitle = normaliseStatsText(formVersionObj.title if formVersionObj and formVersionObj.title else (formObj.title if formObj else "Review form")) or "Review form"
    subjectName = targetInfo.get("subjectName") or "staff member"
    supervisorName = targetInfo.get("supervisorName") or "supervisor"
    subjectLine = f"{formTitle} submission for {subjectName}"
    bodyLines = [
        f"A new {formTitle} has been submitted.",
        "",
        f"Submission ID: {submissionObj.submission_id}",
        f"Submitted at: {submissionObj.submitted_at}",
        f"Staff member: {targetInfo.get('subjectName') or 'Not provided'}",
        f"Staff member email: {targetInfo.get('subjectEmail') or 'Not provided'}",
        f"Supervisor: {supervisorName if supervisorName else 'Not provided'}",
        f"Supervisor email: {targetInfo.get('supervisorEmail') or 'Not provided'}",
        "",
        "Form details:",
    ]
    for item in answerSummary:
        promptText = item.get("promptText") or "Question"
        answerText = item.get("answerText") or "No response provided"
        bodyLines.append(f"- {promptText}: {answerText}")
    bodyLines.extend(["", "This email was generated by the Review System."])
    return subjectLine, "\n".join(bodyLines)


# this  Function prepares teh data needed ot preview submission emails in the form
def getEmailPreviewContext(formObj, formVersionObj, questions):
    answerSummary = []
    for questionObj in questions or []:
        answerSummary.append({
            "questionVersionId": int(questionObj.question_version_id),
            "promptText": normaliseStatsText(questionObj.prompt_text),
            "promptKey": normaliseStatsKey(questionObj.prompt_text),
            "answerText": "",
        })
    targetInfo = findSubmissionEmailTargets(answerSummary)
    previewSubmission = type("PreviewSubmission", (), {"submission_id": "Pending", "submitted_at": "Pending"})()
    defaultSubject, defaultBody = buildDefaultSubmissionEmail(formObj, formVersionObj, previewSubmission, answerSummary, targetInfo)
    return {
        "defaultEmailSubject": defaultSubject,
        "defaultEmailBody": defaultBody,
        "emailQuestionPrompts": [{
            "questionVersionId": item["questionVersionId"],
            "promptText": item["promptText"],
            "promptKey": item["promptKey"],
        } for item in answerSummary],
    }


# This function sends the submission email payload through the active delivery service.
def sendSubmissionEmails(formObj, formVersionObj, submissionObj, questions, answerByQuestionVersionId, customSubject=None, customBody=None):
    answerSummary = buildSubmissionAnswerSummary(questions, answerByQuestionVersionId)
    targetInfo = findSubmissionEmailTargets(answerSummary)
    defaultSubject, defaultBody = buildDefaultSubmissionEmail(formObj, formVersionObj, submissionObj, answerSummary, targetInfo)
    emailSubject = normaliseStatsText(customSubject) or defaultSubject
    emailBody = str(customBody or "").strip() or defaultBody
    deliveryService = EmailDeliveryServiceFactory.create(app.config)
    return deliveryService.sendSubmissionEmail(
        recipients=targetInfo.get("recipientList") or [],
        subject=emailSubject,
        body=emailBody,
        metadata={
            "submissionId": int(submissionObj.submission_id),
            "formId": int(formObj.form_id),
            "formVersionId": int(formVersionObj.form_version_id) if formVersionObj else None,
            "subjectName": targetInfo.get("subjectName") or "",
            "subjectEmail": targetInfo.get("subjectEmail") or "",
            "supervisorName": targetInfo.get("supervisorName") or "",
            "supervisorEmail": targetInfo.get("supervisorEmail") or "",
            "answers": answerSummary,
        },
    )


# This function builds the payload passed into the local summariser service.
def buildSubmissionSummaryPayload(formObj, formVersionObj, submissionObj, questions, answerByQuestionVersionId):
    answerSummary = buildSubmissionAnswerSummary(questions, answerByQuestionVersionId)
    summaryService = LocalSubmissionSummaryServiceFactory.create(app.config)
    formTitle = normaliseStatsText(formVersionObj.title if formVersionObj and formVersionObj.title else (formObj.title if formObj else "Review form")) or "Review form"
    return summaryService.generateSummary(
        formTitle=formTitle,
        submissionId=int(submissionObj.submission_id),
        submittedAt=submissionObj.submitted_at,
        answerSummary=answerSummary,
    )


# this  Function saves teh generated summary back onto the submission record
def storeSubmissionSummary(submissionObj, summaryResult, commitChanges=True):
    submissionObj.summary_text = normaliseStatsText(summaryResult.summaryText) or None
    submissionObj.summary_payload = str(summaryResult.payloadJson or "").strip() or None
    submissionObj.summary_status = normaliseStatsText(summaryResult.status) or "generated"
    submissionObj.summary_model = normaliseStatsText(summaryResult.modelName) or None
    submissionObj.summary_error = normaliseStatsText(summaryResult.message) or None
    submissionObj.summary_generated_at = datetime.utcnow() if submissionObj.summary_status in ("generated", "disabled") else None
    if commitChanges:
        db.session.commit()
    return submissionObj


# This function generates a local summary and stores it on the submission.
def generateAndStoreSubmissionSummary(formObj, formVersionObj, submissionObj, questions, answerByQuestionVersionId, commitChanges=True):
    try:
        summaryResult = buildSubmissionSummaryPayload(formObj, formVersionObj, submissionObj, questions, answerByQuestionVersionId)
    except Exception as exc:
        summaryResult = type("SummaryResult", (), {
            "summaryText": "",
            "payloadJson": "",
            "status": "error",
            "modelName": normaliseStatsText(app.config.get("LOCAL_SUMMARY_MODEL_NAME") or "localRuleBasedSummariser-v1"),
            "message": f"{type(exc).__name__}: {exc}",
        })()
    return storeSubmissionSummary(submissionObj, summaryResult, commitChanges=commitChanges)


# this function converts posted form data into normalised answer records.
def parseSubmissionPayload(payloadText):
    try:
        return json.loads(payloadText) if payloadText else None
    except (TypeError, ValueError, json.JSONDecodeError):
        return None

app.config.from_object(Config)

# Set  teh database connection environment variables for teh target machine so the app does not rely on the local default credentials shown here
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


# this  Section defines the database models used by forms, users, submissions, and branching
# This model stores role records used by the permission system.
class Role(db.Model):
    __tablename__ = "roles"

    role_id = db.Column(db.SmallInteger, primary_key=True, autoincrement=True)
    role_name = db.Column(db.String(32), unique=True, nullable=False)


# this  model stores application user accounts and their role links
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


# This model stores the top-level form definition shared across versions.
class Form(db.Model):
    __tablename__ = "forms"

    form_id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    form_key = db.Column(db.String(64), unique=True, nullable=False)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    created_by = db.Column(db.BigInteger, db.ForeignKey("users.user_id"), nullable=False)


# this  model stores each saved version of a form and its metadata
class FormVersion(db.Model):
    __tablename__ = "form_versions"

    form_version_id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    form_id = db.Column(db.BigInteger, db.ForeignKey("forms.form_id"), nullable=False)
    version_number = db.Column(db.Integer, nullable=False)
    title = db.Column(db.String(255), nullable=True)
    description = db.Column(db.Text, nullable=True)
    created_by = db.Column(db.BigInteger, db.ForeignKey("users.user_id"), nullable=False)
    notes = db.Column(db.String(255), nullable=True)


# this  model stores teh reusable parent record for a question across versions
class Question(db.Model):
    __tablename__ = "questions"

    question_id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    question_key = db.Column(db.String(64), unique=True, nullable=False)
    created_by = db.Column(db.BigInteger, db.ForeignKey("users.user_id"), nullable=False)


# This model stores the version-specific wording and settings for a question.
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


# This model stores selectable options for a versioned question.
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


# this  model stores Section records used ot group questions within a form version
class FormVersionSection(db.Model):
    __tablename__ = "form_version_sections"

    section_id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    form_version_id = db.Column(db.BigInteger, db.ForeignKey("form_versions.form_version_id"), nullable=False, index=True)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    sort_order = db.Column(db.Integer, nullable=False, default=0)


# This model stores the ordering and placement of questions inside a form version.
class FormVersionQuestion(db.Model):
    __tablename__ = "form_version_questions"

    form_version_question_id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    form_version_id = db.Column(db.BigInteger, db.ForeignKey("form_versions.form_version_id"), nullable=False)
    question_version_id = db.Column(db.BigInteger, db.ForeignKey("question_versions.question_version_id"), nullable=False)
    section_id = db.Column(db.BigInteger, db.ForeignKey("form_version_sections.section_id"), nullable=True)
    sort_order = db.Column(db.Integer, nullable=False, default=0)


# This model stores branching rules that control which questions appear next.
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


# this  model stores a completed form submission and its summary data
class FormSubmission(db.Model):
    __tablename__ = "form_submissions"

    submission_id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    form_id = db.Column(db.BigInteger, db.ForeignKey("forms.form_id"), nullable=False)
    form_version_id = db.Column(db.BigInteger, db.ForeignKey("form_versions.form_version_id"), nullable=False)
    submitted_by = db.Column(db.BigInteger, db.ForeignKey("users.user_id"), nullable=False)
    submitted_at = db.Column(db.DateTime, nullable=False, server_default=db.func.current_timestamp())
    summary_text = db.Column(db.Text, nullable=True)
    summary_payload = db.Column(db.Text, nullable=True)
    summary_status = db.Column(db.String(32), nullable=True)
    summary_model = db.Column(db.String(120), nullable=True)
    summary_error = db.Column(db.Text, nullable=True)
    summary_generated_at = db.Column(db.DateTime, nullable=True)


# this  model stores the individual answers linked to a submitted form
class SubmissionAnswer(db.Model):
    __tablename__ = "submission_answers"

    submission_answer_id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    submission_id = db.Column(db.BigInteger, db.ForeignKey("form_submissions.submission_id"), nullable=False)
    question_version_id = db.Column(db.BigInteger, db.ForeignKey("question_versions.question_version_id"), nullable=False)
    answer_text = db.Column(db.Text, nullable=True)
    answer_number = db.Column(db.Numeric(18, 6), nullable=True)
    answer_option_value = db.Column(db.String(128), nullable=True)


# This model stores one-time setup and reset tokens issued to user accounts.
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


# this  model stores teh saved security question answers for a user
class UserSecurityQuestion(db.Model):
    __tablename__ = "user_security_questions"

    security_question_id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    user_id = db.Column(db.BigInteger, db.ForeignKey("users.user_id"), nullable=False)
    question_key = db.Column(db.String(64), nullable=False)
    question_text = db.Column(db.String(255), nullable=False)
    answer_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, server_default=db.func.current_timestamp())


# This section contains current-user helpers and permission checks used by the routes.
# this  Function returns the logged-in user record for the current session
def getCurrentUser():
    userId = session.get("user_id")
    if not str(userId or "").isdigit():
        return None
    return User.query.filter_by(user_id=int(userId)).first()


# this  Function returns teh current user role name in a normalised format
def getCurrentRoleName(userObj=None, refreshSession=True):
    if userObj is None:
        userObj = getCurrentUser()

    roleName = ""
    if userObj and userObj.role_id is not None:
        roleRow = db.session.query(Role.role_name).filter(Role.role_id == userObj.role_id).first()
        if roleRow:
            roleName = normaliseRoleName(roleRow[0])

    if not roleName:
        roleName = normaliseRoleName(session.get("role_name"))

    if refreshSession and userObj:
        session["role_name"] = roleName
        session["username"] = userObj.username
        session["role_id"] = int(userObj.role_id or 0)
    return roleName


# This function checks whether the current user has one of the supplied roles.
def currentUserHasRole(*roleNames):
    currentRoleName = getCurrentRoleName(refreshSession=True)
    normalisedRoleNames = {normaliseRoleName(roleName) for roleName in roleNames}
    return currentRoleName in normalisedRoleNames


# this function checks whether the current user can manage accounts.
def currentUserCanManageAccounts():
    return currentUserHasRole("admin", "developer")


# this  Function checks whether teh current user can view every submission
def currentUserCanViewAllSubmissions():
    return currentUserHasRole("admin", "developer")


# This function checks whether the current user can assign a target role during account management.
def currentUserCanAssignRole(targetRoleName, targetUser=None):
    currentRoleName = getCurrentRoleName(refreshSession=True)
    normalisedTargetRoleName = normaliseRoleName(targetRoleName)
    targetUserRoleName = normaliseRoleName(targetUser.role.role_name if (targetUser and targetUser.role) else None)

    if currentRoleName == "developer":
        return normalisedTargetRoleName in ("standard", "admin", "developer")
    if currentRoleName == "admin":
        return normalisedTargetRoleName in ("standard", "admin") and targetUserRoleName not in ("developer",)
    return False


# This function returns the visible role choices for the current account-management user.
def getManageableRoleOptions(targetUser=None):
    roleRows = Role.query.order_by(Role.role_name.asc()).all()
    return [
        roleRow
        for roleRow in roleRows
        if currentUserCanAssignRole(roleRow.role_name, targetUser=targetUser)
    ]


# this  Function checks whether teh current user can access developer branding tools
def currentUserCanViewBranding():
    return currentUserHasRole("developer")


# this  Function refreshes the stored session role details from the live database record
@app.before_request
def syncCurrentUserContext():
    if not session.get("user_id"):
        return
    userObj = getCurrentUser()
    if not userObj or not userObj.is_active:
        session.clear()
        return
    getCurrentRoleName(userObj=userObj, refreshSession=True)


# This decorator redirects users to sign in before they open a protected route.
def loginRequired(view_func):
    @wraps(view_func)
    def wrapper(*args, **kwargs):
        userId = session.get("user_id")
        if not userId:
            return redirect(url_for("index"))
        userObj = getCurrentUser()
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
        getCurrentRoleName(userObj=userObj, refreshSession=True)
        session["session_version"] = int(userObj.session_version or 1)
        return view_func(*args, **kwargs)
    return wrapper


# this  decorator restricts a Route ot admin users only
def adminRequired(view_func):
    @wraps(view_func)
    def wrapper(*args, **kwargs):
        if not session.get("user_id"):
            return redirect(url_for("index"))
        if getCurrentRoleName(refreshSession=True) != "admin":
            flash("Admins only.", "error")
            return redirect(url_for("dashboard"))
        return view_func(*args, **kwargs)
    return wrapper


# This decorator restricts a route to developer users only.
def developerRequired(view_func):
    @wraps(view_func)
    def wrapper(*args, **kwargs):
        if not session.get("user_id"):
            return redirect(url_for("index"))
        if getCurrentRoleName(refreshSession=True) != "developer":
            flash("Developers only.", "error")
            return redirect(url_for("dashboard"))
        return view_func(*args, **kwargs)
    return wrapper


# this  decorator restricts a Route to admin or developer editors
def editorRequired(view_func):
    @wraps(view_func)
    def wrapper(*args, **kwargs):
        if not session.get("user_id"):
            return redirect(url_for("index"))
        roleName = getCurrentRoleName(refreshSession=True)
        if roleName not in ("admin", "developer"):
            flash("Editors only.", "error")
            return redirect(url_for("dashboard"))
        return view_func(*args, **kwargs)
    return wrapper


# this  Section injects shared branding and theme values into every rendered template
# This function injects branding, theme, and role values into each template render.
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
    themeBackgroundColour = app.config.get("THEME_BACKGROUND_COLOUR")
    themeButtonColour = app.config.get("THEME_BUTTON_COLOUR")
    themeButtonTextColour = app.config.get("THEME_BUTTON_TEXT_COLOUR")
    # Configure the Microsoft Graph environment values in config before expecting live email sending, otherwise the UI will stay in mock-email mode.
    graphConfigured = bool(app.config.get("GRAPH_CLIENT_ID") and app.config.get("GRAPH_CLIENT_SECRET") and app.config.get("GRAPH_TENANT_ID") and app.config.get("GRAPH_SENDER_EMAIL"))
    emailDeliveryMode = (app.config.get("EMAIL_DELIVERY_MODE") or "auto").strip().lower()
    usingMockEmailStrategy = (not graphConfigured) or emailDeliveryMode == "mock"
    currentRoleName = getCurrentRoleName(refreshSession=True)
    return {
        "siteLogoUrl": siteLogoUrl,
        "themeBackgroundColour": themeBackgroundColour,
        "themeButtonColour": themeButtonColour,
        "themeButtonTextColour": themeButtonTextColour,
        "graphConfigured": graphConfigured,
        "usingMockEmailStrategy": usingMockEmailStrategy,
        "currentRoleName": currentRoleName,
        "canManageAccounts": currentUserCanManageAccounts(),
        "canViewAllSubmissions": currentUserCanViewAllSubmissions(),
        "canViewBranding": currentUserCanViewBranding(),
    }


# this  Route lets developers update teh logo and theme branding values
@app.route("/admin/branding", methods=["GET", "POST"])
@developerRequired
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


# this section keeps the database schema and default records in sync with the current code.
# This function applies the database checks and safe schema updates used by the app.
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

    formSubmissionsAlter = [
        ("summary_text", "ALTER TABLE form_submissions ADD COLUMN summary_text TEXT NULL AFTER submitted_at"),
        ("summary_payload", "ALTER TABLE form_submissions ADD COLUMN summary_payload TEXT NULL AFTER summary_text"),
        ("summary_status", "ALTER TABLE form_submissions ADD COLUMN summary_status VARCHAR(32) NULL AFTER summary_payload"),
        ("summary_model", "ALTER TABLE form_submissions ADD COLUMN summary_model VARCHAR(120) NULL AFTER summary_status"),
        ("summary_error", "ALTER TABLE form_submissions ADD COLUMN summary_error TEXT NULL AFTER summary_model"),
        ("summary_generated_at", "ALTER TABLE form_submissions ADD COLUMN summary_generated_at DATETIME NULL AFTER summary_error"),
    ]
    for columnName, statement in formSubmissionsAlter:
        if tableExists("form_submissions") and not columnExists("form_submissions", columnName):
            db.session.execute(db.text(statement))

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


# this  Function inserts teh default user roles when they are missing
def seedRolesIfMissing():
    existingRoles = {normaliseRoleName(role.role_name): role for role in Role.query.all()}
    for roleName in ("admin", "standard", "developer"):
        if roleName not in existingRoles:
            db.session.add(Role(role_name=roleName))
    db.session.commit()


# this  Function runs the database readiness checks before the app serves requests
@app.before_request
def _ensureDbReady():
    if not app.config.get("_SEEDED_ROLES"):
        db.session.execute(db.text("SELECT 1"))
        ensureDatabaseSchema()
        seedRolesIfMissing()
        app.config["_SEEDED_ROLES"] = True
    ensureLockedTeamQuestionPresent()


# This function gets the active form and its latest editable version.
def _getActiveFormAndLatestVersion():
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


#:)

# This function gets the section layout and grouped questions for a form version.
def _getSectionsForVersion(form_version_id: int):
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


# this  Function gets every question for a form version in display order
def _getQuestionsForVersion(form_version_id: int):
    unsectioned_questions, sections_with_questions = _getSectionsForVersion(form_version_id)
    out = []
    out.extend(unsectioned_questions)
    for item in sections_with_questions:
        out.extend(item.get("questions") or [])
    return out

DEFAULT_LOCKED_TEAM_PROMPT = "What is the team (if known) of the person the form is about?"
DEFAULT_LOCKED_TEAM_HINT = "Leave blank if the team is not known."


# this  Function adds teh locked team question when the form version does not have it yet
def ensureLockedTeamQuestionPresent():
    formObj, latestVersion = _getActiveFormAndLatestVersion()
    if not formObj or not latestVersion:
        return

    existingQuestions = _getQuestionsForVersion(int(latestVersion.form_version_id))
    if any(isSubjectTeamPrompt(questionObj.prompt_text) for questionObj in existingQuestions):
        return

    newQuestion = Question(question_key=uuid.uuid4().hex, created_by=int(latestVersion.created_by or 1))
    db.session.add(newQuestion)
    db.session.flush()

    newQuestionVersion = QuestionVersion(
        question_id=newQuestion.question_id,
        version_number=1,
        prompt_text=DEFAULT_LOCKED_TEAM_PROMPT,
        response_type="text",
        is_required=False,
        hint_text=DEFAULT_LOCKED_TEAM_HINT,
        question_description=None,
        is_locked=True,
        help_text=None,
        is_active=True,
        created_by=int(latestVersion.created_by or 1),
    )
    db.session.add(newQuestionVersion)
    db.session.flush()

    newFormVersion = FormVersion(
        form_id=formObj.form_id,
        version_number=int(latestVersion.version_number or 0) + 1,
        title=latestVersion.title,
        description=latestVersion.description,
        created_by=int(latestVersion.created_by or 1),
        notes=latestVersion.notes,
    )
    db.session.add(newFormVersion)
    db.session.flush()

    sectionIdMap = {}
    oldSections = (
        FormVersionSection.query
        .filter(FormVersionSection.form_version_id == latestVersion.form_version_id)
        .order_by(FormVersionSection.sort_order.asc(), FormVersionSection.section_id.asc())
        .all()
    )
    for oldSection in oldSections:
        newSection = FormVersionSection(
            form_version_id=newFormVersion.form_version_id,
            title=oldSection.title,
            description=oldSection.description,
            sort_order=int(oldSection.sort_order or 0),
        )
        db.session.add(newSection)
        db.session.flush()
        sectionIdMap[int(oldSection.section_id)] = int(newSection.section_id)

    insertedTeamQuestion = False

    def addQuestionLink(questionVersionId, sectionId, sortOrder):
        db.session.add(FormVersionQuestion(
            form_version_id=newFormVersion.form_version_id,
            question_version_id=int(questionVersionId),
            section_id=sectionId,
            sort_order=int(sortOrder),
        ))

    unsectionedQuestions, sectionsWithQuestions = _getSectionsForVersion(int(latestVersion.form_version_id))
    unsectionedSortOrder = 0
    for questionObj in unsectionedQuestions:
        addQuestionLink(questionObj.question_version_id, None, unsectionedSortOrder)
        unsectionedSortOrder += 1
        if not insertedTeamQuestion and isSubjectNamePrompt(questionObj.prompt_text):
            addQuestionLink(newQuestionVersion.question_version_id, None, unsectionedSortOrder)
            unsectionedSortOrder += 1
            insertedTeamQuestion = True

    for sectionItem in sectionsWithQuestions:
        oldSection = sectionItem.get("section")
        targetSectionId = sectionIdMap.get(int(oldSection.section_id)) if oldSection else None
        sectionSortOrder = 0
        for questionObj in sectionItem.get("questions") or []:
            addQuestionLink(questionObj.question_version_id, targetSectionId, sectionSortOrder)
            sectionSortOrder += 1
            if not insertedTeamQuestion and isSubjectNamePrompt(questionObj.prompt_text):
                addQuestionLink(newQuestionVersion.question_version_id, targetSectionId, sectionSortOrder)
                sectionSortOrder += 1
                insertedTeamQuestion = True

    if not insertedTeamQuestion:
        addQuestionLink(newQuestionVersion.question_version_id, None, unsectionedSortOrder)

    existingBranches = (
        FormQuestionBranching.query
        .filter(FormQuestionBranching.form_version_id == latestVersion.form_version_id)
        .order_by(FormQuestionBranching.priority.asc(), FormQuestionBranching.branching_id.asc())
        .all()
    )
    for branchRow in existingBranches:
        db.session.add(FormQuestionBranching(
            form_version_id=newFormVersion.form_version_id,
            source_question_version_id=branchRow.source_question_version_id,
            target_question_version_id=branchRow.target_question_version_id,
            operator=branchRow.operator,
            compare_option_value=branchRow.compare_option_value,
            compare_number=branchRow.compare_number,
            compare_text=branchRow.compare_text,
            action=branchRow.action,
            priority=branchRow.priority,
        ))

    formObj.title = newFormVersion.title or formObj.title
    formObj.description = newFormVersion.description
    db.session.commit()


# This function returns the saved branching rules for a form version.
def _getBranchingForVersion(form_version_id: int):
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


# This route returns the branching rules for the live form as JSON.
@app.route("/api/branching/<int:form_version_id>", methods=["GET"])
@loginRequired
def api_branching(form_version_id: int):
    return jsonify(_getBranchingForVersion(form_version_id))


# this  Section contains teh authentication and account-management routes
# This route handles the sign-in page and its authentication checks.
@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        username = normaliseCredentialText(request.form.get("username") or "")
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
        session["role_name"] = normaliseRoleName(user.role.role_name if user.role else None)
        session["session_version"] = int(user.session_version or 1)
        return redirect(url_for("dashboard"))

    return render_template("index.html")


# This route redirects users into the first-time account setup flow.
@app.route("/signup", methods=["GET", "POST"])
def signup():
    flash("Accounts can only be created by an admin.", "warning")
    return redirect(url_for("index"))


# this  Route handles teh first-time password setup workflow
@app.route("/set-password", methods=["GET", "POST"])
def set_password():
    questionMap = getSecurityQuestionMap()
    if request.method == "POST":
        username = normaliseCredentialText(request.form.get("username") or "")
        setupCode = normaliseCredentialText(request.form.get("setup_code") or "")
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
        cleanKeys = [normaliseCredentialText(value) for value in selectedKeys]
        if len(set(cleanKeys)) != 5 or any(key not in questionMap for key in cleanKeys):
            flash("Please choose 5 different security questions.", "error")
            return render_template("set_password.html", securityQuestions=securityQuestions, presetUsername=username), 400
        cleanAnswers = [normaliseSecurityAnswer(value) for value in answerValues]
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

    presetUsername = normaliseCredentialText(request.args.get("username") or "")
    return render_template("set_password.html", securityQuestions=securityQuestions, presetUsername=presetUsername)


# this  Route handles the reset-key and security-question password reset flow
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
            username = normaliseCredentialText(request.form.get("username") or "")
            resetCode = normaliseCredentialText(request.form.get("reset_code") or "")
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
            username = normaliseCredentialText(request.form.get("username") or "")
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
            answerOne = normaliseSecurityAnswer(request.form.get(f"question_answer_{questionRows[0].security_question_id}") or "")
            answerTwo = normaliseSecurityAnswer(request.form.get(f"question_answer_{questionRows[1].security_question_id}") or "")
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


# This route lets editors create accounts and issue setup or reset codes.
@app.route("/admin/users", methods=["GET", "POST"])
@editorRequired
def manage_users():
    adminId = int(session.get("user_id"))
    revealCode = None
    revealTitle = None
    revealMeta = None

    if request.method == "POST":
        formAction = request.form.get("form_action") or ""
        if formAction == "create_user":
            username = normaliseCredentialText(request.form.get("username") or "")
            displayName = normaliseCredentialText(request.form.get("display_name") or "")
            roleIdRaw = request.form.get("role_id") or ""
            roleObj = Role.query.filter_by(role_id=int(roleIdRaw)).first() if str(roleIdRaw).isdigit() else None
            if not username or len(username) > 64:
                flash("Please enter a valid username.", "error")
                return redirect(url_for("manage_users"))
            if not roleObj:
                flash("Please choose an account role.", "error")
                return redirect(url_for("manage_users"))
            if not currentUserCanAssignRole(roleObj.role_name):
                flash("You do not have permission to create that type of account.", "error")
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

        elif formAction == "change_role":
            userIdRaw = request.form.get("user_id") or ""
            roleIdRaw = request.form.get("new_role_id") or ""
            userObj = User.query.filter_by(user_id=int(userIdRaw)).first() if str(userIdRaw).isdigit() else None
            roleObj = Role.query.filter_by(role_id=int(roleIdRaw)).first() if str(roleIdRaw).isdigit() else None
            if not userObj or not roleObj:
                flash("User or role not found.", "error")
                return redirect(url_for("manage_users"))
            if not currentUserCanAssignRole(roleObj.role_name, targetUser=userObj):
                flash("You do not have permission to change that account to the selected role.", "error")
                return redirect(url_for("manage_users"))
            if userObj.user_id == adminId and normaliseRoleName(roleObj.role_name) != getCurrentRoleName(refreshSession=True):
                flash("You cannot change your own account role here.", "warning")
                return redirect(url_for("manage_users"))
            if int(userObj.role_id or 0) == int(roleObj.role_id):
                flash("That account already has that role.", "info")
                return redirect(url_for("manage_users"))
            userObj.role_id = int(roleObj.role_id)
            userObj.session_version = int(userObj.session_version or 1) + 1
            db.session.commit()
            flash(f"Updated {userObj.username} to {roleObj.role_name}.", "success")

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

    roleOptions = getManageableRoleOptions()
    userRows = User.query.join(Role, Role.role_id == User.role_id).order_by(User.username.asc()).all()
    userRoleOptionMap = {
        int(userRow.user_id): getManageableRoleOptions(targetUser=userRow)
        for userRow in userRows
    }
    return render_template(
        "manage_users.html",
        roleOptions=roleOptions,
        userRows=userRows,
        revealCode=revealCode,
        revealTitle=revealTitle,
        revealMeta=revealMeta,
        currentRoleName=getCurrentRoleName(refreshSession=True),
        userRoleOptionMap=userRoleOptionMap,
    )


# this  Section contains teh dashboard, submission viewing, and sign-out routes
# This route shows the dashboard cards and the submissions visible to the current user.
@app.route("/dashboard")
@loginRequired
def dashboard():
    canViewAllSubmissions = currentUserCanViewAllSubmissions()
    user_id = int(session.get("user_id"))

    q = (
        db.session.query(FormSubmission, Form, FormVersion, User)
        .join(Form, Form.form_id == FormSubmission.form_id)
        .join(FormVersion, FormVersion.form_version_id == FormSubmission.form_version_id)
        .join(User, User.user_id == FormSubmission.submitted_by)
    )

    if not canViewAllSubmissions:
        q = q.filter(FormSubmission.submitted_by == user_id)

    submissions = q.order_by(FormSubmission.submitted_at.desc(), FormSubmission.submission_id.desc()).all()

    return render_template("dashboard.html", submissions=submissions, is_admin=canViewAllSubmissions, canViewAllSubmissions=canViewAllSubmissions)


# this  Route shows a saved submission in its read-only versioned form
@app.route("/submission/<int:submission_id>")
@loginRequired
def view_submission(submission_id: int):
    canViewAllSubmissions = currentUserCanViewAllSubmissions()
    user_id = int(session.get("user_id"))

    submission = FormSubmission.query.filter_by(submission_id=submission_id).first()
    if not submission:
        flash("Submission not found.", "error")
        return redirect(url_for("dashboard"))

    if not canViewAllSubmissions and int(submission.submitted_by) != user_id:
        flash("You do not have permission to view that submission.", "error")
        return redirect(url_for("dashboard"))

    form_obj = Form.query.filter_by(form_id=submission.form_id).first()
    form_version = FormVersion.query.filter_by(form_version_id=submission.form_version_id).first()

    unsectioned_questions, sections_with_questions = _getSectionsForVersion(submission.form_version_id)

    answer_rows = (
        SubmissionAnswer.query.filter_by(submission_id=submission.submission_id)
        .all()
    )

    questions = (unsectioned_questions + [q for s in sections_with_questions for q in (s.get("questions") or [])])
    answerByQuestionVersionId = {int(answerRow.question_version_id): answerRow for answerRow in answer_rows}

    if not normaliseStatsText(submission.summary_text) and normaliseStatsText(submission.summary_status) != "disabled":
        generateAndStoreSubmissionSummary(
            formObj=form_obj,
            formVersionObj=form_version,
            submissionObj=submission,
            questions=questions,
            answerByQuestionVersionId=answerByQuestionVersionId,
            commitChanges=True,
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
        questions=questions,
        is_admin=canViewAllSubmissions,
        canViewAllSubmissions=canViewAllSubmissions,
        view_only=True,
        answers=answers,
        submission=submission,
        submissionSummaryPayload=parseSubmissionPayload(submission.summary_payload),
    )


# this  Route signs teh current user out and clears their session
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))


# this section contains the live form, edit-form, and branching routes.
# This route renders the live form and stores new submissions.
@app.route("/form", methods=["GET", "POST"])
@loginRequired
def form():
    form_obj, latest_version = _getActiveFormAndLatestVersion()

    if not form_obj:
        return render_template("form.html", form=None)

    if not latest_version:
        return render_template(
            "form.html",
            form=form_obj,
            form_version=None,
            questions=[],
            is_admin=currentUserCanManageAccounts(),
        )

    if request.method == "POST":
        user_id = int(session["user_id"])
        unsectioned_questions, sections_with_questions = _getSectionsForVersion(latest_version.form_version_id)
        questions = unsectioned_questions + [q for s in sections_with_questions for q in (s.get("questions") or [])]

        sub = FormSubmission(
            form_id=form_obj.form_id,
            form_version_id=latest_version.form_version_id,
            submitted_by=user_id,
        )
        db.session.add(sub)
        db.session.flush()

        answerByQuestionVersionId = {}

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
            answerByQuestionVersionId[int(q.question_version_id)] = ans

        db.session.commit()

        generateAndStoreSubmissionSummary(
            formObj=form_obj,
            formVersionObj=latest_version,
            submissionObj=sub,
            questions=questions,
            answerByQuestionVersionId=answerByQuestionVersionId,
            commitChanges=True,
        )

        emailResult = sendSubmissionEmails(
            formObj=form_obj,
            formVersionObj=latest_version,
            submissionObj=sub,
            questions=questions,
            answerByQuestionVersionId=answerByQuestionVersionId,
            customSubject=request.form.get("emailSubject"),
            customBody=request.form.get("emailBody"),
        )

        if not emailResult.recipients:
            flash("Form submitted. No email was sent because no staff member or supervisor email address was provided on the form.", "warning")
        elif emailResult.status == "sent":
            flash("Form submitted and email sent.", "success")
        elif emailResult.status == "mocked":
            flash("Form submitted. Email was captured by the mock email strategy for development and marking.", "info")
        else:
            flash(f"Form submitted. Email delivery could not be completed: {emailResult.message}", "warning")
        if normaliseStatsText(sub.summary_status) == "error":
            flash(f"The form was saved, but the local summary could not be generated: {sub.summary_error}", "warning")
        return redirect(url_for("form"))

    unsectioned_questions, sections_with_questions = _getSectionsForVersion(latest_version.form_version_id)
    questions = (unsectioned_questions + [q for s in sections_with_questions for q in (s.get("questions") or [])])
    emailPreviewContext = getEmailPreviewContext(form_obj, latest_version, questions)

    return render_template(
        "form.html",
        form=form_obj,
        form_version=latest_version,
        unsectioned_questions=unsectioned_questions,
        sections_with_questions=sections_with_questions,
        questions=questions,
        is_admin=currentUserCanManageAccounts(),
        defaultEmailSubject=emailPreviewContext["defaultEmailSubject"],
        defaultEmailBody=emailPreviewContext["defaultEmailBody"],
        emailQuestionPrompts=emailPreviewContext["emailQuestionPrompts"],
    )


# this  Route lets editors change teh form structure and save a new version
@app.route("/edit-form", methods=["GET", "POST"])
@editorRequired
def editform():
    form_obj, latest_version = _getActiveFormAndLatestVersion()

    if not form_obj:
        flash("No active form available.", "error")
        return redirect(url_for("dashboard"))

    if not latest_version:
        flash("No form version exists yet.", "error")
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        user_id = int(session["user_id"])
        isDeveloper = currentUserHasRole("developer")
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
        if not currentUserHasRole("developer"):
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
        label_to_value_for_source = {}

        def storeQvIdMapping(sourceKey, targetQvId):
            qv_id_map[sourceKey] = int(targetQvId)
            qv_id_map[str(sourceKey)] = int(targetQvId)

        def resolveQvId(sourceKey):
            if sourceKey in qv_id_map:
                return int(qv_id_map[sourceKey])
            sourceKeyStr = str(sourceKey)
            if sourceKeyStr in qv_id_map:
                return int(qv_id_map[sourceKeyStr])
            try:
                sourceKeyInt = int(sourceKeyStr)
            except (TypeError, ValueError):
                return None
            if sourceKeyInt in qv_id_map:
                return int(qv_id_map[sourceKeyInt])
            return sourceKeyInt

        def storeLabelValueMap(sourceKey, mapping):
            label_to_value_for_source[str(sourceKey)] = dict(mapping or {})

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
                    storeQvIdMapping(qv_id, qv_id)
                    if current_qv.response_type in ("select", "multi_select"):
                        m = {}
                        for opt in current_qv.options:
                            lbl = (opt.option_label or "").strip()
                            val = (opt.option_value or "").strip()
                            if lbl:
                                m[lbl] = val if val else lbl
                        storeLabelValueMap(qv_id, m)
                    else:
                        storeLabelValueMap(qv_id, {})
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
                        storeLabelValueMap(qv_id, m)
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
                        storeLabelValueMap(qv_id, {lbl: lbl for lbl in new_options_lines})
                else:
                    storeLabelValueMap(qv_id, {})

                all_qv_ids.append(int(new_qv.question_version_id))
                storeQvIdMapping(qv_id, int(new_qv.question_version_id))

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
                    storeLabelValueMap(key, {lbl: lbl for lbl in lines})
                else:
                    storeLabelValueMap(key, {})

                all_qv_ids.append(int(qv.question_version_id))
                storeQvIdMapping(key, int(qv.question_version_id))

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
            branch_state[str(s)] = (e == "1")

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
                src_key = str(src_raw)
                if src_key in branch_state and not branch_state.get(src_key):
                    continue
                used_sources.add(src_key)
                if not tgt_raw or not opt_raw:
                    continue
                tgt_key = str(tgt_raw)
                per_source.setdefault(src_key, []).append((opt_raw, tgt_key))

            for src_key, pairs in per_source.items():
                src = resolveQvId(src_key)
                if src is None or src not in all_set:
                    continue
                pr = 0
                for opt_label, tgt_key in pairs:
                    opt_val = label_to_value_for_source.get(str(src_key), {}).get(opt_label, opt_label)
                    tgt = resolveQvId(tgt_key)
                    if tgt is None or tgt not in all_set:
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
            src_old_key = str(src_old)
            if src_old_key in branch_state and not branch_state.get(src_old_key):
                continue
            if submitted_has_maps and src_old_key in used_sources:
                continue

            src = resolveQvId(src_old_key)
            tgt_old = int(b.target_question_version_id)
            tgt = resolveQvId(str(tgt_old))

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

    unsectioned_questions, sections_with_questions = _getSectionsForVersion(latest_version.form_version_id)
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
        is_developer=currentUserHasRole("developer"),
        branch_maps=branch_maps,
    )


# This route builds the stats page, charts, and configurable monitor cards.
@app.route("/stats", methods=["GET", "POST"])
@statsRequired
def stats():
    canEditStats = currentUserHasRole("admin", "developer")
    isDeveloper = currentUserHasRole("developer")
    statsState = getStatsState()
    visibleSectionKeys = [str(value) for value in statsState.get("visibleSectionKeys", []) if str(value).strip()]
    visibleSummaryCardKeys = [str(value) for value in statsState.get("visibleSummaryCardKeys", []) if str(value).strip()]

    sectionOptions = [
        {"key": "trainingAlerts", "label": "Training alerts"},
        {"key": "trackedQuestions", "label": "Tracked issue questions editor"},
        {"key": "customMonitors", "label": "Custom monitored stats"},
        {"key": "staffChart", "label": "People submitted about chart"},
        {"key": "issueChart", "label": "Recurring issues chart"},
        {"key": "trendChart", "label": "Trend over time chart"},
        {"key": "topIssuesTable", "label": "Top recurring issues table"},
        {"key": "staffTable", "label": "Staff needing attention table"},
        {"key": "teamTable", "label": "Team breakdown table"},
        {"key": "supervisorTable", "label": "Supervisor breakdown table"},
        {"key": "recentFeedback", "label": "Recent feedback comments"},
    ]
    summaryCardOptions = [
        {"key": "totalSubmissions", "label": "Total submissions"},
        {"key": "submittedToday", "label": "Submitted today"},
        {"key": "submittedThisWeek", "label": "Submitted this week"},
        {"key": "submittedThisMonth", "label": "Submitted this month"},
        {"key": "uniqueStaffMembers", "label": "Unique staff members"},
        {"key": "mostCommonIssue", "label": "Most common issue"},
        {"key": "mostSubmittedAbout", "label": "Most submitted about"},
        {"key": "highestVolumeTeam", "label": "Highest volume team"},
    ]

    formObj = Form.query.filter_by(is_active=True).order_by(Form.form_id.desc()).first()
    if not formObj:
        return render_template(
            "stats.html",
            statsReady=False,
            canEditStats=canEditStats,
            isDeveloper=isDeveloper,
            trackedQuestionKeys=[],
            candidateQuestions=[],
            versionFilters=[],
            selectedFormVersionIds=[],
            visibleSectionKeys=visibleSectionKeys,
            visibleSummaryCardKeys=visibleSummaryCardKeys,
            sectionOptions=sectionOptions,
            summaryCardOptions=summaryCardOptions,
            customMonitorItems=[],
            customMonitorMeasureOptions=CUSTOM_MONITOR_MEASURE_OPTIONS,
            monitorQuestionOptions=[],
            customMonitorCards=[],
            startDateValue="",
            endDateValue="",
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
            canEditStats=canEditStats,
            isDeveloper=isDeveloper,
            trackedQuestionKeys=[],
            candidateQuestions=[],
            versionFilters=[],
            selectedFormVersionIds=[],
            visibleSectionKeys=visibleSectionKeys,
            visibleSummaryCardKeys=visibleSummaryCardKeys,
            sectionOptions=sectionOptions,
            summaryCardOptions=summaryCardOptions,
            customMonitorItems=[],
            customMonitorMeasureOptions=CUSTOM_MONITOR_MEASURE_OPTIONS,
            monitorQuestionOptions=[],
            customMonitorCards=[],
            startDateValue="",
            endDateValue="",
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
    latestQuestionKeyById = {}
    subjectQuestionIds = []
    supervisorQuestionIds = []
    teamQuestionIds = []
    feedbackQuestionIds = []
    candidateQuestionMap = {}
    monitorQuestionMap = {}

    for formVersionQuestion, questionVersion in allFormLinks:
        qid = int(questionVersion.question_version_id)
        questionById[qid] = questionVersion
        optionMap = {}
        for option in questionVersion.options:
            optionMap[normaliseStatsText(option.option_value)] = normaliseStatsText(option.option_label) or normaliseStatsText(option.option_value)
        optionLabelByQuestion[qid] = optionMap

        promptText = normaliseStatsText(questionVersion.prompt_text)
        promptKey = normaliseStatsKey(promptText)

        if isSubjectNamePrompt(promptText):
            subjectQuestionIds.append(qid)
        if isSupervisorNamePrompt(promptText):
            supervisorQuestionIds.append(qid)
        if isSubjectTeamPrompt(promptText):
            teamQuestionIds.append(qid)
        if isFeedbackCommentPrompt(promptText):
            feedbackQuestionIds.append(qid)

        isCandidate = questionVersion.response_type in ("select", "multi_select", "rating") and not isIdentityPrompt(promptText)
        if promptText and promptKey not in monitorQuestionMap:
            monitorQuestionMap[promptKey] = {
                "questionKey": promptKey,
                "promptText": promptText,
                "responseType": questionVersion.response_type,
            }

        if isCandidate and promptKey not in candidateQuestionMap:
            candidateQuestionMap[promptKey] = {
                "questionKey": promptKey,
                "promptText": promptText,
                "responseType": questionVersion.response_type,
            }

        if int(formVersionQuestion.form_version_id) == int(latestVersion.form_version_id):
            latestQuestionKeyById[qid] = promptKey

    candidateQuestions = sorted(candidateQuestionMap.values(), key=lambda item: item["promptText"].lower())
    monitorQuestionOptions = sorted(monitorQuestionMap.values(), key=lambda item: item["promptText"].lower())
    customMonitorItems = sanitizeCustomMonitorItems(statsState.get("customMonitorItems", []), monitorQuestionMap)

    trackedQuestionKeys = [str(x) for x in statsState.get("trackedQuestionKeys", []) if str(x).strip() != ""]
    if not trackedQuestionKeys:
        legacyTrackedIds = [int(x) for x in statsState.get("trackedQuestionVersionIds", []) if str(x).isdigit()]
        for qid in legacyTrackedIds:
            promptKey = latestQuestionKeyById.get(int(qid))
            if promptKey and promptKey not in trackedQuestionKeys:
                trackedQuestionKeys.append(promptKey)

    selectedFormVersionIds = []
    for value in request.args.getlist("versions"):
        if str(value).isdigit() and int(value) in versionById:
            selectedFormVersionIds.append(int(value))
    if not selectedFormVersionIds:
        selectedFormVersionIds = [int(item.form_version_id) for item in formVersions]

    startDateValue = (request.values.get("startDate") or "").strip()
    endDateValue = (request.values.get("endDate") or "").strip()

    if request.method == "POST" and canEditStats:
        selectedKeys = request.form.getlist("trackedQuestionKeys")
        trackedQuestionKeys = [str(x) for x in selectedKeys if str(x).strip() != ""]
        trackedQuestionVersionIds = [qid for qid, promptKey in latestQuestionKeyById.items() if promptKey in trackedQuestionKeys]
        visibleSectionKeys = request.form.getlist("visibleSectionKeys")
        visibleSummaryCardKeys = request.form.getlist("visibleSummaryCardKeys")

        removeMonitorIds = {normaliseStatsText(value) for value in request.form.getlist("removeCustomMonitorIds") if normaliseStatsText(value)}
        customMonitorItemsToSave = []
        existingMonitorIds = request.form.getlist("customMonitorIds")
        existingMonitorTitles = request.form.getlist("customMonitorTitles")
        existingMonitorQuestionKeys = request.form.getlist("customMonitorQuestionKeys")
        existingMonitorMeasureTypes = request.form.getlist("customMonitorMeasureTypes")
        allowedMeasureTypes = {item["key"] for item in CUSTOM_MONITOR_MEASURE_OPTIONS}

        for index, monitorId in enumerate(existingMonitorIds):
            cleanMonitorId = normaliseStatsText(monitorId)
            if not cleanMonitorId or cleanMonitorId in removeMonitorIds:
                continue
            title = normaliseStatsText(existingMonitorTitles[index] if index < len(existingMonitorTitles) else "")
            questionKey = normaliseStatsKey(existingMonitorQuestionKeys[index] if index < len(existingMonitorQuestionKeys) else "")
            measureType = normaliseStatsText(existingMonitorMeasureTypes[index] if index < len(existingMonitorMeasureTypes) else "")
            if questionKey not in monitorQuestionMap:
                continue
            if measureType not in allowedMeasureTypes:
                measureType = "answeredCount"
            if not title:
                title = f"{monitorQuestionMap[questionKey]['promptText']} · {getCustomMonitorMeasureLabel(measureType)}"
            customMonitorItemsToSave.append({
                "monitorId": cleanMonitorId,
                "title": title,
                "questionKey": questionKey,
                "measureType": measureType,
            })

        newCustomMonitorTitle = normaliseStatsText(request.form.get("newCustomMonitorTitle"))
        newCustomMonitorQuestionKey = normaliseStatsKey(request.form.get("newCustomMonitorQuestionKey"))
        newCustomMonitorMeasureType = normaliseStatsText(request.form.get("newCustomMonitorMeasureType"))
        if newCustomMonitorMeasureType not in allowedMeasureTypes:
            newCustomMonitorMeasureType = "answeredCount"
        if newCustomMonitorTitle and newCustomMonitorQuestionKey in monitorQuestionMap:
            customMonitorItemsToSave.append({
                "monitorId": uuid.uuid4().hex[:12],
                "title": newCustomMonitorTitle,
                "questionKey": newCustomMonitorQuestionKey,
                "measureType": newCustomMonitorMeasureType,
            })

        customMonitorItems = sanitizeCustomMonitorItems(customMonitorItemsToSave, monitorQuestionMap)
        setStatsState(
            trackedQuestionKeys,
            trackedQuestionVersionIds,
            visibleSectionKeys=visibleSectionKeys,
            visibleSummaryCardKeys=visibleSummaryCardKeys,
            customMonitorItems=customMonitorItems,
        )
        flash("Stats page options updated.", "success")
        redirectParts = []
        for value in request.form.getlist("versions"):
            if str(value).isdigit() and int(value) in versionById:
                redirectParts.append(f"versions={int(value)}")
        if startDateValue:
            redirectParts.append(f"startDate={startDateValue}")
        if endDateValue:
            redirectParts.append(f"endDate={endDateValue}")
        redirectUrl = url_for("stats")
        if redirectParts:
            redirectUrl = f"{redirectUrl}?{'&'.join(redirectParts)}"
        return redirect(redirectUrl)

    if not trackedQuestionKeys:
        trackedQuestionKeys = [item["questionKey"] for item in candidateQuestions]

    versionFilters = []
    for item in sorted(formVersions, key=lambda value: (int(value.version_number), int(value.form_version_id)), reverse=True):
        versionTitle = normaliseStatsText(item.title) or normaliseStatsText(formObj.title) or "Untitled form"
        versionFilters.append({
            "formVersionId": int(item.form_version_id),
            "versionNumber": int(item.version_number),
            "title": versionTitle,
            "isSelected": int(item.form_version_id) in selectedFormVersionIds,
        })

    submissionsQuery = (
        FormSubmission.query
        .filter(FormSubmission.form_id == formObj.form_id)
        .filter(FormSubmission.form_version_id.in_(selectedFormVersionIds))
    )

    if startDateValue:
        try:
            startDate = datetime.strptime(startDateValue, "%Y-%m-%d")
            submissionsQuery = submissionsQuery.filter(FormSubmission.submitted_at >= startDate)
        except ValueError:
            startDateValue = ""
    if endDateValue:
        try:
            endDateExclusive = datetime.strptime(endDateValue, "%Y-%m-%d") + timedelta(days=1)
            submissionsQuery = submissionsQuery.filter(FormSubmission.submitted_at < endDateExclusive)
        except ValueError:
            endDateValue = ""

    submissions = submissionsQuery.order_by(FormSubmission.submitted_at.asc(), FormSubmission.submission_id.asc()).all()
    submissionIds = [int(sub.submission_id) for sub in submissions]
    answers = []
    if submissionIds:
        answers = SubmissionAnswer.query.filter(SubmissionAnswer.submission_id.in_(submissionIds)).all()

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
    answerCounterByPromptKey = defaultdict(Counter)
    answeredSubmissionCounterByPromptKey = Counter()

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
            promptText = normaliseStatsText(questionVersion.prompt_text)
            promptKey = normaliseStatsKey(promptText)
            answerLabels = buildAnswerLabelList(questionVersion, answer, optionLabelByQuestion)

            if answerLabels:
                answeredSubmissionCounterByPromptKey[promptKey] += 1
                for answerLabel in answerLabels:
                    cleanAnswerLabel = normaliseStatsText(answerLabel)
                    if cleanAnswerLabel:
                        answerCounterByPromptKey[promptKey][cleanAnswerLabel] += 1

            if qid in subjectQuestionIds and answerLabels:
                candidateValue = sanitizeStatsEntityValue(answerLabels[0], "staff")
                if candidateValue:
                    subjectName = candidateValue
            if qid in supervisorQuestionIds and answerLabels:
                candidateValue = sanitizeStatsEntityValue(answerLabels[0], "supervisor")
                if candidateValue:
                    supervisorName = candidateValue
            if qid in teamQuestionIds and answerLabels:
                for answerLabel in answerLabels:
                    candidateValue = sanitizeStatsEntityValue(answerLabel, "team")
                    if candidateValue and candidateValue not in teamValues:
                        teamValues.append(candidateValue)
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

    knownStaffCounter = Counter({name: count for name, count in staffCounter.items() if normaliseStatsKey(name) != "unknown"})
    knownTeamCounter = Counter({name: count for name, count in teamCounter.items() if normaliseStatsKey(name) != "unknown"})
    knownSupervisorCounter = Counter({name: count for name, count in supervisorCounter.items() if normaliseStatsKey(name) != "unknown"})

    currentDateTime = datetime.now()
    startOfToday = currentDateTime.replace(hour=0, minute=0, second=0, microsecond=0)
    startOfWeek = startOfToday - timedelta(days=startOfToday.weekday())
    startOfMonth = startOfToday.replace(day=1)
    submittedTodayCount = 0
    submittedThisWeekCount = 0
    submittedThisMonthCount = 0
    for submission in submissions:
        submittedAt = submission.submitted_at
        if not submittedAt or submittedAt > currentDateTime:
            continue
        if submittedAt >= startOfToday:
            submittedTodayCount += 1
        if submittedAt >= startOfWeek:
            submittedThisWeekCount += 1
        if submittedAt >= startOfMonth:
            submittedThisMonthCount += 1

    topStaff = knownStaffCounter.most_common(10)
    topIssues = issueCounter.most_common(10)
    topTeams = knownTeamCounter.most_common(10) or teamCounter.most_common(10)
    topSupervisors = knownSupervisorCounter.most_common(10) or supervisorCounter.most_common(10)

    staffTable = []
    for staffName, count in knownStaffCounter.most_common(15):
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
    for supervisorName, count in (knownSupervisorCounter.most_common(15) or supervisorCounter.most_common(15)):
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
            promptText = normaliseStatsText(questionVersion.prompt_text)
            promptKey = normaliseStatsKey(promptText)
            if promptKey not in trackedQuestionKeySet:
                continue
            answerValues = buildAnswerLabelList(questionVersion, answer, optionLabelByQuestion)
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

    summaryCardDefinitions = [
        {"key": "totalSubmissions", "label": "Total submissions", "value": len(submissions)},
        {"key": "submittedToday", "label": "Submitted today", "value": submittedTodayCount},
        {"key": "submittedThisWeek", "label": "Submitted this week", "value": submittedThisWeekCount},
        {"key": "submittedThisMonth", "label": "Submitted this month", "value": submittedThisMonthCount},
        {"key": "uniqueStaffMembers", "label": "Unique staff members", "value": len(knownStaffCounter)},
        {"key": "mostCommonIssue", "label": "Most common issue", "value": topIssues[0][0] if topIssues else "No issue data yet"},
        {"key": "mostSubmittedAbout", "label": "Most submitted about", "value": topStaff[0][0] if topStaff else "No data yet"},
        {"key": "highestVolumeTeam", "label": "Highest volume team", "value": topTeams[0][0] if topTeams else "No data yet"},
    ]
    visibleSummaryCardKeySet = set(visibleSummaryCardKeys or DEFAULT_VISIBLE_SUMMARY_CARD_KEYS)
    summaryCards = [item for item in summaryCardDefinitions if item["key"] in visibleSummaryCardKeySet]

    customMonitorCards = []
    for monitorItem in customMonitorItems:
        questionInfo = monitorQuestionMap.get(monitorItem["questionKey"])
        customMonitorCards.append({
            "title": monitorItem["title"],
            "value": buildCustomMonitorValue(monitorItem, answerCounterByPromptKey, answeredSubmissionCounterByPromptKey),
            "questionPrompt": questionInfo["promptText"] if questionInfo else monitorItem["questionKey"],
            "measureLabel": getCustomMonitorMeasureLabel(monitorItem["measureType"]),
        })

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
        canEditStats=canEditStats,
        isDeveloper=isDeveloper,
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
        visibleSectionKeys=visibleSectionKeys,
        visibleSummaryCardKeys=visibleSummaryCardKeys,
        sectionOptions=sectionOptions,
        summaryCardOptions=summaryCardOptions,
        customMonitorItems=customMonitorItems,
        customMonitorMeasureOptions=CUSTOM_MONITOR_MEASURE_OPTIONS,
        monitorQuestionOptions=monitorQuestionOptions,
        customMonitorCards=customMonitorCards,
        startDateValue=startDateValue,
        endDateValue=endDateValue,
    )

if __name__ == "__main__":
    app.run(debug=True)
