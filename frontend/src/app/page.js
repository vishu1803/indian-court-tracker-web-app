// frontend/src/app/page.js
'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import Button from '@/components/ui/Button';
import Card from '@/components/ui/Card';
import { 
  MagnifyingGlassIcon,
  DocumentTextIcon,
  ScaleIcon,
  ClockIcon,
  CheckBadgeIcon 
} from '@heroicons/react/24/outline';
import { apiEndpoints } from '@/lib/api';
import { formatDate, storage } from '@/lib/utils';
import { STORAGE_KEYS } from '@/lib/constants';

const HomePage = () => {
  const [recentSearches, setRecentSearches] = useState([]);
  const [healthStatus, setHealthStatus] = useState(null);

  useEffect(() => {
    // Load recent searches from localStorage
    const recent = storage.get(STORAGE_KEYS.RECENT_SEARCHES, []);
    setRecentSearches(recent.slice(0, 5));

    // Check API health
    checkApiHealth();
  }, []);

  const checkApiHealth = async () => {
    try {
      const response = await apiEndpoints.healthCheck();
      setHealthStatus(response.data);
    } catch (error) {
      setHealthStatus({ status: 'unhealthy', error: 'API not accessible' });
    }
  };

  const features = [
    {
      icon: MagnifyingGlassIcon,
      title: 'Case Search',
      description: 'Search for case details across High Courts and District Courts using case type, number, and year.',
      href: '/search',
      color: 'blue',
    },
    {
      icon: DocumentTextIcon,
      title: 'Daily Cause Lists',
      description: 'View daily cause lists to check which cases are scheduled for hearing on specific dates.',
      href: '/cause-list',
      color: 'green',
    },
    {
      icon: ClockIcon,
      title: 'Real-time Updates',
      description: 'Get the latest case information directly from official eCourts portals with caching for speed.',
      href: '/search',
      color: 'purple',
    },
  ];

  return (
    <div className="space-y-12">
      {/* Hero Section */}
      <div className="text-center">
        <div className="flex justify-center mb-6">
          <div className="flex items-center justify-center w-16 h-16 bg-blue-100 rounded-full">
            <ScaleIcon className="w-8 h-8 text-blue-600" />
          </div>
        </div>
        
        <h1 className="text-4xl font-bold text-gray-900 sm:text-5xl md:text-6xl">
          Indian Court Case
          <span className="text-blue-600"> Tracker</span>
        </h1>
        
        <p className="mt-6 max-w-2xl mx-auto text-xl text-gray-600">
          Track case details and daily cause lists from official Indian eCourts portals. 
          Search across High Courts and District Courts in real-time.
        </p>

        <div className="mt-8 flex flex-col sm:flex-row gap-4 justify-center">
          <Link href="/search">
            <Button size="lg" className="w-full sm:w-auto">
              <MagnifyingGlassIcon className="w-5 h-5 mr-2" />
              Search Cases
            </Button>
          </Link>
          <Link href="/cause-list">
            <Button variant="outline" size="lg" className="w-full sm:w-auto">
              <DocumentTextIcon className="w-5 h-5 mr-2" />
              View Cause Lists
            </Button>
          </Link>
        </div>

        {/* API Status */}
        {healthStatus && (
          <div className="mt-6 flex justify-center">
            <div className={`inline-flex items-center px-3 py-1 rounded-full text-sm ${
              healthStatus.status === 'healthy' 
                ? 'bg-green-100 text-green-800' 
                : 'bg-red-100 text-red-800'
            }`}>
              <CheckBadgeIcon className="w-4 h-4 mr-1" />
              API Status: {healthStatus.status}
            </div>
          </div>
        )}
      </div>

      {/* Features Section */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
        {features.map((feature, index) => (
          <Card key={index} className="hover:shadow-lg transition-shadow cursor-pointer">
            <Link href={feature.href}>
              <Card.Content>
                <div className={`inline-flex items-center justify-center w-12 h-12 rounded-lg mb-4 ${
                  feature.color === 'blue' ? 'bg-blue-100' :
                  feature.color === 'green' ? 'bg-green-100' :
                  'bg-purple-100'
                }`}>
                  <feature.icon className={`w-6 h-6 ${
                    feature.color === 'blue' ? 'text-blue-600' :
                    feature.color === 'green' ? 'text-green-600' :
                    'text-purple-600'
                  }`} />
                </div>
                <h3 className="text-lg font-semibold text-gray-900 mb-2">
                  {feature.title}
                </h3>
                <p className="text-gray-600">
                  {feature.description}
                </p>
              </Card.Content>
            </Link>
          </Card>
        ))}
      </div>

      {/* Recent Searches */}
      {recentSearches.length > 0 && (
        <Card>
          <Card.Header>
            <Card.Title>Recent Searches</Card.Title>
            <p className="text-sm text-gray-600 mt-1">
              Your recently searched cases
            </p>
          </Card.Header>
          <Card.Content>
            <div className="space-y-3">
              {recentSearches.map((search, index) => (
                <div
                  key={index}
                  className="flex items-center justify-between p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors"
                >
                  <div>
                    <p className="font-medium text-gray-900">
                      {search.case_type} {search.case_number}/{search.year}
                    </p>
                    <p className="text-sm text-gray-500">
                      Searched on {formatDate(search.searchedAt)}
                    </p>
                  </div>
                  <Link href={`/search?case_type=${search.case_type}&case_number=${search.case_number}&year=${search.year}`}>
                    <Button variant="outline" size="sm">
                      Search Again
                    </Button>
                  </Link>
                </div>
              ))}
            </div>
            <div className="mt-4 pt-4 border-t border-gray-200">
              <Link href="/search">
                <Button variant="ghost" className="w-full">
                  View All Searches
                </Button>
              </Link>
            </div>
          </Card.Content>
        </Card>
      )}

      {/* Information Section */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
        <Card>
          <Card.Header>
            <Card.Title>Data Sources</Card.Title>
          </Card.Header>
          <Card.Content>
            <div className="space-y-4">
              <div>
                <h4 className="font-medium text-gray-900">High Courts</h4>
                <p className="text-sm text-gray-600">
                  Data from hcservices.ecourts.gov.in covering all 25 High Courts in India
                </p>
              </div>
              <div>
                <h4 className="font-medium text-gray-900">District Courts</h4>
                <p className="text-sm text-gray-600">
                  Information from services.ecourts.gov.in covering 2,852+ district court complexes
                </p>
              </div>
            </div>
          </Card.Content>
        </Card>

        <Card>
          <Card.Header>
            <Card.Title>How It Works</Card.Title>
          </Card.Header>
          <Card.Content>
            <div className="space-y-4">
              <div className="flex items-start space-x-3">
                <div className="flex-shrink-0 w-6 h-6 bg-blue-100 rounded-full flex items-center justify-center">
                  <span className="text-xs font-medium text-blue-600">1</span>
                </div>
                <p className="text-sm text-gray-600">
                  Enter case details (type, number, year)
                </p>
              </div>
              <div className="flex items-start space-x-3">
                <div className="flex-shrink-0 w-6 h-6 bg-blue-100 rounded-full flex items-center justify-center">
                  <span className="text-xs font-medium text-blue-600">2</span>
                </div>
                <p className="text-sm text-gray-600">
                  System searches both High Court and District Court portals
                </p>
              </div>
              <div className="flex items-start space-x-3">
                <div className="flex-shrink-0 w-6 h-6 bg-blue-100 rounded-full flex items-center justify-center">
                  <span className="text-xs font-medium text-blue-600">3</span>
                </div>
                <p className="text-sm text-gray-600">
                  Get comprehensive case details and downloadable documents
                </p>
              </div>
            </div>
          </Card.Content>
        </Card>
      </div>

      {/* Disclaimer */}
      <Card className="bg-yellow-50 border-yellow-200">
        <Card.Content>
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <svg className="h-5 w-5 text-yellow-400" viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
              </svg>
            </div>
            <div className="ml-3">
              <h3 className="text-sm font-medium text-yellow-800">
                Educational Purpose
              </h3>
              <div className="mt-1 text-sm text-yellow-700">
                <p>
                  This application is built for educational purposes to demonstrate web scraping and API development. 
                  Always verify information from official court websites for legal proceedings.
                </p>
              </div>
            </div>
          </div>
        </Card.Content>
      </Card>
    </div>
  );
};

export default HomePage;
