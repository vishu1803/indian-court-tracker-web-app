// frontend/src/lib/utils.js
import { clsx } from 'clsx';
import { format, parseISO, isValid } from 'date-fns';

// Import STORAGE_KEYS from constants
import { STORAGE_KEYS } from './constants';

// Utility for merging class names
export function cn(...inputs) {
  return clsx(inputs);
}

// Date formatting utilities
export const formatDate = (dateString, formatStr = 'dd/MM/yyyy') => {
  if (!dateString) return 'N/A';
  
  try {
    const date = typeof dateString === 'string' ? parseISO(dateString) : dateString;
    return isValid(date) ? format(date, formatStr) : 'Invalid Date';
  } catch (error) {
    console.error('Date formatting error:', error);
    return 'Invalid Date';
  }
};

export const formatDateTime = (dateString) => {
  return formatDate(dateString, 'dd/MM/yyyy HH:mm');
};

// Case status utilities
export const getCaseStatusColor = (status) => {
  if (!status) return 'gray';
  
  const statusLower = status.toLowerCase();
  
  if (statusLower.includes('disposed') || statusLower.includes('dismissed')) {
    return 'red';
  } else if (statusLower.includes('admitted') || statusLower.includes('allowed')) {
    return 'green';
  } else if (statusLower.includes('pending')) {
    return 'yellow';
  } else {
    return 'blue';
  }
};

export const getCaseStatusBadgeClasses = (status) => {
  const color = getCaseStatusColor(status);
  
  const colorClasses = {
    red: 'bg-red-100 text-red-800 border-red-200',
    green: 'bg-green-100 text-green-800 border-green-200',
    yellow: 'bg-yellow-100 text-yellow-800 border-yellow-200',
    blue: 'bg-blue-100 text-blue-800 border-blue-200',
    gray: 'bg-gray-100 text-gray-800 border-gray-200',
  };
  
  return `inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border ${colorClasses[color]}`;
};

// Text truncation
export const truncateText = (text, maxLength = 100) => {
  if (!text || text.length <= maxLength) return text;
  return text.substring(0, maxLength) + '...';
};

// Validation utilities
export const validateCaseNumber = (caseNumber) => {
  if (!caseNumber) return 'Case number is required';
  if (caseNumber.trim().length < 1) return 'Case number cannot be empty';
  if (caseNumber.length > 50) return 'Case number is too long';
  return null;
};

export const validateYear = (year) => {
  const currentYear = new Date().getFullYear();
  const numYear = parseInt(year);
  
  if (!year) return 'Year is required';
  if (isNaN(numYear)) return 'Year must be a number';
  if (numYear < 1950) return 'Year cannot be before 1950';
  if (numYear > currentYear + 1) return `Year cannot be more than ${currentYear + 1}`;
  
  return null;
};

// Local storage utilities
export const storage = {
  set: (key, value) => {
    try {
      localStorage.setItem(key, JSON.stringify(value));
    } catch (error) {
      console.error('LocalStorage set error:', error);
    }
  },
  
  get: (key, defaultValue = null) => {
    try {
      const item = localStorage.getItem(key);
      return item ? JSON.parse(item) : defaultValue;
    } catch (error) {
      console.error('LocalStorage get error:', error);
      return defaultValue;
    }
  },
  
  remove: (key) => {
    try {
      localStorage.removeItem(key);
    } catch (error) {
      console.error('LocalStorage remove error:', error);
    }
  },
};

// Re-export STORAGE_KEYS for convenience
export { STORAGE_KEYS };
