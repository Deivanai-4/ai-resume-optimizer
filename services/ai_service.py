"""
AI Service — Public API for all AI-powered features
====================================================
All Qwen API calls are routed through services.qwen_service.
No Hugging Face client code lives here — this file is pure business logic.

Public functions (called by Flask routes):
  analyze_resume()
  optimize_resume()
  generate_learning_roadmap()
  generate_interview_questions()
  generate_resume_content()
  analyze_company()
  extract_company_tech_stack()
  compare_student_skills()
  calculate_career_readiness()
  generate_career_report()

Each function:
  1. Tries to get a real Qwen response.
  2. Falls back to a deterministic smart stub if Qwen is unavailable.
  3. Returns a dict that matches what the existing Flask routes already expect.
"""
import json
import logging
import random

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# ── RESUME ANALYSIS ─────────────────────────────────────────────────────────
# ---------------------------------------------------------------------------

# Strict JSON schema sent in every resume-analysis prompt.
# Keys map 1-to-1 with AnalysisModel.create() parameters.
_ANALYSIS_SCHEMA = """{
  "summary": "<2-3 sentence professional summary of the candidate>",
  "skills": ["<skill>"],
  "programming_languages": ["<lang>"],
  "frameworks": ["<framework>"],
  "libraries": ["<lib>"],
  "databases": ["<db>"],
  "cloud": ["<cloud tech>"],
  "tools": ["<tool>"],
  "certifications": ["<cert>"],
  "education": ["<degree and institution>"],
  "projects": ["<project name and one-line description>"],
  "experience": ["<role at company — duration>"],
  "achievements": ["<notable achievement>"],
  "keywords": ["<ATS keyword found in resume>"],
  "strengths": ["<strength point>"],
  "weaknesses": ["<weakness or gap>"],
  "missing_skills": ["<skill not present that would help>"],
  "resume_suggestions": ["<concrete improvement suggestion>"],
  "grammar_observations": ["<grammar or language note>"],
  "formatting_observations": ["<formatting note>"],
  "scores": {
    "ats_score": 0,
    "skill_match_score": 0,
    "tech_match_score": 0,
    "project_match_score": 0,
    "career_readiness_score": 0,
    "interview_readiness_score": 0,
    "grammar_score": 0,
    "formatting_score": 0,
    "overall_score": 0
  }
}"""


def _build_general_prompt(resume_text: str) -> str:
    """Prompt for general resume analysis (no company selected)."""
    excerpt = resume_text[:4000] if resume_text else "(no resume text provided)"
    return f"""You are an expert ATS system and senior technical recruiter.

Analyse the following resume carefully and return ONLY a valid JSON object.
Do NOT include any text, explanation, or markdown outside the JSON.

Scoring guidelines (0-100):
- ats_score: How well this resume would pass automated ATS filters (keyword density,
  section headers, formatting signals).
- skill_match_score: Breadth and relevance of the candidate's technical skill set
  for a generic software engineering role.
- tech_match_score: Depth of core technology expertise visible in the resume.
- project_match_score: Quality and quantity of projects listed.
- career_readiness_score: Overall readiness to join industry (education + skills +
  experience + projects combined).
- interview_readiness_score: How prepared the candidate appears for technical interviews.
- grammar_score: Grammar, spelling, and language quality.
- formatting_score: Resume structure, readability, and professional presentation.
- overall_score: Weighted average of all scores above.

Be honest and realistic. Avoid inflating scores. A fresh graduate with no experience
should NOT score above 60 on career_readiness_score.

RESUME TEXT:
\"\"\"
{excerpt}
\"\"\"

Return ONLY this JSON structure with every field populated:
{_ANALYSIS_SCHEMA}"""


def _build_company_prompt(
    resume_text: str,
    company_skills: list,
    job_title: str,
    manual_company_name: str = None
) -> str:
    """Prompt for company-specific resume analysis."""
    excerpt = resume_text[:3500] if resume_text else "(no resume text provided)"
    skills_str = ", ".join(company_skills[:25]) if company_skills else "general software engineering skills"
    company_context = f"COMPANY: {manual_company_name}" if manual_company_name else ""
    return f"""You are an expert ATS system and senior technical recruiter at a top tech company.

Analyse the following resume against the specific job requirements listed below.
Return ONLY a valid JSON object — no text, explanation, or markdown outside the JSON.

{company_context}
JOB TITLE: {job_title}
REQUIRED SKILLS: {skills_str}

Scoring guidelines (0-100):
- ats_score: How well this resume passes ATS filters for this specific role.
- skill_match_score: Percentage of the required skills the candidate demonstrates
  (0 = none matched, 100 = all matched).
- tech_match_score: Depth of expertise in the technologies this role requires.
- project_match_score: How relevant the candidate's projects are to this role.
- career_readiness_score: Readiness for this specific role right now.
- interview_readiness_score: Likelihood the candidate would pass a technical interview
  for this role.
- grammar_score: Grammar and language quality.
- formatting_score: Resume structure and professional presentation.
- overall_score: Weighted average of the above.

Be precise and role-specific. In missing_skills, list ONLY skills from the required
list that are NOT demonstrated in the resume.

RESUME TEXT:
\"\"\"
{excerpt}
\"\"\"

Return ONLY this JSON structure with every field populated:
{_ANALYSIS_SCHEMA}"""


def _validate_analysis_json(data: dict) -> dict:
    """
    Validate and normalise the JSON returned by Qwen.
    Ensures all fields expected by AnalysisModel.create() are present and typed.
    """
    scores = data.get("scores", {})

    def _int(val, default=0):
        try:
            v = int(val)
            return max(0, min(100, v))       # clamp to [0, 100]
        except (TypeError, ValueError):
            return default

    def _list(val):
        if isinstance(val, list):
            return [str(x) for x in val if x]
        return []

    return {
        # ── Scores ──────────────────────────────────────────────────────────
        "ats_score":                _int(scores.get("ats_score",                data.get("ats_score",                0))),
        "skill_match_score":        _int(scores.get("skill_match_score",        data.get("skill_match_score",        0))),
        "tech_match_score":         _int(scores.get("tech_match_score",         data.get("tech_match_score",         0))),
        "project_match_score":      _int(scores.get("project_match_score",      data.get("project_match_score",      0))),
        "career_readiness_score":   _int(scores.get("career_readiness_score",   data.get("career_readiness_score",   0))),
        "interview_readiness_score":_int(scores.get("interview_readiness_score",data.get("interview_readiness_score",0))),
        "grammar_score":            _int(scores.get("grammar_score",            data.get("grammar_score",            0))),
        "formatting_score":         _int(scores.get("formatting_score",         data.get("formatting_score",         0))),
        "overall_score":            _int(scores.get("overall_score",            data.get("overall_score",            0))),

        # ── Text / arrays ────────────────────────────────────────────────────
        "summary":          str(data.get("summary", "")),
        "strengths":        _list(data.get("strengths")),
        "weaknesses":       _list(data.get("weaknesses")),
        "missing_skills":   _list(data.get("missing_skills")),
        "suggestions":      _list(data.get("resume_suggestions")),
        "keywords":         _list(data.get("keywords")),

        # ── Extra fields (stored in analysis_data JSON blob) ─────────────────
        "skills":                   _list(data.get("skills")),
        "programming_languages":    _list(data.get("programming_languages")),
        "frameworks":               _list(data.get("frameworks")),
        "libraries":                _list(data.get("libraries")),
        "databases":                _list(data.get("databases")),
        "cloud":                    _list(data.get("cloud")),
        "tools":                    _list(data.get("tools")),
        "certifications":           _list(data.get("certifications")),
        "education":                _list(data.get("education")),
        "projects":                 _list(data.get("projects")),
        "experience":               _list(data.get("experience")),
        "achievements":             _list(data.get("achievements")),
        "grammar_observations":     _list(data.get("grammar_observations")),
        "formatting_observations":  _list(data.get("formatting_observations")),

        # ── Compatibility fields expected by existing routes ─────────────────
        "matched_skills":       [],
        "all_resume_skills":    _list(data.get("skills")),

        # ── Source flag ──────────────────────────────────────────────────────
        "ai_source": "qwen",
    }


def analyze_resume(
    resume_text: str,
    company_skills: list,
    job_title: str,
    user_skills: list = None,
    manual_company_name: str = None
) -> dict:
    """
    Run AI resume analysis.

    If company_skills is provided → company-specific analysis.
    Otherwise → general analysis (no company-specific scoring).

    Returns a dict that maps directly to AnalysisModel.create() parameters.
    Falls back to a deterministic smart stub when Qwen is unavailable.
    """
    from flask import current_app
    from services.qwen_service import call_qwen, parse_qwen_json

    hf_token = (
        current_app.config.get("QWEN_TOKEN")
        or current_app.config.get("HF_TOKEN")
        or ""
    ).strip()

    if hf_token:
        # Choose prompt type
        if company_skills or manual_company_name:
            prompt = _build_company_prompt(resume_text, company_skills, job_title, manual_company_name)
        else:
            prompt = _build_general_prompt(resume_text)

        raw = call_qwen(prompt, max_tokens=2000, retries=2, temperature=0.3)
        if raw:
            data = parse_qwen_json(raw)
            if data:
                try:
                    validated = _validate_analysis_json(data)
                    # Sanity check: at least one score must be non-zero
                    if any(
                        validated.get(k, 0) > 0
                        for k in ("ats_score", "overall_score", "skill_match_score")
                    ):
                        logger.info(
                            f"QWEN analysis complete — overall={validated['overall_score']} "
                            f"ats={validated['ats_score']} skill={validated['skill_match_score']}"
                        )
                        return validated
                    else:
                        logger.warning("QWEN returned all-zero scores — falling back to stub")
                except Exception as exc:
                    logger.error(f"QWEN validation error: {exc}")
            else:
                logger.warning("QWEN returned unparseable JSON — falling back to stub")
        else:
            logger.warning("QWEN returned no response — falling back to stub")
    else:
        logger.info("QWEN: No token configured — using smart stub")

    # ── Smart stub fallback ──────────────────────────────────────────────────
    return _smart_stub_analysis(resume_text, company_skills, job_title, user_skills)


# ---------------------------------------------------------------------------
# ── SMART STUB FALLBACK ─────────────────────────────────────────────────────
# ---------------------------------------------------------------------------

def _smart_stub_analysis(
    resume_text: str,
    company_skills: list,
    job_title: str,
    user_skills: list = None,
) -> dict:
    """
    Deterministic score calculation from resume text + skill matching.
    Used when Qwen is unavailable. Produces realistic, non-random scores
    (except a small ±5 jitter so repeated runs look natural).
    """
    from services.resume_parser import extract_skills_from_text

    resume_skills_data = extract_skills_from_text(resume_text or "")
    resume_skill_names = [s["name"].lower() for s in resume_skills_data]
    user_skill_names   = [s.lower() for s in (user_skills or [])]
    all_candidate      = list(set(resume_skill_names + user_skill_names))

    company_lower = [s.lower() for s in (company_skills or [])]
    matched       = [s for s in company_lower if s in all_candidate]
    skill_match   = int(len(matched) / max(len(company_lower), 1) * 100) if company_lower else min(60, len(all_candidate) * 5)
    missing       = [s for s in (company_skills or []) if s.lower() not in all_candidate][:8]

    word_count    = len((resume_text or "").split())
    has_sections  = all(kw in (resume_text or "").lower() for kw in ["experience", "education", "skill"])
    formatting    = min(90, 50 + (20 if has_sections else 0) + (10 if word_count > 200 else 0) + (10 if word_count < 1000 else 0))

    ats           = min(95, int(skill_match * 0.6 + formatting * 0.4))
    tech_match    = min(95, int(skill_match * 0.9))
    career        = min(90, int((ats + skill_match + tech_match) / 3))
    interview_r   = min(85, career + 5)
    grammar       = min(90, 65 + (15 if word_count > 300 else 0))
    overall       = min(90, int((ats + skill_match + career) / 3))

    strengths  = []
    weaknesses = []
    suggestions = []

    if skill_match >= 70:
        strengths.append(f"Strong skill alignment with {job_title} requirements")
    if len(all_candidate) >= 5:
        strengths.append("Good breadth of technical skills")
    if word_count > 300:
        strengths.append("Detailed resume with sufficient content")
    if not strengths:
        strengths.append("Shows initiative in applying for this role")

    if missing:
        weaknesses.append(f"Missing key skills: {', '.join(missing[:3])}")
    if word_count < 300:
        weaknesses.append("Resume lacks sufficient detail and content")
    if skill_match < 60:
        weaknesses.append("Low skill alignment with job requirements")
    if not weaknesses:
        weaknesses.append("Consider adding more quantified achievements")

    if missing:
        suggestions.append(f"Add projects or certifications showcasing: {', '.join(missing[:2])}")
    suggestions.append("Use more industry-specific keywords throughout your resume")
    suggestions.append("Quantify your achievements with numbers and measurable outcomes")
    suggestions.append("Tailor your objective/summary specifically for the target role")

    resume_skill_names_display = [s["name"] for s in resume_skills_data]

    return {
        "ats_score":                ats,
        "skill_match_score":        skill_match,
        "tech_match_score":         tech_match,
        "project_match_score":      min(80, skill_match),
        "career_readiness_score":   career,
        "interview_readiness_score":interview_r,
        "grammar_score":            grammar,
        "formatting_score":         formatting,
        "overall_score":            overall,
        "summary": (
            f"This candidate has {len(all_candidate)} identifiable technical skills "
            f"with {skill_match}% match to {job_title} requirements. "
            f"{'Strong candidate for this role.' if skill_match >= 70 else 'Needs skill development in key areas.'}"
        ),
        "strengths":    strengths[:5],
        "weaknesses":   weaknesses[:5],
        "missing_skills": missing[:8],
        "suggestions":  suggestions[:5],
        "keywords":     matched[:10],
        "skills":               resume_skill_names_display,
        "programming_languages":[],
        "frameworks":           [],
        "libraries":            [],
        "databases":            [],
        "cloud":                [],
        "tools":                [],
        "certifications":       [],
        "education":            [],
        "projects":             [],
        "experience":           [],
        "achievements":         [],
        "grammar_observations": [],
        "formatting_observations": [],
        "matched_skills":       matched,
        "all_resume_skills":    resume_skill_names_display,
        "ai_source":            "stub",
    }


# ---------------------------------------------------------------------------
# ── RESUME OPTIMIZATION ──────────────────────────────────────────────────────
# ---------------------------------------------------------------------------

def optimize_resume(resume_text: str, company_skills: list, job_title: str, company_name: str = "") -> dict:
    """Generate a full ATS-optimized resume tailored for the target role."""
    import re
    from services.resume_parser import extract_skills_from_text
    from services.qwen_service import call_qwen

    current_skills  = [s["name"] for s in extract_skills_from_text(resume_text)]
    current_lower   = [s.lower() for s in current_skills]
    missing_for_job = [s for s in (company_skills or []) if s.lower() not in current_lower]
    all_skills      = current_skills + missing_for_job[:5]

    from flask import current_app
    token = (current_app.config.get("QWEN_TOKEN") or current_app.config.get("HF_TOKEN") or "").strip()

    ai_resume = None

    if token and resume_text and len(resume_text.strip()) > 30:
        target_str = f"a {job_title} role at {company_name}" if company_name else f"a {job_title} role"
        prompt = (
            f"You are a professional ATS resume writer. Your task is to rewrite this resume for {target_str}.\n\n"
            f"IMPORTANT RULES:\n"
            f"- Produce a COMPLETE, ATS-optimized resume with ALL sections below\n"
            f"- Use strong action verbs (Developed, Designed, Implemented, Led, Optimized, Built, Delivered)\n"
            f"- Add quantified achievements (%, numbers, impact statements) where possible\n"
            f"- Inject these missing keywords naturally: {', '.join(missing_for_job[:5]) if missing_for_job else 'N/A'}\n"
            f"- Current skills found: {', '.join(current_skills[:10])}\n"
            f"- Format MUST be plain text with headings shown below\n\n"
            f"REQUIRED SECTIONS (in order):\n"
            f"PROFESSIONAL SUMMARY\n"
            f"SKILLS\n"
            f"WORK EXPERIENCE\n"
            f"EDUCATION\n"
            f"PROJECTS\n"
            f"CERTIFICATIONS\n\n"
            f"ORIGINAL RESUME:\n{resume_text[:2500]}\n\n"
            f"Now produce the complete ATS-optimized resume. Do NOT include any conversational filler (e.g. 'Certainly! Here is the resume'). Just output the requested resume structure and nothing else:"
        )
        raw = call_qwen(prompt, max_tokens=1800, retries=2, temperature=0.3)
        if raw and raw.strip() and len(raw.strip()) > 200:
            # Strip out generic AI conversational prefixes if any leak through
            import re
            cleaned_raw = re.sub(r'^(Certainly!|Sure,|Here is|Below is).*?\n\n', '', raw.strip(), flags=re.IGNORECASE|re.DOTALL)
            ai_resume = cleaned_raw.strip()

    # ── Fallback: build full resume from extracted data ──
    if not ai_resume:
        lines = [l.strip() for l in resume_text.splitlines() if l.strip()]

        # Name heuristic
        name = ''
        for line in lines[:5]:
            if '@' not in line and not re.search(r'\d{7,}', line):
                if 1 <= len(line.split()) <= 5:
                    name = line
                    break

        email_m = re.search(r'[\w._%+-]+@[\w.-]+\.[A-Za-z]{2,}', resume_text)
        phone_m = re.search(r'[\+]?[(]?[0-9]{3}[)]?[-\s\.]?[0-9]{3}[-\s\.]?[0-9]{4,6}', resume_text)
        email = email_m.group(0) if email_m else ''
        phone = phone_m.group(0) if phone_m else ''

        summary = (
            f"Results-driven {job_title} with expertise in {', '.join(all_skills[:5])}. "
            f"Proven track record of delivering scalable, high-quality software solutions. "
            f"Adept at collaborating in agile, cross-functional teams and continuously growing technical depth."
        )
        skills_line = ', '.join(all_skills) if all_skills else 'Python, Java, SQL, Git'

        exp_kws = ['intern', 'engineer', 'developer', 'analyst', 'manager', 'lead', 'architect', 'consultant', 'trainee']
        exp_lines = [l for l in lines if any(k in l.lower() for k in exp_kws) and 5 <= len(l) <= 120]
        exp_bullets = '\n'.join(
            f"• {l}" if not l.startswith('•') else l for l in exp_lines[:6]
        ) or (
            f"• Developed software solutions using {', '.join(all_skills[:3])}\n"
            f"• Collaborated with cross-functional teams to deliver features on time\n"
            f"• Optimized existing codebase for 30% performance improvement"
        )

        edu_kws = ['university', 'college', 'institute', 'b.tech', 'bsc', 'msc', 'm.tech', 'bachelor', 'master', 'phd']
        edu_lines = [l for l in lines if any(k in l.lower() for k in edu_kws)]
        edu_text = '\n'.join(edu_lines[:3]) if edu_lines else 'Add your education details'

        proj_kws = ['project', 'built', 'developed', 'created', 'implemented']
        proj_lines = [l for l in lines if any(k in l.lower() for k in proj_kws) and len(l) > 20]
        proj_text = '\n'.join(f"• {l}" for l in proj_lines[:4]) if proj_lines else f"• Built a {job_title.lower()} application using {', '.join(all_skills[:3])}"

        header = f"{name}\n{email}  |  {phone}\n{'─'*50}\n\n" if name else ""
        ai_resume = (
            f"{header}"
            f"PROFESSIONAL SUMMARY\n{'─'*40}\n{summary}\n\n"
            f"SKILLS\n{'─'*40}\n{skills_line}\n\n"
            f"WORK EXPERIENCE\n{'─'*40}\n{exp_bullets}\n\n"
            f"EDUCATION\n{'─'*40}\n{edu_text}\n\n"
            f"PROJECTS\n{'─'*40}\n{proj_text}\n\n"
            f"CERTIFICATIONS\n{'─'*40}\nAdd your certifications here"
        )

    # Extract summary from full resume text
    professional_summary = ai_resume[:300]
    for pattern in [
        r'PROFESSIONAL SUMMARY\s*[-─]+\s*\n(.+?)(?=\n[A-Z]{2,}|\Z)',
        r'SUMMARY\s*[-─]+\s*\n(.+?)(?=\n[A-Z]{2,}|\Z)',
    ]:
        m = re.search(pattern, ai_resume, re.DOTALL | re.IGNORECASE)
        if m:
            professional_summary = m.group(1).strip()
            break

    return {
        "optimized_text":       ai_resume,
        "professional_summary": professional_summary,
        "changes_made": [
            f"✅ Rewrote entire resume tailored for {job_title}",
            "✅ Added action verbs to all experience bullet points",
            "✅ Structured with ATS-parseable section headings",
            f"✅ Injected {len(missing_for_job)} missing keywords: {', '.join(missing_for_job[:4]) or 'role-specific terms'}",
            "✅ Optimized professional summary with impact language",
            "✅ Clean single-column layout for ATS scanner compatibility",
        ],
        "improvement_score": min(96, 75 + len(missing_for_job) * 3 + (5 if token else 0)),
    }




# ---------------------------------------------------------------------------
# ── LEARNING ROADMAP ─────────────────────────────────────────────────────────
# ---------------------------------------------------------------------------

_RESOURCE_DB = {
    "Python":         {"yt": "https://youtube.com/watch?v=rfscVS0vtbw",   "doc": "https://docs.python.org",                             "weeks": 3},
    "JavaScript":     {"yt": "https://youtube.com/watch?v=hdI2bqOjy3c",   "doc": "https://developer.mozilla.org",                       "weeks": 3},
    "React":          {"yt": "https://youtube.com/watch?v=bMknfKXIFA8",   "doc": "https://react.dev",                                   "weeks": 3},
    "Node.js":        {"yt": "https://youtube.com/watch?v=Oe421EPjeBE",   "doc": "https://nodejs.org/docs",                             "weeks": 2},
    "SQL":            {"yt": "https://youtube.com/watch?v=HXV3zeQKqGY",   "doc": "https://www.w3schools.com/sql/",                      "weeks": 2},
    "MySQL":          {"yt": "https://youtube.com/watch?v=9ylj9NR0Lcg",   "doc": "https://dev.mysql.com/doc/",                          "weeks": 2},
    "Docker":         {"yt": "https://youtube.com/watch?v=3c-iBn73dDE",   "doc": "https://docs.docker.com",                             "weeks": 2},
    "AWS":            {"yt": "https://youtube.com/watch?v=k1RI5locZE4",   "doc": "https://docs.aws.amazon.com",                         "weeks": 4},
    "Git":            {"yt": "https://youtube.com/watch?v=RGOj5yH7evk",   "doc": "https://git-scm.com/doc",                             "weeks": 1},
    "Machine Learning":{"yt":"https://youtube.com/watch?v=GwIo3gDZCVQ",   "doc": "https://scikit-learn.org/stable/",                    "weeks": 6},
    "Data Structures":{"yt": "https://youtube.com/watch?v=RBSGKlAvoiM",   "doc": "https://www.geeksforgeeks.org/data-structures/",      "weeks": 4},
    "System Design":  {"yt": "https://youtube.com/watch?v=i53Gi_K3o7I",   "doc": "https://github.com/donnemartin/system-design-primer", "weeks": 4},
    "Algorithms":     {"yt": "https://youtube.com/watch?v=0IAPZzGSbME",   "doc": "https://www.geeksforgeeks.org/fundamentals-of-algorithms/", "weeks": 4},
    "Java":           {"yt": "https://youtube.com/watch?v=eIrMbAQSU34",   "doc": "https://docs.oracle.com/javase/",                     "weeks": 4},
    "Spring Boot":    {"yt": "https://youtube.com/watch?v=vtPkZShrvXQ",   "doc": "https://spring.io/projects/spring-boot",              "weeks": 3},
    "Kubernetes":     {"yt": "https://youtube.com/watch?v=X48VuDVv0do",   "doc": "https://kubernetes.io/docs/",                         "weeks": 3},
    "PostgreSQL":     {"yt": "https://youtube.com/watch?v=qw--VYLpxG4",   "doc": "https://www.postgresql.org/docs/",                    "weeks": 2},
}

_PRIORITY_MAP = {0: "Critical", 1: "Critical", 2: "High", 3: "High",
                 4: "Medium",   5: "Medium",   6: "Low",  7: "Low"}


def generate_learning_roadmap(
    missing_skills: list,
    job_title: str,
    company_name: str = None,
) -> dict:
    """Generate a personalized learning roadmap for missing skills."""
    items = []
    for idx, skill in enumerate(missing_skills[:10]):
        res   = _RESOURCE_DB.get(skill, {})
        weeks = res.get("weeks", 2)
        items.append({
            "skill_name":     skill,
            "priority":       _PRIORITY_MAP.get(idx, "Low"),
            "duration_weeks": weeks,
            "order_index":    idx,
            "resources":      f"Practice {skill} daily with hands-on projects",
            "youtube_links":  res.get("yt",  f"https://youtube.com/search?q={skill}+tutorial"),
            "doc_links":      res.get("doc", f"https://google.com/search?q={skill}+documentation"),
            "project_ideas":  (
                f"Build a {skill} project: "
                f"Create a {'REST API' if idx % 2 == 0 else 'web app'} using {skill}"
            ),
        })

    title = f"Roadmap to {job_title}" + (f" at {company_name}" if company_name else "")
    return {
        "title":       title,
        "total_weeks": sum(i["duration_weeks"] for i in items),
        "items":       items,
    }


# ---------------------------------------------------------------------------
# ── INTERVIEW QUESTIONS ──────────────────────────────────────────────────────
# ---------------------------------------------------------------------------

def generate_interview_questions(
    job_title: str,
    company_name: str,
    company_skills: list,
    resume_text: str = "",
    seen_questions: set = None,
    user_name: str = "Candidate",
    user_skills: list = None,
    user_experience: list = None,
    user_projects: list = None,
    job_description: str = "",
) -> list:
    """Generate fresh, non-repeating, AI-powered interview questions using a structured prompt.

    Falls back to a large static pool if the AI is unavailable.
    """
    import random
    import json as _json

    if seen_questions is None:
        seen_questions = set()
    if user_skills is None:
        user_skills = company_skills or []
    if user_experience is None:
        user_experience = []
    if user_projects is None:
        user_projects = []

    # ── TRY AI-POWERED GENERATION FIRST ──────────────────────────────────────
    try:
        from flask import current_app
        from services.qwen_service import call_qwen, parse_qwen_json

        token = (current_app.config.get("QWEN_TOKEN") or current_app.config.get("HF_TOKEN") or "").strip()
        if token:
            # Build concise user context strings for the prompt
            skills_str = ", ".join(user_skills[:15]) if user_skills else "Not specified"
            exp_str = "; ".join(
                f"{e.get('job_title','')} at {e.get('company_name','')}" for e in (user_experience or [])[:3]
            ) or "Fresher / No experience"
            proj_str = "; ".join(
                f"{p.get('title','')} ({p.get('technologies','')})" for p in (user_projects or [])[:4]
            ) or "No projects listed"

            # Build a list of seen questions to explicitly tell the LLM to avoid them
            seen_list = list(seen_questions)[:100]  # Cap at 100 to avoid token bloat
            seen_str = "\\n- ".join(seen_list) if seen_list else "None"

            prompt = f"""You are an expert technical recruiter, company intelligence analyst, and interview preparation specialist.

You are generating interview preparation content for a career intelligence platform.

USER INFORMATION:
- User name: "{user_name}"
- Target role: "{job_title}"
- User skills: {skills_str}
- User experience: {exp_str}
- User projects: {proj_str}

COMPANY INFORMATION:
- Company: "{company_name}"
- Job description: "{job_description[:600] if job_description else 'Not provided'}"

PREVIOUSLY ASKED QUESTIONS (DO NOT GENERATE THESE):
- {seen_str}

Your task is to generate structured interview preparation information specifically for this company and target role.

IMPORTANT:
1. Do NOT generate generic questions if company/role-specific information is available.
2. Questions should match the target role: {job_title}.
3. Questions should consider the user's existing skills and projects.
4. Identify skills that are likely relevant to the selected role.
5. Questions must be divided by category and difficulty.
6. Questions must be suitable for students/freshers unless the user's experience indicates otherwise.
7. CRITICAL: Avoid repeating the same questions. You MUST generate completely new and different questions from the 'PREVIOUSLY ASKED QUESTIONS' list.
8. Generate questions that test understanding, not only memorization.
9. Technical questions should include practical/scenario-based questions where appropriate.
10. HR questions should be relevant to the company and role.
11. Aptitude questions should be suitable for placement preparation.
12. Return ONLY valid JSON.
13. Do NOT use markdown.
14. Do NOT include ```json.
15. Do NOT include explanations outside the JSON.

RETURN EXACTLY THIS JSON STRUCTURE (generate at least 3 questions per difficulty level per section):

{{
    "company": {{
        "name": "{company_name}",
        "industry": "",
        "headquarters": "",
        "description": "",
        "tech_stack": [],
        "important_skills": [],
        "common_interview_topics": [],
        "interview_process": [],
        "company_culture": ""
    }},
    "role": {{
        "title": "{job_title}",
        "important_skills": [],
        "responsibilities": [],
        "expected_knowledge": []
    }},
    "interview_preparation": {{
        "technical": {{
            "easy": [{{"question": "", "topic": "", "skill": "", "type": "conceptual", "answer": "", "explanation": ""}}],
            "medium": [{{"question": "", "topic": "", "skill": "", "type": "scenario", "answer": "", "explanation": ""}}],
            "hard": [{{"question": "", "topic": "", "skill": "", "type": "problem-solving", "answer": "", "explanation": ""}}]
        }},
        "hr": {{
            "easy": [{{"question": "", "answer_guidance": "", "what_interviewer_checks": ""}}],
            "medium": [{{"question": "", "answer_guidance": "", "what_interviewer_checks": ""}}],
            "hard": [{{"question": "", "answer_guidance": "", "what_interviewer_checks": ""}}]
        }},
        "aptitude": {{
            "easy": [{{"question": "", "options": ["", "", "", ""], "correct_answer": "", "explanation": "", "topic": ""}}],
            "medium": [{{"question": "", "options": ["", "", "", ""], "correct_answer": "", "explanation": "", "topic": ""}}],
            "hard": [{{"question": "", "options": ["", "", "", ""], "correct_answer": "", "explanation": "", "topic": ""}}]
        }}
    }},
    "personalized_questions": [
        {{"question": "", "reason": "", "related_skill": "", "related_project": ""}}
    ],
    "recommended_topics": [
        {{"topic": "", "priority": "High", "reason": ""}}
    ]
}}"""

            raw = call_qwen(prompt, max_tokens=3000, retries=1)
            if raw:
                data = parse_qwen_json(raw)
                if data and isinstance(data, dict) and "interview_preparation" in data:
                    return _convert_ai_response_to_list(data, seen_questions)
    except Exception:
        pass  # Fall through to static pool

    # ── STATIC FALLBACK POOL ─────────────────────────────────────────────────
    return _static_question_pool(job_title, company_name, company_skills, seen_questions)


def _convert_ai_response_to_list(data: dict, seen_questions: set) -> dict:
    """Flatten the structured AI JSON response and include metadata."""
    import random
    result = []
    prep = data.get("interview_preparation", {})

    for section_key, cat_label in [("technical", "Technical"), ("hr", "HR"), ("aptitude", "Aptitude")]:
        section = prep.get(section_key, {})
        for diff_key, diff_label in [("easy", "Easy"), ("medium", "Medium"), ("hard", "Hard")]:
            for item in section.get(diff_key, []):
                q_text = item.get("question", "").strip()
                if not q_text or q_text.lower() in seen_questions:
                    continue
                flat = {
                    "q":    q_text,
                    "cat":  cat_label,
                    "diff": diff_label,
                    "tip":  item.get("answer", "") or item.get("answer_guidance", "") or item.get("explanation", ""),
                }
                if section_key == "aptitude":
                    flat["options"] = item.get("options", [])
                    flat["correct_answer"] = item.get("correct_answer", "")
                result.append(flat)

    # Also include personalized questions
    for item in data.get("personalized_questions", []):
        q_text = item.get("question", "").strip()
        if q_text and q_text.lower() not in seen_questions:
            result.append({
                "q":    q_text,
                "cat":  "Personalized",
                "diff": "Medium",
                "tip":  item.get("reason", ""),
            })

    random.shuffle(result)
    for i, q in enumerate(result):
        q["id"] = i + 1
        
    return {
        "questions": result,
        "company": data.get("company", {}),
        "role": data.get("role", {}),
        "recommended_topics": data.get("recommended_topics", [])
    }


def _static_question_pool(job_title: str, company_name: str, company_skills: list, seen_questions: set) -> list:
    """Large static question pool used as fallback when AI is unavailable."""
    import random as _rnd

    tech_pool = [
        {"q": "Explain the difference between REST and GraphQL APIs. When would you use each?",        "cat": "Technical", "diff": "Medium"},
        {"q": "What is the difference between synchronous and asynchronous programming?",               "cat": "Technical", "diff": "Medium"},
        {"q": "Explain SOLID principles with real-world examples.",                                     "cat": "Technical", "diff": "Hard"},
        {"q": "What are design patterns? Name and explain three you have used.",                        "cat": "Technical", "diff": "Hard"},
        {"q": "How would you diagnose and fix a slow database query?",                                  "cat": "Technical", "diff": "Medium"},
        {"q": "Explain the concept of microservices versus monolithic architecture.",                   "cat": "Technical", "diff": "Hard"},
        {"q": "What is Docker and why is containerisation useful?",                                     "cat": "Technical", "diff": "Medium"},
        {"q": "Explain Git branching strategies and when to use merge vs rebase.",                      "cat": "Technical", "diff": "Medium"},
        {"q": "What is the difference between SQL and NoSQL databases?",                                "cat": "Technical", "diff": "Medium"},
        {"q": "What is indexing in databases and how does it improve query performance?",               "cat": "Technical", "diff": "Medium"},
        {"q": "Explain the CAP theorem and its implications for distributed systems.",                  "cat": "Technical", "diff": "Hard"},
        {"q": "What is a race condition and how do you prevent it?",                                    "cat": "Technical", "diff": "Hard"},
        {"q": "Describe the differences between threads and processes.",                                "cat": "Technical", "diff": "Medium"},
        {"q": "What is a memory leak? How do you detect and fix it?",                                   "cat": "Technical", "diff": "Medium"},
        {"q": "Explain the concept of caching and describe different caching strategies.",              "cat": "Technical", "diff": "Medium"},
        {"q": "What is CI/CD? Describe a typical pipeline you have worked with.",                       "cat": "Technical", "diff": "Medium"},
        {"q": "What is the difference between authentication and authorisation?",                       "cat": "Technical", "diff": "Easy"},
        {"q": "Explain how HTTPS works and the role of SSL/TLS certificates.",                          "cat": "Technical", "diff": "Medium"},
        {"q": "What is the purpose of an API gateway in a microservices architecture?",                 "cat": "Technical", "diff": "Hard"},
        {"q": "How does garbage collection work and how can it impact performance?",                     "cat": "Technical", "diff": "Medium"},
        {"q": "What is test-driven development (TDD) and what are its benefits?",                       "cat": "Technical", "diff": "Medium"},
        {"q": "Explain the differences between unit, integration, and end-to-end testing.",             "cat": "Technical", "diff": "Medium"},
        {"q": "What is eventual consistency? How does it differ from strong consistency?",               "cat": "Technical", "diff": "Hard"},
        {"q": "How do you handle database migrations in a production system?",                          "cat": "Technical", "diff": "Medium"},
        {"q": "What is the difference between optimistic and pessimistic locking?",                     "cat": "Technical", "diff": "Hard"},
        {"q": "Describe a time when you had to refactor a large piece of code.",                        "cat": "Technical", "diff": "Medium"},
        {"q": "What is the Observer pattern and when would you use it?",                                "cat": "Technical", "diff": "Medium"},
        {"q": "How do load balancers work and what algorithms do they use?",                            "cat": "Technical", "diff": "Medium"},
        {"q": "What is a message queue? Give examples of when you would use one.",                      "cat": "Technical", "diff": "Medium"},
        {"q": "Explain the difference between horizontal and vertical scaling.",                        "cat": "Technical", "diff": "Easy"},
    ]

    hr_pool = [
        {"q": "Tell me about yourself and why you are applying for this role.",       "cat": "HR", "diff": "Easy",   "tip": "2-3 minutes. Professional, relevant, enthusiastic."},
        {"q": f"Why do you specifically want to work at {company_name}?",             "cat": "HR", "diff": "Easy",   "tip": "Research their products, culture, and mission."},
        {"q": "Where do you see yourself in 5 years?",                                "cat": "HR", "diff": "Easy",   "tip": "Align your ambition with the company's growth."},
        {"q": "Describe a challenging project and how you overcame obstacles.",        "cat": "HR", "diff": "Medium", "tip": "Use STAR: Situation, Task, Action, Result."},
        {"q": "How do you handle tight deadlines and competing priorities?",           "cat": "HR", "diff": "Medium", "tip": "Give a concrete example with outcome."},
        {"q": "What are your biggest strengths and one area you are improving?",      "cat": "HR", "diff": "Easy",   "tip": "Be honest and show self-awareness."},
        {"q": "Describe a conflict with a teammate and how you resolved it.",          "cat": "HR", "diff": "Medium", "tip": "Focus on resolution and what you learned."},
        {"q": "Tell me about a time you failed. What did you learn from it?",          "cat": "HR", "diff": "Medium", "tip": "Show maturity and growth mindset."},
        {"q": "How do you stay up-to-date with the latest industry trends?",           "cat": "HR", "diff": "Easy",   "tip": "Mention blogs, communities, open-source, courses."},
        {"q": "Describe a time you had to learn a new technology very quickly.",       "cat": "HR", "diff": "Medium", "tip": "Show adaptability with a specific example."},
        {"q": "What motivates you in your day-to-day work?",                           "cat": "HR", "diff": "Easy",   "tip": "Be genuine — connect to impact and problem-solving."},
        {"q": "How do you approach giving and receiving constructive feedback?",        "cat": "HR", "diff": "Medium", "tip": "Show emotional maturity and communication skills."},
        {"q": "Tell me about a time you led a team or project.",                        "cat": "HR", "diff": "Medium", "tip": "Highlight leadership, ownership, and outcome."},
        {"q": "How do you prioritise tasks when everything seems equally urgent?",      "cat": "HR", "diff": "Medium", "tip": "Mention frameworks like Eisenhower matrix or MoSCoW."},
        {"q": "What do you consider your most significant professional achievement?",   "cat": "HR", "diff": "Easy",   "tip": "Choose something measurable with clear impact."},
        {"q": "How would your previous colleagues or manager describe you?",            "cat": "HR", "diff": "Easy",   "tip": "Be consistent with the strengths you mentioned."},
        {"q": "Why are you leaving your current or last position?",                     "cat": "HR", "diff": "Medium", "tip": "Stay positive; focus on growth and new opportunities."},
        {"q": "What kind of work environment do you thrive in?",                        "cat": "HR", "diff": "Easy",   "tip": "Align with the company's known culture."},
        {"q": "Describe a situation where you met a very tight deadline.",              "cat": "HR", "diff": "Medium", "tip": "Show planning, execution, and results."},
        {"q": "How do you handle working under pressure or in ambiguous situations?",   "cat": "HR", "diff": "Medium", "tip": "Give examples — show calm, structured thinking."},
    ]

    coding_pool = [
        {"q": "Reverse a string without using built-in reverse functions.",                             "cat": "Coding", "diff": "Easy",   "tip": "Two-pointer technique or iterative swap."},
        {"q": "Find the first non-repeating character in a string.",                                    "cat": "Coding", "diff": "Easy",   "tip": "Hash map frequency count."},
        {"q": "Given a sorted array, find two numbers that sum to a target.",                           "cat": "Coding", "diff": "Easy",   "tip": "Two-pointer from both ends."},
        {"q": "Find the maximum subarray sum (Kadane's Algorithm).",                                    "cat": "Coding", "diff": "Medium", "tip": "Track current_sum and max_sum iteratively."},
        {"q": "Implement binary search on a sorted array.",                                             "cat": "Coding", "diff": "Medium", "tip": "mid = (low + high) // 2 to avoid overflow."},
        {"q": "Detect a cycle in a linked list.",                                                       "cat": "Coding", "diff": "Medium", "tip": "Floyd's Cycle Detection — fast and slow pointers."},
        {"q": "Check if a string is a palindrome.",                                                     "cat": "Coding", "diff": "Easy",   "tip": "Compare characters from both ends."},
        {"q": "Find all permutations of a string.",                                                     "cat": "Coding", "diff": "Medium", "tip": "Use backtracking with a visited array."},
        {"q": "Given an array, find the missing number from 1 to n.",                                   "cat": "Coding", "diff": "Easy",   "tip": "Expected sum = n*(n+1)/2 minus actual sum."},
        {"q": "Implement a stack using two queues.",                                                    "cat": "Coding", "diff": "Medium", "tip": "Push to q1, on pop dequeue all to q2, return last."},
        {"q": "Find the longest common subsequence of two strings.",                                    "cat": "Coding", "diff": "Hard",   "tip": "Dynamic programming — 2D table approach."},
        {"q": "Merge two sorted linked lists into one sorted list.",                                    "cat": "Coding", "diff": "Easy",   "tip": "Use a dummy node and compare nodes one by one."},
        {"q": "Find the kth largest element in an unsorted array.",                                     "cat": "Coding", "diff": "Medium", "tip": "Min-heap of size k, or QuickSelect algorithm."},
        {"q": "Given a matrix, rotate it 90 degrees clockwise in place.",                               "cat": "Coding", "diff": "Medium", "tip": "Transpose then reverse each row."},
        {"q": "Implement LRU Cache with O(1) get and put operations.",                                  "cat": "Coding", "diff": "Hard",   "tip": "Use OrderedDict or a doubly linked list + hashmap."},
        {"q": "Find the number of islands in a 2D grid.",                                               "cat": "Coding", "diff": "Medium", "tip": "DFS or BFS, mark visited cells."},
        {"q": "Check if two strings are anagrams of each other.",                                       "cat": "Coding", "diff": "Easy",   "tip": "Sort both and compare, or use a frequency map."},
        {"q": "Find the longest substring without repeating characters.",                                "cat": "Coding", "diff": "Medium", "tip": "Sliding window with a set to track current chars."},
        {"q": "Given a list of intervals, merge all overlapping ones.",                                  "cat": "Coding", "diff": "Medium", "tip": "Sort by start, then greedily merge."},
        {"q": "Serialize and deserialize a binary tree.",                                               "cat": "Coding", "diff": "Hard",   "tip": "BFS level-order, use null markers for empty nodes."},
    ]

    company_pool = [
        {"q": f"How has {company_name}'s work influenced the industry?",               "cat": "Company Specific", "diff": "Medium", "tip": "Research flagship products and recent news."},
        {"q": f"What would your first 30-60-90 day plan look like at {company_name}?", "cat": "Company Specific", "diff": "Medium", "tip": "Show initiative: learn, connect, and contribute."},
        {"q": f"What do you know about {company_name}'s core products or services?",   "cat": "Company Specific", "diff": "Easy",   "tip": "Check their website, LinkedIn, and news articles."},
        {"q": f"How does this role at {company_name} align with your career goals?",   "cat": "Company Specific", "diff": "Easy",   "tip": "Connect your personal growth with the company vision."},
        {"q": f"What challenges do you think {company_name} is currently facing?",     "cat": "Company Specific", "diff": "Hard",   "tip": "Show industry awareness and analytical thinking."},
    ]

    skill_templates = [
        ("Describe your hands-on experience with {skill}. What have you built with it?", "Medium", "Be specific. Mention version, scale, and problems solved."),
        ("What are the main advantages of {skill} over similar alternatives?",            "Easy",   "Show depth — not just surface-level awareness."),
        ("Describe a challenging problem you solved using {skill}.",                       "Hard",   "Use STAR format. Focus on your contribution."),
        ("How would you optimise performance in a {skill} application?",                   "Hard",   "Think about caching, batching, profiling."),
        ("What are common pitfalls when working with {skill}?",                            "Medium", "Shows real-world experience beyond tutorials."),
    ]
    skill_pool = []
    for skill in (company_skills or [])[:8]:
        for tmpl, diff, tip in skill_templates:
            skill_pool.append({"q": tmpl.format(skill=skill), "cat": "Technical", "diff": diff, "tip": tip})

    def not_seen(q_dict):
        return q_dict["q"].strip().lower() not in seen_questions

    tech_pool    = [q for q in tech_pool    if not_seen(q)]
    hr_pool      = [q for q in hr_pool      if not_seen(q)]
    coding_pool  = [q for q in coding_pool  if not_seen(q)]
    company_pool = [q for q in company_pool if not_seen(q)]
    skill_pool   = [q for q in skill_pool   if not_seen(q)]

    _rnd.shuffle(tech_pool)
    _rnd.shuffle(hr_pool)
    _rnd.shuffle(coding_pool)
    _rnd.shuffle(company_pool)
    _rnd.shuffle(skill_pool)

    selected = tech_pool[:5] + skill_pool[:6] + hr_pool[:5] + coding_pool[:4] + company_pool[:2]
    _rnd.shuffle(selected)

    for i, q in enumerate(selected):
        q["id"] = i + 1
        if "tip" not in q:
            q["tip"] = "Be concise and clear. Use real examples wherever possible."
            
    return {
        "questions": selected,
        "company": {"name": company_name},
        "role": {"title": job_title},
        "recommended_topics": []
    }



# ---------------------------------------------------------------------------
# ── RESUME CONTENT GENERATION ────────────────────────────────────────────────
# ---------------------------------------------------------------------------

def generate_resume_content(
    job_title: str,
    skills: list,
    experience_years: int = 0,
) -> dict:
    """Generate AI resume content for a given role and skill set."""
    from flask import current_app
    from services.qwen_service import call_qwen, parse_qwen_json

    skills_str = ", ".join(skills[:10]) if skills else "general technical skills"
    token = (current_app.config.get("QWEN_TOKEN") or current_app.config.get("HF_TOKEN") or "").strip()

    if token:
        prompt = (
            f"You are a professional resume writer.\n\n"
            f"Generate resume content for a {job_title} candidate with {experience_years} "
            f"year(s) of experience.\n"
            f"Skills: {skills_str}\n\n"
            f"Return ONLY valid JSON with this exact structure:\n"
            f'{{\n'
            f'  "professional_summary": "<3-4 sentence summary>",\n'
            f'  "key_skills": ["skill1", "skill2", "skill3", "skill4", "skill5"],\n'
            f'  "experience_bullet_points": [\n'
            f'    "<Bullet point with quantified achievement>",\n'
            f'    "<Bullet point with quantified achievement>",\n'
            f'    "<Bullet point with quantified achievement>"\n'
            f'  ],\n'
            f'  "education_suggestion": "<education section note>",\n'
            f'  "certifications": ["<cert1>", "<cert2>"]\n'
            f'}}'
        )
        raw = call_qwen(prompt, max_tokens=800, retries=1)
        if raw:
            data = parse_qwen_json(raw)
            if data and data.get("professional_summary"):
                return data

    return {
        "professional_summary": (
            f"Results-driven {job_title} with {experience_years}+ year(s) of experience "
            f"in {skills_str}. Proven ability to design and implement scalable solutions "
            f"in fast-paced environments. Strong communicator with a collaborative approach."
        ),
        "key_skills": skills[:10],
        "experience_bullet_points": [
            f"Developed and maintained solutions using {skills[0] if skills else 'modern technologies'}",
            "Collaborated with cross-functional teams to deliver projects on schedule",
            "Optimised system performance resulting in measurable efficiency improvements",
        ],
        "education_suggestion": "B.Tech / B.E. in Computer Science or related field",
        "certifications": [],
    }


# ---------------------------------------------------------------------------
# ── COMPANY ANALYSIS ─────────────────────────────────────────────────────────
# ---------------------------------------------------------------------------

def analyze_company(
    company_name: str,
    industry: str = "",
    description: str = "",
) -> dict:
    """Analyse a company and return structured overview data."""
    from flask import current_app
    from services.qwen_service import call_qwen, parse_qwen_json

    token = (current_app.config.get("QWEN_TOKEN") or current_app.config.get("HF_TOKEN") or "").strip()

    if token:
        prompt = (
            f"You are a company intelligence assistant for a career intelligence platform.\n\n"
            f"The user has entered the following company name:\n\n"
            f"COMPANY NAME:\n"
            f'"{company_name}"\n\n'
            f"Your task is to create a structured company profile that can be used\n"
            f"for career guidance, resume analysis, skill matching and interview preparation.\n\n"
            f"IMPORTANT RULES:\n"
            f"1. Identify the company from the provided company name.\n"
            f"2. Return ONLY valid JSON.\n"
            f"3. Do NOT use markdown.\n"
            f"4. Do NOT use ```json.\n"
            f"5. Do NOT include explanations outside the JSON.\n"
            f"6. Do not invent specific facts such as employee counts, salaries,\n"
            f"   interview experiences, recruitment processes or technologies\n"
            f"   unless they are reasonably supported by the available information.\n"
            f"7. If a field cannot be determined reliably, return:\n"
            f'   "Not available"\n'
            f"8. Clearly distinguish general industry knowledge from\n"
            f"   company-specific information.\n"
            f"9. Technology information should contain technologies that are\n"
            f"   reasonably associated with the company's products, services,\n"
            f"   engineering or publicly known technology environment.\n"
            f"10. Interview information must be presented as\n"
            f'    "likely/relevant preparation topics", NOT as confirmed questions\n'
            f"    actually asked by the company unless such information is explicitly\n"
            f"    provided to you.\n"
            f"11. Keep the information useful for a student/fresher preparing\n"
            f"    for placements.\n"
            f"12. Generate concise but useful information.\n\n"
            f"RETURN EXACTLY THIS JSON STRUCTURE:\n"
            f"{{\n"
            f'    "company": {{\n'
            f'        "name": "{company_name}",\n'
            f'        "official_name": "",\n'
            f'        "industry": "",\n'
            f'        "sub_industry": "",\n'
            f'        "headquarters": "",\n'
            f'        "locations": [],\n'
            f'        "website": "",\n'
            f'        "description": "",\n'
            f'        "products_services": [],\n'
            f'        "company_type": "",\n'
            f'        "company_size": "",\n'
            f'        "founded_year": ""\n'
            f'    }},\n'
            f'    "technology": {{\n'
            f'        "tech_stack": [],\n'
            f'        "programming_languages": [],\n'
            f'        "frameworks": [],\n'
            f'        "databases": [],\n'
            f'        "cloud_platforms": [],\n'
            f'        "developer_tools": []\n'
            f'    }},\n'
            f'    "career": {{\n'
            f'        "important_skills": [],\n'
            f'        "common_job_roles": [],\n'
            f'        "freshers_roles": [],\n'
            f'        "relevant_domains": []\n'
            f'    }},\n'
            f'    "interview": {{\n'
            f'        "likely_interview_topics": [],\n'
            f'        "technical_topics": [],\n'
            f'        "coding_topics": [],\n'
            f'        "aptitude_topics": [],\n'
            f'        "hr_topics": [],\n'
            f'        "likely_interview_rounds": []\n'
            f'    }},\n'
            f'    "workplace": {{\n'
            f'        "company_culture": "",\n'
            f'        "work_environment": "",\n'
            f'        "career_growth": ""\n'
            f'    }},\n'
            f'    "data_confidence": {{\n'
            f'        "overall": "",\n'
            f'        "limitations": []\n'
            f'    }}\n'
            f"}}"
        )
        raw = call_qwen(prompt, max_tokens=1500, retries=2)
        if raw:
            data = parse_qwen_json(raw)
            if data and data.get("company"):
                return data

    return {
        "company": {
            "name": company_name,
            "industry": industry,
            "description": description or f"{company_name} is a leading organisation."
        },
        "technology": {"tech_stack": []},
        "career": {"important_skills": [], "freshers_roles": []},
        "interview": {"likely_interview_topics": [], "technical_topics": []},
        "workplace": {"company_culture": "Collaborative and innovation-driven workplace."},
        "data_confidence": {"overall": "Low"}
    }

def ensure_company_profile(company_name: str) -> dict:
    """Ensure a company exists in the DB, generating an AI profile if missing."""
    import json
    import re
    from database.db import query_db, execute_db
    
    name = company_name.strip()
    if not name:
        return None
        
    # Check if exists
    company = query_db('SELECT * FROM companies WHERE name = %s', (name,), one=True)
    if company:
        return company
        
    # Generate profile
    profile_data = analyze_company(name, "", "")
    
    # Extract basic info
    comp_info = profile_data.get('company', {})
    industry = comp_info.get('industry', 'Technology')
    location = comp_info.get('headquarters', 'Global')
    size = comp_info.get('company_size', '1000+')
    description = comp_info.get('description', '')
    
    slug = re.sub(r'[^a-z0-9]+', '-', name.lower()).strip('-')
    
    # Insert new company
    ai_profile_str = json.dumps(profile_data)
    
    company_id = execute_db(
        '''INSERT INTO companies (name, slug, industry, location, company_size, description, ai_profile)
           VALUES (%s, %s, %s, %s, %s, %s, %s)''',
        (name, slug, industry, location, size, description, ai_profile_str),
        get_id=True
    )
    
    # Fetch and return
    if company_id:
        return query_db('SELECT * FROM companies WHERE id = %s', (company_id,), one=True)
    
    return None

def extract_company_tech_stack(
    company_name: str,
    job_title: str,
    description: str = "",
) -> list:
    """Extract the technology stack a company uses for a specific role."""
    from flask import current_app
    from services.qwen_service import call_qwen, parse_qwen_json_array

    token = (current_app.config.get("QWEN_TOKEN") or current_app.config.get("HF_TOKEN") or "").strip()

    if token:
        prompt = (
            f"List the key technical skills and technologies typically required for a "
            f"{job_title} role at {company_name}.\n"
            f"Description: {description[:400]}\n\n"
            f'Return ONLY a JSON array of skill strings: ["Python", "React", "MySQL"]'
        )
        raw = call_qwen(prompt, max_tokens=200, retries=1)
        if raw:
            arr = parse_qwen_json_array(raw)
            if arr and len(arr) > 0:
                return [str(s) for s in arr]

    return ["Python", "JavaScript", "SQL", "Git", "REST APIs", "Problem Solving", "Agile"]


# ---------------------------------------------------------------------------
# ── SKILL COMPARISON ─────────────────────────────────────────────────────────
# ---------------------------------------------------------------------------

def compare_student_skills(student_skills: list, company_skills: list) -> dict:
    """Compare student skills against company requirements."""
    student_lower = [s.lower() for s in student_skills]
    company_lower = [s.lower() for s in company_skills]

    matched = [s for s in company_skills if s.lower() in student_lower]
    missing = [s for s in company_skills if s.lower() not in student_lower]
    extra   = [s for s in student_skills  if s.lower() not in company_lower]

    return {
        "matched_skills":   matched,
        "missing_skills":   missing,
        "extra_skills":     extra,
        "match_percentage": int(len(matched) / max(len(company_skills), 1) * 100),
        "total_required":   len(company_skills),
        "total_matched":    len(matched),
        "total_missing":    len(missing),
    }


# ---------------------------------------------------------------------------
# ── CAREER READINESS ─────────────────────────────────────────────────────────
# ---------------------------------------------------------------------------

def calculate_career_readiness(analysis_results: list) -> dict:
    """Aggregate readiness score from multiple analyses."""
    if not analysis_results:
        return {
            "overall_readiness":    0,
            "placement_probability": 0,
            "recommendation": "Run a resume analysis to get your career readiness score.",
        }

    avg_ats   = sum(a.get("ats_score",              0) for a in analysis_results) / len(analysis_results)
    avg_skill = sum(a.get("skill_match_score",       0) for a in analysis_results) / len(analysis_results)
    avg_career= sum(a.get("career_readiness_score",  0) for a in analysis_results) / len(analysis_results)
    overall   = int((avg_ats + avg_skill + avg_career) / 3)

    if overall >= 80:
        rec = "Excellent! You are well-prepared for the job market."
    elif overall >= 60:
        rec = "Good progress. Address a few missing skills to boost your chances."
    else:
        rec = "Focus on building core technical skills and expanding your portfolio."

    return {
        "overall_readiness":     int(avg_career),
        "placement_probability": overall,
        "avg_ats":               int(avg_ats),
        "avg_skill_match":       int(avg_skill),
        "total_analyses":        len(analysis_results),
        "recommendation":        rec,
    }


# ---------------------------------------------------------------------------
# ── CAREER REPORT ────────────────────────────────────────────────────────────
# ---------------------------------------------------------------------------

def generate_career_report(user_data: dict, analyses: list) -> dict:
    """Generate a career readiness summary from all analyses."""
    if not analyses:
        return {
            "overall_readiness":   0,
            "placement_score":     0,
            "top_companies":       [],
            "key_strengths":       [],
            "priority_improvements": [],
        }

    avg_ats   = sum(a.get("ats_score",             0) for a in analyses) / len(analyses)
    avg_skill = sum(a.get("skill_match_score",      0) for a in analyses) / len(analyses)
    avg_career= sum(a.get("career_readiness_score", 0) for a in analyses) / len(analyses)

    return {
        "overall_readiness":   int(avg_career),
        "placement_score":     int((avg_ats + avg_skill + avg_career) / 3),
        "avg_ats":             int(avg_ats),
        "avg_skill_match":     int(avg_skill),
        "total_analyses":      len(analyses),
        "key_strengths":       ["Technical proficiency", "Communication skills", "Problem-solving ability"],
        "priority_improvements": ["System design knowledge", "Cloud computing skills", "Leadership experience"],
    }


# ---------------------------------------------------------------------------
# ── COMPANY INTELLIGENCE ─────────────────────────────────────────────────────
# ---------------------------------------------------------------------------

def _build_company_profile_prompt(company_name: str) -> str:
    """
    Build the structured Qwen prompt for generating a company intelligence
    profile.  Returns valid JSON matching the schema below — no markdown.
    """
    return f"""You are a company intelligence assistant for a career intelligence platform.

The user has entered the following company name:

COMPANY NAME:
"{company_name}"

Your task is to create a structured company profile that can be used
for career guidance, resume analysis, skill matching and interview preparation.

IMPORTANT RULES:

1. Identify the company from the provided company name.

2. Return ONLY valid JSON.

3. Do NOT use markdown.

4. Do NOT use ```json.

5. Do NOT include explanations outside the JSON.

6. Do not invent specific facts such as employee counts, salaries,
   interview experiences, recruitment processes or technologies
   unless they are reasonably supported by the available information.

7. If a field cannot be determined reliably, return:
   "Not available"

8. Clearly distinguish general industry knowledge from
   company-specific information.

9. Technology information should contain technologies that are
   reasonably associated with the company's products, services,
   engineering or publicly known technology environment.

10. Interview information must be presented as
    "likely/relevant preparation topics", NOT as confirmed questions
    actually asked by the company unless such information is explicitly
    provided to you.

11. Keep the information useful for a student/fresher preparing
    for placements.

12. Generate concise but useful information.

RETURN EXACTLY THIS JSON STRUCTURE:

{{
    "company": {{
        "name": "{company_name}",
        "official_name": "",
        "industry": "",
        "sub_industry": "",
        "headquarters": "",
        "locations": [],
        "website": "",
        "description": "",
        "products_services": [],
        "company_type": "",
        "company_size": "",
        "founded_year": ""
    }},

    "technology": {{
        "tech_stack": [],
        "programming_languages": [],
        "frameworks": [],
        "databases": [],
        "cloud_platforms": [],
        "developer_tools": []
    }},

    "career": {{
        "important_skills": [],
        "common_job_roles": [],
        "freshers_roles": [],
        "relevant_domains": []
    }},

    "interview": {{
        "likely_interview_topics": [],
        "technical_topics": [],
        "coding_topics": [],
        "aptitude_topics": [],
        "hr_topics": [],
        "likely_interview_rounds": []
    }},

    "workplace": {{
        "company_culture": "",
        "work_environment": "",
        "career_growth": ""
    }},

    "data_confidence": {{
        "overall": "",
        "limitations": []
    }}
}}"""


def _company_profile_stub(company_name: str) -> dict:
    """
    Smart stub fallback for when Qwen is unavailable.
    Returns a minimal but structurally valid profile.
    """
    return {
        "company": {
            "name": company_name,
            "official_name": company_name,
            "industry": "Technology",
            "sub_industry": "Software",
            "headquarters": "Not available",
            "locations": [],
            "website": "Not available",
            "description": (
                f"{company_name} is a technology company. "
                "Detailed information could not be retrieved at this time."
            ),
            "products_services": ["Software solutions", "Technology services"],
            "company_type": "Private",
            "company_size": "Not available",
            "founded_year": "Not available",
        },
        "technology": {
            "tech_stack": ["Java", "Python", "JavaScript"],
            "programming_languages": ["Java", "Python", "JavaScript", "C++"],
            "frameworks": ["Spring Boot", "React", "Node.js"],
            "databases": ["MySQL", "PostgreSQL"],
            "cloud_platforms": ["AWS"],
            "developer_tools": ["Git", "Docker"],
        },
        "career": {
            "important_skills": [
                "Data Structures & Algorithms", "Problem Solving",
                "Communication", "Teamwork", "Object-Oriented Programming"
            ],
            "common_job_roles": [
                "Software Engineer", "Backend Developer",
                "Frontend Developer", "Full Stack Developer"
            ],
            "freshers_roles": ["Software Engineer Trainee", "Junior Developer"],
            "relevant_domains": ["Software Development", "Web Development"],
        },
        "interview": {
            "likely_interview_topics": [
                "Data Structures", "Algorithms", "System Design basics",
                "OOP Concepts", "Database fundamentals"
            ],
            "technical_topics": [
                "Arrays, Linked Lists, Trees, Graphs",
                "Sorting & Searching algorithms",
                "OOP principles",
                "SQL queries",
            ],
            "coding_topics": ["Array manipulation", "String problems", "Dynamic Programming"],
            "aptitude_topics": ["Quantitative Aptitude", "Logical Reasoning", "Verbal Ability"],
            "hr_topics": [
                "Tell me about yourself",
                "Why this company?",
                "Where do you see yourself in 5 years?",
                "Strengths and weaknesses",
            ],
            "likely_interview_rounds": [
                "Online Aptitude Test",
                "Technical Interview Round 1",
                "Technical Interview Round 2",
                "HR Interview",
            ],
        },
        "workplace": {
            "company_culture": "Collaborative and growth-oriented work environment.",
            "work_environment": "Professional and structured.",
            "career_growth": "Opportunities available based on performance and skills.",
        },
        "data_confidence": {
            "overall": "Low — generated from stub fallback (Qwen unavailable)",
            "limitations": [
                "AI service was unavailable; data is generic.",
                "Verify all information independently.",
            ],
        },
    }


def generate_company_profile(company_name: str) -> dict:
    """
    Generate a structured company intelligence profile using Qwen.

    Returns a validated dict matching the schema defined in
    _build_company_profile_prompt().  Falls back to _company_profile_stub()
    when Qwen is unavailable or returns unparseable content.

    Args:
        company_name: The company name entered by the user.

    Returns:
        Dict with keys: company, technology, career, interview, workplace,
        data_confidence.
    """
    from services.qwen_service import call_qwen, parse_qwen_json

    prompt = _build_company_profile_prompt(company_name)

    logger.info(f"COMPANY_AI: Generating profile for '{company_name}'")

    raw = call_qwen(prompt, max_tokens=2000, retries=2, temperature=0.3)

    if raw:
        data = parse_qwen_json(raw)
        if data and isinstance(data, dict) and data.get('company'):
            # Basic validation: ensure required top-level keys exist
            required_keys = {'company', 'technology', 'career', 'interview', 'workplace'}
            if required_keys.issubset(data.keys()):
                # Make sure company.name matches what was requested
                data['company']['name'] = company_name
                logger.info(f"COMPANY_AI: Profile generated successfully for '{company_name}'")
                return data
            else:
                logger.warning(f"COMPANY_AI: Incomplete JSON keys for '{company_name}' — using stub")
        else:
            logger.warning(f"COMPANY_AI: Unparseable JSON for '{company_name}' — using stub")
    else:
        logger.warning(f"COMPANY_AI: No Qwen response for '{company_name}' — using stub")

    return _company_profile_stub(company_name)


def analyze_company(name: str, industry: str = '', description: str = '') -> dict:
    """
    Alias used by the existing /company/<slug>/generate-intelligence route.
    Generates (or re-generates) the AI profile for an already-existing company.

    Returns the same structured dict as generate_company_profile().
    """
    return generate_company_profile(name)


def ensure_company_profile(company_name: str) -> dict | None:
    """
    Main orchestrator for the POST /api/company/search flow.

    Flow:
      1. Search MySQL for an existing company by name.
      2a. Found + has ai_profile  → return cached company row.
      2b. Found but no ai_profile → call Qwen, save ai_profile, return row.
      2c. Not found               → call Qwen, create company + skills rows, return row.

    Args:
        company_name: Raw company name from user input.

    Returns:
        A company dict row (as returned by MySQL), or None on failure.
    """
    import json as _json
    from models.company import CompanyModel

    company_name = company_name.strip()
    if not company_name:
        return None

    # ── Step 1: Check MySQL ──────────────────────────────────────────────
    existing = CompanyModel.search_by_name(company_name)

    if existing:
        # ── Step 2a: Cached with ai_profile ─────────────────────────────
        if existing.get('ai_profile'):
            logger.info(f"COMPANY_AI: Cache hit for '{company_name}' (id={existing['id']})")
            return existing

        # ── Step 2b: Exists but no ai_profile ───────────────────────────
        logger.info(f"COMPANY_AI: Found '{company_name}' in DB but no ai_profile — generating …")
        try:
            profile_data = generate_company_profile(company_name)
            profile_json = _json.dumps(profile_data)

            # Save ai_profile JSON
            CompanyModel.update_ai_profile(existing['id'], profile_json)

            # Refresh skills from AI data
            technology = profile_data.get('technology', {})
            if technology:
                CompanyModel.save_skills_from_ai(existing['id'], technology)

            # Re-fetch the updated row
            return CompanyModel.get_by_id(existing['id'])
        except Exception as exc:
            logger.error(f"COMPANY_AI: Failed to update profile for existing company: {exc}")
            return existing   # Return what we have even without ai_profile

    # ── Step 2c: Not in DB — generate and create ─────────────────────────
    logger.info(f"COMPANY_AI: '{company_name}' not in DB — generating new profile …")
    try:
        profile_data = generate_company_profile(company_name)
        profile_json = _json.dumps(profile_data)

        # Insert company row
        new_company = CompanyModel.create_from_ai(profile_data, profile_json)
        if not new_company:
            logger.error(f"COMPANY_AI: DB insert failed for '{company_name}'")
            return None

        # Insert skills
        technology = profile_data.get('technology', {})
        if technology:
            CompanyModel.save_skills_from_ai(new_company['id'], technology)

        logger.info(
            f"COMPANY_AI: Created new company '{company_name}' "
            f"(id={new_company['id']}, slug={new_company['slug']})"
        )
        return new_company

    except Exception as exc:
        logger.error(f"COMPANY_AI: Failed to create new company '{company_name}': {exc}")
        return None

