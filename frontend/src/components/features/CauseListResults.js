// frontend/src/components/features/CauseListResults.js
import { useState, useMemo } from 'react';
import Card from '@/components/ui/Card';
import Button from '@/components/ui/Button';
import Input from '@/components/ui/Input';
import LoadingSpinner from '@/components/ui/LoadingSpinner';
import { formatDate } from '@/lib/utils';
import { 
  MagnifyingGlassIcon,
  CalendarIcon,
  BuildingLibraryIcon,
  DocumentTextIcon,
  FunnelIcon 
} from '@heroicons/react/24/outline';

const CauseListResults = ({ result, loading }) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedCourt, setSelectedCourt] = useState('');
  const [currentPage, setCurrentPage] = useState(1);
  const itemsPerPage = 20;

  // Filter and search entries
  const filteredEntries = useMemo(() => {
    if (!result?.entries) return [];

    let filtered = result.entries;

    // Filter by court
    if (selectedCourt) {
      filtered = filtered.filter(entry => 
        entry.court_name?.toLowerCase().includes(selectedCourt.toLowerCase())
      );
    }

    // Search filter
    if (searchTerm) {
      const term = searchTerm.toLowerCase();
      filtered = filtered.filter(entry =>
        entry.case_number?.toLowerCase().includes(term) ||
        entry.case_type?.toLowerCase().includes(term) ||
        entry.parties?.toLowerCase().includes(term) ||
        entry.judge_name?.toLowerCase().includes(term)
      );
    }

    return filtered;
  }, [result?.entries, searchTerm, selectedCourt]);

  // Pagination
  const totalPages = Math.ceil(filteredEntries.length / itemsPerPage);
  const paginatedEntries = filteredEntries.slice(
    (currentPage - 1) * itemsPerPage,
    currentPage * itemsPerPage
  );

  if (loading) {
    return (
      <Card className="text-center py-12">
        <LoadingSpinner size="lg" text="Fetching cause list..." />
      </Card>
    );
  }

  if (!result) {
    return null;
  }

  const { hearing_date, total_cases, court_wise_count, cached, last_updated } = result;

  return (
    <div className="space-y-6">
      {/* Summary Header */}
      <Card>
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-lg font-medium text-gray-900">
              Cause List for {formatDate(hearing_date)}
            </h3>
            <div className="flex items-center space-x-4 text-sm text-gray-500 mt-1">
              <span className="flex items-center">
                <DocumentTextIcon className="h-4 w-4 mr-1" />
                {total_cases} cases
              </span>
              <span className="flex items-center">
                <BuildingLibraryIcon className="h-4 w-4 mr-1" />
                {Object.keys(court_wise_count).length} courts
              </span>
              {cached && (
                <span className="text-green-600 bg-green-100 px-2 py-1 rounded-full text-xs">
                  Cached
                </span>
              )}
            </div>
          </div>
          
          {last_updated && (
            <div className="text-right text-sm text-gray-500">
              <p>Last updated</p>
              <p>{formatDate(last_updated, 'dd/MM/yyyy HH:mm')}</p>
            </div>
          )}
        </div>
      </Card>

      {total_cases > 0 ? (
        <>
          {/* Court-wise Statistics */}
          <Card>
            <Card.Header>
              <Card.Title>Court-wise Distribution</Card.Title>
            </Card.Header>
            <Card.Content>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {Object.entries(court_wise_count).map(([court, count]) => (
                  <div
                    key={court}
                    className="p-3 bg-gray-50 rounded-lg cursor-pointer hover:bg-gray-100 transition-colors"
                    onClick={() => setSelectedCourt(court === selectedCourt ? '' : court)}
                  >
                    <div className="flex items-center justify-between">
                      <h4 className="text-sm font-medium text-gray-900 truncate">
                        {court}
                      </h4>
                      <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                        {count}
                      </span>
                    </div>
                    {selectedCourt === court && (
                      <p className="text-xs text-blue-600 mt-1">
                        Filtered • Click to remove filter
                      </p>
                    )}
                  </div>
                ))}
              </div>
            </Card.Content>
          </Card>

          {/* Search and Filters */}
          <Card>
            <Card.Content className="py-4">
              <div className="flex flex-col sm:flex-row gap-4">
                <div className="flex-1">
                  <Input
                    placeholder="Search by case number, type, parties, or judge..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    className="w-full"
                  />
                </div>
                <div className="flex items-center space-x-2 text-sm text-gray-500">
                  <FunnelIcon className="h-4 w-4" />
                  <span>
                    Showing {filteredEntries.length} of {total_cases} cases
                  </span>
                </div>
              </div>
            </Card.Content>
          </Card>

          {/* Cause List Entries */}
          {paginatedEntries.length > 0 ? (
            <Card>
              <Card.Header>
                <Card.Title>Cases Listed ({filteredEntries.length})</Card.Title>
              </Card.Header>
              <Card.Content padding="none">
                <div className="overflow-x-auto">
                  <table className="min-w-full divide-y divide-gray-200">
                    <thead className="bg-gray-50">
                      <tr>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Case Details
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Parties
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Court/Judge
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Time/Hall
                        </th>
                      </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-200">
                      {paginatedEntries.map((entry, index) => (
                        <tr key={`${entry.id || index}`} className="hover:bg-gray-50">
                          <td className="px-6 py-4 whitespace-nowrap">
                            <div>
                              <div className="text-sm font-medium text-gray-900">
                                {entry.case_type} {entry.case_number}
                                {entry.case_year && `/${entry.case_year}`}
                              </div>
                              <div className="text-sm text-gray-500">
                                {entry.hearing_purpose || 'Regular hearing'}
                              </div>
                            </div>
                          </td>
                          <td className="px-6 py-4">
                            <div className="text-sm text-gray-900 max-w-xs truncate">
                              {entry.parties || 'Parties not specified'}
                            </div>
                          </td>
                          <td className="px-6 py-4">
                            <div>
                              <div className="text-sm text-gray-900 truncate max-w-xs">
                                {entry.court_name || 'Court not specified'}
                              </div>
                              {entry.judge_name && (
                                <div className="text-sm text-gray-500 truncate max-w-xs">
                                  {entry.judge_name}
                                </div>
                              )}
                            </div>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                            <div>
                              {entry.hearing_time && (
                                <div>{entry.hearing_time}</div>
                              )}
                              {entry.court_hall && (
                                <div>Hall: {entry.court_hall}</div>
                              )}
                            </div>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </Card.Content>
            </Card>
          ) : (
            <Card className="text-center py-8">
              <MagnifyingGlassIcon className="h-8 w-8 mx-auto text-gray-400 mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">
                No cases match your search
              </h3>
              <p className="text-gray-600">
                Try adjusting your search terms or removing filters
              </p>
            </Card>
          )}

          {/* Pagination */}
          {totalPages > 1 && (
            <Card>
              <Card.Content className="py-4">
                <div className="flex justify-between items-center">
                  <div className="text-sm text-gray-500">
                    Page {currentPage} of {totalPages}
                  </div>
                  <div className="flex space-x-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setCurrentPage(Math.max(1, currentPage - 1))}
                      disabled={currentPage === 1}
                    >
                      Previous
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setCurrentPage(Math.min(totalPages, currentPage + 1))}
                      disabled={currentPage === totalPages}
                    >
                      Next
                    </Button>
                  </div>
                </div>
              </Card.Content>
            </Card>
          )}
        </>
      ) : (
        <Card className="text-center py-12">
          <CalendarIcon className="h-12 w-12 mx-auto text-gray-400 mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">
            No Cause List Available
          </h3>
          <p className="text-gray-600 mb-4">
            No cases are listed for {formatDate(hearing_date)}
          </p>
          <div className="space-y-1 text-sm text-gray-500">
            <p>• The cause list might not be published yet</p>
            <p>• This could be a holiday or non-working day</p>
            <p>• Try a different date or court</p>
          </div>
        </Card>
      )}
    </div>
  );
};

export default CauseListResults;
