import React, { ReactNode, ReactElement } from 'react';
import { AlertTriangle } from 'lucide-react';

interface Props {
  children: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

export class ErrorBoundary extends React.Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error('❌ React Error Boundary caught an error:', error);
    console.error('Error Info:', errorInfo);
  }

  render(): ReactElement {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen bg-red-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-lg border-2 border-red-200 p-8 max-w-2xl shadow-lg">
            <div className="flex items-center space-x-3 mb-4">
              <AlertTriangle className="w-8 h-8 text-red-600" />
              <h1 className="text-2xl font-bold text-red-800">Something went wrong</h1>
            </div>
            
            <div className="bg-red-50 border border-red-200 rounded p-4 mb-4">
              <p className="text-red-800 font-mono text-sm break-words">
                {this.state.error?.message || 'Unknown error'}
              </p>
            </div>

            <div className="space-y-2 text-sm text-gray-700">
              <p><strong>Troubleshooting steps:</strong></p>
              <ul className="list-disc list-inside space-y-1">
                <li>Check the browser console (F12) for more details</li>
                <li>Try refreshing the page (Ctrl+R)</li>
                <li>Make sure the API server is running on port 8000</li>
                <li>Make sure the detector is running with --test flag</li>
              </ul>
            </div>

            <div className="mt-6 flex space-x-3">
              <button
                onClick={() => window.location.reload()}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
              >
                Refresh Page
              </button>
              <button
                onClick={() => this.setState({ hasError: false, error: null })}
                className="px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 transition-colors"
              >
                Try Again
              </button>
            </div>

            <div className="mt-4 pt-4 border-t border-gray-200 text-xs text-gray-600">
              <details>
                <summary className="cursor-pointer hover:text-gray-800">Full error details</summary>
                <pre className="mt-2 bg-gray-100 p-2 rounded overflow-auto max-h-48">
                  {this.state.error?.stack || 'No stack trace available'}
                </pre>
              </details>
            </div>
          </div>
        </div>
      );
    }

    return this.props.children as ReactElement;
  }
}
