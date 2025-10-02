// frontend/src/hooks/useCaseSearch.js
import { useState, useCallback } from 'react';
import { apiEndpoints } from '@/lib/api';
import { storage, STORAGE_KEYS } from '@/lib/utils';
import toast from 'react-hot-toast';

export const useCaseSearch = () => {
  const [state, setState] = useState({
    loading: false,
    error: null,
    data: null,
    executionTime: null,
  });

  const searchCase = useCallback(async (caseData) => {
    setState(prev => ({ ...prev, loading: true, error: null }));
    
    try {
      const response = await apiEndpoints.searchCase(caseData);
      const result = response.data;
      
      setState({
        loading: false,
        error: null,
        data: result,
        executionTime: result.execution_time_ms,
      });

      // Save to recent searches
      saveToRecentSearches(caseData);
      
      if (result.success) {
        toast.success(result.cached ? 'Retrieved from cache' : 'Case found successfully');
      } else {
        toast.error(result.message);
      }

      return result;
    } catch (error) {
      const errorMessage = error.response?.data?.detail || 'Failed to search case';
      setState(prev => ({
        ...prev,
        loading: false,
        error: errorMessage,
      }));
      toast.error(errorMessage);
      throw error;
    }
  }, []);

  const refreshCase = useCallback(async (queryId) => {
    try {
      const response = await apiEndpoints.refreshCase(queryId);
      toast.success('Case refresh initiated');
      return response.data;
    } catch (error) {
      toast.error('Failed to refresh case');
      throw error;
    }
  }, []);

  const saveToRecentSearches = useCallback((caseData) => {
    const recent = storage.get(STORAGE_KEYS.RECENT_SEARCHES, []);
    const newSearch = {
      ...caseData,
      searchedAt: new Date().toISOString(),
    };
    
    // Remove duplicate if exists
    const filtered = recent.filter(
      item => !(item.case_type === caseData.case_type && 
                item.case_number === caseData.case_number && 
                item.year === caseData.year)
    );
    
    // Add to beginning and limit to 50 items
    const updated = [newSearch, ...filtered].slice(0, 50);
    storage.set(STORAGE_KEYS.RECENT_SEARCHES, updated);
  }, []);

  return {
    ...state,
    searchCase,
    refreshCase,
  };
};
