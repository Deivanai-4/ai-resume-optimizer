from services.resume_generation_service import render_pdf_bytes, render_docx_bytes

content = {
    'candidate': {'name': 'Test User', 'email': 'test@example.com', 'phone': '+91-9999999999', 'location': 'Chennai, India', 'linkedin': '', 'github': '', 'portfolio': ''},
    'target': {'company': 'Google', 'job_role': 'Software Engineer'},
    'professional_summary': 'Experienced developer with strong Python skills.',
    'skills': {'programming': ['Python', 'JavaScript'], 'frameworks': ['Flask', 'React'], 'databases': ['MySQL'], 'analytics': [], 'tools': ['Git'], 'other': []},
    'education': [{'degree': 'B.E. Computer Science', 'institution': 'MIT', 'year': '2020-2024', 'cgpa': '8.5', 'field': 'CS'}],
    'experience': [],
    'projects': [{'name': 'AI Resume', 'technologies': 'Python, Flask', 'description': 'Built AI resume builder', 'bullets': ['Developed AI generation', 'Deployed on Render'], 'github': ''}],
    'certifications': ['AWS Cloud Practitioner'],
    'achievements': ['Winner of Hackathon 2024'],
    'ats': {'score': 75, 'matched_keywords': ['Python'], 'missing_keywords': ['Kubernetes'], 'partial_keywords': []}
}

# Test all templates
for tpl in ['classic', 'modern', 'minimal', 'classic_ats', 'modern_pro', 'prestige_red']:
    pdf = render_pdf_bytes(content, tpl)
    status = f'OK - {len(pdf)} bytes' if pdf else 'FAILED'
    print(f'PDF ({tpl}): {status}')

# Test minimal/incomplete profile
min_content = {
    'candidate': {'name': 'Minimal User', 'email': 'min@test.com'},
    'skills': {},
    'education': [],
    'experience': [],
    'projects': [],
    'certifications': [],
    'achievements': []
}
pdf2 = render_pdf_bytes(min_content, 'classic')
status2 = f'OK - {len(pdf2)} bytes' if pdf2 else 'FAILED'
print(f'PDF (minimal/incomplete content): {status2}')

# Test missing optional fields
no_name = {'candidate': {}, 'skills': {'programming': ['Python']}, 'education': [], 'experience': [], 'projects': [], 'certifications': [], 'achievements': []}
pdf3 = render_pdf_bytes(no_name, 'classic')
status3 = f'OK - {len(pdf3)} bytes' if pdf3 else 'FAILED'
print(f'PDF (missing name/email): {status3}')

# Test DOCX
docx = render_docx_bytes(content, 'classic')
status_d = f'OK - {len(docx)} bytes' if docx else 'FAILED'
print(f'DOCX (classic): {status_d}')

docx2 = render_docx_bytes(min_content, 'modern')
status_d2 = f'OK - {len(docx2)} bytes' if docx2 else 'FAILED'
print(f'DOCX (minimal content): {status_d2}')

print('All tests complete.')
