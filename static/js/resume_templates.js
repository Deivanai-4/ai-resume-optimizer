/**
 * AI Career Intelligence Platform — Resume Template Registry
 * ===========================================================
 * 100 distinct resume template configurations.
 *
 * Layout families (structural, not just color):
 *   single_col       — Classic single-column
 *   colored_header   — Full-width colored banner header
 *   left_sidebar     — Left sidebar + right main content
 *   right_sidebar    — Right sidebar variant
 *   two_col_skills   — Two-column with skills/contact left, content right
 *   top_banner       — Thin top accent band, rest white
 *   timeline         — Left-line timeline for experience
 *   minimal_line     — Ultra-minimal, border-top section heads
 *   academic         — Education-first, publication-style
 *   compact          — Tightly spaced, two-column skills grid
 *
 * Each template object:
 *   id            {string}  Unique backend key stored in DB
 *   name          {string}  Display name
 *   category      {string}  Filter category
 *   layout        {string}  Layout family key
 *   accent        {string}  Primary accent hex color
 *   accent2       {string}  Secondary accent hex color
 *   bg            {string}  Page background color
 *   sidebar_bg    {string}  Sidebar background (sidebar layouts)
 *   font          {string}  Body font stack
 *   heading_font  {string}  Optional heading font stack
 *   heading_style {string}  'border-bottom' | 'left-bar' | 'uppercase-only' | 'bg-pill' | 'inline' | 'dotted'
 *   font_size     {number}  Base font size (pt)
 *   name_size     {number}  Candidate name font size (pt)
 *   spacing       {string}  'compact' | 'normal' | 'spacious'
 *   ats           {boolean} ATS-friendly badge
 *   desc          {string}  Short description
 */
'use strict';

const RESUME_TEMPLATES = [

  // ═══════════════════════════════════════════════════════════════
  // LAYOUT: single_col — Classic single-column templates (1–22)
  // ═══════════════════════════════════════════════════════════════

  {
    id: 'classic_ats', name: 'Classic ATS', category: 'ATS Friendly', layout: 'single_col',
    accent: '#1E3A5F', accent2: '#2563EB', bg: '#fff', font: 'Georgia, serif',
    heading_style: 'border-bottom', font_size: 11, name_size: 24, spacing: 'normal', ats: true,
    desc: 'Traditional serif font, centered header, two solid underlines. Maximum parser compatibility.'
  },
  {
    id: 'classic_slate', name: 'Classic Slate', category: 'ATS Friendly', layout: 'single_col',
    accent: '#334155', accent2: '#475569', bg: '#fff', font: 'Georgia, serif',
    heading_style: 'border-bottom', font_size: 11, name_size: 23, spacing: 'normal', ats: true,
    desc: 'Slate-grey serif, clean underline headings. Timeless and universally readable.'
  },
  {
    id: 'classic_forest', name: 'Classic Forest', category: 'ATS Friendly', layout: 'single_col',
    accent: '#14532D', accent2: '#16A34A', bg: '#fff', font: 'Georgia, serif',
    heading_style: 'border-bottom', font_size: 11, name_size: 23, spacing: 'normal', ats: true,
    desc: 'Deep forest green accents on clean serif. Professional and distinct.'
  },
  {
    id: 'classic_maroon', name: 'Classic Maroon', category: 'ATS Friendly', layout: 'single_col',
    accent: '#7F1D1D', accent2: '#B91C1C', bg: '#fff', font: 'Georgia, serif',
    heading_style: 'border-bottom', font_size: 11, name_size: 23, spacing: 'normal', ats: true,
    desc: 'Deep maroon serif. Executive authority with clean layout.'
  },
  {
    id: 'classic_black', name: 'Black & White', category: 'ATS Friendly', layout: 'single_col',
    accent: '#000000', accent2: '#222222', bg: '#fff', font: 'Arial, Helvetica, sans-serif',
    heading_style: 'border-bottom', font_size: 11, name_size: 24, spacing: 'normal', ats: true,
    desc: 'Pure monochrome sans-serif. Clean, safe, and universally ATS-compatible.'
  },
  {
    id: 'sans_navy', name: 'Sans Navy', category: 'Professional', layout: 'single_col',
    accent: '#1E40AF', accent2: '#3B82F6', bg: '#fff', font: 'Arial, Helvetica, sans-serif',
    heading_style: 'border-bottom', font_size: 11, name_size: 23, spacing: 'normal', ats: true,
    desc: 'Navy sans-serif, clean section borders. Modern professional look.'
  },
  {
    id: 'sans_teal', name: 'Sans Teal', category: 'Modern Corporate', layout: 'single_col',
    accent: '#0F766E', accent2: '#14B8A6', bg: '#fff', font: 'Arial, sans-serif',
    heading_style: 'left-bar', font_size: 11, name_size: 22, spacing: 'normal', ats: true,
    desc: 'Teal left-bar section headings. Fresh and corporate.'
  },
  {
    id: 'sans_violet', name: 'Sans Violet', category: 'Modern Corporate', layout: 'single_col',
    accent: '#6D28D9', accent2: '#8B5CF6', bg: '#fff', font: 'Inter, Arial, sans-serif',
    heading_style: 'left-bar', font_size: 11, name_size: 22, spacing: 'normal', ats: true,
    desc: 'Violet left-bar section headings. Confident and modern.'
  },
  {
    id: 'sans_rose', name: 'Soft Rose', category: 'Creative', layout: 'single_col',
    accent: '#9F1239', accent2: '#E11D48', bg: '#fff', font: 'Georgia, serif',
    heading_style: 'bg-pill', font_size: 11, name_size: 22, spacing: 'normal', ats: false,
    desc: 'Rose-accented pill-style section headings. Creative yet readable.'
  },
  {
    id: 'executive_black', name: 'Executive Black', category: 'Executive', layout: 'single_col',
    accent: '#111827', accent2: '#374151', bg: '#fff', font: 'Georgia, "Times New Roman", serif',
    heading_style: 'uppercase-only', font_size: 12, name_size: 26, spacing: 'spacious', ats: true,
    desc: 'Large name, generous spacing, uppercase headings. Senior-level presence.'
  },
  {
    id: 'executive_navy', name: 'Executive Navy', category: 'Executive', layout: 'single_col',
    accent: '#1e3a5f', accent2: '#2563eb', bg: '#fff', font: '"Palatino Linotype", Palatino, serif',
    heading_style: 'uppercase-only', font_size: 12, name_size: 26, spacing: 'spacious', ats: true,
    desc: 'Navy serif executive style with generous whitespace.'
  },
  {
    id: 'executive_gold', name: 'Executive Gold', category: 'Executive', layout: 'single_col',
    accent: '#92400E', accent2: '#D97706', bg: '#fff', font: '"Palatino Linotype", serif',
    heading_style: 'border-bottom', font_size: 11.5, name_size: 25, spacing: 'spacious', ats: true,
    desc: 'Warm gold-amber serif. Prestigious and memorable.'
  },
  {
    id: 'student_blue', name: 'Student Blue', category: 'Student / Fresher', layout: 'single_col',
    accent: '#1D4ED8', accent2: '#3B82F6', bg: '#fff', font: 'Arial, sans-serif',
    heading_style: 'left-bar', font_size: 11, name_size: 21, spacing: 'compact', ats: true,
    desc: 'Compact, education-friendly layout with blue accents. Great for freshers.'
  },
  {
    id: 'student_teal', name: 'Student Teal', category: 'Student / Fresher', layout: 'single_col',
    accent: '#0D9488', accent2: '#14B8A6', bg: '#fff', font: 'Arial, sans-serif',
    heading_style: 'left-bar', font_size: 11, name_size: 21, spacing: 'compact', ats: true,
    desc: 'Teal compact layout optimized for freshers and interns.'
  },
  {
    id: 'student_green', name: 'Student Green', category: 'Student / Fresher', layout: 'single_col',
    accent: '#166534', accent2: '#22C55E', bg: '#fff', font: 'Arial, sans-serif',
    heading_style: 'border-bottom', font_size: 11, name_size: 21, spacing: 'compact', ats: true,
    desc: 'Green compact layout for campus placements and internships.'
  },
  {
    id: 'dotted_purple', name: 'Dotted Purple', category: 'Creative', layout: 'single_col',
    accent: '#7C3AED', accent2: '#A855F7', bg: '#fff', font: 'Inter, Arial, sans-serif',
    heading_style: 'dotted', font_size: 11, name_size: 22, spacing: 'normal', ats: false,
    desc: 'Dotted section dividers with purple accents. Creative and stylish.'
  },
  {
    id: 'dotted_coral', name: 'Dotted Coral', category: 'Creative', layout: 'single_col',
    accent: '#BE185D', accent2: '#EC4899', bg: '#fff', font: 'Inter, Arial, sans-serif',
    heading_style: 'dotted', font_size: 11, name_size: 22, spacing: 'normal', ats: false,
    desc: 'Coral dotted dividers. Bold and visually engaging.'
  },
  {
    id: 'data_analyst_blue', name: 'Data Analyst', category: 'Data Analyst', layout: 'single_col',
    accent: '#075985', accent2: '#0EA5E9', bg: '#fff', font: 'Arial, sans-serif',
    heading_style: 'left-bar', font_size: 11, name_size: 22, spacing: 'normal', ats: true,
    desc: 'Structured layout emphasizing analytics skills. Data-focused hierarchy.'
  },
  {
    id: 'data_dark_blue', name: 'Analytics Pro', category: 'Data Analyst', layout: 'single_col',
    accent: '#1e3a5f', accent2: '#0ea5e9', bg: '#fff', font: 'Arial, sans-serif',
    heading_style: 'bg-pill', font_size: 11, name_size: 22, spacing: 'normal', ats: true,
    desc: 'Dark blue pill headings for data analyst and BI roles.'
  },
  {
    id: 'inline_orange', name: 'Inline Orange', category: 'Modern Corporate', layout: 'single_col',
    accent: '#C2410C', accent2: '#EA580C', bg: '#fff', font: 'Inter, Arial, sans-serif',
    heading_style: 'inline', font_size: 11, name_size: 22, spacing: 'normal', ats: true,
    desc: 'Warm orange inline headings. Vibrant and professional.'
  },
  {
    id: 'inline_slate', name: 'Inline Slate', category: 'Professional', layout: 'single_col',
    accent: '#475569', accent2: '#64748B', bg: '#fff', font: 'Inter, Arial, sans-serif',
    heading_style: 'inline', font_size: 11, name_size: 22, spacing: 'normal', ats: true,
    desc: 'Slate inline section headers with clean spacing.'
  },
  {
    id: 'classic_indigo', name: 'Classic Indigo', category: 'Professional', layout: 'single_col',
    accent: '#3730A3', accent2: '#4F46E5', bg: '#fff', font: 'Georgia, serif',
    heading_style: 'border-bottom', font_size: 11, name_size: 23, spacing: 'normal', ats: true,
    desc: 'Deep indigo serif. Bold headings, traditional structure.'
  },
  {
    id: 'single_olive', name: 'Olive Classic', category: 'Professional', layout: 'single_col',
    accent: '#365314', accent2: '#4D7C0F', bg: '#fff', font: 'Georgia, serif',
    heading_style: 'border-bottom', font_size: 11, name_size: 22, spacing: 'normal', ats: true,
    desc: 'Olive-green classical. Unique earthy professional tone.'
  },

  // ═══════════════════════════════════════════════════════════════
  // LAYOUT: colored_header — Full-width colored banner (23–34)
  // ═══════════════════════════════════════════════════════════════

  {
    id: 'modern_pro', name: 'Modern Professional', category: 'Modern Corporate', layout: 'colored_header',
    accent: '#4F46E5', accent2: '#7C3AED', bg: '#fff', font: 'Inter, Arial, sans-serif',
    heading_style: 'border-bottom', font_size: 11, name_size: 24, spacing: 'normal', ats: true,
    desc: 'Indigo banner header, badge-style skills, left-bordered summary block.'
  },
  {
    id: 'header_teal', name: 'Teal Corporate', category: 'Modern Corporate', layout: 'colored_header',
    accent: '#0F766E', accent2: '#14B8A6', bg: '#fff', font: 'Inter, Arial, sans-serif',
    heading_style: 'border-bottom', font_size: 11, name_size: 23, spacing: 'normal', ats: true,
    desc: 'Teal full-width header. Modern corporate with warm personality.'
  },
  {
    id: 'header_navy', name: 'Navy Prestige', category: 'Professional', layout: 'colored_header',
    accent: '#1E3A5F', accent2: '#2563EB', bg: '#fff', font: 'Arial, Helvetica, sans-serif',
    heading_style: 'border-bottom', font_size: 11, name_size: 23, spacing: 'normal', ats: true,
    desc: 'Classic navy banner header. Authority and trust.'
  },
  {
    id: 'header_charcoal', name: 'Charcoal Pro', category: 'Executive', layout: 'colored_header',
    accent: '#1C1917', accent2: '#44403C', bg: '#fff', font: 'Arial, sans-serif',
    heading_style: 'border-bottom', font_size: 11, name_size: 24, spacing: 'normal', ats: true,
    desc: 'Rich charcoal header. Dark, sophisticated executive look.'
  },
  {
    id: 'header_forest', name: 'Forest Modern', category: 'Modern Corporate', layout: 'colored_header',
    accent: '#14532D', accent2: '#16A34A', bg: '#fff', font: 'Inter, Arial, sans-serif',
    heading_style: 'left-bar', font_size: 11, name_size: 22, spacing: 'normal', ats: true,
    desc: 'Forest green banner with left-bar headings. Fresh and distinctive.'
  },
  {
    id: 'header_rose', name: 'Rose Corporate', category: 'Creative', layout: 'colored_header',
    accent: '#9F1239', accent2: '#F43F5E', bg: '#fff', font: 'Inter, Arial, sans-serif',
    heading_style: 'border-bottom', font_size: 11, name_size: 22, spacing: 'normal', ats: false,
    desc: 'Bold rose-red header. Creative and confident.'
  },
  {
    id: 'header_violet', name: 'Violet Modern', category: 'Modern Corporate', layout: 'colored_header',
    accent: '#5B21B6', accent2: '#8B5CF6', bg: '#fff', font: 'Inter, Arial, sans-serif',
    heading_style: 'left-bar', font_size: 11, name_size: 22, spacing: 'normal', ats: true,
    desc: 'Deep violet header with gradient. Premium modern style.'
  },
  {
    id: 'header_sky', name: 'Sky Blue Modern', category: 'Modern Corporate', layout: 'colored_header',
    accent: '#0369A1', accent2: '#0EA5E9', bg: '#fff', font: 'Arial, sans-serif',
    heading_style: 'border-bottom', font_size: 11, name_size: 22, spacing: 'normal', ats: true,
    desc: 'Sky blue banner. Light, approachable, and professional.'
  },
  {
    id: 'header_orange', name: 'Sunrise Orange', category: 'Creative', layout: 'colored_header',
    accent: '#9A3412', accent2: '#EA580C', bg: '#fff', font: 'Inter, Arial, sans-serif',
    heading_style: 'border-bottom', font_size: 11, name_size: 22, spacing: 'normal', ats: false,
    desc: 'Warm orange header. Energetic, creative, and distinctive.'
  },
  {
    id: 'header_slate_grad', name: 'Slate Gradient', category: 'Executive', layout: 'colored_header',
    accent: '#0F172A', accent2: '#334155', bg: '#fff', font: 'Arial, sans-serif',
    heading_style: 'left-bar', font_size: 11, name_size: 24, spacing: 'spacious', ats: true,
    desc: 'Deep slate gradient header. Senior executive presence.'
  },
  {
    id: 'header_purple_soft', name: 'Soft Purple', category: 'Student / Fresher', layout: 'colored_header',
    accent: '#7C3AED', accent2: '#A78BFA', bg: '#fff', font: 'Arial, sans-serif',
    heading_style: 'border-bottom', font_size: 11, name_size: 21, spacing: 'compact', ats: true,
    desc: 'Soft purple header. Approachable and fresh for campus placements.'
  },
  {
    id: 'header_crimson', name: 'Crimson Bold', category: 'Executive', layout: 'colored_header',
    accent: '#7F1D1D', accent2: '#DC2626', bg: '#fff', font: '"Palatino Linotype", serif',
    heading_style: 'border-bottom', font_size: 11.5, name_size: 25, spacing: 'spacious', ats: true,
    desc: 'Crimson serif banner. Bold executive authority.'
  },

  // ═══════════════════════════════════════════════════════════════
  // LAYOUT: left_sidebar — Left sidebar templates (35–48)
  // ═══════════════════════════════════════════════════════════════

  {
    id: 'profile_photo', name: 'Profile Sidebar', category: 'Two-Column / Sidebar', layout: 'left_sidebar',
    accent: '#0F766E', accent2: '#14B8A6', bg: '#fff', sidebar_bg: '#F0FDF4',
    font: 'Roboto, Arial, sans-serif', heading_style: 'border-bottom',
    font_size: 11, name_size: 22, spacing: 'normal', ats: false,
    desc: 'Green sidebar with avatar initials, skills, and contact. Content on right.'
  },
  {
    id: 'sidebar_navy', name: 'Navy Sidebar', category: 'Two-Column / Sidebar', layout: 'left_sidebar',
    accent: '#1E3A5F', accent2: '#3B82F6', bg: '#fff', sidebar_bg: '#EFF6FF',
    font: 'Arial, sans-serif', heading_style: 'border-bottom',
    font_size: 11, name_size: 22, spacing: 'normal', ats: false,
    desc: 'Navy sidebar. Skills and contact on left, experience and projects on right.'
  },
  {
    id: 'sidebar_purple', name: 'Purple Sidebar', category: 'Two-Column / Sidebar', layout: 'left_sidebar',
    accent: '#5B21B6', accent2: '#8B5CF6', bg: '#fff', sidebar_bg: '#F5F3FF',
    font: 'Inter, Arial, sans-serif', heading_style: 'border-bottom',
    font_size: 11, name_size: 22, spacing: 'normal', ats: false,
    desc: 'Purple sidebar with skill pills and contact info.'
  },
  {
    id: 'sidebar_dark', name: 'Dark Sidebar', category: 'Software Developer', layout: 'left_sidebar',
    accent: '#818CF8', accent2: '#A5B4FC', bg: '#fff', sidebar_bg: '#0F172A',
    font: 'Inter, Arial, sans-serif', heading_style: 'border-bottom',
    font_size: 11, name_size: 22, spacing: 'normal', ats: false,
    desc: 'Dark sidebar with white text and code-style skill tags. Dev-focused.'
  },
  {
    id: 'sidebar_rose', name: 'Rose Sidebar', category: 'Creative', layout: 'left_sidebar',
    accent: '#BE185D', accent2: '#F472B6', bg: '#fff', sidebar_bg: '#FFF1F2',
    font: 'Inter, Arial, sans-serif', heading_style: 'border-bottom',
    font_size: 11, name_size: 22, spacing: 'normal', ats: false,
    desc: 'Soft rose sidebar for creative professionals.'
  },
  {
    id: 'sidebar_charcoal', name: 'Charcoal Sidebar', category: 'Executive', layout: 'left_sidebar',
    accent: '#374151', accent2: '#6B7280', bg: '#fff', sidebar_bg: '#F9FAFB',
    font: 'Arial, sans-serif', heading_style: 'left-bar',
    font_size: 11, name_size: 22, spacing: 'spacious', ats: true,
    desc: 'Subtle charcoal sidebar. Sleek and professional.'
  },
  {
    id: 'sidebar_amber', name: 'Amber Sidebar', category: 'Creative', layout: 'left_sidebar',
    accent: '#92400E', accent2: '#F59E0B', bg: '#fff', sidebar_bg: '#FFFBEB',
    font: 'Arial, sans-serif', heading_style: 'border-bottom',
    font_size: 11, name_size: 22, spacing: 'normal', ats: false,
    desc: 'Warm amber sidebar. Distinctive and inviting.'
  },
  {
    id: 'sidebar_slate_dark', name: 'Midnight Sidebar', category: 'Software Developer', layout: 'left_sidebar',
    accent: '#38BDF8', accent2: '#7DD3FC', bg: '#fff', sidebar_bg: '#1E293B',
    font: 'Inter, Arial, sans-serif', heading_style: 'border-bottom',
    font_size: 11, name_size: 21, spacing: 'normal', ats: false,
    desc: 'Midnight blue sidebar with sky-blue accents. Modern developer look.'
  },
  {
    id: 'sidebar_forest_dark', name: 'Forest Dark Sidebar', category: 'Software Developer', layout: 'left_sidebar',
    accent: '#86EFAC', accent2: '#4ADE80', bg: '#fff', sidebar_bg: '#14532D',
    font: 'Inter, Arial, sans-serif', heading_style: 'border-bottom',
    font_size: 11, name_size: 21, spacing: 'normal', ats: false,
    desc: 'Deep forest sidebar with light green accents. Bold developer style.'
  },
  {
    id: 'sidebar_indigo_light', name: 'Indigo Light Sidebar', category: 'Modern Corporate', layout: 'left_sidebar',
    accent: '#4338CA', accent2: '#6366F1', bg: '#fff', sidebar_bg: '#EEF2FF',
    font: 'Inter, Arial, sans-serif', heading_style: 'left-bar',
    font_size: 11, name_size: 22, spacing: 'normal', ats: true,
    desc: 'Light indigo sidebar. Modern, ATS-friendly layout.'
  },
  {
    id: 'sidebar_student', name: 'Student Sidebar', category: 'Student / Fresher', layout: 'left_sidebar',
    accent: '#1D4ED8', accent2: '#60A5FA', bg: '#fff', sidebar_bg: '#DBEAFE',
    font: 'Arial, sans-serif', heading_style: 'border-bottom',
    font_size: 11, name_size: 20, spacing: 'compact', ats: false,
    desc: 'Light blue sidebar for students and entry-level candidates.'
  },
  {
    id: 'sidebar_academic', name: 'Academic Sidebar', category: 'Academic', layout: 'left_sidebar',
    accent: '#1E3A5F', accent2: '#2563EB', bg: '#fff', sidebar_bg: '#F8FAFC',
    font: 'Georgia, serif', heading_style: 'uppercase-only',
    font_size: 11, name_size: 22, spacing: 'spacious', ats: true,
    desc: 'Sidebar with serif font for academic and research CVs.'
  },
  {
    id: 'sidebar_data', name: 'Data Sidebar', category: 'Data Analyst', layout: 'left_sidebar',
    accent: '#075985', accent2: '#0284C7', bg: '#fff', sidebar_bg: '#F0F9FF',
    font: 'Arial, sans-serif', heading_style: 'left-bar',
    font_size: 11, name_size: 22, spacing: 'normal', ats: true,
    desc: 'Blue sidebar with skill bars for data analyst roles.'
  },
  {
    id: 'sidebar_minimal', name: 'Minimal Sidebar', category: 'Minimalist', layout: 'left_sidebar',
    accent: '#6B7280', accent2: '#9CA3AF', bg: '#fff', sidebar_bg: '#F9FAFB',
    font: 'Arial, Helvetica, sans-serif', heading_style: 'uppercase-only',
    font_size: 11, name_size: 21, spacing: 'normal', ats: true,
    desc: 'Greyscale sidebar. Ultra-clean and parser-safe.'
  },

  // ═══════════════════════════════════════════════════════════════
  // LAYOUT: top_banner — Thin top band (49–58)
  // ═══════════════════════════════════════════════════════════════

  {
    id: 'banner_indigo', name: 'Indigo Banner', category: 'Modern Corporate', layout: 'top_banner',
    accent: '#4F46E5', accent2: '#818CF8', bg: '#fff', font: 'Inter, Arial, sans-serif',
    heading_style: 'left-bar', font_size: 11, name_size: 22, spacing: 'normal', ats: true,
    desc: 'Thin indigo top strip, name and contact below. Clean modern look.'
  },
  {
    id: 'banner_teal', name: 'Teal Banner', category: 'Modern Corporate', layout: 'top_banner',
    accent: '#0F766E', accent2: '#14B8A6', bg: '#fff', font: 'Arial, sans-serif',
    heading_style: 'left-bar', font_size: 11, name_size: 22, spacing: 'normal', ats: true,
    desc: 'Teal top strip with clean body layout.'
  },
  {
    id: 'banner_black', name: 'Bold Black Banner', category: 'Minimalist', layout: 'top_banner',
    accent: '#111827', accent2: '#374151', bg: '#fff', font: 'Arial, Helvetica, sans-serif',
    heading_style: 'uppercase-only', font_size: 11, name_size: 22, spacing: 'normal', ats: true,
    desc: 'Black banner strip. Bold, minimal, maximally ATS-safe.'
  },
  {
    id: 'banner_rose', name: 'Rose Banner', category: 'Creative', layout: 'top_banner',
    accent: '#9F1239', accent2: '#F43F5E', bg: '#fff', font: 'Inter, Arial, sans-serif',
    heading_style: 'left-bar', font_size: 11, name_size: 22, spacing: 'normal', ats: false,
    desc: 'Rose banner strip. Creative and warm.'
  },
  {
    id: 'banner_violet', name: 'Violet Banner', category: 'Creative', layout: 'top_banner',
    accent: '#7C3AED', accent2: '#A78BFA', bg: '#fff', font: 'Inter, Arial, sans-serif',
    heading_style: 'left-bar', font_size: 11, name_size: 22, spacing: 'normal', ats: false,
    desc: 'Purple banner with inline name and bold skills.'
  },
  {
    id: 'banner_sky', name: 'Sky Banner', category: 'Student / Fresher', layout: 'top_banner',
    accent: '#0284C7', accent2: '#38BDF8', bg: '#fff', font: 'Arial, sans-serif',
    heading_style: 'border-bottom', font_size: 11, name_size: 21, spacing: 'compact', ats: true,
    desc: 'Light sky-blue banner. Entry-level and fresher friendly.'
  },
  {
    id: 'banner_amber', name: 'Amber Banner', category: 'Creative', layout: 'top_banner',
    accent: '#D97706', accent2: '#FBBF24', bg: '#fff', font: 'Inter, Arial, sans-serif',
    heading_style: 'left-bar', font_size: 11, name_size: 22, spacing: 'normal', ats: false,
    desc: 'Warm amber banner. Warm and welcoming creative style.'
  },
  {
    id: 'banner_forest', name: 'Forest Banner', category: 'Professional', layout: 'top_banner',
    accent: '#14532D', accent2: '#22C55E', bg: '#fff', font: 'Arial, sans-serif',
    heading_style: 'border-bottom', font_size: 11, name_size: 22, spacing: 'normal', ats: true,
    desc: 'Forest green banner. Distinctive eco-friendly aesthetic.'
  },
  {
    id: 'banner_slate', name: 'Slate Banner', category: 'Professional', layout: 'top_banner',
    accent: '#0F172A', accent2: '#475569', bg: '#fff', font: 'Arial, sans-serif',
    heading_style: 'border-bottom', font_size: 11, name_size: 22, spacing: 'normal', ats: true,
    desc: 'Dark slate banner. Strong and professional.'
  },
  {
    id: 'banner_crimson', name: 'Crimson Banner', category: 'Executive', layout: 'top_banner',
    accent: '#7F1D1D', accent2: '#B91C1C', bg: '#fff', font: 'Georgia, serif',
    heading_style: 'border-bottom', font_size: 11, name_size: 23, spacing: 'normal', ats: true,
    desc: 'Crimson banner with serif body. Senior-level presence.'
  },

  // ═══════════════════════════════════════════════════════════════
  // LAYOUT: minimal_line — Ultra-minimal (59–68)
  // ═══════════════════════════════════════════════════════════════

  {
    id: 'minimal_ats', name: 'Minimal ATS', category: 'Minimalist', layout: 'minimal_line',
    accent: '#374151', accent2: '#6B7280', bg: '#fff', font: 'Arial, Helvetica, sans-serif',
    heading_style: 'uppercase-only', font_size: 11, name_size: 22, spacing: 'normal', ats: true,
    desc: 'Ultra-clean whitespace, top-border headings. Pure ATS compatibility.'
  },
  {
    id: 'minimal_black', name: 'Minimal Black', category: 'Minimalist', layout: 'minimal_line',
    accent: '#000000', accent2: '#333333', bg: '#fff', font: 'Arial, Helvetica, sans-serif',
    heading_style: 'uppercase-only', font_size: 11, name_size: 22, spacing: 'normal', ats: true,
    desc: 'Pure black and white. The safest possible ATS layout.'
  },
  {
    id: 'minimal_navy', name: 'Minimal Navy', category: 'Minimalist', layout: 'minimal_line',
    accent: '#1E3A5F', accent2: '#475569', bg: '#fff', font: 'Arial, sans-serif',
    heading_style: 'uppercase-only', font_size: 11, name_size: 22, spacing: 'normal', ats: true,
    desc: 'Minimal layout with navy accent for section names only.'
  },
  {
    id: 'minimal_green', name: 'Minimal Green', category: 'Minimalist', layout: 'minimal_line',
    accent: '#166534', accent2: '#4B5563', bg: '#fff', font: 'Arial, sans-serif',
    heading_style: 'uppercase-only', font_size: 11, name_size: 22, spacing: 'normal', ats: true,
    desc: 'Minimal green accents. Clean and unobtrusive.'
  },
  {
    id: 'minimal_spacious', name: 'Minimal Spacious', category: 'Minimalist', layout: 'minimal_line',
    accent: '#374151', accent2: '#9CA3AF', bg: '#fff', font: 'Arial, Helvetica, sans-serif',
    heading_style: 'uppercase-only', font_size: 11.5, name_size: 23, spacing: 'spacious', ats: true,
    desc: 'Generous whitespace, no visual noise. Executive-grade minimalism.'
  },
  {
    id: 'minimal_compact', name: 'Compact Minimal', category: 'Minimalist', layout: 'minimal_line',
    accent: '#111827', accent2: '#374151', bg: '#fff', font: 'Arial, Helvetica, sans-serif',
    heading_style: 'uppercase-only', font_size: 10, name_size: 20, spacing: 'compact', ats: true,
    desc: 'Tight spacing, fit more content on one page. Minimal and dense.'
  },
  {
    id: 'minimal_sans_teal', name: 'Clean Teal', category: 'Minimalist', layout: 'minimal_line',
    accent: '#0F766E', accent2: '#64748B', bg: '#fff', font: 'Arial, sans-serif',
    heading_style: 'uppercase-only', font_size: 11, name_size: 22, spacing: 'normal', ats: true,
    desc: 'Minimal with teal section headings. Calm and professional.'
  },
  {
    id: 'minimal_serif', name: 'Minimal Serif', category: 'Minimalist', layout: 'minimal_line',
    accent: '#1E293B', accent2: '#475569', bg: '#fff', font: 'Georgia, serif',
    heading_style: 'uppercase-only', font_size: 11, name_size: 22, spacing: 'normal', ats: true,
    desc: 'Minimal with serif font. Traditional meets restrained.'
  },
  {
    id: 'minimal_student', name: 'Student Minimal', category: 'Student / Fresher', layout: 'minimal_line',
    accent: '#1D4ED8', accent2: '#64748B', bg: '#fff', font: 'Arial, sans-serif',
    heading_style: 'uppercase-only', font_size: 10.5, name_size: 21, spacing: 'compact', ats: true,
    desc: 'Minimal compact layout tailored for fresh graduates and interns.'
  },
  {
    id: 'minimal_data', name: 'Data Minimal', category: 'Data Analyst', layout: 'minimal_line',
    accent: '#075985', accent2: '#64748B', bg: '#fff', font: 'Arial, sans-serif',
    heading_style: 'uppercase-only', font_size: 11, name_size: 22, spacing: 'normal', ats: true,
    desc: 'Clean data-focused minimal layout. Analytical precision.'
  },

  // ═══════════════════════════════════════════════════════════════
  // LAYOUT: tech_dev — Developer / Technical (69–78)
  // ═══════════════════════════════════════════════════════════════

  {
    id: 'tech_dev', name: 'Technical / Dev', category: 'Software Developer', layout: 'tech_dev',
    accent: '#818CF8', accent2: '#C4B5FD', bg: '#0F172A', font: "'Fira Code', Consolas, monospace",
    heading_style: 'inline', font_size: 10.5, name_size: 22, spacing: 'normal', ats: false,
    desc: 'Dark midnight header, code-style skill tags, indigo accents. For developers.'
  },
  {
    id: 'tech_green', name: 'Terminal Green', category: 'Software Developer', layout: 'tech_dev',
    accent: '#22C55E', accent2: '#86EFAC', bg: '#0A0F0D', font: "'Fira Code', Consolas, monospace",
    heading_style: 'inline', font_size: 10.5, name_size: 22, spacing: 'normal', ats: false,
    desc: 'Green-on-dark terminal aesthetic. Iconic hacker/dev style.'
  },
  {
    id: 'tech_cyan', name: 'Cyber Cyan', category: 'Software Developer', layout: 'tech_dev',
    accent: '#06B6D4', accent2: '#67E8F9', bg: '#0C1A22', font: "'Fira Code', Consolas, monospace",
    heading_style: 'inline', font_size: 10.5, name_size: 22, spacing: 'normal', ats: false,
    desc: 'Cyan cyberpunk style on deep dark background. Striking developer résumé.'
  },
  {
    id: 'tech_orange', name: 'Hacker Orange', category: 'Software Developer', layout: 'tech_dev',
    accent: '#FB923C', accent2: '#FDBA74', bg: '#1C0A00', font: "'Fira Code', Consolas, monospace",
    heading_style: 'inline', font_size: 10.5, name_size: 22, spacing: 'normal', ats: false,
    desc: 'Orange-on-dark. Bold retro developer aesthetic.'
  },
  {
    id: 'tech_minimal', name: 'Dev Minimal', category: 'Software Developer', layout: 'tech_dev',
    accent: '#4F46E5', accent2: '#818CF8', bg: '#F8FAFC', font: "'Fira Code', Consolas, monospace",
    heading_style: 'border-bottom', font_size: 10.5, name_size: 21, spacing: 'normal', ats: true,
    desc: 'Light-background developer template with code font. ATS-safe tech style.'
  },
  {
    id: 'tech_rose', name: 'Dev Rose', category: 'Software Developer', layout: 'tech_dev',
    accent: '#F43F5E', accent2: '#FB7185', bg: '#18030A', font: "'Fira Code', Consolas, monospace",
    heading_style: 'inline', font_size: 10.5, name_size: 21, spacing: 'normal', ats: false,
    desc: 'Rose-on-dark for software developers with creative flair.'
  },
  {
    id: 'tech_gold', name: 'Dev Gold', category: 'Software Developer', layout: 'tech_dev',
    accent: '#FBBF24', accent2: '#FDE68A', bg: '#0F0A00', font: "'Fira Code', Consolas, monospace",
    heading_style: 'inline', font_size: 10.5, name_size: 22, spacing: 'normal', ats: false,
    desc: 'Gold-on-dark. Classic "dark theme IDE" inspired resume.'
  },
  {
    id: 'tech_violet', name: 'Dev Violet', category: 'Software Developer', layout: 'tech_dev',
    accent: '#A855F7', accent2: '#D8B4FE', bg: '#0D0820', font: "'Fira Code', Consolas, monospace",
    heading_style: 'inline', font_size: 10.5, name_size: 22, spacing: 'normal', ats: false,
    desc: 'Violet synthwave aesthetic. Vibrant and creative dev style.'
  },
  {
    id: 'tech_slate_light', name: 'Slate Dev', category: 'Software Developer', layout: 'tech_dev',
    accent: '#0F172A', accent2: '#475569', bg: '#F8FAFC', font: "'Fira Code', Consolas, monospace",
    heading_style: 'left-bar', font_size: 10.5, name_size: 21, spacing: 'normal', ats: true,
    desc: 'Light slate developer template. ATS-compatible with code aesthetics.'
  },
  {
    id: 'tech_teal_dark', name: 'Dev Teal Dark', category: 'Software Developer', layout: 'tech_dev',
    accent: '#2DD4BF', accent2: '#99F6E4', bg: '#042F2E', font: "'Fira Code', Consolas, monospace",
    heading_style: 'inline', font_size: 10.5, name_size: 22, spacing: 'normal', ats: false,
    desc: 'Teal-on-dark for full-stack and backend developers.'
  },

  // ═══════════════════════════════════════════════════════════════
  // LAYOUT: timeline — Timeline experience layout (79–83)
  // ═══════════════════════════════════════════════════════════════

  {
    id: 'timeline_navy', name: 'Timeline Navy', category: 'Timeline', layout: 'timeline',
    accent: '#1E3A5F', accent2: '#3B82F6', bg: '#fff', font: 'Arial, sans-serif',
    heading_style: 'border-bottom', font_size: 11, name_size: 22, spacing: 'normal', ats: true,
    desc: 'Left-line timeline for experience. Chronological flow with navy dots.'
  },
  {
    id: 'timeline_teal', name: 'Timeline Teal', category: 'Timeline', layout: 'timeline',
    accent: '#0F766E', accent2: '#14B8A6', bg: '#fff', font: 'Inter, Arial, sans-serif',
    heading_style: 'border-bottom', font_size: 11, name_size: 22, spacing: 'normal', ats: false,
    desc: 'Teal timeline dots and vertical line. Visual career progression.'
  },
  {
    id: 'timeline_violet', name: 'Timeline Violet', category: 'Timeline', layout: 'timeline',
    accent: '#6D28D9', accent2: '#8B5CF6', bg: '#fff', font: 'Inter, Arial, sans-serif',
    heading_style: 'left-bar', font_size: 11, name_size: 22, spacing: 'normal', ats: false,
    desc: 'Purple timeline. Creative and structured visual hierarchy.'
  },
  {
    id: 'timeline_rose', name: 'Timeline Rose', category: 'Timeline', layout: 'timeline',
    accent: '#9F1239', accent2: '#E11D48', bg: '#fff', font: 'Inter, Arial, sans-serif',
    heading_style: 'border-bottom', font_size: 11, name_size: 22, spacing: 'normal', ats: false,
    desc: 'Rose timeline. Bold visual career storytelling.'
  },
  {
    id: 'timeline_black', name: 'Timeline Minimal', category: 'Timeline', layout: 'timeline',
    accent: '#111827', accent2: '#374151', bg: '#fff', font: 'Arial, sans-serif',
    heading_style: 'uppercase-only', font_size: 11, name_size: 22, spacing: 'normal', ats: true,
    desc: 'Black minimal timeline. Structured chronology without visual overload.'
  },

  // ═══════════════════════════════════════════════════════════════
  // LAYOUT: academic — Education-first academic CV (84–89)
  // ═══════════════════════════════════════════════════════════════

  {
    id: 'academic_classic', name: 'Academic Classic', category: 'Academic', layout: 'academic',
    accent: '#1E3A5F', accent2: '#2563EB', bg: '#fff', font: 'Georgia, "Times New Roman", serif',
    heading_style: 'border-bottom', font_size: 11.5, name_size: 23, spacing: 'spacious', ats: true,
    desc: 'Education first, publications style. Serif font for academic CVs.'
  },
  {
    id: 'academic_modern', name: 'Academic Modern', category: 'Academic', layout: 'academic',
    accent: '#0F766E', accent2: '#14B8A6', bg: '#fff', font: 'Arial, sans-serif',
    heading_style: 'left-bar', font_size: 11, name_size: 22, spacing: 'spacious', ats: true,
    desc: 'Modern academic layout. Education and research in a clean sans layout.'
  },
  {
    id: 'academic_navy_serif', name: 'Academic Navy', category: 'Academic', layout: 'academic',
    accent: '#1C3557', accent2: '#2563EB', bg: '#fff', font: '"Palatino Linotype", Palatino, serif',
    heading_style: 'uppercase-only', font_size: 12, name_size: 24, spacing: 'spacious', ats: true,
    desc: 'Palatino serif academic. Traditional research/university CV.'
  },
  {
    id: 'academic_charcoal', name: 'Academic Charcoal', category: 'Academic', layout: 'academic',
    accent: '#374151', accent2: '#6B7280', bg: '#fff', font: 'Georgia, serif',
    heading_style: 'border-bottom', font_size: 11.5, name_size: 22, spacing: 'spacious', ats: true,
    desc: 'Charcoal grey academic layout with serif body.'
  },
  {
    id: 'academic_maroon', name: 'Academic Maroon', category: 'Academic', layout: 'academic',
    accent: '#7F1D1D', accent2: '#B91C1C', bg: '#fff', font: '"Palatino Linotype", serif',
    heading_style: 'border-bottom', font_size: 11.5, name_size: 23, spacing: 'spacious', ats: true,
    desc: 'Maroon serif. Research and faculty application CV.'
  },
  {
    id: 'academic_green', name: 'Academic Green', category: 'Academic', layout: 'academic',
    accent: '#14532D', accent2: '#16A34A', bg: '#fff', font: 'Georgia, serif',
    heading_style: 'border-bottom', font_size: 11.5, name_size: 22, spacing: 'spacious', ats: true,
    desc: 'Forest green academic. Education-forward with natural tones.'
  },

  // ═══════════════════════════════════════════════════════════════
  // LAYOUT: compact — One-page compact (90–95)
  // ═══════════════════════════════════════════════════════════════

  {
    id: 'compact_navy', name: 'Compact Navy', category: 'Compact One-Page', layout: 'compact',
    accent: '#1E3A5F', accent2: '#2563EB', bg: '#fff', font: 'Arial, Helvetica, sans-serif',
    heading_style: 'border-bottom', font_size: 9.5, name_size: 19, spacing: 'compact', ats: true,
    desc: 'Everything on one page. Small font, high density. For senior profiles.'
  },
  {
    id: 'compact_teal', name: 'Compact Teal', category: 'Compact One-Page', layout: 'compact',
    accent: '#0F766E', accent2: '#14B8A6', bg: '#fff', font: 'Arial, sans-serif',
    heading_style: 'left-bar', font_size: 9.5, name_size: 19, spacing: 'compact', ats: true,
    desc: 'Compact teal layout. Maximum content, minimum pages.'
  },
  {
    id: 'compact_indigo', name: 'Compact Indigo', category: 'Compact One-Page', layout: 'compact',
    accent: '#4338CA', accent2: '#6366F1', bg: '#fff', font: 'Arial, sans-serif',
    heading_style: 'left-bar', font_size: 9.5, name_size: 19, spacing: 'compact', ats: true,
    desc: 'Dense indigo layout for experienced professionals.'
  },
  {
    id: 'compact_charcoal', name: 'Compact Charcoal', category: 'Compact One-Page', layout: 'compact',
    accent: '#374151', accent2: '#6B7280', bg: '#fff', font: 'Arial, sans-serif',
    heading_style: 'uppercase-only', font_size: 9.5, name_size: 19, spacing: 'compact', ats: true,
    desc: 'Charcoal compact. Professional single-page for experienced candidates.'
  },
  {
    id: 'compact_forest', name: 'Compact Forest', category: 'Compact One-Page', layout: 'compact',
    accent: '#14532D', accent2: '#16A34A', bg: '#fff', font: 'Arial, sans-serif',
    heading_style: 'border-bottom', font_size: 9.5, name_size: 19, spacing: 'compact', ats: true,
    desc: 'Green compact one-pager. Efficient and distinct.'
  },
  {
    id: 'compact_rose', name: 'Compact Rose', category: 'Compact One-Page', layout: 'compact',
    accent: '#9F1239', accent2: '#E11D48', bg: '#fff', font: 'Arial, sans-serif',
    heading_style: 'left-bar', font_size: 9.5, name_size: 19, spacing: 'compact', ats: true,
    desc: 'Rose compact one-pager. Compact yet distinctive.'
  },

  // ═══════════════════════════════════════════════════════════════
  // LAYOUT: two_col_skills — Two-column skills layout (96–100)
  // ═══════════════════════════════════════════════════════════════

  {
    id: 'twocol_skills_navy', name: 'Skills Split Navy', category: 'Two-Column / Sidebar', layout: 'two_col_skills',
    accent: '#1E3A5F', accent2: '#3B82F6', bg: '#fff', sidebar_bg: '#F8FAFC',
    font: 'Arial, sans-serif', heading_style: 'border-bottom',
    font_size: 11, name_size: 22, spacing: 'normal', ats: true,
    desc: 'Two-column top: skills and contact on left, summary on right. Experience below.'
  },
  {
    id: 'twocol_skills_teal', name: 'Skills Split Teal', category: 'Two-Column / Sidebar', layout: 'two_col_skills',
    accent: '#0F766E', accent2: '#14B8A6', bg: '#fff', sidebar_bg: '#F0FDF4',
    font: 'Inter, Arial, sans-serif', heading_style: 'border-bottom',
    font_size: 11, name_size: 22, spacing: 'normal', ats: true,
    desc: 'Teal two-column split. Skills grid left, summary and experience right.'
  },
  {
    id: 'twocol_skills_violet', name: 'Skills Split Violet', category: 'Two-Column / Sidebar', layout: 'two_col_skills',
    accent: '#5B21B6', accent2: '#7C3AED', bg: '#fff', sidebar_bg: '#F5F3FF',
    font: 'Inter, Arial, sans-serif', heading_style: 'left-bar',
    font_size: 11, name_size: 22, spacing: 'normal', ats: true,
    desc: 'Violet two-column split. Prominent skills with left-bar headings.'
  },
  {
    id: 'twocol_skills_data', name: 'Data Skills Split', category: 'Data Analyst', layout: 'two_col_skills',
    accent: '#075985', accent2: '#0EA5E9', bg: '#fff', sidebar_bg: '#F0F9FF',
    font: 'Arial, sans-serif', heading_style: 'border-bottom',
    font_size: 11, name_size: 22, spacing: 'normal', ats: true,
    desc: 'Two-column layout emphasizing data skills and tools. For data professionals.'
  },
  {
    id: 'twocol_skills_exec', name: 'Executive Split', category: 'Executive', layout: 'two_col_skills',
    accent: '#1C1917', accent2: '#44403C', bg: '#fff', sidebar_bg: '#F9FAFB',
    font: 'Georgia, serif', heading_style: 'border-bottom',
    font_size: 11.5, name_size: 24, spacing: 'spacious', ats: true,
    desc: 'Two-column executive: core competencies left, career summary right.'
  }

];

// ── Category list for filter dropdown ────────────────────────────────────────
const TEMPLATE_CATEGORIES = [
  'ATS Friendly', 'Modern Corporate', 'Professional', 'Minimalist',
  'Creative', 'Software Developer', 'Data Analyst', 'Student / Fresher',
  'Academic', 'Executive', 'Two-Column / Sidebar', 'Timeline',
  'Compact One-Page'
];

// ── Lookup helper ─────────────────────────────────────────────────────────────
function getTemplateById(id) {
  return RESUME_TEMPLATES.find(t => t.id === id) || RESUME_TEMPLATES[0];
}
