// frontend/src/hooks/useCauseList.js
import { useState, useCallback } from 'react';
import { apiEndpoints } from '@/lib/api';
import toast from 'react-hot-toast';

export const useCauseList = () => {
  const [state, setState] = useState({
    loading: false,
    error: null,
    data: null,
  });

  const [checkState, setCheckState] = useState({
    loading: false,
    error: null,
    data: null,
  });

  const fetchCauseList = useCallback(async (dateData) => {
    setState(prev => ({ ...prev, loading: true, error: null }));
    
    try {
      const response = await apiEndpoints.getCauseListByDate(dateData);
      const result = response.data;
      
      setState({
        loading: false,
        error: null,
        data: result,
      });

      toast.success(
        `Found ${result.total_cases} cases${result.cached ? ' (from cache)' : ''}`
      );

      return result;
    } catch (error) {
      const errorMessage = error.response?.data?.detail || 'Failed to fetch cause list';
      setState(prev => ({
        ...prev,
        loading: false,
        error: errorMessage,
      }));
      throw error;
    }
  }, []);

  const checkCaseInCauseList = useCallback(async (params) => {
    setCheckState(prev => ({ ...prev, loading: true, error: null }));
    
    try {
      const response = await apiEndpoints.checkCaseInCauseList(params);
      const result = response.data;
      
      setCheckState({
        loading: false,
        error: null,
        data: result,
      });

      if (result.found) {
        toast.success(`Case found in ${result.listings.length} court(s)`);
      } else {
        toast.info('Case not found in cause list');
      }

      return result;
    } catch (error) {
      const errorMessage = error.response?.data?.detail || 'Failed to check case listing';
      setCheckState(prev => ({
        ...prev,
        loading: false,
        error: errorMessage,
      }));
      throw error;
    }
  }, []);

  return {
    causeList: state,
    caseCheck: checkState,
    fetchCauseList,
    checkCaseInCauseList,
  };
};
