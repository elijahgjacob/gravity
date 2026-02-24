import React, { useState } from 'react'

export default function ResultsDisplay({ results }) {
  const [displayCount, setDisplayCount] = useState(10)

  if (!results) {
    return (
      <div className="results-placeholder">
        <p>Enter a query above to see relevant ad campaigns</p>
      </div>
    )
  }

  const { campaigns, ad_eligibility, extracted_categories } = results
  const displayedCampaigns = campaigns.slice(0, displayCount)

  const getEligibilityColor = (score) => {
    if (score >= 0.8) return 'high'
    if (score >= 0.5) return 'medium'
    return 'low'
  }

  return (
    <div className="results-container">
      <div className="results-header">
        <div className="results-meta">
          <div className="meta-item">
            <span className="meta-label">Ad Eligibility:</span>
            <span className={`eligibility-score ${getEligibilityColor(ad_eligibility)}`}>
              {(ad_eligibility * 100).toFixed(0)}%
            </span>
          </div>
          <div className="meta-item">
            <span className="meta-label">Categories:</span>
            <div className="categories">
              {extracted_categories.map((cat, idx) => (
                <span key={idx} className="category-tag">{cat}</span>
              ))}
            </div>
          </div>
          <div className="meta-item">
            <span className="meta-label">Total Campaigns:</span>
            <span className="meta-value">{campaigns.length}</span>
          </div>
        </div>
      </div>

      <div className="campaigns-list">
        {displayedCampaigns.map((campaign, idx) => (
          <div key={campaign.id} className="campaign-card">
            <div className="campaign-header">
              <span className="campaign-rank">#{idx + 1}</span>
              <span className="campaign-vertical">{campaign.vertical}</span>
              <span className="relevance-score">
                {(campaign.relevance_score * 100).toFixed(1)}% relevant
              </span>
            </div>
            <h3 className="campaign-title">{campaign.title}</h3>
            <p className="campaign-description">{campaign.description}</p>
            <div className="campaign-footer">
              <span className="campaign-category">{campaign.category}</span>
              {campaign.targeting && (
                <div className="targeting-info">
                  {campaign.targeting.age_range && (
                    <span className="targeting-tag">
                      Age: {campaign.targeting.age_range[0]}-{campaign.targeting.age_range[1]}
                    </span>
                  )}
                  {campaign.targeting.gender && (
                    <span className="targeting-tag">
                      {campaign.targeting.gender}
                    </span>
                  )}
                  {campaign.targeting.locations && campaign.targeting.locations.length > 0 && (
                    <span className="targeting-tag">
                      {campaign.targeting.locations.join(', ')}
                    </span>
                  )}
                </div>
              )}
            </div>
          </div>
        ))}
      </div>

      {campaigns.length > displayCount && (
        <div className="load-more">
          <button
            onClick={() => setDisplayCount(Math.min(displayCount + 10, campaigns.length))}
            className="load-more-btn"
          >
            Load More ({campaigns.length - displayCount} remaining)
          </button>
        </div>
      )}
    </div>
  )
}
