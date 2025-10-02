// frontend/src/components/forms/CaseSearchForm.js
import { useState } from 'react';
import { useForm } from 'react-hook-form';
import Button from '@/components/ui/Button';
import Input from '@/components/ui/Input';
import Select from '@/components/ui/Select';
import Card from '@/components/ui/Card';
import { CASE_TYPES } from '@/lib/constants';
import { validateCaseNumber, validateYear } from '@/lib/utils';

const CaseSearchForm = ({ onSubmit, loading = false }) => {
  const {
    register,
    handleSubmit,
    formState: { errors },
    watch,
    setValue,
  } = useForm({
    defaultValues: {
      case_type: '',
      case_number: '',
      year: new Date().getFullYear().toString(),
    }
  });

  const [recentSearches, setRecentSearches] = useState([]);

  // Load recent searches from localStorage on component mount
  useState(() => {
    const recent = JSON.parse(localStorage.getItem('recent_searches') || '[]');
    setRecentSearches(recent.slice(0, 5)); // Show only last 5
  }, []);

  const onFormSubmit = (data) => {
    // Validate data
    const caseNumberError = validateCaseNumber(data.case_number);
    const yearError = validateYear(data.year);

    if (caseNumberError || yearError) {
      return;
    }

    // Clean and format data
    const formattedData = {
      case_type: data.case_type.toUpperCase().trim(),
      case_number: data.case_number.trim(),
      year: parseInt(data.year),
    };

    onSubmit(formattedData);
  };

  const fillFromRecent = (search) => {
    setValue('case_type', search.case_type);
    setValue('case_number', search.case_number);
    setValue('year', search.year.toString());
  };

  return (
    <Card>
      <Card.Header>
        <Card.Title>Search Case Details</Card.Title>
        <p className="text-sm text-gray-600 mt-1">
          Enter case details to search across High Courts and District Courts
        </p>
      </Card.Header>

      <Card.Content>
        <form onSubmit={handleSubmit(onFormSubmit)} className="space-y-6">
          {/* Case Type Selection */}
          <Select
            label="Case Type"
            {...register('case_type', { 
              required: 'Case type is required' 
            })}
            error={errors.case_type?.message}
            options={CASE_TYPES}
            placeholder="Select case type (e.g., WP, CRL, CA)"
            helperText="Common types: WP (Writ Petition), CRL (Criminal), CA (Civil Appeal)"
          />

          {/* Case Number Input */}
          <Input
            label="Case Number"
            {...register('case_number', {
              required: 'Case number is required',
              validate: validateCaseNumber,
            })}
            error={errors.case_number?.message}
            placeholder="Enter case number (e.g., 12345, 1234/2024)"
            helperText="Enter the case number without year suffix"
          />

          {/* Year Selection */}
          <Input
            label="Year"
            type="number"
            {...register('year', {
              required: 'Year is required',
              validate: validateYear,
            })}
            error={errors.year?.message}
            min="1950"
            max={new Date().getFullYear() + 1}
            placeholder="Enter filing year"
            helperText="Year when the case was filed"
          />

          {/* Submit Button */}
          <Button
            type="submit"
            className="w-full"
            loading={loading}
            disabled={loading}
          >
            {loading ? 'Searching...' : 'Search Case'}
          </Button>
        </form>

        {/* Recent Searches */}
        {recentSearches.length > 0 && (
          <div className="mt-8 pt-6 border-t border-gray-200">
            <h4 className="text-sm font-medium text-gray-900 mb-3">
              Recent Searches
            </h4>
            <div className="space-y-2">
              {recentSearches.map((search, index) => (
                <div
                  key={index}
                  className="flex items-center justify-between p-3 bg-gray-50 rounded-lg hover:bg-gray-100 cursor-pointer transition-colors"
                  onClick={() => fillFromRecent(search)}
                >
                  <div className="flex-1">
                    <p className="text-sm font-medium text-gray-900">
                      {search.case_type} {search.case_number}/{search.year}
                    </p>
                    <p className="text-xs text-gray-500">
                      Searched on {new Date(search.searchedAt).toLocaleDateString()}
                    </p>
                  </div>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={(e) => {
                      e.stopPropagation();
                      fillFromRecent(search);
                    }}
                  >
                    Use
                  </Button>
                </div>
              ))}
            </div>
          </div>
        )}
      </Card.Content>
    </Card>
  );
};

export default CaseSearchForm;
