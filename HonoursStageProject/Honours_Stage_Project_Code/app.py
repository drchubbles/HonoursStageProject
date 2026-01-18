# app.py
from __future__ import annotations

import os
import uuid
from functools import wraps
from decimal import Decimal

from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-change-me")

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


class FormVersionQuestion(db.Model):
    __tablename__ = "form_version_questions"

    form_version_question_id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    form_version_id = db.Column(db.BigInteger, db.ForeignKey("form_versions.form_version_id"), nullable=False)
    question_version_id = db.Column(db.BigInteger, db.ForeignKey("question_versions.question_version_id"), nullable=False)
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


def seed_roles_if_missing():
    for role_name in ("admin", "standard"):
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


def _get_questions_for_version(form_version_id: int):
    return (
        db.session.query(QuestionVersion)
        .join(
            FormVersionQuestion,
            FormVersionQuestion.question_version_id == QuestionVersion.question_version_id,
        )
        .filter(FormVersionQuestion.form_version_id == form_version_id)
        .order_by(FormVersionQuestion.sort_order)
        .all()
    )


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
    return render_template("dashboard.html")


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
        questions = _get_questions_for_version(latest_version.form_version_id)

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

    questions = _get_questions_for_version(latest_version.form_version_id)

    return render_template(
        "form.html",
        form=form_obj,
        form_version=latest_version,
        questions=questions,
        is_admin=session.get("role_name") == "admin",
    )


@app.route("/edit-form", methods=["GET", "POST"])
@admin_required
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
        next_version_number = int(latest_version.version_number) + 1

        ordered_existing = request.form.getlist("existing_qv_id")
        delete_ids = set(request.form.getlist("delete_qv_id"))

        final_existing_qv_ids = []
        qv_id_map = {}

        for qv_id_str in ordered_existing:
            if not qv_id_str:
                continue
            if qv_id_str in delete_ids:
                continue

            qv_id = int(qv_id_str)
            current_qv = QuestionVersion.query.filter_by(question_version_id=qv_id).first()
            if not current_qv:
                continue

            new_prompt = (request.form.get(f"existing_prompt_{qv_id}") or "").strip()
            new_type = (request.form.get(f"existing_type_{qv_id}") or "").strip()
            new_required = (request.form.get(f"existing_required_{qv_id}") or "0").strip()
            new_help = (request.form.get(f"existing_help_{qv_id}") or "").strip()
            new_options_text = request.form.get(f"existing_options_{qv_id}") or ""

            if not new_prompt:
                new_prompt = current_qv.prompt_text

            if new_type not in ("text", "number", "rating", "select", "multi_select"):
                new_type = current_qv.response_type

            req_bool = (new_required == "1")
            help_val = new_help if new_help else None

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
            if (current_qv.help_text or "") != (help_val or ""):
                changed = True
            if new_type in ("select", "multi_select") or current_qv.response_type in ("select", "multi_select"):
                if current_options_lines != new_options_lines:
                    changed = True

            if not changed:
                final_existing_qv_ids.append(qv_id)
                qv_id_map[qv_id] = qv_id
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
                help_text=help_val,
                is_active=True,
                created_by=user_id,
            )
            db.session.add(new_qv)
            db.session.flush()

            if new_type in ("select", "multi_select"):
                for idx, label in enumerate(new_options_lines):
                    db.session.add(
                        QuestionVersionOption(
                            question_version_id=new_qv.question_version_id,
                            option_value=label,
                            option_label=label,
                            sort_order=idx,
                        )
                    )

            final_existing_qv_ids.append(int(new_qv.question_version_id))
            qv_id_map[qv_id] = int(new_qv.question_version_id)

        new_prompts = request.form.getlist("new_prompt")
        new_types = request.form.getlist("new_type")
        new_requireds = request.form.getlist("new_required")
        new_helps = request.form.getlist("new_help")
        new_options_texts = request.form.getlist("new_options")

        created_new_qv_ids = []
        n = max(len(new_prompts), len(new_types), len(new_requireds), len(new_helps), len(new_options_texts))
        for i in range(n):
            prompt = (new_prompts[i] if i < len(new_prompts) else "").strip()
            rtype = (new_types[i] if i < len(new_types) else "").strip()
            req = (new_requireds[i] if i < len(new_requireds) else "0").strip()
            help_text = (new_helps[i] if i < len(new_helps) else "").strip()
            options_text = (new_options_texts[i] if i < len(new_options_texts) else "") or ""

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
                help_text=(help_text if help_text else None),
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

            created_new_qv_ids.append(int(qv.question_version_id))

        all_qv_ids = final_existing_qv_ids + created_new_qv_ids

        new_fv = FormVersion(
            form_id=form_obj.form_id,
            version_number=next_version_number,
            created_by=user_id,
            notes=None,
        )
        db.session.add(new_fv)
        db.session.flush()

        for idx, qv_id in enumerate(all_qv_ids):
            db.session.add(
                FormVersionQuestion(
                    form_version_id=new_fv.form_version_id,
                    question_version_id=int(qv_id),
                    sort_order=idx,
                )
            )

        all_set = set(int(x) for x in all_qv_ids)

        b_sources = request.form.getlist("branch_source")
        b_targets = request.form.getlist("branch_target")
        b_operators = request.form.getlist("branch_operator")
        b_compare_option_values = request.form.getlist("branch_compare_option_value")
        b_actions = request.form.getlist("branch_action")
        b_priorities = request.form.getlist("branch_priority")

        m = max(len(b_sources), len(b_targets), len(b_operators), len(b_compare_option_values), len(b_actions), len(b_priorities))
        for i in range(m):
            src_raw = (b_sources[i] if i < len(b_sources) else "").strip()
            tgt_raw = (b_targets[i] if i < len(b_targets) else "").strip()
            op = (b_operators[i] if i < len(b_operators) else "equals").strip() or "equals"
            cov = (b_compare_option_values[i] if i < len(b_compare_option_values) else None)
            act = (b_actions[i] if i < len(b_actions) else "goto").strip() or "goto"
            pr_raw = (b_priorities[i] if i < len(b_priorities) else "0").strip() or "0"

            if not src_raw or not tgt_raw:
                continue

            try:
                src_old = int(src_raw)
                tgt_old = int(tgt_raw)
                pr = int(pr_raw)
            except ValueError:
                continue

            src = int(qv_id_map.get(src_old, src_old))
            tgt = int(qv_id_map.get(tgt_old, tgt_old))

            if src not in all_set or tgt not in all_set:
                continue

            if op not in ("equals", "not_equals", "in", "not_in", "gt", "gte", "lt", "lte", "contains", "is_empty", "is_not_empty"):
                op = "equals"
            if act not in ("show", "hide", "goto"):
                act = "goto"

            db.session.add(
                FormQuestionBranching(
                    form_version_id=new_fv.form_version_id,
                    source_question_version_id=src,
                    target_question_version_id=tgt,
                    operator=op,
                    compare_option_value=(cov if cov else None),
                    compare_text=None,
                    compare_number=None,
                    action=act,
                    priority=pr,
                )
            )

        db.session.commit()
        flash(f"Form updated. New version: {next_version_number}", "success")
        return redirect(url_for("form"))

    questions = _get_questions_for_version(latest_version.form_version_id)

    branches = (
        FormQuestionBranching.query
        .filter(FormQuestionBranching.form_version_id == latest_version.form_version_id)
        .filter(FormQuestionBranching.action == "goto")
        .all()
    )

    branch_map = {}
    for b in branches:
        src = int(b.source_question_version_id)
        tgt = int(b.target_question_version_id)
        key = (b.compare_option_value or "").strip()
        if not key:
            continue
        if src not in branch_map:
            branch_map[src] = {}
        branch_map[src][key] = tgt

    return render_template(
        "editform.html",
        form=form_obj,
        form_version=latest_version,
        questions=questions,
        branch_map=branch_map,
    )


@app.route("/stats")
@login_required
def stats():
    return render_template("stats.html")


if __name__ == "__main__":
    app.run(debug=True)
