import React, { useState } from 'react'
import { ChevronDown } from 'lucide-react'

export function Accordion({ children, defaultOpen = false }) {
  const [isOpen, setIsOpen] = useState(defaultOpen)

  return (
    <div className="border rounded-lg bg-card">
      {React.Children.map(children, child =>
        React.cloneElement(child, { isOpen, setIsOpen })
      )}
    </div>
  )
}

export function AccordionItem({ children, isOpen, setIsOpen }) {
  return (
    <div className="border-b last:border-b-0">
      {React.Children.map(children, child =>
        React.cloneElement(child, { isOpen, setIsOpen })
      )}
    </div>
  )
}

export function AccordionTrigger({ children, isOpen, setIsOpen }) {
  return (
    <button
      onClick={() => setIsOpen(!isOpen)}
      className="flex w-full items-center justify-between p-3 text-left text-sm font-medium transition-all hover:bg-muted/50"
      type="button"
    >
      <span>{children}</span>
      <ChevronDown
        className={`w-4 h-4 transition-transform duration-200 ${
          isOpen ? 'rotate-180' : ''
        }`}
      />
    </button>
  )
}

export function AccordionContent({ children, isOpen }) {
  return (
    <div
      className={`overflow-hidden transition-all duration-200 ${
        isOpen ? 'max-h-[2000px] opacity-100' : 'max-h-0 opacity-0'
      }`}
    >
      <div className="p-3 pt-0">{children}</div>
    </div>
  )
}
