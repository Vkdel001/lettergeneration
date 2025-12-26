import React from 'react';
import { FileText, Download, Folder, MessageSquare, Mail } from 'lucide-react';

const TabNavigation = ({ activeTab, onTabChange }) => {
  const tabs = [
    {
      id: 'combine',
      label: 'Generate and Combine',
      icon: FileText,
      description: 'Upload Excel files and generate PDF letters'
    },
    {
      id: 'sms-links',
      label: 'SMS Links',
      icon: MessageSquare,
      description: 'Generate SMS links from existing PDF folders'
    },
    {
      id: 'browse',
      label: 'Browse & Download',
      icon: Folder,
      description: 'Download previously combined PDF files'
    },
    {
      id: 'email-config',
      label: 'Email Notifications',
      icon: Mail,
      description: 'Configure email notifications for completion alerts'
    }
  ];

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 mb-8">
      <h2 className="text-2xl font-bold mb-6 text-gray-800 text-center">Manage Old Files</h2>
      
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {tabs.map((tab) => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.id;
          
          return (
            <button
              key={tab.id}
              onClick={() => onTabChange(tab.id)}
              className={`
                p-6 rounded-xl border-2 transition-all duration-300 transform hover:scale-105 shadow-lg
                ${isActive 
                  ? 'bg-gradient-to-br from-blue-500 to-blue-600 text-white border-blue-600 shadow-blue-200' 
                  : 'bg-gradient-to-br from-gray-50 to-gray-100 text-gray-700 border-gray-300 hover:border-blue-300 hover:shadow-blue-100'
                }
              `}
            >
              <Icon className="mx-auto mb-4" size={40} />
              <h3 className="font-bold text-xl mb-3">{tab.label}</h3>
              <p className={`text-sm font-medium ${isActive ? 'text-blue-100' : 'text-gray-600'}`}>
                {tab.description}
              </p>
            </button>
          );
        })}
      </div>
    </div>
  );
};

export default TabNavigation;