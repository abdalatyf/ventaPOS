import React from 'react';

export const SkeletonLoader = ({ className = '', style = {} }) => {
  return (
    <div 
      className={`skeleton-line placeholder ${className}`} 
      style={{ 
        minHeight: '20px', 
        borderRadius: '4px',
        animation: 'placeholder-glow 2s ease-in-out infinite',
        ...style 
      }}
    ></div>
  );
};

export const CardSkeleton = () => {
  return (
    <div className="card">
      <div className="card-body">
        <div className="d-flex align-items-center mb-3">
          <SkeletonLoader style={{ width: '40px', height: '40px', borderRadius: '50%', marginRight: '15px' }} />
          <div className="w-100">
            <SkeletonLoader style={{ width: '50%', marginBottom: '8px' }} />
            <SkeletonLoader style={{ width: '30%' }} />
          </div>
        </div>
        <SkeletonLoader style={{ height: '2rem', width: '80%' }} />
      </div>
    </div>
  );
};
