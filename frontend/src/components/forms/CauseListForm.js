// frontend/src/components/forms/CauseListForm.js
import { useForm } from 'react-hook-form';
import Button from '@/components/ui/Button';
import Input from '@/components/ui/Input';
import Select from '@/components/ui/Select';
import Card from '@/components/ui/Card';
import { COURT_TYPES } from '@/lib/constants';
import { format } from 'date-fns';

const CauseListForm = ({ onSubmit, loading = false, availableCourts = [] }) => {
  const {
    register,
    handleSubmit,
    formState: { errors },
    watch,
  } = useForm({
    defaultValues: {
      hearing_date: format(new Date(), 'yyyy-MM-dd'),
      court_name: '',
      court_type: '',
    }
  });

  const onFormSubmit = (data) => {
    const formattedData = {
      hearing_date: data.hearing_date,
      court_name: data.court_name || null,
      court_type: data.court_type || null,
    };

    onSubmit(formattedData);
  };

  const setTodaysDate = () => {
    document.getElementById('hearing_date').value = format(new Date(), 'yyyy-MM-dd');
  };

  const setTomorrowsDate = () => {
    const tomorrow = new Date();
    tomorrow.setDate(tomorrow.getDate() + 1);
    document.getElementById('hearing_date').value = format(tomorrow, 'yyyy-MM-dd');
  };

  // Convert available courts to options format
  const courtOptions = availableCourts.map(court => ({
    value: court,
    label: court
  }));

  return (
    <Card>
      <Card.Header>
        <Card.Title>Daily Cause List</Card.Title>
        <p className="text-sm text-gray-600 mt-1">
          Search for daily cause lists by date and court
        </p>
      </Card.Header>

      <Card.Content>
        <form onSubmit={handleSubmit(onFormSubmit)} className="space-y-6">
          {/* Date Selection */}
          <div>
            <Input
              id="hearing_date"
              label="Hearing Date"
              type="date"
              {...register('hearing_date', {
                required: 'Hearing date is required',
              })}
              error={errors.hearing_date?.message}
              helperText="Select the date for which you want to view the cause list"
            />
            
            {/* Quick date buttons */}
            <div className="flex space-x-2 mt-2">
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={setTodaysDate}
              >
                Today
              </Button>
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={setTomorrowsDate}
              >
                Tomorrow
              </Button>
            </div>
          </div>

          {/* Court Type Filter */}
          <Select
            label="Court Type (Optional)"
            {...register('court_type')}
            options={COURT_TYPES}
            placeholder="All court types"
            helperText="Filter by court type"
          />

          {/* Specific Court Filter */}
          {courtOptions.length > 0 && (
            <Select
              label="Specific Court (Optional)"
              {...register('court_name')}
              options={courtOptions}
              placeholder="All courts"
              helperText="Filter by specific court"
            />
          )}

          {/* Submit Button */}
          <Button
            type="submit"
            className="w-full"
            loading={loading}
            disabled={loading}
          >
            {loading ? 'Fetching Cause List...' : 'Get Cause List'}
          </Button>
        </form>

        {/* Information Box */}
        <div className="mt-6 p-4 bg-blue-50 rounded-lg">
          <h4 className="text-sm font-medium text-blue-900 mb-2">
            📋 About Cause Lists
          </h4>
          <ul className="text-sm text-blue-800 space-y-1">
            <li>• Cause lists show cases scheduled for hearing on a specific date</li>
            <li>• Lists are typically published the evening before the hearing date</li>
            <li>• You can check if your case is listed for tomorrow's hearing</li>
            <li>• Data is sourced from official eCourts portals</li>
          </ul>
        </div>
      </Card.Content>
    </Card>
  );
};

export default CauseListForm;
