// frontend/src/components/forms/CaseListingCheckForm.js
import { useForm } from 'react-hook-form';
import Button from '@/components/ui/Button';
import Input from '@/components/ui/Input';
import Select from '@/components/ui/Select';
import Card from '@/components/ui/Card';
import { CASE_TYPES } from '@/lib/constants';
import { validateCaseNumber, validateYear } from '@/lib/utils';
import { format } from 'date-fns';

const CaseListingCheckForm = ({ onSubmit, loading = false }) => {
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm({
    defaultValues: {
      case_type: '',
      case_number: '',
      year: new Date().getFullYear().toString(),
      hearing_date: format(new Date(), 'yyyy-MM-dd'),
    }
  });

  const onFormSubmit = (data) => {
    const formattedData = {
      case_type: data.case_type.toUpperCase().trim(),
      case_number: data.case_number.trim(),
      year: parseInt(data.year),
      hearing_date: data.hearing_date,
    };

    onSubmit(formattedData);
  };

  return (
    <Card>
      <Card.Header>
        <Card.Title>Check Case in Cause List</Card.Title>
        <p className="text-sm text-gray-600 mt-1">
          Check if your case is listed for hearing on a specific date
        </p>
      </Card.Header>

      <Card.Content>
        <form onSubmit={handleSubmit(onFormSubmit)} className="space-y-6">
          {/* Case Details Row */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Select
              label="Case Type"
              {...register('case_type', { 
                required: 'Case type is required' 
              })}
              error={errors.case_type?.message}
              options={CASE_TYPES}
              placeholder="Select type"
            />

            <Input
              label="Case Number"
              {...register('case_number', {
                required: 'Case number is required',
                validate: validateCaseNumber,
              })}
              error={errors.case_number?.message}
              placeholder="Case number"
            />

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
              placeholder="Year"
            />
          </div>

          {/* Hearing Date */}
          <Input
            label="Check for Date"
            type="date"
            {...register('hearing_date', {
              required: 'Date is required',
            })}
            error={errors.hearing_date?.message}
            helperText="Date to check if case is listed"
          />

          {/* Submit Button */}
          <Button
            type="submit"
            className="w-full"
            loading={loading}
            disabled={loading}
          >
            {loading ? 'Checking...' : 'Check Case Listing'}
          </Button>
        </form>
      </Card.Content>
    </Card>
  );
};

export default CaseListingCheckForm;
