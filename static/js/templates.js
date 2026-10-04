/**
 * AI Career Intelligence Platform — Legacy Template Config
 * =========================================================
 * Backward-compatible shim — the full registry is in resume_templates.js.
 * This file is kept for any legacy references.
 */
'use strict';

// TEMPLATES is a subset for legacy compatibility — use RESUME_TEMPLATES for full list.
const TEMPLATES = [
  {
    id: 'classic_ats', name: 'Classic ATS', category: 'ATS-Safe',
    accent: '#1E3A5F', font: 'Georgia, serif', ats: true,
    desc: 'Traditional single-column, serif font. Maximum ATS compatibility.'
  },
  {
    id: 'modern_pro', name: 'Modern Professional', category: 'Modern',
    accent: '#4F46E5', font: 'Inter, sans-serif', ats: true,
    desc: 'Clean colored header, badge-style skills, left-bordered summary block.'
  },
  {
    id: 'minimal_ats', name: 'Minimal ATS', category: 'Minimal',
    accent: '#374151', font: 'Arial, sans-serif', ats: true,
    desc: 'Ultra-minimal, whitespace-heavy, plain text. Pure parser-safe.'
  },
  {
    id: 'profile_photo', name: 'Profile / Sidebar', category: 'Professional',
    accent: '#0F766E', font: 'Roboto, sans-serif', ats: false,
    desc: 'Two-column layout: left sidebar with contact & skills, right with content.'
  },
  {
    id: 'tech_dev', name: 'Technical / Developer', category: 'Tech',
    accent: '#1E293B', font: "'Fira Code', monospace", ats: true,
    desc: 'Dark header bar, skills first, code-style typography. Ideal for developers.'
  }
];
