"""
Resume Generation Service
=========================
Orchestrates AI-powered resume creation and ATS optimization.

All Qwen calls go through qwen_service.call_qwen() — never directly to HuggingFace.

Public API:
    generate_resume(user_id, wizard_data, source_resume_id, company_id,
                    company_name_manual, job_role, job_description, template)
    → dict  (validated JSON content + metadata)

    render_pdf(content_json, template, output_path) → path
    render_docx(content_json, template, output_path) → path
"""
import json
import logging
import os
import re

logger = logging.getLogger(__name__)

# ── JSON SCHEMA ───────────────────────────────────────────────────────────────

_RESUME_SCHEMA = """{
  "candidate": {
    "name": "",
    "email": "",
    "phone": "",
    "location": "",
    "linkedin": "",
    "github": "",
    "portfolio": ""
  },
  "target": {
    "company": "",
    "job_role": ""
  },
  "professional_summary": "",
  "skills": {
    "programming": [],
    "frameworks": [],
    "databases": [],
    "analytics": [],
    "tools": [],
    "other": []
  },
  "experience": [
    {
      "title": "",
      "company": "",
      "duration": "",
      "responsibilities": []
    }
  ],
  "projects": [
    {
      "name": "",
      "technologies": "",
      "description": "",
      "bullets": [],
      "github": "",
      "url": ""
    }
  ],
  "education": [
    {
      "degree": "",
      "institution": "",
      "year": "",
      "cgpa": ""
    }
  ],
  "certifications": [],
  "achievements": [],
  "ats": {
    "score": 0,
    "matched_keywords": [],
    "missing_keywords": [],
    "partial_keywords": []
  },
  "optimization_notes": []
}"""

# ── DATA COLLECTORS ───────────────────────────────────────────────────────────


def collect_candidate_data(user_id, wizard_data=None):
    """
    Collect all candidate information from the database (profile, skills,
    education, projects, experience, certifications).

    If wizard_data is provided (Flow B — no resume), merge it with DB data.
    DB data is always preferred to avoid inconsistency.
    """
    from models.profile import ProfileModel
    from models.user import UserModel

    user = UserModel.get_by_id(user_id) or {}
    profile = ProfileModel.get(user_id) or {}
    skills = ProfileModel.get_skills(user_id) or []
    education = ProfileModel.get_education(user_id) or []
    projects = ProfileModel.get_projects(user_id) or []
    experience = ProfileModel.get_experience(user_id) or []
    certifications = ProfileModel.get_certifications(user_id) or []

    # Merge wizard form data for fields not yet in DB
    wd = wizard_data or {}

    candidate = {
        "name":      user.get("full_name") or wd.get("full_name", ""),
        "email":     user.get("email")     or wd.get("email", ""),
        "phone":     profile.get("phone")  or wd.get("phone", ""),
        "location":  profile.get("location") or wd.get("location", ""),
        "linkedin":  profile.get("linkedin_url") or wd.get("linkedin", ""),
        "github":    profile.get("github_url")   or wd.get("github", ""),
        "portfolio": profile.get("portfolio_url") or wd.get("portfolio", ""),
        "objective": profile.get("career_objective") or wd.get("career_objective", ""),
    }

    # Skills — normalise by category
    skill_map = {
        "Programming": [], "Framework": [], "Database": [],
        "Cloud": [], "DevOps": [], "Tool": [], "Soft Skill": [], "Other": []
    }
    for s in skills:
        cat = s.get("category", "Other")
        skill_map.setdefault(cat, []).append(s.get("skill_name", ""))

    # Wizard skills supplement DB skills
    for ws in wd.get("skills", []):
        name = ws.get("name", "").strip()
        cat  = ws.get("category", "Other")
        if name and name not in skill_map.get(cat, []):
            skill_map.setdefault(cat, []).append(name)

    education_list = []
    seen_edu = set()
    for e in education:
        key = (e.get("institution") or "").strip().lower()
        if key and key not in seen_edu:
            seen_edu.add(key)
            education_list.append({
                "degree":      e.get("degree", ""),
                "institution": e.get("institution", ""),
                "year":        f"{e.get('start_year','')}–{e.get('end_year','')}",
                "cgpa":        str(e.get("cgpa", "") or ""),
                "field":       e.get("field_of_study", ""),
            })
    # Wizard education entries — only add if not already in DB
    for we in wd.get("education", []):
        key = (we.get("institution") or "").strip().lower()
        if key and key not in seen_edu:
            seen_edu.add(key)
            education_list.append({
                "degree":      we.get("degree", ""),
                "institution": we.get("institution", ""),
                "year":        f"{we.get('start_year','')}–{we.get('graduation_year','')}",
                "cgpa":        we.get("cgpa", ""),
                "field":       we.get("department", ""),
            })

    project_list = []
    seen_projects = set()
    for p in projects:
        key = (p.get("title") or "").strip().lower()
        if key and key not in seen_projects:
            seen_projects.add(key)
            project_list.append({
                "name":         p.get("title", ""),
                "technologies": p.get("technologies", ""),
                "description":  p.get("description", ""),
                "github":       p.get("github_url", ""),
                "url":          p.get("live_url", ""),
            })
    for wp in wd.get("projects", []):
        key = (wp.get("name") or wp.get("title") or "").strip().lower()
        if key and key not in seen_projects:
            seen_projects.add(key)
            project_list.append({
                "name":         wp.get("name") or wp.get("title", ""),
                "technologies": wp.get("technologies", ""),
                "description":  wp.get("description", ""),
                "github":       wp.get("github_url", ""),
                "url":          wp.get("project_url", ""),
                "role":         wp.get("role", ""),
            })

    experience_list = []
    for exp in experience:
        experience_list.append({
            "title":   exp.get("job_title", ""),
            "company": exp.get("company_name", ""),
            "start":   str(exp.get("start_date", "") or ""),
            "end":     str(exp.get("end_date", "") or "Present"),
            "current": bool(exp.get("is_current")),
            "desc":    exp.get("description", ""),
        })
    for we in wd.get("experience", []):
        if we.get("company") and we.get("role"):
            experience_list.append({
                "title":   we.get("role", ""),
                "company": we.get("company", ""),
                "start":   we.get("start_date", ""),
                "end":     we.get("end_date", "Present"),
                "current": bool(we.get("is_current")),
                "desc":    we.get("responsibilities", ""),
            })

    cert_list = []
    for c in certifications:
        cert_list.append({
            "name":   c.get("cert_name", ""),
            "org":    c.get("issuing_org", ""),
            "year":   str(c.get("issue_date", "") or ""),
            "url":    c.get("credential_url", ""),
        })
    for wc in wd.get("certifications", []):
        if wc.get("name"):
            cert_list.append({
                "name": wc.get("name", ""),
                "org":  wc.get("org", ""),
                "year": wc.get("year", ""),
                "url":  wc.get("url", ""),
            })

    achievements = list(wd.get("achievements", []))

    return {
        "candidate":    candidate,
        "skills":       skill_map,
        "education":    education_list,
        "projects":     project_list,
        "experience":   experience_list,
        "certifications": cert_list,
        "achievements": achievements,
    }


def collect_company_data(company_id=None, company_name_manual=None, job_description=None):
    """
    Collect company intelligence from DB or use manual entry.
    Returns a dict safe for inclusion in the AI prompt.
    """
    company = {}
    required_skills = []
    jobs = []

    if company_id:
        try:
            from models.company import CompanyModel
            db_company = CompanyModel.get_by_id(company_id)
            if db_company:
                company = {
                    "name":        db_company.get("name", ""),
                    "industry":    db_company.get("industry", ""),
                    "description": db_company.get("description", ""),
                    "process":     db_company.get("recruitment_process", ""),
                }
                skills_rows = CompanyModel.get_skills(company_id)
                required_skills = [s["skill_name"] for s in (skills_rows or [])]
                jobs = CompanyModel.get_jobs(company_id)
        except Exception as e:
            logger.warning(f"Company DB lookup failed: {e}")

    if not company.get("name") and company_name_manual:
        company = {"name": company_name_manual, "industry": "", "description": "", "process": ""}

    return {
        "company":         company,
        "required_skills": required_skills,
        "jobs":            jobs,
        "job_description": job_description or "",
    }


# ── PROMPT BUILDER ────────────────────────────────────────────────────────────

def build_resume_generation_prompt(candidate_data, company_data, job_role):
    """
    Build the Qwen prompt for resume generation.
    All fabrication is explicitly forbidden in the prompt.
    """
    cand     = candidate_data
    company  = company_data.get("company", {})
    req_sk   = company_data.get("required_skills", [])
    jd_text  = company_data.get("job_description", "")

    # Flatten skills
    all_skills = []
    for cat_skills in cand["skills"].values():
        all_skills.extend(cat_skills)

    # Summarize candidate for the prompt
    education_lines = "\n".join(
        f"- {e['degree']} {e.get('field','')} at {e['institution']} ({e['year']}) CGPA: {e['cgpa']}"
        for e in cand["education"]
    ) or "Not provided — extract from SOURCE RESUME below"

    project_lines = "\n".join(
        f"- {p['name']}: {p['description']} [Tech: {p['technologies']}]"
        for p in cand.get("projects", []) if p.get("name")
    ) or "Not provided — extract from SOURCE RESUME below"

    exp_lines = "\n".join(
        f"- {e['title']} at {e['company']} ({e.get('start','')} - {e.get('end','')}): {e.get('desc','')}"
        for e in cand["experience"]
    ) or "Not provided — extract from SOURCE RESUME below"

    cert_lines = "\n".join(
        f"- {c['name']} by {c['org']} ({c['year']})" for c in cand["certifications"]
    ) or "None"

    achv_lines = "\n".join(
        f"- {a}" if isinstance(a, str) else f"- {a.get('title','')}: {a.get('description','')}"
        for a in cand["achievements"]
    ) or "None"

    company_name = company.get("name", "the target company")
    industry     = company.get("industry", "technology")
    req_sk_str   = ", ".join(req_sk[:15]) if req_sk else "general software engineering skills"

    jd_section = ""
    if jd_text and jd_text.strip():
        jd_section = f"""
JOB DESCRIPTION (use this as a strong ATS optimization source):
{jd_text[:1500]}
"""

    # Source resume section — the actual uploaded PDF/DOCX text
    source_resume_section = ""
    raw_resume = cand.get("_source_resume", "")
    if raw_resume and raw_resume.strip():
        source_resume_section = f"""
===== SOURCE RESUME (RAW TEXT from uploaded file) =====
Use this raw resume text as the PRIMARY source to extract Education, Work Experience,
Projects, Certifications, and any other details when the CANDIDATE PROFILE above says
"Not provided". Extract them accurately and do NOT mark sections as N/A if the
information exists anywhere in this raw text.

{raw_resume}
===== END OF SOURCE RESUME =====
"""

    prompt = f"""You are an expert ATS resume writer and career counselor.

Analyze the following candidate profile and source resume carefully, then create
a truthful, professional, ATS-optimized resume for the target role.

STRICT RULES — NEVER VIOLATE:
1. NEVER output "N/A" for Education, Experience, or Projects if information is
   available in the SOURCE RESUME TEXT below. Always extract and use that data.
2. Do NOT invent any skill, experience, project, certification, metric, or
   technology that is not present in the candidate data or source resume.
3. Do NOT add fake responsibilities, fake companies, or fake achievements.
4. If the candidate does not have a required skill, list it in ats.missing_keywords.
5. You MAY improve wording, clarity, and professional language while staying truthful.
6. Use strong action verbs in bullet points (e.g., Developed, Implemented, Designed).
7. Avoid first-person ("I", "me", "my").
8. Keep the professional_summary to 3-4 concise sentences.
9. Return ONLY the JSON object. No markdown, no explanation outside JSON.
10. All array fields must be populated. Never leave education, projects, or
    experience as an empty array if the source resume contains that information.

===== CANDIDATE PROFILE (from user database) =====

Name: {cand['candidate']['name']}
Email: {cand['candidate']['email']}
Phone: {cand['candidate']['phone']}
Location: {cand['candidate']['location']}
LinkedIn: {cand['candidate']['linkedin']}
GitHub: {cand['candidate']['github']}

Skills:
{json.dumps(cand['skills'], indent=2)}

Education:
{education_lines}

Projects:
{project_lines}

Experience:
{exp_lines}

Certifications:
{cert_lines}

Achievements:
{achv_lines}
{source_resume_section}
===== TARGET =====

Company: {company_name}
Industry: {industry}
Job Role: {job_role}
Required Skills: {req_sk_str}
{jd_section}
===== TASK =====

Generate a complete, ATS-optimized resume:
- Use the CANDIDATE PROFILE data as primary source.
- If Education, Experience, or Projects say "Not provided", extract them from
  the SOURCE RESUME raw text above. Every field must be filled accurately.
- Improve descriptions to be professional and ATS-keyword-rich.
- Write a compelling 3-4 sentence professional_summary for the target role.
- For ats.score: integer 0-100 based on skill and keyword match to the target role.
- For ats.missing_keywords: skills in required_skills NOT in the candidate's skillset.

Return ONLY this exact JSON structure (all arrays populated, no null or N/A values):

{_RESUME_SCHEMA}"""

    return prompt


# ── MAIN GENERATOR ────────────────────────────────────────────────────────────

def generate_resume(user_id, wizard_data=None, source_resume_id=None,
                    company_id=None, company_name_manual=None,
                    job_role="Software Engineer", job_description=None,
                    template="classic", source_resume_text=None):
    """
    Main entry point for AI resume generation.

    Returns:
        dict with keys:
            content_json   — full structured resume data (dict)
            ats_score      — int 0-100
            skill_match    — int 0-100
            label          — human-readable label
            missing_skills — list of strings
            optimization_notes — list of strings
            error          — None or error message string

    All Qwen calls go through qwen_service.call_qwen().
    """
    from services.qwen_service import call_qwen, parse_qwen_json

    # 1. Collect data
    candidate_data = collect_candidate_data(user_id, wizard_data)
    company_data   = collect_company_data(company_id, company_name_manual, job_description)

    # If source resume text is available, include it fully for AI extraction
    if source_resume_text:
        candidate_data["_source_resume"] = source_resume_text[:4000]

    company_name = company_data["company"].get("name") or company_name_manual or "General"
    label = f"{company_name} — {job_role}"

    # 2. Build prompt
    prompt = build_resume_generation_prompt(candidate_data, company_data, job_role)

    # 3. Call Qwen
    logger.info(f"Generating resume for user={user_id} target='{label}'")
    raw = call_qwen(prompt, max_tokens=2500, retries=2, temperature=0.35)

    if not raw:
        logger.error("Qwen returned no response for resume generation")
        return _fallback_resume(candidate_data, company_data, job_role, label,
                                error="AI generation failed — Qwen returned no response.")

    # 4. Parse JSON
    content = parse_qwen_json(raw)
    if not content:
        logger.error("Qwen response could not be parsed as JSON")
        return _fallback_resume(candidate_data, company_data, job_role, label,
                                error="AI generation failed — response was not valid JSON.")

    # 5. Validate and patch
    content = _validate_and_patch(content, candidate_data, company_name, job_role)

    # 6. Extract scores
    ats_block   = content.get("ats", {})
    ai_score    = int(min(100, max(0, ats_block.get("score", 0))))

    # If AI returned 0, compute a real keyword-based ATS score as fallback
    if ai_score == 0:
        ai_score = _compute_keyword_ats_score(content, job_description, job_role, company_data.get("required_skills", []))
        ats_block["score"] = ai_score
        content["ats"] = ats_block

    ats_score   = ai_score
    req_skills  = company_data.get("required_skills", [])
    all_sk      = _flat_skills(content.get("skills", {}))
    skill_match = _calc_skill_match(all_sk, req_skills) if req_skills else _compute_keyword_ats_score(content, job_description, job_role, [])

    logger.info(f"Resume generated — ATS={ats_score} SkillMatch={skill_match}")

    return {
        "content_json":        content,
        "ats_score":           ats_score,
        "skill_match":         skill_match,
        "label":               label,
        "missing_skills":      ats_block.get("missing_keywords", []),
        "matched_skills":      ats_block.get("matched_keywords", []),
        "optimization_notes":  content.get("optimization_notes", []),
        "error":               None,
    }


# ── VALIDATION ────────────────────────────────────────────────────────────────

def _validate_and_patch(content, candidate_data, company_name, job_role):
    """
    Ensure required fields exist and strip any invented data.
    Qwen sometimes hallucinates experience — detect and remove.
    """
    # Ensure candidate block matches real data
    real_cand = candidate_data["candidate"]
    c = content.setdefault("candidate", {})
    for key in ("name", "email", "phone", "location", "linkedin", "github"):
        if not c.get(key) and real_cand.get(key):
            c[key] = real_cand[key]

    content.setdefault("target", {})["company"]  = company_name
    content.setdefault("target", {})["job_role"]  = job_role

    # Ensure skills is a dict with expected keys
    if not isinstance(content.get("skills"), dict):
        content["skills"] = {}
    for k in ("programming", "frameworks", "databases", "analytics", "tools", "other"):
        content["skills"].setdefault(k, [])

    # Validate experience — remove only clearly hallucinated companies
    # If source resume was provided, trust AI extraction — it read the actual file
    has_source_resume = bool(candidate_data.get("_source_resume"))
    real_companies = {e["company"].lower() for e in candidate_data.get("experience", [])}
    real_companies.add("fresher")  # allow "Fresher" token
    validated_exp = []
    for exp in content.get("experience", []):
        co = (exp.get("company") or "").lower().strip()
        # If source resume was uploaded, trust AI extraction (it read the actual file)
        # Only strip if NO source resume and company is completely unknown
        if has_source_resume or not co or co in real_companies or not real_companies - {"fresher"}:
            validated_exp.append(exp)
        else:
            logger.warning(f"Removed potentially hallucinated experience: {exp.get('company')}")
    content["experience"] = validated_exp

    # Ensure lists exist
    for key in ("projects", "education", "certifications", "achievements", "optimization_notes"):
        if not isinstance(content.get(key), list):
            content[key] = []

    # Remove N/A placeholder items that Qwen sometimes inserts
    def _clean_na(items, key_field):
        return [
            item for item in items
            if isinstance(item, dict) and (item.get(key_field) or "").strip().upper() not in ("N/A", "NA", "", "NONE")
        ]
    content["education"] = _clean_na(content.get("education", []), "degree")
    content["projects"]  = _clean_na(content.get("projects", []),  "name")
    content["experience"] = [
        exp for exp in content.get("experience", [])
        if isinstance(exp, dict) and (exp.get("company") or exp.get("title") or "").strip().upper() not in ("N/A", "NA", "", "NONE", "FRESHER")
    ] or content.get("experience", [])  # keep original if all removed
    if not isinstance(content.get("ats"), dict):
        content["ats"] = {"score": 0, "matched_keywords": [], "missing_keywords": [], "partial_keywords": []}

    return content


def _flat_skills(skills_dict):
    """Flatten skills dict to a deduplicated list of lowercase skill tokens.
    Handles comma-separated strings like 'python,sql,ml' correctly."""
    flat = set()
    for v in skills_dict.values():
        if isinstance(v, list):
            for s in v:
                if s and isinstance(s, str):
                    # Split on comma to handle 'python,sql,ml' stored as single string
                    for tok in s.split(','):
                        tok = tok.strip().lower()
                        if tok:
                            flat.add(tok)
    return list(flat)


def _compute_keyword_ats_score(content, job_description, job_role, required_skills):
    """
    Compute a realistic ATS score by comparing resume text tokens
    against job description keywords. Falls back to a skills-based
    calculation when no job description is provided.
    """
    # Build the resume text corpus
    corpus_parts = []
    corpus_parts.append(content.get("professional_summary", ""))
    for exp in content.get("experience", []):
        corpus_parts.append(exp.get("title", ""))
        corpus_parts.append(exp.get("company", ""))
        for r in (exp.get("responsibilities") or []):
            corpus_parts.append(str(r))
    for proj in content.get("projects", []):
        corpus_parts.append(proj.get("name", ""))
        corpus_parts.append(proj.get("description", ""))
        corpus_parts.append(proj.get("technologies", ""))
    for edu in content.get("education", []):
        corpus_parts.append(edu.get("degree", ""))
    # Add all skills
    corpus_parts.extend(_flat_skills(content.get("skills", {})))

    resume_text = " ".join(corpus_parts).lower()
    resume_tokens = set(re.findall(r'[a-zA-Z0-9#+.]{2,}', resume_text))

    # Extract keywords from job description + role
    jd_text = ((job_description or "") + " " + (job_role or "")).lower()
    jd_tokens = set(re.findall(r'[a-zA-Z0-9#+.]{2,}', jd_text))

    # Remove stop words
    stop = {'and','the','for','with','in','of','to','a','an','is','are','be',
            'will','we','you','your','our','that','this','have','has','on',
            'at','as','or','from','by','not','can','may','job','role','work'}
    jd_tokens -= stop
    resume_tokens -= stop

    if required_skills:
        req_lower = [s.lower() for s in required_skills]
        matched = sum(1 for s in req_lower if any(s in rt for rt in resume_tokens))
        base = int(matched / len(req_lower) * 100)
    elif jd_tokens:
        matched = len(jd_tokens & resume_tokens)
        base = int(min(100, matched / max(1, len(jd_tokens)) * 150))  # 150x to scale up
    else:
        # No JD provided: score based on resume completeness
        has_exp = len(content.get("experience", [])) > 0
        has_edu = len(content.get("education", [])) > 0
        has_proj = len(content.get("projects", [])) > 0
        has_skills = bool(_flat_skills(content.get("skills", {})))
        has_summary = bool(content.get("professional_summary", "").strip())
        base = (int(has_exp) + int(has_edu) + int(has_proj) + int(has_skills) + int(has_summary)) * 14

    return min(100, max(5, base))


def _calc_skill_match(resume_skills, required_skills):
    if not required_skills:
        return 0
    matched = sum(1 for s in required_skills if s.lower() in resume_skills)
    return int(matched / len(required_skills) * 100)


def _fallback_resume(candidate_data, company_data, job_role, label, error):
    """Return a minimal structured resume from real DB data without AI."""
    cand = candidate_data["candidate"]
    sk   = candidate_data["skills"]
    all_sk_flat = []
    for v in sk.values():
        all_sk_flat.extend(v)

    req_skills   = company_data.get("required_skills", [])
    skill_lower  = [s.lower() for s in all_sk_flat]
    missing      = [s for s in req_skills if s.lower() not in skill_lower]
    matched      = [s for s in req_skills if s.lower() in skill_lower]
    skill_match  = _calc_skill_match(skill_lower, req_skills)

    # Deduplicate and split comma-separated skills (e.g. 'python,sql,ml' -> ['python','sql','ml'])
    all_sk_clean = []
    seen_sk = set()
    for raw in all_sk_flat:
        for tok in (raw or "").split(','):
            tok = tok.strip()
            if tok and tok.lower() not in seen_sk:
                seen_sk.add(tok.lower())
                all_sk_clean.append(tok)

    content = {
        "candidate": cand,
        "target": {"company": company_data["company"].get("name",""), "job_role": job_role},
        "professional_summary": (
            f"{cand.get('name','Candidate')} is an aspiring {job_role} "
            f"with skills in {', '.join(all_sk_clean[:5])}. "
            f"Passionate about technology and eager to contribute to "
            f"{company_data['company'].get('name','the target organization')}."
        ),
        "skills": sk,
        "experience": [
            {"title": e["title"], "company": e["company"],
             "duration": f"{e['start']} – {e['end']}",
             "responsibilities": [e.get("desc", "")] if e.get("desc") else []}
            for e in candidate_data.get("experience", [])
        ],
        "projects": [
            {"name": p["name"], "technologies": p.get("technologies",""),
             "description": p.get("description",""),
             "bullets": [p.get("description","")],
             "github": p.get("github",""), "url": p.get("url","")}
            for p in candidate_data.get("projects", [])
        ],
        "education": candidate_data.get("education", []),
        "certifications": [c["name"] for c in candidate_data.get("certifications", [])],
        "achievements": candidate_data.get("achievements", []),
        "ats": {
            "score": skill_match,
            "matched_keywords": matched,
            "missing_keywords": missing,
            "partial_keywords": []
        },
        "optimization_notes": [
            "AI generation was unavailable. Resume was built from your profile data.",
            "Consider running generation again when the AI service is available."
        ]
    }

    return {
        "content_json":       content,
        "ats_score":          skill_match,
        "skill_match":        skill_match,
        "label":              label,
        "missing_skills":     missing,
        "matched_skills":     matched,
        "optimization_notes": content["optimization_notes"],
        "error":              error,
    }


# ── PDF RENDERER ──────────────────────────────────────────────────────────────

def render_pdf(content_json, template_name="classic", output_path=None):
    """
    Render a generated resume to PDF using reportlab.
    Returns the output_path on success, None on failure.
    """
    try:
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch
        from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
        from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer,
                                        HRFlowable, ListFlowable, ListItem)

        if not output_path:
            return None

        PAGE_W, PAGE_H = A4
        doc = SimpleDocTemplate(
            output_path, pagesize=A4,
            rightMargin=0.65*inch, leftMargin=0.65*inch,
            topMargin=0.65*inch,   bottomMargin=0.65*inch
        )

        styles = getSampleStyleSheet()
        PALETTE = {
            "classic": {"primary": "#1E3A5F", "accent": "#2563EB", "line": "#334155"},
            "modern":  {"primary": "#4F46E5", "accent": "#7C3AED", "line": "#6366F1"},
            "minimal": {"primary": "#111827", "accent": "#374151", "line": "#6B7280"},
            "clean_classic": {"primary": "#000000", "accent": "#000000", "line": "#000000"},
            "prestige_red":  {"primary": "#8B0000", "accent": "#8B0000", "line": "#8B0000"},
        }.get(template_name, {
            "primary": "#1E3A5F", "accent": "#2563EB", "line": "#334155"
        })

        def hex_color(h):
            h = h.lstrip("#")
            return colors.Color(*[int(h[i:i+2],16)/255 for i in (0,2,4)])

        c_primary = hex_color(PALETTE["primary"])
        c_accent  = hex_color(PALETTE["accent"])
        c_line    = hex_color(PALETTE["line"])
        c_text    = hex_color("#1E293B")
        c_muted   = hex_color("#64748B")

        # Alignments
        header_align = TA_LEFT if template_name == "prestige_red" else TA_CENTER

        # Styles
        name_st  = ParagraphStyle("Name",  parent=styles["Normal"], fontSize=20,
                                  fontName="Helvetica-Bold", textColor=c_primary,
                                  alignment=header_align, spaceAfter=2)
        contact_st = ParagraphStyle("Contact", parent=styles["Normal"], fontSize=9,
                                    textColor=c_muted, alignment=header_align, spaceAfter=8)
        section_st = ParagraphStyle("Section", parent=styles["Normal"], fontSize=11,
                                    fontName="Helvetica-Bold", textColor=c_primary,
                                    spaceBefore=10, spaceAfter=3)
        body_st  = ParagraphStyle("Body", parent=styles["Normal"], fontSize=9.5,
                                  textColor=c_text, leading=14, spaceAfter=2,
                                  alignment=TA_JUSTIFY)
        bullet_st = ParagraphStyle("Bullet", parent=styles["Normal"], fontSize=9.5,
                                   textColor=c_text, leading=13, leftIndent=12,
                                   spaceAfter=1)
        job_title_st = ParagraphStyle("JobTitle", parent=styles["Normal"], fontSize=10,
                                      fontName="Helvetica-Bold", textColor=c_text, spaceAfter=1)
        meta_st = ParagraphStyle("Meta", parent=styles["Normal"], fontSize=9,
                                 textColor=c_muted, spaceAfter=2)

        cand = content_json.get("candidate", {})
        story = []

        # ── Header ──────────────────────────────────────────────────────────
        story.append(Paragraph(cand.get("name", "Candidate Name"), name_st))
        
        # Add job role below name for prestige_red style
        if template_name == "prestige_red":
            role_st = ParagraphStyle("Role", parent=styles["Normal"], fontSize=11,
                                     fontName="Helvetica-Oblique", textColor=c_muted,
                                     alignment=header_align, spaceAfter=4)
            story.append(Paragraph(content_json.get("target", {}).get("job_role", "Professional"), role_st))

        contact_parts = [p for p in [
            cand.get("email"), cand.get("phone"), cand.get("location"),
            cand.get("linkedin"), cand.get("github"), cand.get("portfolio")
        ] if p]
        story.append(Paragraph("  |  ".join(contact_parts), contact_st))
        story.append(HRFlowable(width="100%", thickness=1.5, color=c_accent, spaceAfter=6))

        def section(title):
            story.append(Paragraph(title.upper(), section_st))
            story.append(HRFlowable(width="100%", thickness=0.5, color=c_line, spaceAfter=4))

        # ── Professional Summary ─────────────────────────────────────────────
        summary = content_json.get("professional_summary", "")
        if summary:
            section("Professional Summary")
            story.append(Paragraph(summary, body_st))

        # ── Skills ──────────────────────────────────────────────────────────
        sk = content_json.get("skills", {})
        all_sk_lines = []
        labels_map = {
            "programming": "Programming",
            "frameworks":  "Frameworks",
            "databases":   "Databases",
            "analytics":   "Data & Analytics",
            "tools":       "Tools",
            "other":       "Other",
        }
        for key, label in labels_map.items():
            vals = [s for s in sk.get(key, []) if s]
            if vals:
                all_sk_lines.append(f"<b>{label}:</b> {', '.join(vals)}")
        if all_sk_lines:
            section("Skills")
            for line in all_sk_lines:
                story.append(Paragraph(line, body_st))

        # ── Education ───────────────────────────────────────────────────────
        education = content_json.get("education", [])
        if education:
            section("Education")
            for edu in education:
                deg  = edu.get("degree", "")
                inst = edu.get("institution", "")
                yr   = edu.get("year", "")
                cgpa = f" | CGPA: {edu['cgpa']}" if edu.get("cgpa") else ""
                field = f", {edu['field']}" if edu.get("field") else ""
                story.append(Paragraph(f"<b>{deg}{field}</b>", job_title_st))
                story.append(Paragraph(f"{inst}  {yr}{cgpa}", meta_st))

        # ── Experience ──────────────────────────────────────────────────────
        experience = content_json.get("experience", [])
        if experience:
            section("Experience")
            for exp in experience:
                title   = exp.get("title", "")
                company = exp.get("company", "")
                dur     = exp.get("duration", "")
                if title or company:
                    story.append(Paragraph(f"<b>{title}</b> — {company}", job_title_st))
                    if dur:
                        story.append(Paragraph(dur, meta_st))
                for resp in (exp.get("responsibilities") or []):
                    if resp:
                        story.append(Paragraph(f"• {resp}", bullet_st))
                story.append(Spacer(1, 4))

        # ── Projects ────────────────────────────────────────────────────────
        projects = content_json.get("projects", [])
        if projects:
            section("Projects")
            for proj in projects:
                name  = proj.get("name", "")
                tech  = proj.get("technologies", "")
                desc  = proj.get("description", "")
                bullets = proj.get("bullets", [])
                gh    = proj.get("github", "")
                header = f"<b>{name}</b>"
                if tech:
                    header += f" <font color='#64748B' size='8'>| {tech}</font>"
                story.append(Paragraph(header, job_title_st))
                if desc and not bullets:
                    story.append(Paragraph(desc, bullet_st))
                for b in (bullets or []):
                    if b:
                        story.append(Paragraph(f"• {b}", bullet_st))
                if gh:
                    story.append(Paragraph(f"<font color='#2563EB'>{gh}</font>", meta_st))
                story.append(Spacer(1, 4))

        # ── Certifications ──────────────────────────────────────────────────
        certs = content_json.get("certifications", [])
        if certs:
            section("Certifications")
            for cert in certs:
                if isinstance(cert, dict):
                    story.append(Paragraph(
                        f"• <b>{cert.get('name','')}</b> — {cert.get('org','')} ({cert.get('year','')})",
                        bullet_st
                    ))
                else:
                    story.append(Paragraph(f"• {cert}", bullet_st))

        # ── Achievements ────────────────────────────────────────────────────
        achievements = content_json.get("achievements", [])
        if achievements:
            section("Achievements")
            for ach in achievements:
                if isinstance(ach, dict):
                    story.append(Paragraph(
                        f"• <b>{ach.get('title','')}</b>: {ach.get('description','')}",
                        bullet_st
                    ))
                else:
                    story.append(Paragraph(f"• {ach}", bullet_st))

        doc.build(story)
        return output_path

    except Exception as exc:
        logger.error(f"PDF render error: {exc}")
        return None


# ── DOCX RENDERER ─────────────────────────────────────────────────────────────

def render_docx(content_json, template_name="classic", output_path=None):
    """
    Render a generated resume to DOCX using python-docx.
    Returns the output_path on success, None on failure.
    """
    try:
        from docx import Document
        from docx.shared import Pt, RGBColor, Inches, Cm
        from docx.enum.text import WD_ALIGN_PARAGRAPH
        from docx.oxml.ns import qn
        from docx.oxml import OxmlElement

        if not output_path:
            return None

        PALETTES = {
            "classic":       (0x1E, 0x3A, 0x5F),
            "modern":        (0x4F, 0x46, 0xE5),
            "minimal":       (0x11, 0x18, 0x27),
            "clean_classic": (0x00, 0x00, 0x00),
            "prestige_red":  (0x8B, 0x00, 0x00),
        }
        pr, pg, pb = PALETTES.get(template_name, PALETTES["classic"])

        header_align = WD_ALIGN_PARAGRAPH.LEFT if template_name == "prestige_red" else WD_ALIGN_PARAGRAPH.CENTER

        doc = Document()

        # Page margins
        for section in doc.sections:
            section.top_margin    = Cm(1.5)
            section.bottom_margin = Cm(1.5)
            section.left_margin   = Cm(2)
            section.right_margin  = Cm(2)

        def add_hr(p):
            """Add a horizontal rule after a paragraph."""
            p_elem = p._element
            pPr = p_elem.get_or_add_pPr()
            pBdr = OxmlElement('w:pBdr')
            bottom = OxmlElement('w:bottom')
            bottom.set(qn('w:val'), 'single')
            bottom.set(qn('w:sz'), '6')
            bottom.set(qn('w:space'), '1')
            bottom.set(qn('w:color'), f'{pr:02X}{pg:02X}{pb:02X}')
            pBdr.append(bottom)
            pPr.append(pBdr)

        def set_run_color(run, r, g, b):
            run.font.color.rgb = RGBColor(r, g, b)

        cand = content_json.get("candidate", {})

        # ── Name ────────────────────────────────────────────────────────────
        name_p = doc.add_paragraph()
        name_p.alignment = header_align
        name_r = name_p.add_run(cand.get("name", "Candidate Name"))
        name_r.bold = True
        name_r.font.size = Pt(20)
        set_run_color(name_r, pr, pg, pb)
        
        # Add job role for prestige_red
        if template_name == "prestige_red":
            role_p = doc.add_paragraph()
            role_p.alignment = header_align
            role_r = role_p.add_run(content_json.get("target", {}).get("job_role", "Professional"))
            role_r.italic = True
            role_r.font.size = Pt(11)
            set_run_color(role_r, 0x64, 0x74, 0x8B)

        # ── Contact ─────────────────────────────────────────────────────────
        contact_parts = [p for p in [
            cand.get("email"), cand.get("phone"), cand.get("location"),
            cand.get("linkedin"), cand.get("github")
        ] if p]
        contact_p = doc.add_paragraph("  |  ".join(contact_parts))
        contact_p.alignment = header_align
        for run in contact_p.runs:
            run.font.size = Pt(9)
            set_run_color(run, 0x64, 0x74, 0x8B)
        add_hr(contact_p)

        def add_section(title):
            p = doc.add_paragraph()
            run = p.add_run(title.upper())
            run.bold = True
            run.font.size = Pt(10.5)
            set_run_color(run, pr, pg, pb)
            add_hr(p)

        def add_body(text, bold=False, indent=False):
            p = doc.add_paragraph()
            if indent:
                p.paragraph_format.left_indent = Inches(0.2)
            run = p.add_run(text)
            run.bold = bold
            run.font.size = Pt(9.5)

        # ── Summary ─────────────────────────────────────────────────────────
        summary = content_json.get("professional_summary", "")
        if summary:
            add_section("Professional Summary")
            add_body(summary)

        # ── Skills ──────────────────────────────────────────────────────────
        sk = content_json.get("skills", {})
        labels_map = {
            "programming": "Programming", "frameworks": "Frameworks",
            "databases": "Databases", "analytics": "Data & Analytics",
            "tools": "Tools", "other": "Other",
        }
        skill_lines = []
        for key, label in labels_map.items():
            vals = [s for s in sk.get(key, []) if s]
            if vals:
                skill_lines.append((label, ", ".join(vals)))
        if skill_lines:
            add_section("Skills")
            for label, val in skill_lines:
                p = doc.add_paragraph()
                r1 = p.add_run(f"{label}: ")
                r1.bold = True
                r1.font.size = Pt(9.5)
                r2 = p.add_run(val)
                r2.font.size = Pt(9.5)

        # ── Education ───────────────────────────────────────────────────────
        education = content_json.get("education", [])
        if education:
            add_section("Education")
            for edu in education:
                deg   = edu.get("degree","")
                field = edu.get("field","")
                inst  = edu.get("institution","")
                yr    = edu.get("year","")
                cgpa  = f" | CGPA: {edu['cgpa']}" if edu.get("cgpa") else ""
                p = doc.add_paragraph()
                r = p.add_run(f"{deg}{', '+field if field else ''}")
                r.bold = True; r.font.size = Pt(10)
                add_body(f"{inst}  {yr}{cgpa}")

        # ── Experience ──────────────────────────────────────────────────────
        experience = content_json.get("experience", [])
        if experience:
            add_section("Experience")
            for exp in experience:
                title   = exp.get("title","")
                company = exp.get("company","")
                dur     = exp.get("duration","")
                if title or company:
                    p = doc.add_paragraph()
                    r = p.add_run(f"{title} — {company}")
                    r.bold = True; r.font.size = Pt(10)
                if dur:
                    add_body(dur)
                for resp in (exp.get("responsibilities") or []):
                    if resp:
                        add_body(f"• {resp}", indent=True)

        # ── Projects ────────────────────────────────────────────────────────
        projects = content_json.get("projects", [])
        if projects:
            add_section("Projects")
            for proj in projects:
                name = proj.get("name","")
                tech = proj.get("technologies","")
                bullets = proj.get("bullets", [])
                desc = proj.get("description","")
                p = doc.add_paragraph()
                r = p.add_run(name)
                r.bold = True; r.font.size = Pt(10)
                if tech:
                    add_body(f"Technologies: {tech}")
                if desc and not bullets:
                    add_body(f"• {desc}", indent=True)
                for b in (bullets or []):
                    if b:
                        add_body(f"• {b}", indent=True)

        # ── Certifications ──────────────────────────────────────────────────
        certs = content_json.get("certifications", [])
        if certs:
            add_section("Certifications")
            for cert in certs:
                if isinstance(cert, dict):
                    add_body(f"• {cert.get('name','')} — {cert.get('org','')} ({cert.get('year','')})", indent=True)
                else:
                    add_body(f"• {cert}", indent=True)

        # ── Achievements ─────────────────────────────────────────────────────
        achievements = content_json.get("achievements", [])
        if achievements:
            add_section("Achievements")
            for ach in achievements:
                if isinstance(ach, dict):
                    add_body(f"• {ach.get('title','')}: {ach.get('description','')}", indent=True)
                else:
                    add_body(f"• {ach}", indent=True)

        doc.save(output_path)
        return output_path

    except Exception as exc:
        logger.error(f"DOCX render error: {exc}")
        return None


# ── SECTION REGENERATOR ───────────────────────────────────────────────────────

def regenerate_section(content_json, section_name, user_id,
                       company_name, job_role, extra_context=""):
    """
    Regenerate a single section of an existing resume using Qwen.
    Returns updated content for that section only.
    """
    from services.qwen_service import call_qwen, parse_qwen_json

    current = content_json.get(section_name, "")
    current_str = json.dumps(current) if not isinstance(current, str) else current

    prompt = (
        f"You are a professional resume writer.\n\n"
        f"Improve the following '{section_name}' section of a resume.\n"
        f"Target: {job_role} at {company_name}.\n"
        f"Extra context: {extra_context}\n\n"
        f"Current content:\n{current_str[:1000]}\n\n"
        f"Rules:\n"
        f"- Keep information truthful\n"
        f"- Do not invent data\n"
        f"- Use professional, ATS-friendly language\n"
        f"- Return ONLY the improved content in the same JSON type (string if string, array if array)\n"
        f"- No explanation, no markdown outside JSON"
    )

    raw = call_qwen(prompt, max_tokens=800, retries=1, temperature=0.4)
    if not raw:
        return current

    # For string fields (summary)
    if isinstance(current, str):
        stripped = raw.strip().strip('"').strip("'")
        return stripped if len(stripped) > 10 else current

    # For list/dict fields
    parsed = parse_qwen_json(raw)
    if parsed is None:
        from services.qwen_service import parse_qwen_json_array
        parsed = parse_qwen_json_array(raw)
    return parsed if parsed else current
