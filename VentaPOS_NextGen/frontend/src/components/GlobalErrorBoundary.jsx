import React from 'react';
import { IconAlertTriangle, IconRefresh, IconHome } from '@tabler/icons-react';

export default class GlobalErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    console.error('Unhandled Global UI Error:', error, errorInfo);
  }

  handleReload = () => {
    window.location.reload();
  };

  handleGoHome = () => {
    window.location.href = '/';
  };

  render() {
    if (this.state.hasError) {
      return (
        <div
          className="d-flex align-items-center justify-content-center min-vh-100 bg-light p-3"
          dir="rtl"
          style={{ fontFamily: 'Cairo, sans-serif' }}
        >
          <div className="card shadow-sm border-secondary-subtle" style={{ maxWidth: '520px', width: '100%' }}>
            <div className="card-body text-center p-4">
              <div
                className="d-inline-flex align-items-center justify-content-center rounded-circle bg-danger-subtle text-danger mb-3"
                style={{ width: '64px', height: '64px' }}
              >
                <IconAlertTriangle size={36} />
              </div>
              <h3 className="card-title fw-bold text-dark mb-2">عفواً، حدث خطأ غير متوقع</h3>
              <p className="text-muted mb-4 small">
                حدث خلل مؤقت أثناء عرض الشاشة. يمكنك محاولة إعادة تحميل الصفحة أو العودة إلى الشاشة الرئيسية.
              </p>

              {this.state.error && (
                <div
                  className="alert alert-danger text-start small mb-4 py-2 px-3 overflow-auto"
                  style={{ maxHeight: '120px', direction: 'ltr', fontSize: '0.82rem' }}
                >
                  {this.state.error.message || String(this.state.error)}
                </div>
              )}

              <div className="d-flex align-items-center justify-content-center gap-2">
                <button
                  type="button"
                  className="btn btn-primary d-inline-flex align-items-center gap-1 px-4 py-2 fw-bold"
                  onClick={this.handleReload}
                >
                  <IconRefresh size={18} />
                  إعادة تحميل الصفحة
                </button>
                <button
                  type="button"
                  className="btn btn-outline-secondary d-inline-flex align-items-center gap-1 px-4 py-2 fw-bold"
                  onClick={this.handleGoHome}
                >
                  <IconHome size={18} />
                  الرئيسية
                </button>
              </div>
            </div>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}
