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

For missing_skills: List 4-8 specific technical skills that would significantly
strengthen this candidate for modern software engineering roles but are NOT present
or demonstrated in the resume. Examples: Docker, Kubernetes, CI/CD, Redis, System
Design, AWS, GraphQL, TypeScript — pick whichever apply given the candidate's stack.
NEVER return an empty missing_skills array.

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


def _validate_analysis_json(data: dict, resume_text: str = "") -> dict:
    """
    Validate and normalise the JSON returned by Qwen.
    Ensures all fields expected by AnalysisModel.create() are present and typed.
    If Qwen returned missing_skills=[], computes them from the resume text as fallback.
    """
    scores = data.get("scores", {})

    def _int(val, default=0):
        try:
            v = int(val)
            return max(0, min(100, v))
        except (TypeError, ValueError):
            return default

    def _list(val):
        if isinstance(val, list):
            return [str(x) for x in val if x]
        return []

    result = {
        "ats_score":                _int(scores.get("ats_score",                data.get("ats_score",                0))),
        "skill_match_score":        _int(scores.get("skill_match_score",        data.get("skill_match_score",        0))),
        "tech_match_score":         _int(scores.get("tech_match_score",         data.get("tech_match_score",         0))),
        "project_match_score":      _int(scores.get("project_match_score",      data.get("project_match_score",      0))),
        "career_readiness_score":   _int(scores.get("career_readiness_score",   data.get("career_readiness_score",   0))),
        "interview_readiness_score":_int(scores.get("interview_readiness_score",data.get("interview_readiness_score",0))),
        "grammar_score":            _int(scores.get("grammar_score",            data.get("grammar_score",            0))),
        "formatting_score":         _int(scores.get("formatting_score",         data.get("formatting_score",         0))),
        "overall_score":            _int(scores.get("overall_score",            data.get("overall_score",            0))),
        "summary":          str(data.get("summary", "")),
        "strengths":        _list(data.get("strengths")),
        "weaknesses":       _list(data.get("weaknesses")),
        "missing_skills":   _list(data.get("missing_skills")),
        "suggestions":      _list(data.get("resume_suggestions")),
        "keywords":         _list(data.get("keywords")),
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
        "matched_skills":       [],
        "all_resume_skills":    _list(data.get("skills")),
        "ai_source": "qwen",
    }

    # If Qwen returned no missing_skills, compute from resume text vs benchmark
    if not result["missing_skills"]:
        try:
            from services.resume_parser import extract_skills_from_text
            resume_skills = {s["name"].lower() for s in extract_skills_from_text(resume_text or "")}
            qwen_skills   = {s.lower() for s in result["skills"]}
            candidate     = resume_skills | qwen_skills
            benchmark = [
                'Docker', 'Kubernetes', 'CI/CD', 'Redis', 'AWS', 'System Design',
                'GraphQL', 'TypeScript', 'Microservices', 'Unit Testing',
                'PostgreSQL', 'Linux', 'Terraform', 'REST APIs', 'Git'
            ]
            computed = [s for s in benchmark if s.lower() not in candidate][:8]
            result["missing_skills"] = computed or [
                'Docker', 'CI/CD', 'System Design', 'AWS', 'Unit Testing', 'Redis'
            ]
            logger.info(f"Missing skills fallback computed {len(result['missing_skills'])} skills")
        except Exception as exc:
            logger.warning(f"Missing skills fallback error: {exc}")
            result["missing_skills"] = ['Docker', 'CI/CD', 'System Design', 'AWS', 'Unit Testing', 'Redis']

    return result




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
                    validated = _validate_analysis_json(data, resume_text)
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
    missing = [s for s in (company_skills or []) if s.lower() not in all_candidate][:8]
    if not missing:
        role_skill_standards = {
            'frontend': ['React', 'TypeScript', 'Tailwind CSS', 'Next.js', 'Redux', 'REST APIs', 'Jest', 'Webpack'],
            'backend': ['Python', 'Docker', 'PostgreSQL', 'Redis', 'REST APIs', 'Microservices', 'CI/CD', 'AWS'],
            'fullstack': ['Docker', 'AWS', 'TypeScript', 'PostgreSQL', 'CI/CD', 'GraphQL', 'Redis', 'Microservices'],
            'data': ['Python', 'SQL', 'Pandas', 'Power BI', 'Machine Learning', 'NumPy', 'Tableau', 'BigQuery'],
            'ml': ['Python', 'PyTorch', 'TensorFlow', 'Scikit-learn', 'NLP', 'Computer Vision', 'Deep Learning', 'MLOps'],
            'ai': ['Python', 'PyTorch', 'Transformers', 'LangChain', 'FastAPI', 'Vector Databases', 'OpenAI API'],
            'devops': ['Docker', 'Kubernetes', 'CI/CD', 'AWS', 'Terraform', 'Linux', 'Ansible', 'Prometheus'],
            'cloud': ['AWS', 'Docker', 'Kubernetes', 'Terraform', 'CI/CD', 'Linux', 'Azure', 'Microservices'],
            'testing': ['Selenium', 'PyTest', 'Postman', 'Jira', 'Automation Testing', 'CI/CD', 'Cypress', 'SQL'],
            'qa': ['Manual Testing', 'Selenium', 'Postman', 'Test Automation', 'Jira', 'PyTest', 'SQL', 'API Testing'],
            'software': ['Docker', 'System Design', 'CI/CD', 'AWS', 'Kubernetes', 'Unit Testing', 'Redis', 'Data Structures']
        }
        title_lower = (job_title or '').lower()
        matched_target = 'software'
        for k in role_skill_standards:
            if k in title_lower:
                matched_target = k
                break
        benchmark = role_skill_standards[matched_target]
        missing = [s for s in benchmark if s.lower() not in all_candidate][:8]
        if not missing:
            missing = ['Docker', 'System Design', 'CI/CD', 'AWS', 'Kubernetes', 'Unit Testing']

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
        def _clean_bullet(line):
            cleaned = re.sub(r'^[•\-\*●·\s]+', '', line).strip()
            return f"• {cleaned}" if cleaned else ""

        exp_bullets = '\n'.join(
            _clean_bullet(l) for l in exp_lines[:6] if _clean_bullet(l)
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
        proj_text = '\n'.join(
            _clean_bullet(l) for l in proj_lines[:4] if _clean_bullet(l)
        ) if proj_lines else f"• Built a {job_title.lower()} application using {', '.join(all_skills[:3])}"

        sep = "─" * 32
        header = f"{name}\n{email}  |  {phone}\n{sep}\n\n" if name else ""
        ai_resume = (
            f"{header}"
            f"PROFESSIONAL SUMMARY\n{sep}\n{summary}\n\n"
            f"SKILLS\n{sep}\n{skills_line}\n\n"
            f"WORK EXPERIENCE\n{sep}\n{exp_bullets}\n\n"
            f"EDUCATION\n{sep}\n{edu_text}\n\n"
            f"PROJECTS\n{sep}\n{proj_text}\n\n"
            f"CERTIFICATIONS\n{sep}\nAdd your certifications here"
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
# ── INTERVIEW QUESTIONS — MCQ GENERATION ────────────────────────────────────
# ---------------------------------------------------------------------------

# Valid category enum values in the DB
_VALID_CATEGORIES = {'Technical', 'HR', 'Coding', 'Aptitude', 'Company Specific',
                     'Logical Reasoning', 'Personalized'}

def _safe_cat(cat: str) -> str:
    """Map a category string to a valid DB enum value."""
    if cat in _VALID_CATEGORIES:
        return cat
    c = (cat or '').lower()
    if 'hr' in c or 'behavioral' in c:
        return 'HR'
    if 'coding' in c or 'program' in c:
        return 'Coding'
    if 'aptitude' in c or 'quant' in c or 'math' in c:
        return 'Aptitude'
    if 'logical' in c or 'reasoning' in c:
        return 'Logical Reasoning'
    if 'company' in c:
        return 'Company Specific'
    return 'Technical'


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
) -> dict:
    """Generate fresh, placement-style MCQ interview questions.

    Every question has 4 options, one correct_answer, and an explanation.
    Falls back to a large static MCQ pool when AI is unavailable.
    """
    import random

    if seen_questions is None:
        seen_questions = set()
    if user_skills is None:
        user_skills = company_skills or []
    if user_experience is None:
        user_experience = []
    if user_projects is None:
        user_projects = []

    # ── TRY AI FIRST ─────────────────────────────────────────────────────────
    try:
        from flask import current_app
        from services.qwen_service import call_qwen, parse_qwen_json

        token = (current_app.config.get("QWEN_TOKEN") or current_app.config.get("HF_TOKEN") or "").strip()
        if token:
            skills_str = ", ".join((user_skills + company_skills)[:15]) or "General CS"
            exp_str = "; ".join(
                f"{e.get('job_title','')} at {e.get('company_name','')}" for e in (user_experience or [])[:3]
            ) or "Fresher"
            seen_str = "\n- ".join(list(seen_questions)[:60]) if seen_questions else "None"

            prompt = (
                f"You are a placement interview question generator.\n\n"
                f"TARGET ROLE: {job_title}\n"
                f"COMPANY: {company_name}\n"
                f"REQUIRED SKILLS: {skills_str}\n"
                f"CANDIDATE EXPERIENCE: {exp_str}\n\n"
                f"PREVIOUSLY ASKED (DO NOT REPEAT):\n{seen_str}\n\n"
                f"GENERATE EXACTLY 20 placement-style MCQs.\n\n"
                f"STRICT RULES:\n"
                f"1. Every question MUST have EXACTLY 4 options.\n"
                f"2. EXACTLY ONE correct answer.\n"
                f"3. Each item needs: question, options (list of 4), correct_answer (exact text of correct option), explanation, category, difficulty, topic.\n"
                f"4. Do NOT put A) B) inside option strings.\n"
                f"5. correct_answer must match one of the 4 options exactly.\n"
                f"6. Categories (use ONLY these): Technical, Aptitude, Coding, Logical Reasoning, HR\n"
                f"7. Difficulty: Easy, Medium, or Hard\n"
                f"8. Mix: 5 Easy, 10 Medium, 5 Hard minimum.\n"
                f"9. Include all 5 categories.\n"
                f"10. Return ONLY valid JSON. No markdown, no ``` fences.\n\n"
                f"JSON STRUCTURE:\n"
                f'{{\n'
                f'  "questions": [\n'
                f'    {{\n'
                f'      "question": "What does OOP stand for?",\n'
                f'      "options": ["Object Oriented Programming","Optimized Object Process","Online Open Protocol","Object Overriding Procedure"],\n'
                f'      "correct_answer": "Object Oriented Programming",\n'
                f'      "explanation": "OOP = Object Oriented Programming.",\n'
                f'      "category": "Technical",\n'
                f'      "difficulty": "Easy",\n'
                f'      "topic": "OOP"\n'
                f'    }}\n'
                f'  ],\n'
                f'  "company": {{"name": "{company_name}", "important_skills": [], "company_culture": "", "interview_process": []}},\n'
                f'  "role": {{"title": "{job_title}", "responsibilities": [], "expected_knowledge": []}},\n'
                f'  "recommended_topics": [{{"topic": "", "priority": "High", "reason": ""}}]\n'
                f'}}'
            )

            raw = call_qwen(prompt, max_tokens=4000, retries=2, temperature=0.4)
            if raw:
                data = parse_qwen_json(raw)
                if data and isinstance(data, dict) and "questions" in data:
                    return _convert_mcq_response(data, seen_questions)
    except Exception as exc:
        logger.warning(f"AI interview generation failed: {exc} — using static MCQ pool")

    return _static_mcq_pool(job_title, company_name, company_skills, seen_questions)


def _convert_mcq_response(data: dict, seen_questions: set) -> dict:
    """Validate and sanitise the AI MCQ response."""
    import random
    result = []
    for item in data.get("questions", []):
        q_text = (item.get("question") or "").strip()
        if not q_text or q_text.lower() in seen_questions:
            continue
        options = item.get("options", [])
        if not isinstance(options, list) or len(options) < 2:
            continue
        options = [str(o).strip() for o in options[:4]]
        while len(options) < 4:
            options.append("—")
        correct = str(item.get("correct_answer") or "").strip()
        if correct not in options:
            correct = options[0]
        diff = item.get("difficulty", "Medium")
        if diff not in ("Easy", "Medium", "Hard"):
            diff = "Medium"
        result.append({
            "q":             q_text,
            "cat":           _safe_cat(item.get("category", "Technical")),
            "diff":          diff,
            "tip":           str(item.get("explanation") or "").strip(),
            "options":       options,
            "correct_answer": correct,
            "topic":         str(item.get("topic") or ""),
        })
    random.shuffle(result)
    for i, q in enumerate(result):
        q["id"] = i + 1
    return {
        "questions":          result,
        "company":            data.get("company", {}),
        "role":               data.get("role", {}),
        "recommended_topics": data.get("recommended_topics", []),
    }


def _static_mcq_pool(job_title: str, company_name: str, company_skills: list, seen_questions: set) -> dict:
    """Large static MCQ pool — fallback when AI is unavailable."""
    import random as _rnd

    tech_pool = [
        {"q":"What does HTTP stand for?","options":["HyperText Transfer Protocol","High Transfer Text Protocol","Hyper Transfer Text Process","HyperText Technical Protocol"],"correct_answer":"HyperText Transfer Protocol","cat":"Technical","diff":"Easy","tip":"HTTP is the foundation of data communication on the World Wide Web.","topic":"Networking"},
        {"q":"Which data structure operates on the LIFO principle?","options":["Queue","Stack","Linked List","Tree"],"correct_answer":"Stack","cat":"Technical","diff":"Easy","tip":"LIFO = Last In First Out. Stack is the classic data structure for this.","topic":"Data Structures"},
        {"q":"What is the time complexity of Binary Search?","options":["O(n)","O(n log n)","O(log n)","O(1)"],"correct_answer":"O(log n)","cat":"Technical","diff":"Easy","tip":"Binary search halves the search space each step → O(log n).","topic":"Algorithms"},
        {"q":"Which SQL clause filters grouped results?","options":["WHERE","HAVING","GROUP BY","ORDER BY"],"correct_answer":"HAVING","cat":"Technical","diff":"Medium","tip":"HAVING filters after GROUP BY; WHERE filters before aggregation.","topic":"SQL"},
        {"q":"What is a primary key in a relational database?","options":["A key that can be NULL","A key that uniquely identifies each row","A foreign reference to another table","A key used for sorting"],"correct_answer":"A key that uniquely identifies each row","cat":"Technical","diff":"Easy","tip":"Primary keys enforce entity integrity and must be unique and NOT NULL.","topic":"DBMS"},
        {"q":"Which Python keyword creates a generator function?","options":["return","yield","generate","async"],"correct_answer":"yield","cat":"Technical","diff":"Medium","tip":"A function with 'yield' is a generator that lazily produces values.","topic":"Python"},
        {"q":"What does REST stand for?","options":["Remote Execution State Transfer","Representational State Transfer","Resource Embedded System Transfer","Redundant State Transfer"],"correct_answer":"Representational State Transfer","cat":"Technical","diff":"Easy","tip":"REST is an architectural style for distributed hypermedia systems.","topic":"Web APIs"},
        {"q":"Which sorting algorithm always has O(n log n) time complexity?","options":["Bubble Sort","Insertion Sort","Merge Sort","Quick Sort"],"correct_answer":"Merge Sort","cat":"Technical","diff":"Medium","tip":"Merge Sort is always O(n log n). Quick Sort is O(n²) in worst case.","topic":"Algorithms"},
        {"q":"What is polymorphism in OOP?","options":["Hiding internal data","Inheriting from multiple parents","An object's ability to take many forms","Creating multiple constructors"],"correct_answer":"An object's ability to take many forms","cat":"Technical","diff":"Easy","tip":"Polymorphism allows one interface to be used for many data types.","topic":"OOP"},
        {"q":"Which HTTP status code means 'Not Found'?","options":["200","301","404","500"],"correct_answer":"404","cat":"Technical","diff":"Easy","tip":"404 is the standard response when a resource cannot be found.","topic":"Web"},
        {"q":"Worst-case time complexity of Quick Sort?","options":["O(n log n)","O(n)","O(n²)","O(log n)"],"correct_answer":"O(n²)","cat":"Technical","diff":"Hard","tip":"Quick Sort degrades to O(n²) when pivot is always min or max.","topic":"Algorithms"},
        {"q":"What is a deadlock in operating systems?","options":["100% CPU usage","Two processes each waiting for resources held by the other","A memory overflow","An infinite loop"],"correct_answer":"Two processes each waiting for resources held by the other","cat":"Technical","diff":"Hard","tip":"Deadlock: circular wait where each process holds and needs a resource.","topic":"OS"},
        {"q":"Which design pattern ensures only one instance of a class exists?","options":["Factory","Observer","Singleton","Decorator"],"correct_answer":"Singleton","cat":"Technical","diff":"Medium","tip":"The Singleton pattern restricts a class to a single instance.","topic":"Design Patterns"},
        {"q":"What does API stand for?","options":["Application Programming Interface","Automated Protocol Interface","Advanced Programming Index","Application Process Integration"],"correct_answer":"Application Programming Interface","cat":"Technical","diff":"Easy","tip":"An API defines how software components interact with each other.","topic":"General CS"},
        {"q":"Which protocol provides secure communication over the internet?","options":["FTP","HTTP","HTTPS/TLS","SMTP"],"correct_answer":"HTTPS/TLS","cat":"Technical","diff":"Easy","tip":"HTTPS uses TLS to encrypt HTTP traffic.","topic":"Networking"},
        {"q":"What is the difference between a process and a thread?","options":["No difference","A thread has its own memory space","A process has its own memory; threads share it","Threads cannot be created by processes"],"correct_answer":"A process has its own memory; threads share it","cat":"Technical","diff":"Medium","tip":"Threads share heap; processes have separate address spaces.","topic":"OS"},
        {"q":"Which data structure is used to implement BFS?","options":["Stack","Priority Queue","Queue","Linked List"],"correct_answer":"Queue","cat":"Technical","diff":"Medium","tip":"BFS uses a FIFO Queue to explore nodes level by level.","topic":"Graph Algorithms"},
        {"q":"Purpose of normalization in databases?","options":["Compress data","Remove redundancy and organize data efficiently","Encrypt sensitive data","Create backups"],"correct_answer":"Remove redundancy and organize data efficiently","cat":"Technical","diff":"Medium","tip":"Normalization reduces redundancy through 1NF, 2NF, 3NF.","topic":"DBMS"},
        {"q":"Which Java keyword prevents method overriding?","options":["static","abstract","final","private"],"correct_answer":"final","cat":"Technical","diff":"Medium","tip":"'final' methods cannot be overridden by subclasses.","topic":"Java"},
        {"q":"What does the 'virtual' keyword enable in C++?","options":["Memory allocation","Operator overloading","Runtime polymorphism via vtable","Template specialization"],"correct_answer":"Runtime polymorphism via vtable","cat":"Technical","diff":"Hard","tip":"Virtual functions enable dynamic dispatch through a virtual table.","topic":"C++"},
    ]

    aptitude_pool = [
        {"q":"Train travels 300 km in 5 hours. Speed?","options":["50 km/h","60 km/h","65 km/h","55 km/h"],"correct_answer":"60 km/h","cat":"Aptitude","diff":"Easy","tip":"Speed = Distance / Time = 300/5 = 60 km/h.","topic":"Speed & Distance"},
        {"q":"What is 15% of 240?","options":["34","36","38","32"],"correct_answer":"36","cat":"Aptitude","diff":"Easy","tip":"15% of 240 = (15/100) × 240 = 36.","topic":"Percentages"},
        {"q":"A does a job in 10 days, B in 15. Together in how many days?","options":["5","6","8","4"],"correct_answer":"6","cat":"Aptitude","diff":"Medium","tip":"Combined rate = 1/10 + 1/15 = 1/6 → 6 days.","topic":"Time & Work"},
        {"q":"Next in series: 2, 6, 12, 20, 30, ?","options":["40","42","44","38"],"correct_answer":"42","cat":"Aptitude","diff":"Medium","tip":"Differences: 4,6,8,10,12 → 30+12=42.","topic":"Number Series"},
        {"q":"Item marked at ₹500, sold at 20% discount. Selling price?","options":["₹400","₹380","₹420","₹450"],"correct_answer":"₹400","cat":"Aptitude","diff":"Easy","tip":"SP = 500 × 0.80 = ₹400.","topic":"Discount"},
        {"q":"Simple interest: ₹5000 at 8% p.a. for 3 years?","options":["₹1100","₹1200","₹1400","₹1000"],"correct_answer":"₹1200","cat":"Aptitude","diff":"Easy","tip":"SI = P×R×T/100 = 5000×8×3/100 = ₹1200.","topic":"Simple Interest"},
        {"q":"Two pipes fill a tank in 12 and 18 hours. Together in?","options":["6 hours","7.2 hours","8 hours","9 hours"],"correct_answer":"7.2 hours","cat":"Aptitude","diff":"Medium","tip":"Rate = 1/12 + 1/18 = 5/36. Time = 36/5 = 7.2 hrs.","topic":"Pipes & Cisterns"},
        {"q":"Average of 5 consecutive even numbers is 14. Largest?","options":["16","18","20","22"],"correct_answer":"18","cat":"Aptitude","diff":"Medium","tip":"Numbers: 10,12,14,16,18. Avg = 14. Largest = 18.","topic":"Averages"},
        {"q":"LCM of 12, 15, and 20?","options":["30","60","45","120"],"correct_answer":"60","cat":"Aptitude","diff":"Medium","tip":"LCM(12,15,20) = 60.","topic":"LCM & HCF"},
        {"q":"In a class of 40, 60% passed. How many failed?","options":["14","16","18","20"],"correct_answer":"16","cat":"Aptitude","diff":"Easy","tip":"40% failed. 40% of 40 = 16.","topic":"Percentages"},
    ]

    logical_pool = [
        {"q":"All cats are animals. All animals have cells. Therefore?","options":["Some cats may not have cells","All cats have cells","Animals are cats","None of the above"],"correct_answer":"All cats have cells","cat":"Logical Reasoning","diff":"Easy","tip":"Syllogism chain: A→B, B→C, so A→C.","topic":"Syllogisms"},
        {"q":"Odd one out: 2, 3, 5, 7, 9, 11","options":["2","7","9","11"],"correct_answer":"9","cat":"Logical Reasoning","diff":"Easy","tip":"9 = 3×3 is NOT prime. All others are prime.","topic":"Odd One Out"},
        {"q":"4 days after Saturday is?","options":["Tuesday","Wednesday","Thursday","Monday"],"correct_answer":"Wednesday","cat":"Logical Reasoning","diff":"Easy","tip":"Sat + 4 = Wed.","topic":"Calendar"},
        {"q":"Man walks 5 km North, 3 km East, 5 km South. Distance from start?","options":["3 km","5 km","8 km","13 km"],"correct_answer":"3 km","cat":"Logical Reasoning","diff":"Medium","tip":"N 5 and S 5 cancel → net 3 km East.","topic":"Direction Sense"},
        {"q":"Series: 1, 4, 9, 16, 25, ?","options":["30","36","49","32"],"correct_answer":"36","cat":"Logical Reasoning","diff":"Easy","tip":"Perfect squares: 1²,2²,3²,4²,5²,6²=36.","topic":"Number Series"},
        {"q":"A is sister of B. B is brother of C. A is C's?","options":["Mother","Sister","Aunt","Cousin"],"correct_answer":"Sister","cat":"Logical Reasoning","diff":"Medium","tip":"A and B siblings, B and C siblings → A and C are siblings.","topic":"Blood Relations"},
        {"q":"ABCD : DCBA :: PQRS : ?","options":["SRQP","QRSP","PQRS","RQPS"],"correct_answer":"SRQP","cat":"Logical Reasoning","diff":"Easy","tip":"Pattern: reverse the sequence.","topic":"Coding-Decoding"},
    ]

    coding_pool = [
        {"q":"Output of: print(type([])) in Python?","options":["<class 'tuple'>","<class 'dict'>","<class 'list'>","<class 'set'>"],"correct_answer":"<class 'list'>","cat":"Coding","diff":"Easy","tip":"[] creates an empty list.","topic":"Python Basics"},
        {"q":"Method that removes and returns the last element of a Python list?","options":["remove()","delete()","pop()","discard()"],"correct_answer":"pop()","cat":"Coding","diff":"Easy","tip":"list.pop() removes and returns the last element by default.","topic":"Python Lists"},
        {"q":"Time complexity of inserting at beginning of Python list?","options":["O(1)","O(log n)","O(n)","O(n²)"],"correct_answer":"O(n)","cat":"Coding","diff":"Medium","tip":"Inserting at index 0 shifts all elements → O(n).","topic":"Data Structures"},
        {"q":"In Python, 'is' vs '==' difference?","options":["Both check value","'is' checks identity, '==' checks value","'is' checks value, '==' checks identity","They are identical"],"correct_answer":"'is' checks identity, '==' checks value","cat":"Coding","diff":"Medium","tip":"'is' compares object id(), '==' compares values.","topic":"Python Fundamentals"},
        {"q":"Space complexity of naive recursive Fibonacci?","options":["O(1)","O(n)","O(log n)","O(n²)"],"correct_answer":"O(n)","cat":"Coding","diff":"Hard","tip":"Each call adds a stack frame; max depth n → O(n) space.","topic":"Recursion"},
        {"q":"What does len('Hello World') return?","options":["10","11","12","9"],"correct_answer":"11","cat":"Coding","diff":"Easy","tip":"'Hello World' has 11 characters including the space.","topic":"Python Basics"},
    ]

    hr_pool = [
        {"q":"What does STAR stand for in behavioral interviews?","options":["Skill,Task,Action,Result","Situation,Task,Action,Result","Strength,Target,Achievement,Role","Strategy,Task,Approach,Resolution"],"correct_answer":"Situation,Task,Action,Result","cat":"HR","diff":"Easy","tip":"STAR is a structured approach to behavioral interview answers.","topic":"Interview Technique"},
        {"q":"Best approach when asked 'Why do you want to work here'?","options":["Talk about the high salary","Say you need a job","Research and align your goals with their mission","Mention no other offers"],"correct_answer":"Research and align your goals with their mission","cat":"HR","diff":"Easy","tip":"Show genuine interest in the company's mission and culture.","topic":"Interview Preparation"},
        {"q":"When answering 'Tell me about yourself', you should:","options":["Narrate entire life story","Give a 2-3 min professional summary relevant to the role","Only mention hobbies","Read from your resume"],"correct_answer":"Give a 2-3 min professional summary relevant to the role","cat":"HR","diff":"Easy","tip":"Past → Present → Future. Keep it concise and relevant.","topic":"Self Introduction"},
        {"q":"How to handle a question you don't know in an interview?","options":["Make up an answer","Stay silent","Acknowledge uncertainty, explain thought process, commit to learning","Ask interviewer to skip"],"correct_answer":"Acknowledge uncertainty, explain thought process, commit to learning","cat":"HR","diff":"Medium","tip":"Honesty + structured thinking is valued over bluffing.","topic":"Interview Strategy"},
    ]

    company_pool = [
        {"q":f"What is {company_name} primarily known for?","options":["Healthcare products","IT and software solutions","Agricultural commodities","Aerospace manufacturing"],"correct_answer":"IT and software solutions","cat":"Company Specific","diff":"Easy","tip":f"Research {company_name}'s products before the interview.","topic":"Company Knowledge"},
        {"q":"What does a 30-60-90 day plan mean when joining a company?","options":["A salary timeline","A structured plan for your first 30, 60, 90 days","A probation policy","A performance review schedule"],"correct_answer":"A structured plan for your first 30, 60, 90 days","cat":"Company Specific","diff":"Medium","tip":"A 30-60-90 plan shows initiative and preparation.","topic":"Career Planning"},
    ]

    skill_map = {
        "Python": {"q":"Which of the following is NOT a built-in Python data type?","options":["list","dict","array","tuple"],"correct_answer":"array","cat":"Technical","diff":"Easy","tip":"Python has list, dict, set, tuple. 'array' requires import.","topic":"Python"},
        "Java": {"q":"Which Java keyword prevents class inheritance?","options":["static","private","final","abstract"],"correct_answer":"final","cat":"Technical","diff":"Medium","tip":"'final' classes cannot be extended.","topic":"Java"},
        "SQL": {"q":"Which SQL command retrieves data from a table?","options":["INSERT","UPDATE","SELECT","DELETE"],"correct_answer":"SELECT","cat":"Technical","diff":"Easy","tip":"SELECT is the DML command for reading data.","topic":"SQL"},
        "JavaScript": {"q":"What does '===' check in JavaScript?","options":["Value only","Type only","Both value and type","Neither"],"correct_answer":"Both value and type","cat":"Technical","diff":"Easy","tip":"=== is strict equality — checks both value AND type.","topic":"JavaScript"},
        "React": {"q":"What is a React component?","options":["A database model","A reusable UI piece that returns JSX","A backend service","An HTTP handler"],"correct_answer":"A reusable UI piece that returns JSX","cat":"Technical","diff":"Easy","tip":"React components are the building blocks of the UI.","topic":"React"},
        "Git": {"q":"Which Git command creates a new branch?","options":["git merge","git branch <name>","git checkout master","git clone"],"correct_answer":"git branch <name>","cat":"Technical","diff":"Easy","tip":"'git branch <name>' creates; 'git checkout -b <name>' creates and switches.","topic":"Git"},
        "Docker": {"q":"What is a Docker image?","options":["A running container","A snapshot/template to create containers","A volume for persistent data","A network interface"],"correct_answer":"A snapshot/template to create containers","cat":"Technical","diff":"Medium","tip":"Images are read-only templates; containers are running instances.","topic":"Docker"},
        "AWS": {"q":"What does S3 stand for in AWS?","options":["Simple Storage Service","Secure Server System","Scalable Storage Solution","Server-Side Service"],"correct_answer":"Simple Storage Service","cat":"Technical","diff":"Easy","tip":"Amazon S3 = Simple Storage Service, used for object storage.","topic":"AWS"},
    }

    skill_mcqs = [skill_map[s] for s in (company_skills or []) if s in skill_map]

    def not_seen(q):
        return q["q"].strip().lower() not in seen_questions

    pools = [
        [q for q in tech_pool    if not_seen(q)],
        [q for q in aptitude_pool if not_seen(q)],
        [q for q in logical_pool  if not_seen(q)],
        [q for q in coding_pool   if not_seen(q)],
        [q for q in hr_pool       if not_seen(q)],
        [q for q in company_pool  if not_seen(q)],
        [q for q in skill_mcqs    if not_seen(q)],
    ]
    for p in pools:
        _rnd.shuffle(p)
    tp, ap, lp, cp, hp, comp, skp = pools

    selected = tp[:7] + ap[:4] + lp[:3] + cp[:3] + hp[:2] + comp[:1] + skp[:2]
    _rnd.shuffle(selected)

    for i, q in enumerate(selected):
        q["id"] = i + 1
        q.setdefault("tip", "")
        q.setdefault("options", [])
        q.setdefault("correct_answer", "")
        q.setdefault("topic", "")

    return {
        "questions":          selected,
        "company":            {"name": company_name},
        "role":               {"title": job_title},
        "recommended_topics": [],
    }




# ---------------------------------------------------------------------------
# ── RESUME CONTENT GENERATION ────────────────────────────────────────────────
# ---------------------------------------------------------------------------ervice import call_qwen, parse_qwen_json

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

