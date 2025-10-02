// frontend/src/app/case/[id]/page.js
'use client';

import { useState, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import CaseSearchResults from '@/components/features/CaseSearchResults';
import LoadingSpinner from '@/components/ui/LoadingSpinner';
import Card from '@/components/ui/Card';
import Button from '@/components/ui/Button';
import { apiEndpoints } from '@/lib/api';
import { ArrowLeftIcon } from '@heroicons/react/24/outline';

export default function CaseDetailsPage() {
  const params = useParams();
  const router = useRouter();
  const [caseData, setCaseData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [refreshing, setRefreshing] = useState(false);

  useEffect(() => {
    if (params.id) {
      fetchCaseDetails(params.id);
    }
  }, [params.id]);

  const fetchCaseDetails = async (queryId) => {
    try {
      setLoading(true);
      setError(null);
      const response = await apiEndpoints.getCaseById(queryId);
      
      // Transform data to match CaseSearchResults expected format
      const transformedData = {
        success: true,
        query: response.data,
        cached: false,
        execution_time_ms: 0,
      };
      
      setCaseData(transformedData);
    } catch (error) {
      console.error('Failed to fetch case details:', error);
      setError(error.response?.data?.detail || 'Failed to load case details');
    } finally {
      setLoading(false);
    }
  };

  const handleRefresh = async (queryId) => {
    setRefreshing(true);
    try {
      await apiEndpoints.refreshCase(queryId);
      // Wait a moment then refetch
      setTimeout(() => {
        fetchCaseDetails(queryId);
      }, 2000);
    } catch (error) {
      console.error('Refresh failed:', error);
    } finally {
      setRefreshing(false);
    }
  };

  if (loading) {
    return (
      <div className="max-w-6xl mx-auto">
        <Card className="text-center py-12">
          <LoadingSpinner size="lg" text="Loading case details..." />
        </Card>
      </div>
    );
  }

  if (error) {
    return (
      <div className="max-w-6xl mx-auto space-y-6">
        <Button
          variant="outline"
          onClick={() => router.back()}
          className="inline-flex items-center"
        >
          <ArrowLeftIcon className="h-4 w-4 mr-2" />
          Go Back
        </Button>
        
        <Card className="text-center py-12">
          <div className="text-red-500 mb-4">
            <svg className="h-12 w-12 mx-auto" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <h3 className="text-lg font-medium text-gray-900 mb-2">
            Unable to Load Case
          </h3>
          <p className="text-gray-600 mb-4">
            {error}
          </p>
          <Button onClick={() => fetchCaseDetails(params.id)}>
            Try Again
          </Button>
        </Card>
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      <div className="flex items-center space-x-4">
        <Button
          variant="outline"
          onClick={() => router.back()}
          className="inline-flex items-center"
        >
          <ArrowLeftIcon className="h-4 w-4 mr-2" />
          Go Back
        </Button>
        
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Case Details</h1>
          <p className="text-gray-600">
            Detailed information for query #{params.id}
          </p>
        </div>
      </div>

      <CaseSearchResults
        result={caseData}
        loading={false}
        onRefresh={handleRefresh}
        refreshing={refreshing}
      />
    </div>
  );
}
