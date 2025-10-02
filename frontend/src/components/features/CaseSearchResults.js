// frontend/src/components/features/CaseSearchResults.js
import { useState } from 'react';
import Card from '@/components/ui/Card';
import Button from '@/components/ui/Button';
import LoadingSpinner from '@/components/ui/LoadingSpinner';
import { 
  formatDate, 
  getCaseStatusBadgeClasses, 
  truncateText 
} from '@/lib/utils';
import { 
  DocumentArrowDownIcon, 
  ArrowPathIcon,
  ClockIcon,
  ScaleIcon,
  UserIcon,
  CalendarIcon 
} from '@heroicons/react/24/outline';
import { downloadFile } from '@/lib/api';

const CaseSearchResults = ({ 
  result, 
  loading, 
  onRefresh, 
  refreshing = false 
}) => {
  const [downloadingJudgments, setDownloadingJudgments] = useState(new Set());

  if (loading) {
    return (
      <Card className="text-center py-12">
        <LoadingSpinner size="lg" text="Searching case details..." />
      </Card>
    );
  }

  if (!result) {
    return null;
  }

  const { query, success, message, cached, execution_time_ms } = result;
  const caseData = query?.case;

  const handleJudgmentDownload = async (judgment) => {
    if (!judgment.pdf_url) return;

    setDownloadingJudgments(prev => new Set([...prev, judgment.id]));
    
    try {
      await downloadFile(judgment.id, judgment.file_name);
    } catch (error) {
      console.error('Download failed:', error);
    } finally {
      setDownloadingJudgments(prev => {
        const newSet = new Set(prev);
        newSet.delete(judgment.id);
        return newSet;
      });
    }
  };

  return (
    <div className="space-y-6">
      {/* Search Summary */}
      <Card>
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-lg font-medium text-gray-900">
              Search Results for {query.case_type} {query.case_number}/{query.year}
            </h3>
            <div className="flex items-center space-x-4 text-sm text-gray-500 mt-1">
              <span className="flex items-center">
                <ClockIcon className="h-4 w-4 mr-1" />
                {execution_time_ms}ms
              </span>
              {cached && (
                <span className="text-green-600 bg-green-100 px-2 py-1 rounded-full text-xs">
                  Cached Result
                </span>
              )}
            </div>
          </div>
          
          <Button
            variant="outline"
            size="sm"
            onClick={() => onRefresh(query.id)}
            disabled={refreshing}
            loading={refreshing}
          >
            <ArrowPathIcon className="h-4 w-4 mr-2" />
            Refresh
          </Button>
        </div>
      </Card>

      {success && caseData ? (
        <>
          {/* Main Case Details */}
          <Card>
            <Card.Header>
              <div className="flex items-center justify-between">
                <Card.Title>Case Details</Card.Title>
                <span className={getCaseStatusBadgeClasses(caseData.case_status)}>
                  {caseData.case_status || 'Status Unknown'}
                </span>
              </div>
            </Card.Header>

            <Card.Content>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {/* Left Column */}
                <div className="space-y-4">
                  <div>
                    <h4 className="flex items-center text-sm font-medium text-gray-700 mb-2">
                      <UserIcon className="h-4 w-4 mr-2" />
                      Parties
                    </h4>
                    <div className="space-y-2">
                      <div>
                        <span className="text-xs text-gray-500 uppercase tracking-wide">
                          Petitioner/Appellant
                        </span>
                        <p className="text-sm text-gray-900">
                          {caseData.parties_petitioner || 'Not available'}
                        </p>
                      </div>
                      <div>
                        <span className="text-xs text-gray-500 uppercase tracking-wide">
                          Respondent/Defendant
                        </span>
                        <p className="text-sm text-gray-900">
                          {caseData.parties_respondent || 'Not available'}
                        </p>
                      </div>
                    </div>
                  </div>

                  <div>
                    <h4 className="flex items-center text-sm font-medium text-gray-700 mb-2">
                      <CalendarIcon className="h-4 w-4 mr-2" />
                      Important Dates
                    </h4>
                    <div className="space-y-2">
                      <div className="flex justify-between">
                        <span className="text-xs text-gray-500">Filing Date:</span>
                        <span className="text-sm text-gray-900">
                          {formatDate(caseData.filing_date)}
                        </span>
                      </div>
                      {caseData.registration_date && (
                        <div className="flex justify-between">
                          <span className="text-xs text-gray-500">Registration:</span>
                          <span className="text-sm text-gray-900">
                            {formatDate(caseData.registration_date)}
                          </span>
                        </div>
                      )}
                      <div className="flex justify-between">
                        <span className="text-xs text-gray-500">Next Hearing:</span>
                        <span className="text-sm text-gray-900 font-medium">
                          {formatDate(caseData.next_hearing_date)}
                        </span>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Right Column */}
                <div className="space-y-4">
                  <div>
                    <h4 className="flex items-center text-sm font-medium text-gray-700 mb-2">
                      <ScaleIcon className="h-4 w-4 mr-2" />
                      Court Information
                    </h4>
                    <div className="space-y-2">
                      <div className="flex justify-between">
                        <span className="text-xs text-gray-500">Court:</span>
                        <span className="text-sm text-gray-900 text-right">
                          {truncateText(caseData.court_name, 40) || 'Not specified'}
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-xs text-gray-500">Type:</span>
                        <span className="text-sm text-gray-900">
                          {caseData.court_type?.replace('_', ' ') || 'Not specified'}
                        </span>
                      </div>
                      {caseData.judge_name && (
                        <div className="flex justify-between">
                          <span className="text-xs text-gray-500">Judge:</span>
                          <span className="text-sm text-gray-900 text-right">
                            {truncateText(caseData.judge_name, 40)}
                          </span>
                        </div>
                      )}
                      {caseData.court_hall && (
                        <div className="flex justify-between">
                          <span className="text-xs text-gray-500">Court Hall:</span>
                          <span className="text-sm text-gray-900">
                            {caseData.court_hall}
                          </span>
                        </div>
                      )}
                    </div>
                  </div>

                  {(caseData.case_category || caseData.disposal_nature) && (
                    <div>
                      <h4 className="text-sm font-medium text-gray-700 mb-2">
                        Additional Information
                      </h4>
                      <div className="space-y-2">
                        {caseData.case_category && (
                          <div className="flex justify-between">
                            <span className="text-xs text-gray-500">Category:</span>
                            <span className="text-sm text-gray-900">
                              {caseData.case_category}
                            </span>
                          </div>
                        )}
                        {caseData.disposal_nature && (
                          <div className="flex justify-between">
                            <span className="text-xs text-gray-500">Disposal:</span>
                            <span className="text-sm text-gray-900">
                              {caseData.disposal_nature}
                            </span>
                          </div>
                        )}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            </Card.Content>
          </Card>

          {/* Judgments/Orders */}
          {caseData.judgments && caseData.judgments.length > 0 && (
            <Card>
              <Card.Header>
                <Card.Title>Judgments & Orders ({caseData.judgments.length})</Card.Title>
              </Card.Header>
              <Card.Content>
                <div className="space-y-3">
                  {caseData.judgments.map((judgment) => (
                    <div
                      key={judgment.id}
                      className="flex items-center justify-between p-4 border border-gray-200 rounded-lg hover:bg-gray-50"
                    >
                      <div className="flex-1">
                        <div className="flex items-center space-x-2">
                          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                            {judgment.judgment_type}
                          </span>
                          {judgment.judgment_date && (
                            <span className="text-sm text-gray-500">
                              {formatDate(judgment.judgment_date)}
                            </span>
                          )}
                        </div>
                        <p className="text-sm text-gray-900 mt-1">
                          {judgment.file_name || `${judgment.judgment_type} Document`}
                        </p>
                        {judgment.file_size && (
                          <p className="text-xs text-gray-500">
                            Size: {Math.round(judgment.file_size / 1024)}KB
                          </p>
                        )}
                      </div>
                      
                      {judgment.pdf_url && judgment.is_available && (
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => handleJudgmentDownload(judgment)}
                          loading={downloadingJudgments.has(judgment.id)}
                          disabled={downloadingJudgments.has(judgment.id)}
                        >
                          <DocumentArrowDownIcon className="h-4 w-4 mr-2" />
                          Download
                        </Button>
                      )}
                    </div>
                  ))}
                </div>
              </Card.Content>
            </Card>
          )}
        </>
      ) : (
        /* No Results Found */
        <Card className="text-center py-12">
          <div className="text-gray-400 mb-4">
            <ScaleIcon className="h-12 w-12 mx-auto" />
          </div>
          <h3 className="text-lg font-medium text-gray-900 mb-2">
            Case Not Found
          </h3>
          <p className="text-gray-600 mb-4">
            {message || 'The case was not found in any of the court portals.'}
          </p>
          <div className="space-y-2 text-sm text-gray-500">
            <p>• Verify the case type, number, and year</p>
            <p>• The case might not be digitized yet</p>
            <p>• Try searching in a different court portal manually</p>
          </div>
        </Card>
      )}
    </div>
  );
};

export default CaseSearchResults;
