// frontend/src/app/cause-list/page.js
'use client';

import { useState, useEffect } from 'react';
import CauseListForm from '@/components/forms/CauseListForm';
import CauseListResults from '@/components/features/CauseListResults';
import CaseListingCheckForm from '@/components/forms/CaseListingCheckForm';
import Card from '@/components/ui/Card';
import { useCauseList } from '@/hooks/useCauseList';
import { apiEndpoints } from '@/lib/api';

export default function CauseListPage() {
  const { causeList, caseCheck, fetchCauseList, checkCaseInCauseList } = useCauseList();
  const [availableCourts, setAvailableCourts] = useState([]);
  const [activeTab, setActiveTab] = useState('causeList'); // 'causeList' or 'checkCase'

  useEffect(() => {
    // Load available courts
    loadAvailableCourts();
  }, []);

  const loadAvailableCourts = async () => {
    try {
      const response = await apiEndpoints.getAvailableCourts();
      setAvailableCourts(response.data.courts || []);
    } catch (error) {
      console.error('Failed to load courts:', error);
    }
  };

  const handleCauseListSearch = async (formData) => {
    try {
      await fetchCauseList(formData);
    } catch (error) {
      console.error('Cause list search failed:', error);
    }
  };

  const handleCaseListingCheck = async (formData) => {
    try {
      await checkCaseInCauseList(formData);
    } catch (error) {
      console.error('Case listing check failed:', error);
    }
  };

  const tabs = [
    { id: 'causeList', label: 'Daily Cause List', description: 'View all cases for a date' },
    { id: 'checkCase', label: 'Check Case Listing', description: 'Check if specific case is listed' },
  ];

  return (
    <div className="max-w-7xl mx-auto space-y-8">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Daily Cause Lists</h1>
        <p className="mt-2 text-gray-600">
          View daily cause lists and check case listings across Indian courts
        </p>
      </div>

      {/* Tab Navigation */}
      <Card>
        <Card.Content className="py-4">
          <div className="flex space-x-8">
            {tabs.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex flex-col items-start pb-2 border-b-2 transition-colors ${
                  activeTab === tab.id
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700'
                }`}
              >
                <span className="font-medium">{tab.label}</span>
                <span className="text-sm text-gray-500 mt-1">{tab.description}</span>
              </button>
            ))}
          </div>
        </Card.Content>
      </Card>

      {activeTab === 'causeList' ? (
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
          {/* Cause List Form */}
          <div className="lg:col-span-1">
            <div className="sticky top-6">
              <CauseListForm
                onSubmit={handleCauseListSearch}
                loading={causeList.loading}
                availableCourts={availableCourts}
              />
            </div>
          </div>

          {/* Cause List Results */}
          <div className="lg:col-span-3">
            <CauseListResults
              result={causeList.data}
              loading={causeList.loading}
            />
          </div>
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Case Listing Check Form */}
          <div className="lg:col-span-1">
            <div className="sticky top-6">
              <CaseListingCheckForm
                onSubmit={handleCaseListingCheck}
                loading={caseCheck.loading}
              />
            </div>
          </div>

          {/* Case Listing Check Results */}
          <div className="lg:col-span-2">
            {caseCheck.data && (
              <Card>
                <Card.Header>
                  <Card.Title>Case Listing Results</Card.Title>
                </Card.Header>
                <Card.Content>
                  {caseCheck.data.found ? (
                    <div className="space-y-4">
                      <div className="flex items-center space-x-2">
                        <div className="w-3 h-3 bg-green-500 rounded-full"></div>
                        <span className="font-medium text-green-800">
                          Case Found in Cause List
                        </span>
                      </div>
                      
                      <div className="bg-green-50 p-4 rounded-lg">
                        <h4 className="font-medium text-gray-900 mb-2">
                          {caseCheck.data.case_details.case_type} {caseCheck.data.case_details.case_number}/{caseCheck.data.case_details.year}
                        </h4>
                        <p className="text-sm text-gray-600 mb-3">
                          Listed for hearing on {new Date(caseCheck.data.hearing_date).toLocaleDateString()}
                        </p>
                        
                        <div className="space-y-3">
                          {caseCheck.data.listings.map((listing, index) => (
                            <div key={index} className="bg-white p-3 rounded border">
                              <div className="grid grid-cols-2 gap-4 text-sm">
                                <div>
                                  <span className="text-gray-500">Court:</span>
                                  <p className="font-medium">{listing.court_name}</p>
                                </div>
                                {listing.hearing_time && (
                                  <div>
                                    <span className="text-gray-500">Time:</span>
                                    <p className="font-medium">{listing.hearing_time}</p>
                                  </div>
                                )}
                                {listing.court_hall && (
                                  <div>
                                    <span className="text-gray-500">Hall:</span>
                                    <p className="font-medium">{listing.court_hall}</p>
                                  </div>
                                )}
                                {listing.judge_name && (
                                  <div>
                                    <span className="text-gray-500">Judge:</span>
                                    <p className="font-medium">{listing.judge_name}</p>
                                  </div>
                                )}
                              </div>
                              {listing.parties && (
                                <div className="mt-2">
                                  <span className="text-gray-500 text-sm">Parties:</span>
                                  <p className="text-sm">{listing.parties}</p>
                                </div>
                              )}
                            </div>
                          ))}
                        </div>
                      </div>
                    </div>
                  ) : (
                    <div className="space-y-4">
                      <div className="flex items-center space-x-2">
                        <div className="w-3 h-3 bg-gray-400 rounded-full"></div>
                        <span className="font-medium text-gray-600">
                          Case Not Found in Cause List
                        </span>
                      </div>
                      
                      <div className="bg-gray-50 p-4 rounded-lg">
                        <h4 className="font-medium text-gray-900 mb-2">
                          {caseCheck.data.case_details.case_type} {caseCheck.data.case_details.case_number}/{caseCheck.data.case_details.year}
                        </h4>
                        <p className="text-sm text-gray-600 mb-3">
                          Not listed for hearing on {new Date(caseCheck.data.hearing_date).toLocaleDateString()}
                        </p>
                        <p className="text-sm text-gray-500">
                          {caseCheck.data.message}
                        </p>
                      </div>
                    </div>
                  )}
                </Card.Content>
              </Card>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
