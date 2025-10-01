// frontend/src/lib/constants.js

export const CASE_TYPES = [
  { value: 'WP', label: 'Writ Petition (WP)' },
  { value: 'CRL', label: 'Criminal (CRL)' },
  { value: 'CWP', label: 'Civil Writ Petition (CWP)' },
  { value: 'PIL', label: 'Public Interest Litigation (PIL)' },
  { value: 'CA', label: 'Civil Appeal (CA)' },
  { value: 'SLP', label: 'Special Leave Petition (SLP)' },
  { value: 'CC', label: 'Contempt Case (CC)' },
  { value: 'TC', label: 'Transfer Case (TC)' },
  { value: 'IA', label: 'Interlocutory Application (IA)' },
  { value: 'MA', label: 'Miscellaneous Application (MA)' },
  { value: 'RFA', label: 'Regular First Appeal (RFA)' },
  { value: 'RSA', label: 'Regular Second Appeal (RSA)' },
  { value: 'CS', label: 'Civil Suit (CS)' },
  { value: 'OS', label: 'Original Suit (OS)' },
  { value: 'ARB', label: 'Arbitration (ARB)' },
  { value: 'COMP', label: 'Company Petition (COMP)' },
];

export const COURT_TYPES = [
  { value: 'HIGH_COURT', label: 'High Court' },
  { value: 'DISTRICT_COURT', label: 'District Court' },
];

export const CASE_STATUSES = [
  'Pending',
  'Disposed',
  'Admitted',
  'Dismissed',
  'Allowed',
  'Partly Allowed',
  'Withdrawn',
  'Transferred',
];

export const JUDGMENT_TYPES = [
  { value: 'JUDGMENT', label: 'Judgment' },
  { value: 'ORDER', label: 'Order' },
  { value: 'NOTICE', label: 'Notice' },
];

// Navigation items
export const NAVIGATION_ITEMS = [
  { name: 'Home', href: '/' },
  { name: 'Case Search', href: '/search' },
  { name: 'Cause Lists', href: '/cause-list' },
];

// API status messages
export const API_MESSAGES = {
  SEARCHING: 'Searching case details...',
  SCRAPING: 'Scraping data from court portals...',
  PROCESSING: 'Processing case information...',
  SUCCESS: 'Case details retrieved successfully',
  NOT_FOUND: 'Case not found in any portal',
  ERROR: 'An error occurred while searching',
  CACHE_HIT: 'Retrieved from cache',
};

// Local storage keys
export const STORAGE_KEYS = {
  RECENT_SEARCHES: 'recent_searches',
  USER_PREFERENCES: 'user_preferences',
  FAVORITE_COURTS: 'favorite_courts',
};

// Date format constants
export const DATE_FORMATS = {
  DISPLAY: 'dd/MM/yyyy',
  INPUT: 'yyyy-MM-dd',
  DATETIME: 'dd/MM/yyyy HH:mm',
  API: 'yyyy-MM-dd',
};

// Pagination constants
export const PAGINATION = {
  DEFAULT_PAGE_SIZE: 20,
  MAX_PAGE_SIZE: 100,
};

// File size limits
export const FILE_LIMITS = {
  MAX_PDF_SIZE: 50 * 1024 * 1024, // 50MB
};

export default {
  CASE_TYPES,
  COURT_TYPES,
  CASE_STATUSES,
  JUDGMENT_TYPES,
  NAVIGATION_ITEMS,
  API_MESSAGES,
  STORAGE_KEYS,
  DATE_FORMATS,
  PAGINATION,
  FILE_LIMITS,
};
