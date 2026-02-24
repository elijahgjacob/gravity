import React, { useState } from 'react'
import { Card, CardContent, CardHeader } from './ui/card'
import { Badge } from './ui/badge'
import { Button } from './ui/button'
import { TrendingUp, MapPin, Users, Award, Tag, Search } from 'lucide-react'

export default function ResultsDisplay({ results }) {
  const [displayCount, setDisplayCount] = useState(10)

  if (!results) {
    return (
      <Card className="border-dashed border-2 bg-muted/50">
        <div className="p-12 text-center">
          <div className="w-16 h-16 bg-muted rounded-full flex items-center justify-center mx-auto mb-4">
            <Search className="w-8 h-8 text-muted-foreground" />
          </div>
          <p className="text-muted-foreground text-lg">Enter a query above to see relevant ad campaigns</p>
        </div>
      </Card>
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
    <div className="space-y-6">
      <Card className="shadow-md bg-card">
        <CardHeader className="pb-4">
          <div className="flex flex-wrap gap-6">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-muted rounded-lg">
                <Award className="w-5 h-5 text-foreground" />
              </div>
              <div>
                <p className="text-sm font-medium text-muted-foreground">Ad Eligibility</p>
                <Badge 
                  variant={ad_eligibility >= 0.8 ? "default" : ad_eligibility >= 0.5 ? "secondary" : "outline"}
                  className={`text-base font-bold mt-1 ${
                    ad_eligibility >= 0.8 ? 'bg-emerald-600 text-white' : 
                    ad_eligibility >= 0.5 ? 'bg-amber-500 text-white' : 
                    ''
                  }`}
                >
                  {(ad_eligibility * 100).toFixed(0)}%
                </Badge>
              </div>
            </div>

            <div className="flex items-start gap-3 flex-1">
              <div className="p-2 bg-muted rounded-lg">
                <Tag className="w-5 h-5 text-foreground" />
              </div>
              <div className="flex-1">
                <p className="text-sm font-medium text-muted-foreground mb-2">Categories</p>
                <div className="flex flex-wrap gap-2">
                  {extracted_categories.map((cat, idx) => (
                    <Badge key={idx} variant="secondary" className="bg-blue-600/20 text-blue-400 hover:bg-blue-600/30 border-blue-500/30">
                      {cat}
                    </Badge>
                  ))}
                </div>
              </div>
            </div>

            <div className="flex items-center gap-3">
              <div className="p-2 bg-muted rounded-lg">
                <TrendingUp className="w-5 h-5 text-foreground" />
              </div>
              <div>
                <p className="text-sm font-medium text-muted-foreground">Total Campaigns</p>
                <p className="text-2xl font-bold text-foreground mt-1">{campaigns.length}</p>
              </div>
            </div>
          </div>
        </CardHeader>
      </Card>

      <div className="space-y-3">
        {displayedCampaigns.map((campaign, idx) => (
          <Card 
            key={campaign.id} 
            className="hover:border-primary/50 hover:shadow-lg transition-all duration-200 bg-card group"
          >
            <CardContent className="p-5">
              <div className="flex items-start justify-between mb-3">
                <div className="flex items-center gap-3">
                  <div className="flex items-center justify-center w-8 h-8 rounded-full bg-primary text-primary-foreground font-bold text-sm">
                    {idx + 1}
                  </div>
                  <Badge className="bg-primary hover:bg-primary/90 text-primary-foreground">
                    {campaign.vertical}
                  </Badge>
                </div>
                <Badge 
                  variant="outline" 
                  className="flex items-center gap-1.5 border-emerald-500/30 bg-emerald-500/10 text-emerald-400 font-semibold"
                >
                  <TrendingUp className="w-3 h-3" />
                  {(campaign.relevance_score * 100).toFixed(1)}% match
                </Badge>
              </div>

              <h3 className="text-xl font-bold text-foreground mb-2 group-hover:text-primary/80 transition-colors">
                {campaign.title}
              </h3>
              <p className="text-muted-foreground leading-relaxed mb-4">
                {campaign.description}
              </p>

              <div className="flex flex-wrap items-center gap-2">
                <Badge variant="secondary" className="bg-secondary text-secondary-foreground">
                  {campaign.category}
                </Badge>

                {campaign.targeting && (
                  <>
                    {campaign.targeting.age_range && (
                      <Badge variant="outline" className="flex items-center gap-1 border-border">
                        <Users className="w-3 h-3" />
                        Age {campaign.targeting.age_range[0]}-{campaign.targeting.age_range[1]}
                      </Badge>
                    )}
                    {campaign.targeting.gender && (
                      <Badge variant="outline" className="border-border">
                        {campaign.targeting.gender}
                      </Badge>
                    )}
                    {campaign.targeting.locations && campaign.targeting.locations.length > 0 && (
                      <Badge variant="outline" className="flex items-center gap-1 border-border">
                        <MapPin className="w-3 h-3" />
                        {campaign.targeting.locations.join(', ')}
                      </Badge>
                    )}
                  </>
                )}
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {campaigns.length > displayCount && (
        <div className="flex justify-center pt-4">
          <Button
            onClick={() => setDisplayCount(Math.min(displayCount + 10, campaigns.length))}
            variant="outline"
            size="lg"
            className="shadow-sm hover:shadow-md transition-all"
          >
            Load More ({campaigns.length - displayCount} remaining)
          </Button>
        </div>
      )}
    </div>
  )
}
