

from __future__ import annotations
import os
import uuid
import json
from functools import wraps
from decimal import Decimal
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from config import Config

app = Flask(__name__)


def ensureBrandingState():
    uploadLogoFolder = app.config.get("UPLOAD_LOGO_FOLDER")
    if not uploadLogoFolder:
        uploadLogoFolder = os.path.join(app.root_path, "static", "uploads", "logos")
    if uploadLogoFolder:
        os.makedirs(uploadLogoFolder, exist_ok=True)
    brandingStateFilename = app.config.get("BRANDING_STATE_FILENAME", "siteBranding.json")
    brandingStatePath = os.path.join(uploadLogoFolder, brandingStateFilename)
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
    password_hash = db.Column(db.String(255), nullable=False)
    role_id = db.Column(db.SmallInteger, db.ForeignKey("roles.role_id"), nullable=False)
    is_active = db.Column(db.Boolean, nullable=False, default=True)

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


def login_required(view_func):
    @wraps(view_func)
    def wrapper(*args, **kwargs):
        if not session.get("user_id"):
            return redirect(url_for("index"))
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
    logoFilename = brandingState.get("logoFilename") or app.config.get("DEFAULT_LOGO_FILENAME")
    siteLogoUrl = url_for("static", filename=f"uploads/logos/{logoFilename}")
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



def seed_roles_if_missing():
    for role_name in ("admin", "standard", "developer"):
        if not Role.query.filter_by(role_name=role_name).first():
            db.session.add(Role(role_name=role_name))
    db.session.commit()


@app.before_request
def _ensure_db_ready():
    if not app.config.get("_SEEDED_ROLES"):
        db.session.execute(db.text("SELECT 1"))
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
        username = (request.form.get("username") or "").strip()
        password = request.form.get("password") or ""

        user = User.query.filter_by(username=username).first()
        if not user or not user.is_active or not check_password_hash(user.password_hash, password):
            flash("Invalid username or password.", "error")
            return render_template("index.html"), 401

        session["user_id"] = int(user.user_id)
        session["username"] = user.username
        session["role_name"] = user.role.role_name if user.role else None
        return redirect(url_for("dashboard"))

    return render_template("index.html")


@app.route("/signup", methods=["GET", "POST"])
def signup():
    roles = Role.query.all()

    if request.method == "POST":
        username = (request.form.get("username") or "").strip()
        password = request.form.get("password") or ""
        confirm = request.form.get("confirm_password") or ""
        role_id = request.form.get("role_id")

        if not username or len(username) > 64:
            flash("Invalid username.", "error")
            return render_template("signup.html", roles=roles), 400

        if password != confirm or len(password) < 8:
            flash("Invalid password.", "error")
            return render_template("signup.html", roles=roles), 400

        if not role_id:
            flash("Role selection required.", "error")
            return render_template("signup.html", roles=roles), 400

        if User.query.filter_by(username=username).first():
            flash("Username already exists.", "error")
            return render_template("signup.html", roles=roles), 409

        user = User(
            username=username,
            password_hash=generate_password_hash(password),
            role_id=int(role_id),
            is_active=True,
        )
        db.session.add(user)
        db.session.commit()

        flash("Account created.", "success")
        return redirect(url_for("index"))

    return render_template("signup.html", roles=roles)


@app.route("/reset-password", methods=["GET", "POST"])
def reset_password():
    if request.method == "POST":
        username = (request.form.get("username") or "").strip()
        new_password = request.form.get("new_password") or ""
        confirm = request.form.get("confirm_new_password") or ""

        if new_password != confirm or len(new_password) < 8:
            flash("Invalid password.", "error")
            return render_template("reset_password.html"), 400

        user = User.query.filter_by(username=username).first()
        if not user:
            flash("User not found.", "error")
            return render_template("reset_password.html"), 404

        user.password_hash = generate_password_hash(new_password)
        db.session.commit()

        flash("Password updated.", "success")
        return redirect(url_for("index"))

    return render_template("reset_password.html")


@app.route("/dashboard")
@login_required
def dashboard():
    is_admin = session.get("role_name") == "admin"
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
    is_admin = session.get("role_name") == "admin"
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


@app.route("/stats")
@login_required
def stats():
    return render_template("stats.html")


if __name__ == "__main__":
    app.run(debug=True)