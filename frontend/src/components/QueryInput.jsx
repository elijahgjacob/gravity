import React, { useState } from 'react'
import { Button } from './ui/button'
import { Input } from './ui/input'
import { Label } from './ui/label'
import { Select } from './ui/select'
import { Search, ChevronDown, ChevronUp, Sparkles } from 'lucide-react'

export default function QueryInput({ onSubmit, loading }) {
  const [query, setQuery] = useState('')
  const [showContext, setShowContext] = useState(false)
  const [context, setContext] = useState({
    age: '',
    gender: '',
    location: '',
    interests: ''
  })

  const handleSubmit = (e) => {
    e.preventDefault()
    if (!query.trim()) return

    const requestData = { query: query.trim() }
    
    if (showContext && (context.age || context.gender || context.location || context.interests)) {
      requestData.context = {}
      if (context.age) requestData.context.age = parseInt(context.age)
      if (context.gender) requestData.context.gender = context.gender
      if (context.location) requestData.context.location = context.location
      if (context.interests) requestData.context.interests = context.interests.split(',').map(i => i.trim())
    }

    onSubmit(requestData)
  }

  const exampleQueries = [
    'best running shoes for marathon',
    'affordable laptop for students',
    'luxury watches for men',
    'organic dog food delivery',
    'yoga classes near me'
  ]

  return (
    <div className="space-y-4">
      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="space-y-3">
          <Label htmlFor="query" className="text-base font-semibold">Search Query</Label>
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-muted-foreground" />
            <Input
              id="query"
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Enter a search query..."
              disabled={loading}
              className="pl-10 h-12 text-base focus:ring-primary"
            />
          </div>
          
          <div className="flex flex-wrap gap-2 items-center">
            <span className="text-sm text-muted-foreground font-medium flex items-center gap-1">
              <Sparkles className="w-3.5 h-3.5" />
              Examples:
            </span>
            {exampleQueries.map((example, idx) => (
              <Button
                key={idx}
                type="button"
                onClick={() => setQuery(example)}
                disabled={loading}
                variant="outline"
                size="sm"
                className="text-xs hover:bg-accent transition-all"
              >
                {example}
              </Button>
            ))}
          </div>
        </div>

        <div className="space-y-3">
          <Button
            type="button"
            onClick={() => setShowContext(!showContext)}
            variant="ghost"
            size="sm"
            disabled={loading}
            className="flex items-center gap-2 hover:bg-accent"
          >
            {showContext ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
            {showContext ? 'Hide' : 'Add'} Context (Optional)
          </Button>

          {showContext && (
            <div className="space-y-4 p-4 bg-muted rounded-lg border border-border animate-slide-down">
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="age">Age</Label>
                  <Input
                    id="age"
                    type="number"
                    value={context.age}
                    onChange={(e) => setContext({...context, age: e.target.value})}
                    placeholder="e.g., 25"
                    disabled={loading}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="gender">Gender</Label>
                  <Select
                    id="gender"
                    value={context.gender}
                    onChange={(e) => setContext({...context, gender: e.target.value})}
                    disabled={loading}
                  >
                    <option value="">Select...</option>
                    <option value="male">Male</option>
                    <option value="female">Female</option>
                    <option value="other">Other</option>
                  </Select>
                </div>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="location">Location</Label>
                  <Input
                    id="location"
                    type="text"
                    value={context.location}
                    onChange={(e) => setContext({...context, location: e.target.value})}
                    placeholder="e.g., New York"
                    disabled={loading}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="interests">Interests</Label>
                  <Input
                    id="interests"
                    type="text"
                    value={context.interests}
                    onChange={(e) => setContext({...context, interests: e.target.value})}
                    placeholder="e.g., sports, technology"
                    disabled={loading}
                  />
                </div>
              </div>
            </div>
          )}
        </div>

        <Button 
          type="submit" 
          disabled={loading || !query.trim()} 
          className="w-full h-12 text-base font-semibold transition-all shadow-md hover:shadow-lg"
        >
          {loading ? (
            <>
              <div className="w-4 h-4 border-2 border-primary-foreground border-t-transparent rounded-full animate-spin" />
              Searching...
            </>
          ) : (
            <>
              <Search className="w-5 h-5" />
              Search Campaigns
            </>
          )}
        </Button>
      </form>
    </div>
  )
}
