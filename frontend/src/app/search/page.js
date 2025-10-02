// frontend/src/app/search/page.js
'use client';

import { useState, useEffect } from 'react';
import { useSearchParams } from 'next/navigation';
import CaseSearchForm from '@/components/forms/CaseSearchForm';
import CaseSearchResults from '@/components/features/CaseSearchResults';
import { useCaseSearch } from '@/hooks/useCaseSearch';
import { validateCaseNumber, validateYear } from '@/lib/utils';

export default function CaseSearchPage() {
  const searchParams = useSearchParams();
  const { loading, error, data, searchCase, refreshCase } = useCaseSearch();
  const [refreshing, setRefreshing] = useState(false);

  // Auto-search if URL params are provided
  useEffect(() => {
    const caseType = searchParams.get('case_type');
    const caseNumber = searchParams.get('case_number');
    const year = searchParams.get('year');

    if (caseType && caseNumber && year) {
      // Validate parameters
      const caseNumberError = validateCaseNumber(caseNumber);
      const yearError = validateYear(year);

      if (!caseNumberError && !yearError) {
        handleSearch({
          case_type: caseType.toUpperCase(),
          case_number: caseNumber,
          year: parseInt(year),
        });
      }
    }
  }, [searchParams]);

  const handleSearch = async (formData) => {
    try {
      await searchCase(formData);
    } catch (error) {
      console.error('Search failed:', error);
    }
  };

  const handleRefresh = async (queryId) => {
    setRefreshing(true);
    try {
      await refreshCase(queryId);
      // Re-fetch the case data after refresh
      if (data?.query) {
        const { case_type, case_number, year } = data.query;
        await searchCase({ case_type, case_number, year });
      }
    } catch (error) {
      console.error('Refresh failed:', error);
    } finally {
      setRefreshing(false);
    }
  };

  return (
    <div className="max-w-6xl mx-auto space-y-8">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Case Search</h1>
        <p className="mt-2 text-gray-600">
          Search for case details across Indian High Courts and District Courts
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Search Form */}
        <div className="lg:col-span-1">
          <div className="sticky top-6">
            <CaseSearchForm 
              onSubmit={handleSearch}
              loading={loading}
            />
          </div>
        </div>

        {/* Search Results */}
        <div className="lg:col-span-2">
          <CaseSearchResults
            result={data}
            loading={loading}
            onRefresh={handleRefresh}
            refreshing={refreshing}
          />
        </div>
      </div>
    </div>
  );
}
